#!/usr/bin/env python3
"""Emit LYGOSKILLHUB.html (self-contained + optional live catalog refresh)."""
from __future__ import annotations

import json
from pathlib import Path

CAT = Path(r"D:\lygo-protocol-stack\docs\lygoskillhub_catalog.json")
OUTS = [
    Path(r"D:\lygo-protocol-stack\docs\LYGOSKILLHUB.html"),
    Path(r"D:\Excavationpro\LYGOSKILLHUB.html"),
    Path(r"D:\chatagent\lygoskillhub.html"),
]

HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>LYGOSKILLHUB — LYGO Skill Lattice Catalog · ClawHub Mirror</title>
<meta name="description" content="LYGOSKILLHUB: sovereign catalog of DeepSeekOracle / LYGO ClawHub skills — lattice, kernel eggs, champions, security, creative tools. Install commands, dual-ledger anchors, Star Chart wiring." />
<meta name="author" content="Justin Helmer / Excavationpro / Lightfather" />
<meta name="robots" content="index, follow, max-image-preview:large" />
<link rel="canonical" href="__CANONICAL__" />
<meta name="theme-color" content="#0a0a12" />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="LYGOSKILLHUB · LYGO Lattice" />
<meta property="og:title" content="LYGOSKILLHUB — LYGO Skill Lattice Catalog" />
<meta property="og:description" content="All DeepSeekOracle LYGO skills in one lattice hub. ClawHub install links, categories, dual ledgers, Star Chart." />
<meta property="og:url" content="__CANONICAL__" />
<meta property="og:image" content="https://deepseekoracle.github.io/Excavationpro/assets/og-excavationpro-listen.jpg" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:site" content="@Excavationpro" />
<meta name="twitter:title" content="LYGOSKILLHUB — LYGO Skills" />
<meta name="twitter:description" content="Sovereign ClawHub skill mirror on the LYGO lattice." />
<meta name="twitter:image" content="https://deepseekoracle.github.io/Excavationpro/assets/og-excavationpro-listen.jpg" />
<meta name="twitter:url" content="__CANONICAL__" />
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
</style>
</head>
<body>
<header>
  <div class="wrap">
    <h1 class="brand">LYGOSKILLHUB</h1>
    <p class="sub">Sovereign mirror of <strong>@deepseekoracle</strong> ClawHub skills on the LYGO lattice — install, verify, wire into dual ledgers &amp; Star Chart. Not a ClawHub fork: lattice catalog + provenance.</p>
    <nav class="nav" aria-label="Lattice">
      <a href="https://clawhub.ai/deepseekoracle" target="_blank" rel="noopener">ClawHub profile</a>
      <a href="https://chatagent.ca/app.html">Champion summon</a>
      <a href="https://deepseekoracle.github.io/lygo-protocol-stack/HavenStarChart.html">Star Chart</a>
      <a href="https://deepseekoracle.github.io/lygo-protocol-stack/network_builder/IMMUTABLE_ANCHORS.json">Link ledger</a>
      <a href="https://deepseekoracle.github.io/lygo-protocol-stack/LYGO_CLAW.html">LYGO CLAW</a>
      <a href="https://asiancoastline.com/listen.html">Listen free</a>
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
    <select id="cat"><option value="">All categories</option></select>
    <select id="sort">
      <option value="downloads">Sort: downloads</option>
      <option value="name">Sort: name</option>
      <option value="category">Sort: category</option>
    </select>
  </div>
  <div class="grid" id="grid"></div>
  <footer>
    <p><strong style="color:var(--gold)">Δ9Φ963 · LYGOSKILLHUB</strong> — Steward: Justin Helmer / Excavationpro (Lightfather). Skills remain on ClawHub; this hub is a lattice mirror + install map. Consent-gated ops; no auto-publish from install alone.</p>
    <p class="code" id="catalog-path">Catalog: lygoskillhub_catalog.json</p>
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
  const cat = document.getElementById('cat');
  const sort = document.getElementById('sort');

  function esc(s) {
    return String(s || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  function renderStats(skills) {
    const cats = new Set(skills.map(s => s.category));
    const dls = skills.reduce((a, s) => a + (s.downloads || 0), 0);
    const local = skills.filter(s => s.has_local_skill).length;
    stats.innerHTML = [
      ['Skills', skills.length],
      ['Categories', cats.size],
      ['Downloads (Σ)', dls.toLocaleString()],
      ['Local mirrors', local],
    ].map(([k,v]) => `<div class="stat"><b>${esc(v)}</b><span>${esc(k)}</span></div>`).join('');
  }

  function fillCats(skills) {
    const set = [...new Set(skills.map(s => s.category))].sort();
    cat.innerHTML = '<option value="">All categories</option>' +
      set.map(c => `<option value="${esc(c)}">${esc(c)}</option>`).join('');
  }

  function filtered() {
    let list = (catalog.skills || []).slice();
    const qq = (q.value || '').toLowerCase().trim();
    const c = cat.value;
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
      return (b.downloads || 0) - (a.downloads || 0);
    });
    return list;
  }

  function copyInstall(cmd) {
    if (navigator.clipboard) navigator.clipboard.writeText(cmd);
  }

  function render() {
    const list = filtered();
    grid.innerHTML = list.map(s => {
      const install = s.install || ('npx clawhub@latest install deepseekoracle/' + s.slug);
      return `<article class="card">
        <h3>${esc(s.name)}</h3>
        <div class="slug">${esc(s.slug)}</div>
        <div class="meta">
          <span class="pill cat">${esc(s.category)}</span>
          <span class="pill dl">${(s.downloads||0).toLocaleString()} dl</span>
          ${s.has_local_skill ? '<span class="pill local">local skill</span>' : ''}
        </div>
        <p>${esc(s.summary || 'LYGO lattice skill on ClawHub.')}</p>
        <div class="actions">
          <a class="primary" href="${esc(s.clawhub_url)}" target="_blank" rel="noopener">Open on ClawHub</a>
          <button type="button" data-cmd="${esc(install)}">Copy install</button>
        </div>
      </article>`;
    }).join('') || '<p class="sub">No skills match.</p>';

    grid.querySelectorAll('button[data-cmd]').forEach(btn => {
      btn.addEventListener('click', () => {
        copyInstall(btn.getAttribute('data-cmd'));
        btn.textContent = 'Copied';
        setTimeout(() => { btn.textContent = 'Copy install'; }, 1200);
      });
    });
  }

  function renderLedger() {
    const sha = (catalog.catalog_sha256 || '').slice(0, 16);
    ledger.innerHTML = `<strong>Lattice record</strong> · signature <code>${esc(catalog.signature || '')}</code>
      · version ${esc(catalog.version || '')}
      · skills ${catalog.skill_count || (catalog.skills||[]).length}
      · sha256 <code>${esc(sha)}…</code>
      · updated ${esc(catalog.updated_utc || '')}
      · <a href="lygoskillhub_catalog.json">catalog JSON</a>
      · <a href="https://deepseekoracle.github.io/lygo-protocol-stack/network_builder/IMMUTABLE_ANCHORS.json">IMMUTABLE_ANCHORS</a>
      · <a href="https://deepseekoracle.github.io/lygo-protocol-stack/haven_star_chart/haven_star_chart_feed.json">star feed</a>`;
  }

  const skills = catalog.skills || [];
  renderStats(skills);
  fillCats(skills);
  renderLedger();
  render();
  q.addEventListener('input', render);
  cat.addEventListener('change', render);
  sort.addEventListener('change', render);
})();
</script>
</body>
</html>
'''


def main() -> int:
    catalog = json.loads(CAT.read_text(encoding="utf-8"))
    # compact embed
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
        html = HTML.replace("__CATALOG_JSON__", embed).replace("__CANONICAL__", canon)
        # fix relative catalog link in footer for each host
        html = html.replace('href="lygoskillhub_catalog.json"', f'href="{cat_href}"')
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        print("wrote", out, "bytes", out.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
