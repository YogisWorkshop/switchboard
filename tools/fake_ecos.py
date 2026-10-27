"""A pretend ECoS for testing without hardware.  python tools/fake_ecos.py

Console: go / stop = press the ECoS's own power button
d = drop all connections (cable pulled), s = go silent / answer again, q = quit.
"""
import re
import socket
import sys
import threading

PORT = 15471

ACCESSORIES = {   # object id -> [name, addr, protocol, state]
    20000: ["T1", 1, "DCC", 0],
    20001: ["T2", 2, "DCC", 0],
    20002: ["T3", 3, "DCC", 1],
    20003: ["T4", 4, "DCC", 0],
    20004: ["T5", 5, "MM", 0],
    20005: ["T6", 6, "MM", 1],
}
ROUTE = 30000


class FakeEcos:
    def __init__(self, port=PORT):
        self.silent = False
        self.power = "GO"
        self.clients = []
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
        buffer = b""
        try:
            while True:
                chunk = sock.recv(1024)
                if not chunk:
                    return
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    self._handle(sock, line.decode().strip())
        except OSError:
            pass

    @staticmethod
    def _reply(command, lines=()):
        body = "".join(f"{line}\r\n" for line in lines)
        return f"<REPLY {command}>\r\n{body}<END 0 (OK)>\r\n".encode()

    @staticmethod
    def _event(obj_id, option):
        return f"<EVENT {obj_id}>\r\n{obj_id} {option}\r\n<END 0 (OK)>\r\n".encode()

    def _handle(self, sock, command):
        if self.silent:
            return
        if command.startswith("queryObjects(11"):
            lines = [f'{i} name1["{n}"] addr[{a}] protocol[{p}]'
                     for i, (n, a, p, _) in ACCESSORIES.items()]
            lines.append(f'{ROUTE} name1["Route"]')
            sock.sendall(self._reply(command, lines))
        elif command.startswith("get(1, status)"):
            sock.sendall(self._reply(command, [f"1 status[{self.power}]"]))
        elif m := re.match(r"set\(1, (go|stop)\)", command):
            sock.sendall(self._reply(command))
            self.set_power(m.group(1).upper())
        elif m := re.match(r"get\((\d+), state\)", command):
            obj_id = int(m.group(1))
            sock.sendall(self._reply(command, [f"{obj_id} state[{ACCESSORIES[obj_id][3]}]"]))
        elif m := re.match(r"set\(11, switch\[(DCC|MM)(\d+)([rg])\]\)", command):
            protocol, address, port = m.group(1), int(m.group(2)), m.group(3)
            sock.sendall(self._reply(command))
            for obj_id, item in ACCESSORIES.items():
                if item[1] == address and item[2] == protocol:
                    item[3] = 1 if port == "r" else 0
                    for option in ("switching[1]", f"state[{item[3]}]", "switching[0]"):
                        for client in list(self.clients):
                            try:
                                client.sendall(self._event(obj_id, option))
                            except OSError:
                                pass
        else:                                  # request(...) and anything else
            sock.sendall(self._reply(command))

    def set_power(self, status):
        """GO or STOP, from a command or from the ECoS's own buttons."""
        self.power = status
        for client in list(self.clients):
            try:
                client.sendall(self._event(1, f"status[{status}]"))
            except OSError:
                pass

    def drop_all(self):
        for client in self.clients:
            try:
                client.shutdown(socket.SHUT_RDWR)
                client.close()
            except OSError:
                pass
        self.clients.clear()


if __name__ == "__main__":
    ecos = FakeEcos()
    print("Fake ECoS on port", PORT, " (d = drop, s = silent toggle, q = quit)")
    for line in sys.stdin:
        key = line.strip()
        if key in ("go", "stop"):
            ecos.set_power(key.upper())
        elif key == "d":
            ecos.drop_all()
            print("dropped")
        elif key == "s":
            ecos.silent = not ecos.silent
            print("silent" if ecos.silent else "answering")
        elif key == "q":
            break