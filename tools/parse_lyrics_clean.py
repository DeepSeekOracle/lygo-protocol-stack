#!/usr/bin/env python3
"""
Clean lyric extraction for Excavationpro listen portal.

- Keeps only lyric blocks ([INTRO], [VERSE], [CHORUS], [OUTRO], etc.)
- Strips STYLE / STRUCTURE / BEAT DIRECTION / VOCAL DIRECTION
- Strips chat, AI notes, production planning between songs
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

DROP_LINE_PREFIXES = (
    "style:",
    "structure:",
    "beat direction:",
    "vocal direction for gemini:",
    "vocal direction:",
    "artist:",
    "album:",
    "chapter:",
    "this response is ai-generated",
    "we need to",
    "we're locking",
    "we're moving",
    "i want to go",
    "next",
    "the user wants",
    "so i'll",
    "i'll craft",
    "i'll start",
    "i'll refine",
    "target is",
    "no chorus",
    "just four verses",
)

SECTION_KEEP = re.compile(
    r"^\[(INTRO|VERSE|CHORUS|HOOK|BRIDGE|OUTRO|PRE-?CHORUS|BREAK|SKIT|INTERLUDE|REFRAIN|DROP|TAG).*"
    r"\]\s*$",
    re.I,
)
TRACK_HEADER = re.compile(
    r"(?:^|\n)\s*(?:Track\s+(\d+)\s*[:\-]?\s*[\"']?([^\"'\n(]+?)[\"']?\s*$"
    r"|\(Track\s+(\d+)\s*:\s*[\"']?([^\"'\n)]+)[\"']?\))",
    re.I | re.M,
)
MONIKER = re.compile(r"\bTHE\s+[A-Z][A-Z\s']+\b")


def is_drop_line(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    low = s.lower()
    if any(low.startswith(p) for p in DROP_LINE_PREFIXES):
        return True
    if low.startswith("yeah.") and "debt" not in low and len(s) < 20:
        return False
    # chatty meta
    if "hybrid industrial" in low and "verse" not in low:
        return True
    if "for reference only" in low:
        return True
    if re.match(r"^\(?track\s+\d+", low):
        return True
    return False


def clean_lyrics_body(block: str) -> str:
    out: list[str] = []
    in_lyric_section = False
    for raw in block.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            if in_lyric_section and out and out[-1] != "":
                out.append("")
            continue
        if SECTION_KEEP.match(stripped):
            in_lyric_section = True
            # normalize tag to short form for display
            tag = re.sub(r"\s*—.*$", "", stripped)
            tag = re.sub(r",.*$", "", tag)
            out.append(tag.upper() if tag.startswith("[") else tag)
            continue
        if is_drop_line(stripped):
            in_lyric_section = False
            continue
        # stop at next production header after lyrics started
        if in_lyric_section and re.match(
            r"^(STYLE|STRUCTURE|BEAT|VOCAL|ARTIST|ALBUM|CHAPTER)\s*:", stripped, re.I
        ):
            in_lyric_section = False
            continue
        if in_lyric_section:
            # drop parenthetical echo tags like "... (first knife twisted)" keep main line
            main = re.sub(r"\s*\([^)]*\)\s*$", "", stripped)
            # remove trailing ellipsis doubles
            main = re.sub(r"\.{3,}", "…", main)
            if main:
                out.append(main)
    # trim trailing empties
    while out and out[-1] == "":
        out.pop()
    # collapse 3+ blanks
    cleaned: list[str] = []
    blank = 0
    for ln in out:
        if ln == "":
            blank += 1
            if blank <= 1:
                cleaned.append("")
        else:
            blank = 0
            cleaned.append(ln)
    return "\n".join(cleaned).strip()


def split_tracks(text: str) -> list[dict]:
    """Split multi-track lyric dump into {title, moniker, lyrics}."""
    # find starts
    starts: list[tuple[int, str, str]] = []
    for m in re.finditer(
        r"(?:^|\n)\s*(?:Track\s+(\d+)\s*[:\-]?\s*[\"']?([A-Za-z][^\"'\n]{2,80}?)[\"']?\s*$"
        r"|\(Track\s+(\d+)\s*:\s*[\"']?([A-Za-z][^\"'\n)]{2,80})[\"']?\))",
        text,
        re.I | re.M,
    ):
        num = m.group(1) or m.group(3) or ""
        title = (m.group(2) or m.group(4) or "").strip().strip('"').strip()
        title = re.sub(r"\.+$", "", title).strip()
        starts.append((m.start(), num, title))

    # also CHAPTER monikers as secondary
    tracks: list[dict] = []
    if not starts:
        # single blob
        body = clean_lyrics_body(text)
        if body:
            tracks.append({"title": "Untitled", "moniker": "", "lyrics": body, "track_num": ""})
        return tracks

    for i, (pos, num, title) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
        chunk = text[pos:end]
        # moniker from CHAPTER line
        moniker = ""
        ch = re.search(r"^CHAPTER:\s*\d+\s*—\s*(.+)$", chunk, re.M | re.I)
        if ch:
            moniker = ch.group(1).strip()
        # or from title if THE X
        if re.match(r"^THE\s+", title, re.I):
            moniker = title.upper()
        body = clean_lyrics_body(chunk)
        if not body or len(body) < 40:
            continue
        tracks.append(
            {
                "title": title,
                "moniker": moniker.upper() if moniker else "",
                "lyrics": body,
                "track_num": str(num),
            }
        )
    return tracks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="Raw lyrics .txt")
    ap.add_argument("--out", required=True, help="Clean JSON out")
    ap.add_argument("--album", default="VENGEANCE CODEX")
    ap.add_argument("--artist", default="Excavationpro")
    args = ap.parse_args()
    text = Path(args.src).read_text(encoding="utf-8", errors="replace")
    tracks = split_tracks(text)
    doc = {
        "signature": "Delta9Phi963-LYRICS-CLEAN-v1",
        "artist": args.artist,
        "album": args.album,
        "source_file": str(args.src),
        "track_count": len(tracks),
        "tracks": tracks,
        "license": "LYGO Music License v1.0 — free listen/download; all other rights reserved",
        "copyright": "© Justin Helmer / Excavationpro (Lightfather). Lyrics © steward.",
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "tracks": len(tracks), "out": str(out)}, indent=2))
    for t in tracks:
        print(f"  - [{t.get('track_num')}] {t['title']} / {t.get('moniker')} ({len(t['lyrics'])} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
