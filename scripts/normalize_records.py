"""Normalize CSV, HTML, JSON and JSONL exports without using an API."""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
from pathlib import Path


def value(record: dict, *names: str, default: str = "") -> str:
    lowered = {str(key).lower(): record[key] for key in record}
    for name in names:
        if name.lower() in lowered:
            return str(lowered[name.lower()] or "")
    return default


def normalize_record(record: dict, index: int, source: str) -> dict:
    content = value(record, "content", "strcontent", "message", "text", "body")
    sender = value(record, "sender", "talker", "from", "author", default="unknown")
    timestamp = value(record, "timestamp", "createtime", "time", "date")
    media = value(record, "media_type", "type", default="text") or "unknown"
    return {
        "message_id": value(record, "message_id", "id", default=f"msg_{index:06d}"),
        "source_files": [source],
        "sender": {"label": sender, "confidence": 1.0, "evidence": "structured_export"},
        "timestamp": {"value": timestamp or None, "kind": "observed" if timestamp else "unknown", "confidence": 1.0 if timestamp else 0.0},
        "content": content,
        "content_confidence": 1.0,
        "media_type": media,
        "usefulness": "context" if content else "unknown",
        "evidence_label": "Observed",
        "page": None,
        "bbox": None,
    }


def read_input(path: Path) -> list[dict]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    if suffix in {".jsonl", ".ndjson"}:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else data.get("messages", data.get("rows", [data]))
    if suffix in {".html", ".htm"}:
        text = html.unescape(re.sub(r"<[^>]+>", " ", path.read_text(encoding="utf-8", errors="replace")))
        chunks = [chunk.strip() for chunk in re.split(r"\s{2,}|\n+", text) if chunk.strip()]
        return [{"message": chunk} for chunk in chunks]
    raise ValueError(f"unsupported_input:{path.suffix}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = Path(args.input).name
    records = [normalize_record(record, index, source) for index, record in enumerate(read_input(Path(args.input)), 1)]
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(json.dumps(record, ensure_ascii=False) for record in records) + ("\n" if records else ""), encoding="utf-8")
    print(json.dumps({"records": len(records), "output": str(output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
