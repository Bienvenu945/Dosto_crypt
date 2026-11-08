import unittest

from core import converter as c


class TextToRepresentation(unittest.TestCase):
    def test_hex_example_from_readme(self):
        self.assertEqual(c.text_to_hex("Bonjour"), "426f6e6a6f7572")

    def test_binary_example_from_readme(self):
        expected = (
            "01000010 01101111 01101110 01101010\n"
            "01101111 01110101 01110010"
        )
        self.assertEqual(c.text_to_binary("Bonjour", bytes_per_line=4), expected)

    def test_hex_separator_and_wrapping(self):
        self.assertEqual(c.text_to_hex("abcd", separator=" "), "61 62 63 64")
        self.assertEqual(c.text_to_hex("abcd", bytes_per_line=2), "6162\n6364")

    def test_empty_text_rejected(self):
        with self.assertRaises(c.ConversionError):
            c.text_to_hex("")

    def test_unencodable_surrogate_rejected(self):
        with self.assertRaises(c.ConversionError):
            c.text_to_bytes("\ud800")


class RepresentationToText(unittest.TestCase):
    def test_hex_tolerates_spaces_newlines_prefix_and_case(self):
        self.assertEqual(c.hex_to_text("0x42 6F\n6e 6A 6f 75 72"), "Bonjour")

    def test_binary_tolerates_whitespace(self):
        self.assertEqual(c.binary_to_text("01000010\n01101111"), "Bo")

    def test_invalid_hex_char(self):
        with self.assertRaises(c.ConversionError):
            c.hex_to_bytes("zz")

    def test_odd_hex_length(self):
        with self.assertRaises(c.ConversionError):
            c.hex_to_bytes("abc")

    def test_binary_not_multiple_of_8(self):
        with self.assertRaises(c.ConversionError):
            c.binary_to_bytes("0100001")

    def test_binary_invalid_char(self):
        with self.assertRaises(c.ConversionError):
            c.binary_to_bytes("0100002")

    def test_empty_inputs(self):
        for func in (c.hex_to_bytes, c.binary_to_bytes):
            with self.assertRaises(c.ConversionError):
                func("  \n ")

    def test_invalid_utf8_bytes(self):
        with self.assertRaises(c.ConversionError):
            c.bytes_to_text(b"\xff\xfe\x00")


class Roundtrip(unittest.TestCase):
    SAMPLES = ["Bonjour", "é à ç ñ €", "日本語のテキスト", "😀🚀 emoji", "ligne1\nligne2\ttab", "[rich] {markup}"]

    def test_roundtrip_all_formats(self):
        for text in self.SAMPLES:
            for fmt in c.SUPPORTED_FORMATS:
                with self.subTest(text=text, fmt=fmt):
                    encoded = c.encode_text(text, fmt, bytes_per_line=4)
                    decoded = c.bytes_to_text(c.decode_representation(encoded, fmt))
                    self.assertEqual(decoded, text)

    def test_unknown_format(self):
        with self.assertRaises(c.ConversionError):
            c.encode_text("a", "base64")
        with self.assertRaises(c.ConversionError):
            c.decode_representation("a", "base64")


if __name__ == "__main__":
    unittest.main()
