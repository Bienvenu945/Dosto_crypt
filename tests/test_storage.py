import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core import storage


class StorageCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        patcher = mock.patch.dict(os.environ, {"DOSTO_CRYPT_HOME": str(self.dir / "home")})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._tmp.cleanup)


class Settings(StorageCase):
    def test_defaults_then_roundtrip(self):
        self.assertEqual(storage.load_settings(), storage.DEFAULT_SETTINGS)
        settings = dict(storage.DEFAULT_SETTINGS, accent="green", hexdump_width=8)
        self.assertTrue(storage.save_settings(settings))
        self.assertEqual(storage.load_settings(), settings)

    def test_invalid_values_fall_back(self):
        storage.app_home().mkdir(parents=True)
        storage.settings_path().write_text(json.dumps({"accent": "pink", "hexdump_width": 99, "output_dir": 3}))
        self.assertEqual(storage.load_settings(), storage.DEFAULT_SETTINGS)

    def test_corrupted_file_falls_back(self):
        storage.app_home().mkdir(parents=True)
        storage.settings_path().write_text("{not json")
        self.assertEqual(storage.load_settings(), storage.DEFAULT_SETTINGS)


class History(StorageCase):
    def test_add_load_clear(self):
        self.assertEqual(storage.load_history(), [])
        self.assertTrue(storage.add_history("Texte → Hexadécimal", "texte", "a.hex", 7, "abc"))
        entries = storage.load_history()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].operation, "Texte → Hexadécimal")
        self.assertEqual(entries[0].size, 7)
        self.assertTrue(storage.clear_history())
        self.assertEqual(storage.load_history(), [])

    def test_limit(self):
        with mock.patch.object(storage, "HISTORY_LIMIT", 3):
            for i in range(5):
                storage.add_history("op", f"s{i}")
        self.assertEqual([e.source for e in storage.load_history()], ["s2", "s3", "s4"])

    def test_corrupted_and_partial_rows_ignored(self):
        storage.app_home().mkdir(parents=True)
        storage.history_path().write_text(json.dumps([{"bad": 1}, "x", {
            "timestamp": "t", "operation": "o", "source": "s", "target": "-", "size": 1}]))
        self.assertEqual(len(storage.load_history()), 1)
        storage.history_path().write_text("garbage")
        self.assertEqual(storage.load_history(), [])

    def test_export_json_and_csv(self):
        storage.add_history("op", "é", "t", 3)
        out_json = storage.export_history(self.dir / "h.json", "json")
        self.assertEqual(json.loads(out_json.read_text(encoding="utf-8"))[0]["source"], "é")
        out_csv = storage.export_history(self.dir / "x" / "h.csv", "csv")
        self.assertIn("timestamp,operation", out_csv.read_text(encoding="utf-8"))
        with self.assertRaises(storage.StorageError):
            storage.export_history(self.dir / "h.xml", "xml")

    def test_unwritable_home_is_not_fatal(self):
        blocker = self.dir / "blocker"
        blocker.write_text("file, not dir")
        with mock.patch.dict(os.environ, {"DOSTO_CRYPT_HOME": str(blocker / "sub")}):
            self.assertFalse(storage.add_history("op", "s"))


if __name__ == "__main__":
    unittest.main()
