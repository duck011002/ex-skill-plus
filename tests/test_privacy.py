import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from privacy_scan import scan


class PrivacyTests(unittest.TestCase):
    def test_clean_synthetic_tree_has_no_findings(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "README.md").write_text("synthetic fixture only", encoding="utf-8")
            self.assertEqual(scan(root), [])

    def test_identifier_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "private.txt").write_text("contact " + "test" + "@example.com", encoding="utf-8")
            self.assertTrue(scan(root))


if __name__ == "__main__":
    unittest.main()
