"""Validate the evidence map and normalized records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


LABELS = {"Observed", "Pattern", "UserProvided", "Unknown"}


def validate(evidence_path: str | Path) -> list[str]:
    errors: list[str] = []
    path = Path(evidence_path).expanduser().resolve()
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line_{line_no}:invalid_json:{exc.msg}")
            continue
        label = item.get("label") or item.get("evidence_label")
        if label not in LABELS:
            errors.append(f"line_{line_no}:invalid_label")
        if label in {"Observed", "Pattern"}:
            if not item.get("source_files"):
                errors.append(f"line_{line_no}:missing_source_files")
            if label == "Observed" and not item.get("message_ids") and not item.get("message_id"):
                errors.append(f"line_{line_no}:missing_message_id")
        confidence = item.get("confidence")
        if confidence is not None and not 0 <= float(confidence) <= 1:
            errors.append(f"line_{line_no}:invalid_confidence")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence_map")
    args = parser.parse_args()
    errors = validate(args.evidence_map)
    if errors:
        print("\n".join(errors))
        raise SystemExit(1)
    print("evidence_ok")


if __name__ == "__main__":
    main()
