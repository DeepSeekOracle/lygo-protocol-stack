#!/usr/bin/env python3
"""
Map Excavationpro / Lightfather music into Haven Star Chart nodes.

Live rebuild source: public_stream_playlist.json (+ lyrics_index albums).
When albums are tagged on tracks (via add_album_to_listen_portal), they expand
into track stars under GALAXY_EXCAVATIONPRO_MUSIC (fork of Lightfather).

Usage:
  python tools/map_music_to_star_chart.py --json          # preview nodes
  python tools/build_haven_star_chart.py                 # full chart (includes music)
  python tools/map_music_to_star_chart.py --rebuild-chart # chart + optional excav sync
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
CAT = STACK / "data" / "music_catalog"
LISTEN_URL = "https://deepseekoracle.github.io/Excavationpro/excavationpro-listen.html"
HF_STREAM = "https://huggingface.co/datasets/DeepSeekOracle/excavationpro-music-stream"
LICENSE_URL = "https://eternalhaven.ca/lygo-music-license.html"

# Fork root — Lightfather / Justin Helmer / Excavationpro music realm
HUB_ID = "LATTICE_EXCAVATIONPRO_MUSIC"
LIGHTFATHER = "CHAMPION_LIGHTFATHER"
GALAXY_ID = "GALAXY_EXCAVATIONPRO_MUSIC"
CONSTELLATION_ID = "music_codex"

MAX_TRACKS_PER_ALBUM = 80  # safety: expand fully for tagged albums under this
MAX_UNTAGGED_SAMPLE = 0  # do not flood chart with 10k untagged masters


def _safe_id(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", (s or "").upper()).strip("_")
    return (s or "UNKNOWN")[:64]


def _load_playlist() -> dict:
    p = CAT / "public_stream_playlist.json"
    if not p.is_file():
        return {"tracks": []}
    return json.loads(p.read_text(encoding="utf-8"))


def _load_lyrics() -> dict:
    p = CAT / "lyrics" / "lyrics_index.json"
    if not p.is_file():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def build_music_nodes() -> tuple[list[dict], dict]:
    """Return (nodes, stats) for chart merge."""
    pl = _load_playlist()
    lyrics = _load_lyrics()
    tracks = pl.get("tracks") or []
    total = len(tracks)
    by_album: dict[str, list[dict]] = defaultdict(list)
    untagged = 0
    for t in tracks:
        alb = (t.get("album") or "").strip()
        if alb:
            by_album[alb].append(t)
        else:
            untagged += 1

    nodes: list[dict] = []

    # Hub — sovereign music portal
    nodes.append(
        {
            "id": HUB_ID,
            "kind": "music_hub",
            "name": "Excavationpro Music Portal",
            "glyph": "🎧",
            "equation": f"Listen({total}) ⊗ CAS ⊗ HF",
            "tone": "432Hz",
            "tags": [
                "MUSIC",
                "EXCAVATIONPRO",
                "LIGHTFATHER",
                "LATTICE",
                "LISTEN_PORTAL",
                "MUSIC_CODEX",
            ],
            "connections": [LIGHTFATHER, "SEAL_000", "PORTAL_HF_MUSIC", "PORTAL_STACK"],
            "urls": {
                "live": LISTEN_URL,
                "hf": HF_STREAM,
                "license": LICENSE_URL,
            },
            "layer": 2,
            "meta": {
                "steward": "Justin Helmer / Lightfather / Excavationpro",
                "stream_count": total,
                "tagged_albums": len(by_album),
                "untagged_streams": untagged,
                "live_map": True,
            },
        }
    )

    # License star
    nodes.append(
        {
            "id": "LATTICE_LYGO_MUSIC_LICENSE",
            "kind": "music_hub",
            "name": "LYGO Music License v1.0",
            "glyph": "📜",
            "equation": "FreeListen ∧ FreeDownload ∧ AllRightsReserved",
            "tone": "528Hz",
            "tags": ["MUSIC", "LICENSE", "EXCAVATIONPRO", "MUSIC_CODEX"],
            "connections": [HUB_ID, LIGHTFATHER],
            "urls": {"live": LICENSE_URL},
            "layer": 3,
        }
    )

    lyrics_by_sha = (lyrics.get("by_sha256") or {}) if isinstance(lyrics, dict) else {}

    for album, album_tracks in sorted(by_album.items(), key=lambda x: x[0].lower()):
        aid = f"MUSIC_ALBUM_{_safe_id(album)}"
        n_tracks = len(album_tracks)
        with_lyrics = sum(1 for t in album_tracks if t.get("sha256") in lyrics_by_sha)
        nodes.append(
            {
                "id": aid,
                "kind": "music_album",
                "name": album,
                "glyph": "💿",
                "equation": f"Album({n_tracks}) · lyrics={with_lyrics}",
                "tone": "440Hz",
                "tags": [
                    "MUSIC",
                    "MUSIC_ALBUM",
                    "EXCAVATIONPRO",
                    "LIGHTFATHER",
                    "MUSIC_CODEX",
                    _safe_id(album)[:24],
                ],
                "connections": [HUB_ID, LIGHTFATHER],
                "urls": {
                    "live": f"{LISTEN_URL}?q={album.replace(' ', '+')}",
                    "license": LICENSE_URL,
                },
                "layer": 3,
                "meta": {
                    "album": album,
                    "track_count": n_tracks,
                    "lyrics_count": with_lyrics,
                    "artist": album_tracks[0].get("artist") or "Excavationpro",
                },
            }
        )

        # Expand track stars for tagged albums (live map)
        if n_tracks <= MAX_TRACKS_PER_ALBUM:
            for t in album_tracks:
                sha = t.get("sha256") or ""
                if not sha:
                    continue
                tid = f"MUSIC_TRACK_{sha[:16].upper()}"
                title = t.get("title") or sha[:12]
                mon = (t.get("moniker") or "").strip()
                has_lyr = sha in lyrics_by_sha
                name = f"{title}" + (f" · {mon}" if mon else "")
                nodes.append(
                    {
                        "id": tid,
                        "kind": "music_track",
                        "name": name[:120],
                        "glyph": "♪" if has_lyr else "·",
                        "equation": f"SHA256({sha[:12]}…)",
                        "tone": "396Hz",
                        "tags": [
                            "MUSIC",
                            "MUSIC_TRACK",
                            "EXCAVATIONPRO",
                            "MUSIC_CODEX",
                            "HAS_LYRICS" if has_lyr else "AUDIO_ONLY",
                        ],
                        "connections": [aid, HUB_ID],
                        "urls": {
                            "stream": t.get("stream_url") or "",
                            "live": f"{LISTEN_URL}?q={sha[:16]}",
                        },
                        "layer": 4,
                        "meta": {
                            "sha256": sha,
                            "album": album,
                            "moniker": mon,
                            "has_lyrics": has_lyr,
                            "isrcs": t.get("isrcs") or [],
                        },
                    }
                )
                if has_lyr:
                    nodes[-1]["connections"].append("LATTICE_LYGO_MUSIC_LICENSE")

    # Catalog cloud (single star) so untagged vault remains represented without flooding
    if untagged:
        nodes.append(
            {
                "id": "MUSIC_CATALOG_CLOUD",
                "kind": "music_hub",
                "name": f"Sovereign Stream Cloud ({untagged})",
                "glyph": "☁♪",
                "equation": f"CAS_streams={untagged}+tagged",
                "tone": "174Hz",
                "tags": ["MUSIC", "EXCAVATIONPRO", "CATALOG_CLOUD", "MUSIC_CODEX"],
                "connections": [HUB_ID, LIGHTFATHER],
                "urls": {"live": LISTEN_URL, "hf": HF_STREAM},
                "layer": 3,
                "meta": {
                    "untagged_count": untagged,
                    "note": "Full 10k+ vault playable on listen portal; chart shows tagged albums as live forks.",
                },
            }
        )

    stats = {
        "total_playlist_tracks": total,
        "tagged_albums": len(by_album),
        "music_nodes": len(nodes),
        "track_stars": sum(1 for n in nodes if n.get("kind") == "music_track"),
        "album_stars": sum(1 for n in nodes if n.get("kind") == "music_album"),
        "lyrics_linked": sum(1 for n in nodes if "HAS_LYRICS" in (n.get("tags") or [])),
    }
    return nodes, stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--rebuild-chart", action="store_true")
    ap.add_argument("--sync-excav", action="store_true")
    args = ap.parse_args()
    nodes, stats = build_music_nodes()
    report = {
        "signature": "Delta9Phi963-MUSIC-STAR-MAP-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "galaxy": GALAXY_ID,
        "constellation": CONSTELLATION_ID,
        "fork_of": LIGHTFATHER,
        "stats": stats,
        "nodes": nodes if args.json else f"{len(nodes)} nodes (use --json for full)",
    }
    if args.json:
        print(json.dumps({"stats": stats, "nodes": nodes}, indent=2))
    else:
        print(json.dumps({"stats": stats, "preview": [n["id"] for n in nodes[:20]]}, indent=2))

    out = CAT / "music_star_map_last.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps({"stats": stats, "node_ids": [n["id"] for n in nodes], "nodes": nodes}, indent=2)
        + "\n",
        encoding="utf-8",
    )

    if args.rebuild_chart:
        r = subprocess.run(
            [sys.executable, str(STACK / "tools" / "build_haven_star_chart.py")],
            cwd=str(STACK),
        )
        if r.returncode != 0:
            return r.returncode
        if args.sync_excav:
            subprocess.run(
                [
                    sys.executable,
                    str(STACK / "tools" / "sync_excavationpro_haven_star.py"),
                    "--dest",
                    str(STACK.parent / "Excavationpro"),
                ],
                cwd=str(STACK),
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
