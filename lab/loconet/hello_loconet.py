import serial

PORT = PORT = "/dev/serial/by-id/usb-RR-CirKits_LocoBuffer-NG_CDC_ACM_SERIAL_DEVICE_AA5700230A-if00"

port = serial.Serial(PORT, 57600, timeout=1)
print(f"Listening on {port.name}. Ctrl-C to quit.")

try:
    while True:
        data = port.read(64)
        if data:
            print(data.hex(" "))
except KeyboardInterrupt:
    print("\nStopped.")
finally:
    port.close()