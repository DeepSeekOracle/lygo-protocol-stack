#!/usr/bin/env python3
"""Install additive play-listing plugin into working listen page (minimal core touch)."""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

EXCAV = Path(r"I:\E Drive\Excavationpro")
STACK = Path(r"I:\E Drive\lygo-protocol-stack")
LISTEN = EXCAV / "excavationpro-listen.html"
DOCS = STACK / "docs" / "excavationpro-listen.html"
PLUGIN = EXCAV / "listen-plugins" / "play-listing.js"
PLUGIN_DOCS = STACK / "docs" / "listen-plugins" / "play-listing.js"


def main() -> int:
    if not PLUGIN.is_file():
        raise SystemExit(f"missing plugin {PLUGIN}")

    # syntax-check plugin
    r = subprocess.run(["node", "--check", str(PLUGIN)], capture_output=True, text=True)
    print("plugin node", r.returncode, (r.stderr or "OK")[:300])
    if r.returncode != 0:
        return 1

    html = LISTEN.read_text(encoding="utf-8")
    before = len(html)

    # Must not already have broken inlined systems
    for bad in ("PLAYINDEX_FINAL", "audio./*"):
        if bad in html:
            print("WARN core still has", bad)

    # 1) Mount before track list
    if 'id="play-listing-mount"' not in html:
        if '<div class="list" id="list">' in html:
            html = html.replace(
                '<div class="list" id="list">',
                '<div id="play-listing-mount" aria-live="polite"></div>\n    <div class="list" id="list">',
                1,
            )
            print("[ok] mount before list")
        else:
            raise SystemExit("list not found")

    # 2) LYGO_LISTEN export — additive, inside main script before final </script>
    export = """
// LYGO_LISTEN_EXPORT — safe hook for additive plugins (do not remove playIndex)
window.LYGO_LISTEN = {
  playIndex: function (i) { return playIndex(i); },
  getTracks: function () { return tracks; },
  getCurrent: function () { return current; },
  getAudio: function () { return audio; }
};
"""
    if "LYGO_LISTEN_EXPORT" not in html:
        # insert before last </script> of main player (last occurrence)
        idx = html.rfind("</script>")
        if idx < 0:
            raise SystemExit("no script end")
        html = html[:idx] + export + "\n" + html[idx:]
        print("[ok] LYGO_LISTEN export")

    # 3) Plugin script AFTER main script (external — failure isolated)
    tag = '<script src="listen-plugins/play-listing.js?v=1" defer></script>'
    if "listen-plugins/play-listing.js" not in html:
        html = html.replace("</body>", tag + "\n</body>", 1)
        print("[ok] plugin script tag")

    if len(html) < before * 0.9:
        raise SystemExit(f"shrink {before}->{len(html)}")

    LISTEN.write_text(html, encoding="utf-8")
    shutil.copy2(LISTEN, DOCS)

    # mirror plugin to docs for stack pages completeness
    PLUGIN_DOCS.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PLUGIN, PLUGIN_DOCS)

    # verify core JS still valid
    scripts = re.findall(
        r"<script(?![^>]*application/json)(?![^>]*src=)[^>]*>([\s\S]*?)</script>",
        html,
    )
    if not scripts:
        # fallback: all inline scripts without src
        scripts = []
        for m in re.finditer(r"<script(?![^>]*src=)([^>]*)>([\s\S]*?)</script>", html):
            if "application/json" in m.group(1) or "ld+json" in m.group(1):
                continue
            scripts.append(m.group(2))
    main_js = max(scripts, key=len)
    tmp = STACK / "_tmp_listen_main.js"
    tmp.write_text(main_js, encoding="utf-8")
    r2 = subprocess.run(["node", "--check", str(tmp)], capture_output=True, text=True)
    print("core node", r2.returncode, (r2.stderr or "OK")[:400])
    if r2.returncode != 0:
        return 1

    print("size", len(html))
    print("mount", 'id="play-listing-mount"' in html)
    print("plugin tag", "play-listing.js" in html)
    print("export", "LYGO_LISTEN_EXPORT" in html)
    print("no jsonblob in core", "jsonblob.com" not in html)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
