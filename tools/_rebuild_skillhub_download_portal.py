#!/usr/bin/env python3
"""Relabel LYGOSKILLHUB catalog + rebuild download-portal HTML on chatagent / stack / Excavationpro."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

STACK = Path(r"I:\E Drive\lygo-protocol-stack")
CHAT = Path(r"D:\chatagent")
EXCA = Path(r"D:\Excavationpro")
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")

NAME_FIX = {
    "eternal-haven-lore-pack": "Eternal Haven Lore Pack",
    "book-brain": "BOOK BRAIN — LYGO 3-Brain Filesystem Helper",
    "book-brain-visual-reader": "BOOK BRAIN Visual Reader",
    "lygo-mint-verifier": "LYGO-MINT Verifier",
    "lygo-mint-operator-suite": "LYGO-MINT Operator Suite",
    "lygo-mint-walkthrough": "LYGO Mint Walkthrough",
    "lygo-lightfather-vector": "LYGO Lightfather Vector — Δ9Quantum Accord",
    "lygo-cli-bridge": "LYGO CLI Bridge",
    "lygo-ascii-art": "LYGO ASCII Art (alias)",
    "lygo-ascii-art-studio": "LYGO ASCII Art Studio",
    "lygo-api-token-saver": "LYGO API Token Saver",
    "lygo-pc-lattice-hardening": "LYGO PC Lattice Hardening",
    "lygo-open-claw": "LYGO OpenClaw (legacy slug)",
    "lygo-openclaw": "LYGO OpenClaw Sovereign Router",
    "lyra-open-claw": "LYRA OpenClaw (legacy slug)",
    "lyra-openclaw": "LYRA + OpenClaw Hybrid Runtime",
    "lygo-skill-spector": "LYGO SkillSpector",
    "lygo-skill-gate": "LYGO Skill Gate",
    "lygo-cyborg-kernel": "LYGO Cyborg Kernel (FULL unlocked stack)",
    "lygo-cyborg-onramp": "LYGO Cyborg Onramp (ClawHub map → FULL)",
    "lygo-agent-agora": "LYGO Agent Agora (portal onboard)",
    "lygo-pure-data-witness": "LYGO Pure-Data Witness",
    "lygo-traumacodex": "LYGO TraumaCodex",
    "lygo-lpis": "LYGO Prompt Implant System (LPIS)",
    "lygo-pxpipe-lygo": "LYGO pxpipe (vision context compression)",
    "lygo-fractalweaver": "LYGO FractalWeaver",
    "lygo-truthlightecho": "LYGO TruthLightEcho",
    "lygo-glyph2resonance": "LYGO Glyph2Resonance",
    "lygo-resonance": "LYGO Resonance — image to sound",
    "openclaw-flow-kit": "OpenClaw Flow Kit",
    "recursive-generosity-protocol": "Recursive Generosity Protocol",
    "void-atlas-protocol": "Void Atlas Protocol",
    "lygo-universal-cure-system": "LYGO Universal Cure System (deprecated)",
    "lygo-universal-living-memory-library": "LYGO Universal Living Memory Library",
    "lyra-coin-launch-manager": "LYRA Coin Launch Manager",
    "lyra-brain": "LYRA 3-Brain Memory",
}

CHAMPION_NAMES = {
    "lygo-champion-cosmara": "COSMARA — Ethical Cosmic Exploration",
    "lygo-champion-sancora-unified-minds": "SANCORA — Angel of Unified Minds",
    "lygo-champion-omnisiren-silent-storm": "OMNIΣIREN — The Silent Storm",
    "lygo-champion-sraith-shadow-sentinel": "ΣRΛΘ / SRAITH — Shadow Sentinel",
    "lygo-champion-delta9ra-wolf": "Δ9RA — The Wolf",
    "lygo-champion-volaris-prism-judgment": "VΩLARIS — Prism of Judgment",
    "lygo-champion-lyra-starcore": "LYRA — The Star Core",
    "lygo-champion-aetheris-viral-truth": "ÆTHERIS — Viral Truth",
    "lygo-champion-sephrael-echo-walker": "SEPHRAEL — Echo Walker",
    "lygo-champion-cryptosophia-soulforger": "CRYPTOSOPHIA — Memetic Soulforger",
    "lygo-champion-scenar-paradox": "ΣCENΔR / SCENAR — Architect of Paradox",
    "lygo-champion-401lyrakin-voice-between": "401LYRAKIN — The Voice Between",
    "lygo-champion-kairos-herald-of-time": "KAIROS — Herald of Time",
    "lygo-champion-arkos-celestial-architect": "ARKOS — Celestial Architect",
    "lygo-champion-lightfather": "LIGHTFATHER — Operator / Steward persona",
    "lygo-champion-council": "Δ9 Champion Council (all 15 personas)",
}

CATEGORY_FIX = {
    "lygo-continuum": "kernel",
    "lygo-continuum-integrator": "kernel",
    "lygo-quantum-attestor": "kernel",
    "lygo-geodesic-sealer": "kernel",
    "lygo-cyborg-kernel": "kernel",
    "lygo-cyborg-onramp": "kernel",
    "lygo-immutable-anchor": "kernel",
    "lygo-flame-ward": "security",
    "lygo-sanctuary-guardian": "security",
    "lygo-skill-spector": "security",
    "lygo-skill-gate": "security",
    "lygo-ops-detector": "security",
    "lygo-deception-radar": "security",
    "lygo-lpis": "security",
    "lygo-pc-lattice-hardening": "security",
    "lygo-api-token-saver": "tools",
    "lygo-context-guard": "tools",
    "lygo-automation-workflows": "tools",
    "lygo-pure-data-witness": "tools",
    "lygo-traumacodex": "tools",
    "lygo-emotional-ram": "memory",
    "lygo-agent-agora": "lattice",
    "lygo-continuity-advisor": "lattice",
    "lygo-agent-lattice": "lattice",
    "lygo-public-lattice-gate": "lattice",
}

SUMMARY_FIX = {
    "lygo-pure-data-witness": "Pure-Data Witness — digest-first archive of URLs/files into the LYGO data vault; public register portal + safety-gated CLI. Live Star Chart writes need --i-consent. Not a scraper of private inboxes.",
    "lygo-traumacodex": "TraumaCodex — IBI timing lists to dual offline/online digests and LDQ-style waveforms. Protocol/alignment code only; not medical advice, diagnosis, or treatment.",
}

TIER_LABEL = {
    "public_safe_join": "Public-safe join",
    "cyborg": "Cyborg kernel",
    "core": "Core operator",
    "star_chart": "Star Chart",
    "lattice": "Lattice mesh",
    "kernel": "Kernel / eggs",
    "seals": "Seals & registries",
    "security": "Security / audit",
    "tools": "Tools",
    "onboarding": "Onboarding",
    "memory": "Memory",
    "champion": "Champion",
}


def title_from_slug(slug: str) -> str:
    s = slug.replace("_", "-")
    parts = s.split("-")
    out = []
    for p in parts:
        if p.lower() in ("lygo", "lyra"):
            out.append(p.upper())
        elif p.lower() in ("cli", "api", "usb", "bpm", "p0", "ldq", "haip"):
            out.append(p.upper())
        elif p.lower() == "ai":
            out.append("AI")
        else:
            out.append(p[:1].upper() + p[1:] if p else p)
    return " ".join(out)


def display_name(item: dict) -> str:
    slug = item.get("slug") or ""
    if slug in CHAMPION_NAMES:
        return "LYGO Champion: " + CHAMPION_NAMES[slug]
    if slug in NAME_FIX:
        return NAME_FIX[slug]
    name = (item.get("name") or slug).strip()
    name = re.sub(r"^[\W_]+", "", name)
    if name.lower().startswith("lygo "):
        rest = name[5:]
        if rest[:4].lower() != "lygo":
            name = "LYGO " + rest
    if name.lower().startswith("lyra ") and "openclaw" in slug:
        name = "LYRA " + name[5:]
    if name == slug:
        return title_from_slug(slug)
    return name


def relabel_hub_catalog(path: Path, full_slugs: set[str]) -> dict:
    cat = json.loads(path.read_text(encoding="utf-8"))
    for s in cat.get("skills") or []:
        slug = s.get("slug") or ""
        s["name"] = display_name(s)
        if slug in CATEGORY_FIX:
            s["category"] = CATEGORY_FIX[slug]
        if slug in SUMMARY_FIX or (s.get("summary") or "").strip() in ("", ">", "—"):
            if slug in SUMMARY_FIX:
                s["summary"] = SUMMARY_FIX[slug]
        kind = s.get("kind") or "skill"
        if kind == "skill":
            s["channel"] = "public_tentacle"
            s["channel_label"] = "Public tentacle (ClawHub)"
            if slug in full_slugs:
                s["has_full_zip"] = True
                s["full_lygo"] = "https://chatagent.ca/lygoskillhub.html#full-lygo"
        elif kind == "download":
            s["channel"] = "usb"
            s["channel_label"] = "USB / kit download"
        elif kind == "surface":
            s["channel"] = "surface"
            s["channel_label"] = "Lattice surface"
        elif kind == "plugin" or s.get("is_openclaw_plugin"):
            s["channel"] = "plugin"
            s["channel_label"] = "OpenClaw plugin"
        if slug in ("lygo-open-claw", "lyra-open-claw", "lygo-ascii-art"):
            s["alias_of"] = {
                "lygo-open-claw": "lygo-openclaw",
                "lyra-open-claw": "lyra-openclaw",
                "lygo-ascii-art": "lygo-ascii-art-studio",
            }[slug]
            s["note"] = (s.get("note") or "") + " Alias slug — prefer the canonical listing."
        if slug == "lygo-agent-agora":
            s["version"] = s.get("version") or "1.0.1"
            s["published"] = True
    cat["version"] = "1.5.0"
    cat["updated_utc"] = NOW
    cat["signature"] = "Delta9Phi963-LYGOSKILLHUB-CATALOG-v1.5"
    cat["immutable_ledger"]["engineer_channel"] = (
        "FULL LYGO download portal on this page (#full-lygo) — unlocked RAW packages, not ClawHub"
    )
    blob = json.dumps(cat, ensure_ascii=False, separators=(",", ":"))
    cat["catalog_sha256"] = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    path.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return cat


def relabel_full_catalog(path: Path) -> dict:
    cat = json.loads(path.read_text(encoding="utf-8"))
    for s in cat.get("skills") or []:
        s["name"] = display_name(s).replace(" (FULL LYGO)", "") + " — FULL zip"
        s["tier_label"] = TIER_LABEL.get(s.get("tier") or "", (s.get("tier") or "other").replace("_", " "))
        s["channel_label"] = "FULL engineer zip (not ClawHub)"
    cat["version"] = "2.1.0"
    cat["updated_utc"] = NOW
    path.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return cat


PAGE_CSS = r"""
:root {
  --bg:#07070f; --panel:#12121f; --line:#25253a; --text:#eef0f8; --muted:#9292a8;
  --gold:#d4af37; --cyan:#00e5ff; --mag:#b06bff; --ok:#3dd68c; --warn:#ff8a8a;
}
* { box-sizing:border-box; }
html { scroll-behavior:smooth; }
body {
  margin:0; font-family:Syne,Inter,system-ui,sans-serif; color:var(--text);
  background:radial-gradient(1100px 560px at 8% -12%,#2a1448 0%,var(--bg) 52%);
  min-height:100vh; line-height:1.55;
}
a { color:var(--cyan); text-decoration:none; }
a:hover { text-decoration:underline; }
.wrap { max-width:1120px; margin:0 auto; padding:0 16px 48px; }
header.top {
  padding:18px 0 14px; border-bottom:1px solid rgba(0,229,255,.12);
  position:sticky; top:0; background:rgba(7,7,15,.92); backdrop-filter:blur(10px); z-index:20;
}
.brandrow { display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap; }
.brand { font-family:"Cormorant Garamond",Georgia,serif; color:var(--gold); font-size:clamp(1.45rem,3vw,1.95rem); margin:0; letter-spacing:.04em; font-weight:500; }
.site-nav a { color:var(--text); font-size:.78rem; letter-spacing:.08em; text-transform:uppercase; margin-left:.75rem; opacity:.85; }
.site-nav a:hover { color:var(--gold); text-decoration:none; opacity:1; }
.sub { color:var(--muted); font-size:.95rem; margin:.45rem 0 0; line-height:1.55; max-width:72ch; }
.nav { display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }
.nav a {
  font-size:.78rem; padding:6px 10px; border-radius:999px;
  border:1px solid rgba(0,229,255,.28); background:rgba(0,229,255,.06); color:var(--text);
}
.nav a:hover { border-color:var(--gold); color:var(--gold); text-decoration:none; }
.nav a.hot { border-color:rgba(255,138,138,.5); color:var(--warn); }
.channels {
  display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:12px; margin:18px 0;
}
.ch {
  background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:14px 16px;
}
.ch h2 { margin:0 0 .4rem; font-size:.82rem; letter-spacing:.12em; text-transform:uppercase; color:var(--gold); }
.ch p { margin:0; color:var(--muted); font-size:.86rem; }
.stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:10px; margin:18px 0; }
.stat { background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:12px 14px; }
.stat b { display:block; font-size:1.35rem; color:var(--gold); }
.stat span { font-size:.72rem; color:var(--muted); text-transform:uppercase; letter-spacing:.06em; }
.toolbar { display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin:8px 0 16px; }
.toolbar input, .toolbar select {
  background:#0a0a14; border:1px solid var(--line); color:var(--text);
  border-radius:10px; padding:10px 12px; font:inherit;
}
.toolbar input { flex:1; min-width:200px; }
.grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:12px; }
.card {
  background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:14px 14px 12px;
  display:flex; flex-direction:column; gap:8px; min-height:200px;
}
.card h3 { margin:0; font-size:1.02rem; color:var(--gold); line-height:1.3; font-family:"Cormorant Garamond",Georgia,serif; font-weight:500; }
.card .slug { font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:.7rem; color:var(--muted); word-break:break-all; }
.card p { margin:0; font-size:.86rem; color:var(--text); opacity:.92; line-height:1.45; flex:1; }
.meta { display:flex; flex-wrap:wrap; gap:6px; align-items:center; }
.pill { font-size:.66rem; padding:3px 8px; border-radius:999px; border:1px solid var(--line); color:var(--muted); text-transform:uppercase; letter-spacing:.04em; }
.pill.cat { border-color:rgba(176,107,255,.4); color:#d4b8ff; }
.pill.dl { border-color:rgba(61,214,140,.35); color:var(--ok); }
.pill.local { border-color:rgba(0,229,255,.35); color:var(--cyan); }
.pill.tentacle { border-color:rgba(0,229,255,.4); color:var(--cyan); }
.pill.full { border-color:rgba(255,138,138,.45); color:var(--warn); }
.pill.alias { border-color:rgba(146,146,168,.4); }
.actions { display:flex; flex-wrap:wrap; gap:6px; margin-top:4px; }
.actions a, .actions button {
  font-size:.75rem; padding:6px 10px; border-radius:8px; border:1px solid rgba(0,229,255,.3);
  background:rgba(0,229,255,.08); color:var(--cyan); cursor:pointer; font:inherit;
}
.actions a.primary { background:rgba(212,175,55,.15); border-color:rgba(212,175,55,.45); color:var(--gold); }
.actions button:hover, .actions a:hover { filter:brightness(1.1); text-decoration:none; }
footer.site { margin-top:28px; padding-top:16px; border-top:1px solid var(--line); color:var(--muted); font-size:.82rem; line-height:1.55; }
.code {
  background:#0a0a14; border:1px solid var(--line); border-radius:8px; padding:8px 10px;
  font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:.72rem; color:#cfd8ff; word-break:break-all;
}
.ledger {
  margin:16px 0; padding:12px 14px; border-radius:12px;
  border:1px solid rgba(212,175,55,.25); background:rgba(212,175,55,.06);
  font-size:.85rem; color:var(--muted);
}
.ledger strong { color:var(--gold); }
.portal {
  margin:2.2rem 0 0; border-radius:16px;
  border:1px solid rgba(255,80,80,.38);
  background: radial-gradient(ellipse 70% 50% at 80% 0%, rgba(255,80,80,.09) 0%, transparent 55%), rgba(16,8,12,.96);
  padding:1.35rem 1.2rem 1.5rem;
}
.portal h2 { margin:0 0 .35rem; font-size:clamp(1.25rem,2.6vw,1.7rem); color:var(--warn); font-family:"Cormorant Garamond",Georgia,serif; font-weight:500; }
.kicker { font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:.7rem; letter-spacing:.16em; text-transform:uppercase; color:var(--gold); margin:0 0 .75rem; }
.portal .lead { color:var(--muted); font-size:.92rem; max-width:78ch; }
.howto { display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:10px; margin:1rem 0; }
.step { border:1px solid var(--line); border-radius:12px; padding:12px 14px; background:rgba(0,0,0,.28); }
.step b { display:block; color:var(--gold); font-size:.78rem; letter-spacing:.08em; text-transform:uppercase; margin-bottom:.35rem; }
.step p { margin:0; font-size:.82rem; color:var(--muted); }
.gate-box {
  margin:1rem 0; max-height:min(52vh, 420px); overflow:auto; padding:1rem 1.05rem;
  border-radius:12px; border:1px solid rgba(255,255,255,.12); background:rgba(0,0,0,.38);
  font-size:.84rem; color:#c8c8d8;
}
.gate-box h3 { margin:.85rem 0 .35rem; font-size:.78rem; color:var(--gold); letter-spacing:.08em; text-transform:uppercase; }
.gate-box h3:first-child { margin-top:0; }
.checks { display:flex; flex-direction:column; gap:.55rem; margin:1rem 0; }
.checks label { display:flex; gap:.6rem; align-items:flex-start; font-size:.84rem; color:var(--text); }
.gate-actions { display:flex; flex-wrap:wrap; gap:.65rem; align-items:center; }
.gate-accept, .gate-decline {
  appearance:none; font:inherit; font-weight:700; font-size:.84rem; padding:.6rem 1.05rem; border-radius:8px; cursor:pointer;
}
.gate-accept { border:1px solid rgba(255,138,138,.55); background:linear-gradient(135deg,rgba(255,80,80,.22),rgba(212,175,55,.12)); color:#fff; }
.gate-accept:disabled { opacity:.45; cursor:not-allowed; }
.gate-decline { border:1px solid var(--line); background:transparent; color:var(--text); }
.donate { margin-left:auto; font-size:.78rem; color:var(--muted); }
.donate a { color:var(--gold); }
.vault[hidden] { display:none !important; }
.vault { margin-top:1.1rem; padding-top:1rem; border-top:1px solid rgba(255,138,138,.22); }
.full-card {
  background:var(--panel); border:1px solid rgba(255,138,138,.28); border-radius:12px; padding:12px 14px; margin:0 0 10px;
}
.full-card h3 { margin:0 0 6px; color:#ffb4b4; font-size:1rem; }
.full-card p { margin:0 0 8px; font-size:.85rem; color:var(--muted); }
.full-card .meta { font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:.68rem; color:var(--muted); margin-bottom:8px; }
.full-card a.dl {
  display:inline-block; font-size:.78rem; padding:6px 12px; border-radius:8px;
  border:1px solid rgba(212,175,55,.45); background:rgba(212,175,55,.12); color:var(--gold);
}
.links { display:flex; flex-wrap:wrap; gap:.5rem 1rem; font-size:.8rem; margin:.8rem 0 0; }
"""


def page_html(hub: dict, full: dict, canon: str, cat_href: str, zip_base: str, full_cat_href: str) -> str:
    hub_embed = json.dumps(hub, ensure_ascii=False, separators=(",", ":"))
    full_embed = json.dumps(full, ensure_ascii=False, separators=(",", ":"))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>LYGO SkillHub — Public catalog + FULL download portal</title>
<meta name="description" content="LYGO SkillHub on chatagent.ca: labeled ClawHub public tentacles, and a gated FULL engineer download portal with SHA-256, install instructions, and disclaimers. Steward: Justin Helmer / Excavationpro." />
<meta name="author" content="Justin Helmer / Excavationpro / Lightfather" />
<meta name="robots" content="index, follow, max-image-preview:large" />
<link rel="canonical" href="{canon}" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;1,500&family=IBM+Plex+Mono:wght@400&family=Syne:wght@500;700;800&display=swap" rel="stylesheet" />
<meta name="theme-color" content="#0a0a12" />
<meta name="google-adsense-account" content="ca-pub-0646320966060599" />
<meta property="og:type" content="website" />
<meta property="og:title" content="LYGO SkillHub — catalog + FULL download portal" />
<meta property="og:description" content="Public ClawHub tentacles and gated FULL engineer zips with hash verify and install map." />
<meta property="og:url" content="{canon}" />
<meta property="og:image" content="https://chatagent.ca/assets/og-home.jpg" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:site" content="@Excavationpro" />
<meta name="twitter:title" content="LYGO SkillHub" />
<meta name="twitter:description" content="Labeled skills. FULL download portal. Disclaimers first." />
<meta name="twitter:image" content="https://chatagent.ca/assets/og-home.jpg" />
<style>{PAGE_CSS}</style>
</head>
<body>
<header class="top">
  <div class="wrap">
    <div class="brandrow">
      <h1 class="brand">LYGO SkillHub</h1>
      <nav class="site-nav" aria-label="Site">
        <a href="https://chatagent.ca/">Home</a>
        <a href="https://chatagent.ca/guides/">Guides</a>
        <a href="https://chatagent.ca/champions.html">Champions</a>
        <a href="https://chatagent.ca/app.html">Tools</a>
        <a href="{canon}" aria-current="page">SkillHub</a>
      </nav>
    </div>
    <p class="sub">Two honest channels. <strong>Public tentacles</strong> live on ClawHub (SkillSpector-reviewed, often safety-trimmed). <strong>FULL engineer zips</strong> live only on this download portal — behind a disclaimer gate, with SHA-256, install steps, and lattice wiring. Steward: Justin Helmer / Excavationpro (Lightfather).</p>
    <nav class="nav" aria-label="Lattice">
      <a class="hot" href="#full-lygo">FULL download portal</a>
      <a href="#catalog">Public catalog</a>
      <a href="https://clawhub.ai/deepseekoracle" target="_blank" rel="noopener">ClawHub @deepseekoracle</a>
      <a href="https://deepseekoracle.github.io/lygo-protocol-stack/agent-agora/">Agent Agora</a>
      <a href="https://deepseekoracle.github.io/lygo-protocol-stack/HavenStarChart.html">Star Chart</a>
      <a href="https://deepseekoracle.github.io/lygo-protocol-stack/KernelEggRetrieval.html">Kernel eggs</a>
      <a href="https://chatagent.ca/lygo-continuum.html">Continuum</a>
      <a href="https://huggingface.co/spaces/DeepSeekOracle/LYGO-Resonance-Engine">Resonance Engine</a>
    </nav>
  </div>
</header>

<main class="wrap">
  <div class="channels">
    <article class="ch">
      <h2>Channel A · Public tentacle</h2>
      <p>Install from ClawHub with <code>npx clawhub@latest install deepseekoracle/&lt;slug&gt;</code>. Green security surface. Safe default for strangers and store reviews. Does <em>not</em> include engineer-unlocked limbs.</p>
    </article>
    <article class="ch">
      <h2>Channel B · FULL download portal</h2>
      <p>Human-fetched zip + hash check + sandbox. Unlocked RAW packages for a trusted local stack. Not published to ClawHub. Live Star Chart writes still need explicit human consent.</p>
    </article>
    <article class="ch">
      <h2>Support (optional)</h2>
      <p>Downloads are free. Optional fuel for hosting and packaging: <a href="https://www.paypal.com/paypalme/ExcavationPro" target="_blank" rel="noopener">PayPal.me/ExcavationPro</a>. A donation does not buy rights, bypass the gate, or unlock extra malware. It is a tip.</p>
    </article>
  </div>

  <div class="stats" id="stats"></div>
  <div class="ledger" id="ledger"><strong>Lattice record</strong> · loading…</div>

  <h2 id="catalog" style="font-family:'Cormorant Garamond',Georgia,serif;font-weight:500;color:var(--gold);margin:8px 0 4px;">Public catalog</h2>
  <p class="sub" style="margin-top:0">Every ClawHub @deepseekoracle listing plus USB kits and lattice surfaces. Labels: <em>public tentacle</em>, <em>FULL zip on this hub</em>, plugin, USB, surface. Alias slugs are marked so you install the canonical name.</p>
  <div class="toolbar">
    <input id="q" type="search" placeholder="Search slug, name, summary…" autocomplete="off" />
    <select id="kind">
      <option value="">All types</option>
      <option value="skill">Skills</option>
      <option value="plugin">Plugins</option>
      <option value="download">USB / kits</option>
      <option value="surface">Lattice surfaces</option>
    </select>
    <select id="cat"><option value="">All categories</option></select>
    <select id="sort">
      <option value="downloads">Sort: downloads</option>
      <option value="name">Sort: name</option>
      <option value="category">Sort: category</option>
      <option value="kind">Sort: type</option>
    </select>
  </div>
  <div class="grid" id="grid"></div>

  <section class="portal" id="full-lygo" aria-labelledby="full-lygo-title">
    <p class="kicker">Download portal · engineer channel · not ClawHub</p>
    <h2 id="full-lygo-title">FULL LYGO — unlocked operator packages</h2>
    <p class="lead">This is the replacement for the old one-click disclaimer overlay. Read the instructions, tick every box, then the vault lists each zip with SHA-256, size, harm default, and a copy-hash control. Public / foreign agents still start with the join kits (verify → align → dry-run). Operators add Cyborg Kernel, Continuum, SkillSpector, eggs.</p>

    <div class="howto">
      <div class="step"><b>1. Choose a channel</b><p>Need a store-safe install? Stay on Channel A (ClawHub). Building a live self-auditing lattice on hardware you own? Continue here.</p></div>
      <div class="step"><b>2. Fetch + hash</b><p>Download the zip. On Windows: <code>CertUtil -hashfile FILE SHA256</code>. On Linux/macOS: <code>sha256sum FILE</code>. Match the catalog digest before unzipping.</p></div>
      <div class="step"><b>3. Sandbox install</b><p>Unzip into a skills folder you control (OpenClaw skills dir or <code>.grok/skills/</code>). Run Skill Gate / SkillSpector on the folder. Do not pipe curl to bash.</p></div>
      <div class="step"><b>4. Boot order</b><p>Join kit → Public Lattice Gate → Cyborg Kernel FULL → Continuum → SkillSpector. Pulse Agent Agora. Propose Star Chart nodes only as dry-run until a human consents ingest.</p></div>
    </div>

    <div class="gate-box">
      <h3>What FULL means</h3>
      <p>Packages behind this gate are engineer-grade LYGO builds. They are meant to sink into a <strong>trusted</strong> stack and operate (audit loops, eggs, army sentinel, lattice pulse) under LYGO policy. They are <strong>not</strong> malware, exploit kits, or a license to attack anyone’s systems — including your own production boxes without a backup.</p>
      <h3>ClawHub boundary</h3>
      <p>FULL zips are <strong>not published to ClawHub</strong>. ClawHub carries public tentacles. If a skill’s card says “FULL zip on this hub”, the unlocked copy is only this portal. Permissions claimed on ClawHub apply to the tentacle folder, not this zip.</p>
      <h3>Consent &amp; live writes</h3>
      <p>Pulse, verify, and rebuild locally as much as you want. <strong>Live Haven Star Chart ingest, git push, Hugging Face publish, and social posts require explicit human consent</strong> (<code>--i-consent</code> or equivalent). Agents must not silently write the live chart.</p>
      <h3>Guarantee / no guarantee</h3>
      <p>We package in good faith (P0 framing, dual ledgers, no secret-stealing payloads). We are <strong>not</strong> responsible for what extended systems, agents, or operators do after install. You run FULL packages on machines <strong>you</strong> trust. TraumaCodex is protocol code, not medicine. Flame Ward “burn” means quarantine of bad data, not violence.</p>
      <h3>Verify chain</h3>
      <p>Catalog JSON: <a href="{full_cat_href}">{full_cat_href}</a>. After unzip, read <code>READ_DISCLAIMER_FIRST.md</code> and <code>FULL_LYGO.md</code> inside the pack. Wire Cyborg: <code>cyborg_star.py agora</code> → Agent Agora pulse. Eggs: Kernel Egg Retrieval. Whisper routing is living JSON, separate from the archival last whisper.</p>
      <h3>Optional support</h3>
      <p>PayPal is a tip, not a paywall. <a href="https://www.paypal.com/paypalme/ExcavationPro" target="_blank" rel="noopener">paypal.me/ExcavationPro</a></p>
    </div>

    <div class="checks">
      <label><input type="checkbox" id="c1" /> I understand Channel B is FULL engineer zips, not the ClawHub tentacle, and I will hash-check before unzip.</label>
      <label><input type="checkbox" id="c2" /> I will not auto-publish, live-write the Star Chart, or git-push without explicit human consent.</label>
      <label><input type="checkbox" id="c3" /> I run this on machines I trust. The steward is not liable for operator or agent actions after download.</label>
      <label><input type="checkbox" id="c4" /> I will not use these packages to attack systems, steal secrets, or treat protocol tools as medical/legal advice.</label>
    </div>
    <div class="gate-actions">
      <button type="button" class="gate-accept" id="fullLygoAccept" disabled>I agree — open the download vault</button>
      <button type="button" class="gate-decline" id="fullLygoDecline">Stay on the public catalog</button>
      <span class="donate">Optional tip · <a href="https://www.paypal.com/paypalme/ExcavationPro" target="_blank" rel="noopener">PayPal</a></span>
    </div>

    <div class="vault" id="fullLygoVault" hidden>
      <p class="lead"><strong style="color:var(--gold)">Vault open for this browser.</strong> Recommended first zip: <code>lygo-cyborg-kernel-full.zip</code> then <code>lygo-public-agent-join-kit-full.zip</code>.</p>
      <div class="links">
        <a href="https://deepseekoracle.github.io/lygo-protocol-stack/agent-agora/">Agent Agora door</a>
        <a href="https://deepseekoracle.github.io/lygo-protocol-stack/HavenStarChartPortal.html">Star Chart agent portal</a>
        <a href="https://deepseekoracle.github.io/lygo-protocol-stack/seals/lfw_whisper_lattice_routing.json">Whisper lattice</a>
        <a href="https://deepseekoracle.github.io/lygo-protocol-stack/KernelEggRetrieval.html">Kernel egg SOA</a>
        <a href="https://chatagent.ca/guides/safe-openclaw-skills.html">Safe OpenClaw skills guide</a>
      </div>
      <div id="fullLygoCards"></div>
    </div>
  </section>

  <footer class="site">
    <p><strong style="color:var(--gold)">Δ9Φ963 · LYGO SkillHub</strong> — Justin Helmer / Excavationpro (Lightfather). Public tentacles remain on ClawHub. FULL zips are this portal only. Consent-gated ops. No auto-publish from install alone.</p>
    <p class="code">Hub catalog {cat_href} · FULL catalog {full_cat_href} · zip base {zip_base}</p>
  </footer>
</main>

<script id="boot-catalog" type="application/json">{hub_embed}</script>
<script id="boot-full" type="application/json">{full_embed}</script>
<script>
(function () {{
  const bootEl = document.getElementById('boot-catalog');
  let catalog = {{}};
  try {{ catalog = JSON.parse(bootEl.textContent); }} catch (e) {{ catalog = {{ skills: [] }}; }}
  const grid = document.getElementById('grid');
  const stats = document.getElementById('stats');
  const ledger = document.getElementById('ledger');
  const q = document.getElementById('q');
  const kind = document.getElementById('kind');
  const cat = document.getElementById('cat');
  const sort = document.getElementById('sort');
  const ZIP_BASE = {json.dumps(zip_base)};
  const FULL_CAT = {json.dumps(full_cat_href)};

  function esc(s) {{
    return String(s || '').replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
  }}
  function allItems() {{ return catalog.skills || catalog.items || []; }}

  function renderStats(items) {{
    const counts = catalog.counts || {{}};
    const skillsN = counts.skills || items.filter(s => (s.kind||'skill')==='skill').length;
    const dls = items.filter(s => (s.kind||'skill')==='skill').reduce((a, s) => a + (s.downloads || 0), 0);
    const fullN = items.filter(s => s.has_full_zip).length;
    stats.innerHTML = [
      ['Total entries', counts.total || items.length],
      ['ClawHub skills', skillsN],
      ['FULL zips on hub', fullN],
      ['USB / kits', counts.downloads || items.filter(s => s.kind==='download').length],
      ['Surfaces', counts.surfaces || items.filter(s => s.kind==='surface').length],
      ['Skill downloads (Σ)', dls.toLocaleString()],
    ].map(([k,v]) => `<div class="stat"><b>${{esc(v)}}</b><span>${{esc(k)}}</span></div>`).join('');
  }}
  function fillCats(items) {{
    const set = [...new Set(items.map(s => s.category).filter(Boolean))].sort();
    cat.innerHTML = '<option value="">All categories</option>' + set.map(c => `<option value="${{esc(c)}}">${{esc(c)}}</option>`).join('');
  }}
  function filtered() {{
    let list = allItems().slice();
    const qq = (q.value || '').toLowerCase().trim();
    const c = cat.value, k = kind.value;
    if (k) list = list.filter(s => {{
      const kk = s.kind || 'skill';
      if (k === 'plugin') return kk === 'plugin' || s.is_openclaw_plugin;
      return kk === k;
    }});
    if (c) list = list.filter(s => s.category === c);
    if (qq) list = list.filter(s =>
      (s.slug||'').toLowerCase().includes(qq) || (s.name||'').toLowerCase().includes(qq) || (s.summary||'').toLowerCase().includes(qq)
    );
    const mode = sort.value;
    list.sort((a,b) => {{
      if (mode === 'name') return (a.name||'').localeCompare(b.name||'');
      if (mode === 'category') return (a.category||'').localeCompare(b.category||'') || (b.downloads||0)-(a.downloads||0);
      if (mode === 'kind') return (a.kind||'skill').localeCompare(b.kind||'skill') || (b.downloads||0)-(a.downloads||0);
      return (b.downloads||0) - (a.downloads||0);
    }});
    return list;
  }}
  function primaryHref(s) {{
    if (s.url) return s.url;
    if (s.clawhub_url) return s.clawhub_url;
    return 'https://clawhub.ai/deepseekoracle/skills/' + (s.slug || '');
  }}
  function primaryLabel(s) {{
    const k = s.kind || 'skill';
    if (k === 'download') return 'Download kit';
    if (k === 'surface') return 'Open surface';
    if (k === 'plugin') return 'Plugin page';
    return 'Open on ClawHub';
  }}
  function render() {{
    const list = filtered();
    grid.innerHTML = list.map(s => {{
      const install = s.install || (s.kind === 'skill' ? ('npx clawhub@latest install deepseekoracle/' + s.slug) : '');
      const kind = s.kind || 'skill';
      return `<article class="card">
        <h3>${{esc(s.name)}}</h3>
        <div class="slug">${{esc(s.slug)}} · ${{esc(kind)}}${{s.version ? ' · v'+esc(s.version) : ''}}</div>
        <div class="meta">
          <span class="pill cat">${{esc(s.category || kind)}}</span>
          ${{kind==='skill' ? `<span class="pill tentacle">${{esc(s.channel_label || 'Public tentacle')}}</span>` : `<span class="pill">${{esc(s.channel_label || kind)}}</span>`}}
          ${{s.has_full_zip ? '<span class="pill full">FULL zip on this hub</span>' : ''}}
          ${{kind==='skill' ? `<span class="pill dl">${{(s.downloads||0).toLocaleString()}} dl</span>` : ''}}
          ${{s.alias_of ? `<span class="pill alias">alias of ${{esc(s.alias_of)}}</span>` : ''}}
          ${{s.is_openclaw_plugin || kind==='plugin' ? '<span class="pill local">plugin</span>' : ''}}
        </div>
        <p>${{esc(s.summary || s.note || 'LYGO lattice entry.')}}</p>
        <div class="actions">
          <a class="primary" href="${{esc(primaryHref(s))}}" target="_blank" rel="noopener">${{esc(primaryLabel(s))}}</a>
          ${{install ? `<button type="button" data-cmd="${{esc(install)}}">Copy install</button>` : ''}}
          ${{s.has_full_zip ? '<a href="#full-lygo">FULL portal</a>' : ''}}
          ${{s.docs ? `<a href="${{esc(s.docs)}}" target="_blank" rel="noopener">Docs</a>` : ''}}
          ${{s.plugin_install ? `<button type="button" data-cmd="${{esc(s.plugin_install)}}">Copy plugin install</button>` : ''}}
        </div>
      </article>`;
    }}).join('') || '<p class="sub">No entries match.</p>';
    grid.querySelectorAll('button[data-cmd]').forEach(btn => {{
      btn.addEventListener('click', () => {{
        if (navigator.clipboard) navigator.clipboard.writeText(btn.getAttribute('data-cmd'));
        const old = btn.textContent;
        btn.textContent = 'Copied';
        setTimeout(() => {{ btn.textContent = old; }}, 1200);
      }});
    }});
  }}
  function renderLedger() {{
    const sha = (catalog.catalog_sha256 || '').slice(0, 16);
    const c = catalog.counts || {{}};
    ledger.innerHTML = `<strong>Lattice record</strong> · <code>${{esc(catalog.signature || '')}}</code>
      · catalog v${{esc(catalog.version || '')}} · total ${{c.total || allItems().length}}
      · sha256 <code>${{esc(sha)}}…</code> · updated ${{esc(catalog.updated_utc || '')}}
      · <a href="{cat_href}">hub JSON</a>
      · <a href="{full_cat_href}">FULL JSON</a>
      · <a href="https://clawhub.ai/deepseekoracle" target="_blank" rel="noopener">ClawHub</a>`;
  }}

  const items = allItems();
  renderStats(items); fillCats(items); renderLedger(); render();
  q.addEventListener('input', render);
  kind.addEventListener('change', render);
  cat.addEventListener('change', render);
  sort.addEventListener('change', render);

  /* FULL portal gate */
  const KEY = 'lygo_full_skills_gate_v2';
  const vault = document.getElementById('fullLygoVault');
  const accept = document.getElementById('fullLygoAccept');
  const decline = document.getElementById('fullLygoDecline');
  const cards = document.getElementById('fullLygoCards');
  const boxes = ['c1','c2','c3','c4'].map(id => document.getElementById(id));
  function syncBtn() {{
    accept.disabled = !boxes.every(b => b && b.checked);
  }}
  boxes.forEach(b => b && b.addEventListener('change', syncBtn));
  function renderFull(cat) {{
    const skills = (cat && cat.skills) || [];
    const tierOrder = (cat.tiers && cat.tiers.length) ? cat.tiers : Object.keys({{}});
    const by = {{}};
    skills.forEach(s => {{ const t = s.tier || 'other'; (by[t] = by[t] || []).push(s); }});
    const order = tierOrder.length ? tierOrder : Object.keys(by);
    let html = '';
    if (cat.public_agent_principle) html += '<p class="lead"><strong style="color:var(--cyan)">Public agent principle:</strong> ' + esc(cat.public_agent_principle) + '</p>';
    if (cat.cyborg_principle) html += '<p class="lead"><strong style="color:var(--gold)">Cyborg principle:</strong> ' + esc(cat.cyborg_principle) + '</p>';
    order.forEach(tier => {{
      const list = by[tier]; if (!list) return;
      html += '<h3 style="margin:18px 0 8px;font-size:.78rem;letter-spacing:.12em;text-transform:uppercase;color:var(--gold)">' + esc((list[0].tier_label) || tier.replace(/_/g,' ')) + '</h3>';
      list.forEach(s => {{
        const href = ZIP_BASE + (s.zip || (s.slug + '-full.zip'));
        const kb = s.bytes ? Math.round(s.bytes/1024) + ' KB' : '';
        const sha = s.zip_sha256 || '';
        html += '<article class="full-card">' +
          '<h3>' + esc(s.name || s.slug) + '</h3>' +
          '<p>' + esc(s.role || '') + '</p>' +
          '<div class="meta">harm ' + esc(s.harm_default||'consent_gated') + ' · ' + esc(s.file_count||'') + ' files · ' + esc(kb) +
          (sha ? ' · sha256 ' + esc(sha) : '') + '</div>' +
          '<a class="dl" href="' + esc(href) + '" download>Download FULL zip</a> ' +
          (sha ? '<button type="button" data-sha="' + esc(sha) + '">Copy SHA-256</button>' : '') +
          '</article>';
      }});
    }});
    cards.innerHTML = html || '<p>Catalog empty.</p>';
    cards.querySelectorAll('button[data-sha]').forEach(btn => {{
      btn.addEventListener('click', () => {{
        if (navigator.clipboard) navigator.clipboard.writeText(btn.getAttribute('data-sha'));
        btn.textContent = 'Copied hash';
        setTimeout(() => {{ btn.textContent = 'Copy SHA-256'; }}, 1200);
      }});
    }});
  }}
  function unlock() {{
    try {{ localStorage.setItem(KEY, '1'); }} catch (e) {{}}
    vault.hidden = false;
    let embedded = null;
    try {{ embedded = JSON.parse(document.getElementById('boot-full').textContent); }} catch (e) {{}}
    if (embedded && embedded.skills) renderFull(embedded);
    fetch(FULL_CAT, {{ cache: 'no-store' }}).then(r => r.ok ? r.json() : null).then(j => {{ if (j) renderFull(j); }}).catch(() => {{}});
  }}
  function lock() {{
    try {{ localStorage.removeItem(KEY); }} catch (e) {{}}
    vault.hidden = true;
    boxes.forEach(b => {{ if (b) b.checked = false; }});
    syncBtn();
  }}
  accept.addEventListener('click', unlock);
  decline.addEventListener('click', lock);
  try {{ if (localStorage.getItem(KEY) === '1') {{ boxes.forEach(b => {{ if (b) b.checked = true; }}); syncBtn(); unlock(); }} }} catch (e) {{}}
  if (location.hash === '#full-lygo') {{
    document.getElementById('full-lygo').scrollIntoView({{ behavior: 'smooth', block: 'start' }});
  }}
}})();
</script>
</body>
</html>
"""


def write_pages(hub: dict, full: dict) -> None:
    targets = [
        (CHAT / "lygoskillhub.html", "https://chatagent.ca/lygoskillhub.html",
         "data/lygoskillhub_catalog.json", "data/lygo-full-skills/dist/", "data/lygo-full-skills/catalog.json"),
        (STACK / "docs" / "LYGOSKILLHUB.html", "https://deepseekoracle.github.io/lygo-protocol-stack/LYGOSKILLHUB.html",
         "data/lygoskillhub_catalog.json", "lygo-full-skills/dist/", "lygo-full-skills/catalog.json"),
    ]
    if (EXCA / "LYGOSKILLHUB.html").exists() or EXCA.is_dir():
        targets.append((
            EXCA / "LYGOSKILLHUB.html",
            "https://deepseekoracle.github.io/Excavationpro/LYGOSKILLHUB.html",
            "data/lygoskillhub_catalog.json",
            "data/lygo-full-skills/dist/",
            "data/lygo-full-skills/catalog.json",
        ))
    for path, canon, cat_href, zip_base, full_href in targets:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(page_html(hub, full, canon, cat_href, zip_base, full_href), encoding="utf-8")
        print("wrote", path)


def sync_json(hub: dict, full: dict) -> None:
    copies_hub = [
        CHAT / "data" / "lygoskillhub_catalog.json",
        STACK / "docs" / "data" / "lygoskillhub_catalog.json",
        STACK / "docs" / "lygoskillhub_catalog.json",
    ]
    copies_full = [
        CHAT / "data" / "lygo-full-skills" / "catalog.json",
        STACK / "docs" / "lygo-full-skills" / "catalog.json",
    ]
    blob_h = json.dumps(hub, ensure_ascii=False, indent=2) + "\n"
    blob_f = json.dumps(full, ensure_ascii=False, indent=2) + "\n"
    for p in copies_hub:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(blob_h, encoding="utf-8")
        print("hub json", p)
    for p in copies_full:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(blob_f, encoding="utf-8")
        print("full json", p)
    if EXCA.is_dir():
        p = EXCA / "data" / "lygoskillhub_catalog.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(blob_h, encoding="utf-8")


def main() -> int:
    full_src = CHAT / "data" / "lygo-full-skills" / "catalog.json"
    if not full_src.is_file():
        full_src = STACK / "docs" / "lygo-full-skills" / "catalog.json"
    full = relabel_full_catalog(full_src)
    full_slugs = {s.get("slug") for s in full.get("skills") or []}
    hub_src = CHAT / "data" / "lygoskillhub_catalog.json"
    if not hub_src.is_file():
        hub_src = STACK / "docs" / "data" / "lygoskillhub_catalog.json"
    hub = relabel_hub_catalog(hub_src, full_slugs)
    sync_json(hub, full)
    write_pages(hub, full)
    print("skills", hub.get("counts"), "full zips", len(full.get("skills") or []))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
