"""LocoNet protocol: turning a stream of bytes into messages. No serial port here."""
from dataclasses import dataclass

def message_length(message):
    size_bits = (message[0] >> 5) & 0b11
    if size_bits == 0b00:
        return 2
    if size_bits == 0b01:
        return 4
    if size_bits == 0b10:
        return 6
    if len(message) < 2:
        return None
    return message[1]


def checksum_ok(message):
    result = 0
    for byte in message:
        result ^= byte
    return result == 0xFF


class Framer:
    def __init__(self):
        self.buffer = bytearray()

    def feed(self, data):
        self.buffer += data
        messages = []
        while True:
            while self.buffer and self.buffer[0] < 0x80:
                del self.buffer[0]
            if not self.buffer:
                break
            length = message_length(self.buffer)
            if length is None:
                break
            if length < 2 or any(byte >= 0x80 for byte in self.buffer[1:length]):
                del self.buffer[0]
                continue
            if len(self.buffer) < length:
                break
            messages.append(bytes(self.buffer[:length]))
            del self.buffer[:length]
        return messages

OPC_SW_REQ = 0xB0
OPC_INPUT_REP = 0xB2

def with_checksum(body):
    checksum = 0xFF
    for byte in body:
        checksum ^= byte
    return bytes(body) + bytes([checksum])

@dataclass
class SwitchRequest:
    address: int
    closed: bool
    on: bool

    def to_bytes(self):
        if not 1 <= self.address <= 2048:
            raise ValueError(f"turnout address must be 1-2048, not {self.address}")
        raw = self.address - 1
        sw1 = raw & 0x7F
        sw2 = (raw >> 7) & 0x0F
        if self.closed:
            sw2 |= 0x20
        if self.on:
            sw2 |= 0x10
        return with_checksum([OPC_SW_REQ, sw1, sw2])

@dataclass
class SensorReport:
    address: int
    occupied: bool


def decode(message):
    opcode = message[0]
    if opcode == OPC_SW_REQ:
        sw1 = message[1]
        sw2 = message[2]
        address = (((sw2 & 0x0F) << 7) | sw1) + 1
        closed = bool(sw2 & 0x20)
        on = bool(sw2 & 0x10)
        return SwitchRequest(address, closed, on)
    if opcode == OPC_INPUT_REP:
        in1 = message[1]
        in2 = message[2]
        address = (((in2 & 0x0F) << 8) | (in1 << 1) | ((in2 & 0x20) >> 5)) + 1
        occupied = bool(in2 & 0x10)
        return SensorReport(address, occupied)
    return None

if __name__ == "__main__":
    framer = Framer()
    tests = [
        "b0 00 30 7f b0 00 20 6f",   # two messages in one read
        "b2 3a",                     # first half of a message...
        "50 27",                     # ...and the second half
        "3a 50 b2 3a 40 37",         # junk before an opcode
        "b0 01 b2 3a 50 27",         # a message cut short by a new opcode
    ]
    for chunk in tests:
        messages = framer.feed(bytes.fromhex(chunk))
        print(f"{chunk:<26} -> {[m.hex(' ') for m in messages]}")