#!/usr/bin/env python3
"""Rescan audio for DistroKid QZ*/QM42K* ISRCs only; rewrite catalog ledger files."""
from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAT = ROOT / "data" / "music_catalog"
AUDIO = {".wav", ".mp3", ".flac", ".m4a", ".aiff", ".aif", ".ogg", ".aac"}
CODE = re.compile(r"^(QZ[A-Z0-9]{10}|QM42K\d{7})$")
JUNK_NAME = re.compile(r"(?i)(grok-video|canvas-video|pexels)")


def format_isrc(c: str) -> str:
    c = re.sub(r"[^A-Za-z0-9]", "", c).upper()
    return f"{c[0:2]}-{c[2:5]}-{c[5:7]}-{c[7:12]}"


def extract_code(filename: str) -> str | None:
    stem = Path(filename).stem
    alnum = re.sub(r"[^A-Za-z0-9]", "", stem).upper()
    if len(alnum) < 12:
        return None
    tail = alnum[-12:]
    if CODE.match(tail):
        return tail
    return None


def title_from(filename: str, code: str) -> str:
    stem = Path(filename).stem
    # remove compact code variants
    t = re.sub(re.escape(code), "", stem, flags=re.I)
    t = re.sub(r"[_\-]+", " ", t).strip(" -_.")
    return t or stem


def main() -> int:
    roots = [
        Path(r"J:\ALL SOUND FILES"),
        Path(r"J:\Music 2024"),
        Path(r"J:\FINISHED BEAT STARS MUSIC"),
    ]
    found: dict[str, dict] = {}
    files_seen = 0
    for root in roots:
        if not root.exists():
            continue
        for dp, dns, fns in os.walk(root):
            low = dp.lower()
            if any(x in low for x in ("hearthstone", "fortnite", "battle.net", "epic games", ".git")):
                dns.clear()
                continue
            for fn in fns:
                files_seen += 1
                ext = Path(fn).suffix.lower()
                if ext not in AUDIO:
                    continue
                if JUNK_NAME.search(fn) or JUNK_NAME.search(dp):
                    continue
                code = extract_code(fn)
                if not code:
                    continue
                isrc = format_isrc(code)
                full = str(Path(dp) / fn)
                prefer = "DONE ALBUM" in full or "0 DONE ALBUM" in full
                prev = found.get(isrc)
                if prev and not prefer and "DONE ALBUM" in (prev.get("local_path") or ""):
                    continue
                found[isrc] = {
                    "title": title_from(fn, code),
                    "artist": "Excavationpro",
                    "album": Path(dp).name,
                    "isrc": isrc,
                    "upc": None,
                    "local_path": full,
                    "filename": fn,
                    "spotify_url": None,
                    "sources": ["filesystem"],
                }

    # preserve non-isrc catalog rows that are legit audio titles (optional light keep)
    cat_path = CAT / "excavationpro_catalog.json"
    old = json.loads(cat_path.read_text(encoding="utf-8")) if cat_path.exists() else {"tracks": [], "albums": []}
    non = []
    for t in old.get("tracks") or []:
        if t.get("isrc"):
            continue
        fn = t.get("filename") or ""
        path = t.get("local_path") or ""
        ext = Path(fn).suffix.lower()
        if ext and ext not in AUDIO:
            continue
        if JUNK_NAME.search(fn + path):
            continue
        non.append(t)

    # merge spotify album-only rows still in old via albums key
    albums = old.get("albums") or []

    tracks = list(found.values()) + non
    cat = {
        **{k: v for k, v in old.items() if k not in ("tracks", "track_count", "tracks_with_isrc", "tracks_with_local_file")},
        "tracks": tracks,
        "albums": albums,
        "track_count": len(tracks),
        "tracks_with_isrc": len(found),
        "tracks_with_local_file": sum(1 for t in tracks if t.get("local_path")),
        "isrc_cleanup": {
            "valid_isrcs": len(found),
            "policy": "QZ********** or QM42K******* trailing on audio stems only",
            "files_seen": files_seen,
        },
    }
    cat_path.write_text(json.dumps(cat, indent=2, ensure_ascii=False), encoding="utf-8")

    (CAT / "excavationpro_isrcs_unique.txt").write_text("\n".join(sorted(found)) + "\n", encoding="utf-8")
    fields = ["title", "artist", "album", "isrc", "upc", "spotify_url", "local_path", "filename"]
    with (CAT / "excavationpro_ISRC_READY_for_distributor.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for k in sorted(found):
            w.writerow({x: found[k].get(x) or "" for x in fields})

    print("files_seen", files_seen)
    print("valid_isrcs", len(found))
    print("has_92453", any("92453" in k for k in found))
    print("has_cypher_32714", any("32714" in k for k in found))
    bad = [k for k in found if not CODE.match(re.sub(r"[^A-Z0-9]", "", k))]
    print("invalid remaining", bad[:10], "count", len(bad))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
