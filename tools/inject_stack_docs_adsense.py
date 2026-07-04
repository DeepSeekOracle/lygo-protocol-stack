#!/usr/bin/env python3
"""AdSense head snippet on lygo-protocol-stack/docs public HTML pages."""

from __future__ import annotations

import re
import sys
from pathlib import Path

PUB = "ca-pub-0646320966060599"
MARKER = f"client={PUB}"
META = f'  <meta name="google-adsense-account" content="{PUB}" />\n'
SCRIPT = (
    f'  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={PUB}"\n'
    '       crossorigin="anonymous"></script>\n'
)
BLOCK = META + SCRIPT
DOCS = Path(__file__).resolve().parents[1] / "docs"


def inject(text: str) -> str:
    if MARKER in text:
        return text
    m = re.search(r"(<head[^>]*>\s*)", text, re.I)
    if not m:
        return text
    insert_at = m.end()
    vm = re.search(r"<meta[^>]+viewport[^>]*>\s*", text[insert_at : insert_at + 600], re.I)
    if vm:
        insert_at += vm.end()
    return text[:insert_at] + "\n" + BLOCK + text[insert_at:]


def main() -> int:
    changed = []
    for html in DOCS.rglob("*.html"):
        if "haven_star_chart" in str(html):
            continue
        raw = html.read_text(encoding="utf-8", errors="replace")
        new = inject(raw)
        if new != raw:
            html.write_text(new, encoding="utf-8")
            changed.append(html.relative_to(DOCS))
    print(f"updated {len(changed)}", *[str(c) for c in changed], sep="\n ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())