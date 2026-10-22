import socket

ECOS_HOST = "192.168.1.2"
ECOS_PORT = 15471

sock = socket.create_connection((ECOS_HOST, ECOS_PORT), timeout=3)
sock.sendall(b"get(1, info)\n")
data = sock.recv(1024)
print(data.decode("utf-8"))
sock.close()