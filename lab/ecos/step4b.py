import connection
import time

ECOS_HOST = "192.168.1.2" \
""   # your ECoS IP


def list_accessories(sock):
    reply = connection.send_command(sock, "queryObjects(11, name1, addr, protocol)")
    for obj_id, options in reply.entries:
        name = options.get("name1", ["-"])[0]
        addr = options.get("addr", ["-"])[0]
        proto = options.get("protocol", ["-"])[0]
        print(f"{obj_id}  addr {addr:>5}  {proto:<4}  {name}")


def switch_turnout(sock, address, port, protocol_name="DCC"):
    if port not in ("r", "g"):
        raise ValueError(f"port must be 'r' or 'g', not {port!r}")
    command = f"set(11, switch[{protocol_name}{address}{port}])"
    reply = connection.send_command(sock, command)
    print(f"{command}  ->  {reply.code} ({reply.text})")


sock = connection.connect(ECOS_HOST)

list_accessories(sock)
print()

switch_turnout(sock, 1, "r")
input("Look at the turnout, then press Enter to switch it back...")
switch_turnout(sock, 1, "g")

time.sleep(3)
sock.close()