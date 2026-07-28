#!/usr/bin/env python3
"""
Ingest:
  - I:\\Actors\\RoadtoknowwhereQZZ7Q2672138.wav (DistroKid UPC release)
  - C:\\Users\\justi\\Music\\NOT UPLOADED to Git\\* (Hollow Codex + singles)

Encode → MUSIC_VAULT public_stream → playlist + lyrics_index → optional HF + hub.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
CAT = STACK / "data" / "music_catalog"
DOCS = STACK / "docs"
EXCAV = Path(r"D:\Excavationpro")
if not EXCAV.is_dir():
    EXCAV = STACK.parent / "Excavationpro"
VAULT = Path(r"I:\E Drive\MUSIC_VAULT")
STREAM_DIR = VAULT / "public_stream"
HF_REPO = "DeepSeekOracle/excavationpro-music-stream"
BASE = f"https://huggingface.co/datasets/{HF_REPO}/resolve/main"

NOT_UPLOADED = Path(r"C:\Users\justi\Music\NOT UPLOADED to Git")
HOLLOW_DIR = NOT_UPLOADED / "HOLLOW CODEX ALBUM"
HOLLOW_TXT = HOLLOW_DIR / "THE HOLLOW CODEX ALBUM STRUCTURE.txt"
ROAD_WAV = Path(r"I:\Actors\RoadtoknowwhereQZZ7Q2672138.wav")

ARTIST = "Excavationpro"
LABEL = "Excavationpro"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def encode_to_mp3(src: Path, dest: Path, bitrate: str = "160k") -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size > 2000:
        return "exists"
    if src.suffix.lower() == ".mp3":
        shutil.copy2(src, dest)
        return "copy"
    # wav/flac/etc → ffmpeg 160k mp3
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-codec:a",
        "libmp3lame",
        "-b:a",
        bitrate,
        "-ar",
        "44100",
        "-ac",
        "2",
        str(dest),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not dest.is_file():
        raise RuntimeError(f"ffmpeg failed for {src}: {r.stderr[-400:]}")
    return "encoded"


def clean_lyrics_body(block: str) -> str:
    """Keep performance-facing lyric lines; drop STYLE/BEAT chat noise."""
    lines_out: list[str] = []
    skip_prefixes = (
        "ARTIST:",
        "ALBUM:",
        "CHAPTER:",
        "STYLE:",
        "STRUCTURE:",
        "BEAT DIRECTION",
        "VOCAL DIRECTION",
        "do two at a time",
        "We need to generate",
        "We're pushing",
        "Let's craft",
        "The user's deep",
        "Here are Tracks",
        "both locked",
    )
    for raw in block.splitlines():
        line = raw.strip()
        if not line:
            if lines_out and lines_out[-1] != "":
                lines_out.append("")
            continue
        if any(line.startswith(p) for p in skip_prefixes):
            continue
        if line.startswith("A slow,") or line.startswith("A steady,") or line.startswith("Baritone,"):
            continue
        if "Gemini" in line or "PRO." in line and "Track" in line:
            continue
        # drop echo parentheticals optionally keep full line
        lines_out.append(line)
    # trim trailing empties
    while lines_out and lines_out[-1] == "":
        lines_out.pop()
    return "\n".join(lines_out).strip()


def parse_hollow_codex_lyrics(path: Path) -> dict[str, dict]:
    """Map moniker (THE FLATLINE, …) → lyrics dict."""
    text = path.read_text(encoding="utf-8", errors="replace")
    # Normalize FADEOUT moniker
    monikers = [
        "THE FLATLINE",
        "THE SHIFT",
        "THE SILENCE",
        "THE FADEOUT",
        "THE VANISHED",
        "THE MORNING AFTER",
        "THE ECHO",
        "THE LAST SPARK",
    ]
    # Also accept FADEOUT as THE FADEOUT in files
    results: dict[str, dict] = {}

    # Prefer headers like: (Track 2: "THE SHIFT") or Track 1: "THE FLATLINE"
    # Use the LAST match so chat preambles don't steal lyrics from later real blocks.
    for mon in monikers:
        header = re.compile(
            rf"(?:\(Track\s+\d+:\s*[\"“]{re.escape(mon)}[\"”]\)|"
            rf"Track\s+\d+:\s*[\"“]{re.escape(mon)}[\"”])",
            re.I,
        )
        headers = list(header.finditer(text))
        if not headers and mon == "THE FADEOUT":
            headers = list(
                re.finditer(
                    r"(?:\(Track\s+\d+:\s*[\"“]THE FADEOUT[\"”]\)|Track\s+\d+:\s*[\"“]THE FADEOUT[\"”])",
                    text,
                    re.I,
                )
            )
        if not headers:
            continue
        start = headers[-1].end()
        # next track header after this
        nxt = re.search(
            r"\(Track\s+\d+:\s*[\"“]THE\s+|Track\s+\d+:\s*[\"“]THE\s+",
            text[start:],
            re.I,
        )
        chunk = text[start : start + nxt.start()] if nxt else text[start:]
        lyr_m = re.search(r"(\[INTRO[\s\S]+)", chunk, re.I)
        if not lyr_m:
            continue
        body = clean_lyrics_body(lyr_m.group(1))
        if len(body) < 80:
            continue
        ch_m = re.search(r"CHAPTER:\s*(.+)", chunk)
        results[mon] = {
            "moniker": mon,
            "title": mon,
            "chapter": (ch_m.group(1).strip() if ch_m else ""),
            "lyrics": body,
            "album": "THE HOLLOW CODEX",
            "artist": ARTIST,
        }

    return results


def moniker_from_filename(name: str) -> str:
    # "THE FLATLINE -The_Absence_of_War.mp3" or "FADEOUT - Rest_..."
    stem = Path(name).stem
    m = re.match(r"^(THE\s+[A-Z][A-Z\s]+?)\s*[-–]", stem, re.I)
    if m:
        return re.sub(r"\s+", " ", m.group(1).strip().upper())
    m = re.match(r"^(FADEOUT)\s*[-–]", stem, re.I)
    if m:
        return "THE FADEOUT"
    # "Dirt_On_My_Skin"
    return ""


def pretty_title_from_file(name: str) -> str:
    stem = Path(name).stem
    # Hollow: "THE ECHO - Buried_Heartbeat" → prefer moniker + subtitle
    m = re.match(r"^(THE\s+.+?|FADEOUT)\s*[-–]\s*(.+)$", stem, re.I)
    if m:
        mon = m.group(1).strip()
        if mon.upper() == "FADEOUT":
            mon = "THE FADEOUT"
        sub = m.group(2).replace("_", " ").strip()
        return f"{mon.title().replace('The ', 'THE ')} — {sub}"
    s = stem.replace("_", " ")
    s = re.sub(r"QZZ7Q\d+", "", s, flags=re.I)
    s = re.sub(r"\s+", " ", s).strip()
    # Roadtoknowwhere → Road to Know Where
    if re.search(r"road\s*to\s*know\s*where|roadtoknowwhere", s, re.I):
        return "Road to Know Where"
    return s


def load_playlist() -> dict:
    p = CAT / "public_stream_playlist.json"
    return json.loads(p.read_text(encoding="utf-8"))


def save_playlist(pl: dict) -> None:
    pl["generated_at"] = utc_now()
    text = json.dumps(pl, indent=2, ensure_ascii=False) + "\n"
    for t in (
        CAT / "public_stream_playlist.json",
        VAULT / "manifest" / "public_stream_playlist.json",
        DOCS / "data" / "public_stream_playlist.json",
        EXCAV / "data" / "public_stream_playlist.json",
    ):
        try:
            t.parent.mkdir(parents=True, exist_ok=True)
            t.write_text(text, encoding="utf-8")
        except OSError as e:
            print(f"[warn] playlist {t}: {e}")


def load_lyrics_index() -> dict:
    p = CAT / "lyrics" / "lyrics_index.json"
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return {
        "signature": "Delta9Phi963-LYRICS-INDEX-v1",
        "artist": ARTIST,
        "copyright": "© Justin Helmer / Excavationpro (Lightfather). Lyrics © steward.",
        "license": "LYGO Music License v1.0 — free listen/download; all other rights reserved.",
        "by_sha256": {},
        "by_moniker": {},
        "albums": {},
        "updated_utc": "",
    }


def save_lyrics_index(idx: dict) -> None:
    idx["updated_utc"] = utc_now()
    text = json.dumps(idx, indent=2, ensure_ascii=False) + "\n"
    for t in (
        CAT / "lyrics" / "lyrics_index.json",
        DOCS / "data" / "lyrics_index.json",
        EXCAV / "data" / "lyrics_index.json",
    ):
        try:
            t.parent.mkdir(parents=True, exist_ok=True)
            t.write_text(text, encoding="utf-8")
        except OSError as e:
            print(f"[warn] lyrics {t}: {e}")


def upsert_track(pl: dict, entry: dict) -> tuple[bool, Path]:
    """Add or update track by sha256. Returns (is_new, dest_path)."""
    digest = entry["sha256"]
    existing = {t.get("sha256"): t for t in pl.get("tracks") or []}
    if digest in existing:
        t = existing[digest]
        for k, v in entry.items():
            if v is not None and v != "" and k != "sha256":
                if k == "aliases":
                    t["aliases"] = list(dict.fromkeys((t.get("aliases") or []) + list(v)))
                elif k == "isrcs" and t.get("isrcs"):
                    t["isrcs"] = list(dict.fromkeys(list(t.get("isrcs") or []) + list(v)))
                else:
                    t[k] = v
        return False, Path(entry.get("local_stream") or "")
    pl.setdefault("tracks", []).append(entry)
    return True, Path(entry.get("local_stream") or "")


def process_audio(
    src: Path,
    *,
    title: str,
    album: str,
    moniker: str = "",
    extra: dict | None = None,
) -> dict:
    # Hash master for identity (prefer master wav/mp3 as source of truth)
    digest = sha256_file(src)
    dest = STREAM_DIR / digest[:2] / f"{digest}.mp3"
    status = encode_to_mp3(src, dest)
    print(f"  [{status}] {title}  sha={digest[:12]}…  → {dest.name}")
    hf_path = f"stream/{digest[:2]}/{digest}.mp3"
    aliases = [title, src.stem]
    if moniker:
        aliases.extend([moniker, f"{title} ({moniker})"])
    entry = {
        "sha256": digest,
        "title": title,
        "aliases": list(dict.fromkeys(aliases)),
        "isrcs": [],
        "size": dest.stat().st_size if dest.is_file() else 0,
        "stream_file": dest.name,
        "local_stream": str(dest),
        "stream_url": f"{BASE}/{hf_path}",
        "hf_path": hf_path,
        "album": album,
        "artist": ARTIST,
        "label": LABEL,
        "moniker": moniker,
        "source_path": str(src),
        "added_utc": utc_now(),
    }
    if extra:
        entry.update(extra)
    return entry


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--publish-hf", action="store_true")
    ap.add_argument("--hub", action="store_true")
    ap.add_argument("--no-chart", action="store_true")
    args = ap.parse_args()

    STREAM_DIR.mkdir(parents=True, exist_ok=True)
    hollow_lyrics = {}
    if HOLLOW_TXT.is_file():
        hollow_lyrics = parse_hollow_codex_lyrics(HOLLOW_TXT)
        print(f"Hollow Codex lyrics monikers: {sorted(hollow_lyrics.keys())}")
    else:
        print("[warn] hollow structure txt missing")

    # save clean lyrics json for archive
    clean_path = CAT / "lyrics" / "hollow_codex_lyrics_clean.json"
    clean_path.parent.mkdir(parents=True, exist_ok=True)
    clean_path.write_text(
        json.dumps(
            {
                "signature": "Delta9Phi963-HOLLOW-CODEX-LYRICS-v1",
                "album": "THE HOLLOW CODEX",
                "artist": ARTIST,
                "tracks": list(hollow_lyrics.values()),
                "updated_utc": utc_now(),
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    pl = load_playlist()
    idx = load_lyrics_index()
    uploads: list[tuple[Path, str]] = []
    added: list[dict] = []

    # --- 1) Road to Know Where ---
    if ROAD_WAV.is_file():
        entry = process_audio(
            ROAD_WAV,
            title="Road to Know Where",
            album="Road to Know Where",
            moniker="",
            extra={
                "upc": "825192882162",
                "distrokid_upc": "825192882162",
                "record_label": LABEL,
                "upload_date": "2026-05-16",
                "release_date": "2026-05-20",
                "release_type": "single",
            },
        )
        is_new, _ = upsert_track(pl, entry)
        uploads.append((Path(entry["local_stream"]), entry["hf_path"]))
        added.append(entry)
        print(f"  Road to Know Where new={is_new} UPC={entry['upc']}")
    else:
        print("[warn] Road wav missing", ROAD_WAV)

    # --- 2) Hollow Codex album tracks ---
    hollow_tracks_meta = []
    if HOLLOW_DIR.is_dir():
        mp3s = sorted(HOLLOW_DIR.glob("*.mp3"))
        for src in mp3s:
            mon = moniker_from_filename(src.name)
            if mon == "FADEOUT":
                mon = "THE FADEOUT"
            title = pretty_title_from_file(src.name)
            entry = process_audio(
                src,
                title=title,
                album="THE HOLLOW CODEX",
                moniker=mon,
                extra={"release_type": "album"},
            )
            is_new, _ = upsert_track(pl, entry)
            uploads.append((Path(entry["local_stream"]), entry["hf_path"]))
            added.append(entry)
            lyr = hollow_lyrics.get(mon) or hollow_lyrics.get(mon.replace("THE ", "THE "))
            body = (lyr or {}).get("lyrics") or ""
            hollow_tracks_meta.append(
                {
                    "sha256": entry["sha256"],
                    "title": title,
                    "moniker": mon,
                    "has_lyrics": bool(body),
                    "stream_url": entry["stream_url"],
                }
            )
            if body:
                rec = {
                    "title": title,
                    "album": "THE HOLLOW CODEX",
                    "artist": ARTIST,
                    "moniker": mon,
                    "chapter_title": (lyr or {}).get("chapter") or mon,
                    "lyrics": body,
                    "copyright": idx["copyright"],
                    "license": idx["license"],
                }
                idx.setdefault("by_sha256", {})[entry["sha256"]] = rec
                if mon:
                    idx.setdefault("by_moniker", {})[mon] = rec
            print(f"  hollow {mon or title}: lyrics={bool(body)} new={is_new}")

        idx.setdefault("albums", {})["THE_HOLLOW_CODEX"] = {
            "album": "THE HOLLOW CODEX",
            "artist": ARTIST,
            "tracks": hollow_tracks_meta,
        }

    # --- 3) Loose singles in NOT UPLOADED root ---
    if NOT_UPLOADED.is_dir():
        for src in sorted(NOT_UPLOADED.glob("*.mp3")):
            title = pretty_title_from_file(src.name)
            mon = moniker_from_filename(src.name)
            album = "NOT UPLOADED Singles"
            # These three often sit with Vengeance / Breaker catalog
            if re.search(r"dirt.?on.?my.?skin", title, re.I):
                album = "VENGEANCE CODEX"
            elif re.search(r"king.?of.?the.?ruins|king.?of.?ruin", title, re.I):
                album = "VENGEANCE CODEX"
            elif re.search(r"riding.?in.?a.?hearse", title, re.I):
                album = "VENGEANCE CODEX"
            entry = process_audio(
                src,
                title=title,
                album=album,
                moniker=mon,
                extra={"release_type": "single"},
            )
            is_new, _ = upsert_track(pl, entry)
            uploads.append((Path(entry["local_stream"]), entry["hf_path"]))
            added.append(entry)
            print(f"  single {title}: new={is_new} album={album}")

    # Road album entry in lyrics index (instrumental/no lyrics ok)
    road = next((e for e in added if e.get("upc") == "825192882162"), None)
    if road:
        idx.setdefault("albums", {})["ROAD_TO_KNOW_WHERE"] = {
            "album": "Road to Know Where",
            "artist": ARTIST,
            "upc": "825192882162",
            "record_label": LABEL,
            "upload_date": "2026-05-16",
            "release_date": "2026-05-20",
            "tracks": [
                {
                    "sha256": road["sha256"],
                    "title": road["title"],
                    "moniker": "",
                    "has_lyrics": False,
                    "stream_url": road["stream_url"],
                    "upc": "825192882162",
                }
            ],
        }

    # stats
    pl["stats"] = pl.get("stats") or {}
    pl["stats"]["playlist_tracks"] = len(pl.get("tracks") or [])
    pl["stats"]["last_ingest"] = {
        "utc": utc_now(),
        "added_or_updated": len(added),
        "source": "not_uploaded_to_git + road_to_know_where",
    }

    save_playlist(pl)
    save_lyrics_index(idx)

    man = {
        "signature": "Delta9Phi963-INGEST-NOT-UPLOADED-v1",
        "added_utc": utc_now(),
        "track_count": len(added),
        "hollow_lyrics_monikers": sorted(hollow_lyrics.keys()),
        "tracks": [
            {
                "title": e["title"],
                "album": e.get("album"),
                "sha256": e["sha256"],
                "upc": e.get("upc"),
                "hf_path": e.get("hf_path"),
            }
            for e in added
        ],
    }
    man_path = CAT / "albums" / "not_uploaded_ingest_manifest.json"
    man_path.parent.mkdir(parents=True, exist_ok=True)
    man_path.write_text(json.dumps(man, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": str(man_path), "tracks": len(added), "playlist": len(pl["tracks"])}, indent=2))

    if args.publish_hf:
        try:
            from huggingface_hub import HfApi

            token = None
            for tp in (
                Path.home() / ".cache" / "huggingface" / "token",
                Path.home() / ".huggingface" / "token",
            ):
                if tp.is_file():
                    token = tp.read_text(encoding="utf-8").strip()
                    break
            api = HfApi(token=token)
            seen = set()
            for local, repo_path in uploads:
                if not local.is_file() or repo_path in seen:
                    continue
                seen.add(repo_path)
                print(f"HF upload {repo_path} …")
                api.upload_file(
                    path_or_fileobj=str(local),
                    path_in_repo=repo_path,
                    repo_id=HF_REPO,
                    repo_type="dataset",
                    commit_message=f"stream: {Path(repo_path).name[:16]}",
                )
            for local_name, repo_name in (
                (CAT / "public_stream_playlist.json", "public_stream_playlist.json"),
                (CAT / "lyrics" / "lyrics_index.json", "lyrics/lyrics_index.json"),
                (clean_path, "lyrics/hollow_codex_lyrics_clean.json"),
            ):
                if local_name.is_file():
                    api.upload_file(
                        path_or_fileobj=str(local_name),
                        path_in_repo=repo_name,
                        repo_id=HF_REPO,
                        repo_type="dataset",
                        commit_message=f"index: {repo_name}",
                    )
            print("HF publish OK")
        except Exception as e:
            print("HF publish failed:", type(e).__name__, e)
            return 1

    if args.hub:
        r = subprocess.run(
            [
                sys.executable,
                str(STACK / "tools" / "build_public_music_stream.py"),
                "--hub",
                "--base-url",
                f"{BASE}/stream",
            ],
            cwd=str(STACK),
        )
        print("hub exit", r.returncode)
        # sync listen page to Excavationpro
        for src, dst in (
            (DOCS / "excavationpro-listen.html", EXCAV / "excavationpro-listen.html"),
            (CAT / "public_stream_playlist.json", EXCAV / "data" / "public_stream_playlist.json"),
            (CAT / "lyrics" / "lyrics_index.json", EXCAV / "data" / "lyrics_index.json"),
        ):
            if src.is_file():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                print("synced", dst)

    if not args.no_chart and (args.publish_hf or args.hub):
        r = subprocess.run(
            [
                sys.executable,
                str(STACK / "tools" / "map_music_to_star_chart.py"),
                "--rebuild-chart",
                "--sync-excav",
            ],
            cwd=str(STACK),
        )
        print("star chart exit", r.returncode)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
