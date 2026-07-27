#!/usr/bin/env python3
"""
Add a local album folder to the sovereign listen portal pipeline.

1) Pick unique master MP3s (prefer clean title; skip dupes by size/hash)
2) CAS hash + copy into MUSIC_VAULT public_stream
3) Merge into public_stream_playlist.json
4) Optional HF upload of new stream files
5) Optional --hub rebuild listen HTML
6) Attach lyrics monikers from clean lyrics JSON

Usage:
  python tools/add_album_to_listen_portal.py ^
    --folder "C:\\Users\\justi\\Music\\BREAKER OF CODES" ^
    --album "VENGEANCE CODEX" ^
    --lyrics-json data/music_catalog/lyrics/vengeance_codex_lyrics_clean.json ^
    --encode --publish-hf --hub
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
CAT = STACK / "data" / "music_catalog"
DOCS = STACK / "docs"
EXCAV = STACK.parent / "Excavationpro"
VAULT = Path(r"I:\E Drive\MUSIC_VAULT")
STREAM_DIR = VAULT / "public_stream"
HF_REPO = "DeepSeekOracle/excavationpro-music-stream"
BASE_URL = f"https://huggingface.co/datasets/{HF_REPO}/resolve/main/stream"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def pretty_title(stem: str) -> str:
    s = stem
    # drop parenthetical moniker
    s = re.sub(r"\s*\([^)]*\)\s*$", "", s)
    s = re.sub(r"\s*=\s*.*$", "", s)
    s = s.replace("_", " ").replace("'", "'")
    s = re.sub(r"\s+", " ", s).strip()
    # title case careful
    return s


def extract_moniker(name: str) -> str:
    m = re.search(r"\((THE\s+[^)]+)\)", name, re.I)
    if m:
        return m.group(1).strip().upper()
    m = re.search(r"=\s*(THE\s+.+)$", name, re.I)
    if m:
        return m.group(1).strip().upper()
    m = re.search(r"\((BREAKER OF CODES)\)", name, re.I)
    if m:
        return "BREAKER OF CODES"
    return ""


def pick_unique_mp3s(folder: Path) -> list[Path]:
    """Prefer clean-named mp3; skip alternate tags if same size as clean."""
    files = [p for p in folder.glob("*.mp3") if p.is_file()]
    # group by normalized base title
    groups: dict[str, list[Path]] = {}
    for p in files:
        base = pretty_title(p.stem).lower()
        groups.setdefault(base, []).append(p)
    chosen: list[Path] = []
    for base, paths in groups.items():
        # prefer no paren / no =
        clean = [p for p in paths if "(" not in p.name and "=" not in p.name]
        if clean:
            # shortest name among clean
            chosen.append(sorted(clean, key=lambda x: len(x.name))[0])
        else:
            chosen.append(sorted(paths, key=lambda x: len(x.name))[0])
    return sorted(chosen, key=lambda p: p.name.lower())


def encode_or_copy(src: Path, dest: Path) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size > 1000:
        return "exists"
    # source already mp3 of reasonable size → copy
    shutil.copy2(src, dest)
    return "copy"


def load_playlist() -> dict:
    p = CAT / "public_stream_playlist.json"
    return json.loads(p.read_text(encoding="utf-8"))


def save_playlist(pl: dict) -> None:
    text = json.dumps(pl, indent=2) + "\n"
    targets = [
        CAT / "public_stream_playlist.json",
        VAULT / "manifest" / "public_stream_playlist.json",
        DOCS / "data" / "public_stream_playlist.json",
        EXCAV / "data" / "public_stream_playlist.json",
    ]
    for t in targets:
        try:
            t.parent.mkdir(parents=True, exist_ok=True)
            t.write_text(text, encoding="utf-8")
        except OSError as e:
            print(f"[warn] playlist write {t}: {e}")


def load_lyrics_index() -> dict:
    p = CAT / "lyrics" / "lyrics_index.json"
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return {
        "signature": "Delta9Phi963-LYRICS-INDEX-v1",
        "artist": "Excavationpro",
        "copyright": "© Justin Helmer / Excavationpro (Lightfather). Lyrics © steward.",
        "license": "LYGO Music License v1.0 — free listen/download; all other rights reserved. https://eternalhaven.ca/lygo-music-license.html",
        "by_sha256": {},
        "by_moniker": {},
        "albums": {},
        "updated_utc": "",
    }


def save_lyrics_index(idx: dict) -> None:
    idx["updated_utc"] = utc_now()
    text = json.dumps(idx, indent=2) + "\n"
    for t in (
        CAT / "lyrics" / "lyrics_index.json",
        DOCS / "data" / "lyrics_index.json",
        EXCAV / "data" / "lyrics_index.json",
    ):
        try:
            t.parent.mkdir(parents=True, exist_ok=True)
            t.write_text(text, encoding="utf-8")
        except OSError as e:
            print(f"[warn] lyrics write {t}: {e}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--folder", required=True)
    ap.add_argument("--album", default="VENGEANCE CODEX")
    ap.add_argument("--artist", default="Excavationpro")
    ap.add_argument("--lyrics-json", default="")
    ap.add_argument("--encode", action="store_true")
    ap.add_argument("--publish-hf", action="store_true")
    ap.add_argument("--hub", action="store_true")
    args = ap.parse_args()

    folder = Path(args.folder)
    if not folder.is_dir():
        print("folder missing", folder)
        return 2

    masters = pick_unique_mp3s(folder)
    print(f"unique masters: {len(masters)}")
    for m in masters:
        print(" ", m.name, "→", pretty_title(m.stem), extract_moniker(m.name))

    # lyrics by moniker
    moniker_lyrics: dict[str, dict] = {}
    if args.lyrics_json:
        lj = Path(args.lyrics_json)
        if lj.is_file():
            clean = json.loads(lj.read_text(encoding="utf-8"))
            for t in clean.get("tracks") or []:
                mon = (t.get("moniker") or t.get("title") or "").upper().strip()
                if mon:
                    moniker_lyrics[mon] = t

    pl = load_playlist()
    existing = {t.get("sha256") for t in pl.get("tracks") or [] if t.get("sha256")}
    new_tracks = []
    uploaded_paths = []

    for src in masters:
        digest = sha256_file(src)
        # sharded path if needed — keep flat if < 10000 flat; use first2 hex shard always when flat full
        flat = STREAM_DIR / f"{digest}.mp3"
        shard = STREAM_DIR / digest[:2] / f"{digest}.mp3"
        # prefer existing location
        if flat.is_file():
            dest = flat
            hf_path = f"stream/{digest}.mp3"
        elif shard.is_file():
            dest = shard
            hf_path = f"stream/{digest[:2]}/{digest}.mp3"
        else:
            # new: use shard layout (safer for 10k dir limit)
            dest = shard
            hf_path = f"stream/{digest[:2]}/{digest}.mp3"

        title = pretty_title(src.stem)
        moniker = extract_moniker(src.name)
        aliases = [title, src.stem]
        if moniker:
            aliases.append(moniker)
            aliases.append(f"{title} ({moniker})")

        if args.encode or True:
            status = encode_or_copy(src, dest)
            print(f"  encode {title}: {status} sha={digest[:12]}…")

        stream_url = f"{BASE_URL}/{digest[:2]}/{digest}.mp3" if "/stream/" + digest[:2] in ("/stream/" + digest[:2]) else f"{BASE_URL}/{digest}.mp3"
        # correct URL from hf_path
        stream_url = f"https://huggingface.co/datasets/{HF_REPO}/resolve/main/{hf_path}"

        entry = {
            "sha256": digest,
            "title": title,
            "aliases": aliases,
            "isrcs": [],
            "size": dest.stat().st_size if dest.is_file() else src.stat().st_size,
            "stream_file": dest.name,
            "local_stream": str(dest),
            "stream_url": stream_url,
            "hf_path": hf_path,
            "album": args.album,
            "artist": args.artist,
            "moniker": moniker,
            "source_folder": str(folder),
            "added_utc": utc_now(),
        }
        if digest not in existing:
            pl.setdefault("tracks", []).append(entry)
            existing.add(digest)
            new_tracks.append(entry)
            uploaded_paths.append((dest, hf_path))
        else:
            # update metadata on existing
            for t in pl["tracks"]:
                if t.get("sha256") == digest:
                    t["album"] = args.album
                    t["artist"] = args.artist
                    t["moniker"] = moniker
                    t["title"] = title
                    t["aliases"] = list(dict.fromkeys((t.get("aliases") or []) + aliases))
                    t["stream_url"] = stream_url
                    t["hf_path"] = hf_path
                    break
            new_tracks.append(entry)
            if dest.is_file():
                uploaded_paths.append((dest, hf_path))

    # lyrics index
    idx = load_lyrics_index()
    album_key = args.album.upper().replace(" ", "_")
    idx.setdefault("albums", {})[album_key] = {
        "album": args.album,
        "artist": args.artist,
        "tracks": [],
    }
    for e in new_tracks:
        mon = (e.get("moniker") or "").upper()
        # map moniker lyrics; also try THE X match
        lyr = moniker_lyrics.get(mon)
        if not lyr and mon:
            for k, v in moniker_lyrics.items():
                if mon in k or k in mon:
                    lyr = v
                    break
        # BREAKER OF CODES moniker — no lyrics yet in first 8 chapters
        body = (lyr or {}).get("lyrics") or ""
        chapter_title = (lyr or {}).get("title") or mon or e["title"]
        if body:
            idx["by_sha256"][e["sha256"]] = {
                "title": e["title"],
                "album": args.album,
                "artist": args.artist,
                "moniker": mon,
                "chapter_title": chapter_title,
                "lyrics": body,
                "copyright": idx["copyright"],
                "license": idx["license"],
            }
            if mon:
                idx["by_moniker"][mon] = idx["by_sha256"][e["sha256"]]
        idx["albums"][album_key]["tracks"].append(
            {
                "sha256": e["sha256"],
                "title": e["title"],
                "moniker": mon,
                "has_lyrics": bool(body),
                "stream_url": e["stream_url"],
            }
        )

    save_playlist(pl)
    save_lyrics_index(idx)

    # album manifest
    man = {
        "signature": "Delta9Phi963-ALBUM-ADD-v1",
        "album": args.album,
        "artist": args.artist,
        "folder": str(folder),
        "added_utc": utc_now(),
        "track_count": len(new_tracks),
        "tracks": new_tracks,
        "lyrics_matched": sum(1 for t in idx["albums"][album_key]["tracks"] if t.get("has_lyrics")),
    }
    man_path = CAT / "albums" / "vengeance_codex_manifest.json"
    man_path.parent.mkdir(parents=True, exist_ok=True)
    man_path.write_text(json.dumps(man, indent=2) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "playlist_tracks": len(pl.get("tracks") or []),
                "album_tracks": len(new_tracks),
                "lyrics_matched": man["lyrics_matched"],
                "manifest": str(man_path),
            },
            indent=2,
        )
    )

    if args.publish_hf:
        try:
            from huggingface_hub import HfApi

            token = None
            tp = Path.home() / ".cache" / "huggingface" / "token"
            if tp.is_file():
                token = tp.read_text(encoding="utf-8").strip()
            api = HfApi(token=token)
            for local, repo_path in uploaded_paths:
                if not local.is_file():
                    continue
                print(f"HF upload {repo_path} …")
                api.upload_file(
                    path_or_fileobj=str(local),
                    path_in_repo=repo_path,
                    repo_id=HF_REPO,
                    repo_type="dataset",
                    commit_message=f"Add {args.album}: {local.name}",
                )
            # playlist + lyrics index
            api.upload_file(
                path_or_fileobj=str(CAT / "public_stream_playlist.json"),
                path_in_repo="public_stream_playlist.json",
                repo_id=HF_REPO,
                repo_type="dataset",
                commit_message=f"Playlist update: {args.album}",
            )
            api.upload_file(
                path_or_fileobj=str(CAT / "lyrics" / "lyrics_index.json"),
                path_in_repo="lyrics/lyrics_index.json",
                repo_id=HF_REPO,
                repo_type="dataset",
                commit_message=f"Lyrics index: {args.album}",
            )
            print("HF publish OK")
        except Exception as e:
            print("HF publish failed:", type(e).__name__, e)
            return 1

    if args.hub:
        # rebuild listen hub via existing tool
        sys.path.insert(0, str(STACK / "tools"))
        hub = STACK / "tools" / "build_public_music_stream.py"
        import subprocess

        r = subprocess.run(
            [sys.executable, str(hub), "--hub", "--base-url", BASE_URL],
            cwd=str(STACK),
        )
        print("hub rebuild exit", r.returncode)
        if r.returncode != 0:
            return r.returncode

    # Live-map music into Haven Star Chart (tagged albums → track stars)
    if args.publish_hf or args.hub or args.encode:
        import subprocess

        chart = subprocess.run(
            [
                sys.executable,
                str(STACK / "tools" / "map_music_to_star_chart.py"),
                "--rebuild-chart",
                "--sync-excav",
            ],
            cwd=str(STACK),
        )
        print("star chart music map exit", chart.returncode)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
