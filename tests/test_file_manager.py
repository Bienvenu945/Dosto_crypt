import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core import file_manager as fm


class FileManagerCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()


class SaveAndLoad(FileManagerCase):
    DATA = "Bonjour é€ 😀".encode()

    def test_save_hex_and_roundtrip(self):
        result = fm.save_output(self.dir / "a.hex", self.DATA, fm.KIND_HEX)
        self.assertTrue(result.verified)
        self.assertEqual(result.sha256, hashlib.sha256(self.DATA).hexdigest())
        self.assertEqual(fm.load_file(result.path).data, self.DATA)
        self.assertEqual(fm.load_file(result.path).source, fm.SRC_HEX)

    def test_save_bin_is_raw(self):
        result = fm.save_output(self.dir / "a.bin", self.DATA, fm.KIND_BIN)
        self.assertEqual(result.path.read_bytes(), self.DATA)
        self.assertTrue(result.verified)

    def test_save_bits_autodetected_on_reload(self):
        result = fm.save_output(self.dir / "bits.txt", self.DATA, fm.KIND_BITS)
        loaded = fm.load_file(result.path)
        self.assertEqual(loaded.source, fm.SRC_BINARY)
        self.assertEqual(loaded.data, self.DATA)

    def test_extract_text_from_each_format(self):
        for kind, name in ((fm.KIND_HEX, "t.hex"), (fm.KIND_BIN, "t.bin"), (fm.KIND_BITS, "t.txt")):
            with self.subTest(kind=kind):
                fm.save_output(self.dir / name, self.DATA, kind)
                text, _ = fm.extract_text(self.dir / name)
                self.assertEqual(text, self.DATA.decode())

    def test_save_text_utf8(self):
        result = fm.save_text(self.dir / "t.txt", "ligne1\nligne2 é")
        self.assertTrue(result.verified)
        self.assertEqual(result.path.read_text(encoding="utf-8"), "ligne1\nligne2 é")

    def test_no_overwrite_by_default(self):
        fm.save_output(self.dir / "a.hex", self.DATA, fm.KIND_HEX)
        with self.assertRaises(fm.FileAlreadyExistsError):
            fm.save_output(self.dir / "a.hex", b"x", fm.KIND_HEX)
        fm.save_output(self.dir / "a.hex", b"x", fm.KIND_HEX, overwrite=True)
        self.assertEqual(fm.load_file(self.dir / "a.hex").data, b"x")

    def test_creates_missing_directory_and_leaves_no_tmp(self):
        target = self.dir / "sub" / "deep" / "a.hex"
        fm.save_output(target, b"abc", fm.KIND_HEX)
        self.assertTrue(target.exists())
        self.assertEqual([p.name for p in target.parent.iterdir()], ["a.hex"])

    def test_empty_data_rejected(self):
        with self.assertRaises(fm.FileManagerError):
            fm.save_output(self.dir / "e.hex", b"", fm.KIND_HEX)

    def test_unknown_kind_rejected(self):
        with self.assertRaises(fm.FileManagerError):
            fm.save_output(self.dir / "x", b"a", "zip")


class ReadErrors(FileManagerCase):
    def test_missing_file(self):
        with self.assertRaises(fm.FileManagerError):
            fm.load_file(self.dir / "nope.bin")

    def test_directory_is_not_a_file(self):
        with self.assertRaises(fm.FileManagerError):
            fm.load_file(self.dir)

    def test_empty_file(self):
        (self.dir / "e.bin").write_bytes(b"")
        with self.assertRaises(fm.FileManagerError):
            fm.load_file(self.dir / "e.bin")

    def test_corrupted_hex_file(self):
        (self.dir / "bad.hex").write_text("zz12")
        with self.assertRaises(fm.FileManagerError):
            fm.load_file(self.dir / "bad.hex")

    def test_non_ascii_hex_file(self):
        (self.dir / "bad.hex").write_bytes("é".encode())
        with self.assertRaises(fm.FileManagerError):
            fm.load_file(self.dir / "bad.hex")

    def test_non_text_extraction_gives_hint(self):
        (self.dir / "x.bin").write_bytes(b"\xff\xfe\x00\x01")
        with self.assertRaises(fm.FileManagerError) as ctx:
            fm.extract_text(self.dir / "x.bin")
        self.assertIn("Hex Viewer", str(ctx.exception))

    def test_quoted_path_is_cleaned(self):
        (self.dir / "q.bin").write_bytes(b"hi")
        self.assertEqual(fm.read_bytes(f'"{self.dir / "q.bin"}"'), b"hi")

    def test_read_range(self):
        (self.dir / "r.bin").write_bytes(bytes(range(100)))
        self.assertEqual(fm.read_range(self.dir / "r.bin", 10, 5), bytes(range(10, 15)))


