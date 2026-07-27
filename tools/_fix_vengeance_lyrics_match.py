#!/usr/bin/env python3
"""Rematch VENGEANCE CODEX monikers to lyrics and re-upload index."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
CAT = STACK / "data" / "music_catalog"
FOLDER = Path(r"C:\Users\justi\Music\BREAKER OF CODES")
HF_REPO = "DeepSeekOracle/excavationpro-music-stream"


def main() -> int:
    lyrics = json.loads((CAT / "lyrics" / "vengeance_codex_lyrics_clean.json").read_text(encoding="utf-8"))
    by_mon = {}
    for t in lyrics.get("tracks") or []:
        m = (t.get("moniker") or t.get("title") or "").upper().strip()
        if m:
            by_mon[m] = t

    title_to_mon: dict[str, str] = {}
    for p in FOLDER.glob("*.mp3"):
        mon = ""
        m = re.search(r"\((THE\s+[^)]+)\)", p.name, re.I)
        if m:
            mon = m.group(1).upper()
        m2 = re.search(r"=\s*(THE\s+.+?)\.mp3$", p.name, re.I)
        if m2:
            mon = m2.group(1).upper().strip()
        if re.search(r"\(BREAKER OF CODES\)", p.name, re.I):
            mon = "BREAKER OF CODES"
        base = re.sub(r"\s*\([^)]*\)\s*$", "", p.stem)
        base = re.sub(r"\s*=\s*.*$", "", base)
        base = base.replace("_", " ").strip().lower()
        base = re.sub(r"\s+", " ", base)
        if mon:
            title_to_mon[base] = mon
            title_to_mon[base.replace("'", "").replace("’", "")] = mon

    print("title_to_mon", title_to_mon)

    pl = json.loads((CAT / "public_stream_playlist.json").read_text(encoding="utf-8"))
    idx = json.loads((CAT / "lyrics" / "lyrics_index.json").read_text(encoding="utf-8"))
    matched = 0
    for t in pl.get("tracks") or []:
        if t.get("album") != "VENGEANCE CODEX":
            continue
        title = re.sub(r"\s+", " ", (t.get("title") or "").lower().strip())
        mon = (t.get("moniker") or "").upper()
        if not mon:
            mon = title_to_mon.get(title) or title_to_mon.get(title.replace("'", "").replace("’", "")) or ""
            if not mon:
                for k, v in title_to_mon.items():
                    if k in title or title in k:
                        mon = v
                        break
        t["moniker"] = mon
        lyr = by_mon.get(mon)
        if not lyr and mon:
            for k, v in by_mon.items():
                if mon in k or k in mon:
                    lyr = v
                    break
        body = (lyr or {}).get("lyrics") or ""
        if body and t.get("sha256"):
            idx["by_sha256"][t["sha256"]] = {
                "title": t.get("title"),
                "album": "VENGEANCE CODEX",
                "artist": "Excavationpro",
                "moniker": mon,
                "chapter_title": (lyr or {}).get("title") or mon,
                "lyrics": body,
                "copyright": idx.get("copyright"),
                "license": idx.get("license"),
            }
            if mon:
                idx["by_moniker"][mon] = idx["by_sha256"][t["sha256"]]
            matched += 1
        print(f"  {t.get('title')}: moniker={mon or '-'} lyrics={'Y' if body else 'N'}")

    idx["updated_utc"] = datetime.now(timezone.utc).isoformat()
    ak = "VENGEANCE_CODEX"
    if ak in (idx.get("albums") or {}):
        for tr in idx["albums"][ak]["tracks"]:
            tr["has_lyrics"] = tr.get("sha256") in idx["by_sha256"]
            for t in pl["tracks"]:
                if t.get("sha256") == tr.get("sha256"):
                    tr["moniker"] = t.get("moniker", "")
                    break

    (CAT / "public_stream_playlist.json").write_text(json.dumps(pl, indent=2) + "\n", encoding="utf-8")
    for dest in (
        CAT / "lyrics" / "lyrics_index.json",
        STACK / "docs" / "data" / "lyrics_index.json",
        STACK.parent / "Excavationpro" / "data" / "lyrics_index.json",
    ):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(idx, indent=2) + "\n", encoding="utf-8")
        print("wrote", dest)

    print("matched", matched, "lyrics entries", len(idx.get("by_sha256") or {}))

    from huggingface_hub import HfApi

    token = (Path.home() / ".cache" / "huggingface" / "token").read_text(encoding="utf-8").strip()
    api = HfApi(token=token)
    api.upload_file(
        path_or_fileobj=str(CAT / "lyrics" / "lyrics_index.json"),
        path_in_repo="lyrics/lyrics_index.json",
        repo_id=HF_REPO,
        repo_type="dataset",
        commit_message="Lyrics index: VENGEANCE CODEX moniker match",
    )
    api.upload_file(
        path_or_fileobj=str(CAT / "public_stream_playlist.json"),
        path_in_repo="public_stream_playlist.json",
        repo_id=HF_REPO,
        repo_type="dataset",
        commit_message="Playlist moniker tags: VENGEANCE CODEX",
    )
    print("HF OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
