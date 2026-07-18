#!/usr/bin/env python3
"""Restore listen page to pre-play-count working build + tiny safe fixes only."""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

EXCAV = Path(r"I:\E Drive\Excavationpro")
STACK = Path(r"I:\E Drive\lygo-protocol-stack")
LISTEN = EXCAV / "excavationpro-listen.html"
DOCS = STACK / "docs" / "excavationpro-listen.html"


def main() -> int:
    # Prefer restored file already written; if play-count markers present, bail message
    html = LISTEN.read_text(encoding="utf-8")

    # Minimal safety: never MediaElementSource (HF mute risk)
    if "createMediaElementSource(audio)" in html:
        html = html.replace(
            "createMediaElementSource(audio)",
            "null /* disabled: HF stream playback */",
        )
        html = html.replace(
            "function ensureAnalyser() {",
            "function ensureAnalyser() { return; // disabled\n",
            1,
        )
        print("disabled MediaElementSource")

    # Clean audio element (single, no crossorigin)
    html = re.sub(
        r"<audio\b[^>]*>\s*(?:</audio>\s*)*",
        '<audio id="audio" controls preload="none" playsinline></audio>\n',
        html,
        count=1,
    )

    # Disable crossfade if present (can stall)
    if "function maybeCrossfade()" in html:
        html = re.sub(
            r"function maybeCrossfade\(\)\s*\{",
            "function maybeCrossfade(){ return;",
            html,
            count=1,
        )
        print("crossfade off")

    LISTEN.write_text(html, encoding="utf-8")
    shutil.copy2(LISTEN, DOCS)

    # syntax check
    scripts = re.findall(
        r"<script(?![^>]*application/json)[^>]*>([\s\S]*?)</script>", html
    )
    main_js = max(scripts, key=len)
    tmp = STACK / "_tmp_listen_main.js"
    tmp.write_text(main_js, encoding="utf-8")
    r = subprocess.run(["node", "--check", str(tmp)], capture_output=True, text=True)
    print("node", r.returncode, (r.stderr or "OK")[:400])
    if r.returncode != 0:
        return 1

    print("size", len(html))
    print("has play counts", any(x in html for x in ("jsonblob", "hits.dwyl", "play-trophy", "PLAYINDEX_FINAL")))
    print("has radio", "btn-radio" in html)
    print("has sticky", "sticky-top" in html)
    print("audio", re.search(r"<audio[^>]*>", html).group(0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
