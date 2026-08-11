"""Inventory screenshots, run optional RapidOCR, and emit reviewable JSONL."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None

_OCR_ENGINE = None


def load_manifest(root: Path, manifest_path: Path | None) -> dict:
    candidate = manifest_path or root / "manifest.json"
    if candidate.exists():
        data = json.loads(candidate.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return {"schema_version": "legacy", "pages": data}
        return data
    from build_manifest import build_manifest

    return build_manifest(root)


def parse_rapidocr(path: Path) -> list[tuple[str, float, list[float] | None]]:
    global _OCR_ENGINE
    try:
        if _OCR_ENGINE is None:
            from rapidocr_onnxruntime import RapidOCR

            _OCR_ENGINE = RapidOCR()
    except ImportError:
        return []
    if Image is None:
        return []
    try:
        result, _ = _OCR_ENGINE(str(path))
    except Exception:
        return []
    rows: list[tuple[str, float, list[float] | None]] = []
    for item in result or []:
        if len(item) < 3:
            continue
        box, text, score = item[0], str(item[1]), float(item[2])
        coords = None
        try:
            flat = [float(value) for point in box for value in point]
            coords = [min(flat[0::2]), min(flat[1::2]), max(flat[0::2]), max(flat[1::2])]
        except Exception:
            pass
        if text.strip():
            rows.append((text.strip(), score, coords))
    return rows


def dedup_key(text: str) -> str:
    return re.sub(r"\s+", "", text).lower()


def clean(root: str | Path, output_dir: str | Path, manifest_path: str | Path | None = None, ocr: str = "rapidocr", max_pages: int | None = None) -> dict:
    root = Path(root).expanduser().resolve()
    output = Path(output_dir).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(root, Path(manifest_path).expanduser().resolve() if manifest_path else None)
    pages = manifest.get("pages", [])[:max_pages] if max_pages else manifest.get("pages", [])
    records: list[dict] = []
    review: list[dict] = []
    seen: list[tuple[str, str]] = []
    for page_record in pages:
        page = int(page_record.get("page", len(records) + 1))
        name = str(page_record.get("file", ""))
        image_path = root / name
        digest = page_record.get("sha256") or hashlib.sha256(image_path.read_bytes()).hexdigest() if image_path.exists() else ""
        ocr_rows = parse_rapidocr(image_path) if ocr == "rapidocr" and image_path.exists() else []
        if not ocr_rows:
            record = {
                "message_id": f"msg_{len(records) + 1:06d}",
                "source_files": [name],
                "sender": {"label": "unknown", "confidence": 0.0, "evidence": "not_extracted"},
                "timestamp": {"value": None, "kind": "unknown", "confidence": 0.0},
                "content": None,
                "content_confidence": 0.0,
                "media_type": "image" if image_path.suffix.lower() else "unknown",
                "usefulness": "review",
                "evidence_label": "Unknown",
                "page": page,
                "bbox": None,
                "page_sha256": digest,
            }
            records.append(record)
            review.append({"page": page, "file": name, "reason": "no_ocr_text_or_unreadable"})
            continue
        width = int(page_record.get("width") or 0)
        if not width and Image is not None and image_path.exists():
            try:
                with Image.open(image_path) as image:
                    width = image.width
            except Exception:
                width = 0
        for text, score, bbox in ocr_rows:
            key = dedup_key(text)
            duplicate_of = None
            for previous_key, previous_id in reversed(seen[-50:]):
                ratio = difflib.SequenceMatcher(None, key, previous_key).ratio()
                if key and ratio >= 0.92:
                    duplicate_of = previous_id
                    break
            record_id = f"msg_{len(records) + 1:06d}"
            label = "Observed" if score >= 0.8 else "Unknown"
            sender_label = "unknown"
            sender_confidence = 0.0
            sender_evidence = "sender_requires_layout_review"
            if bbox and width:
                center_x = (bbox[0] + bbox[2]) / 2
                if center_x >= width * 0.62:
                    sender_label, sender_confidence, sender_evidence = "owner", 0.55, "horizontal_bubble_heuristic"
                elif center_x <= width * 0.38:
                    sender_label, sender_confidence, sender_evidence = "subject", 0.55, "horizontal_bubble_heuristic"
            timestamp_match = re.fullmatch(r"(?:[01]?\d|2[0-3]):[0-5]\d", text)
            timestamp = {"value": text, "kind": "observed", "confidence": score} if timestamp_match else {"value": None, "kind": "unknown", "confidence": 0.0}
            records.append({
                "message_id": record_id,
                "source_files": [name],
                "sender": {"label": sender_label, "confidence": sender_confidence, "evidence": sender_evidence},
                "timestamp": timestamp,
                "content": text,
                "content_confidence": score,
                "media_type": "text",
                "usefulness": "context" if score >= 0.8 else "review",
                "evidence_label": label,
                "page": page,
                "bbox": bbox,
                "page_sha256": digest,
                "duplicate_of": duplicate_of,
            })
            seen.append((key, record_id))
            if score < 0.8:
                review.append({"page": page, "file": name, "message_id": record_id, "reason": "low_ocr_confidence", "confidence": score})
    normalized = output / "normalized_messages.jsonl"
    normalized.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in records) + ("\n" if records else ""), encoding="utf-8")
    report = {
        "input_dir": str(root),
        "pages_seen": len(pages),
        "messages_emitted": len(records),
        "review_items": len(review),
        "ocr_engine": ocr,
        "duplicate_messages": sum(1 for item in records if item.get("duplicate_of")),
        "raw_files_are_not_copied": True,
    }
    (output / "quality_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "review_queue.jsonl").write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in review) + ("\n" if review else ""), encoding="utf-8")
    (output / "cleaning_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--manifest")
    parser.add_argument("--ocr", choices=("rapidocr", "none"), default="rapidocr")
    parser.add_argument("--max-pages", type=int)
    args = parser.parse_args()
    print(json.dumps(clean(args.input, args.output, args.manifest, args.ocr, args.max_pages), ensure_ascii=False))


if __name__ == "__main__":
    main()
