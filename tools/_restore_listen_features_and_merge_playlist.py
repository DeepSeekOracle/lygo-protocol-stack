#!/usr/bin/env python3
"""Restore full listen features + merge current playlist + wire lyrics panel."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
EXCAV = STACK.parent / "Excavationpro"
CAT = STACK / "data" / "music_catalog"
DOCS = STACK / "docs"

FEATURE_MARKERS = [
    "filter-chips",
    "wave-canvas",
    "play-listing",
    "Crossfade",
    "btn-pwa-install",
    "share-modal",
    "mediaSession",
    "btn-radio",
]


def slim_playlist(pl: dict) -> dict:
    tracks = []
    for t in pl.get("tracks") or []:
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
        "public_base_url": pl.get("public_base_url"),
        "hf_dataset": pl.get("hf_dataset")
        or "https://huggingface.co/datasets/DeepSeekOracle/excavationpro-music-stream",
        "stats": pl.get("stats") or {},
        "generated_at": pl.get("generated_at") or pl.get("published_at"),
        "tracks": tracks,
    }


def ensure_plugins() -> None:
    src_listing = DOCS / "listen-plugins" / "play-listing.js"
    if not src_listing.is_file():
        src_listing = EXCAV / "listen-plugins" / "play-listing.js"
    src_lyrics = DOCS / "listen-plugins" / "lyrics-panel.js"
    if not src_lyrics.is_file():
        src_lyrics = EXCAV / "listen-plugins" / "lyrics-panel.js"

    roots = [
        EXCAV,
        DOCS,
        Path(r"I:\E Drive\Excavationpro"),
        Path(r"I:\E Drive\lygo-protocol-stack\docs"),
    ]
    for root in roots:
        plug = root / "listen-plugins"
        plug.mkdir(parents=True, exist_ok=True)
        data = root / "data"
        data.mkdir(parents=True, exist_ok=True)
        for src, dest in (
            (src_listing, plug / "play-listing.js"),
            (src_lyrics, plug / "lyrics-panel.js"),
        ):
            if not src.is_file():
                continue
            try:
                if dest.resolve() == src.resolve():
                    continue
                shutil.copy2(src, dest)
            except OSError as e:
                print("plugin copy warn", dest, e)
        for src, name in (
            (CAT / "lyrics" / "lyrics_index.json", "lyrics_index.json"),
            (CAT / "public_stream_playlist.json", "public_stream_playlist.json"),
        ):
            if src.is_file():
                try:
                    shutil.copy2(src, data / name)
                except OSError as e:
                    print("data copy warn", data / name, e)


def patch_html(path: Path, slim_pl: dict) -> dict:
    if not path.is_file():
        return {"path": str(path), "ok": False, "error": "missing"}
    html = path.read_text(encoding="utf-8")
    report: dict = {
        "path": str(path),
        "markers_before": {m: (m in html) for m in FEATURE_MARKERS},
    }

    m = re.search(
        r'(<script id="boot" type="application/json">)(.*?)(</script>)',
        html,
        re.S,
    )
    if not m:
        return {**report, "ok": False, "error": "no boot json"}
    try:
        data = json.loads(m.group(2))
    except json.JSONDecodeError:
        data = {}
    data["playlist"] = slim_pl
    new_boot = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    html = html[: m.start(2)] + new_boot + html[m.end(2) :]

    if "listen-plugins/play-listing.js" not in html:
        html = html.replace(
            "</body>",
            '<script src="listen-plugins/play-listing.js?v=5" defer></script>\n</body>',
            1,
        )
    if "lyrics-panel.js" not in html:
        html = html.replace(
            "</body>",
            '<script src="listen-plugins/lyrics-panel.js?v=1" defer></script>\n</body>',
            1,
        )
    if 'id="play-listing-mount"' not in html:
        if 'id="panel-player"' in html:
            html = html.replace(
                'id="panel-player">',
                'id="panel-player">\n    <div id="play-listing-mount" aria-live="polite"></div>',
                1,
            )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    report["ok"] = True
    report["tracks"] = len(slim_pl.get("tracks") or [])
    report["size"] = path.stat().st_size
    report["markers_after"] = {m: (m in html) for m in FEATURE_MARKERS}
    report["lyrics_panel"] = "lyrics-panel.js" in html
    report["play_listing"] = "play-listing.js" in html
    report["vengeance_in_boot"] = "VENGEANCE" in html
    return report


def main() -> int:
    excav = EXCAV / "excavationpro-listen.html"
    if not excav.is_file():
        print("missing excav listen page")
        return 2

    html0 = excav.read_text(encoding="utf-8")
    missing = [m for m in FEATURE_MARKERS if m not in html0]
    if missing:
        print("restoring ba25875 full-feature page; missing:", missing)
        raw = subprocess.check_output(
            ["git", "-C", str(EXCAV), "show", "ba25875:excavationpro-listen.html"]
        )
        excav.write_bytes(raw)

    pl = json.loads((CAT / "public_stream_playlist.json").read_text(encoding="utf-8"))
    slim = slim_playlist(pl)
    print("playlist tracks", len(slim["tracks"]))
    print(
        "vengeance tracks",
        sum(1 for t in slim["tracks"] if (t.get("album") or "") == "VENGEANCE CODEX"),
    )

    ensure_plugins()

    targets = [
        excav,
        DOCS / "excavationpro-listen.html",
        Path(r"I:\E Drive\Excavationpro\excavationpro-listen.html"),
        Path(r"I:\E Drive\lygo-protocol-stack\docs\excavationpro-listen.html"),
    ]

    # seed feature-complete file to all targets then patch playlist
    for t in targets:
        if t != excav:
            try:
                t.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(excav, t)
            except OSError as e:
                print("seed warn", t, e)

    results = [patch_html(t, slim) for t in targets if t.is_file()]

    # re-apply v2 enhance (additive) on stack enhance target paths
    enhance = STACK / "tools" / "_enhance_listen_portal_v2.py"
    if enhance.is_file():
        r = subprocess.run(
            [sys.executable, str(enhance)],
            cwd=str(STACK),
            capture_output=True,
            text=True,
            timeout=180,
        )
        print((r.stdout or "")[-600:])
        if r.returncode != 0:
            print("enhance warn", (r.stderr or "")[-300:])

    # enhance may rewrite pages — re-seed from best and re-patch
    # Prefer excav after enhance if enhance wrote I:\ paths
    ensure_plugins()
    # if enhance improved I: Drive copy, pull best size with features
    candidates = [t for t in targets if t.is_file()]
    best = max(candidates, key=lambda p: (sum(1 for m in FEATURE_MARKERS if m in p.read_text(encoding="utf-8")), p.stat().st_size))
    print("best feature file", best, best.stat().st_size)
    for t in targets:
        if t != best and t.parent.exists():
            try:
                shutil.copy2(best, t)
            except OSError:
                pass
    results = [patch_html(t, slim) for t in targets if t.is_file()]

    print(json.dumps(results, indent=2))
    final = excav.read_text(encoding="utf-8")
    print("FINAL size", excav.stat().st_size)
    for m in FEATURE_MARKERS + ["lyrics-panel", "play-listing.js", "VENGEANCE"]:
        print(("OK" if m in final else "MISS"), m)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
