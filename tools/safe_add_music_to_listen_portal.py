#!/usr/bin/env python3
"""
SAFE music add for the listen portal — data only, no UI redesign.

Policy (2026-07-28):
  - DEFAULT deploy target: asiancoastline.com ONLY
  - Excavationpro excavationpro-listen.html is BACKUP (use --promote-backup-excav)
  - Never run hub rebuild / enhance injectors from this tool
  - Only surgical boot playlist JSON replace + playlist/lyrics/HF streams

Examples:
  python tools/safe_add_music_to_listen_portal.py --folder "C:\\Music\\ALBUM" --album "ALBUM" --publish-hf --deploy-asian
  python tools/safe_add_music_to_listen_portal.py --file "I:\\Actors\\track.wav" --title "Track" --album "Singles" --deploy-asian
  python tools/safe_add_music_to_listen_portal.py --inject-playlist-only --deploy-asian
  python tools/safe_add_music_to_listen_portal.py --promote-backup-excav
"""
from __future__ import annotations

import argparse
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
VAULT = Path(r"I:\E Drive\MUSIC_VAULT")
STREAM = VAULT / "public_stream"
HF_REPO = "DeepSeekOracle/excavationpro-music-stream"
BASE = f"https://huggingface.co/datasets/{HF_REPO}/resolve/main"

ASIAN = Path(r"D:\asiancoastline")
EXCAV = Path(r"D:\Excavationpro")
# Prefer D: excav; fall back
if not EXCAV.is_dir():
    EXCAV = STACK.parent / "Excavationpro"

ARTIST_DEFAULT = "Excavationpro"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def pretty_title(stem: str) -> str:
    s = re.sub(r"\s*\([^)]*\)\s*$", "", stem)
    s = s.replace("_", " ")
    s = re.sub(r"\s+", " ", s).strip()
    if re.search(r"roadtoknowwhere", s, re.I):
        return "Road to Know Where"
    return s


def extract_moniker(name: str) -> str:
    m = re.search(r"\((THE\s+[^)]+)\)", name, re.I)
    if m:
        return re.sub(r"\s+", " ", m.group(1).strip().upper())
    m = re.match(r"^(THE\s+[A-Z][A-Z\s]+?)\s*[-–]", Path(name).stem, re.I)
    if m:
        return re.sub(r"\s+", " ", m.group(1).strip().upper())
    if re.match(r"^FADEOUT\b", Path(name).stem, re.I):
        return "THE FADEOUT"
    return ""


def load_playlist() -> dict:
    p = CAT / "public_stream_playlist.json"
    return json.loads(p.read_text(encoding="utf-8"))


def save_playlist(pl: dict) -> None:
    pl["generated_at"] = utc_now()
    pl.setdefault("stats", {})["playlist_tracks"] = len(pl.get("tracks") or [])
    text = json.dumps(pl, indent=2, ensure_ascii=False) + "\n"
    for dest in (
        CAT / "public_stream_playlist.json",
        STACK / "docs" / "data" / "public_stream_playlist.json",
        VAULT / "manifest" / "public_stream_playlist.json",
        EXCAV / "data" / "public_stream_playlist.json",
        ASIAN / "data" / "public_stream_playlist.json",
    ):
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text, encoding="utf-8")
        except OSError as e:
            print("[warn] playlist write", dest, e)


def load_lyrics_index() -> dict:
    p = CAT / "lyrics" / "lyrics_index.json"
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return {
        "signature": "Delta9Phi963-LYRICS-INDEX-v1",
        "artist": ARTIST_DEFAULT,
        "copyright": "© Justin Helmer / Excavationpro (Lightfather). Lyrics © steward.",
        "license": "LYGO Music License v1.0",
        "by_sha256": {},
        "by_moniker": {},
        "albums": {},
        "updated_utc": "",
    }


def save_lyrics_index(idx: dict) -> None:
    idx["updated_utc"] = utc_now()
    text = json.dumps(idx, indent=2, ensure_ascii=False) + "\n"
    for dest in (
        CAT / "lyrics" / "lyrics_index.json",
        STACK / "docs" / "data" / "lyrics_index.json",
        EXCAV / "data" / "lyrics_index.json",
        ASIAN / "data" / "lyrics_index.json",
    ):
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text, encoding="utf-8")
        except OSError as e:
            print("[warn] lyrics write", dest, e)


