#!/usr/bin/env python3
"""
EXCAVATIONPRO music catalog recovery
- Sweep local drives for audio + ISRC/UPC patterns in filenames
- Pull public Spotify artist discography (web HTML + oEmbed fallbacks)
- Emit CSV / JSON / Markdown registry for re-distribution

Usage:
  python tools/music_catalog_recovery.py
  python tools/music_catalog_recovery.py --roots "J:\\" "I:\\E Drive"
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

# DistroKid / Excavationpro real codes only (avoid UUID/hex/pexels false positives)
# Compact 12-char: QZ + 10 alnum, or QM42K + 7 digits
ISRC_RE = re.compile(
    r"(?i)(?:^|[\s_\-])("
    r"QZ[A-Z0-9]{10}"
    r"|QM42K\d{7}"
    r")(?:$|[\s_\.\-])"
)
# UPC/EAN 12–13 digits (avoid bare years)
UPC_RE = re.compile(r"\b(\d{12,13})\b")
AUDIO_EXT = {".mp3", ".wav", ".flac", ".m4a", ".aiff", ".aif", ".ogg", ".aac", ".wma"}
JUNK_MEDIA = re.compile(r"(?i)(grok-video|canvas-video|pexels|\.jpg|\.png|\.mp4|\.webm|\.gif)")

SPOTIFY_ARTIST_ID = "6CkZ4bN2xu3WRKbjEL3u2S"
ARTIST_NAME = "Excavationpro"
UA = "Excavationpro-CatalogRecovery/1.0 (local stewardship; redistribution recovery)"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_isrc(raw: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]", "", raw).upper()
    if len(s) == 12:
        return f"{s[0:2]}-{s[2:5]}-{s[5:7]}-{s[7:12]}"
    return s


def extract_isrcs(text: str) -> List[str]:
    found = []
    for m in ISRC_RE.finditer(text or ""):
        found.append(normalize_isrc(m.group(1)))
    # de-dupe preserve order
    seen: Set[str] = set()
    out = []
    for x in found:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def extract_upcs(text: str) -> List[str]:
    out = []
    for m in UPC_RE.finditer(text or ""):
        u = m.group(1)
        # skip pure years / small ints already filtered by length
        if u.startswith("20") and len(u) == 4:
            continue
        out.append(u)
    return list(dict.fromkeys(out))


def http_get(url: str, timeout: int = 45) -> str:
    req = Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/json"})
    with urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def scan_filesystem(
    roots: List[Path],
    max_files: int = 500_000,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    rows: List[Dict[str, Any]] = []
    stats = defaultdict(int)
    for root in roots:
        if not root.exists():
            stats[f"missing:{root}"] = 1
            continue
        print(f"[scan] {root} …", flush=True)
        for dirpath, dirnames, filenames in os.walk(root):
            # skip huge game/system junk
            low = dirpath.lower()
            if any(
                x in low
                for x in (
                    "\\windows\\",
                    "\\$recycle",
                    "\\node_modules",
                    "\\battle.net",
                    "\\epic games",
                    "\\steam",
                    "\\fortnite",
                    "\\.git\\",
                    "\\program files",
                )
            ):
                dirnames[:] = []
                continue
            for fn in filenames:
                stats["files_seen"] += 1
                if stats["files_seen"] > max_files:
                    print("[scan] max_files reached", flush=True)
                    return rows, dict(stats)
                ext = Path(fn).suffix.lower()
                is_audio = ext in AUDIO_EXT
                if not is_audio:
                    continue  # never scrape ISRCs from images/videos
                if JUNK_MEDIA.search(fn) or JUNK_MEDIA.search(dirpath):
                    continue
                full = str(Path(dirpath) / fn)
                isrcs = extract_isrcs(fn)
                upcs = extract_upcs(fn)
                if not is_audio and not isrcs and not upcs:
                    continue
                title_guess = Path(fn).stem
                for isrc in isrcs:
                    title_guess = re.sub(re.escape(isrc.replace("-", "")), "", title_guess, flags=re.I)
                    title_guess = re.sub(re.escape(isrc), "", title_guess, flags=re.I)
                title_guess = re.sub(r"[_\-]+", " ", title_guess).strip(" -_.")
                row = {
                    "source": "filesystem",
                    "path": full,
                    "filename": fn,
                    "extension": ext,
                    "is_audio": is_audio,
                    "title_guess": title_guess or Path(fn).stem,
                    "isrcs": isrcs,
                    "upcs": upcs,
                    "album_guess": Path(dirpath).name,
                    "artist_guess": ARTIST_NAME if "excavation" in full.lower() else "",
                }
                rows.append(row)
                stats["matched"] += 1
                if isrcs:
                    stats["with_isrc"] += 1
                if is_audio:
                    stats["audio"] += 1
                if stats["matched"] % 500 == 0:
                    print(f"  … {stats['matched']} matches / {stats['files_seen']} files", flush=True)
    return rows, dict(stats)


def fetch_spotify_artist_albums(artist_id: str) -> List[Dict[str, Any]]:
    """Best-effort: parse open.spotify.com artist page for album links + titles."""
    albums: List[Dict[str, Any]] = []
    try:
        html = http_get(f"https://open.spotify.com/artist/{artist_id}")
    except Exception as e:
        print(f"[spotify] artist page fail: {e}", flush=True)
        return albums

    # album links: /album/ID and nearby titles
    album_ids = list(dict.fromkeys(re.findall(r"/album/([a-zA-Z0-9]{22})", html)))
    print(f"[spotify] album ids on artist page: {len(album_ids)}", flush=True)

    # og / json-ish titles
    title_map: Dict[str, str] = {}
    for m in re.finditer(
        r'"uri":"spotify:album:([a-zA-Z0-9]{22})"[^}]{0,400}?"name":"([^"]+)"',
        html,
    ):
        title_map[m.group(1)] = m.group(2).encode("utf-8").decode("unicode_escape", errors="replace")

    for i, aid in enumerate(album_ids[:400]):  # safety cap
        title = title_map.get(aid, "")
        album_url = f"https://open.spotify.com/album/{aid}"
        tracks: List[Dict[str, Any]] = []
        album_upc = ""
        try:
            ahtml = http_get(album_url)
            time.sleep(0.35)  # be polite
            if not title:
                om = re.search(r'property="og:title" content="([^"]+)"', ahtml)
                if om:
                    title = om.group(1).split(" - ")[0].strip()
            # datePublished from ld+json
            dm = re.search(r'"datePublished"\s*:\s*"([^"]+)"', ahtml)
            date_pub = dm.group(1) if dm else ""
            # Tracks: modern Spotify SSR uses aria-label on track rows
            # e.g. spotify:track:ID" aria-label="Track Title"
            for tm in re.finditer(
                r'spotify:track:([a-zA-Z0-9]{22})"[^>]*aria-label="([^"]+)"',
                ahtml,
            ):
                tid, tname = tm.group(1), tm.group(2)
                tracks.append(
                    {
                        "spotify_track_id": tid,
                        "title": tname,
                        "spotify_url": f"https://open.spotify.com/track/{tid}",
                    }
                )
            if not tracks:
                # fallback: track href + nearby text
                for tm in re.finditer(
                    r'href="/track/([a-zA-Z0-9]{22})"[^>]*>\s*<p[^>]*>([^<]+)</p>',
                    ahtml,
                ):
                    tracks.append(
                        {
                            "spotify_track_id": tm.group(1),
                            "title": tm.group(2).strip(),
                            "spotify_url": f"https://open.spotify.com/track/{tm.group(1)}",
                        }
                    )
            # de-dupe tracks
            seen_t: Set[str] = set()
            uniq = []
            for t in tracks:
                if t["spotify_track_id"] in seen_t:
                    continue
                seen_t.add(t["spotify_track_id"])
                uniq.append(t)
            tracks = uniq
            um = re.search(r'"upc"\s*:\s*"(\d{12,14})"', ahtml, re.I)
            if um:
                album_upc = um.group(1)
        except Exception as e:
            print(f"[spotify] album {aid} fail: {e}", flush=True)
            date_pub = ""

        albums.append(
            {
                "source": "spotify",
                "spotify_album_id": aid,
                "title": title or aid,
                "spotify_url": album_url,
                "upc": album_upc,
                "date_published": locals().get("date_pub") or "",
                "track_count": len(tracks),
                "tracks": tracks,
            }
        )
        if (i + 1) % 10 == 0:
            print(f"  … scraped {i+1}/{len(album_ids[:400])} albums", flush=True)
    return albums


def merge_registry(
    fs_rows: List[Dict[str, Any]],
    albums: List[Dict[str, Any]],
) -> Dict[str, Any]:
    by_isrc: Dict[str, Dict[str, Any]] = {}
    tracks_out: List[Dict[str, Any]] = []

    for r in fs_rows:
        for isrc in r.get("isrcs") or [""]:
            key = isrc or f"path:{r['path']}"
            entry = {
                "title": r.get("title_guess"),
                "isrc": isrc or None,
                "upc": (r.get("upcs") or [None])[0],
                "album": r.get("album_guess"),
                "artist": r.get("artist_guess") or ARTIST_NAME,
                "local_path": r.get("path"),
                "filename": r.get("filename"),
                "spotify_track_id": None,
                "spotify_url": None,
                "sources": ["filesystem"],
            }
            if isrc and isrc in by_isrc:
                prev = by_isrc[isrc]
                prev["local_path"] = prev.get("local_path") or entry["local_path"]
                if "filesystem" not in prev["sources"]:
                    prev["sources"].append("filesystem")
            else:
                by_isrc[key] = entry
                tracks_out.append(entry)

    for alb in albums:
        for t in alb.get("tracks") or []:
            entry = {
                "title": t.get("title"),
                "isrc": None,
                "upc": alb.get("upc") or None,
                "album": alb.get("title"),
                "artist": ARTIST_NAME,
                "local_path": None,
                "filename": None,
                "spotify_track_id": t.get("spotify_track_id"),
                "spotify_url": t.get("spotify_url"),
                "spotify_album_id": alb.get("spotify_album_id"),
                "spotify_album_url": alb.get("spotify_url"),
                "sources": ["spotify"],
            }
            # merge by title+album if possible
            merged = False
            for prev in tracks_out:
                if (
                    prev.get("title")
                    and t.get("title")
                    and prev["title"].lower().strip() == t["title"].lower().strip()
                    and (not prev.get("album") or prev["album"] == alb.get("title") or "filesystem" in prev["sources"])
                ):
                    prev["spotify_track_id"] = t.get("spotify_track_id")
                    prev["spotify_url"] = t.get("spotify_url")
                    prev["spotify_album_id"] = alb.get("spotify_album_id")
                    prev["spotify_album_url"] = alb.get("spotify_url")
                    if alb.get("upc") and not prev.get("upc"):
                        prev["upc"] = alb.get("upc")
                    if "spotify" not in prev["sources"]:
                        prev["sources"].append("spotify")
                    if not prev.get("album"):
                        prev["album"] = alb.get("title")
                    merged = True
                    break
            if not merged:
                tracks_out.append(entry)

    return {
        "artist": ARTIST_NAME,
        "spotify_artist_id": SPOTIFY_ARTIST_ID,
        "spotify_artist_url": f"https://open.spotify.com/artist/{SPOTIFY_ARTIST_ID}",
        "generated_at": utc_now(),
        "album_count_spotify": len(albums),
        "track_count": len(tracks_out),
        "tracks_with_isrc": sum(1 for t in tracks_out if t.get("isrc")),
        "tracks_with_local_file": sum(1 for t in tracks_out if t.get("local_path")),
        "albums": albums,
        "tracks": tracks_out,
        "notes": [
            "DistroKid vault requires logged-in browser; this registry merges local disk + public Spotify.",
            "ISRCs primarily recovered from local filenames when DistroKid vault is restricted.",
            "UPCs appear when present in Spotify page JSON or filenames.",
            "For full DistroKid export: while logged in, download each vault file page or use browser console script (see companion HTML helper).",
        ],
    }


def write_outputs(reg: Dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "excavationpro_catalog.json"
    csv_path = out_dir / "excavationpro_catalog.csv"
    md_path = out_dir / "excavationpro_catalog.md"
    albums_csv = out_dir / "excavationpro_albums.csv"

    json_path.write_text(json.dumps(reg, indent=2, ensure_ascii=False), encoding="utf-8")

    fields = [
        "title",
        "artist",
        "album",
        "isrc",
        "upc",
        "spotify_track_id",
        "spotify_url",
        "spotify_album_id",
        "local_path",
        "filename",
        "sources",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for t in reg["tracks"]:
            row = dict(t)
            row["sources"] = ";".join(row.get("sources") or [])
            w.writerow(row)

    with albums_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["title", "spotify_album_id", "spotify_url", "upc", "track_count"],
        )
        w.writeheader()
        for a in reg.get("albums") or []:
            w.writerow(
                {
                    "title": a.get("title"),
                    "spotify_album_id": a.get("spotify_album_id"),
                    "spotify_url": a.get("spotify_url"),
                    "upc": a.get("upc"),
                    "track_count": a.get("track_count"),
                }
            )

    lines = [
        f"# {ARTIST_NAME} — Music Catalog Recovery Registry",
        "",
        f"Generated: `{reg['generated_at']}`",
        f"Spotify: {reg['spotify_artist_url']}",
        "",
        "## Summary",
        f"- Spotify albums scraped: **{reg['album_count_spotify']}**",
        f"- Track rows (merged): **{reg['track_count']}**",
        f"- Rows with ISRC: **{reg['tracks_with_isrc']}**",
        f"- Rows with local file: **{reg['tracks_with_local_file']}**",
        "",
        "## Notes",
    ]
    for n in reg.get("notes") or []:
        lines.append(f"- {n}")
    lines += ["", "## Albums (Spotify)", ""]
    for a in reg.get("albums") or []:
        lines.append(
            f"- **{a.get('title')}** — {a.get('track_count', 0)} tracks"
            + (f" — UPC `{a.get('upc')}`" if a.get("upc") else "")
            + f" — [Spotify]({a.get('spotify_url')})"
        )
    lines += ["", "## Tracks (first 200 of merged list)", ""]
    lines.append("| Title | Album | ISRC | UPC | Spotify | Local |")
    lines.append("|-------|-------|------|-----|---------|-------|")
    for t in (reg.get("tracks") or [])[:200]:
        lines.append(
            f"| {t.get('title') or ''} | {t.get('album') or ''} | {t.get('isrc') or ''} | "
            f"{t.get('upc') or ''} | {t.get('spotify_url') or ''} | "
            f"{'yes' if t.get('local_path') else ''} |"
        )
    if reg["track_count"] > 200:
        lines.append("")
        lines.append(f"*… {reg['track_count'] - 200} more rows in CSV/JSON.*")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[out] {json_path}")
    print(f"[out] {csv_path}")
    print(f"[out] {albums_csv}")
    print(f"[out] {md_path}")


def write_browser_helper(out_dir: Path) -> None:
    """Bookmarklet-style instructions + console script for DistroKid vault (user runs while logged in)."""
    helper = out_dir / "DISTROKID_VAULT_BROWSER_HELPER.md"
    helper.write_text(
        """# DistroKid Vault Browser Helper (run while logged in)

