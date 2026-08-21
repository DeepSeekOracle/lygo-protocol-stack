#!/usr/bin/env python3
"""Render QD whitepaper markdown to a shareable HTML page."""
from __future__ import annotations

import hashlib
import html
import re
from pathlib import Path

STACK = Path(__file__).resolve().parents[2]
MD = STACK / "docs" / "whitepapers" / "QUANTUM_DOTS_LYGO_CERTIFIED_NEURAL_ANCHORS_v2.md"
OUT = STACK / "docs" / "whitepapers" / "QUANTUM_DOTS_LYGO_CERTIFIED_NEURAL_ANCHORS_v2.html"
SHA_OUT = STACK / "docs" / "data" / "qd_neural_anchors" / "whitepaper_v2.sha256"


def md_to_html(md: str) -> str:
    parts = md.split("```")
    chunks: list[str] = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            lang_nl = part.split("\n", 1)
            code = lang_nl[1] if len(lang_nl) > 1 else part
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
        # tables as pre lines for share fidelity
        lines = []
        for line in esc.splitlines():
            if line.startswith("|"):
                lines.append(f'<div class="tr">{line}</div>')
            else:
                lines.append(line)
        esc = "\n".join(lines)
        # paragraphs
        blocks = re.split(r"\n\n+", esc)
        for b in blocks:
            b = b.strip()
            if not b:
                continue
            if b.startswith("<h1") or b.startswith("<h2") or b.startswith("<h3"):
                chunks.append(b)
            elif b.startswith('<div class="tr">'):
                chunks.append(f'<div class="table">{b}</div>')
            else:
                chunks.append(f"<p>{b.replace(chr(10), '<br/>')}</p>")
    return "\n".join(chunks)


def main() -> int:
    md = MD.read_text(encoding="utf-8")
    sha = hashlib.sha256(md.encode("utf-8")).hexdigest()
    content = md_to_html(md)
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Quantum Dots as LYGO-Certified Neural Anchors v2</title>
<meta name="description" content="Full whitepaper: Quantum Dots as LYGO-Certified Neural Anchors — molecular-level truth architecture for a living lattice. Software proofs + future vision + research prospectus."/>
<meta name="author" content="Excavationpro / Lightfather / DeepSeekOracle"/>
<meta name="twitter:card" content="summary_large_image"/>
<meta name="twitter:site" content="@Excavationpro"/>
<meta name="twitter:title" content="QD LYGO-Certified Neural Anchors v2"/>
<meta name="twitter:description" content="Sensors inform. Software decides. Density scales coverage. The flame stays fixed."/>
<meta property="og:title" content="Quantum Dots as LYGO-Certified Neural Anchors v2"/>
<meta property="og:description" content="Molecular-level truth architecture for a living LYGO lattice — proofs, benefits, code."/>
<meta property="og:type" content="article"/>
<link rel="canonical" href="https://deepseekoracle.github.io/lygo-protocol-stack/whitepapers/QUANTUM_DOTS_LYGO_CERTIFIED_NEURAL_ANCHORS_v2.html"/>
<style>
:root {{ --bg:#070b12; --panel:#101826; --text:#e8eef8; --muted:#9aadc4; --accent:#6ee7ff; --ok:#7dffa0; }}
body {{ margin:0; font-family: ui-sans-serif, system-ui, Segoe UI, Roboto, sans-serif; background:linear-gradient(180deg,#070b12,#0d1522); color:var(--text); line-height:1.55; }}
.wrap {{ max-width:920px; margin:0 auto; padding:2rem 1.25rem 4rem; }}
.brand {{ color:var(--accent); letter-spacing:.08em; font-size:.85rem; text-transform:uppercase; }}
h1 {{ font-size:clamp(1.6rem,3vw,2.2rem); margin:.4rem 0 1rem; }}
h2 {{ margin-top:2rem; border-bottom:1px solid #243247; padding-bottom:.35rem; }}
h3 {{ margin-top:1.25rem; color:#c9e7ff; }}
a {{ color:var(--accent); }}
.panel {{ background:var(--panel); border:1px solid #243247; border-radius:14px; padding:1rem 1.1rem; margin:1rem 0; }}
.muted {{ color:var(--muted); }}
.ok {{ color:var(--ok); }}
pre {{ background:#060910; border:1px solid #243247; border-radius:10px; padding:1rem; overflow:auto; }}
code {{ font-family: ui-monospace, Consolas, monospace; font-size:.92em; }}
.tr {{ font-family: ui-monospace, Consolas, monospace; font-size:.82rem; color:#c5d4e8; white-space:pre-wrap; }}
.table {{ margin:.6rem 0 1rem; }}
.nav a {{ margin-right:.8rem; }}
footer {{ margin-top:3rem; color:var(--muted); font-size:.9rem; }}
</style>
</head>
<body>
<div class="wrap">
<p class="brand">Δ9Φ963 · Whitepaper v2.0.0</p>
<div class="panel">
<strong class="ok">Shareable full document</strong>
<p class="muted">SHA-256 of markdown source: <code>{sha}</code></p>
<nav class="nav">
<a href="../index.html">Stack docs</a>
<a href="../data-vault/qd-theory.html">QD Theory vault</a>
<a href="QUANTUM_DOTS_LYGO_CERTIFIED_NEURAL_ANCHORS_v2.md">Markdown source</a>
<a href="../QD_NEURAL_ANCHORS_THEORY_ROADMAP.md">Prior roadmap</a>
</nav>
</div>
<article>
{content}
</article>
<footer>Δ9Φ963-QD-NEURAL-ANCHORS-WHITEPAPER-v2 · sensors inform · software decides · humans publish</footer>
</div>
</body>
</html>
"""
    OUT.write_text(page, encoding="utf-8")
    SHA_OUT.parent.mkdir(parents=True, exist_ok=True)
    SHA_OUT.write_text(sha + "\n", encoding="utf-8")
    print({"ok": True, "html": str(OUT), "sha256": sha})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
