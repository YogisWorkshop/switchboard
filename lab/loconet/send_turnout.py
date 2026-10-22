import sys
import time

import serial

import loconet_protocol

PORT = "/dev/serial/by-id/usb-RR-CirKits_LocoBuffer-NG_CDC_ACM_SERIAL_DEVICE_AA5700230A-if00"
ADDRESS = 1
PULSE = 0.2   # seconds between ON and OFF


def show(prefix, message):
    print(f"{prefix} {message.hex(' '):<14} {loconet_protocol.decode(message)}")


def send(port, framer, request):
    message = request.to_bytes()
    show(">>", message)
    port.write(message)
    deadline = time.monotonic() + 1.0
    while time.monotonic() < deadline:
        for received in framer.feed(port.read(64)):
            show("<<", received)
            if received == message:
                return True
    print("   no echo within 1 second!")
    return False


def listen(port, framer, seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        for received in framer.feed(port.read(64)):
            show("<<", received)


if len(sys.argv) > 1:
    port = serial.serial_for_url(sys.argv[1], timeout=0.1)
else:
    port = serial.Serial(PORT, 57600, timeout=0.1)
framer = loconet_protocol.Framer()

print(f"Turnout {ADDRESS}: type r or g, q to quit.")
try:
    while True:
        choice = input("> ").strip()
        if choice == "q":
            break
        if choice not in ("r", "g"):
            print("  ?")
            continue
        closed = choice == "g"
        send(port, framer, loconet_protocol.SwitchRequest(ADDRESS, closed, on=True))
        time.sleep(PULSE)
        send(port, framer, loconet_protocol.SwitchRequest(ADDRESS, closed, on=False))
        listen(port, framer, 1.0)
except KeyboardInterrupt:
    print()
finally:
    port.close()