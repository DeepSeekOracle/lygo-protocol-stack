#!/usr/bin/env python3
"""Remove floating mini/overlay player from listen portal — keep bottom dock only."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

LISTEN = Path(r"I:\E Drive\Excavationpro\excavationpro-listen.html")
DOCS = Path(r"I:\E Drive\lygo-protocol-stack\docs\excavationpro-listen.html")


def main() -> int:
    html = LISTEN.read_text(encoding="utf-8")
    before = len(html)

    # CSS block for mini-player
    html = re.sub(
        r"/\* --- Mini player --- \*/[\s\S]*?(?=/\* ---|\.nav-main a\.tool|/\* =====|$)",
        "",
        html,
        count=1,
    )
    # Also remove standalone .mini-player rules if not in comment block
    html = re.sub(
        r"\.mini-player\s*\{[^}]*\}(?:\s*\.mini-player[^{]*\{[^}]*\})*",
        "",
        html,
    )
    html = re.sub(r"\.mini-player[^{]*\{[^}]*\}", "", html)
    html = re.sub(r"body\.has-mini[^{]*\{[^}]*\}", "", html)
    # multi-line mini-player CSS
    html = re.sub(
        r"\.mini-player\s*\{[\s\S]*?\n\}",
        "",
        html,
    )
    html = re.sub(
        r"\.mini-player\.[a-zA-Z-]+\s*\{[\s\S]*?\n\}",
        "",
        html,
    )
    html = re.sub(
        r"\.mini-player [^{]+\{[\s\S]*?\n\}",
        "",
        html,
    )
    html = re.sub(
        r"body\.has-mini[^{]*\{[\s\S]*?\n\}",
        "",
        html,
    )

    # HTML element
    html = re.sub(
        r'<div class="mini-player"[\s\S]*?</div>\s*',
        "",
        html,
        count=1,
    )

    # JS: updateMini function and listeners
    html = re.sub(
        r"// --- Mini player ---[\s\S]*?(?=// ---|/\* =====|function ensure|document\.getElementById\('btn-share'\)|$)",
        "",
        html,
        count=1,
    )
    # Broader: remove updateMini and its call sites
    html = re.sub(
        r"function updateMini\(\)\s*\{[\s\S]*?\n  \}\n?",
        "function updateMini(){ /* mini player removed */ }\n",
        html,
        count=1,
    )
    html = re.sub(
        r"document\.getElementById\('mp-play'\)\?\.addEventListener\([\s\S]*?\}\);\n?",
        "",
        html,
    )
    html = re.sub(
        r"document\.getElementById\('mp-next'\)\?\.addEventListener\([\s\S]*?\}\);\n?",
        "",
        html,
    )
    html = re.sub(
        r"document\.getElementById\('mp-prev'\)\?\.addEventListener\([\s\S]*?\}\);\n?",
        "",
        html,
    )
    html = re.sub(
        r"document\.getElementById\('mp-expand'\)\?\.addEventListener\([\s\S]*?\}\);\n?",
        "",
        html,
    )
    # Remove has-mini class toggles
    html = html.replace("document.body.classList.add('has-mini');", "")
    html = html.replace("document.body.classList.remove('has-mini');", "")
    html = html.replace('document.body.classList.add("has-mini");', "")
    html = html.replace('document.body.classList.remove("has-mini");', "")

    # Kill audio play/pause listeners that only call updateMini if we can isolate them
    # Safer: leave updateMini as no-op

    if len(html) < before * 0.85:
        raise SystemExit(f"abort shrink {before}->{len(html)}")

    LISTEN.write_text(html, encoding="utf-8")
    shutil.copy2(LISTEN, DOCS)
    print(f"wrote {len(html)} (was {before})")
    for s in ("mini-player", "has-mini", "mp-play", "updateMini"):
        print(s, html.count(s))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
