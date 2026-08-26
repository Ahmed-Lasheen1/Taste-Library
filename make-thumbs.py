#!/usr/bin/env python3
"""
Generate grid thumbnails from the full-size captures in images/.

The app loads images/thumbs/<id>.jpg in the card grid and the full PNG only in the
detail modal — the captures total several MB, the thumbnails a few hundred KB. If a
thumbnail is missing the app silently falls back to the full image, so this is a
performance fix rather than a correctness one.

    python3 make-thumbs.py            # only what's missing or stale
    python3 make-thumbs.py --force    # rebuild everything
    python3 make-thumbs.py --width 1200

Requires Pillow:  pip install Pillow
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(ROOT, "design-taste-library.json")
THUMBS = os.path.join(ROOT, "images", "thumbs")


def main() -> int:
    ap = argparse.ArgumentParser(description="Build thumbnails for the taste library.")
    ap.add_argument("--force", action="store_true", help="rebuild even if up to date")
    ap.add_argument("--width", type=int, default=900, help="thumbnail width (default 900)")
    ap.add_argument("--quality", type=int, default=82, help="JPEG quality (default 82)")
    args = ap.parse_args()

    try:
        from PIL import Image
    except ImportError:
        print("Pillow is required:  pip install Pillow", file=sys.stderr)
        return 1

    with open(LIB, encoding="utf-8") as fh:
        entries = json.load(fh)["entries"]

    os.makedirs(THUMBS, exist_ok=True)
    built = skipped = 0
    missing_src: list[str] = []
    before = after = 0

    for e in entries:
        src = os.path.join(ROOT, e["source"]["screenshot"])
        dst = os.path.join(THUMBS, f"{e['id']}.jpg")

        if not os.path.exists(src):
            missing_src.append(f"{e['id']} -> {e['source']['screenshot']}")
            continue

        # stale if the capture is newer than the thumbnail
        fresh = os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src)
        if fresh and not args.force:
            skipped += 1
            continue

        with Image.open(src) as im:
            im = im.convert("RGB")
            w = min(args.width, im.width)
            h = round(im.height * w / im.width)
            im.resize((w, h), Image.LANCZOS).save(dst, "JPEG", quality=args.quality, optimize=True)

        b, a = os.path.getsize(src), os.path.getsize(dst)
        before += b
        after += a
        built += 1
        print(f"  {e['id']:<16} {b // 1024:>6}K -> {a // 1024:>5}K")

    print()
    if built:
        pct = 100 - (100 * after // before) if before else 0
        print(f"  built {built}  ({before // 1024}K -> {after // 1024}K, {pct}% smaller)")
    if skipped:
        print(f"  up to date: {skipped}  (use --force to rebuild)")
    if missing_src:
        print("\n  MISSING CAPTURES — these entries have no screenshot on disk:", file=sys.stderr)
        for m in missing_src:
            print(f"    {m}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
