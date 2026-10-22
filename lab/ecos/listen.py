import connection

ECOS_HOST = "192.168.1.2"

ecos = connection.Connection(ECOS_HOST)

for command in ["request(1, view)", "request(20000, view)"]:
    reply = ecos.send_command(command)
    print(f"{command}  ->  {reply.code}  ({reply.text})")

print("Listening... throw turnout 1 or press GO/STOP on the ECoS. Ctrl-C to quit.")
try:
    while True:
        try:
            message = ecos.read_message()
        except TimeoutError:
            continue
        print(f"{message.kind} {message.header}: {message.entries}")
except KeyboardInterrupt:
    print("\nStopped.")
finally:
    ecos.close