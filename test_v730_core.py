import tempfile
import unittest
from pathlib import Path

from outerclient_v730_duplicates import physical_key, suggested_keeper, maven_range_result
from outerclient_v730_versions import load_cache, save_cache


class Core730Tests(unittest.TestCase):
    def test_physical_identity(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "sodium.jar"
            path.write_bytes(b"jar")
            self.assertEqual(physical_key(path), physical_key(path))

    def test_unambiguous_keeper(self):
        records = [
            {"path": "good", "compatibility": "compatible"},
            {"path": "bad", "compatibility": "incompatible"},
        ]
        self.assertEqual(suggested_keeper(records), "good")
        records[1]["compatibility"] = "unknown"
        self.assertIsNone(suggested_keeper(records))

    def test_two_compatible_need_choice(self):
        self.assertIsNone(suggested_keeper([
            {"path": "a", "compatibility": "compatible"},
            {"path": "b", "compatibility": "compatible"},
        ]))

    def test_cache_round_trip(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "versions.json"
            self.assertEqual(
                save_cache(["1.21.1", "1.21.1", "1.20.1"], path),
                ["1.21.1", "1.20.1"],
            )
            self.assertEqual(load_cache(path), ["1.21.1", "1.20.1"])

    def test_maven_range(self):
        self.assertTrue(maven_range_result("1.20.1", "[1.20,1.21)"))
        self.assertFalse(maven_range_result("1.21", "[1.20,1.21)"))
        self.assertIsNone(maven_range_result("1.20.1", "???"))


if __name__ == "__main__":
    unittest.main()
