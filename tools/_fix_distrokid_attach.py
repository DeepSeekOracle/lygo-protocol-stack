#!/usr/bin/env python3
"""Revert false DistroKid matches; attach remaining ISRCs by file SHA."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STACK / "tools"))
from safe_add_music_to_listen_portal import (  # noqa: E402
    load_playlist,
    save_playlist,
    slim_playlist,
    surgical_inject_boot,
    git_push_repo,
    ASIAN,
    EXCAV,
    CAT,
    HF_REPO,
)

REPORT = CAT / "distrokid_attach_last_run.json"
ROOT = Path(r"C:\Users\justi\Music\BLACK OUT")

BAD_DK = {
    "Deep in Thought",
    "Converted Souls",
    "Pain in the Speakers",
    "The Giver Is Retiring",
    "Cathedral King of the Broken",
}

# DistroKid title -> local file (prefer wav)
SHA_FILES = {
    "QT6692624421": ROOT / r"BREAKER OF CODES\BROKEN by Wind\_hub_stage\INVISIBLE MAN Servant to the Seen.wav",
    "QT6692624423": ROOT / r"BREAKER OF CODES\BROKEN by Wind\_hub_stage\Only Thing That Never Left.wav",
    "QT6692624424": ROOT / r"BREAKER OF CODES\BROKEN by Wind\_hub_stage\Pain in the Speakers.wav",
    "QT6692624425": ROOT / r"BREAKER OF CODES\BROKEN by Wind\_hub_stage\The Giver Is Retiring.wav",
    "QT6682675656": ROOT / r"BREAKER OF CODES\King of the Broken\MONOCHROME - The_Heavy_Grip.mp3",
}

# Official titles/albums for SHA attach
SHA_META = {
    "QT6692624421": ("Invisible Man", "In My Head", "859745631945", "2026-09-09", "1234167381"),
    "QT6692624423": ("Only Thing That Never Left", "In My Head", "859745631945", "2026-09-09", "1234167381"),
    "QT6692624424": ("Pain in the Speakers", "In My Head", "859745631945", "2026-09-09", "1234167381"),
    "QT6692624425": ("The Giver Is Retiring", "In My Head", "859745631945", "2026-09-09", "1234167381"),
    "QT6682675656": ("Monochrome", "War Dogs", "859744746909", "2026-08-30", "1234125872"),
}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def strip_dk(t: dict) -> None:
    for k in ("distrokid_title", "distrokid_upc", "upc", "release_date", "release_id"):
        t.pop(k, None)
    # keep album if it was set by ingest (Savage Soul etc.) only strip if we set distrokid album
    t["isrcs"] = []


def main() -> int:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    pl = load_playlist()
    tracks = pl.get("tracks") or []
    by_title = { (t.get("title") or ""): t for t in tracks }

    # revert false hits
    revert_local = set()
    for h in report.get("hits") or []:
        if h.get("dk_title") in BAD_DK or int(h.get("score") or 0) < 70:
            revert_local.add(h.get("local_title"))
        # swapped beast/born wild
        if h.get("dk_title") == "Beast King" and h.get("local_title") == "BEAST King Born Wild":
            revert_local.add(h.get("local_title"))
        if h.get("dk_title") == "Born Wild" and h.get("local_title") == "BEAST King":
            revert_local.add(h.get("local_title"))

    reverted = 0
    for t in tracks:
        if (t.get("title") or "") in revert_local or (t.get("distrokid_title") in BAD_DK):
            strip_dk(t)
            reverted += 1

    # correct Beast King / Born Wild
    beast = by_title.get("BEAST King")
    born = by_title.get("BEAST King Born Wild")
    if beast:
        beast["isrcs"] = ["QT6692634135"]
        beast["album"] = "Stronger Predator"
        beast["upc"] = beast["distrokid_upc"] = "859745817639"
        beast["distrokid_title"] = "Beast King"
        beast["release_date"] = "2026-09-13"
        beast["release_id"] = "1234175931"
    if born:
        born["isrcs"] = ["QT6692634136"]
        born["album"] = "Stronger Predator"
        born["upc"] = born["distrokid_upc"] = "859745817639"
        born["distrokid_title"] = "Born Wild"
        born["release_date"] = "2026-09-13"
        born["release_id"] = "1234175931"

    by_sha = { (t.get("sha256") or "").lower(): t for t in tracks }
    sha_hits = []
    missing_files = []
    for isrc, path in SHA_FILES.items():
        if not path.is_file():
            missing_files.append(str(path))
            continue
        digest = sha256_file(path)
        t = by_sha.get(digest)
        title, album, upc, date, rid = SHA_META[isrc]
        if not t:
            missing_files.append(f"no playlist sha {title} {digest[:16]}")
            continue
        t["isrcs"] = [isrc]
        t["album"] = album
        t["upc"] = t["distrokid_upc"] = upc
        t["distrokid_title"] = title
        t["release_date"] = date
        t["release_id"] = rid
        aliases = list(t.get("aliases") or [])
        if title not in aliases:
            aliases.append(title)
        t["aliases"] = aliases
        sha_hits.append({"isrc": isrc, "title": title, "local": t.get("title")})

    pl["tracks"] = tracks
    save_playlist(pl)
    slim = slim_playlist(pl)
    save_playlist(pl)
    print(json.dumps({"reverted": reverted, "sha_hits": sha_hits, "missing": missing_files}, indent=2))

    asian = ASIAN / "listen.html"
    if asian.is_file():
        surgical_inject_boot(asian, slim)
        git_push_repo(ASIAN, ["listen.html", "data"], "music: fix DistroKid ISRC false matches")
    excav = EXCAV / "excavationpro-listen.html"
    if excav.is_file():
        surgical_inject_boot(excav, slim)
        git_push_repo(EXCAV, ["excavationpro-listen.html", "data"], "music: fix DistroKid ISRC false matches (backup)")
    try:
        from huggingface_hub import HfApi

        HfApi().upload_file(
            path_or_fileobj=str(CAT / "public_stream_playlist.json"),
            path_in_repo="public_stream_playlist.json",
            repo_id=HF_REPO,
            repo_type="dataset",
            commit_message="playlist DistroKid ISRC fix",
        )
        print("HF playlist OK")
    except Exception as e:
        print("HF skip", e)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
