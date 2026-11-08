import unittest

from utils import validators as v


class Validators(unittest.TestCase):
    def test_clean_binary_and_hex(self):
        self.assertEqual(v.clean_binary("0100 0010\n"), "01000010")
        self.assertEqual(v.clean_hex("0xAB cd"), "abcd")

    def test_is_valid(self):
        self.assertTrue(v.is_valid_hex("de ad be ef"))
        self.assertFalse(v.is_valid_hex("xyz"))
        self.assertTrue(v.is_valid_binary("10101010"))
        self.assertFalse(v.is_valid_binary("1010"))

    def test_error_messages_are_specific(self):
        with self.assertRaisesRegex(v.ValidationError, "multiple de 8"):
            v.clean_binary("101")
        with self.assertRaisesRegex(v.ValidationError, "pair"):
            v.clean_hex("abc")

    def test_filename(self):
        self.assertEqual(v.validate_filename(" out ", ".hex"), "out.hex")
        self.assertEqual(v.validate_filename("out.dat", ".hex"), "out.dat")
        for bad in ("", "..", "a/b", "a:b", "a*b"):
            with self.subTest(bad=bad), self.assertRaises(v.ValidationError):
                v.validate_filename(bad)

    def test_parse_int(self):
        self.assertEqual(v.parse_int("128"), 128)
        self.assertEqual(v.parse_int("0x80"), 128)
        self.assertEqual(v.parse_int("010"), 10)
        with self.assertRaises(v.ValidationError):
            v.parse_int("abc")
        with self.assertRaises(v.ValidationError):
            v.parse_int("-1")
        with self.assertRaises(v.ValidationError):
            v.parse_int("11", maximum=10)


if __name__ == "__main__":
    unittest.main()
