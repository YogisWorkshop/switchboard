"""Talking to the ECoS over TCP. Knows about sockets, not about the text format."""

import socket

from stations.ecos import protocol

ECOS_PORT = 15471


class Connection:
    def __init__(self, host, port=ECOS_PORT):
        self.sock = socket.create_connection((host, port), timeout=3)
        self.buffer = b""
        self.lines = []

    def read_message(self):
        while True:
            while b"\n" in self.buffer:
                raw_line, self.buffer = self.buffer.split(b"\n", 1)
                line = raw_line.decode("utf-8").rstrip("\r")
                self.lines.append(line)
                if line.startswith("<END"):
                    lines = self.lines
                    self.lines = []
                    return protocol.parse_message(lines)
            chunk = self.sock.recv(1024)
            if not chunk:
                raise ConnectionError("ECoS closed the connection")
            self.buffer += chunk

    def send(self, command):
        self.sock.sendall((command + "\n").encode("utf-8"))

    def send_command(self, command):
        self.send(command)
        return self.read_message()

    def close(self):
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.sock.close()