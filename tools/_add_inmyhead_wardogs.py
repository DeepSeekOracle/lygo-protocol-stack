#!/usr/bin/env python3
"""Add remaining DistroKid In My Head / War Dogs masters that were not hashed in."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
TOOL = STACK / "tools" / "safe_add_music_to_listen_portal.py"
ROOT = Path(r"C:\Users\justi\Music\BLACK OUT")

FILES = [
    (
        ROOT / r"BREAKER OF CODES\BROKEN by Wind\_hub_stage\INVISIBLE MAN Servant to the Seen.wav",
        "Invisible Man",
        "In My Head",
        "859745631945",
        "QT6692624421",
    ),
    (
        ROOT / r"BREAKER OF CODES\BROKEN by Wind\_hub_stage\Only Thing That Never Left.wav",
        "Only Thing That Never Left",
        "In My Head",
        "859745631945",
        "QT6692624423",
    ),
    (
        ROOT / r"BREAKER OF CODES\BROKEN by Wind\_hub_stage\Pain in the Speakers.wav",
        "Pain in the Speakers",
        "In My Head",
        "859745631945",
        "QT6692624424",
    ),
    (
        ROOT / r"BREAKER OF CODES\BROKEN by Wind\_hub_stage\The Giver Is Retiring.wav",
        "The Giver Is Retiring",
        "In My Head",
        "859745631945",
        "QT6692624425",
    ),
    (
        ROOT / r"BREAKER OF CODES\King of the Broken\MONOCHROME - The_Heavy_Grip.mp3",
        "Monochrome",
        "War Dogs",
        "859744746909",
        "QT6682675656",
    ),
    (
        ROOT / r"BREAKER OF CODES\King of the Broken\CATHEDRAL King_of_the_Broken.mp3",
        "Cathedral King of the Broken",
        "War Dogs",
        "859744746909",
        "QT6682675657",
    ),
]


def main() -> int:
    for path, title, album, upc, isrc in FILES:
        if not path.is_file():
            print("MISSING FILE", path)
            continue
        print("ADD", title, path.name)
        r = subprocess.run(
            [
                sys.executable,
                str(TOOL),
                "--file",
                str(path),
                "--title",
                title,
                "--album",
                album,
                "--upc",
                upc,
                "--artist",
                "Excavationpro",
                "--publish-hf",
            ],
            cwd=str(STACK),
        )
        if r.returncode != 0:
            return r.returncode
        # attach ISRC on the new title
        from safe_add_music_to_listen_portal import load_playlist, save_playlist

        pl = load_playlist()
        for t in pl.get("tracks") or []:
            if (t.get("title") or "") == title or title in (t.get("aliases") or []):
                isrcs = list(t.get("isrcs") or [])
                if isrc not in isrcs:
                    isrcs.append(isrc)
                t["isrcs"] = isrcs
                t["distrokid_title"] = title
                t["album"] = album
                t["upc"] = t["distrokid_upc"] = upc
        save_playlist(pl)
    r = subprocess.run(
        [sys.executable, str(TOOL), "--inject-playlist-only", "--deploy-asian"],
        cwd=str(STACK),
    )
    if r.returncode != 0:
        return r.returncode
    return subprocess.run(
        [sys.executable, str(TOOL), "--promote-backup-excav"],
        cwd=str(STACK),
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
