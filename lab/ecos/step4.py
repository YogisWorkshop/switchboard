import socket

import protocol

ECOS_HOSE = "192.168.1.2"
ECOS_PORT = 15471

def read_lines(sock):
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
    lines = read_lines(sock)
    return protocol.parse_reply(lines)

sock = socket.create_connection((ECOS_HOSE, ECOS_PORT), timeout=3)

reply = send_command(sock, "get(1, status)")
obj_id, options = reply.entries[0]
print("Track power:", options["status"][0])
print()

reply = send_command(sock, "queryObjects(10, name, addr, protocol)")
for obj_id, options in sorted(reply.entries, key=lambda entry: int(entry[1]["addr"][0])):
    print(f"{obj_id} addr {options['addr'][0]:>5} {options['name'][0]} {options['protocol'][0]:<8}")
print()

reply = send_command(sock, "get(99999, name)")
if not reply.ok:
    print(f"Error {reply.code}: {reply.text}")

sock.close