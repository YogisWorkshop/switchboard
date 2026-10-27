"""A pretend CS3 for testing without hardware.  python tools/fake_cs3.py

Console: t <addr> r|g [mm] = throw a turnout "on the CS3 screen"
         go / stop = press the CS3 screen's power button
         d = drop all connections, s = go silent / answer again, q = quit
"""
import socket
import sys
import threading

from stations.cs3 import cs3_protocol as p

PORT = p.CS3_PORT
GUI_HASH = 0xB326            # what the CS3 screen uses as sender
TRACK_HASH = 0x8B3F          # the track processor, which confirms every command


class FakeCs3:
    def __init__(self, port=PORT):
        self.silent = False
        self.power = None
        self.clients = []
        self.positions = {}                    # (protocol, address) -> 0 / 1
        self.server = socket.socket()
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(("127.0.0.1", port))
        self.server.listen()
        threading.Thread(target=self._accept, daemon=True).start()

    def _accept(self):
        while True:
            try:
                sock, _ = self.server.accept()
            except OSError:
                return
            self.clients.append(sock)
            threading.Thread(target=self._serve, args=(sock,), daemon=True).start()

    def _serve(self, sock):
        framer = p.Framer()
        try:
            while True:
                data = sock.recv(1024)
                if not data:
                    return
                for frame in framer.feed(data):
                    self._handle(frame)
        except OSError:
            pass

    def broadcast(self, frame):
        for client in list(self.clients):
            try:
                client.sendall(frame.to_bytes())
            except OSError:
                pass

    def _handle(self, frame):
        if self.silent or frame.response:
            return
        if frame.command == p.CMD_PING:
            reply = bytes.fromhex("6373f555") + bytes([2, 5]) + (0xFFFF).to_bytes(2, "big")
            self.broadcast(p.Frame(p.CMD_PING, True, GUI_HASH, reply))
        elif frame.command == p.CMD_ACCESSORY:
            self._confirm(frame)
        elif frame.command == p.CMD_SYSTEM and len(frame.data) >= 5:
            self._confirm_power(frame)

    def _confirm_power(self, frame):
        """Only GO and STOP are answered. Like the real CS3: confirmed twice."""
        if frame.data[4] not in (p.SUB_GO, p.SUB_STOP):
            return
        self.power = frame.data[4] == p.SUB_GO
        self.broadcast(p.Frame(p.CMD_SYSTEM, True, TRACK_HASH, frame.data))
        self.broadcast(p.Frame(p.CMD_SYSTEM, True, TRACK_HASH, frame.data))

    def screen_power(self, go):
        """The GO/STOP button on the CS3 screen."""
        frame = p.system_frame(p.SUB_GO if go else p.SUB_STOP)
        frame.hash_code = GUI_HASH
        self.broadcast(frame)
        self._confirm_power(frame)

    def _confirm(self, frame):
        decoded = p.decode(frame)
        self.positions[(decoded.protocol, decoded.address)] = decoded.position
        self.broadcast(p.Frame(frame.command, True, TRACK_HASH, frame.data))
        if decoded.switch_time:                # the CS3 reports the OFF itself
            off = frame.data[:4] + bytes([decoded.position, 0])
            threading.Timer(0.1, self.broadcast,
                            [p.Frame(frame.command, True, TRACK_HASH, off)]).start()

    def screen_throw(self, address, protocol, position):
        """A throw from the CS3 screen: ON + OFF, each confirmed."""
        on = p.accessory_frame(address, position, 1, protocol)
        off = p.accessory_frame(address, position, 0, protocol)
        for frame in (on, off):
            frame.hash_code = GUI_HASH
            self.broadcast(frame)
            self._confirm(frame)

    def drop_all(self):
        for client in self.clients:
            try:
                client.shutdown(socket.SHUT_RDWR)
                client.close()
            except OSError:
                pass
        self.clients.clear()


if __name__ == "__main__":
    cs3 = FakeCs3()
    print("Fake CS3 on port", PORT, " (t <addr> r|g [mm], d = drop, s = silent toggle, q = quit)")
    for line in sys.stdin:
        parts = line.split()
        if not parts:
            continue
        if parts[0] in ("go", "stop"):
            cs3.screen_power(parts[0] == "go")
        elif parts[0] == "d":
            cs3.drop_all()
            print("dropped")
        elif parts[0] == "s":
            cs3.silent = not cs3.silent
            print("silent" if cs3.silent else "answering")
        elif parts[0] == "t" and len(parts) in (3, 4) and parts[1].isdigit() and parts[2] in ("r", "g"):
            protocol = "MM" if len(parts) == 4 and parts[3].lower() == "mm" else "DCC"
            cs3.screen_throw(int(parts[1]), protocol, 0 if parts[2] == "r" else 1)
        elif parts[0] == "q":
            break