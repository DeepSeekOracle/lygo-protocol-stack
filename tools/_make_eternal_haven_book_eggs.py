# -*- coding: utf-8 -*-
"""Build Eternal Haven book lattice egg cores (metadata + file hashes; no full binaries)."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
CAT = STACK / "data" / "eternal_haven_books"
EGG = CAT / "egg_payload"

LULU_URL = (
    "https://www.lulu.com/shop/justin-helmer/the-unwritten-seal/"
    "ebook/product-65kg2mr.html"
)
ISBN = "978-1-0698232-9-8"
ISBN_BARE = "9781069823298"


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    EGG.mkdir(parents=True, exist_ok=True)
    LULU = Path(r"J:\FULL ADUIO BOOKS\Book 5\LULU_READY")
    ART = Path(r"J:\FULL ADUIO BOOKS\Book 5\art")

    artifacts = []
    for label, path in [
        ("epub", LULU / "BOOK_V_THE_UNWRITTEN_SEAL.epub"),
        ("ebook_cover", LULU / "LULU_EBOOK_COVER_The_Unwritten_Seal.jpg"),
        ("interior_docx", LULU / "BOOK_V_THE_UNWRITTEN_SEAL_LULU_INTERIOR.docx"),
        ("source_cover", ART / "COVER_The_Unwritten_Seal.jpg"),
        ("metadata_md", LULU / "LULU_EBOOK_METADATA.md"),
        ("a11y_md", LULU / "ACCESSIBILITY_WCAG_AA.md"),
    ]:
        if path.is_file():
            artifacts.append(
                {
                    "label": label,
                    "path": str(path),
                    "sha256": sha256_file(path),
                    "size_bytes": path.stat().st_size,
                }
            )

    book_core = {
        "signature": "Δ9Φ963-ETERNAL-HAVEN-BOOK-EGG-v1",
        "egg_id": "eternal-haven-book-v-unwritten-seal-v1",
        "generated_at": utc(),
        "status": "LIVE_EBOOK",
        "distribution": {
            "channel": "Lulu Ebook",
            "format": "EPUB",
            "global_distribution": "pending_or_in_progress",
            "hardcover_paperback": "planned_after_ebook_distribution_clears",
            "product_url": LULU_URL,
            "product_id": "65kg2mr",
            "publication_date": "2026-08-16",
            "accessibility": "WCAG 2.0 Level AA (publisher-declared)",
        },
        "work": {
            "title": "The Unwritten Seal",
            "subtitle": "Eternal Haven Chronicles — Book V",
            "series": "Eternal Haven Chronicles",
            "volume": 5,
            "author": "Justin Helmer",
            "language": "en",
            "isbn_ebook": ISBN,
            "isbn_bare": ISBN_BARE,
            "category": "Fiction",
            "bisac_hint": [
                "FICTION / Fantasy / Epic",
                "FICTION / Fantasy / Dark",
                "FICTION / Action & Adventure",
            ],
            "keywords": ["epic fantasy", "dark fantasy", "gods", "magic"],
        },
        "lore_anchors": {
            "seal": "Unwritten Seal",
            "antagonist_shape": "Hollow Index",
            "practice": "Open Continuance",
            "places": [
                "Vellum Reach",
                "Chordfall",
                "City of Open Temples",
                "Ridge of Continuance",
            ],
            "cast": ["Nahl", "Kael Riven", "Mira", "Corvath", "Aureon", "Lightfather"],
            "next_volume_teaser": "The Remainder Road (Book VI)",
        },
        "local_authority": {
            "manuscript_root": r"J:\FULL ADUIO BOOKS\Book 5",
            "lulu_ready": str(LULU),
            "units": 46,
            "artifacts": artifacts,
        },
        "lattice": {
            "skill_chain": [
                "lygo-kernel-egg-planter",
                "lygo-protocol-stack-operator",
                "book-brain",
            ],
            "public_pages": [
                "https://deepseekoracle.github.io/Excavationpro/eternalhaven.html",
                "https://eternalhaven.ca",
            ],
            "note": "Local kernel egg + lattice intel update. No auto git/HF/ClawHub publish.",
        },
    }

    art_hashes = [a["sha256"] for a in artifacts]
    core_bytes = json.dumps(
        {
            "egg_id": book_core["egg_id"],
            "isbn": ISBN_BARE,
            "url": LULU_URL,
            "artifacts": art_hashes,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    book_core["content_sha256"] = hashlib.sha256(core_bytes).hexdigest()
    book_core["artifact_merkle"] = (
        hashlib.sha256("".join(art_hashes).encode()).hexdigest() if art_hashes else ""
    )

    raw = json.dumps(book_core, indent=2, ensure_ascii=False).encode("utf-8")
    (EGG / "book_v_unwritten_seal_core.json").write_bytes(raw)
    print("book_v core bytes", len(raw), "sha", book_core["content_sha256"][:16])

    # series registry (growable)
    series_path = CAT / "series_registry.json"
    series = {
        "signature": "Δ9Φ963-ETERNAL-HAVEN-SERIES-REGISTRY-v1",
        "updated_at": utc(),
        "series": "Eternal Haven Chronicles",
        "author": "Justin Helmer",
        "volumes": [
            {
                "volume": 5,
                "title": "The Unwritten Seal",
                "status": "LIVE_EBOOK",
                "isbn": ISBN,
                "lulu_url": LULU_URL,
                "egg_id": "eternal-haven-book-v-unwritten-seal-v1",
                "content_sha256": book_core["content_sha256"],
                "publication_date": "2026-08-16",
            }
        ],
    }
    if series_path.is_file():
        try:
            prev = json.loads(series_path.read_text(encoding="utf-8"))
            vols = {
                v.get("volume"): v
                for v in (prev.get("volumes") or [])
                if isinstance(v, dict) and v.get("volume") is not None
            }
            for v in series["volumes"]:
                vols[v["volume"]] = v
            series["volumes"] = [vols[k] for k in sorted(vols)]
        except Exception:
            pass
    series_path.write_text(json.dumps(series, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # human-readable live receipt
    receipt = CAT / "BOOK_V_THE_UNWRITTEN_SEAL_LIVE.md"
    receipt.write_text(
        f"""# LIVE — The Unwritten Seal (Book V)