DistroKid vault pages are **session-authenticated**. This helper does **not** bypass login —
you paste it into the browser console on vault pages while signed in as EXCAVATIONPRO.

## A. From a vault folder page (list of songs)

1. Open https://distrokid.com/vault/ (or your folder URL)
2. Press F12 → Console
3. Paste:

```javascript
(async () => {
  const links = [...document.querySelectorAll('a[href*="/vault/file/"]')];
  const hrefs = [...new Set(links.map(a => a.href))];
  console.log('Found file links:', hrefs.length);
  copy(hrefs.join('\\n'));
  alert('Copied ' + hrefs.length + ' vault file URLs to clipboard. Paste into vault_urls.txt');
})();
```

## B. From each song page (metadata scrape)

On a single song/file page (`/vault/file/?id=...`), paste:

```javascript
(() => {
  const text = document.body.innerText;
  const isrc = (text.match(/ISRC[:\\s]*([A-Z0-9\\-]{12,15})/i) || [])[1] || '';
  const upc = (text.match(/UPC[:\\s]*(\\d{12,13})/i) || [])[1] || '';
  const title = (document.querySelector('h1,h2,.title') || {}).innerText || document.title;
  const row = {url: location.href, title, isrc, upc, rawSnippet: text.slice(0, 2000)};
  copy(JSON.stringify(row, null, 2));
  console.log(row);
  alert('Metadata JSON copied');
})();
```

