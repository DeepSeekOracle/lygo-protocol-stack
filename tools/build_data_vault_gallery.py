#!/usr/bin/env python3
"""Build web-optimized Data Vault gallery from Grok/seal screenshot archives.

Sources (I: Drive):
  - LYRA LOCAL/grok_chats/New folder/** (seal_archive + root shots)
  - LYRA LOCAL/220+/**
  - Old OpenClaw GROK CHATS screenshots

Outputs under docs/data-vault/assets/gallery/:
  - full/*.jpg  (max edge 1400)
  - thumb/*.jpg (max edge 420)
  - manifest.json
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(r"I:\E Drive")
STACK = ROOT / "lygo-protocol-stack"
OUT = STACK / "docs" / "data-vault" / "assets" / "gallery"
FULL = OUT / "full"
THUMB = OUT / "thumb"
MANIFEST = STACK / "docs" / "data-vault" / "data" / "gallery_manifest.json"

SOURCES = [
    ROOT / "LYRA LOCAL" / "grok_chats" / "New folder",
    ROOT / "LYRA LOCAL" / "220+",
    ROOT / "Old files openclaw" / "OLD openclaw" / "workspace" / "GROK CHATS",
]

EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
FULL_MAX = 1400
THUMB_MAX = 420
JPEG_Q_FULL = 82
JPEG_Q_THUMB = 72


def sha256_file(path: Path, limit: int | None = None) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        if limit:
            h.update(f.read(limit))
        else:
            while True:
                b = f.read(1024 * 1024)
                if not b:
                    break
                h.update(b)
    return h.hexdigest()


def infer_meta(path: Path, root: Path) -> dict:
    name = path.name
    stem = path.stem
    rel = str(path.relative_to(root)).replace("\\", "/")
    tags: list[str] = []
    title = stem.replace("_", " ").replace("-", " ")

    if "seal_archive" in rel.lower():
        tags.append("SEAL_ARCHIVE")
    if "screenshot" in name.lower():
        tags.append("SCREENSHOT")
    if "qr" in name.lower():
        tags.append("QR")

    seals = re.findall(r"SEAL_[0-9A-Za-z]+", name, flags=re.I)
    seals += re.findall(r"WARSEAL_[0-9A-Za-z]+", name, flags=re.I)
    for s in seals:
        tags.append(s.upper())
    if seals:
        title = " / ".join(s.upper() for s in seals)
        tags.append("SEAL")

    if re.search(r"(?i)deadman|lfw|lantern", name):
        tags.append("FAILSAFE")
    if re.search(r"(?i)lyra|lightfather|champion|council", name):
        tags.append("LYRA")
    if re.search(r"(?i)grok", name):
        tags.append("GROK")
    if re.search(r"(?i)track\s*\d", name):
        tags.append("MUSIC_ART")

    # prefer non-duplicate "(1)" variants as secondary
    dup = bool(re.search(r"\(\d+\)\s*$", stem)) or " (1)" in name
    return {
        "title": title[:140],
        "tags": sorted(set(tags)),
        "source_rel": rel,
        "duplicate_name": dup,
    }


def fit(img: Image.Image, max_edge: int) -> Image.Image:
    img = ImageOps.exif_transpose(img)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    elif img.mode == "L":
        img = img.convert("RGB")
    w, h = img.size
    scale = min(1.0, max_edge / float(max(w, h)))
    if scale < 1.0:
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)
    return img


def collect() -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []
    for root in SOURCES:
        if not root.exists():
            print("missing source", root)
            continue
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in EXTS:
                continue
            # skip tiny icons / broken
            if p.stat().st_size < 8_000:
                continue
            pairs.append((root, p))
    return pairs


def main() -> int:
    FULL.mkdir(parents=True, exist_ok=True)
    THUMB.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()

    items = collect()
    print("candidates", len(items))

    # Prefer non-(1) duplicates when content hashes collide later
    items.sort(key=lambda rp: (rp[1].stat().st_size, 0 if "(1)" not in rp[1].name else 1), reverse=True)

    seen_content: set[str] = set()
    gallery: list[dict] = []
    skipped_dup = 0
    errors = 0

    for i, (root, path) in enumerate(items, 1):
        try:
            # quick hash of first 256KB + size to catch exact copies cheaply, then full file hash
            quick = sha256_file(path, limit=256 * 1024) + f":{path.stat().st_size}"
            if quick in seen_content:
                skipped_dup += 1
                continue
            # open + normalize
            with Image.open(path) as im:
                im.load()
                full_img = fit(im, FULL_MAX)
                # content fingerprint after normalize (dedupe near-identical exports)
                import io

                buf = io.BytesIO()
                full_img.save(buf, format="JPEG", quality=60, optimize=True)
                content_fp = hashlib.sha256(buf.getvalue()).hexdigest()
                if content_fp in seen_content:
                    skipped_dup += 1
                    continue
                seen_content.add(content_fp)
                seen_content.add(quick)

                gid = content_fp[:16]
                full_name = f"{gid}.jpg"
                thumb_name = f"{gid}.jpg"
                full_path = FULL / full_name
                thumb_path = THUMB / thumb_name
                if not full_path.exists():
                    full_img.save(full_path, format="JPEG", quality=JPEG_Q_FULL, optimize=True)
                thumb_img = fit(full_img, THUMB_MAX)
                if not thumb_path.exists():
                    thumb_img.save(thumb_path, format="JPEG", quality=JPEG_Q_THUMB, optimize=True)

                meta = infer_meta(path, root)
                gallery.append(
                    {
                        "id": gid,
                        "title": meta["title"],
                        "tags": meta["tags"],
                        "source_rel": meta["source_rel"],
                        "source_root": str(root.name),
                        "original_name": path.name,
                        "original_bytes": path.stat().st_size,
                        "full": f"assets/gallery/full/{full_name}",
                        "thumb": f"assets/gallery/thumb/{thumb_name}",
                        "full_bytes": full_path.stat().st_size,
                        "width": full_img.size[0],
                        "height": full_img.size[1],
                    }
                )
        except Exception as e:
            errors += 1
            print("ERR", path.name, e)
        if i % 50 == 0:
            print(f"processed {i}/{len(items)} kept={len(gallery)} dups={skipped_dup} err={errors}")

    # Sort: SEAL_* first, then screenshots by name
    def sk(it: dict) -> tuple:
        seals = [t for t in it.get("tags") or [] if t.startswith("SEAL_")]
        return (0 if seals else 1, seals[0] if seals else "", it.get("original_name") or "")

    gallery.sort(key=sk)

    manifest = {
        "signature": "Delta9Phi963-DATA-VAULT-GALLERY-v1",
        "generated_utc": now,
        "count": len(gallery),
        "candidates": len(items),
        "skipped_duplicates": skipped_dup,
        "errors": errors,
        "note": (
            "Web-optimized JPEG gallery from LYRA LOCAL grok_chats seal_archive + related screenshots. "
            "Originals remain on steward disk; Pages hosts compressed thumbs/fulls only."
        ),
        "sources": [str(s) for s in SOURCES if s.exists()],
        "items": gallery,
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Update vault manifest stats if present
    vman = STACK / "docs" / "data-vault" / "data" / "vault_manifest.json"
    if vman.is_file():
        man = json.loads(vman.read_text(encoding="utf-8"))
        man.setdefault("stats", {})
        man["stats"]["gallery_images"] = len(gallery)
        man["generated_utc"] = now
        pages = man.get("pages") or []
        if "gallery.html" not in pages:
            pages.append("gallery.html")
        man["pages"] = pages
        vman.write_text(json.dumps(man, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    total_bytes = sum(p.stat().st_size for p in FULL.glob("*.jpg")) + sum(
        p.stat().st_size for p in THUMB.glob("*.jpg")
    )
    print(
        json.dumps(
            {
                "ok": True,
                "gallery": len(gallery),
                "skipped_duplicates": skipped_dup,
                "errors": errors,
                "out_mb": round(total_bytes / 1e6, 1),
                "manifest": str(MANIFEST),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
