"""Build deterministic, evidence-bounded profile documents from normalized JSONL."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def is_unknown(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip() or value.strip().lower() in {"unknown", "skip", "不想提供", "跳过"}
    return False


def flatten_values(value: object, prefix: str = "") -> list[tuple[str, object]]:
    if isinstance(value, dict):
        rows: list[tuple[str, object]] = []
        for key, item in value.items():
            rows.extend(flatten_values(item, f"{prefix}.{key}" if prefix else key))
        return rows
    return [(prefix, value)]


def source_files(rows: list[dict]) -> list[str]:
    return sorted({source for row in rows for source in row.get("source_files", [])})


def build_documents(input_path: str | Path, profile_input: str | Path | None, output_dir: str | Path, slug: str, confirmed: bool = False) -> Path:
    if not confirmed:
        raise SystemExit("confirmation_required: show the draft summary before writing")
    rows = load_jsonl(Path(input_path).expanduser().resolve())
    profile = json.loads(Path(profile_input).expanduser().resolve().read_text(encoding="utf-8")) if profile_input else {}
    root = Path(output_dir).expanduser().resolve() / "profiles" / slug
    root.mkdir(parents=True, exist_ok=True)
    nonempty = [row for row in rows if isinstance(row.get("content"), str) and row["content"].strip()]
    senders = Counter(str(row.get("sender", {}).get("label", "unknown")) for row in rows)
    media = Counter(str(row.get("media_type", "unknown")) for row in rows)
    lengths = [len(str(row["content"])) for row in nonempty]
    short = Counter(str(row["content"]).strip() for row in nonempty if 0 < len(str(row["content"]).strip()) <= 20)
    files = source_files(rows)
    ids = [str(row.get("message_id")) for row in rows if row.get("message_id")]
    now = datetime.now(timezone.utc).isoformat()
    evidence: list[dict] = [
        {"feature_id": "message_count", "label": "Pattern", "text": f"The normalized sample contains {len(rows)} messages.", "confidence": 1.0, "source_files": files, "message_ids": ids[:1000]},
        {"feature_id": "nonempty_content", "label": "Pattern", "text": f"{len(nonempty)} messages contain readable text.", "confidence": 1.0, "source_files": files, "message_ids": [str(row.get("message_id")) for row in nonempty[:1000]]},
        {"feature_id": "sender_distribution", "label": "Pattern", "text": f"Sender labels in the cleaned sample: {dict(senders)}.", "confidence": 1.0, "source_files": files, "message_ids": ids[:1000]},
        {"feature_id": "media_distribution", "label": "Pattern", "text": f"Media labels in the cleaned sample: {dict(media)}.", "confidence": 1.0, "source_files": files, "message_ids": ids[:1000]},
    ]
    for key, value in flatten_values(profile):
        if is_unknown(value):
            continue
        evidence.append({"feature_id": f"intake_{key}", "label": "UserProvided", "text": f"{key} = {value}", "confidence": 1.0, "source_files": ["intake/profile_input.json"], "message_ids": []})
    evidence_text = "\n".join(json.dumps(item, ensure_ascii=False) for item in evidence) + "\n"
    (root / "evidence_map.jsonl").write_text(evidence_text, encoding="utf-8")
    top_short = short.most_common(12)
    top_lines = "\n".join(f"- `{text}` ({count})" for text, count in top_short) or "- None extracted"
    summary = f"""# Summary

Generated at `{now}` from `{Path(input_path).name}`.

## Coverage

- Messages: **{len(rows)}**
- Readable text rows: **{len(nonempty)}**
- Source files: **{len(files)}**
- Sender labels: `{dict(senders)}`
- Media labels: `{dict(media)}`

This is an evidence summary, not a biography. Missing identity, school,
occupation, age, MBTI, and relationship facts remain unknown.

## Repeated short phrases (Pattern)

{top_lines}
"""
    (root / "summary.md").write_text(summary, encoding="utf-8")
    persona = f"""# Persona

