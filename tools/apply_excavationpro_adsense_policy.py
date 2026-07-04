#!/usr/bin/env python3
"""AdSense policy hardening: allowlist monetization, strip risky pages, noindex dev tools."""

from __future__ import annotations

import re
import sys
from pathlib import Path

PUB = "ca-pub-0646320966060599"
ROOT = Path(__file__).resolve().parents[2] / "Excavationpro"
SKIP_DIRS = {"aichat", "haven_star_chart", "Hytale", "LYRA"}

# Pages that may show ad units (consent-gated on eternalhaven).
MONETIZE = {
    "eternalhaven.html",
}

# Full AdSense site readiness: verification meta + head loader; keep in-page slots.
ADSENSE_READY = {
    "LYGOBPMFinder.html",
}

# Substantive public pages: site-verification meta only (no adsbygoogle.js, no <ins>).
META_ONLY = {
    "eternalhaven.html",
    "index.html",
    "main.html",
    "Expromain.html",
    "Ethics.html",
    "EthicalChipFirmware.html",
    "BiometricEntropyHarness.html",
    "HavenStarChart.html",
    "Musicplayer.html",
    "memorymaker.html",
    "sealmaker.html",
    "SovereignLatticeMesh.html",
    "LYGORESONANCE.html",
    "lygorhaven.html",
    "PAGE4ADVANCED.html",
    "lygo-nano-kernel.html",
    "LYGONanoKernelP04.html",
    "lygolink.html",
    "lygorepo.html",
    "LYGO-Network/LYGOGUARDIAN.html",
    "LYGO-Network/Ethical-Chip-FirmwareV2.html",
    "LYGO-Network/Ethical-Chip-Firmware.html",
    "LYGO-Network/champions.html",
    "LYGO-Network/FIRMWARE.html",
    "LYGO-Network/FIRMWAREV2.html",
    "LYGO-Network/LYGO-Portal.html",
    "LYGO-Network/LYGO-Quantum-Matrix.html",
    "LYGO-Network/lygolink.html",
    "LYGO-Network/SUMMARYP1.html",
    "LYGO-Network/SUMMARYP2.html",
    "LYGO-Network/SUMMARYP3.html",
    "LYGO-Network/SAMPARCHITECTURE.html",
    "LYGO-Network/legacy-guardian-music.html",
    "LYGO-Network/QUANTUMCOUNCILTERMINAL.html",
    "LYGO-Network/OMNIΣIREN.html",
    "LYGO-Network/OMNIΣIRENSTORM.html",
    "LYGO-Network/LYGOINTERFAITHDECODER.html",
    "LYGO-Network/pokerneldocs.html",
}

# Never monetize or verify — remove all AdSense; add noindex.
DENY = {
    "grokbanish.html",
    "grok.html",
    "grokburn.html",
    "grokdone.html",
    "grokflamed.html",
    "lygorepotest.html",
    "lygorepoadd.html",
    "LYGO-Network/test.html",
    "LYGO-Network/underconstruction.html",
    "LYGO-Network/admin.html",
    "LYGO-Network/LYGOOS.html",
    "LYGO-Network/lygorepoadd.html",
    "LYGO-Network/bankr.html",
    "LYGO-Network/pokernel.html",
    "LYGO-Network/pokernelv2.html",
    "LYGO-Network/lygopov2.html",
    "LYGO-Network/updatefeed.html",
    "ADSENSE_HEAD_SNIPPET.html",
    "LYGO-Network/ETERNALHAVEN.html",
}

META_LINE = f'<meta name="google-adsense-account" content="{PUB}">'
HEAD_ADSENSE_SCRIPT = (
    f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={PUB}"\n'
    f'     crossorigin="anonymous"></script>'
)
RE_HEAD_ADSENSE = re.compile(
    r"<script[^>]*googlesyndication\.com/pagead/js/adsbygoogle[^>]*>",
    re.I,
)

