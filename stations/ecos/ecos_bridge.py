import threading
from concurrent.futures import ThreadPoolExecutor

from stations.bridge import StationBridge
from stations.ecos.ecos_client import EcosClient

HEARTBEAT_SECONDS = 3

# Protocol name used inside switch[...]. Confirm "MM" on the real ECoS.
SWITCH_PREFIX = {"DCC": "DCC", "MM": "MM"}


def normalize_protocol(text):
    """ECoS protocol string -> "DCC" or "MM", or None if the tiles can't use it."""
    text = text.upper()
    if text.startswith("DCC"):
        return "DCC"
    if text.startswith("MM") or text == "MOT":
        return "MM"
    return None


class EcosBridge(StationBridge):
    def __init__(self, host):
        super().__init__()
        self.host = host
        self.client = None
        self.accessories = {}                 # ECoS object id -> (address, protocol)
        self._token = None                    # identifies the current connection
        self._heartbeat_stop = threading.Event()
        self._sender = ThreadPoolExecutor(max_workers=1)

    # ---- hooks (see StationBridge) --------------------------------------

    def _open(self):
        token = object()
        self._token = token
        client = EcosClient(
            self.host, self._on_event, lambda: self._client_lost(token)
        )
        try:
            client.send_command("request(1, view)")
            reply = client.send_command("queryObjects(11, name1, addr, protocol)")
            accessories = {}
            for obj_id, options in reply.entries:
                if "addr" not in options:         # routes have no address
                    continue
                protocol = normalize_protocol(options.get("protocol", [""])[0])
                if protocol is None:
                    continue
                accessories[obj_id] = (int(options["addr"][0]), protocol)
            for obj_id in accessories:
                client.send_command(f"request({obj_id}, view)")
        except Exception:
            self._token = None
            client.close()
            raise
        self.accessories = accessories
        self.client = client
        self._start_heartbeat(client, token)

    def _resync(self):
        """Read track power and every turnout's position, so the panel starts out correct."""
        self._power_from_reply(self.client.send_command("get(1, status)"))
        for obj_id, (address, protocol) in self.accessories.items():
            reply = self.client.send_command(f"get({obj_id}, state)")
            state = reply.entries[0][1].get("state") if reply.ok and reply.entries else None
            if state:
                self.turnout_changed.emit(address, protocol, state[0] == "1")

    def _close(self):
        self._token = None                    # a late disconnect callback is now ignored
        self._heartbeat_stop.set()
        client, self.client = self.client, None
        if client is not None:
            client.close()

    def _send_turnout(self, address, protocol, diverging):
        if self.client is None:
            raise ConnectionError("not connected")
        self._sender.submit(self._do_send, self.client, address, protocol, diverging)

    def _send_power(self, on):
        if self.client is None:
            raise ConnectionError("not connected")
        command = "set(1, go)" if on else "set(1, stop)"
        self._sender.submit(self._do_command, self.client, command)

    def _power_from_reply(self, reply):
        status = reply.entries[0][1].get("status") if reply.ok and reply.entries else None
        if status:
            self.report_power(status[0] == "GO")

    # ---- sending (runs on the sender thread, never the UI thread) --------

    def _do_send(self, client, address, protocol, diverging):
        port = "r" if diverging else "g"
        self._do_command(
            client, f"set(11, switch[{SWITCH_PREFIX[protocol]}{address}{port}])"
        )

    def _do_command(self, client, command):
        try:
            reply = client.send_command(command)
        except OSError:
            self.report_lost()
            return
        if not reply.ok:
            print(f"ECoS refused {command}: {reply.code} ({reply.text})")

    # ---- incoming (runs on the client's reader thread) -------------------

    def _on_event(self, message):
        for obj_id, options in message.entries:
            if obj_id == 1 and "status" in options:       # the ECoS itself: track power
                self.report_power(options["status"][0] == "GO")
            accessory = self.accessories.get(obj_id)
            if accessory is not None and "state" in options:
                address, protocol = accessory
                self.turnout_changed.emit(address, protocol, options["state"][0] == "1")

    def _client_lost(self, token):
        if token is self._token:              # ignore callbacks from old connections
            self.report_lost()

    # ---- heartbeat -------------------------------------------------------

    def _start_heartbeat(self, client, token):
        self._heartbeat_stop = stop = threading.Event()

        def run():
            while not stop.wait(HEARTBEAT_SECONDS):
                try:
                    self._power_from_reply(client.send_command("get(1, status)"))
                except OSError:               # includes TimeoutError
                    self._client_lost(token)
                    return

        threading.Thread(target=run, daemon=True).start()