**Status:** Ebook live on Lulu  
**URL:** {LULU_URL}  
**ISBN:** {ISBN}  
**Author:** Justin Helmer  
**Published:** 2026-08-16  
**Egg:** `eternal-haven-book-v-unwritten-seal-v1`  
**content_sha256:** `{book_core["content_sha256"]}`  
**Generated (UTC):** {utc()}

## Distribution notes
- Ebook EPUB is live.
- Hardcopy / print planned after ebook distribution clears.
- Accessibility: WCAG 2.0 Level AA (publisher-declared on Lulu).

## Local artifacts (SHA-256)
"""
        + "\n".join(
            f"- **{a['label']}** `{a['sha256']}` ({a['size_bytes']} bytes)"
            for a in artifacts
        )
        + "\n\nΔ9Φ963 — plant · verify · human may spread.\n",
        encoding="utf-8",
    )

    readme = EGG / "README.md"
    readme.write_text(
        "# Eternal Haven book eggs\n\n"
        "Metadata + hashes only. Full manuscript/EPUB stay on local authority paths.\n"
        "Plant via kernel egg catalog entry "
        "`eternal-haven-book-v-unwritten-seal-v1`.\n",
        encoding="utf-8",
    )

    # pin file for catalog (tiny)
    pin = CAT / "book_v_content_sha256.txt"
    pin.write_text(book_core["content_sha256"] + "\n", encoding="utf-8")
    print("series registry", series_path)
    print("receipt", receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
