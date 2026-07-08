"""Extract byte-exact identifiers that must stay as plain text alongside images."""

from __future__ import annotations

import re

HEX_HASH = re.compile(r"\b[0-9a-fA-F]{32,64}\b")
API_KEYISH = re.compile(r"\b(sk-[A-Za-z0-9]{20,}|xai-[A-Za-z0-9]{20,})\b")
LONG_ID = re.compile(r"\b[A-Za-z0-9_\-]{24,}\b")


def extract_exact_identifiers(text: str) -> list[str]:
    found: set[str] = set()
    for pat in (HEX_HASH, API_KEYISH, LONG_ID):
        for m in pat.finditer(text):
            found.add(m.group(0))
    return sorted(found, key=len, reverse=True)[:64]