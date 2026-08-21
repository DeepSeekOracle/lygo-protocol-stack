#!/usr/bin/env python3
"""Render Emotional RAM whitepaper to shareable HTML."""
from __future__ import annotations

import hashlib
import html
import re
from pathlib import Path

STACK = Path(__file__).resolve().parents[2]
MD = STACK / "docs" / "whitepapers" / "LYGO_EMOTIONAL_RAM_v1.md"
OUT = STACK / "docs" / "whitepapers" / "LYGO_EMOTIONAL_RAM_v1.html"


def md_to_html(md: str) -> str:
    parts = md.split("```")
    chunks: list[str] = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            code = part.split("\n", 1)[1] if "\n" in part else part
            chunks.append(f"<pre><code>{html.escape(code.rstrip())}\n</code></pre>")
            continue
        esc = html.escape(part)

        def h2(m: re.Match[str]) -> str:
            t = m.group(1)
            slug = re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
            return f'<h2 id="{slug}">{t}</h2>'

        esc = re.sub(r"^# (.*?)$", r"<h1>\1</h1>", esc, flags=re.M)
        esc = re.sub(r"^## (.*?)$", h2, esc, flags=re.M)
        esc = re.sub(r"^### (.*?)$", r"<h3>\1</h3>", esc, flags=re.M)
        esc = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", esc)
        esc = re.sub(r"`([^`]+)`", r"<code>\1</code>", esc)
        for b in re.split(r"\n\n+", esc):
            b = b.strip()
            if not b:
                continue
            if b.startswith("<h"):
                chunks.append(b)
            elif b.startswith("|"):
                chunks.append(
                    "<div class='table'>"
                    + "".join(f"<div class='tr'>{html.escape(line) if False else line}</div>" for line in b.splitlines())
                    + "</div>"
                )
            else:
                chunks.append(f"<p>{b.replace(chr(10), '<br/>')}</p>")
    return "\n".join(chunks)


def main() -> int:
    md = MD.read_text(encoding="utf-8")
    sha = hashlib.sha256(md.encode("utf-8")).hexdigest()
    page = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>LYGO Emotional RAM v1</title>
<meta name="description" content="LYGO Emotional RAM — light math for affective/ethical indexing. Humans, animals, swarms, cyborgs."/>
<meta name="twitter:card" content="summary_large_image"/>
<meta name="twitter:site" content="@Excavationpro"/>
<meta property="og:title" content="LYGO Emotional RAM v1"/>
<link rel="canonical" href="https://deepseekoracle.github.io/lygo-protocol-stack/whitepapers/LYGO_EMOTIONAL_RAM_v1.html"/>
<style>
body{{margin:0;font-family:system-ui,Segoe UI,sans-serif;background:#070b12;color:#e8eef8;line-height:1.55}}
.wrap{{max-width:920px;margin:0 auto;padding:2rem 1.25rem 4rem}}
.brand{{color:#ff8fab;letter-spacing:.08em;font-size:.85rem;text-transform:uppercase}}
h2{{border-bottom:1px solid #243247;padding-bottom:.35rem;margin-top:2rem}}
a{{color:#6ee7ff}} .panel{{background:#101826;border:1px solid #243247;border-radius:14px;padding:1rem;margin:1rem 0}}
pre{{background:#060910;border:1px solid #243247;border-radius:10px;padding:1rem;overflow:auto}}
.tr{{font-family:Consolas,monospace;font-size:.82rem;color:#c5d4e8;white-space:pre-wrap}}
.muted{{color:#9aadc4}} .ok{{color:#7dffa0}}
</style></head><body><div class="wrap">
<p class="brand">Δ9Φ963 · Emotional RAM Whitepaper v1</p>
<div class="panel"><strong class="ok">Shareable</strong>
<p class="muted">SHA-256: <code>{sha}</code></p>
<p><a href="LYGO_EMOTIONAL_RAM_v1.md">Markdown</a> ·
<a href="https://clawhub.ai/deepseekoracle/lygo-emotional-ram">ClawHub skill</a> ·
<a href="../index.html">Docs hub</a></p></div>
<article>{md_to_html(md)}</article>
<footer class="muted">Δ9Φ963 — index meaning · damp with grace · humans publish</footer>
</div></body></html>"""
    OUT.write_text(page, encoding="utf-8")
    print({"ok": True, "sha256": sha, "html": str(OUT)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
