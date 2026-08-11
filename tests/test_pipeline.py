import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_manifest import build_manifest
from build_profile import build_documents
from clean_captures import clean
from normalize_records import read_input, normalize_record
from run_intake import advance
from validate_evidence import validate


class PipelineTests(unittest.TestCase):
    def test_image_manifest_clean_and_profile(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            Image.new("RGB", (120, 80), (40, 40, 40)).save(root / "page_001.png")
            manifest = build_manifest(root)
            (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            cleaned = root / "cleaned"
            report = clean(root, cleaned, ocr="none")
            self.assertEqual(report["pages_seen"], 1)
            profile_input = root / "profile.json"
            profile_input.write_text(json.dumps({"owner_alias": "owner", "subject_alias": "subject", "relationship": "unknown"}), encoding="utf-8")
            generated = build_documents(cleaned / "normalized_messages.jsonl", profile_input, root / "generated", "subject", confirmed=True)
            self.assertTrue((generated / "SKILL.md").exists())
            self.assertEqual(validate(generated / "evidence_map.jsonl"), [])

    def test_structured_record_normalization(self):
        record = normalize_record({"id": "x", "sender": "subject", "message": "hello"}, 1, "export.csv")
        self.assertEqual(record["message_id"], "x")
        self.assertEqual(record["content"], "hello")
        self.assertEqual(record["sender"]["label"], "subject")

    def test_intake_is_one_question_at_a_time(self):
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp) / "intake.json"
            first = advance(state)
            self.assertFalse(first["done"])
            self.assertEqual(first["field"], "owner_alias")
            second = advance(state, "owner")
            self.assertEqual(second["field"], "subject_alias")


if __name__ == "__main__":
    unittest.main()
