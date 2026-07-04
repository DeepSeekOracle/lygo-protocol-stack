#!/usr/bin/env python3
"""Build docs/LYGO_BPM_Finder.html from Biophase7 prototype + SEO meta."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(
    r"I:\E Drive\LYRA SYSTEM RETORE\FINAL RESTORE\ALL SEALS\220+\New folder"
    r"\2026Biophase7\Design a LYGO Online BPM finder and.txt"
)
MARKER = "That's a tighter, buildable idea than the original:"

STACK_CANONICAL = "https://deepseekoracle.github.io/lygo-protocol-stack/LYGO_BPM_Finder.html"
EXCA_CANONICAL = "https://deepseekoracle.github.io/Excavationpro/LYGOBPMFinder.html"
OG_IMAGE = (
    "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4"
    "?auto=format&fit=crop&w=1200&q=80"
)

TITLE = "LYGO BPM Finder — Free Online Tempo Detector | MP3, WAV, FLAC"
DESCRIPTION = (
    "Free online BPM finder and tempo detector. Upload MP3, WAV, or FLAC — detect beats "
    "in your browser with confidence score, tap tempo, ÷2/×2 fix, and waveform beat grid. "
    "Private: audio never leaves your device. By Excavationpro / LYGO."
)
KEYWORDS = (
    "BPM finder, tempo detector, online BPM analyzer, find BPM, song tempo, beat detector, "
    "MP3 BPM, WAV BPM, FLAC tempo, music production tool, tap tempo, Excavationpro, LYGO"
)


def seo_head(*, canonical: str, site_name: str) -> str:
    return f"""<title>{TITLE}</title>
<meta name="title" content="{TITLE}">
<meta name="description" content="{DESCRIPTION}">
<meta name="keywords" content="{KEYWORDS}">
<meta name="author" content="Justin Helmer / DeepSeekOracle / Excavationpro">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
<meta name="googlebot" content="index, follow">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{site_name}">
<meta property="og:url" content="{canonical}">
<meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{DESCRIPTION}">
<meta property="og:image" content="{OG_IMAGE}">
<meta property="og:image:alt" content="LYGO BPM Finder — online tempo detection for producers">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@Excavationpro">
<meta name="twitter:creator" content="@Excavationpro">
<meta name="twitter:title" content="{TITLE}">
<meta name="twitter:description" content="{DESCRIPTION}">
<meta name="twitter:image" content="{OG_IMAGE}">
<meta name="twitter:image:alt" content="LYGO BPM Finder — online tempo detection">
<script type="application/ld+json">{{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "LYGO BPM Finder",
  "url": "{canonical}",
  "applicationCategory": "MusicApplication",
  "operatingSystem": "Any (Web Browser)",
  "description": "{DESCRIPTION}",
  "offers": {{ "@type": "Offer", "price": "0", "priceCurrency": "USD" }},
  "featureList": "BPM detection, tap tempo, confidence score, waveform beat grid, private client-side processing",
  "browserRequirements": "Requires JavaScript and Web Audio API",
  "author": {{ "@type": "Organization", "name": "Excavationpro / LYGO Systems" }}
}}</script>
<meta name="google-adsense-account" content="ca-pub-0646320966060599">"""


def prototype_html() -> str:
    text = SRC.read_text(encoding="utf-8")
    if MARKER not in text:
        raise SystemExit(f"Marker not found in {SRC}")
    chunk = text.split(MARKER, 1)[1]
    start = chunk.index("<!DOCTYPE html>")
    html = chunk[start:]
    end = html.rindex("</html>") + len("</html>")
    return html[:end]


def brand(html: str) -> str:
    html = html.replace(
        '<p class="eyebrow">Tempo detection</p>',
        '<p class="eyebrow">LYGO · Biophase7 · Creative</p>',
        1,
    )
    html = html.replace("<h1>BPM Finder</h1>", "<h1>LYGO BPM Finder</h1>", 1)
    html = html.replace('<div class="rack">', '<main class="rack" id="bpm-finder-app">', 1)
    html = html.replace(
        "Nothing loaded yet.",
        "Nothing loaded yet. Audio stays on your device.",
        1,
    )
    html = html.replace(
        """    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
  }""",
        """    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 24px;
    gap: 16px;
  }""",
        1,
    )
    footer_css = """
  .site-footer {
    max-width: 560px;
    width: 100%;
    font-size: 12px;
    color: var(--muted);
    text-align: center;
    line-height: 1.5;
  }
  .site-footer a { color: var(--teal); text-decoration: none; }
  .site-footer a:hover { text-decoration: underline; }

"""
    html = html.replace(
        "  @media (prefers-reduced-motion: reduce)",
        footer_css + "  @media (prefers-reduced-motion: reduce)",
        1,
    )
    return html


def inject_seo(html: str, *, canonical: str, site_name: str) -> str:
    style_start = html.index("<style>")
    head_open = html.index("<head>")
    new_head = f"""<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{seo_head(canonical=canonical, site_name=site_name)}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Work+Sans:wght@400;500;600&display=swap" rel="stylesheet">
"""
    return html[:head_open] + new_head + html[style_start:]

def add_footer(html: str, footer: str) -> str:
    if "class=\"site-footer\"" in html:
        return html
    return html.replace(
        "</div>\n\n<script type=\"module\">",
        "</main>\n\n" + footer + "\n<script type=\"module\">",
        1,
    )


def main() -> int:
    base = brand(prototype_html())
    stack_footer = """
<p class="site-footer">
  <strong>Privacy:</strong> <a href="https://www.npmjs.com/package/bpm-detective" rel="noopener noreferrer" target="_blank">bpm-detective</a> runs locally — no server upload.
  · <a href="index.html">LYGO stack index</a>
  · <a href="https://deepseekoracle.github.io/Excavationpro/eternalhaven.html">Main hub</a>
  · <a href="BIOPHASE7_BPM_FINDER.md">Spec</a>
</p>"""
    exca_footer = """
<p class="site-footer">
  <strong>Privacy:</strong> <a href="https://www.npmjs.com/package/bpm-detective" rel="noopener noreferrer" target="_blank">bpm-detective</a> runs locally — no server upload.
  · <a href="eternalhaven.html">Eternal Haven hub</a>
  · <a href="LYGORESONANCE.html">LYGO Resonance</a>
  · <a href="https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/docs/BIOPHASE7_BPM_FINDER.md">Spec</a>
</p>"""

    stack = inject_seo(base, canonical=STACK_CANONICAL, site_name="LYGO Protocol Stack")
    stack = add_footer(stack, stack_footer)
    stack_path = ROOT / "docs" / "LYGO_BPM_Finder.html"
    stack_path.write_text(stack, encoding="utf-8")
    print("Wrote", stack_path)

    exca = inject_seo(base, canonical=EXCA_CANONICAL, site_name="Excavationpro / LYGO")
    exca = add_footer(exca, exca_footer)
    exca_path = ROOT.parent / "Excavationpro" / "LYGOBPMFinder.html"
    if exca_path.parent.is_dir():
        exca_path.write_text(exca, encoding="utf-8")
        print("Wrote", exca_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())