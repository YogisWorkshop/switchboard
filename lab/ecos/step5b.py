import ecos_client

ECOS_HOST = "192.168.1.2"   # your ECoS IP


def show_event(message):
    for obj_id, options in message.entries:
        print(f"  EVENT {obj_id}: {options}")


def show_disconnect():
    print("  Connection closed.")


client = ecos_client.EcosClient(ECOS_HOST, show_event, show_disconnect)

client.send_command("request(1, view)")
reply = client.send_command("queryObjects(11)")
for obj_id, options in reply.entries:
    client.send_command(f"request({obj_id}, view)")
print(f"Watching the ECoS and {len(reply.entries)} accessories.")

print("Type e.g. '1 r' or '1 g' to throw turnout 1, 'q' to quit.")
try:
    while True:
        parts = input("> ").split()
        if parts == ["q"]:
            break
        if len(parts) == 2 and parts[0].isdigit() and parts[1] in ("r", "g"):
            address, port = parts
            reply = client.send_command(f"set(11, switch[DCC{address}{port}])")
            print(f"  REPLY {reply.header}: {reply.code} ({reply.text})")
        else:
            print("  ?")
except KeyboardInterrupt:
    pass
finally:
    client.close()