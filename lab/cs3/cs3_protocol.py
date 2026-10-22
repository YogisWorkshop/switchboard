"""Märklin CS2/CS3 CAN protocol: 13-byte frames <-> Python objects. No sockets here.

Source: Märklin "Kommunikationsprotokoll CS2 CAN" version 2.0.

Every message, over CAN, UDP or TCP, is one 13-byte frame:

    byte 0-3   CAN identifier (29 bits used, big endian)
    byte 4     DLC = number of data bytes actually used (0-8)
    byte 5-12  data, always 8 bytes, unused ones are 0

The 29-bit CAN identifier packs four fields:

    bits 28-25  priority     (4 bits)
    bits 24-17  command      (8 bits)   e.g. 0x0B = switch accessory
    bit  16     response     (1 bit)    1 = this is an answer / confirmation
    bits 15-0   hash         (16 bits)  identifies the sender
"""

from dataclasses import dataclass

CS3_PORT = 15731          # TCP: one connection, frames in both directions
FRAME_SIZE = 13

# Command field values
CMD_SYSTEM = 0x00         # stop / go / halt (sub-command in data byte 4)
CMD_ACCESSORY = 0x0B      # switch an accessory (turnout, signal)
CMD_S88_EVENT = 0x11      # feedback contact query / report
CMD_PING = 0x18           # "who is on the bus?"

# System sub-commands (data byte 4 of a CMD_SYSTEM frame)
SUB_STOP = 0x00
SUB_GO = 0x01
SUB_HALT = 0x02
SUB_NAMES = {
    SUB_STOP: "STOP", SUB_GO: "GO", SUB_HALT: "HALT",
    0x03: "LOCO E-STOP", 0x06: "SWITCH TIME", 0x0A: "OVERLOAD",
    0x0B: "STATUS",      # measured values (current, voltage, temp), polled by the CS3 every 5 s
    0x20: "TIME",
    0x30: "MFX SEEK",    # seen several times a second at the club, mfx registration
}
# The sub-commands a panel cares about; everything else is background chatter
IMPORTANT_SUBS = {SUB_STOP, SUB_GO, SUB_HALT, 0x0A}

# Command names, for readable logs (spec overview table + LocoNet_CS_Bridge)
COMMAND_NAMES = {
    0x00: "SYSTEM", 0x01: "DISCOVERY", 0x02: "BIND", 0x03: "VERIFY",
    0x04: "LOCO SPEED", 0x05: "LOCO DIR", 0x06: "LOCO FUNC",
    0x07: "READ CONFIG", 0x08: "WRITE CONFIG", 0x0B: "ACCESSORY",
    0x10: "S88 POLL", 0x11: "S88 EVENT", 0x18: "PING",
}

# Accessory decoders are addressed by a 32-bit "UID" in data bytes 0-3.
# The protocol decides the range; the user-facing address is added on top.
ACCESSORY_BASES = {"MM": 0x3000, "DCC": 0x3800}
ACCESSORY_RANGE = 0x0400  # 1024 addresses per range
# Address 1 -> base + 0. The spec's own example is ambiguous, but the club's
# LocoNet_CS_Bridge v2.1 uses exactly this mapping and works on the real CS3.
ADDRESS_OFFSET = 1

# Accessory positions: 0 = red / round / diverging, 1 = green / straight
POSITION_RED = 0
POSITION_GREEN = 1


def make_hash(uid):
    """The sender hash, built from a 32-bit UID the way the spec describes.

    XOR the high and low 16 bits, then force bits 9-7 to 0b110. That bit
    pattern marks the frame as "new" CS2 protocol, never CS1.
    """
    value = ((uid >> 16) ^ uid) & 0xFFFF
    return (value & ~0x0380) | 0x0300


# Switchboard's own made-up UID ("SWB1" in ASCII) and the hash derived from it.
MY_UID = 0x53574231
MY_HASH = make_hash(MY_UID)


@dataclass
class Frame:
    command: int
    response: bool
    hash_code: int
    data: bytes

    def to_bytes(self):
        if len(self.data) > 8:
            raise ValueError(f"at most 8 data bytes, got {len(self.data)}")
        can_id = (self.command << 17) | (int(self.response) << 16) | self.hash_code
        return (can_id.to_bytes(4, "big")
                + bytes([len(self.data)])
                + self.data.ljust(8, b"\x00"))

    @classmethod
    def from_bytes(cls, raw):
        can_id = int.from_bytes(raw[0:4], "big")
        command = (can_id >> 17) & 0xFF
        response = bool((can_id >> 16) & 1)
        hash_code = can_id & 0xFFFF
        dlc = min(raw[4], 8)
        return cls(command, response, hash_code, bytes(raw[5:5 + dlc]))


# ----------------------------------------------------------------- building
def system_frame(sub_command, uid=0):
    """Stop/go/halt. uid 0 means 'everybody'."""
    data = uid.to_bytes(4, "big") + bytes([sub_command])
    return Frame(CMD_SYSTEM, False, MY_HASH, data)


def accessory_uid(address, protocol="DCC"):
    if protocol not in ACCESSORY_BASES:
        raise ValueError(f"protocol must be 'DCC' or 'MM', not {protocol!r}")
    index = address - ADDRESS_OFFSET
    if not 0 <= index < ACCESSORY_RANGE:
        raise ValueError(f"accessory address out of range: {address}")
    return ACCESSORY_BASES[protocol] + index


