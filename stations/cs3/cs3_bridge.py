import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

from stations.bridge import StationBridge
from stations.cs3 import cs3_protocol
from stations.cs3.cs3_client import Cs3Client


class Cs3Bridge(StationBridge):
    PING_SECONDS = 5        # how often we ask "who is on the bus?"
    SILENCE_SECONDS = 15    # no frame at all for this long = connection lost
    CONNECT_TIMEOUT = 3     # how long to wait for the CS3 to say anything after connecting

    def __init__(self, host):
        super().__init__()
        self.host = host
        self.client = None
        self._token = None                    # identifies the current connection
        self._last_frame = time.monotonic()
        self._got_frame = threading.Event()
        self._heartbeat_stop = threading.Event()
        self._sender = ThreadPoolExecutor(max_workers=1)

    # ---- hooks (see StationBridge) --------------------------------------

    def _open(self):
        token = object()
        self._token = token
        self._last_frame = time.monotonic()
        self._got_frame.clear()
        client = Cs3Client(
            self.host, self._on_frame, lambda: self._client_lost(token)
        )
        # A TCP connection can succeed even though nobody is home, so don't
        # call it connected until the CS3 has actually said something.
        client.send(cs3_protocol.ping_frame())
        if not self._got_frame.wait(self.CONNECT_TIMEOUT):
            self._token = None
            client.close()
            raise TimeoutError("connected, but the CS3 is not answering")
        self.client = client
        self._start_heartbeat(client, token)

    # _resync stays the default (does nothing): the CS3 cannot be asked for
    # turnout positions, so they stay as they were until the next confirmation.

    def _close(self):
        self._token = None                    # a late disconnect callback is now ignored
        self._heartbeat_stop.set()
        client, self.client = self.client, None
        if client is not None:
            client.close()

    def _send_turnout(self, address, protocol, diverging):
        if self.client is None:
            raise ConnectionError("not connected")
        cs3_protocol.accessory_uid(address, protocol)   # ValueError if out of range
        self._sender.submit(
            self._do_send, self.client, self._token, address, protocol, diverging
        )

    def _send_power(self, on):
        if self.client is None:
            raise ConnectionError("not connected")
        sub = cs3_protocol.SUB_GO if on else cs3_protocol.SUB_STOP
        self._sender.submit(self._do_send_power, self.client, self._token, sub)

    # ---- sending (runs on the sender thread, never the UI thread) --------

    def _do_send(self, client, token, address, protocol, diverging):
        position = cs3_protocol.POSITION_RED if diverging else cs3_protocol.POSITION_GREEN
        try:
            reply = client.switch_accessory(address, position, protocol)
        except OSError:
            self._client_lost(token)
            return
        if reply is None:
            print(f"CS3 did not confirm {protocol} {address}")
        # On success there is nothing to do here: the confirmation also arrives
        # through _on_frame, and that is the one place the panel gets updated.

    def _do_send_power(self, client, token, sub_command):
        try:
            client.send(cs3_protocol.system_frame(sub_command))
        except OSError:
            self._client_lost(token)
        # The CS3 confirms GO/STOP; _on_frame turns that into power_changed.

    # ---- incoming (runs on the client's reader thread) -------------------

    def _on_frame(self, frame):
        self._last_frame = time.monotonic()
        self._got_frame.set()
        try:
            decoded = cs3_protocol.decode(frame)
            if (isinstance(decoded, cs3_protocol.AccessorySwitch)
                    and decoded.response and decoded.protocol != "?"):
                diverging = decoded.position == cs3_protocol.POSITION_RED
                self.turnout_changed.emit(decoded.address, decoded.protocol, diverging)
            elif (isinstance(decoded, cs3_protocol.SystemCommand) and decoded.response
                    and decoded.sub_command in (cs3_protocol.SUB_GO, cs3_protocol.SUB_STOP)):
                self.report_power(decoded.sub_command == cs3_protocol.SUB_GO)
        except Exception:
            traceback.print_exc()             # never let a bug kill the reader thread

    def _client_lost(self, token):
        if token is self._token:              # ignore callbacks from old connections
            self.report_lost()

    # ---- heartbeat -------------------------------------------------------

    def _start_heartbeat(self, client, token):
        self._heartbeat_stop = stop = threading.Event()

        def run():
            while not stop.wait(self.PING_SECONDS):
                if time.monotonic() - self._last_frame > self.SILENCE_SECONDS:
                    self._client_lost(token)
                    return
                try:
                    client.send(cs3_protocol.ping_frame())
                except OSError:
                    self._client_lost(token)
                    return

        threading.Thread(target=run, daemon=True).start()