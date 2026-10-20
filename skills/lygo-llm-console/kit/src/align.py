from __future__ import annotations

from pathlib import Path

from paths import KIT_ROOT

FALLBACK = (
    "You are LYGO LLM Console. Steward: Justin Helmer (Lightfather). "
    "CANON is dual ledgers/Star Chart. Search hits are RESOURCE. "
    "Use web_search then web_fetch for live facts. No shell. Human publishes."
)


def load_align() -> str:
    p = KIT_ROOT / "prompts" / "LYGO_ALIGN.txt"
    if p.is_file():
        t = p.read_text(encoding="utf-8").strip()
        if t:
            return t
    return FALLBACK