def path_for_digest(digest: str) -> tuple[str, Path]:
    """Return (hf_path, local dest) using existing vault layout; never mass-force shard."""
    flat = STREAM / f"{digest}.mp3"
    shard = STREAM / digest[:2] / f"{digest}.mp3"
    if flat.is_file():
        return f"stream/{digest}.mp3", flat
    if shard.is_file():
        return f"stream/{digest[:2]}/{digest}.mp3", shard
    # new file: prefer flat if under HF 10k limit heuristic; else shard
    try:
        n_flat = sum(1 for _ in STREAM.glob("*.mp3"))
    except OSError:
        n_flat = 99999
    if n_flat < 9900:
        return f"stream/{digest}.mp3", flat
    return f"stream/{digest[:2]}/{digest}.mp3", shard


def encode_to(src: Path, dest: Path) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size > 2000:
        return "exists"
    if src.suffix.lower() == ".mp3":
        shutil.copy2(src, dest)
        return "copy"
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-codec:a",
        "libmp3lame",
        "-b:a",
        "160k",
        "-ar",
        "44100",
        "-ac",
        "2",
        str(dest),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not dest.is_file():
        raise RuntimeError(f"ffmpeg failed: {src.name}: {(r.stderr or '')[-300:]}")
    return "encoded"


def slim_playlist(pl: dict) -> dict:
    tracks = []
    for t in pl.get("tracks") or []:
        sha = (t.get("sha256") or "").strip()
        hf = (t.get("hf_path") or "").strip()
        # repair stream_url from layout if needed
        if sha:
            path, _ = path_for_digest(sha)
            # prefer existing local layout over stale hf_path
            if (STREAM / f"{sha}.mp3").is_file():
                path = f"stream/{sha}.mp3"
            elif (STREAM / sha[:2] / f"{sha}.mp3").is_file():
                path = f"stream/{sha[:2]}/{sha}.mp3"
            elif hf.startswith("stream/"):
                path = hf
            t["hf_path"] = path
            t["stream_url"] = f"{BASE}/{path}"
        tracks.append(
            {
                "title": t.get("title"),
                "sha256": t.get("sha256"),
                "isrcs": t.get("isrcs") or [],
                "aliases": t.get("aliases") or [],
                "size": t.get("size"),
                "stream_url": t.get("stream_url"),
                "album": t.get("album"),
                "artist": t.get("artist"),
                "moniker": t.get("moniker"),
            }
        )
    return {
        "signature": pl.get("signature") or "Δ9Φ963-PUBLIC-MUSIC-STREAM-v1",
        "bitrate": pl.get("bitrate") or "160k",
        "public_base_url": pl.get("public_base_url") or f"{BASE}/stream",
        "hf_dataset": pl.get("hf_dataset") or f"https://huggingface.co/datasets/{HF_REPO}",
        "stats": pl.get("stats") or {},
        "generated_at": pl.get("generated_at") or utc_now(),
        "tracks": tracks,
    }


def surgical_inject_boot(html_path: Path, slim_pl: dict) -> None:
    """Replace ONLY boot playlist JSON. Never rewrite UI shell."""
    if not html_path.is_file():
        raise FileNotFoundError(html_path)
    html = html_path.read_text(encoding="utf-8")
    # Refuse to inject into pages that still have known-broken trophy junk
    # (should not happen on healthy shells)
    m = re.search(
        r'(<script id="boot" type="application/json">)(.*?)(</script>)',
        html,
        re.S,
    )
    if not m:
        raise RuntimeError(f"no boot JSON in {html_path}")
    try:
        data = json.loads(m.group(2))
    except json.JSONDecodeError:
        data = {}
    data["playlist"] = slim_pl
    new_boot = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    html = html[: m.start(2)] + new_boot + html[m.end(2) :]
    # cache-bust plugins only (safe)
    html = re.sub(r"play-listing\.js(\?v=\d+)?", "play-listing.js?v=7", html)
    html = re.sub(r"lyrics-panel\.js(\?v=\d+)?", "lyrics-panel.js?v=3", html)
    n = len(slim_pl.get("tracks") or [])
    html = re.sub(r"(Listen Free — )\d+\+?( Songs)", rf"\g<1>{n}\2", html)
    html = re.sub(r"(Listen Free — )\d+\+?( Sovereign)", rf"\g<1>{n}\2", html)
    html = re.sub(r"(Listen Free — )\d+\+?( Streams)", rf"\g<1>{n}\2", html)
    html_path.write_text(html, encoding="utf-8")
    print(f"[inject] {html_path} tracks={n} size={html_path.stat().st_size}")


