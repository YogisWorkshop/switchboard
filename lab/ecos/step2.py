import socket

ECOS_HOST = "192.168.1.2"
ECOS_PORT = 15471

def read_reply(sock):
    buffer = b""
    lines = []
    while True:
        chunk = sock.recv(1024)
        if not chunk:
            raise ConnectionError("ECoS closed the connection")
        buffer += chunk
        while b"\n" in buffer:
            raw_line, buffer = buffer.split(b"\n", 1)
            line = raw_line.decode("utf-8").rstrip("\r")
            lines.append(line)
            if line.startswith("<END"):
                return lines

def send_command(sock, command):
    sock.sendall((command + "\n").encode("utf-8"))
    return read_reply(sock)

sock = socket.create_connection((ECOS_HOST, ECOS_PORT), timeout=3)

for command in ["get(1, status)", "queryObjects(10, name)",  "get(99999, name)"]:
    print(f">> {command}")
    for line in send_command(sock, command):
        print(line)
    print()

sock.close