class StreamingAndBatch(FileManagerCase):
    def test_convert_file_multi_chunk(self):
        data = bytes(range(256)) * 3  # 768 octets
        src = self.dir / "src.bin"
        src.write_bytes(data)
        steps = []
        with mock.patch.object(fm, "CHUNK_SIZE", 64):
            for kind in fm.STREAM_KINDS:
                dst = self.dir / f"out_{kind}.txt"
                result = fm.convert_file(src, dst, kind, progress=lambda d, t: steps.append((d, t)))
                self.assertTrue(result.verified)
                source = fm.SRC_HEX if kind == fm.KIND_HEX else fm.SRC_BINARY
                self.assertEqual(fm.load_file(dst, source).data, data)
        self.assertEqual(steps[-1], (768, 768))
        self.assertGreater(len(steps), 12)

    def test_convert_file_guards(self):
        src = self.dir / "s.bin"
        src.write_bytes(b"abc")
        with self.assertRaises(fm.FileManagerError):
            fm.convert_file(src, src, fm.KIND_HEX, overwrite=True)  # même fichier
        with self.assertRaises(fm.FileManagerError):
            fm.convert_file(src, self.dir / "o.bin", fm.KIND_BIN)    # mauvais format
        fm.convert_file(src, self.dir / "o.hex", fm.KIND_HEX)
        with self.assertRaises(fm.FileAlreadyExistsError):
            fm.convert_file(src, self.dir / "o.hex", fm.KIND_HEX)
        (self.dir / "empty.bin").write_bytes(b"")
        with self.assertRaises(fm.FileManagerError):
            fm.convert_file(self.dir / "empty.bin", self.dir / "e.hex", fm.KIND_HEX)

    def test_batch_continues_after_error(self):
        src = self.dir / "in"
        src.mkdir()
        (src / "a.txt").write_text("Bonjour")
        (src / "b.txt").write_bytes(b"")  # vide -> erreur
        (src / "c.txt").write_text("Salut")
        files = fm.list_files(src, "*.txt")
        started = []
        results = fm.batch_convert(files, self.dir / "out", fm.KIND_HEX, on_start=started.append)
        self.assertEqual([r.ok for r in results], [True, False, True])
        self.assertEqual(len(started), 3)
        self.assertEqual(fm.load_file(self.dir / "out" / "a.txt.hex").data, b"Bonjour")
        self.assertFalse((self.dir / "out" / "b.txt.hex").exists())

    def test_list_files_filters_and_errors(self):
        (self.dir / "a.txt").write_text("x")
        (self.dir / "b.log").write_text("x")
        (self.dir / "sub").mkdir()
        self.assertEqual([p.name for p in fm.list_files(self.dir, "*.txt")], ["a.txt"])
        with self.assertRaises(fm.FileManagerError):
            fm.list_files(self.dir / "absent")


class InspectAndNames(FileManagerCase):
    def test_inspect_file(self):
        payload = b"%PDF-1.4\n" + b"hello" * 10
        (self.dir / "doc.pdf").write_bytes(payload)
        info = fm.inspect_file(self.dir / "doc.pdf")
        self.assertEqual(info.size, len(payload))
        self.assertEqual(info.sha256, hashlib.sha256(payload).hexdigest())
        self.assertIn("PDF", info.detection.description)
        self.assertEqual(info.extension, ".pdf")
        self.assertFalse(info.sampled)

    def test_human_size(self):
        self.assertEqual(fm.human_size(0), "0 o")
        self.assertEqual(fm.human_size(1536), "1.5 Ko")
        self.assertEqual(fm.human_size(5 * 1024**2), "5.0 Mo")

    def test_build_output_path(self):
        self.assertEqual(fm.build_output_path(self.dir, "data", fm.KIND_HEX), self.dir / "data.hex")
        self.assertEqual(fm.build_output_path(self.dir, "data.dat", fm.KIND_HEX), self.dir / "data.dat")
        with self.assertRaises(ValueError):
            fm.build_output_path(self.dir, "a/b", fm.KIND_HEX)
        with self.assertRaises(ValueError):
            fm.build_output_path(self.dir, "  ", fm.KIND_HEX)

    def test_default_filename(self):
        self.assertTrue(fm.default_filename(fm.KIND_HEX).endswith(".hex"))


if __name__ == "__main__":
    unittest.main()