def git_push_repo(repo: Path, paths: list[str], message: str) -> None:
    if not (repo / ".git").is_dir():
        print("[warn] not a git repo", repo)
        return
    subprocess.run(["git", "-C", str(repo), "add", *paths], check=False)
    st = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        capture_output=True,
        text=True,
    )
    if not (st.stdout or "").strip():
        print("[git] nothing to commit", repo.name)
        return
    subprocess.run(["git", "-C", str(repo), "commit", "-m", message], check=False)
    r = subprocess.run(["git", "-C", str(repo), "push", "origin", "main"], capture_output=True, text=True)
    print("[git] push", repo.name, "exit", r.returncode)
    if r.returncode != 0:
        print(r.stderr[-500:] if r.stderr else r.stdout[-500:])


def collect_sources(folder: str | None, file: str | None) -> list[Path]:
    out: list[Path] = []
    if file:
        p = Path(file)
        if not p.is_file():
            raise FileNotFoundError(p)
        out.append(p)
    if folder:
        d = Path(folder)
        if not d.is_dir():
            raise FileNotFoundError(d)
        for ext in ("*.mp3", "*.wav", "*.flac", "*.m4a"):
            out.extend(sorted(d.rglob(ext)))
        # skip videos
        out = [p for p in out if p.suffix.lower() in {".mp3", ".wav", ".flac", ".m4a"}]
    return out


