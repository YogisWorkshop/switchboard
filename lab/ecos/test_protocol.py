"""Unit tests for protocol.py, using real lines captured from the club ECoS."""

import unittest

import protocol


class TestSplitOutsideQuotes(unittest.TestCase):

    def test_plain_spaces(self):
        result = protocol.split_outside_quotes("a b c", " ")
        self.assertEqual(result, ["a", "b", "c"])

    def test_space_inside_quotes_is_kept(self):
        result = protocol.split_outside_quotes('1005 name["RhB Ge4/4II 612"]', " ")
        self.assertEqual(result, ["1005", 'name["RhB Ge4/4II 612"]'])

    def test_space_inside_brackets_is_kept(self):
        result = protocol.split_outside_quotes("1000 func[0, 1]", " ")
        self.assertEqual(result, ["1000", "func[0, 1]"])


class TestUnquote(unittest.TestCase):

    def test_removes_outer_quotes(self):
        self.assertEqual(protocol.unquote('"Köf 4402"'), "Köf 4402")

    def test_doubled_quote_becomes_single(self):
        self.assertEqual(protocol.unquote('"The ""Big"" Boy"'), 'The "Big" Boy')

    def test_unquoted_value_unchanged(self):
        self.assertEqual(protocol.unquote("STOP"), "STOP")


class TestParseEntry(unittest.TestCase):

    def test_loco_name(self):
        obj_id, options = protocol.parse_entry('1005 name["RhB Ge4/4II 612"]')
        self.assertEqual(obj_id, 1005)
        self.assertEqual(options, {"name": ["RhB Ge4/4II 612"]})

    def test_utf8_name(self):
        obj_id, options = protocol.parse_entry('1020 name["1293 011 ÖBB"]')
        self.assertEqual(options["name"], ["1293 011 ÖBB"])

    def test_two_options(self):
        obj_id, options = protocol.parse_entry('1000 name["SBBC 421 378-1"] addr[0]')
        self.assertEqual(options["name"], ["SBBC 421 378-1"])
        self.assertEqual(options["addr"], ["0"])

    def test_bare_word(self):
        obj_id, options = protocol.parse_entry("1 ECoS2")
        self.assertEqual(options, {"ECoS2": []})

    def test_turnout_event_line(self):
        obj_id, options = protocol.parse_entry("20000 switching[1]")
        self.assertEqual(obj_id, 20000)
        self.assertEqual(options, {"switching": ["1"]})

    def test_several_arguments(self):
        obj_id, options = protocol.parse_entry("1000 func[0, 1]")
        self.assertEqual(options["func"], ["0", "1"])


class TestParseEnd(unittest.TestCase):

    def test_ok(self):
        self.assertEqual(protocol.parse_end("<END 0 (OK)>"), (0, "OK"))

    def test_ok_with_note(self):
        code, text = protocol.parse_end("<END 0 (OK, but obsolete option at 8)>")
        self.assertEqual(code, 0)
        self.assertEqual(text, "OK, but obsolete option at 8")

    def test_error(self):
        code, text = protocol.parse_end("<END 21 (integer out of range at 9)>")
        self.assertEqual(code, 21)


class TestParseMessage(unittest.TestCase):

    def test_reply(self):
        lines = ["<REPLY get(1, status)>", "1 status[STOP]", "<END 0 (OK)>"]
        message = protocol.parse_message(lines)
        self.assertEqual(message.kind, "REPLY")
        self.assertEqual(message.header, "get(1, status)")
        self.assertEqual(message.entries, [(1, {"status": ["STOP"]})])
        self.assertTrue(message.ok)

    def test_error_reply_has_no_entries(self):
        lines = ["<REPLY get(99999, name)>", "<END 21 (integer out of range at 9)>"]
        message = protocol.parse_message(lines)
        self.assertEqual(message.entries, [])
        self.assertFalse(message.ok)

    def test_event_with_two_lines(self):
        lines = ["<EVENT 1>", "1 status2[NONE]", "1 status[STOP]", "<END 0 (OK)>"]
        message = protocol.parse_message(lines)
        self.assertEqual(message.kind, "EVENT")
        self.assertEqual(message.header, "1")
        self.assertEqual(len(message.entries), 2)

    def test_garbage_raises(self):
        with self.assertRaises(ValueError):
            protocol.parse_message(["hello", "<END 0 (OK)>"])


if __name__ == "__main__":
    unittest.main()