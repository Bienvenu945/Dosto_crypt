import unittest

from core import hexdump as h


class Hexdump(unittest.TestCase):
    def test_full_line_format(self):
        line = str(next(h.iter_hexlines(b"Bonjour tout le monde"[:16])))
        self.assertEqual(
            line,
            "00000000  42 6f 6e 6a 6f 75 72 20  74 6f 75 74 20 6c 65 20  |Bonjour tout le |",
        )

    def test_partial_line_keeps_alignment(self):
        full = str(h.HexLine(0, b"A" * 16))
        short = str(h.HexLine(0, b"AB"))
        self.assertEqual(full.index("|"), short.index("|"))
        self.assertTrue(short.endswith("|AB|"))

    def test_offsets_and_start_offset(self):
        lines = list(h.iter_hexlines(bytes(40), start_offset=0x100))
        self.assertEqual([l.offset for l in lines], [0x100, 0x110, 0x120])

    def test_non_printable_shown_as_dot(self):
        self.assertEqual(h.ascii_repr(b"a\x00\n\xffZ"), "a...Z")

    def test_preview_limits_bytes(self):
        lines = h.preview(bytes(200), count=40, width=16)
        self.assertEqual(sum(len(l.data) for l in lines), 40)

    def test_custom_width(self):
        self.assertEqual(len(h.format_hexdump(bytes(16), width=8).splitlines()), 2)
        with self.assertRaises(ValueError):
            list(h.iter_hexlines(b"a", width=0))


if __name__ == "__main__":
    unittest.main()