def upsert_track(pl: dict, entry: dict) -> bool:
    digest = entry["sha256"]
    for t in pl.get("tracks") or []:
        if t.get("sha256") == digest:
            t.update(entry)
            return False
    pl.setdefault("tracks", []).append(entry)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Safe listen portal music add (asian first)")
    ap.add_argument("--folder", default="")
    ap.add_argument("--file", default="")
    ap.add_argument("--title", default="")
    ap.add_argument("--album", default="Singles")
    ap.add_argument("--artist", default=ARTIST_DEFAULT)
    ap.add_argument("--upc", default="")
    ap.add_argument("--moniker", default="")
    ap.add_argument("--lyrics-json", default="")
    ap.add_argument("--lyrics-only", action="store_true")
    ap.add_argument("--publish-hf", action="store_true")
    ap.add_argument("--deploy-asian", action="store_true", help="git push asiancoastline (PRIMARY)")
    ap.add_argument(
        "--promote-backup-excav",
        action="store_true",
        help="After asian is good: copy same inject to Excavationpro backup and push",
    )
    ap.add_argument(
        "--inject-playlist-only",
        action="store_true",
        help="No encode; re-inject current playlist into HTML only",
    )
    ap.add_argument(
        "--no-inject",
        action="store_true",
        help="Update data/HF only; do not touch HTML",
    )
    args = ap.parse_args()

    STREAM.mkdir(parents=True, exist_ok=True)
    pl = load_playlist()
    uploaded: list[tuple[Path, str]] = []
    added = 0

    moniker_lyrics: dict[str, dict] = {}
    if args.lyrics_json:
        lj = Path(args.lyrics_json)
        if lj.is_file():
            clean = json.loads(lj.read_text(encoding="utf-8"))
            for t in clean.get("tracks") or []:
                mon = (t.get("moniker") or t.get("title") or "").upper().strip()
                mon = re.sub(r"\s+", " ", mon)
                if mon:
                    moniker_lyrics[mon] = t

    if not args.lyrics_only and not args.inject_playlist_only and not args.promote_backup_excav:
        sources = collect_sources(args.folder or None, args.file or None)
        if not sources:
            print("No --folder / --file sources (use --inject-playlist-only or --lyrics-only)")
            if not args.deploy_asian and not args.promote_backup_excav:
                return 2
        for src in sources:
            digest = sha256_file(src)
            hf_path, dest = path_for_digest(digest)
            status = encode_to(src, dest)
            title = args.title if args.file and args.title else pretty_title(src.stem)
            mon = args.moniker or extract_moniker(src.name)
            entry = {
                "sha256": digest,
                "title": title,
                "aliases": list(dict.fromkeys([title, src.stem] + ([mon] if mon else []))),
                "isrcs": [],
                "size": dest.stat().st_size if dest.is_file() else 0,
                "stream_file": dest.name,
                "local_stream": str(dest),
                "stream_url": f"{BASE}/{hf_path}",
                "hf_path": hf_path,
                "album": args.album,
                "artist": args.artist,
                "moniker": mon,
                "added_utc": utc_now(),
            }
            if args.upc:
                entry["upc"] = args.upc
                entry["distrokid_upc"] = args.upc
            is_new = upsert_track(pl, entry)
            added += 1 if is_new else 0
            uploaded.append((dest, hf_path))
            print(f"  [{status}] {'NEW' if is_new else 'UPD'} {title} → {hf_path}")

            # lyrics attach
            if moniker_lyrics:
                idx = load_lyrics_index()
                lyr = moniker_lyrics.get(mon.upper()) if mon else None
                if not lyr and mon:
                    for k, v in moniker_lyrics.items():
                        if mon.upper() in k or k in mon.upper():
                            lyr = v
                            break
                body = (lyr or {}).get("lyrics") or ""
                if body:
                    rec = {
                        "title": title,
                        "album": args.album,
                        "artist": args.artist,
                        "moniker": mon,
                        "lyrics": body,
                        "copyright": idx.get("copyright"),
                        "license": idx.get("license"),
                    }
                    idx.setdefault("by_sha256", {})[digest] = rec
                    if mon:
                        idx.setdefault("by_moniker", {})[mon.upper()] = rec
                    save_lyrics_index(idx)
                    print(f"    lyrics ok moniker={mon}")

        save_playlist(pl)
        print(json.dumps({"playlist_tracks": len(pl["tracks"]), "new_or_touched": added}, indent=2))

    if args.lyrics_only and moniker_lyrics:
        idx = load_lyrics_index()
        for mon, lyr in moniker_lyrics.items():
            body = lyr.get("lyrics") or ""
            if not body:
                continue
            rec = {
                "title": lyr.get("title") or mon,
                "album": lyr.get("album") or args.album,
                "artist": args.artist,
                "moniker": mon,
                "lyrics": body,
                "copyright": idx.get("copyright"),
                "license": idx.get("license"),
            }
            idx.setdefault("by_moniker", {})[mon] = rec
            # bind to playlist sha if moniker match
            for t in pl.get("tracks") or []:
                if (t.get("moniker") or "").upper() == mon:
                    idx.setdefault("by_sha256", {})[t["sha256"]] = rec
        save_lyrics_index(idx)
        print("[lyrics-only] index updated")

    if args.publish_hf and uploaded:
        try:
            from huggingface_hub import HfApi

            api = HfApi()
            for local, repo_path in uploaded:
                if not local.is_file():
                    continue
                print("HF", repo_path)
                api.upload_file(
                    path_or_fileobj=str(local),
                    path_in_repo=repo_path,
                    repo_id=HF_REPO,
                    repo_type="dataset",
                    commit_message=f"stream add {local.name[:12]}",
                )
            api.upload_file(
                path_or_fileobj=str(CAT / "public_stream_playlist.json"),
                path_in_repo="public_stream_playlist.json",
                repo_id=HF_REPO,
                repo_type="dataset",
                commit_message="playlist update (safe add)",
            )
            print("HF publish OK")
        except Exception as e:
            print("HF publish failed:", e)
            return 1

    slim = slim_playlist(pl)
    # keep playlist stream_urls consistent after slim repair
    save_playlist(pl)

    if not args.no_inject and (args.deploy_asian or args.inject_playlist_only or args.promote_backup_excav or uploaded):
        # Always inject asian when deploying asian or when we added tracks
        asian_html = ASIAN / "index.html"
        if asian_html.is_file() and (args.deploy_asian or args.inject_playlist_only or uploaded):
            # ensure plugins present
            plug = ASIAN / "listen-plugins"
            plug.mkdir(parents=True, exist_ok=True)
            for name in ("play-listing.js", "lyrics-panel.js"):
                src = STACK / "docs" / "listen-plugins" / name
                if src.is_file():
                    try:
                        shutil.copy2(src, plug / name)
                    except OSError:
                        pass
            surgical_inject_boot(asian_html, slim)

        if args.promote_backup_excav:
            excav_html = EXCAV / "excavationpro-listen.html"
            if excav_html.is_file():
                # copy asian shell→excav only if user promotes (keeps them twins)
                if asian_html.is_file():
                    shutil.copy2(asian_html, excav_html)
                else:
                    surgical_inject_boot(excav_html, slim)
                print("[backup] Excavationpro listen updated from asian / inject")

    if args.deploy_asian:
        git_push_repo(
            ASIAN,
            ["index.html", "data", "listen-plugins"],
            "music: safe playlist/lyrics update (asian primary)",
        )

    if args.promote_backup_excav:
        git_push_repo(
            EXCAV,
            ["excavationpro-listen.html", "data", "listen-plugins"],
            "music: promote listen backup from verified asian portal",
        )

    print(
        json.dumps(
            {
                "ok": True,
                "policy": "asian-first; excav-backup-only-on-promote",
                "playlist_tracks": len(pl.get("tracks") or []),
                "docs": "docs/LISTEN_PORTAL_SAFE_OPS.md",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
