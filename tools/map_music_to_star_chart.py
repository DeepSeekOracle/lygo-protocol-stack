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

MAX_TRACKS_PER_ALBUM = 120  # expand tagged albums fully under this
# Chart policy: map every unique ISRC stream as a star (preferred identity).
# Non-ISRC vault masters remain a single cloud star (avoid 10k flood).


def _safe_id(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", (s or "").upper()).strip("_")
    return (s or "UNKNOWN")[:64]


def _norm_isrc(s: object) -> str:
    if not s:
        return ""
    return re.sub(r"[^A-Za-z0-9]", "", str(s).upper())


def _track_isrcs(t: dict) -> list[str]:
    out: list[str] = []
    for x in t.get("isrcs") or []:
        n = _norm_isrc(x)
        if n and len(n) >= 12:
            out.append(n)
    one = _norm_isrc(t.get("isrc"))
    if one and len(one) >= 12 and one not in out:
        out.append(one)
    return out


def _fmt_isrc(isrc: str) -> str:
    i = _norm_isrc(isrc)
    if len(i) == 12:
        return f"{i[0:2]}-{i[2:5]}-{i[5:7]}-{i[7:12]}"
    return i


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


def _make_track_node(
    *,
    tid: str,
    title: str,
    sha: str,
    mon: str,
    has_lyr: bool,
    album: str,
    isrcs: list[str],
    stream_url: str,
    connections: list[str],
    primary_isrc: str = "",
) -> dict:
    isrc_disp = _fmt_isrc(primary_isrc or (isrcs[0] if isrcs else ""))
    name = title[:90]
    if mon:
        name = f"{name} · {mon}"[:120]
    eq = f"ISRC({isrc_disp})" if isrc_disp else f"SHA256({sha[:12]}…)"
    tags = [
        "MUSIC",
        "MUSIC_TRACK",
        "EXCAVATIONPRO",
        "LIGHTFATHER",
        "MUSIC_CODEX",
        "HAS_LYRICS" if has_lyr else "AUDIO_ONLY",
    ]
    if isrc_disp:
        tags.append("HAS_ISRC")
        tags.append("ISRC_STAR")
    node = {
        "id": tid,
        "kind": "music_track",
        "name": name[:120],
        "glyph": "★" if isrc_disp else ("♪" if has_lyr else "·"),
        "equation": eq,
        "tone": "396Hz",
        "tags": tags,
        "connections": list(connections),
        "urls": {
            "stream": stream_url or "",
            "live": f"{LISTEN_URL}?q={(primary_isrc or sha)[:16]}",
        },
        "layer": 4,
        "meta": {
            "sha256": sha,
            "album": album,
            "moniker": mon,
            "has_lyrics": has_lyr,
            "isrcs": isrcs,
            "primary_isrc": primary_isrc or (isrcs[0] if isrcs else ""),
        },
    }
    if has_lyr:
        node["connections"].append("LATTICE_LYGO_MUSIC_LICENSE")
    return node


def build_music_nodes() -> tuple[list[dict], dict]:
    """Return (nodes, stats) for chart merge.

    Policy:
      1) Portal hub + license
      2) All unique ISRC streams as stars (primary population)
      3) Tagged albums (album= field) as album hubs + their tracks
      4) Non-ISRC remainder as one catalog cloud
    """
    pl = _load_playlist()
    lyrics = _load_lyrics()
    tracks = pl.get("tracks") or []
    total = len(tracks)
    by_album: dict[str, list[dict]] = defaultdict(list)
    no_album = 0
    for t in tracks:
        alb = (t.get("album") or "").strip()
        if alb:
            by_album[alb].append(t)
        else:
            no_album += 1

    # Unique ISRC → best track row
    by_isrc: dict[str, dict] = {}
    for t in tracks:
        for isrc in _track_isrcs(t):
            prev = by_isrc.get(isrc)
            if prev is None:
                by_isrc[isrc] = t
                continue
            # prefer album-tagged, then has stream, then shorter title
            score = (
                (2 if (t.get("album") or "").strip() else 0)
                + (1 if t.get("stream_url") else 0)
                + (1 if t.get("sha256") else 0)
            )
            pscore = (
                (2 if (prev.get("album") or "").strip() else 0)
                + (1 if prev.get("stream_url") else 0)
                + (1 if prev.get("sha256") else 0)
            )
            if score > pscore:
                by_isrc[isrc] = t
            elif score == pscore and len(str(t.get("title") or "")) < len(str(prev.get("title") or "")):
                by_isrc[isrc] = t

    nodes: list[dict] = []
    lyrics_by_sha = (lyrics.get("by_sha256") or {}) if isinstance(lyrics, dict) else {}
    added_sha: set[str] = set()
    added_ids: set[str] = set()

    def add_node(n: dict) -> None:
        if n["id"] in added_ids:
            return
        nodes.append(n)
        added_ids.add(n["id"])
        sha = (n.get("meta") or {}).get("sha256") or ""
        if sha:
            added_sha.add(sha)

    # Hub — sovereign music portal
    add_node(
        {
            "id": HUB_ID,
            "kind": "music_hub",
            "name": "Excavationpro Music Portal",
            "glyph": "🎧",
            "equation": f"Listen({total}) ⊗ ISRC({len(by_isrc)}) ⊗ HF",
            "tone": "432Hz",
            "tags": [
                "MUSIC",
                "EXCAVATIONPRO",
                "LIGHTFATHER",
                "LATTICE",
                "LISTEN_PORTAL",
                "MUSIC_CODEX",
                "ISRC_MAP",
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
                "unique_isrcs": len(by_isrc),
                "tagged_albums": len(by_album),
                "no_album_streams": no_album,
                "live_map": True,
                "map_policy": "isrc_stars_primary",
            },
        }
    )

    # License star
    add_node(
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

    # ISRC registry hub
    isrc_hub = "MUSIC_ISRC_REGISTRY"
    add_node(
        {
            "id": isrc_hub,
            "kind": "music_hub",
            "name": f"ISRC Registry ({len(by_isrc)} stars)",
            "glyph": "◎",
            "equation": f"unique_ISRC={len(by_isrc)}",
            "tone": "741Hz",
            "tags": ["MUSIC", "ISRC", "ISRC_REGISTRY", "EXCAVATIONPRO", "MUSIC_CODEX", "LIGHTFATHER"],
            "connections": [HUB_ID, LIGHTFATHER, "LATTICE_LYGO_MUSIC_LICENSE"],
            "urls": {
                "live": f"{LISTEN_URL}?q=isrc",
                "hf": HF_STREAM,
                "license": LICENSE_URL,
            },
            "layer": 3,
            "meta": {
                "unique_isrcs": len(by_isrc),
                "note": "Each star is a unique commercial ISRC from the sovereign stream catalog.",
            },
        }
    )

    # Bucket hubs by ISRC country/registrant prefix (first 5 alnum) for sky structure
    # e.g. QZMHK, QZS65, QT6EW → cluster parents
    buckets: dict[str, list[str]] = defaultdict(list)
    for isrc in by_isrc:
        buckets[isrc[:5]].append(isrc)

    for prefix, isrc_list in sorted(buckets.items(), key=lambda x: (-len(x[1]), x[0])):
        bid = f"MUSIC_ISRC_BUCKET_{_safe_id(prefix)}"
        add_node(
            {
                "id": bid,
                "kind": "music_hub",
                "name": f"ISRC · {prefix} ({len(isrc_list)})",
                "glyph": "✧",
                "equation": f"prefix({prefix})",
                "tone": "528Hz",
                "tags": ["MUSIC", "ISRC_BUCKET", "MUSIC_CODEX", "EXCAVATIONPRO"],
                "connections": [isrc_hub, HUB_ID],
                "urls": {"live": f"{LISTEN_URL}?q={prefix}"},
                "layer": 3,
                "meta": {"prefix": prefix, "count": len(isrc_list)},
            }
        )

    # ISRC track stars
    for isrc, t in sorted(by_isrc.items(), key=lambda x: (x[1].get("title") or "", x[0])):
        sha = t.get("sha256") or ""
        if not sha:
            continue
        tid = f"MUSIC_ISRC_{isrc}"
        title = t.get("title") or isrc
        mon = (t.get("moniker") or "").strip()
        album = (t.get("album") or "").strip()
        has_lyr = sha in lyrics_by_sha
        prefix = isrc[:5]
        bucket = f"MUSIC_ISRC_BUCKET_{_safe_id(prefix)}"
        conns = [isrc_hub, bucket, HUB_ID]
        if album:
            conns.append(f"MUSIC_ALBUM_{_safe_id(album)}")
        add_node(
            _make_track_node(
                tid=tid,
                title=title,
                sha=sha,
                mon=mon,
                has_lyr=has_lyr,
                album=album,
                isrcs=_track_isrcs(t),
                stream_url=t.get("stream_url") or "",
                connections=conns,
                primary_isrc=isrc,
            )
        )

    # Tagged albums (explicit album=) — hubs + any non-ISRC tracks still in album
    for album, album_tracks in sorted(by_album.items(), key=lambda x: x[0].lower()):
        aid = f"MUSIC_ALBUM_{_safe_id(album)}"
        n_tracks = len(album_tracks)
        with_lyrics = sum(1 for t in album_tracks if t.get("sha256") in lyrics_by_sha)
        with_isrc_n = sum(1 for t in album_tracks if _track_isrcs(t))
        add_node(
            {
                "id": aid,
                "kind": "music_album",
                "name": album,
                "glyph": "💿",
                "equation": f"Album({n_tracks}) · ISRC={with_isrc_n} · lyrics={with_lyrics}",
                "tone": "440Hz",
                "tags": [
                    "MUSIC",
                    "MUSIC_ALBUM",
                    "EXCAVATIONPRO",
                    "LIGHTFATHER",
                    "MUSIC_CODEX",
                    _safe_id(album)[:24],
                ],
                "connections": [HUB_ID, LIGHTFATHER, isrc_hub],
                "urls": {
                    "live": f"{LISTEN_URL}?q={album.replace(' ', '+')}",
                    "license": LICENSE_URL,
                },
                "layer": 3,
                "meta": {
                    "album": album,
                    "track_count": n_tracks,
                    "lyrics_count": with_lyrics,
                    "isrc_count": with_isrc_n,
                    "artist": album_tracks[0].get("artist") or "Excavationpro",
                },
            }
        )

        if n_tracks <= MAX_TRACKS_PER_ALBUM:
            for t in album_tracks:
                sha = t.get("sha256") or ""
                if not sha or sha in added_sha:
                    # already on chart via ISRC star — still link album if ISRC node exists
                    continue
                # non-ISRC album track (e.g. new VENGEANCE cuts without ISRC yet)
                tid = f"MUSIC_TRACK_{sha[:16].upper()}"
                title = t.get("title") or sha[:12]
                mon = (t.get("moniker") or "").strip()
                has_lyr = sha in lyrics_by_sha
                add_node(
                    _make_track_node(
                        tid=tid,
                        title=title,
                        sha=sha,
                        mon=mon,
                        has_lyr=has_lyr,
                        album=album,
                        isrcs=_track_isrcs(t),
                        stream_url=t.get("stream_url") or "",
                        connections=[aid, HUB_ID],
                    )
                )

    # Non-ISRC remainder cloud
    non_isrc = sum(1 for t in tracks if not _track_isrcs(t))
    if non_isrc:
        add_node(
            {
                "id": "MUSIC_CATALOG_CLOUD",
                "kind": "music_hub",
                "name": f"Non-ISRC Stream Cloud ({non_isrc})",
                "glyph": "☁♪",
                "equation": f"streams_without_ISRC={non_isrc}",
                "tone": "174Hz",
                "tags": ["MUSIC", "EXCAVATIONPRO", "CATALOG_CLOUD", "MUSIC_CODEX"],
                "connections": [HUB_ID, LIGHTFATHER],
                "urls": {"live": LISTEN_URL, "hf": HF_STREAM},
                "layer": 3,
                "meta": {
                    "non_isrc_count": non_isrc,
                    "note": (
                        "Vault streams without ISRC stay in this cloud. "
                        "Commercial ISRC identity stars live under MUSIC_ISRC_REGISTRY."
                    ),
                },
            }
        )

    stats = {
        "total_playlist_tracks": total,
        "unique_isrcs": len(by_isrc),
        "isrc_buckets": len(buckets),
        "tagged_albums": len(by_album),
        "music_nodes": len(nodes),
        "track_stars": sum(1 for n in nodes if n.get("kind") == "music_track"),
        "isrc_track_stars": sum(
            1 for n in nodes if n.get("kind") == "music_track" and "ISRC_STAR" in (n.get("tags") or [])
        ),
        "album_stars": sum(1 for n in nodes if n.get("kind") == "music_album"),
        "lyrics_linked": sum(1 for n in nodes if "HAS_LYRICS" in (n.get("tags") or [])),
        "non_isrc_cloud": non_isrc,
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
