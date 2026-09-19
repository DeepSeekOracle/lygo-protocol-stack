#!/usr/bin/env python3
"""Stage unique BLACK OUT songs missing from the listen playlist."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path

FOLDER = Path(r"C:\Users\justi\Music\BLACK OUT")
PLAYLIST = Path(r"I:\E Drive\lygo-protocol-stack\data\music_catalog\public_stream_playlist.json")
STAGE = Path(r"I:\E Drive\MUSIC_VAULT\_staging_black_out")
AUDIO_EXT = {".mp3", ".wav", ".flac", ".m4a"}


def norm(s: str) -> str:
    s = s.lower()
    s = re.sub(r"\([^)]*\)", " ", s)
    s = s.replace("_", " ")
    s = re.sub(
        r"\b(hd|hdx|converted|vocals|instrumental|feat justin helmer)\b",
        " ",
        s,
    )
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_stem_junk(p: Path) -> bool:
    rel = str(p.relative_to(FOLDER)).lower()
    name = p.name.lower()
    if "whitepaper" in rel or "lygo light math" in rel:
        return True
    if "quantum dots" in rel or "quatum dots" in rel:
        return True
    if "blockchain to lygo" in rel:
        return True
    if "savage soul" in rel:
        return True
    if re.match(r"^\d+(lygo|quantum)", name.replace(" ", "").lower()):
        return True
    if re.search(r"theory\d+\.wav$", name):
        return True
    if "mixea" in name or "vocals" in name or "converted" in name:
        return True
    if p.stat().st_size < 800_000:
        return True
    return False


def album_for(p: Path) -> str:
    rel = p.relative_to(FOLDER)
    skip = {
        "breaker of codes",
        "not uploaded to git",
        "_hub_stage",
        "_portal_stage",
        "album",
        "done",
    }
    dirs = [x for x in rel.parts[:-1] if x.lower() not in skip]
    if not dirs:
        return "BLACK OUT"
    d0 = dirs[0]
    if d0.lower().startswith("etrnity"):
        return "Eternity Frequencies"
    if d0.lower() == "july 30-26":
        if len(dirs) > 1 and "ritual" in dirs[1].lower():
            return "Ritual Codes"
        return "BLACK OUT"
    return d0


def pretty_name(p: Path) -> str:
    s = p.stem.replace("_", " ")
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r'[<>:"/\\|?*]', "", s)
    return s + p.suffix.lower()


def main() -> int:
    pl = json.loads(PLAYLIST.read_text(encoding="utf-8"))
    by_sha = {(t.get("sha256") or "").lower() for t in pl.get("tracks") or []}
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)

    groups: dict[str, list] = defaultdict(list)
    for p in FOLDER.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in AUDIO_EXT:
            continue
        rel = str(p.relative_to(FOLDER)).lower()
        if "grok _ x_files" in rel or "_analyze" in rel:
            continue
        digest = sha256_file(p)
        groups[norm(p.stem)].append((p, digest, p.stat().st_size))

    staged = []
    for items in groups.values():
        items = sorted(
            items,
            key=lambda x: (0 if x[0].suffix.lower() in {".wav", ".flac"} else 1, -x[2]),
        )
        best = items[0]
        if any(d in by_sha for _, d, _ in items):
            continue
        if is_stem_junk(best[0]):
            continue
        p = best[0]
        alb = album_for(p)
        dest_dir = STAGE / alb
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / pretty_name(p)
        if dest.exists():
            dest = dest_dir / (dest.stem + " b" + dest.suffix)
        shutil.copy2(p, dest)
        staged.append(alb)
        print(alb, dest.name, dest.stat().st_size, sep="\t")

    print("STAGED", len(staged))
    print(dict(Counter(staged)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
