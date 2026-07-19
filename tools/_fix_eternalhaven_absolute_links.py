#!/usr/bin/env python3
"""Rewrite eternalhaven.ca hub relative links to absolute live URLs.

The hub HTML was copied from Excavationpro/eternalhaven.html and still uses
relative paths that 404 on the thin eternalhaven.ca domain root.
"""
from __future__ import annotations

import re
from pathlib import Path

EX = "https://deepseekoracle.github.io/Excavationpro"
STACK = "https://deepseekoracle.github.io/lygo-protocol-stack"
MUSIC_PORTAL = "https://asiancoastline.com/"  # live free listen hub
LISTEN = f"{EX}/excavationpro-listen.html"
CATALOG = f"{EX}/excavationpro-music-catalog.html"
SOVEREIGN = f"{EX}/excavationpro-sovereign-music-hub.html"

# Order matters: longer prefixes first
REPLACEMENTS: list[tuple[str, str]] = [
    # Music (primary user-facing)
    ("excavationpro-listen.html", LISTEN),
    ("excavationpro-music-catalog.html", CATALOG),
    ("excavationpro-sovereign-music-hub.html", SOVEREIGN),
    ("data/excavationpro_music_ledger.json", f"{EX}/data/excavationpro_music_ledger.json"),
    ("Musicplayer", f"{EX}/Musicplayer"),
    # Network / lattice under Excavationpro
    ("LYGO-Network/", f"{EX}/LYGO-Network/"),
    ("LYGORESONANCE.html", f"{EX}/LYGORESONANCE.html"),
    ("lygorepo.html", f"{EX}/lygorepo.html"),
    ("EthicalChipFirmware.html", f"{EX}/EthicalChipFirmware.html"),
    ("LYRABOOT.html", f"{EX}/LYRABOOT.html"),
    ("aichat/", f"{EX}/aichat/"),
    ("downloads/", f"{EX}/downloads/"),
    # Stack interactive pages (served from protocol-stack Pages, not eternalhaven root)
    ("HavenStarChart.html", f"{STACK}/HavenStarChart.html"),
    ("SovereignLatticeMesh.html", f"{STACK}/SovereignLatticeMesh.html"),
    ("BiometricEntropyHarness.html", f"{STACK}/BiometricEntropyHarness.html"),
]

# Exact href rewrites (attribute-aware)
EXACT_HREF = {
    "index.html": MUSIC_PORTAL,  # "Music Hub" / index hub → real music portal
    "./index.html": MUSIC_PORTAL,
}


def fix_html(text: str) -> str:
    # Music Hub gold button and similar index self-links that mean "music portal"
    text = re.sub(
        r'(href=")index\.html(")',
        rf'\1{MUSIC_PORTAL}\2',
        text,
    )
    # Hash fragments after catalog etc. already covered by prefix replace if we do carefully
    for old, new in REPLACEMENTS:
        # href="old... or href='old...
        text = text.replace(f'href="{old}', f'href="{new}')
        text = text.replace(f"href='{old}", f"href='{new}")
        # bare in other attrs
        text = text.replace(f'"{old}#', f'"{new}#')
        text = text.replace(f"'{old}#", f"'{new}#")
    # Fix double-prefix if any accidental double EX
    text = text.replace(f"{EX}/{EX}/", f"{EX}/")
    text = text.replace(f"{STACK}/{STACK}/", f"{STACK}/")
    # Nav: Listen Free / Catalog already fixed via excavationpro-*.html

    # Explicit music hub CTA that pointed at index
    text = text.replace(
        f'href="{MUSIC_PORTAL}" class="btn btn-large btn-gold"><i class="fas fa-music"></i> Music Hub</a>',
        f'href="{MUSIC_PORTAL}" class="btn btn-large btn-gold" target="_blank" rel="noopener"><i class="fas fa-music"></i> Music Portal</a>',
    )
    # Nav labels clarity
    text = text.replace(
        f'href="{LISTEN}"><i class="fas fa-play"></i> Listen Free</a>',
        f'href="{MUSIC_PORTAL}" target="_blank" rel="noopener"><i class="fas fa-play"></i> Music Portal</a>',
    )
    # Also if still old listen path after replace
    text = text.replace(
        f'href="{LISTEN}"><i class="fas fa-play"></i> Listen Free</a>',
        f'href="{MUSIC_PORTAL}" target="_blank" rel="noopener"><i class="fas fa-play"></i> Music Portal</a>',
    )
    # Catalog ledger nav open new tab
    text = re.sub(
        rf'href="{re.escape(CATALOG)}"',
        f'href="{CATALOG}" target="_blank" rel="noopener"',
        text,
    )
    # Avoid double target attributes
    text = re.sub(r'target="_blank" rel="noopener" target="_blank" rel="noopener"', 'target="_blank" rel="noopener"', text)
    return text


def main() -> None:
    paths = [
        Path(r"I:\E Drive\lygo-protocol-stack\docs\domain-roots\eternalhaven.ca\index.html"),
        Path(r"I:\E Drive\lygo-protocol-stack\docs\domain-roots\eternalhaven.ca\404.html"),
    ]
    for p in paths:
        if not p.is_file():
            print("skip missing", p)
            continue
        raw = p.read_text(encoding="utf-8")
        fixed = fix_html(raw)
        if fixed == raw:
            print("no changes", p)
        else:
            p.write_text(fixed, encoding="utf-8")
            print("fixed", p, "delta chars", len(fixed) - len(raw))
        # sanity: no relative excavationpro-music-catalog left
        leftover = re.findall(
            r'href="(?!https?://|#|mailto:)([^"]+\.html[^"]*)"',
            fixed,
        )
        bad = [h for h in leftover if not h.startswith("privacy") and "http" not in h]
        # privacy.html is ok relative
        bad = [h for h in leftover if h not in ("privacy.html",) and not h.startswith("#")]
        print(" remaining relative html hrefs:", bad[:40], "count", len(bad))


if __name__ == "__main__":
    main()
