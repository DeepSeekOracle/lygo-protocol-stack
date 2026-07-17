#!/usr/bin/env python3
"""
Strip false-positive ISRCs from catalog (UUID fragments, pexels, grok-video, canvas, images).
Keep DistroKid-style codes: QZ********** / QM42K******* on audio masters only.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

CAT = Path(__file__).resolve().parents[1] / "data" / "music_catalog"

# Real DistroKid / US indie codes used by Excavationpro releases
VALID_COMPACT = re.compile(r"^(?:QZ[A-Z0-9]{10}|QM42K\d{7})$", re.I)
# Extract only when glued at end of audio stem (DistroKid export naming)
END_ISRC = re.compile(
    r"(?i)(?:^|[\s_\-])(QZ[A-Z0-9]{10}|QM42K\d{7})$"
)
AUDIO_EXT = {".wav", ".mp3", ".flac", ".m4a", ".aiff", ".aif", ".ogg", ".aac"}
# Reject junk path/name tokens
JUNK = re.compile(
    r"(?i)(grok-video|canvas-video|pexels|tiktok|screenshot|\.jpg|\.png|\.mp4|\.webm|uuid)"
)


def compact(isrc: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", isrc or "").upper()


def format_isrc(c: str) -> str:
    c = compact(c)
    if len(c) != 12:
        return c
    return f"{c[0:2]}-{c[2:5]}-{c[5:7]}-{c[7:12]}"


def is_valid_music_isrc(isrc: str, filename: str = "", path: str = "") -> bool:
    c = compact(isrc)
    if not VALID_COMPACT.match(c):
        return False
    ext = Path(filename or path or "x.wav").suffix.lower()
    # Never accept non-audio as ISRC carriers (images/videos/docs)
    if filename and ext and ext not in AUDIO_EXT:
        return False
    name = (filename or "") + " " + (path or "")
    # Reject obvious non-music containers even if hex looked like an ISRC
    if re.search(r"(?i)(grok-video|canvas-video|pexels|\.jpg|\.png|\.mp4|\.webm|\.gif|\.pl$)", name):
        return False
    if filename:
        stem_alnum = re.sub(r"[^A-Za-z0-9]", "", Path(filename).stem).upper()
        # DistroKid pattern: code is the trailing 12 chars of the stem
        if not stem_alnum.endswith(c):
            return False
    return True


def main() -> int:
    cat_path = CAT / "excavationpro_catalog.json"
    cat = json.loads(cat_path.read_text(encoding="utf-8"))
    tracks = cat.get("tracks") or []
    kept = []
    dropped = []
    for t in tracks:
        isrc = t.get("isrc")
        fn = t.get("filename") or ""
        path = t.get("local_path") or ""
        if not isrc:
            # keep non-isrc audio only; drop images/videos
            if Path(fn).suffix.lower() in {".jpg", ".png", ".mp4", ".webm", ".gif", ".pl", ".jpeg"}:
                dropped.append(t)
                continue
            if re.search(r"(?i)(grok-video|canvas-video|pexels)", fn + path):
                dropped.append(t)
                continue
            kept.append(t)
            continue
        if is_valid_music_isrc(isrc, fn, path):
            t["isrc"] = format_isrc(isrc)
            kept.append(t)
        else:
            dropped.append(t)

    # Dedupe by isrc (prefer DONE ALBUM paths)
    by_isrc = {}
    no_isrc = []
    for t in kept:
        isrc = t.get("isrc")
        if not isrc:
            no_isrc.append(t)
            continue
        prev = by_isrc.get(isrc)
        if not prev:
            by_isrc[isrc] = t
            continue
        score = ("DONE ALBUM" in (t.get("local_path") or "")) * 2 + ("done_album" in str(t.get("sources")))
        pscore = ("DONE ALBUM" in (prev.get("local_path") or "")) * 2
        if score >= pscore:
            by_isrc[isrc] = t

    clean_tracks = list(by_isrc.values()) + no_isrc
    cat["tracks"] = clean_tracks
    cat["track_count"] = len(clean_tracks)
    cat["tracks_with_isrc"] = len(by_isrc)
    cat["tracks_with_local_file"] = sum(1 for t in clean_tracks if t.get("local_path"))
    cat["isrc_cleanup"] = {
        "dropped": len(dropped),
        "unique_valid_isrcs": len(by_isrc),
        "dropped_sample": [
            {"isrc": d.get("isrc"), "filename": d.get("filename")} for d in dropped[:40]
        ],
    }
    cat_path.write_text(json.dumps(cat, indent=2, ensure_ascii=False), encoding="utf-8")

    # rewrite unique + ready csv
    (CAT / "excavationpro_isrcs_unique.txt").write_text(
        "\n".join(sorted(by_isrc.keys())) + "\n", encoding="utf-8"
    )
    fields = ["title", "artist", "album", "isrc", "upc", "spotify_url", "local_path", "filename"]
    with (CAT / "excavationpro_ISRC_READY_for_distributor.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for isrc in sorted(by_isrc):
            r = by_isrc[isrc]
            w.writerow({k: r.get(k) or "" for k in fields})

    print("kept tracks", len(clean_tracks))
    print("valid isrcs", len(by_isrc))
    print("dropped", len(dropped))
    print("dropped sample:")
    for d in dropped[:15]:
        print(" ", d.get("isrc"), d.get("filename"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
