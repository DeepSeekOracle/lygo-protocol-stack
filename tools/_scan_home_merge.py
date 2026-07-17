#!/usr/bin/env python3
"""Full scan of HOME\\HOME (and parent ALL SOUND FILES DistroKid folder) → merge into catalog → rebuild site."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from music_catalog_recovery import (  # noqa: E402
    ARTIST_NAME,
    extract_isrcs,
    extract_upcs,
    fetch_spotify_artist_albums,
    merge_registry,
    scan_filesystem,
    write_outputs,
    write_browser_helper,
    SPOTIFY_ARTIST_ID,
)

CAT = Path(__file__).resolve().parents[1] / "data" / "music_catalog"
HOME = Path(r"J:\ALL SOUND FILES\. KICK STREAM FOLDER\HOME\HOME")
ALL_SOUND = Path(r"J:\ALL SOUND FILES")
DISTRO_SUB = HOME / "1 SOUNDCLOUD  DISTRO KID"


def main() -> int:
    roots = [
        HOME,
        DISTRO_SUB if DISTRO_SUB.exists() else HOME,
        ALL_SOUND,
        Path(r"J:\Music 2024"),
        Path(r"J:\FINISHED BEAT STARS MUSIC"),
    ]
    # de-dupe existing paths
    seen = set()
    uniq_roots = []
    for r in roots:
        s = str(r.resolve()) if r.exists() else str(r)
        if s not in seen and r.exists():
            seen.add(s)
            uniq_roots.append(r)

    print("Scanning roots:", flush=True)
    for r in uniq_roots:
        print(" ", r, flush=True)

    fs_rows, stats = scan_filesystem(uniq_roots, max_files=800_000)
    print("scan stats", stats, flush=True)

    # load previous catalog to preserve spotify if network fails
    prev_albums = []
    prev_path = CAT / "excavationpro_catalog.json"
    if prev_path.exists():
        prev = json.loads(prev_path.read_text(encoding="utf-8"))
        prev_albums = prev.get("albums") or []

    try:
        albums = fetch_spotify_artist_albums(SPOTIFY_ARTIST_ID)
        if not albums:
            albums = prev_albums
    except Exception as e:
        print("spotify fail, keep previous", e, flush=True)
        albums = prev_albums

    reg = merge_registry(fs_rows, albums)
    reg["scan_stats"] = stats
    reg["scan_roots"] = [str(r) for r in uniq_roots]
    reg["home_path"] = str(HOME)
    reg["notes"] = (reg.get("notes") or []) + [
        f"Full rescan including {HOME}",
        "Compared against DistroKid All music Restore.txt via build_music_registry_site.py",
    ]

    # HOME-only ISRC count
    home_isrcs = set()
    for row in fs_rows:
        p = (row.get("path") or "").replace("/", "\\").lower()
        if "kick stream folder" in p and "\\home\\home" in p:
            for i in row.get("isrcs") or []:
                home_isrcs.add(i)

    print(f"HOME path unique ISRCs: {len(home_isrcs)}", flush=True)
    print(f"Total unique ISRCs in merge: {reg['tracks_with_isrc']}", flush=True)
    print(f"Total track rows: {reg['track_count']}", flush=True)

    write_outputs(reg, CAT)
    write_browser_helper(CAT)

    # unique isrc file
    isrcs = sorted({t["isrc"] for t in reg["tracks"] if t.get("isrc")})
    (CAT / "excavationpro_isrcs_unique.txt").write_text("\n".join(isrcs), encoding="utf-8")
    # ready csv already via write_outputs - also write ISRC ready
    import csv

    by = {t["isrc"]: t for t in reg["tracks"] if t.get("isrc")}
    fields = ["title", "artist", "album", "isrc", "upc", "spotify_url", "local_path", "filename"]
    with (CAT / "excavationpro_ISRC_READY_for_distributor.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for isrc in sorted(by):
            r = by[isrc]
            w.writerow({k: r.get(k) or "" for k in fields})

    # home-only list
    home_rows = []
    for row in fs_rows:
        p = (row.get("path") or "").replace("/", "\\")
        if "KICK STREAM FOLDER" in p and "\\HOME\\HOME" in p.replace("/", "\\"):
            home_rows.append(row)
    (CAT / "home_home_scan.json").write_text(
        json.dumps(
            {
                "path": str(HOME),
                "matched_files": len(home_rows),
                "with_isrc": sum(1 for r in home_rows if r.get("isrcs")),
                "unique_isrcs": sorted(home_isrcs),
                "sample": home_rows[:30],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print("HOME matched files", len(home_rows), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