def accessory_frame(address, position, current, protocol="DCC", switch_time=0):
    """position: 0 = red/diverging, 1 = green/straight. current: 1 = on, 0 = off.

    switch_time (10 ms units): 0 -> DLC 6, the CS3 uses its default timeout or
    waits for our OFF. > 0 -> DLC 8, the CS3 switches the coil off itself after
    that time. The club bridge uses 10 (= 100 ms) and needs no OFF frame.
    """
    uid = accessory_uid(address, protocol)
    data = uid.to_bytes(4, "big") + bytes([position, current])
    if switch_time:
        data += switch_time.to_bytes(2, "big")
    return Frame(CMD_ACCESSORY, False, MY_HASH, data)


def ping_frame():
    return Frame(CMD_PING, False, MY_HASH, b"")


def s88_query_frame(device, contact):
    """Ask for the current state of one feedback contact (answer has DLC 8)."""
    data = device.to_bytes(2, "big") + contact.to_bytes(2, "big")
    return Frame(CMD_S88_EVENT, False, MY_HASH, data)


# ----------------------------------------------------------------- decoding
@dataclass
class SystemCommand:
    uid: int
    sub_command: int
    response: bool

    @property
    def name(self):
        return SUB_NAMES.get(self.sub_command, f"sub 0x{self.sub_command:02x}")

    def __str__(self):
        target = "all" if self.uid == 0 else f"0x{self.uid:08x}"
        return f"SYSTEM {self.name} to {target}{' (confirm)' if self.response else ''}"


@dataclass
class AccessorySwitch:
    protocol: str        # "DCC", "MM" or "?" if the UID is in neither range
    address: int         # user-facing address, 0 if unknown
    uid: int             # raw UID, kept for checking the address mapping
    position: int        # 0 = red/diverging, 1 = green/straight
    current: int         # 0 = off, 1 = on
    response: bool
    switch_time: int = 0 # 10 ms units, only in DLC 8 frames

    def __str__(self):
        colour = {0: "red", 1: "green"}.get(self.position, f"pos {self.position}")
        power = "ON" if self.current else "OFF"
        timed = f" for {self.switch_time * 10} ms" if self.switch_time else ""
        confirm = " (confirm)" if self.response else ""
        return (f"ACCESSORY {self.protocol} {self.address} {colour} {power}{timed}{confirm}"
                f"  [uid 0x{self.uid:04x}]")


@dataclass
class FeedbackEvent:
    device: int          # 0 = CS3 internal s88; Link S88 has its own id
    contact: int         # Link S88: bus * 1000 + (module - 1) * 16 + input
    old_state: int
    new_state: int       # 1 = occupied / contact closed
    time: int            # time since last change, in units of 10 ms

    def __str__(self):
        return (f"FEEDBACK device {self.device} contact {self.contact}: "
                f"{self.old_state} -> {self.new_state}")


@dataclass
class PingReply:
    uid: int
    version: str
    device_type: int     # 0xFFFF = CS2/CS3 GUI (master)

    def __str__(self):
        return f"PING REPLY uid 0x{self.uid:08x} version {self.version} device 0x{self.device_type:04x}"


def decode(frame):
    """Turn a Frame into one of the classes above, or None if not understood."""
    data = frame.data

    if frame.command == CMD_SYSTEM and len(data) >= 5:
        uid = int.from_bytes(data[0:4], "big")
        return SystemCommand(uid, data[4], frame.response)

    if frame.command == CMD_ACCESSORY and len(data) >= 6:
        uid = int.from_bytes(data[0:4], "big")
        protocol, address = "?", 0
        for name, base in ACCESSORY_BASES.items():
            if base <= uid < base + ACCESSORY_RANGE:
                protocol, address = name, uid - base + ADDRESS_OFFSET
        switch_time = int.from_bytes(data[6:8], "big") if len(data) >= 8 else 0
        return AccessorySwitch(protocol, address, uid, data[4], data[5], frame.response,
                               switch_time)

    if frame.command == CMD_S88_EVENT and len(data) == 8:
        return FeedbackEvent(
            device=int.from_bytes(data[0:2], "big"),
            contact=int.from_bytes(data[2:4], "big"),
            old_state=data[4],
            new_state=data[5],
            time=int.from_bytes(data[6:8], "big"),
        )

    if frame.command == CMD_PING and frame.response and len(data) == 8:
        return PingReply(
            uid=int.from_bytes(data[0:4], "big"),
            version=f"{data[4]}.{data[5]}",
            device_type=int.from_bytes(data[6:8], "big"),
        )

    return None


# ----------------------------------------------------------------- framing
class Framer:
    """Cuts a TCP byte stream into 13-byte frames.

    Much simpler than LocoNet: every frame has the same length, and TCP
    never loses or corrupts bytes, so no resync is needed.
    """

    def __init__(self):
        self.buffer = bytearray()

    def feed(self, data):
        self.buffer += data
        frames = []
        while len(self.buffer) >= FRAME_SIZE:
            frames.append(Frame.from_bytes(bytes(self.buffer[:FRAME_SIZE])))
            del self.buffer[:FRAME_SIZE]
        return frames
