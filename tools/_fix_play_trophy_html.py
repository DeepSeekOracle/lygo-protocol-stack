#!/usr/bin/env python3
from pathlib import Path
import re

LISTEN = Path(r"I:\E Drive\Excavationpro\excavationpro-listen.html")
DOCS = Path(r"I:\E Drive\lygo-protocol-stack\docs\excavationpro-listen.html")
html = LISTEN.read_text(encoding="utf-8")

CSS = r"""
/* ===== PLAY COUNTS / TROPHY ===== */
.play-trophy {
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
  margin: 0 0 8px; padding: 10px 14px; border-radius: 12px;
  border: 1px solid rgba(212,175,55,.55);
  background: linear-gradient(135deg, rgba(212,175,55,.18), rgba(176,107,255,.12), rgba(0,240,255,.08));
  box-shadow: 0 0 24px rgba(212,175,55,.2);
}
.play-trophy .cup { font-size: 1.75rem; line-height: 1; filter: drop-shadow(0 0 8px rgba(212,175,55,.5)); }
.play-trophy .nums { flex: 1; min-width: 140px; }
.play-trophy .nums .big {
  font-family: Cinzel, serif; font-size: clamp(1.4rem, 3vw, 1.85rem);
  font-weight: 700; color: var(--gold); letter-spacing: .02em;
  font-variant-numeric: tabular-nums;
}
.play-trophy .nums .sub { font-size: .72rem; color: var(--muted); margin-top: 2px; }
.play-trophy .live-dot {
  width: 8px; height: 8px; border-radius: 50%; background: var(--ok);
  box-shadow: 0 0 8px var(--ok); animation: pulseDot 1.6s ease infinite;
}
@keyframes pulseDot { 0%,100%{opacity:1} 50%{opacity:.35} }
.row .plays {
  font-size: .68rem; color: var(--muted); font-variant-numeric: tabular-nums;
  white-space: nowrap; min-width: 3.2rem; text-align: right;
}
.row .plays b { color: var(--cyan); font-weight: 700; }
.row .plays.hot b { color: var(--gold); }
.now .plays-inline { color: var(--gold); font-size: .78rem; margin-left: 6px; }
"""

TROPHY = """
<div class="play-trophy" id="play-trophy" title="Global play tally — increments when listeners actually play tracks (20s or 35% of song)">
  <span class="cup" aria-hidden="true">🏆</span>
  <div class="nums">
    <div class="big" id="trophy-total">▶ plays</div>
    <div class="sub">Total plays · sovereign stream trophy · live across listeners</div>
  </div>
  <span class="live-dot" title="Live counter"></span>
</div>
"""

if "PLAY COUNTS / TROPHY" not in html:
    html = html.replace("</style>", CSS + "\n</style>", 1)
else:
    html = re.sub(
        r"/\* ===== PLAY COUNTS / TROPHY ===== \*/[\s\S]*?(?=\n/\* =====|\n</style>)",
        CSS.strip() + "\n",
        html,
        count=1,
    )

if 'id="play-trophy"' not in html:
    if '<div class="tools">' in html:
        html = html.replace('<div class="tools">', '<div class="tools">\n' + TROPHY + "\n", 1)
    elif 'id="sticky-top"' in html:
        html = html.replace(
            '<div class="sticky-top" id="sticky-top">',
            '<div class="sticky-top" id="sticky-top">\n' + TROPHY + "\n",
            1,
        )
    else:
        html = html.replace("<body>", "<body>\n" + TROPHY + "\n", 1)

LISTEN.write_text(html, encoding="utf-8")
DOCS.write_text(html, encoding="utf-8")
print("play-trophy id", 'id="play-trophy"' in html)
print("css", ".play-trophy {" in html)
print("js", "hits.dwyl.com" in html and "lygo_listen_play_ledger_v1" in html)
print("copyright", "copyright-notice" in html)
