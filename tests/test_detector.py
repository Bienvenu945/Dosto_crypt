import os
import unittest

from core import detector as d


class Detection(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(d.detect_content(b"").kind, d.KIND_EMPTY)

    def test_signatures(self):
        cases = {
            b"\x89PNG\r\n\x1a\n" + b"\x00" * 8: "PNG",
            b"%PDF-1.7\n": "PDF",
            b"PK\x03\x04rest": "ZIP",
            b"\x7fELF\x02\x01": "ELF",
            b"\xff\xd8\xff\xe0": "JPEG",
        }
        for data, label in cases.items():
            with self.subTest(label=label):
                result = d.detect_content(data)
                self.assertEqual(result.kind, d.KIND_SIGNATURE)
                self.assertIn(label, result.description)

    def test_pe_executable(self):
        data = bytearray(128)
        data[:2] = b"MZ"
        data[0x3C:0x40] = (0x40).to_bytes(4, "little")
        data[0x40:0x44] = b"PE\x00\x00"
        self.assertIn("PE", d.detect_content(bytes(data)).description)

    def test_mz_text_is_not_pe(self):
        self.assertEqual(d.detect_content(b"MZ is just text").kind, d.KIND_UTF8)

    def test_hex_text(self):
        self.assertEqual(d.detect_content(b"426f6e6a6f7572\n").kind, d.KIND_HEX_TEXT)

    def test_binary_text(self):
        self.assertEqual(d.detect_content(b"01000010 01101111").kind, d.KIND_BINARY_TEXT)

    def test_utf8_text(self):
        self.assertEqual(d.detect_content("Bonjour é€".encode()).kind, d.KIND_UTF8)

    def test_binary_data(self):
        self.assertEqual(d.detect_content(bytes(range(256))).kind, d.KIND_BINARY)

    def test_truncated_utf8_still_text(self):
        data = ("é" * 50).encode()[:-1]
        self.assertTrue(d.is_probably_text(data))


class Analysis(unittest.TestCase):
    def test_entropy_bounds(self):
        self.assertEqual(d.shannon_entropy(b"\x00" * 100), 0.0)
        self.assertAlmostEqual(d.shannon_entropy(bytes(range(256))), 8.0)
        self.assertEqual(d.shannon_entropy(b""), 0.0)

    def test_analyze_counts(self):
        result = d.analyze(b"ab\x00\x00")
        self.assertEqual(result.size, 4)
        self.assertEqual(result.null_bytes, 2)
        self.assertEqual(result.unique_bytes, 3)
        self.assertAlmostEqual(result.printable_ratio, 0.5)

    def test_entropy_labels(self):
        self.assertIn("Très faible", d.describe_entropy(0.2))
        self.assertIn("Élevée", d.describe_entropy(7.9))

    def test_random_data_has_high_entropy(self):
        self.assertGreater(d.analyze(os.urandom(65536)).entropy, 7.9)


if __name__ == "__main__":
    unittest.main()