## C. Bulk: open all folder links and collect (manual queue)

1. Save folder link list to `vault_urls.txt` (one URL per line)
2. Run local collector later:  
   `python tools/music_catalog_recovery.py --import-json path\\to\\scraped.jsonl`

## D. What DistroKid support can still give you

Even with store restriction, email **support@distrokid.com** and request:

- Full **ISRC / UPC / release date / store delivery** export for account artist **Excavationpro**
- Confirmation whether existing live releases remain on stores or will be taken down
- Any bank/tax export for your records

Keep the Ania email as a record. Ask for a **data export** — many distributors can still provide metadata even when delivery is blocked.

## E. Alternate public sources

- Spotify artist: https://open.spotify.com/artist/6CkZ4bN2xu3WRKbjEL3u2S
- Feature.fm / ffm: https://ffm.to/eovnvo9
- Local disk: J:\\ (ISRC often in filename)

## F. New distributor checklist (per release)

For each track/album you need typically:

| Field | Source |
|-------|--------|
| Artist name | Excavationpro |
| Track title | vault / Spotify / filename |
| Album / release title | vault |
| ISRC | vault / filename |
| UPC (album) | vault |
| Release date | vault / Spotify |
| Genre | your notes |
| Lyrics / explicit | your notes |
| Audio master | vault download / J:\\ |