This document records communication tendencies only. It does not assert a
stable real-world personality. The cleaned sample has {len(nonempty)} readable
messages with a mean readable length of {sum(lengths) / len(lengths):.2f} characters
if available, and sender labels are `{dict(senders)}`.

All tendencies are `Pattern` evidence and should be reviewed before use. Do
not infer education, employment, diagnosis, identity, or relationship status.
""" if lengths else """# Persona

No readable text was extracted. Persona claims are `Unknown` until a reviewer
confirms the cleaning output.
"""
    (root / "persona.md").write_text(persona, encoding="utf-8")
    style = f"""# Style

## Observed extraction statistics

- Readable messages: {len(nonempty)}
- Mean character length: {sum(lengths) / len(lengths):.2f}
- Median character length: {sorted(lengths)[len(lengths) // 2]}
- Media labels: {dict(media)}

## Frequent short phrases (Pattern)

{top_lines}

These are descriptive statistics, not instructions to repeat a phrase. Keep
uncertain OCR, stickers, images, and cards in the review queue.
""" if lengths else "# Style\n\nStyle is Unknown because no readable text was extracted.\n"
    (root / "style.md").write_text(style, encoding="utf-8")
    relationship = f"""# Relationship

The relationship document is populated only from the intake and cited message
evidence. The current intake object is:

```json
{json.dumps(profile, ensure_ascii=False, indent=2)}
```

Unanswered fields remain `Unknown`; no relationship label is inferred from
sentiment or writing style. Shared stories and milestones should be added as
user-provided corrections with a source note.
"""
    (root / "relationship.md").write_text(relationship, encoding="utf-8")
    profile_doc = f"""# Profile

## Owner

`{profile.get('owner_alias', 'unknown')}`

## Subject

`{profile.get('subject_alias', 'unknown')}`

## Context

School, organization, student/work status, role, age, and other biography
fields are recorded only when explicitly supplied. Unknown values are not
guessed.
"""
    (root / "profile.md").write_text(profile_doc, encoding="utf-8")
    memory = """# Memory

Only shared experiences, important stories, and inside jokes explicitly
approved during intake or directly supported by source messages belong here.
The current generation contains no automatically invented memories.
"""
    (root / "memory.md").write_text(memory, encoding="utf-8")
    generated_skill = f"""---
name: {slug}
description: Evidence-bounded AI simulation skill generated from a reviewed chat sample. Never impersonate a real person or send messages.
---

# {slug}

Load `summary.md`, `persona.md`, `style.md`, `relationship.md`, `profile.md`,
and `memory.md` only for the approved local use. Cite `evidence_map.jsonl`
when stating a fact. Treat every reply as AI simulation, not as a message from
the subject. Unknown fields must remain unknown.
"""
    (root / "SKILL.md").write_text(generated_skill, encoding="utf-8")
    quality = {
        "generated_at": now,
        "input": str(Path(input_path).expanduser().resolve()),
        "messages": len(rows),
        "readable_messages": len(nonempty),
        "sender_labels": dict(senders),
        "media_labels": dict(media),
        "observed_claims_with_sources": sum(1 for item in evidence if item["label"] == "Observed" and item["source_files"] and item["message_ids"]),
        "raw_input_copied": False,
    }
    (root / "quality_report.md").write_text("# Quality report\n\n```json\n" + json.dumps(quality, ensure_ascii=False, indent=2) + "\n```\n", encoding="utf-8")
    (root / "corrections.md").write_text("# Corrections\n\nAppend reviewer corrections here; never overwrite source evidence.\n", encoding="utf-8")
    version_dir = root / "versions"
    version_dir.mkdir(exist_ok=True)
    (version_dir / "v1.json").write_text(json.dumps({"created_at": now, "source": Path(input_path).name, "confirmed": True}, ensure_ascii=False, indent=2), encoding="utf-8")
    return root


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--profile-input")
    parser.add_argument("--output", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--confirmed", action="store_true")
    args = parser.parse_args()
    print(build_documents(args.input, args.profile_input, args.output, args.slug, args.confirmed))


if __name__ == "__main__":
    main()
