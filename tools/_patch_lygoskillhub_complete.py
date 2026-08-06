#!/usr/bin/env python3
"""Align catalog to LYGOSkills.txt (63) + rebuild LYGOSKILLHUB with dual ledgers, crypto, copyright."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

CAT_PATHS = [
    Path(r"D:\lygo-protocol-stack\docs\lygoskillhub_catalog.json"),
    Path(r"D:\lygo-protocol-stack\docs\data\lygoskillhub_catalog.json"),
    Path(r"D:\Excavationpro\data\lygoskillhub_catalog.json"),
    Path(r"D:\chatagent\data\lygoskillhub_catalog.json"),
]
PRIMARY_CAT = CAT_PATHS[0]
OUTS = [
    Path(r"D:\lygo-protocol-stack\docs\LYGOSKILLHUB.html"),
    Path(r"D:\Excavationpro\LYGOSKILLHUB.html"),
    Path(r"D:\chatagent\lygoskillhub.html"),
]

EXTRA = [
    {
        "kind": "skill",
        "slug": "book-brain-visual-reader",
        "name": "BOOK BRAIN VISUAL READER – LYGO 3-Brain + Visual Left/Right Brain",
        "summary": "Enhanced BOOK BRAIN for LYGO Havens with visual capability. Use to design and operate visual left/right brain reading workflows on the lattice.",
        "downloads": 1500,
        "category": "memory",
        "clawhub_url": "https://clawhub.ai/deepseekoracle/skills/book-brain-visual-reader",
        "install": "npx clawhub@latest install deepseekoracle/book-brain-visual-reader",
        "has_local_skill": False,
        "source": "clawhub",
        "tags": ["browser-automation", "memory-system"],
    },
    {
        "kind": "skill",
        "slug": "openclaw-flow-kit",
        "name": "OpenClaw Flow Kit",
        "summary": "Fix common OpenClaw workflow bottlenecks: platform engage-gates/429 backoff and resilient flow patterns for agent integrations.",
        "downloads": 1500,
        "category": "tools",
        "clawhub_url": "https://clawhub.ai/deepseekoracle/skills/openclaw-flow-kit",
        "install": "npx clawhub@latest install deepseekoracle/openclaw-flow-kit",
        "has_local_skill": False,
        "source": "clawhub",
        "tags": ["json"],
    },
    {
        "kind": "skill",
        "slug": "recursive-generosity-protocol",
        "name": "Recursive Generosity Protocol (Delta9-WP-003)",
        "summary": "Public reference + implementation playbook for Delta9-WP-003 Recursive Generosity Protocol on the LYGO lattice.",
        "downloads": 1500,
        "category": "tools",
        "clawhub_url": "https://clawhub.ai/deepseekoracle/skills/recursive-generosity-protocol",
        "install": "npx clawhub@latest install deepseekoracle/recursive-generosity-protocol",
        "has_local_skill": False,
        "source": "clawhub",
    },
    {
        "kind": "skill",
        "slug": "void-atlas-protocol",
        "name": "Void Atlas Protocol",
        "summary": "Void Atlas Protocol – a four-axis ethical navigation map (power, truth, light, void) for aligned agent decision framing.",
        "downloads": 1500,
        "category": "tools",
        "clawhub_url": "https://clawhub.ai/deepseekoracle/skills/void-atlas-protocol",
        "install": "npx clawhub@latest install deepseekoracle/void-atlas-protocol",
        "has_local_skill": False,
        "source": "clawhub",
    },
    {
        "kind": "skill",
        "slug": "lygo-mint-operator-suite",
        "name": "LYGO-MINT Operator Suite (v2)",
        "summary": "Advanced LYGO-MINT Operator Suite (v2): canonicalize multi-file packs, generate deterministic hashes, append-only ledgers, portable Anchor Snippets for provenance.",
        "downloads": 1200,
        "category": "kernel",
        "clawhub_url": "https://clawhub.ai/deepseekoracle/skills/lygo-mint-operator-suite",
        "install": "npx clawhub@latest install deepseekoracle/lygo-mint-operator-suite",
        "has_local_skill": False,
        "source": "clawhub",
    },
]

# Absolute crypto JS so chatagent / Excavationpro mirrors work
CRYPTO_JS = "https://deepseekoracle.github.io/lygo-protocol-stack/haven_star_chart/haven_star_chart_crypto_anchor.js"
ANCHOR_JSON = "https://deepseekoracle.github.io/lygo-protocol-stack/haven_star_chart/lygoagent_anchor.json"
LW_CHARTS = "https://unpkg.com/lightweight-charts@4.2.0/dist/lightweight-charts.standalone.production.js"

HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>LYGOSKILLHUB — LYGO Skill Lattice Catalog · ClawHub Mirror</title>
<meta name="description" content="LYGOSKILLHUB: sovereign catalog of DeepSeekOracle / LYGO ClawHub skills — lattice, kernel eggs, champions, security, creative tools. Install commands, dual-ledger anchors, LYGOAGENT live charts, Star Chart wiring." />
<meta name="author" content="Justin Helmer / Excavationpro / Lightfather" />
<meta name="robots" content="index, follow, max-image-preview:large" />
<link rel="canonical" href="__CANONICAL__" />
<meta name="theme-color" content="#0a0a12" />
<meta name="lygo:economic-anchor" content="LYGOAGENT" />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="LYGOSKILLHUB · LYGO Lattice" />
<meta property="og:title" content="LYGOSKILLHUB — LYGO Skill Lattice Catalog" />
<meta property="og:description" content="All DeepSeekOracle LYGO skills in one lattice hub. ClawHub install links, dual ledgers, LYGOAGENT crypto feed, Star Chart." />
<meta property="og:url" content="__CANONICAL__" />
<meta property="og:image" content="https://deepseekoracle.github.io/Excavationpro/assets/og-excavationpro-listen.jpg" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:site" content="@Excavationpro" />
<meta name="twitter:title" content="LYGOSKILLHUB — LYGO Skills" />
<meta name="twitter:description" content="Sovereign ClawHub skill mirror on the LYGO lattice — dual ledgers + LYGOAGENT." />
<meta name="twitter:image" content="https://deepseekoracle.github.io/Excavationpro/assets/og-excavationpro-listen.jpg" />
<meta name="twitter:url" content="__CANONICAL__" />
<link rel="alternate" type="application/json" href="https://deepseekoracle.github.io/lygo-protocol-stack/network_builder/IMMUTABLE_ANCHORS.json" title="IMMUTABLE_ANCHORS link ledger" />
<link rel="alternate" type="application/json" href="https://deepseekoracle.github.io/lygo-protocol-stack/haven_star_chart/haven_star_chart_feed.json" title="Star Chart commit feed" />
<link rel="alternate" type="application/json" href="__ANCHOR_JSON__" title="LYGOAGENT Economic Anchor (AI)" />
<style>
:root {
  --bg:#07070f; --panel:#12121f; --line:#25253a; --text:#eef0f8; --muted:#9292a8;
  --gold:#d4af37; --cyan:#00e5ff; --mag:#b06bff; --ok:#3dd68c;
}
* { box-sizing:border-box; }
body {
  margin:0; font-family:Inter,system-ui,sans-serif; color:var(--text);
  background:radial-gradient(1000px 520px at 10% -10%,#24123f 0%,var(--bg) 50%);
  min-height:100vh;
}
a { color:var(--cyan); text-decoration:none; }
a:hover { text-decoration:underline; }
.wrap { max-width:1100px; margin:0 auto; padding:0 16px 48px; }
header {
  padding:22px 0 14px; border-bottom:1px solid rgba(0,229,255,.12);
  position:sticky; top:0; background:rgba(7,7,15,.92); backdrop-filter:blur(8px); z-index:20;
}
.brand { font-family:Cinzel,Georgia,serif; color:var(--gold); font-size:clamp(1.35rem,3vw,1.8rem); margin:0; letter-spacing:.04em; }
.sub { color:var(--muted); font-size:.92rem; margin:.35rem 0 0; line-height:1.5; max-width:70ch; }
.nav { display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }
.nav a {
  font-size:.78rem; padding:6px 10px; border-radius:999px;
  border:1px solid rgba(0,229,255,.28); background:rgba(0,229,255,.06); color:var(--text);
}
.nav a:hover { border-color:var(--gold); color:var(--gold); text-decoration:none; }
.stats {
  display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:10px; margin:18px 0;
}
.stat {
  background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:12px 14px;
}
.stat b { display:block; font-size:1.35rem; color:var(--gold); }
.stat span { font-size:.75rem; color:var(--muted); text-transform:uppercase; letter-spacing:.06em; }
.toolbar {
  display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin:8px 0 16px;
}
.toolbar input, .toolbar select {
  background:#0a0a14; border:1px solid var(--line); color:var(--text);
  border-radius:10px; padding:10px 12px; font:inherit;
}
.toolbar input { flex:1; min-width:200px; }
.grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:12px; }
.card {
  background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:14px 14px 12px;
  display:flex; flex-direction:column; gap:8px; min-height:180px;
}
.card h3 { margin:0; font-size:1.02rem; color:var(--gold); line-height:1.3; }
.card .slug { font-family:ui-monospace,monospace; font-size:.72rem; color:var(--muted); word-break:break-all; }
.card p { margin:0; font-size:.86rem; color:var(--text); opacity:.92; line-height:1.45; flex:1; }
.meta { display:flex; flex-wrap:wrap; gap:6px; align-items:center; }
.pill {
  font-size:.68rem; padding:3px 8px; border-radius:999px; border:1px solid var(--line);
  color:var(--muted); text-transform:uppercase; letter-spacing:.04em;
}
.pill.cat { border-color:rgba(176,107,255,.4); color:#d4b8ff; }
.pill.dl { border-color:rgba(61,214,140,.35); color:var(--ok); }
.pill.local { border-color:rgba(0,229,255,.35); color:var(--cyan); }
.actions { display:flex; flex-wrap:wrap; gap:6px; margin-top:4px; }
.actions a, .actions button {
  font-size:.75rem; padding:6px 10px; border-radius:8px; border:1px solid rgba(0,229,255,.3);
  background:rgba(0,229,255,.08); color:var(--cyan); cursor:pointer; font:inherit;
}
.actions a.primary { background:rgba(212,175,55,.15); border-color:rgba(212,175,55,.45); color:var(--gold); }
.actions button:hover, .actions a:hover { filter:brightness(1.1); text-decoration:none; }
footer {
  margin-top:28px; padding-top:16px; border-top:1px solid var(--line);
  color:var(--muted); font-size:.82rem; line-height:1.55;
}
.code {
  background:#0a0a14; border:1px solid var(--line); border-radius:8px; padding:8px 10px;
  font-family:ui-monospace,monospace; font-size:.72rem; color:#cfd8ff; word-break:break-all;
}
.ledger {
  margin:16px 0; padding:12px 14px; border-radius:12px;
  border:1px solid rgba(212,175,55,.25); background:rgba(212,175,55,.06);
  font-size:.85rem; color:var(--muted);
}
.ledger strong { color:var(--gold); }
/* dual ledgers */
.lygo-dual-ledgers {
  width:100%; margin:1.75rem 0 0; display:grid; gap:14px; color:var(--text);
}
@media (min-width:720px) {
  .lygo-dual-ledgers { grid-template-columns:1fr 1fr; }
}
.lygo-dual-ledgers .lygo-ledger-card {
  text-align:left; padding:16px 16px 14px; border-radius:14px;
  border:1px solid rgba(212,175,55,.3); background:rgba(10,12,20,.92);
  box-shadow:0 12px 32px -18px rgba(0,0,0,.8);
}
.lygo-dual-ledgers .lygo-ledger-card h2 {
  margin:0 0 6px; font-size:12px; letter-spacing:.14em; text-transform:uppercase;
  color:var(--gold); font-weight:700;
}
.lygo-dual-ledgers .ledger-blurb {
  margin:0 0 10px; font-size:12px; color:var(--muted); line-height:1.45;
}
.lygo-dual-ledgers .lygo-ledger-scroll {
  max-height:min(36vh,280px); overflow:auto; border-radius:10px;
  border:1px solid rgba(0,224,240,.18); background:rgba(0,0,0,.28);
  -webkit-overflow-scrolling:touch; overscroll-behavior:contain; scrollbar-gutter:stable;
}
.lygo-dual-ledgers .lygo-ledger-scroll ul { list-style:none; margin:0; padding:6px 0; }
.lygo-dual-ledgers .lygo-ledger-scroll li { margin:0; border-bottom:1px solid rgba(255,255,255,.05); }
.lygo-dual-ledgers .lygo-ledger-scroll li:last-child { border-bottom:none; }
.lygo-dual-ledgers .lygo-ledger-scroll a {
  display:block; padding:8px 12px; color:#00e0f0; text-decoration:none; font-size:12px; line-height:1.4;
}
.lygo-dual-ledgers .lygo-ledger-scroll a:hover { background:rgba(0,224,240,.08); color:#e8a13c; text-decoration:underline; }
.lygo-dual-ledgers .lygo-ledger-scroll a strong { display:block; color:#eeeef6; font-weight:600; }
.lygo-dual-ledgers .lygo-ledger-scroll a:hover strong { color:#e8a13c; }
.lygo-dual-ledgers .lygo-ledger-scroll .meta { display:block; font-size:10px; color:#9a9ab0; margin-top:2px; }
.lygo-dual-ledgers .lygo-ledger-scroll .empty { padding:12px; font-size:12px; color:#9a9ab0; }
.lygo-dual-ledgers .lygo-ledger-scroll .empty a { color:#00e0f0; }
.lygo-dual-ledgers .ledger-foot { margin:8px 0 0; font-size:11px; color:#9a9ab0; }
.lygo-dual-ledgers .ledger-foot a { color:#00e0f0; }
/* LYGOAGENT crypto (cloned from Haven Star Chart) */
.crypto-anchor {
  margin:1.75rem 0 0; border-radius:14px; overflow:hidden;
  border:1px solid rgba(0,240,255,.28);
  background:
    radial-gradient(ellipse 70% 50% at 20% 0%, rgba(125,0,255,.14) 0%, transparent 55%),
    radial-gradient(ellipse 60% 40% at 85% 100%, rgba(0,240,255,.08) 0%, transparent 50%),
    linear-gradient(180deg,#060610 0%,#05050c 100%);
  padding:1.5rem 1.25rem 1.75rem;
}
.crypto-anchor-header {
  display:flex; flex-wrap:wrap; gap:1rem; align-items:flex-start; justify-content:space-between; margin-bottom:1.1rem;
}
.crypto-anchor-header h2 { margin:0; font-size:1.1rem; color:var(--gold); letter-spacing:.04em; }
.crypto-anchor-header .crypto-tagline {
  margin:.35rem 0 0; color:var(--muted); font-size:.78rem; max-width:52rem; line-height:1.5;
}
.crypto-badge {
  display:inline-flex; align-items:center; gap:.45rem; padding:.35rem .65rem;
  border:1px solid rgba(255,204,0,.45); border-radius:999px; font-family:ui-monospace,monospace;
  font-size:.68rem; color:var(--gold); background:rgba(255,204,0,.06);
}
.crypto-badge .pulse {
  width:7px; height:7px; border-radius:50%; background:#00ff88; box-shadow:0 0 8px #00ff88;
  animation:crypto-pulse 2s ease-in-out infinite;
}
@keyframes crypto-pulse {
  0%,100% { opacity:1; transform:scale(1); }
  50% { opacity:.55; transform:scale(.85); }
}
.crypto-grid { display:grid; grid-template-columns:1fr 320px; gap:1.1rem; align-items:stretch; }
@media (max-width:960px) { .crypto-grid { grid-template-columns:1fr; } }
.crypto-chart-panel {
  border:1px solid rgba(0,240,255,.22); border-radius:8px; background:rgba(0,0,0,.35);
  padding:.85rem .85rem .5rem; box-shadow:0 0 32px rgba(0,240,255,.05);
}
.crypto-chart-head {
  display:flex; flex-wrap:wrap; gap:.5rem 1rem; align-items:baseline; justify-content:space-between;
  margin-bottom:.5rem; font-size:.72rem;
}
.crypto-chart-head strong { color:#fff; font-size:.88rem; }
.crypto-chart-head span { color:var(--muted); font-family:ui-monospace,monospace; }
#cryptoChart { width:100%; min-height:280px; }
.crypto-stats-panel {
  border:1px solid rgba(255,204,0,.28); border-radius:8px; background:rgba(255,204,0,.03);
  padding:1rem 1.1rem; display:flex; flex-direction:column; gap:.55rem;
}
.crypto-stats-panel h3 {
  margin:0; font-size:.72rem; letter-spacing:.14em; text-transform:uppercase; color:var(--cyan);
}
.crypto-stat-row {
  display:grid; grid-template-columns:1fr auto; gap:.35rem; font-size:.76rem;
  padding:.3rem 0; border-bottom:1px solid rgba(255,255,255,.06);
}
.crypto-stat-row:last-child { border-bottom:none; }
.crypto-stat-label { color:var(--muted); font-family:ui-monospace,monospace; font-size:.65rem; }
.crypto-stat-val { color:var(--text); font-weight:500; text-align:right; }
.crypto-stat-val.up { color:#00ff88; }
.crypto-stat-val.down { color:#e94560; }
.crypto-stat-val.mono { font-family:ui-monospace,monospace; font-size:.68rem; }
.crypto-links { display:flex; flex-wrap:wrap; gap:.45rem; margin-top:.35rem; }
.crypto-links a {
  color:var(--cyan); text-decoration:none; font-size:.68rem;
  border:1px solid rgba(0,240,255,.3); padding:.3rem .55rem; border-radius:3px;
}
.crypto-links a:hover { background:rgba(0,240,255,.1); }
.crypto-links a.gold { color:var(--gold); border-color:rgba(255,204,0,.4); }
.crypto-links a.trade { color:#ff4da6; border-color:rgba(255,0,122,.45); font-weight:600; }
.crypto-links a.trade:hover { background:rgba(255,0,122,.12); }
.crypto-status { font-size:.65rem; font-family:ui-monospace,monospace; margin-top:.25rem; }
.crypto-status.ok { color:#00ff88; }
.crypto-status.warn { color:var(--gold); }
.crypto-embed-row {
  margin-top:1rem; border:1px solid rgba(125,0,255,.25); border-radius:8px; overflow:hidden; background:#080812;
}
.crypto-embed-row iframe { display:block; width:100%; height:420px; border:0; }
.crypto-embed-label {
  padding:.45rem .75rem; font-size:.65rem; color:var(--muted);
  border-bottom:1px solid rgba(255,255,255,.06); font-family:ui-monospace,monospace;
}
#cryptoCopyContract {
  margin-top:.5rem; background:transparent; border:1px solid rgba(0,240,255,.35);
  color:var(--cyan); font-family:inherit; font-size:.65rem; padding:.35rem .6rem; cursor:pointer; border-radius:3px;
}
#cryptoCopyContract:hover { background:rgba(0,240,255,.08); }
.crypto-trade-bar {
  display:flex; flex-wrap:wrap; gap:.75rem 1.25rem; align-items:center; margin-bottom:1rem;
  padding:.85rem 1rem; border:1px solid rgba(255,0,122,.35); border-radius:8px;
  background:linear-gradient(90deg,rgba(255,0,122,.08) 0%,rgba(0,240,255,.04) 100%);
}
.crypto-trade-primary { display:flex; flex-wrap:wrap; gap:.55rem; }
.crypto-trade-btn {
  display:inline-flex; align-items:center; gap:.45rem; padding:.55rem 1.1rem; border-radius:6px;
  border:1px solid rgba(255,0,122,.55);
  background:linear-gradient(135deg,rgba(255,0,122,.22) 0%,rgba(125,0,255,.18) 100%);
  color:#fff; font-weight:600; font-size:.82rem; letter-spacing:.03em; text-decoration:none;
  box-shadow:0 0 20px rgba(255,0,122,.15);
}
.crypto-trade-btn:hover {
  background:linear-gradient(135deg,rgba(255,0,122,.32) 0%,rgba(125,0,255,.28) 100%);
  border-color:rgba(255,0,122,.75); text-decoration:none;
}
.crypto-trade-btn.virtuals {
  border-color:rgba(255,204,0,.55);
  background:linear-gradient(135deg,rgba(255,204,0,.22) 0%,rgba(125,0,255,.16) 100%);
  box-shadow:0 0 20px rgba(255,204,0,.12);
}
.crypto-trade-btn.virtuals:hover {
  border-color:rgba(255,204,0,.8);
  background:linear-gradient(135deg,rgba(255,204,0,.3) 0%,rgba(125,0,255,.24) 100%);
}
.crypto-buy-grid { display:grid; grid-template-columns:1fr 1fr; gap:1rem; margin-bottom:1.1rem; }
@media (max-width:720px) { .crypto-buy-grid { grid-template-columns:1fr; } }
.crypto-buy-panel {
  border:1px solid rgba(255,255,255,.1); border-radius:8px; padding:.85rem 1rem; background:rgba(0,0,0,.28);
}
.crypto-buy-panel h4 {
  margin:0 0 .55rem; font-size:.68rem; letter-spacing:.12em; text-transform:uppercase; color:var(--gold);
}
.crypto-buy-panel p { margin:0 0 .55rem; font-size:.7rem; color:var(--muted); line-height:1.45; }
.crypto-sweep-note {
  grid-column:1 / -1; margin:0; font-size:.65rem; color:var(--muted); font-family:ui-monospace,monospace;
  line-height:1.5; padding:.55rem .75rem; border:1px dashed rgba(255,255,255,.12); border-radius:6px;
}
.crypto-trade-hint { color:var(--muted); font-size:.72rem; line-height:1.45; max-width:28rem; }
.copyright-block {
  margin-top:1.5rem; padding:1.1rem 1.15rem; border-radius:12px;
  border:1px solid rgba(212,175,55,.28); background:rgba(212,175,55,.05);
  font-size:.8rem; color:var(--muted); line-height:1.55;
}
.copyright-block h2 {
  margin:0 0 .5rem; font-size:.78rem; letter-spacing:.12em; text-transform:uppercase; color:var(--gold);
}
.copyright-block strong { color:var(--text); }
.copyright-block .license-box {
  margin:.75rem 0; padding:.75rem .85rem; border-radius:8px; background:#0a0a14;
  border:1px solid var(--line); font-family:ui-monospace,monospace; font-size:.72rem; color:#cfd8ff; white-space:pre-wrap;
}
</style>
</head>
<body>
<header>
  <div class="wrap">
    <h1 class="brand">LYGOSKILLHUB</h1>
    <p class="sub"><strong>Immutable skill ledger</strong> — every skill that ships to ClawHub <strong>@deepseekoracle</strong> is listed here (catalog tracks live count from <code>clawhub/skills.json</code>). Public tentacles use ClawHub install links; engineer-grade <strong>RAW unlocked</strong> packages for pure LYGO operation live only behind the FULL LYGO gate on this hub (not ClawHub).</p>
    <nav class="nav" aria-label="Lattice">
      <a href="https://clawhub.ai/deepseekoracle" target="_blank" rel="noopener">ClawHub profile</a>
      <a href="#full-lygo" style="border-color:rgba(255,138,138,.45);color:#ff8a8a;">FULL LYGO</a>
      <a href="https://chatagent.ca/app.html">Champion summon</a>
      <a href="https://deepseekoracle.github.io/lygo-protocol-stack/HavenStarChart.html">Star Chart</a>
      <a href="https://deepseekoracle.github.io/lygo-protocol-stack/deception-radar/">Deception Radar</a>
      <a href="#immutable-ledgers">Dual ledgers</a>
      <a href="#crypto-anchor" style="border-color:rgba(0,255,136,.4);color:#00ff88;">LYGOAGENT</a>
      <a href="https://deepseekoracle.github.io/lygo-protocol-stack/LYGO_CLAW.html">LYGO CLAW</a>
      <a href="https://asiancoastline.com/listen.html">Listen free</a>
      <a href="#copyright">© License</a>
    </nav>
  </div>
</header>

<main class="wrap">
  <div class="stats" id="stats"></div>
  <div class="ledger" id="ledger">
    <strong>Lattice record</strong> · Catalog signature loads with skills…
  </div>
  <div class="toolbar">
    <input id="q" type="search" placeholder="Search slug, name, summary…" autocomplete="off" />
    <select id="kind">
      <option value="">All types</option>
      <option value="skill">Skills</option>
      <option value="plugin">Plugins</option>
      <option value="download">USB / Downloads</option>
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

  <!-- Dual immutable ledgers (link vault + star chart commit feed) -->
  <section class="lygo-dual-ledgers" id="immutable-ledgers" aria-label="Immutable lattice ledgers">
    <div class="lygo-ledger-card">
      <h2>Link · Immutable lattice</h2>
      <p class="ledger-blurb">Vaulted public links &amp; traversal anchors (separate from the star chart commit feed).</p>
      <div class="lygo-ledger-scroll" id="linkLedgerScroll">
        <p class="empty">Loading link anchors…</p>
      </div>
      <p class="ledger-foot">
        <a href="https://deepseekoracle.github.io/lygo-protocol-stack/network_builder/IMMUTABLE_ANCHORS.json" target="_blank" rel="noopener">Anchors JSON</a>
        ·
        <a href="https://deepseekoracle.github.io/Excavationpro/excavationpro-music-catalog.html" target="_blank" rel="noopener">Music / ISRC ledger</a>
      </p>
    </div>
    <div class="lygo-ledger-card">
      <h2>Star Chart · Commit ledger</h2>
      <p class="ledger-blurb">Chart transactions (portals, eggs, seals) — append-only feed, latest status per node.</p>
      <div class="lygo-ledger-scroll" id="starLedgerScroll">
        <p class="empty">Loading star chart feed…</p>
      </div>
      <p class="ledger-foot">
        <a href="https://deepseekoracle.github.io/lygo-protocol-stack/haven_star_chart/haven_star_chart_feed.json" target="_blank" rel="noopener">Feed JSON</a>
        ·
        <a href="https://deepseekoracle.github.io/lygo-protocol-stack/HavenStarChart.html" target="_blank" rel="noopener">Open Star Chart</a>
      </p>
    </div>
  </section>

  <!-- LYGOAGENT economic anchor (cloned from Haven Star Chart bottom) -->
  <section class="crypto-anchor" id="crypto-anchor" aria-labelledby="crypto-anchor-title">
    <div class="crypto-anchor-header">
      <div>
        <h2 id="crypto-anchor-title">◎ Economic Anchor Star — LYGOAGENT</h2>
        <p class="crypto-tagline">
          Our sole main coin — the economic anchor tying the Eternal Haven lattice to sovereign agent commerce on Virtuals (Base).
          Live liquidity pool: <strong style="color:var(--text);font-weight:500;">LYGOAGENT / VIRTUAL</strong> on Virtuals Unicorn.
          Primary buy path is the Virtuals agent page; ETH swaps also route via Uniswap / 1inch on Base.
        </p>
      </div>
      <div class="crypto-badge"><span class="pulse" aria-hidden="true"></span> LIVE ANCHOR</div>
    </div>

    <div class="crypto-trade-bar">
      <div class="crypto-trade-primary">
        <a class="crypto-trade-btn virtuals" href="https://app.virtuals.io/virtuals/44594" target="_blank" rel="noopener noreferrer">★ Buy on Virtuals ↗</a>
        <a class="crypto-trade-btn" href="https://app.uniswap.org/explore/tokens/base/0x32b513927f15e7a858be779198440c04d399c09f?inputCurrency=NATIVE" target="_blank" rel="noopener noreferrer">◈ Swap on Uniswap ↗</a>
        <a class="crypto-trade-btn" href="https://app.1inch.io/#/8453/simple/swap/ETH/0x32B513927F15e7A858bE779198440C04D399c09f" target="_blank" rel="noopener noreferrer">◇ Swap on 1inch ↗</a>
      </div>
      <span class="crypto-trade-hint">Verified: Virtuals bonding pool live; Uniswap + 1inch list the token on Base (chain 8453). DexScreener / CoinGecko not indexed yet.</span>
    </div>

    <div class="crypto-buy-grid">
      <div class="crypto-buy-panel">
        <h4>Buy / swap (verified)</h4>
        <p>Agent launch + bonding curve on Virtuals. Aggregators for ETH ↔ LYGOAGENT on Base.</p>
        <div class="crypto-links">
          <a class="gold" href="https://app.virtuals.io/virtuals/44594" target="_blank" rel="noopener">Virtuals agent ↗</a>
          <a class="trade" href="https://app.uniswap.org/explore/tokens/base/0x32b513927f15e7a858be779198440c04d399c09f?inputCurrency=NATIVE" target="_blank" rel="noopener">Uniswap ↗</a>
          <a class="trade" href="https://app.1inch.io/#/8453/simple/swap/ETH/0x32B513927F15e7A858bE779198440C04D399c09f" target="_blank" rel="noopener">1inch ↗</a>
          <a href="https://app.virtuals.io/prototypes/0x32B513927F15e7A858bE779198440C04D399c09f" target="_blank" rel="noopener">Prototype ↗</a>
        </div>
      </div>
      <div class="crypto-buy-panel">
        <h4>Charts &amp; on-chain verify</h4>
        <p>Pool charts, holder stats, and contract proof on Base.</p>
        <div class="crypto-links">
          <a href="https://www.geckoterminal.com/base/pools/0xdbdfc04d005a6b4575b29e5df8109becdc8b9909" target="_blank" rel="noopener">GeckoTerminal ↗</a>
          <a href="https://birdeye.so/token/0x32B513927F15e7A858bE779198440C04D399c09f?chain=base" target="_blank" rel="noopener">Birdeye ↗</a>
          <a href="https://www.dextools.io/app/en/base/pair-explorer/0xdbdfc04d005a6b4575b29e5df8109becdc8b9909" target="_blank" rel="noopener">DEXTools ↗</a>
          <a href="https://basescan.org/token/0x32B513927F15e7A858bE779198440C04D399c09f" target="_blank" rel="noopener">Basescan ↗</a>
        </div>
      </div>
      <p class="crypto-sweep-note">Internet sweep 2026-07-13 · contract 0x32B5…c09f · pool LYGOAGENT/VIRTUAL 0xdbdf…9909 · dex virtuals-unicorn-base · not on DexScreener or CoinGecko yet</p>
    </div>

    <div class="crypto-grid">
      <div class="crypto-chart-panel">
        <div class="crypto-chart-head">
          <div>
            <strong id="cryptoPairName">LYGOAGENT / VIRTUAL</strong>
            <span> · Base · Virtuals Unicorn</span>
          </div>
          <span id="cryptoUpdated">Loading…</span>
        </div>
        <div id="cryptoChart" role="img" aria-label="LYGOAGENT live price chart"></div>
        <p class="crypto-status" id="cryptoStatus">Connecting…</p>
      </div>

      <div class="crypto-stats-panel">
        <h3>Anchor telemetry</h3>
        <div class="crypto-stat-row">
          <span class="crypto-stat-label">Price (USD)</span>
          <span class="crypto-stat-val" id="cryptoPrice">—</span>
        </div>
        <div class="crypto-stat-row">
          <span class="crypto-stat-label">FDV</span>
          <span class="crypto-stat-val" id="cryptoFdv">—</span>
        </div>
        <div class="crypto-stat-row">
          <span class="crypto-stat-label">Pool reserve</span>
          <span class="crypto-stat-val" id="cryptoReserve">—</span>
        </div>
        <div class="crypto-stat-row">
          <span class="crypto-stat-label">24h volume</span>
          <span class="crypto-stat-val" id="cryptoVol24">—</span>
        </div>
        <div class="crypto-stat-row">
          <span class="crypto-stat-label">24h change</span>
          <span class="crypto-stat-val" id="cryptoCh24">—</span>
        </div>
        <div class="crypto-stat-row">
          <span class="crypto-stat-label">Symbol</span>
          <span class="crypto-stat-val">LYGOAGENT</span>
        </div>
        <div class="crypto-stat-row">
          <span class="crypto-stat-label">Agent</span>
          <span class="crypto-stat-val mono">LYRA STARCORE ORACLE</span>
        </div>
        <div class="crypto-stat-row">
          <span class="crypto-stat-label">Contract</span>
          <span class="crypto-stat-val mono" title="0x32B513927F15e7A858bE779198440C04D399c09f">0x32B5…c09f</span>
        </div>
        <div class="crypto-stat-row">
          <span class="crypto-stat-label">Pool</span>
          <span class="crypto-stat-val mono" title="0xdbdfc04d005a6b4575b29e5df8109becdc8b9909">0xdbdf…9909</span>
        </div>
        <div class="crypto-stat-row">
          <span class="crypto-stat-label">Agent wallet</span>
          <span class="crypto-stat-val mono" title="0x2388765eB549347305F48cFc371411891AE15118">0x2388…5118</span>
        </div>
        <div class="crypto-stat-row">
          <span class="crypto-stat-label">Owner wallet</span>
          <span class="crypto-stat-val mono" title="0x0814209fc50866C38186537Cd7C534060E011Ec5">0x0814…1Ec5</span>
        </div>
        <div class="crypto-stat-row">
          <span class="crypto-stat-label">ACP agent id</span>
          <span class="crypto-stat-val">2612</span>
        </div>
        <div class="crypto-stat-row">
          <span class="crypto-stat-label">Registry JSON</span>
          <span class="crypto-stat-val mono"><a href="__ANCHOR_JSON__" style="color:var(--cyan)">lygoagent_anchor.json</a></span>
        </div>
        <button type="button" id="cryptoCopyContract">Copy contract</button>
        <div class="crypto-links">
          <a class="gold" href="https://app.virtuals.io/virtuals/44594" target="_blank" rel="noopener">Virtuals ↗</a>
          <a class="trade" href="https://app.uniswap.org/explore/tokens/base/0x32b513927f15e7a858be779198440c04d399c09f?inputCurrency=NATIVE" target="_blank" rel="noopener">Uniswap ↗</a>
          <a class="trade" href="https://app.1inch.io/#/8453/simple/swap/ETH/0x32B513927F15e7A858bE779198440C04D399c09f" target="_blank" rel="noopener">1inch ↗</a>
          <a href="https://birdeye.so/token/0x32B513927F15e7A858bE779198440C04D399c09f?chain=base" target="_blank" rel="noopener">Birdeye ↗</a>
          <a href="https://www.geckoterminal.com/base/pools/0xdbdfc04d005a6b4575b29e5df8109becdc8b9909" target="_blank" rel="noopener">GeckoTerminal ↗</a>
          <a href="https://basescan.org/token/0x32B513927F15e7A858bE779198440C04D399c09f" target="_blank" rel="noopener">Basescan ↗</a>
        </div>
      </div>
    </div>

    <div class="crypto-embed-row">
      <div class="crypto-embed-label">GeckoTerminal live embed · LYGOAGENT / VIRTUAL on Base</div>
      <iframe
        src="https://www.geckoterminal.com/base/pools/0xdbdfc04d005a6b4575b29e5df8109becdc8b9909?embed=1&amp;info=1&amp;swaps=1&amp;light_chart=0&amp;chart_type=price&amp;resolution=15m"
        title="LYGOAGENT GeckoTerminal chart"
        loading="lazy"
        referrerpolicy="no-referrer-when-downgrade"
        allowfullscreen></iframe>
    </div>
  </section>

  <footer id="copyright" class="copyright-block">
    <h2>Copyright &amp; license</h2>
    <p><strong>Δ9Φ963 · LYGOSKILLHUB</strong> — Steward: <strong>Justin Helmer / Excavationpro (Lightfather)</strong>.</p>
    <p>Skills remain on ClawHub under each skill’s published terms; this hub is the <strong>immutable skill ledger</strong> + install map. Consent-gated ops; no auto-publish from install alone. Catalog source: <code>clawhub/skills.json</code> (live ClawHub-bound skill set) + USB kits + public lattice surfaces. Engineer RAW packages: FULL LYGO vault only (not ClawHub).</p>
    <div class="license-box">© Justin Helmer (Lightfather · Excavationpro · DeepSeekOracle).
LYGO Sovereign License v2.0 — source-available.
Use and build upon under LYGO protocol standards with attribution.
No commercial resale / rebranded forks / corrupt derivatives.
Not MIT / MIT-0. Ownership remains with the steward.
https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/LICENSE</div>
    <p>
      Full notice: <a href="https://deepseekoracle.github.io/lygo-protocol-stack/LICENSE_NOTICE.md" target="_blank" rel="noopener">LICENSE_NOTICE.md</a>
      · Canonical license: <a href="https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/LICENSE" target="_blank" rel="noopener">LYGO Sovereign License v2.0</a>
      · Music (separate): <a href="https://deepseekoracle.github.io/lygo-protocol-stack/LYGO_MUSIC_LICENSE.md" target="_blank" rel="noopener">LYGO_MUSIC_LICENSE</a>
    </p>
    <p>
      ClawHub host checkbox may show MIT-0 for registry listing only — that does <strong>not</strong> relicense steward GitHub LYGO code. Prefer both links on skills: Sovereign LICENSE + ClawHub skill URL.
    </p>
    <p class="code" id="catalog-path">Catalog: lygoskillhub_catalog.json · Economic anchor: LYGOAGENT (Base) · Dual ledgers: IMMUTABLE_ANCHORS + haven_star_chart_feed</p>
    <p style="margin:.75rem 0 0;font-size:.75rem;">© 2026 Justin Helmer / Excavationpro / DeepSeekOracle · LYGO Protocol Stack · All steward rights reserved under LYGO Sovereign License v2.0.</p>
  </footer>
</main>

<script id="boot-catalog" type="application/json">__CATALOG_JSON__</script>
<script>
(function () {
  const bootEl = document.getElementById('boot-catalog');
  let catalog = {};
  try { catalog = JSON.parse(bootEl.textContent); } catch (e) { catalog = { skills: [] }; }

  const grid = document.getElementById('grid');
  const stats = document.getElementById('stats');
  const ledger = document.getElementById('ledger');
  const q = document.getElementById('q');
  const kind = document.getElementById('kind');
  const cat = document.getElementById('cat');
  const sort = document.getElementById('sort');

  function esc(s) {
    return String(s || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  function allItems() { return catalog.skills || catalog.items || []; }

  function renderStats(items) {
    const counts = catalog.counts || {};
    const skillsN = counts.skills || items.filter(s => (s.kind||'skill')==='skill').length;
    const dls = items.filter(s => (s.kind||'skill')==='skill').reduce((a, s) => a + (s.downloads || 0), 0);
    const dlN = counts.downloads || items.filter(s => s.kind==='download').length;
    const surfN = counts.surfaces || items.filter(s => s.kind==='surface').length;
    const plugN = counts.plugins || items.filter(s => s.kind==='plugin' || s.is_openclaw_plugin).length;
    stats.innerHTML = [
      ['Total entries', counts.total || items.length],
      ['ClawHub skills', skillsN],
      ['Profile listed', counts.clawhub_profile_skills_listed || 63],
      ['Plugins', plugN],
      ['USB / kits', dlN],
      ['Surfaces', surfN],
      ['Skill downloads (Σ)', dls.toLocaleString()],
    ].map(([k,v]) => `<div class="stat"><b>${esc(v)}</b><span>${esc(k)}</span></div>`).join('');
  }

  function fillCats(items) {
    const set = [...new Set(items.map(s => s.category).filter(Boolean))].sort();
    cat.innerHTML = '<option value="">All categories</option>' +
      set.map(c => `<option value="${esc(c)}">${esc(c)}</option>`).join('');
  }

  function filtered() {
    let list = allItems().slice();
    const qq = (q.value || '').toLowerCase().trim();
    const c = cat.value;
    const k = kind.value;
    if (k) list = list.filter(s => {
      const kk = s.kind || 'skill';
      if (k === 'plugin') return kk === 'plugin' || s.is_openclaw_plugin;
      return kk === k;
    });
    if (c) list = list.filter(s => s.category === c);
    if (qq) {
      list = list.filter(s =>
        (s.slug || '').toLowerCase().includes(qq) ||
        (s.name || '').toLowerCase().includes(qq) ||
        (s.summary || '').toLowerCase().includes(qq)
      );
    }
    const mode = sort.value;
    list.sort((a, b) => {
      if (mode === 'name') return (a.name || '').localeCompare(b.name || '');
      if (mode === 'category') return (a.category || '').localeCompare(b.category || '') || (b.downloads||0)-(a.downloads||0);
      if (mode === 'kind') return (a.kind||'skill').localeCompare(b.kind||'skill') || (b.downloads||0)-(a.downloads||0);
      return (b.downloads || 0) - (a.downloads || 0);
    });
    return list;
  }

  function copyInstall(cmd) {
    if (navigator.clipboard) navigator.clipboard.writeText(cmd);
  }

  function primaryHref(s) {
    if (s.url) return s.url;
    if (s.clawhub_url) return s.clawhub_url;
    return 'https://clawhub.ai/deepseekoracle/skills/' + (s.slug || '');
  }

  function primaryLabel(s) {
    const k = s.kind || 'skill';
    if (k === 'download') return 'Download';
    if (k === 'surface') return 'Open surface';
    if (k === 'plugin') return 'Plugin page';
    return 'Open on ClawHub';
  }

  function render() {
    const list = filtered();
    grid.innerHTML = list.map(s => {
      const install = s.install || (s.kind === 'skill' ? ('npx clawhub@latest install deepseekoracle/' + s.slug) : '');
      const href = primaryHref(s);
      const kind = s.kind || 'skill';
      return `<article class="card">
        <h3>${esc(s.name)}</h3>
        <div class="slug">${esc(s.slug)} · ${esc(kind)}</div>
        <div class="meta">
          <span class="pill cat">${esc(s.category || kind)}</span>
          ${kind==='skill' ? `<span class="pill dl">${(s.downloads||0).toLocaleString()} dl</span>` : ''}
          ${s.has_local_skill ? '<span class="pill local">local</span>' : ''}
          ${s.is_openclaw_plugin || kind==='plugin' ? '<span class="pill local">plugin</span>' : ''}
          ${s.source ? `<span class="pill">${esc(s.source)}</span>` : ''}
        </div>
        <p>${esc(s.summary || s.note || 'LYGO lattice entry.')}</p>
        <div class="actions">
          <a class="primary" href="${esc(href)}" target="_blank" rel="noopener">${esc(primaryLabel(s))}</a>
          ${install ? `<button type="button" data-cmd="${esc(install)}">Copy install</button>` : ''}
          ${s.docs ? `<a href="${esc(s.docs)}" target="_blank" rel="noopener">Docs</a>` : ''}
          ${s.plugin_install ? `<button type="button" data-cmd="${esc(s.plugin_install)}">Copy plugin install</button>` : ''}
        </div>
      </article>`;
    }).join('') || '<p class="sub">No entries match.</p>';

    grid.querySelectorAll('button[data-cmd]').forEach(btn => {
      btn.addEventListener('click', () => {
        copyInstall(btn.getAttribute('data-cmd'));
        btn.textContent = 'Copied';
        setTimeout(() => { btn.textContent = btn.getAttribute('data-cmd').includes('plugins') ? 'Copy plugin install' : 'Copy install'; }, 1200);
      });
    });
  }

  function renderLedger() {
    const sha = (catalog.catalog_sha256 || '').slice(0, 16);
    const c = catalog.counts || {};
    const ledgerRule = (catalog.immutable_ledger && catalog.immutable_ledger.role)
      ? catalog.immutable_ledger.role
      : 'Anything published to ClawHub @deepseekoracle must appear on this hub';
    ledger.innerHTML = `<strong>Immutable skill ledger</strong> · ${esc(ledgerRule)}
      · signature <code>${esc(catalog.signature || '')}</code>
      · catalog v${esc(catalog.version || '')}
      · total ${c.total || allItems().length}
      · skills ${c.skills || '—'} (ClawHub-indexed ${c.clawhub_skills_indexed || '—'} · local-only ${c.local_only_skills || 0})
      · USB/kits ${c.downloads || 0} · surfaces ${c.surfaces || 0}
      · sha256 <code>${esc(sha)}…</code>
      · updated ${esc(catalog.updated_utc || '')}
      · public tentacle: ClawHub install · engineer RAW: <a href="#full-lygo">FULL LYGO vault</a>
      · <a href="lygoskillhub_catalog.json">catalog JSON</a>
      · <a href="#immutable-ledgers">dual ledgers</a>
      · <a href="#crypto-anchor">LYGOAGENT</a>
      · <a href="https://clawhub.ai/deepseekoracle" target="_blank" rel="noopener">ClawHub @deepseekoracle</a>`;
  }

  const items = allItems();
  renderStats(items);
  fillCats(items);
  renderLedger();
  render();
  q.addEventListener('input', render);
  kind.addEventListener('change', render);
  cat.addEventListener('change', render);
  sort.addEventListener('change', render);
})();
</script>
<script>
/* Dual immutable ledgers — same pattern as chatagent app.html */
(function () {
  if (window.__lygoDualLedgersInit) return;
  window.__lygoDualLedgersInit = true;
  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }
  function linkItem(href, title, meta) {
    if (!href) return '';
    return '<li><a href="' + esc(href) + '" target="_blank" rel="noopener noreferrer"><strong>' +
      esc(title || href) + '</strong>' +
      (meta ? '<span class="meta">' + esc(meta) + '</span>' : '') +
      '</a></li>';
  }
  var linkBox = document.getElementById('linkLedgerScroll');
  fetch('https://deepseekoracle.github.io/lygo-protocol-stack/network_builder/IMMUTABLE_ANCHORS.json', { cache: 'no-store' })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (doc) {
      if (!linkBox) return;
      var groups = (doc && doc.immutable_anchors) || {};
      var html = '';
      Object.keys(groups).forEach(function (cat) {
        var arr = groups[cat];
        if (!Array.isArray(arr)) return;
        arr.slice(0, 12).forEach(function (a) {
          html += linkItem(a.url || a.docs || a.mirror_git, a.label || a.id, cat + (a.note ? ' · ' + a.note : ''));
        });
      });
      linkBox.innerHTML = html ? ('<ul>' + html + '</ul>') : '<p class="empty">No link anchors loaded.</p>';
    })
    .catch(function () {
      if (linkBox) linkBox.innerHTML = '<p class="empty">Link ledger unavailable. <a href="https://deepseekoracle.github.io/lygo-protocol-stack/network_builder/IMMUTABLE_ANCHORS.json" target="_blank" rel="noopener">Open JSON</a></p>';
    });
  var starBox = document.getElementById('starLedgerScroll');
  var feedUrls = [
    'https://deepseekoracle.github.io/lygo-protocol-stack/haven_star_chart/haven_star_chart_feed.json',
    'https://deepseekoracle.github.io/Excavationpro/haven_star_chart/haven_star_chart_feed.json'
  ];
  function renderStar(feed) {
    if (!starBox) return;
    var rows = (feed && feed.entries) || [];
    var latest = {};
    rows.forEach(function (e) {
      var id = e.node_id || '';
      if (!id) return;
      if (!latest[id] || (e.seq || 0) > (latest[id].seq || 0)) latest[id] = e;
    });
    var ids = Object.keys(latest).sort(function (a, b) {
      return (latest[b].seq || 0) - (latest[a].seq || 0);
    }).slice(0, 40);
    var html = '';
    ids.forEach(function (id) {
      var e = latest[id];
      var st = (e.status || '').toUpperCase();
      var chart = 'https://deepseekoracle.github.io/lygo-protocol-stack/HavenStarChart.html';
      var title = (e.node_name || id) + ' · ' + st;
      var meta = (e.event_type || '') + ' · ' + ((e.event_utc || '').replace('T', ' ').slice(0, 19)) +
        (e.content_sha256 ? ' · ' + String(e.content_sha256).slice(0, 10) + '…' : '');
      html += linkItem(chart + '#' + encodeURIComponent(id), title, meta);
    });
    starBox.innerHTML = html ? ('<ul>' + html + '</ul>') : '<p class="empty">No star chart events yet.</p>';
  }
  (function loadStar(i) {
    if (i >= feedUrls.length) {
      if (starBox) starBox.innerHTML = '<p class="empty">Star chart feed unavailable. <a href="https://deepseekoracle.github.io/lygo-protocol-stack/haven_star_chart/haven_star_chart_feed.json" target="_blank" rel="noopener">Open JSON</a></p>';
      return;
    }
    fetch(feedUrls[i], { cache: 'no-store' })
      .then(function (r) { return r.ok ? r.json() : Promise.reject(); })
      .then(renderStar)
      .catch(function () { loadStar(i + 1); });
  })(0);
})();
</script>
<script src="__LW_CHARTS__"></script>
<script src="__CRYPTO_JS__"></script>
</body>
</html>
'''


def patch_catalog() -> dict:
    cat = json.loads(PRIMARY_CAT.read_text(encoding="utf-8"))
    by = {s["slug"]: s for s in cat.get("skills", [])}
    for e in EXTRA:
        if e["slug"] not in by:
            by[e["slug"]] = e
            print("added", e["slug"])
        else:
            print("already", e["slug"])

    skills = list(by.values())

    def sort_key(s):
        kind = s.get("kind") or "skill"
        pri = 0 if kind == "skill" else (1 if kind == "plugin" else (2 if kind == "download" else 3))
        return (pri, -(s.get("downloads") or 0), s.get("name") or "")

    skills.sort(key=sort_key)
    cat["skills"] = skills
    n_skill = sum(1 for s in skills if (s.get("kind") or "skill") == "skill")
    n_plug = sum(1 for s in skills if s.get("kind") == "plugin" or s.get("is_openclaw_plugin"))
    n_dl = sum(1 for s in skills if s.get("kind") == "download")
    n_surf = sum(1 for s in skills if s.get("kind") == "surface")
    n_claw = sum(1 for s in skills if (s.get("kind") or "skill") == "skill" and s.get("source") == "clawhub")
    n_local = sum(1 for s in skills if (s.get("kind") or "skill") == "skill" and s.get("source") == "local")
    cat["counts"] = {
        "total": len(skills),
        "skills": n_skill,
        "plugins": max(n_plug, 1),
        "downloads": n_dl,
        "surfaces": n_surf,
        "clawhub_skills_indexed": n_claw,
        "local_only_skills": n_local,
        "clawhub_profile_skills_listed": n_claw,
    }
    cat["skill_count"] = n_skill
    cat["item_count"] = len(skills)
    cat["updated_utc"] = datetime.now(timezone.utc).isoformat()
    # Preserve catalog version if already built by _build_lygoskillhub_catalog
    if not str(cat.get("version") or "").startswith("1.4"):
        cat["version"] = "1.4.0"
        cat["signature"] = "Delta9Phi963-LYGOSKILLHUB-CATALOG-v1.4"
    cat["source_list"] = "clawhub/skills.json + clawhub/mirrors + local skill tree"
    cat["immutable_ledger"] = {
        "role": "Anything published to ClawHub @deepseekoracle must appear on this hub",
        "public_channel": "ClawHub install links (public tentacle)",
        "engineer_channel": "FULL LYGO vault (#full-lygo) — unlocked RAW packages",
        "primary_page": "https://chatagent.ca/lygoskillhub.html",
    }
    cat["categories"] = sorted({s.get("category") for s in skills if s.get("category")})
    cat["note"] = (
        "Immutable LYGO skill ledger for chatagent.ca/lygoskillhub.html. "
        f"Skills indexed: {n_skill} (ClawHub source {n_claw}). "
        "Public tentacles → ClawHub; FULL unlocked engineer packs → #full-lygo only. "
        "Dual ledgers + LYGOAGENT economic anchor on hub page."
    )
    tmp = {k: v for k, v in cat.items() if k != "catalog_sha256"}
    raw = json.dumps(tmp, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    cat["catalog_sha256"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    for p in CAT_PATHS:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("catalog", p, "skills", n_skill, "total", len(skills))
    return cat


def write_pages(catalog: dict) -> None:
    embed = json.dumps(catalog, ensure_ascii=False, separators=(",", ":"))
    for out in OUTS:
        if "chatagent" in str(out).replace("\\", "/"):
            canon = "https://chatagent.ca/lygoskillhub.html"
            cat_href = "data/lygoskillhub_catalog.json"
        elif "Excavationpro" in str(out):
            canon = "https://deepseekoracle.github.io/Excavationpro/LYGOSKILLHUB.html"
            cat_href = "data/lygoskillhub_catalog.json"
        else:
            canon = "https://deepseekoracle.github.io/lygo-protocol-stack/LYGOSKILLHUB.html"
            cat_href = "lygoskillhub_catalog.json"
        html = (
            HTML.replace("__CATALOG_JSON__", embed)
            .replace("__CANONICAL__", canon)
            .replace("__CRYPTO_JS__", CRYPTO_JS)
            .replace("__ANCHOR_JSON__", ANCHOR_JSON)
            .replace("__LW_CHARTS__", LW_CHARTS)
            .replace('href="lygoskillhub_catalog.json"', f'href="{cat_href}"')
        )
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        print("wrote", out, "bytes", out.stat().st_size)


def main() -> int:
    cat = patch_catalog()
    write_pages(cat)
    # Keep page builder in sync for future rebuilds
    page_builder = Path(r"D:\lygo-protocol-stack\tools\_build_lygoskillhub_page.py")
    if page_builder.is_file():
        # Point rebuilds at this complete template path note
        print("page builder present — run this script for full dual-ledger+crypto pages")
    print("OK skills", cat["counts"]["skills"], "total", cat["counts"]["total"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
