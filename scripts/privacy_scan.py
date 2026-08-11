"""Scan public-facing text for common accidental identifiers or secrets."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


PATTERNS = {
    "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    "phone": re.compile(r"(?<!\d)(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)"),
    "wxid": re.compile(r"\bwxid_[a-z0-9_-]{6,}\b", re.I),
    "api_key": re.compile(r"\b(?:sk|key)[-_][A-Za-z0-9]{20,}\b", re.I),
    "private_key": re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----"),
}
TEXT_EXTENSIONS = {".md", ".txt", ".json", ".jsonl", ".yaml", ".yml", ".py", ".toml", ".html", ".csv"}


def scan(root: str | Path, allow_private: bool = False) -> list[dict]:
    findings: list[dict] = []
    root = Path(root).expanduser().resolve()
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        if any(part in {".git", ".venv", "venv", "__pycache__"} for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for kind, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                findings.append({"file": str(path.relative_to(root)), "kind": kind, "start": match.start()})
    if allow_private:
        return findings
    return findings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root")
    parser.add_argument("--allow-private", action="store_true")
    args = parser.parse_args()
    findings = scan(args.root, args.allow_private)
    for finding in findings:
        print(f"{finding['kind']}\t{finding['file']}\t{finding['start']}")
    if findings and not args.allow_private:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
