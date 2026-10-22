import serial

import loconet_protocol

PORT = "/dev/serial/by-id/usb-RR-CirKits_LocoBuffer-NG_CDC_ACM_SERIAL_DEVICE_AA5700230A-if00"

port = serial.Serial(PORT, 57600, timeout=1)
framer = loconet_protocol.Framer()
print(f"Listening on {port.name}. Ctrl-C to quit.")

try:
    while True:
        data = port.read(64)
        for message in framer.feed(data):
            if not loconet_protocol.checksum_ok(message):
                print(f"{message.hex(' '):<20} BAD CHECKSUM")
                continue
            decoded = loconet_protocol.decode(message)
            print(f"{message.hex(' '):<20} {decoded}")
except KeyboardInterrupt:
    print("\nStopped.")
finally:
    port.close()