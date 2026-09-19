#!/usr/bin/env python3
"""Attach DistroKid ISRCs / UPCs / official titles to listen-portal tracks."""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
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

RELEASES = CAT / "distrokid_releases_2026q3.json"

# DistroKid store title -> extra local search needles
HINTS = {
    "savage behind the smile": ["savage behind the smile", "behind the smile"],
    "strongest predator": ["predator the monster you created", "stronger predator", "strongest predator"],
    "unbroken and bitter": ["unbroken the bitter crown", "unbroken and bitter"],
    "born wild": ["beast king born wild", "born wild"],
    "not made to fold": ["iron heart not made to fold", "not made to fold"],
    "hate fuel": ["hate fuel swinging with a fist", "hate fuel"],
    "turned into steel": ["last drop turned into steel", "turned into steel"],
    "thorn king": ["thorns king of the ruins", "thorn king"],
    "i am the fire": ["i am the fire forged in flame", "i am the fire"],
    "siren in my skull": ["siren in my skull", "under the weight siren"],
    "words without meat": ["words without meat", "sorry your favorite word"],
    "gave you my all keys to every room": ["gave you my all", "keys to every room"],
    "nothing left to say prison made of air": ["nothing left to say", "prison made of air"],
    "our words mean nothing hollow phrases": ["our words mean nothing", "hollow phrases"],
    "the last word packing the wreckage": ["the last word", "packing the wreckage"],
    "under the lights paper cage": ["under the lights", "paper cage"],
    "blood moon standing in the wreckage": ["blood moon", "standing in the wreckage"],
    "burning embers after the burn": ["burning embers", "after the burn"],
    "cathedral crash": ["cathedral crash", "the altar s end", "altar's end"],
    "cathedral of static": ["cathedral of static", "kingdom undone"],
    "chasing shadows carved into my bones": ["chasing shadows", "carved into my bones"],
    "concrete king cold ground converted": ["concrete king cold ground", "cold ground"],
    "concrete king the concrete crown converted": ["concrete king the concrete crown", "the concrete crown"],
    "crown of scars converted": ["crown of scars"],
    "dark thoughts slim pickings converted": ["dark thoughts", "slim pickings"],
    "cathedral king of the broken": ["cathedral king of the broken", "king of the broken"],
    "cathedral beneath the gilded arch": ["beneath the gilded arch"],
    "hollow crown crown at my feet": ["hollow crown", "crown at my feet"],
    "sleeping through thunder": ["sleeping through thunder", "hollow vessel"],
    "before the credits roll": ["before the credits roll", "horizon"],
    "line in the ashs": ["line in the ashes", "last horizon"],
    "line in the ashes": ["line in the ashes", "last horizon"],
    "mirror lie stolen work of grief": ["mirror", "stolen work of grief"],
    "neon grave architect of chaos": ["neon grave", "architect of chaos"],
    "glass ceiling empire of the invisible": ["glass ceiling", "empire of the invisible"],
    "shattered glass invisible weight": ["shattered glass invisible weight"],
    "converted souls": ["converted souls"],
}


def tok(s: str) -> str:
    s = (s or "").lower()
    s = s.replace("&", " and ")
    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.sub(r"\bconverted\b", " ", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def score(dk: str, local: str) -> int:
    a, b = tok(dk), tok(local)
    if not a or not b:
        return 0
    if a == b:
        return 100
    if a in b or b in a:
        return 80 + min(len(a), len(b))
    at, bt = set(a.split()), set(b.split())
    if not at:
        return 0
    overlap = len(at & bt)
    if overlap == len(at) and overlap >= 2:
        return 70 + overlap
    if overlap >= max(2, (len(at) + 1) // 2):
        return 40 + overlap
    return overlap


def haystack(t: dict) -> str:
    bits = [t.get("title") or "", t.get("moniker") or ""]
    bits.extend(t.get("aliases") or [])
    return " | ".join(bits)


def main() -> int:
    data = json.loads(RELEASES.read_text(encoding="utf-8"))
    pl = load_playlist()
    tracks = pl.get("tracks") or []
    used: set[int] = set()
    matched = []
    unmatched = []

    for rel in data["releases"]:
        album = rel["album"]
        upc = rel["upc"]
        date = rel["date"]
        rid = rel["release_id"]
        for tr in rel["tracks"]:
            title = tr["title"]
            isrc = tr["isrc"]
            needles = HINTS.get(tok(title), [title])
            best_i, best_s = -1, 0
            for i, t in enumerate(tracks):
                if i in used:
                    continue
                hs = haystack(t)
                s = max(score(title, hs), max((score(n, hs) for n in needles), default=0))
                if s > best_s:
                    best_s, best_i = s, i
            if best_i < 0 or best_s < 40:
                unmatched.append({"album": album, "title": title, "isrc": isrc, "best_score": best_s})
                continue
            t = tracks[best_i]
            used.add(best_i)
            isrcs = list(t.get("isrcs") or [])
            if isrc not in isrcs:
                isrcs.append(isrc)
            aliases = list(t.get("aliases") or [])
            for extra in (title, t.get("title") or ""):
                if extra and extra not in aliases:
                    aliases.append(extra)
            t["isrcs"] = isrcs
            t["aliases"] = aliases
            t["album"] = album
            t["upc"] = upc
            t["distrokid_upc"] = upc
            t["distrokid_title"] = title
            t["release_date"] = date
            t["release_id"] = rid
            t["artist"] = t.get("artist") or "Excavationpro"
            matched.append(
                {
                    "isrc": isrc,
                    "dk_title": title,
                    "local_title": t.get("title"),
                    "album": album,
                    "score": best_s,
                }
            )

    pl["tracks"] = tracks
    save_playlist(pl)
    report = {
        "matched": len(matched),
        "unmatched": unmatched,
        "playlist_tracks": len(tracks),
        "utc": datetime.now(timezone.utc).isoformat(),
        "hits": matched,
    }
    (CAT / "distrokid_attach_last_run.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({"matched": len(matched), "unmatched": len(unmatched), "tracks": len(tracks)}, indent=2))
    for u in unmatched:
        print("UNMATCHED", u["album"], u["title"], u["isrc"], "score", u["best_score"])

    slim = slim_playlist(pl)
    save_playlist(pl)
    asian_html = ASIAN / "listen.html"
    if asian_html.is_file():
        surgical_inject_boot(asian_html, slim)
        git_push_repo(
            ASIAN,
            ["listen.html", "data", "listen-plugins"],
            "music: DistroKid ISRC/UPC attach for 2026 Q3 releases",
        )
    excav_html = EXCAV / "excavationpro-listen.html"
    if excav_html.is_file():
        surgical_inject_boot(excav_html, slim)
        git_push_repo(
            EXCAV,
            ["excavationpro-listen.html", "data", "listen-plugins"],
            "music: DistroKid ISRC/UPC attach (backup)",
        )
    try:
        from huggingface_hub import HfApi

        HfApi().upload_file(
            path_or_fileobj=str(CAT / "public_stream_playlist.json"),
            path_in_repo="public_stream_playlist.json",
            repo_id=HF_REPO,
            repo_type="dataset",
            commit_message="playlist DistroKid ISRC/UPC attach",
        )
        print("HF playlist OK")
    except Exception as e:
        print("HF playlist skip:", e)
    return 0 if not unmatched else 0


if __name__ == "__main__":
    raise SystemExit(main())
