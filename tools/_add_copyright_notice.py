#!/usr/bin/env python3
"""Insert/update copyright + own-work disclaimer on listen portal."""
from __future__ import annotations

import re
from pathlib import Path

NOTICE = """
<footer class="wrap copyright-notice" id="copyright-notice" style="margin-top:28px;padding:18px 16px 100px;border-top:1px solid rgba(212,175,55,.25);font-size:.78rem;color:var(--muted);line-height:1.55;max-width:900px">
  <strong style="color:var(--gold)">© Copyright &amp; ownership notice</strong><br>
  All music, vocals, instrumentals, mixes, and related audio on this portal are presented as original works created by
  <strong style="color:var(--text)">Justin Helmer / Excavationpro / Lightfather</strong>, built over years of continuous production
  (including approximately five years of solid full-time creation).
  This sovereign vault is intended to preserve <em>my</em> catalog only — masters hashed from my own project trees
  (DONE ALBUM, Actors, Music 2024, Kick Stream production folders, BeatStars deliveries of my work,
  Haven / Eternal Haven book narration I produced, and related album folders).
  <br><br>
  <strong style="color:var(--gold)">Disclaimer</strong><br>
  To the best of my knowledge, everything published here is my own creation or work I am authorized to stream.
  Third-party / copyrighted libraries (for example device dumps, iPod/iTunes purchase libraries, and game soundtracks)
  are <strong>explicitly excluded</strong> by automated scan filters and vault policy.
  If any non-owned material is ever discovered, it will be removed as soon as filters or a report catch it.
  Takedown / correction: contact the steward via lattice channels or
  <a href="https://www.paypal.com/paypalme/ExcavationPro" style="color:var(--cyan)">PayPal.me/ExcavationPro</a>.
  Streams are for free listening and discovery; commercial rights remain with the steward unless separately licensed.
  <br><br>
  <span style="opacity:.85">Δ9Φ963 · Sovereign Music Vault · Own-work policy · Excavationpro · No iPod/third-party libraries</span>
</footer>
"""

PATHS = [
    Path(r"I:\E Drive\Excavationpro\excavationpro-listen.html"),
    Path(r"I:\E Drive\lygo-protocol-stack\docs\excavationpro-listen.html"),
]


def apply(path: Path) -> None:
    t = path.read_text(encoding="utf-8")
    block = NOTICE.strip()
    if 'id="copyright-notice"' in t:
        t2, n = re.subn(
            r'<footer class="wrap copyright-notice"[\s\S]*?</footer>',
            block,
            t,
            count=1,
        )
        if n:
            path.write_text(t2, encoding="utf-8")
            print(f"[ok] replaced {path}")
            return
    if '<div class="dock">' in t:
        t = t.replace('<div class="dock">', block + "\n\n<div class=\"dock\">", 1)
    else:
        t = t.replace("</body>", block + "\n</body>", 1)
    path.write_text(t, encoding="utf-8")
    print(f"[ok] inserted {path}")


def main() -> int:
    for p in PATHS:
        if p.exists():
            apply(p)
        else:
            print(f"[miss] {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
