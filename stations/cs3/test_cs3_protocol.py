"""Unit tests for cs3_protocol.py. Run: python3 -m unittest -v

Test frames come from the Märklin CS2 CAN protocol 2.0 document and from a
published capture of a real S88 event.
"""

import unittest

from stations.cs3 import cs3_protocol as p


class TestHash(unittest.TestCase):

    def test_bits_9_to_7_are_110(self):
        for uid in (0, 0x53574231, 0xFFFFFFFF, 0x12345678, 0x43533208):
            self.assertEqual((p.make_hash(uid) >> 7) & 0b111, 0b110)

    def test_spec_example_hash_has_the_pattern(self):
        self.assertEqual((0x4711 >> 7) & 0b111, 0b110)


class TestFrame(unittest.TestCase):

    def test_ping_matches_spec_layout(self):
        frame = p.Frame(p.CMD_PING, False, 0x4711, b"")
        self.assertEqual(frame.to_bytes().hex(" "), "00 30 47 11 00 00 00 00 00 00 00 00 00")

    def test_halt_matches_spec_example(self):
        # spec: 00004711 5 00 00 00 00 02  (halt to all)
        frame = p.Frame(p.CMD_SYSTEM, False, 0x4711, bytes([0, 0, 0, 0, p.SUB_HALT]))
        self.assertEqual(frame.to_bytes().hex(" "), "00 00 47 11 05 00 00 00 00 02 00 00 00")

    def test_response_bit(self):
        frame = p.Frame(p.CMD_ACCESSORY, True, 0x4711, bytes(6))
        self.assertEqual(frame.to_bytes()[1], 0x17)

    def test_round_trip(self):
        frame = p.Frame(p.CMD_ACCESSORY, True, 0x2b7f, bytes([0, 0, 0x38, 4, 1, 0]))
        self.assertEqual(p.Frame.from_bytes(frame.to_bytes()), frame)

    def test_frame_is_always_13_bytes(self):
        self.assertEqual(len(p.ping_frame().to_bytes()), 13)

    def test_too_much_data_rejected(self):
        with self.assertRaises(ValueError):
            p.Frame(p.CMD_SYSTEM, False, 0x4711, bytes(9)).to_bytes()


class TestBuilders(unittest.TestCase):

    def test_dcc_accessory_1_green_on(self):
        raw = p.accessory_frame(1, p.POSITION_GREEN, 1, "DCC").to_bytes()
        self.assertEqual(raw[1], 0x16)                    # command 0x0B, no response bit
        self.assertEqual(raw[4], 6)                       # DLC 6
        self.assertEqual(raw[5:11].hex(" "), "00 00 38 00 01 01")

    def test_mm_accessory_uid(self):
        self.assertEqual(p.accessory_uid(3, "MM"), 0x3002)

    def test_bad_protocol(self):
        with self.assertRaises(ValueError):
            p.accessory_uid(1, "SX")

    def test_bad_address(self):
        with self.assertRaises(ValueError):
            p.accessory_uid(0, "DCC")
        with self.assertRaises(ValueError):
            p.accessory_uid(1025, "DCC")

    def test_stop_to_everyone(self):
        raw = p.system_frame(p.SUB_STOP).to_bytes()
        self.assertEqual(raw[4:10].hex(" "), "05 00 00 00 00 00")

    def test_s88_query(self):
        raw = p.s88_query_frame(0, 1).to_bytes()
        self.assertEqual(raw[1], 0x22)
        self.assertEqual(raw[4:9].hex(" "), "04 00 00 00 01")


class TestBridgeCompatibility(unittest.TestCase):
    """Frames exactly as LocoNet_CS_Bridge v2.1 sends them (hash 0x0300)."""

    BRIDGE_DCC_1_RED = "00 16 03 00 08 00 00 38 00 00 01 00 0a"   # LocoNet addr 1 thrown
    BRIDGE_MM_1_RED = "00 16 03 00 08 00 00 30 00 00 01 00 0a"

    def test_bridge_frame_decodes(self):
        frame = p.Frame.from_bytes(bytes.fromhex(self.BRIDGE_DCC_1_RED))
        self.assertEqual(frame.hash_code, 0x0300)
        decoded = p.decode(frame)
        self.assertEqual((decoded.protocol, decoded.address), ("DCC", 1))
        self.assertEqual((decoded.position, decoded.current, decoded.switch_time), (0, 1, 10))

    def test_our_frame_matches_bridge_apart_from_hash(self):
        for protocol, expected in (("DCC", self.BRIDGE_DCC_1_RED), ("MM", self.BRIDGE_MM_1_RED)):
            ours = p.accessory_frame(1, p.POSITION_RED, 1, protocol, switch_time=10).to_bytes()
            bridge = bytes.fromhex(expected)
            self.assertEqual(ours[:2] + ours[4:], bridge[:2] + bridge[4:])

    def test_bridge_hash_has_the_pattern(self):
        self.assertEqual((0x0300 >> 7) & 0b111, 0b110)


class TestDecode(unittest.TestCase):

    def test_real_s88_event(self):
        # Published capture: Link S88, bus 2, module 2, contact 13 -> 2029, closed
        frame = p.Frame.from_bytes(bytes.fromhex("00 23 47 06 08 00 01 07 ED 00 01 08 86"))
        self.assertEqual(frame.command, p.CMD_S88_EVENT)
        self.assertTrue(frame.response)
        self.assertEqual(p.decode(frame), p.FeedbackEvent(1, 2029, 0, 1, 0x0886))

    def test_accessory_round_trip(self):
        frame = p.accessory_frame(42, p.POSITION_RED, 1, "MM")
        decoded = p.decode(frame)
        self.assertEqual((decoded.protocol, decoded.address), ("MM", 42))
        self.assertEqual((decoded.position, decoded.current), (0, 1))

    def test_accessory_outside_known_ranges(self):
        frame = p.Frame(p.CMD_ACCESSORY, True, 0x4711, bytes([0, 0, 0x28, 0, 1, 1]))
        self.assertEqual(p.decode(frame).protocol, "?")

    def test_system_stop(self):
        decoded = p.decode(p.system_frame(p.SUB_STOP))
        self.assertEqual(decoded.name, "STOP")

    def test_ping_reply(self):
        frame = p.Frame(p.CMD_PING, True, 0x4711, bytes([0x43, 0x53, 0x33, 0x01, 2, 5, 0xFF, 0xFF]))
        self.assertEqual(p.decode(frame), p.PingReply(0x43533301, "2.5", 0xFFFF))

    def test_unknown_command(self):
        self.assertIsNone(p.decode(p.Frame(0x36, False, 0x4711, b"")))


class TestFramer(unittest.TestCase):

    def test_split_and_joined(self):
        a = p.ping_frame().to_bytes()
        b = p.system_frame(p.SUB_GO).to_bytes()
        framer = p.Framer()
        self.assertEqual(framer.feed(a[:5]), [])
        frames = framer.feed(a[5:] + b + a[:3])
        self.assertEqual([f.command for f in frames], [p.CMD_PING, p.CMD_SYSTEM])
        self.assertEqual(len(framer.feed(a[3:])), 1)


if __name__ == "__main__":
    unittest.main()