Primary deliverable from this toolkit: `excavationpro_catalog.csv`
""",
        encoding="utf-8",
    )
    print(f"[out] {helper}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--roots",
        nargs="*",
        default=[
            r"J:\ALL SOUND FILES",
            r"J:\FINISHED BEAT STARS MUSIC",
            r"J:\DESKTOP PHOTOS & MUSIC",
            r"J:\2026",
            r"C:\Users\justi\Music",
            r"C:\Users\justi\Documents",
        ],
        help="Folders to scan for audio/ISRC",
    )
    ap.add_argument(
        "--out",
        default=r"I:\E Drive\lygo-protocol-stack\data\music_catalog",
        help="Output directory",
    )
    ap.add_argument("--skip-spotify", action="store_true")
    ap.add_argument("--skip-fs", action="store_true")
    ap.add_argument("--full-j", action="store_true", help="Also scan entire J:\\ (slow)")
    args = ap.parse_args()

    roots = [Path(r) for r in args.roots]
    if args.full_j:
        roots.insert(0, Path(r"J:\\"))

    fs_rows: List[Dict[str, Any]] = []
    stats: Dict[str, int] = {}
    if not args.skip_fs:
        fs_rows, stats = scan_filesystem(roots)
        print(f"[scan] stats: {stats}", flush=True)

    albums: List[Dict[str, Any]] = []
    if not args.skip_spotify:
        albums = fetch_spotify_artist_albums(SPOTIFY_ARTIST_ID)
        print(f"[spotify] albums: {len(albums)}", flush=True)

    reg = merge_registry(fs_rows, albums)
    reg["scan_stats"] = stats
    reg["scan_roots"] = [str(r) for r in roots]

    out_dir = Path(args.out)
    write_outputs(reg, out_dir)
    write_browser_helper(out_dir)

    print(
        f"\nDONE: {reg['track_count']} track rows | "
        f"{reg['tracks_with_isrc']} with ISRC | "
        f"{reg['album_count_spotify']} Spotify albums",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
