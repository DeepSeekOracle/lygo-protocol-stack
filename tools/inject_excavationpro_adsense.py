#!/usr/bin/env python3
"""Ensure AdSense meta + head script on Excavationpro HTML pages (ca-pub-0646320966060599)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

PUB = "ca-pub-0646320966060599"
MARKER = f"client={PUB}"
# Google site-setup snippet (meta form without self-close, per AdSense UI)
META = f'    <meta name="google-adsense-account" content="{PUB}">\n'
SCRIPT = (
    f'    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={PUB}"\n'
    '         crossorigin="anonymous"></script>\n'
)
BLOCK = META + SCRIPT

ROOT = Path(__file__).resolve().parents[2] / "Excavationpro"
SKIP_DIRS = {"aichat", "haven_star_chart", "Hytale", "LYRA"}


HEAD_SCRIPT = re.compile(
    r"<script[^>]+googlesyndication\.com/pagead/js/adsbygoogle",
    re.I,
)


def has_head_script(text: str) -> bool:
    head_end = text.lower().find("</head>")
    chunk = text[: head_end if head_end > 0 else 4000]
    return bool(HEAD_SCRIPT.search(chunk))


def has_head_meta(text: str) -> bool:
    head_end = text.lower().find("</head>")
    chunk = text[: head_end if head_end > 0 else 4000]
    return bool(re.search(r'<meta\s+name="google-adsense-account"', chunk, re.I))


def inject(text: str) -> str:
    if has_head_meta(text) and has_head_script(text):
        return text
    if has_head_script(text) and not has_head_meta(text):
        m = re.search(r"(<head[^>]*>\s*)", text, re.I)
        if m:
            return text[: m.end()] + META + text[m.end() :]
    if has_head_script(text):
        return text
    if f'content="{PUB}"' in text or "google-adsense-account" in text:
        # meta present — insert script after adsense meta line
        pat = re.compile(
            r'(<meta\s+name="google-adsense-account"[^>]*>\s*)',
            re.I,
        )
        if pat.search(text):
            return pat.sub(r"\1" + SCRIPT, text, count=1)
    # After charset/viewport block in <head>
    m = re.search(r"(<head[^>]*>\s*)", text, re.I)
    if not m:
        return text
    insert_at = m.end()
    # Prefer after viewport meta if present
    vm = re.search(r"<meta[^>]+viewport[^>]*>\s*", text[insert_at : insert_at + 800], re.I)
    if vm:
        insert_at += vm.end()
    return text[:insert_at] + "\n" + BLOCK + text[insert_at:]


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT
    if not root.is_dir():
        print(f"MISSING {root}", file=sys.stderr)
        return 2
    changed = []
    for html in root.rglob("*.html"):
        if any(p in SKIP_DIRS for p in html.relative_to(root).parts):
            continue
        raw = html.read_text(encoding="utf-8", errors="replace")
        new = inject(raw)
        if new != raw:
            html.write_text(new, encoding="utf-8")
            changed.append(str(html.relative_to(root)))
    print(f"updated {len(changed)} files")
    for c in changed[:40]:
        print(" ", c)
    if len(changed) > 40:
        print(f"  ... +{len(changed) - 40} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())