RE_META = re.compile(
    r"\s*<meta\s+name=[\"']google-adsense-account[\"'][^>]*>\s*",
    re.I,
)
RE_SCRIPT = re.compile(
    r"\s*<script[^>]*googlesyndication\.com/pagead/js/adsbygoogle[^>]*>.*?</script>\s*"
    r"|\s*<script[^>]*googlesyndication\.com/pagead/js/adsbygoogle[^>]*/>\s*",
    re.I | re.S,
)
RE_INS_BLOCK = re.compile(
    r"<div[^>]*ad-container[^>]*>.*?</div>\s*",
    re.I | re.S,
)
RE_AD_REGION = re.compile(
    r'<div\s+class="ad-region"[^>]*>.*?</div>\s*',
    re.I | re.S,
)
RE_INS = re.compile(
    r"<ins\s+class=[\"']adsbygoogle[\"'][^>]*>.*?</ins>\s*",
    re.I | re.S,
)
RE_PUSH = re.compile(
    r"<script>\s*\(adsbygoogle\s*=\s*window\.adsbygoogle.*?</script>\s*",
    re.I | re.S,
)
RE_ROBOTS_NOINDEX = re.compile(
    r'<meta\s+name=["\']robots["\'][^>]*noindex',
    re.I,
)


def rel_path(html: Path, root: Path) -> str:
    return str(html.relative_to(root)).replace("\\", "/")


def strip_adsense_markup(text: str) -> str:
    text = RE_SCRIPT.sub("\n", text)
    text = RE_META.sub("\n", text)
    text = RE_AD_REGION.sub("", text)
    text = RE_INS_BLOCK.sub("", text)
    text = RE_INS.sub("", text)
    text = RE_PUSH.sub("", text)
    return text


def ensure_meta_in_head(text: str) -> str:
    if RE_META.search(text):
        return text
    m = re.search(r"(<head[^>]*>\s*)", text, re.I)
    if not m:
        return text
    insert = m.end()
    vm = re.search(
        r"<meta[^>]+viewport[^>]*>\s*",
        text[insert : insert + 1200],
        re.I,
    )
    if vm:
        insert += vm.end()
    line = f"\n    {META_LINE}\n"
    return text[:insert] + line + text[insert:]


def ensure_head_adsense_script(text: str) -> str:
    if RE_HEAD_ADSENSE.search(text):
        return text
    if RE_META.search(text):
        return RE_META.sub(
            lambda m: m.group(0) + f"\n{HEAD_ADSENSE_SCRIPT}\n",
            text,
            count=1,
        )
    return ensure_meta_in_head(text).replace(
        META_LINE,
        f"{META_LINE}\n{HEAD_ADSENSE_SCRIPT}",
        1,
    )


def ensure_noindex(text: str) -> str:
    if RE_ROBOTS_NOINDEX.search(text):
        return text
    m = re.search(r"(<head[^>]*>\s*)", text, re.I)
    if not m:
        return text
    tag = '    <meta name="robots" content="noindex, nofollow" />\n'
    return text[: m.end()] + tag + text[m.end() :]


def process_file(html: Path, root: Path) -> bool:
    rel = rel_path(html, root)
    raw = html.read_text(encoding="utf-8", errors="replace")
    new = raw

    if rel in DENY:
        new = strip_adsense_markup(new)
        new = ensure_noindex(new)
    elif rel in ADSENSE_READY:
        new = ensure_meta_in_head(new)
        new = ensure_head_adsense_script(new)
    elif rel in MONETIZE:
        # Keep in-page ad slots; remove global head script (consent-gated load in page JS).
        new = RE_SCRIPT.sub("\n", new)
        new = ensure_meta_in_head(new)
    elif rel in META_ONLY:
        new = strip_adsense_markup(new)
        new = ensure_meta_in_head(new)
    else:
        new = strip_adsense_markup(new)

    if new != raw:
        html.write_text(new, encoding="utf-8")
        return True
    return False


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT
    changed: list[str] = []
    for html in sorted(root.rglob("*.html")):
        if any(p in SKIP_DIRS for p in html.relative_to(root).parts):
            continue
        if process_file(html, root):
            changed.append(rel_path(html, root))
    print(f"policy_applied: {len(changed)} files")
    for c in changed:
        print(f"  {c}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())