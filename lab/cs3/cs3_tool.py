#!/usr/bin/env python3
"""Interactive CS3 test tool for the club. Logs every frame to a file.

Usage:   python3 cs3_tool.py              (uses CS3_HOST below)
         python3 cs3_tool.py <IP>         (one-off override)

Commands at the > prompt:
    ping                 ask every device on the bus to identify itself
    go / stop            track power
    t 5 r                switch DCC accessory 5 to red/diverging   (one frame, CS3 times it)
    t 5 g                switch DCC accessory 5 to green/straight
    t 5 g mm             same, Märklin-Motorola accessory
    tp 5 g               pulse variant: ON, 0.2 s, OFF (DLC 6 frames)
    s 0 1                query feedback device 0, contact 1
    raw <26 hex digits>  send a hand-made 13-byte frame
    quiet / loud         quiet (default): only turnouts, feedback, track power
                         loud: every frame (everything is always logged)
    q                    quit

Everything sent and received goes into cs3_log_<date>_<time>.txt as well,
so the session can be studied afterwards.
"""

import sys
import time

import cs3_client
import cs3_protocol

CS3_HOST = "192.168.1.10"    # club CS3, same address as in LocoNet_CS_Bridge v2.1

show_all = False   # quiet by default: the club CS3 sends up to ~50 frames a second
log_file = open(time.strftime("cs3_log_%Y%m%d_%H%M%S.txt"), "w", encoding="utf-8")


def describe(frame):
    decoded = cs3_protocol.decode(frame)
    raw = frame.to_bytes().hex(" ")
    flag = "R" if frame.response else " "
    name = cs3_protocol.COMMAND_NAMES.get(frame.command, f"cmd 0x{frame.command:02x}")
    text = decoded if decoded is not None else name
    return decoded, f"{raw}  {flag} hash=0x{frame.hash_code:04x}  {text}"


def is_interesting(decoded):
    """What a panel cares about: turnouts, feedback, track power."""
    if isinstance(decoded, (cs3_protocol.AccessorySwitch, cs3_protocol.FeedbackEvent)):
        return True
    if isinstance(decoded, cs3_protocol.SystemCommand):
        return decoded.sub_command in cs3_protocol.IMPORTANT_SUBS
    return False


def log(direction, frame):
    decoded, text = describe(frame)
    line = f"{time.strftime('%H:%M:%S')} {direction} {text}"
    log_file.write(line + "\n")
    log_file.flush()
    if show_all or direction == ">>" or is_interesting(decoded):
        print(line)


def on_frame(frame):
    log("<<", frame)


def on_disconnect():
    print("*** connection closed ***")
    log_file.write("*** connection closed ***\n")


def send(client, frame):
    log(">>", frame)
    client.send(frame)


def handle(client, parts):
    global show_all
    command = parts[0]

    if command == "ping":
        send(client, cs3_protocol.ping_frame())
    elif command in ("go", "stop"):
        sub = cs3_protocol.SUB_GO if command == "go" else cs3_protocol.SUB_STOP
        send(client, cs3_protocol.system_frame(sub))
    elif command in ("t", "tp") and len(parts) in (3, 4) and parts[1].isdigit() and parts[2] in ("r", "g"):
        address = int(parts[1])
        position = cs3_protocol.POSITION_GREEN if parts[2] == "g" else cs3_protocol.POSITION_RED
        protocol = "MM" if len(parts) == 4 and parts[3].lower() == "mm" else "DCC"
        if command == "t":
            # Same as the club bridge: one DLC 8 frame, CS3 switches off after 100 ms
            frame = cs3_protocol.accessory_frame(address, position, 1, protocol, switch_time=10)
            log(">>", frame)
            reply = client.request(frame)
            print("   confirmed" if reply else "   NO CONFIRMATION within 1 s")
        else:
            # Pulse variant: ON (DLC 6), wait 0.2 s, OFF
            on = cs3_protocol.accessory_frame(address, position, 1, protocol)
            off = cs3_protocol.accessory_frame(address, position, 0, protocol)
            log(">>", on)
            reply = client.request(on)
            print("   confirmed" if reply else "   NO CONFIRMATION within 1 s")
            time.sleep(0.2)
            log(">>", off)
            client.request(off)
    elif command == "s" and len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
        send(client, cs3_protocol.s88_query_frame(int(parts[1]), int(parts[2])))
    elif command == "raw" and len(parts) == 2 and len(parts[1]) == 26:
        frame = cs3_protocol.Frame.from_bytes(bytes.fromhex(parts[1]))
        send(client, frame)
    elif command == "quiet":
        show_unknown = False
        print("   hiding frames that don't decode (still logged)")
    elif command == "loud":
        show_all = False   # quiet by default: the club CS3 sends up to ~50 frames a second
    else:
        print("   ?  (ping, go, stop, t|tp <addr> r|g [mm], s <dev> <contact>, raw <hex>, quiet, loud, q)")


def main():
    if len(sys.argv) > 2:
        print(__doc__)
        return
    host = sys.argv[1] if len(sys.argv) == 2 else CS3_HOST
    print(f"Connecting to {host}:{cs3_protocol.CS3_PORT} ... my hash is 0x{cs3_protocol.MY_HASH:04x}")
    client = cs3_client.Cs3Client(host, on_frame, on_disconnect)
    print(f"Connected. Logging to {log_file.name}. Type a command, q to quit.")
    try:
        while True:
            parts = input("> ").split()
            if not parts:
                continue
            if parts == ["q"]:
                break
            try:
                handle(client, parts)
            except ValueError as error:
                print(f"   {error}")
    except (KeyboardInterrupt, EOFError):   # Ctrl-C, or Ctrl-Z on Windows
        print()
    finally:
        client.close()
        log_file.close()


if __name__ == "__main__":
    main()
