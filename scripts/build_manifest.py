"""Create a portable manifest for a directory of screenshots."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def natural_key(path: Path) -> tuple[object, ...]:
    return tuple(int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", path.name))


def image_dimensions(path: Path) -> tuple[int, int]:
    if Image is None:
        return (0, 0)
    with Image.open(path) as image:
        return image.size


def build_manifest(input_dir: str | Path, app: str = "unknown", mode: str = "unknown", offset: float = 0.0, wait_seconds: float = 0.1) -> dict:
    root = Path(input_dir).expanduser().resolve()
    files = sorted((path for path in root.iterdir() if path.suffix.lower() in IMAGE_EXTENSIONS), key=natural_key)
    pages = []
    seen: dict[str, int] = {}
    now = datetime.now(timezone.utc).isoformat()
    for index, path in enumerate(files, 1):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        width, height = image_dimensions(path)
        record = {
            "page": index,
            "file": path.name,
            "sha256": digest,
            "width": width,
            "height": height,
            "captured_at": now,
            "duplicate_of": seen.get(digest),
        }
        seen.setdefault(digest, index)
        pages.append(record)
    return {
        "schema_version": "1.0",
        "run_id": f"manifest_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "app": app,
        "region": [0, 0, 0, 0],
        "mode": mode,
        "offset": offset,
        "wait_seconds": wait_seconds,
        "pages": pages,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir")
    parser.add_argument("--output", default=None)
    parser.add_argument("--app", default="unknown")
    parser.add_argument("--mode", default="unknown")
    parser.add_argument("--offset", type=float, default=0.0)
    parser.add_argument("--wait-seconds", type=float, default=0.1)
    args = parser.parse_args()
    root = Path(args.input_dir).expanduser().resolve()
    output = Path(args.output).expanduser().resolve() if args.output else root / "manifest.json"
    manifest = build_manifest(root, args.app, args.mode, args.offset, args.wait_seconds)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"manifest": str(output), "pages": len(manifest["pages"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
