#!/usr/bin/env python3
"""
Listen portal v3 — deeper UX:
  sticky header + bio + sovereign vault tagline
  real search + smart filters (vocals/instrumental/feat/excavation/BPM)
  themed waveform visualizer + category sections
  favorites playlist + exportable ledger
  mini sticky player + donation progress
  BPMFINDER.CA highlight
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

EXCAV = Path(r"I:\E Drive\Excavationpro")
STACK = Path(r"I:\E Drive\lygo-protocol-stack")
LISTEN = EXCAV / "excavationpro-listen.html"
DOCS = STACK / "docs" / "excavationpro-listen.html"

V3_CSS = r"""
/* ===== LISTEN PORTAL v3 ===== */
body { padding-top: 0; }
.sticky-top {
  position: sticky; top: 0; z-index: 50;
  background: linear-gradient(180deg, rgba(8,8,16,.98) 0%, rgba(8,8,16,.94) 70%, rgba(8,8,16,.88) 100%);
  backdrop-filter: blur(12px); border-bottom: 1px solid rgba(212,175,55,.28);
  box-shadow: 0 8px 28px rgba(0,0,0,.45);
}
.sticky-top .wrap { padding-top: 10px; padding-bottom: 10px; }
.sticky-bio {
  display: flex; flex-wrap: wrap; gap: 12px 18px; align-items: flex-start;
  justify-content: space-between; margin-bottom: 8px;
}
.sticky-bio .who { max-width: 62ch; }
.sticky-bio .who h1 {
  font-family: Cinzel, serif; font-size: clamp(1.15rem, 2.5vw, 1.55rem);
  margin: 0 0 4px; color: var(--gold); letter-spacing: .02em;
}
.sticky-bio .tagline {
  display: inline-block; margin: 0 0 6px; padding: 3px 10px; border-radius: 999px;
  font-size: .72rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase;
  border: 1px solid rgba(0,240,255,.4); color: var(--cyan);
  background: rgba(0,240,255,.08);
}
.sticky-bio .bio {
  margin: 0; font-size: .82rem; color: var(--muted); line-height: 1.45;
}
.sticky-bio .tools { display: flex; flex-direction: column; gap: 8px; min-width: min(280px, 100%); }
.bpm-card {
  display: block; padding: 12px 14px; border-radius: 12px; text-decoration: none !important;
  border: 1px solid rgba(61,214,140,.5);
  background: linear-gradient(135deg, rgba(61,214,140,.16), rgba(0,240,255,.1));
  box-shadow: 0 0 20px rgba(61,214,140,.15);
  transition: transform .15s ease, border-color .15s;
}
.bpm-card:hover { transform: translateY(-1px); border-color: var(--gold); }
.bpm-card strong { display: block; color: var(--ok); font-size: .95rem; letter-spacing: .04em; }
.bpm-card span { display: block; color: var(--muted); font-size: .75rem; margin-top: 3px; line-height: 1.35; }
.donate-progress {
  padding: 10px 12px; border-radius: 10px;
  border: 1px solid rgba(0,112,186,.4); background: rgba(0,112,186,.12);
}
.donate-progress .lbl { display: flex; justify-content: space-between; font-size: .72rem; color: var(--muted); margin-bottom: 5px; }
.donate-progress .bar {
  height: 8px; border-radius: 999px; background: rgba(255,255,255,.08); overflow: hidden;
}
.donate-progress .bar i {
  display: block; height: 100%; width: 0%;
  background: linear-gradient(90deg, #0070ba, var(--cyan), var(--gold));
  transition: width .4s ease;
}
.donate-progress a { font-size: .75rem; color: #7ec8ff; }
.wave-shell {
  margin: 10px 0 12px; padding: 10px 12px; border-radius: 12px;
  border: 1px solid rgba(176,107,255,.25);
  background: radial-gradient(ellipse at 30% 50%, rgba(0,240,255,.08), transparent 55%),
              radial-gradient(ellipse at 70% 40%, rgba(176,107,255,.1), transparent 50%),
              rgba(8,8,16,.75);
}
.wave-shell canvas { width: 100%; height: 64px; display: block; border-radius: 8px; }
.wave-meta { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 6px; font-size: .72rem; color: var(--muted); }
.wave-meta .pill {
  padding: 2px 8px; border-radius: 999px; border: 1px solid rgba(255,255,255,.1);
}
.smart-filters {
  display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 10px; align-items: center;
}
.smart-filters button, .smart-filters select {
  cursor: pointer; border-radius: 999px; padding: 7px 12px; font-size: .76rem; font-weight: 600;
  border: 1px solid rgba(0,240,255,.28); background: rgba(12,12,22,.9); color: var(--muted);
}
.smart-filters button.on {
  border-color: var(--gold); color: var(--gold); background: rgba(212,175,55,.12);
}
.smart-filters button.tool-on {
  border-color: var(--ok); color: var(--ok); background: rgba(61,214,140,.12);
}
.section-heads { display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0 12px; }
.section-heads button {
  cursor: pointer; border-radius: 10px; padding: 8px 12px; font-size: .78rem; font-weight: 600;
  border: 1px solid rgba(176,107,255,.3); background: rgba(18,18,31,.9); color: var(--text);
}
.section-heads button.on { border-color: var(--cyan); color: var(--cyan); box-shadow: 0 0 12px rgba(0,240,255,.15); }
.cat-banner {
  margin: 8px 0; padding: 8px 12px; border-radius: 8px; font-size: .8rem;
  border-left: 3px solid var(--mag); background: rgba(176,107,255,.08); color: var(--muted);
}
.cat-banner b { color: var(--text); }
.fav-panel {
  margin: 10px 0 14px; padding: 12px 14px; border-radius: 12px;
  border: 1px solid rgba(255,107,157,.35); background: rgba(255,107,157,.06);
  display: none;
}
.fav-panel.open { display: block; }
.fav-panel h3 { margin: 0 0 8px; font-size: .95rem; color: #ff6b9d; font-family: Cinzel, serif; }
.fav-panel .fav-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
.fav-panel .fav-actions button {
  cursor: pointer; border-radius: 8px; padding: 7px 12px; font-size: .78rem; font-weight: 600;
  border: 1px solid rgba(255,107,157,.4); background: rgba(255,107,157,.12); color: var(--text);
}
.mini-player {
  position: fixed; left: 12px; right: 12px; bottom: calc(env(safe-area-inset-bottom, 0px) + 8px);
  z-index: 55; max-width: 520px; margin: 0 auto;
  display: none; align-items: center; gap: 10px;
  padding: 8px 12px; border-radius: 14px;
  border: 1px solid rgba(212,175,55,.4);
  background: rgba(12,12,22,.96); box-shadow: 0 8px 32px rgba(0,0,0,.55);
  backdrop-filter: blur(10px);
}
.mini-player.show { display: flex; }
.mini-player .mp-art {
  width: 40px; height: 40px; border-radius: 8px; flex-shrink: 0;
  background: linear-gradient(135deg, rgba(0,240,255,.35), rgba(176,107,255,.4), rgba(212,175,55,.3));
}
.mini-player .mp-info { flex: 1; min-width: 0; }
.mini-player .mp-title {
  font-size: .82rem; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  color: var(--text);
}
.mini-player .mp-sub { font-size: .68rem; color: var(--muted); }
.mini-player button {
  cursor: pointer; border: none; background: transparent; color: var(--gold);
  font-size: 1.1rem; padding: 4px 6px;
}
/* when mini shows, lift cookie banner */
body.has-mini .cookie-banner { bottom: 72px; }
body.has-mini .dock { opacity: .35; pointer-events: none; transition: opacity .2s; }
body.has-mini .dock:hover, body.has-mini .dock:focus-within { opacity: 1; pointer-events: auto; }
.nav-main a.tool {
  border-color: rgba(61,214,140,.55) !important;
  background: rgba(61,214,140,.14) !important;
  color: var(--ok) !important;
  font-weight: 700;
}
.live-pills a.bpm-pill {
  border-color: rgba(61,214,140,.55) !important;
  background: rgba(61,214,140,.16) !important;
  color: #9dffc8 !important;
  font-weight: 700;
}
"""

V3_HEADER_HTML = r"""
<div class="sticky-top" id="sticky-top">
  <div class="wrap sticky-bio">
    <div class="who">
      <div class="tagline">Δ9Φ963 · Sovereign Vault</div>
      <h1>Excavationpro — Listen Free</h1>
      <p class="bio">
        <strong style="color:var(--text)">Justin Helmer / Excavationpro / Lightfather</strong> —
        original music, vaulted by hash, streamed free. Built from years of solid production work.
        Own-work catalog · no DistroKid lock-in · lattice-backed ledger.
      </p>
    </div>
    <div class="tools">
      <a class="bpm-card" href="https://bpmfinder.ca/" target="_blank" rel="noopener" title="Free BPM Finder — our music tool">
        <strong>♪ BPMFINDER.CA</strong>
        <span>Free online tempo detector for MP3/WAV/FLAC — our tool for producers &amp; diggers. Detect song BPM fast.</span>
      </a>
      <div class="donate-progress" id="donate-progress" title="Community support toward hosting &amp; tools">
        <div class="lbl"><span>Support goal (hosting · streams · tools)</span><span id="donate-pct">0%</span></div>
        <div class="bar"><i id="donate-bar"></i></div>
        <div style="margin-top:6px;display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap">
          <a href="https://www.paypal.com/paypalme/ExcavationPro" target="_blank" rel="noopener">PayPal.me/ExcavationPro ↗</a>
          <button type="button" id="donate-cheer" style="cursor:pointer;border-radius:6px;border:1px solid rgba(0,112,186,.5);background:rgba(0,112,186,.2);color:#7ec8ff;font-size:.72rem;padding:4px 8px">I supported ✓</button>
        </div>
      </div>
    </div>
  </div>
</div>
"""

V3_WAVE_HTML = r"""
<div class="wave-shell" id="wave-shell" aria-hidden="false">
  <canvas id="wave-canvas" width="900" height="64" aria-label="Audio visualizer"></canvas>
  <div class="wave-meta">
    <span class="pill" id="wave-cat">All</span>
    <span class="pill" id="wave-count">— tracks</span>
    <span class="pill">Visualizer · live</span>
  </div>
</div>
"""

V3_SMART_FILTERS = r"""
<div class="smart-filters" id="smart-filters" role="toolbar" aria-label="Smart filters">
  <button type="button" data-smart="all" class="on">All types</button>
  <button type="button" data-smart="vocals">Vocals</button>
  <button type="button" data-smart="instrumental">Instrumental</button>
  <button type="button" data-smart="feat">Feat. Justin Helmer</button>
  <button type="button" data-smart="excavation">Excavation cuts</button>
  <button type="button" data-smart="bpm">Has BPM in title</button>
  <button type="button" data-smart="haven">Haven / books</button>
  <select id="bpm-band" aria-label="BPM band" title="When title contains BPM">
    <option value="">BPM band: any</option>
    <option value="slow">Slow (&lt;90)</option>
    <option value="mid">Mid (90–119)</option>
    <option value="up">Up (120–139)</option>
    <option value="fast">Fast (140+)</option>
  </select>
  <button type="button" id="btn-open-favs" class="tool-on">♥ Favorites panel</button>
  <button type="button" id="btn-export-favs">Export favorites ledger</button>
  <button type="button" id="btn-export-view">Export view ledger</button>
  <a href="https://bpmfinder.ca/" target="_blank" rel="noopener" class="bpm-card" style="padding:7px 12px;display:inline-block;border-radius:999px">
    <strong style="font-size:.76rem;display:inline">BPMFINDER.CA ↗</strong>
  </a>
</div>
<div class="section-heads" id="section-heads" role="tablist" aria-label="Categories">
  <button type="button" data-sec="all" class="on">All</button>
  <button type="button" data-sec="vocals">Vocals</button>
  <button type="button" data-sec="instrumental">Instrumentals</button>
  <button type="button" data-sec="feat">Feat. cuts</button>
  <button type="button" data-sec="excavation">Excavation</button>
  <button type="button" data-sec="haven">Haven books</button>
  <button type="button" data-sec="favorites">♥ Favorites</button>
</div>
<div class="cat-banner" id="cat-banner"><b>Library</b> — full sovereign stream pack</div>
<div class="fav-panel" id="fav-panel">
  <h3>♥ Favorites playlist <span id="fav-count" style="font-weight:400;color:var(--muted)"></span></h3>
  <p class="sub" style="margin:0;font-size:.8rem">Saved on this device only. Export ledger as JSON or CSV anytime.</p>
  <div class="fav-actions">
    <button type="button" id="fav-play-all">▶ Play favorites</button>
    <button type="button" id="fav-radio">📡 Radio favorites</button>
    <button type="button" id="fav-export-json">Export JSON ledger</button>
    <button type="button" id="fav-export-csv">Export CSV</button>
    <button type="button" id="fav-clear" style="border-color:rgba(255,77,109,.5)">Clear favorites</button>
  </div>
</div>
"""

V3_MINI_HTML = r"""
<div class="mini-player" id="mini-player" role="region" aria-label="Mini player">
  <div class="mp-art" aria-hidden="true"></div>
  <div class="mp-info">
    <div class="mp-title" id="mp-title">—</div>
    <div class="mp-sub" id="mp-sub">Excavationpro · sovereign stream</div>
  </div>
  <button type="button" id="mp-prev" title="Previous">⏮</button>
  <button type="button" id="mp-play" title="Play/Pause">▶</button>
  <button type="button" id="mp-next" title="Next">⏭</button>
  <button type="button" id="mp-expand" title="Open full dock">▲</button>
</div>
"""

V3_JS = r"""
/* ===== LISTEN PORTAL v3 ===== */
(function listenPortalV3() {
  const LS_FAV = 'lygo_listen_favorites_v1';
  const LS_DONATE = 'lygo_listen_donate_cheer_v1';
  const DONATE_GOAL = 100; // cheer units toward visual goal
  const BPM_RE = /\b(\d{2,3})\s*bpm\b/i;
  const HAVEN_RE = /haven|eternal\s*haven|audiobook|audio\s*book|book\s*\d|chapter\s*\d|lightfather|ascension\s*war|eternal\s*dawn|shattered\s*accord|rise\s*of\s*eleven/i;

  let smartFilter = 'all';
  let section = 'all';
  let bpmBand = '';
  let favs = loadFavs();
  let audioCtx = null;
  let analyser = null;
  let sourceNode = null;
  let raf = 0;
  let waveReady = false;

  function loadFavs() {
    try { return new Set(JSON.parse(localStorage.getItem(LS_FAV) || '[]')); }
    catch (e) { return new Set(); }
  }
  function saveFavs() {
    try { localStorage.setItem(LS_FAV, JSON.stringify([...favs])); } catch (e) {}
  }
  function trackKey(t) {
    return (t && (t.sha256 || t.stream_url || t.title)) || '';
  }
  function blobOf(t) {
    return [t.title, ...(t.aliases || []), ...(t.isrcs || [])].join(' ');
  }
  function classify(t) {
    const b = blobOf(t);
    const low = b.toLowerCase();
    const bpmM = b.match(BPM_RE);
    const bpm = bpmM ? parseInt(bpmM[1], 10) : null;
    const vocals = /vocal|acap|a\s*cap|hook|lyrics|sing/.test(low) && !/instrumental\s*only/.test(low);
    const instrumental = /instrumental|inst\.|beat\s*only|no\s*vocal|type\s*beat|prod\b/.test(low) && !vocals;
    const feat = /feat\.?\s*justin\s*helmer|ft\.?\s*justin\s*helmer|justin\s*helmer/.test(low);
    const excavation = /excavationpro|excavation\s*cut|xpro\b|expro\b/.test(low);
    const haven = HAVEN_RE.test(b);
    return { bpm, vocals, instrumental, feat, excavation, haven };
  }

  // Pre-index classifications
  const meta = tracks.map(t => classify(t));

  function toast(msg) {
    const host = document.getElementById('toast-host') || (() => {
      const d = document.createElement('div');
      d.id = 'toast-host';
      d.className = 'toast-host';
      document.body.appendChild(d);
      return d;
    })();
    const el = document.createElement('div');
    el.className = 'toast';
    el.textContent = msg;
    host.appendChild(el);
    setTimeout(() => el.remove(), 2800);
  }

  function matchSmart(i) {
    const t = tracks[i];
    const m = meta[i];
    if (smartFilter === 'vocals' && !m.vocals) return false;
    if (smartFilter === 'instrumental' && !m.instrumental) return false;
    if (smartFilter === 'feat' && !m.feat) return false;
    if (smartFilter === 'excavation' && !m.excavation) return false;
    if (smartFilter === 'bpm' && m.bpm == null) return false;
    if (smartFilter === 'haven' && !m.haven) return false;
    if (bpmBand && m.bpm != null) {
      if (bpmBand === 'slow' && !(m.bpm < 90)) return false;
      if (bpmBand === 'mid' && !(m.bpm >= 90 && m.bpm < 120)) return false;
      if (bpmBand === 'up' && !(m.bpm >= 120 && m.bpm < 140)) return false;
      if (bpmBand === 'fast' && !(m.bpm >= 140)) return false;
    } else if (bpmBand && m.bpm == null) {
      return false;
    }
    if (section === 'vocals' && !m.vocals) return false;
    if (section === 'instrumental' && !m.instrumental) return false;
    if (section === 'feat' && !m.feat) return false;
    if (section === 'excavation' && !m.excavation) return false;
    if (section === 'haven' && !m.haven) return false;
    if (section === 'favorites' && !favs.has(trackKey(t))) return false;
    return true;
  }

  // Wrap rebuildFilter if present
  const prevRebuild = window.rebuildFilter;
  window.rebuildFilter = function rebuildFilterV3() {
    if (typeof prevRebuild === 'function') {
      // call core rebuild then re-filter — but core may overwrite filteredIdx
      // Safer: implement full rebuild here using same sources
    }
    const q = (document.getElementById('q') && document.getElementById('q').value || '').toLowerCase().trim();
    const f = (document.getElementById('filter') && document.getElementById('filter').value) || 'all';
    const sort = (document.getElementById('sort') && document.getElementById('sort').value) || 'title';
    let idx = tracks.map((_, i) => i);
    if (f === 'isrc') idx = idx.filter(i => (tracks[i].isrcs || []).length);
    if (f === 'playable') idx = idx.filter(i => tracks[i].stream_url);
    // library chips from v2 (if present)
    const chipOn = document.querySelector('#filter-chips [data-lib].on');
    const lib = chipOn ? chipOn.getAttribute('data-lib') : 'all';
    if (lib === 'haven') idx = idx.filter(i => meta[i].haven);
    else if (lib === 'music') idx = idx.filter(i => !meta[i].haven);
    else if (lib === 'favorites') idx = idx.filter(i => favs.has(trackKey(tracks[i])));
    else if (lib === 'queue') {
      // leave to v2 if queue global exists
      try {
        const qlist = JSON.parse(localStorage.getItem('lygo_listen_queue_v1') || '[]');
        const byKey = new Map(tracks.map((t, i) => [trackKey(t), i]));
        idx = qlist.map(k => byKey.get(k)).filter(i => i != null);
      } catch (e) {}
    }
    idx = idx.filter(i => matchSmart(i));
    if (q) {
      idx = idx.filter(i => {
        const t = tracks[i];
        const m = meta[i];
        const hay = [t.title, t.sha256, ...(t.isrcs || []), ...(t.aliases || []),
          m.bpm != null ? m.bpm + ' bpm' : '',
          m.vocals ? 'vocals' : '', m.instrumental ? 'instrumental' : '',
          m.feat ? 'justin helmer' : '', m.excavation ? 'excavationpro' : ''
        ].join(' ').toLowerCase();
        return hay.includes(q);
      });
    }
    if (lib !== 'queue') {
      idx.sort((a, b) => {
        const ta = tracks[a], tb = tracks[b];
        if (sort === 'title-desc') return (tb.title || '').localeCompare(ta.title || '');
        if (sort === 'size') return (tb.size || 0) - (ta.size || 0);
        if (sort === 'isrc') return ((tb.isrcs || []).length ? 1 : 0) - ((ta.isrcs || []).length ? 1 : 0) || (ta.title || '').localeCompare(tb.title || '');
        return (ta.title || '').localeCompare(tb.title || '');
      });
    }
    filteredIdx = idx;
    if (typeof radio !== 'undefined' && (radio || (typeof shuffle !== 'undefined' && shuffle))) {
      if (typeof refillBag === 'function') refillBag(current);
    }
    updateCatBanner();
    if (typeof renderList === 'function') renderList();
    else if (typeof window.renderList === 'function') window.renderList();
  };

  function updateCatBanner() {
    const el = document.getElementById('cat-banner');
    const wc = document.getElementById('wave-count');
    const wcat = document.getElementById('wave-cat');
    const n = filteredIdx.length;
    const labels = {
      all: 'Full library', vocals: 'Vocals', instrumental: 'Instrumentals',
      feat: 'Feat. Justin Helmer', excavation: 'Excavation cuts',
      haven: 'Haven / book audio', favorites: 'Favorites', bpm: 'BPM-tagged titles'
    };
    const lab = labels[section] || labels[smartFilter] || 'Library';
    if (el) el.innerHTML = '<b>' + lab + '</b> — ' + n + ' track' + (n === 1 ? '' : 's') + ' · sovereign streams';
    if (wc) wc.textContent = n + ' tracks';
    if (wcat) wcat.textContent = lab;
    const fc = document.getElementById('fav-count');
    if (fc) fc.textContent = '(' + favs.size + ')';
  }

  // Smart filter buttons
  document.querySelectorAll('#smart-filters [data-smart]').forEach(btn => {
    btn.addEventListener('click', () => {
      smartFilter = btn.getAttribute('data-smart') || 'all';
      document.querySelectorAll('#smart-filters [data-smart]').forEach(b => b.classList.toggle('on', b === btn));
      window.rebuildFilter();
    });
  });
  document.querySelectorAll('#section-heads [data-sec]').forEach(btn => {
    btn.addEventListener('click', () => {
      section = btn.getAttribute('data-sec') || 'all';
      document.querySelectorAll('#section-heads [data-sec]').forEach(b => b.classList.toggle('on', b === btn));
      if (section === 'favorites') {
        const p = document.getElementById('fav-panel');
        if (p) p.classList.add('open');
      }
      window.rebuildFilter();
    });
  });
  const bpmSel = document.getElementById('bpm-band');
  if (bpmSel) bpmSel.addEventListener('change', () => {
    bpmBand = bpmSel.value || '';
    window.rebuildFilter();
  });

  // Favorites panel
  document.getElementById('btn-open-favs')?.addEventListener('click', () => {
    document.getElementById('fav-panel')?.classList.toggle('open');
  });
  document.getElementById('fav-play-all')?.addEventListener('click', () => {
    section = 'favorites'; smartFilter = 'all';
    document.querySelectorAll('#section-heads [data-sec]').forEach(b => b.classList.toggle('on', b.getAttribute('data-sec') === 'favorites'));
    window.rebuildFilter();
    if (filteredIdx.length && typeof playIndex === 'function') playIndex(filteredIdx[0]);
    else toast('No favorites yet — heart some tracks');
  });
  document.getElementById('fav-radio')?.addEventListener('click', () => {
    section = 'favorites';
    window.rebuildFilter();
    if (!filteredIdx.length) return toast('No favorites yet');
    if (typeof toggleRadio === 'function' && !radio) toggleRadio();
    else if (typeof nextTrack === 'function') nextTrack(1);
    toast('♥ Radio · favorites');
  });
  document.getElementById('fav-clear')?.addEventListener('click', () => {
    if (!confirm('Clear all favorites on this device?')) return;
    favs.clear(); saveFavs();
    window.rebuildFilter();
    toast('Favorites cleared');
  });

  function ledgerRows(indices) {
    return indices.map(i => {
      const t = tracks[i];
      const m = meta[i];
      return {
        title: t.title,
        sha256: t.sha256,
        isrcs: t.isrcs || [],
        size: t.size,
        stream_url: t.stream_url || null,
        bpm_in_title: m.bpm,
        tags: {
          vocals: m.vocals,
          instrumental: m.instrumental,
          feat_justin_helmer: m.feat,
          excavation: m.excavation,
          haven: m.haven,
        },
        page: location.origin + location.pathname + '#' + (t.sha256 || i),
      };
    });
  }
  function downloadBlob(name, text, mime) {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([text], { type: mime }));
    a.download = name;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  }
  function exportJson(indices, name) {
    const payload = {
      signature: 'Δ9Φ963-EXCAVATIONPRO-LISTEN-LEDGER-v1',
      artist: 'Excavationpro',
      steward: 'Justin Helmer / Lightfather',
      exported_at: new Date().toISOString(),
      count: indices.length,
      tracks: ledgerRows(indices),
      note: 'Own-work sovereign stream ledger export (client-side).',
    };
    downloadBlob(name, JSON.stringify(payload, null, 2), 'application/json');
    toast('Exported ' + indices.length + ' tracks (JSON)');
  }
  function exportCsv(indices, name) {
    const rows = [['title', 'sha256', 'isrc', 'bpm', 'vocals', 'instrumental', 'feat', 'excavation', 'haven', 'stream_url', 'page']];
    ledgerRows(indices).forEach(r => {
      rows.push([
        r.title, r.sha256, (r.isrcs || []).join(';'), r.bpm_in_title ?? '',
        r.tags.vocals, r.tags.instrumental, r.tags.feat_justin_helmer,
        r.tags.excavation, r.tags.haven, r.stream_url || '', r.page
      ].map(x => '"' + String(x).replace(/"/g, '""') + '"'));
    });
    downloadBlob(name, rows.map(r => r.join(',')).join('\n'), 'text/csv');
    toast('Exported ' + indices.length + ' tracks (CSV)');
  }
  document.getElementById('fav-export-json')?.addEventListener('click', () => {
    const idx = tracks.map((_, i) => i).filter(i => favs.has(trackKey(tracks[i])));
    if (!idx.length) return toast('No favorites');
    exportJson(idx, 'excavationpro-favorites-ledger.json');
  });
  document.getElementById('fav-export-csv')?.addEventListener('click', () => {
    const idx = tracks.map((_, i) => i).filter(i => favs.has(trackKey(tracks[i])));
    if (!idx.length) return toast('No favorites');
    exportCsv(idx, 'excavationpro-favorites-ledger.csv');
  });
  document.getElementById('btn-export-favs')?.addEventListener('click', () => {
    document.getElementById('fav-export-json')?.click();
  });
  document.getElementById('btn-export-view')?.addEventListener('click', () => {
    exportJson(filteredIdx.slice(), 'excavationpro-view-ledger.json');
  });

  // Sync hearts with fav set when v2 toggles — re-read storage on focus
  window.addEventListener('storage', () => { favs = loadFavs(); updateCatBanner(); });
  // Hook heart clicks via MutationObserver is heavy; poll fav storage after clicks
  document.addEventListener('click', (e) => {
    if (e.target.closest && (e.target.closest('[data-heart]') || e.target.closest('#btn-fav'))) {
      setTimeout(() => { favs = loadFavs(); updateCatBanner(); }, 50);
    }
  });

  // --- Waveform visualizer ---
  function ensureAnalyser() {
    if (waveReady) return;
    try {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC || !audio) return;
      audioCtx = new AC();
      analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      sourceNode = audioCtx.createMediaElementSource(audio);
      sourceNode.connect(analyser);
      analyser.connect(audioCtx.destination);
      waveReady = true;
    } catch (e) {
      console.warn('visualizer', e);
    }
  }
  function drawWave() {
    const canvas = document.getElementById('wave-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    // background grid
    ctx.fillStyle = 'rgba(0,0,0,.25)';
    ctx.fillRect(0, 0, w, h);
    if (!analyser || audio.paused) {
      // idle sine
      ctx.strokeStyle = 'rgba(0,240,255,.45)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      const t = Date.now() / 500;
      for (let x = 0; x < w; x++) {
        const y = h / 2 + Math.sin(x / 28 + t) * 10 + Math.sin(x / 11 + t * 1.3) * 4;
        if (x === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }
      ctx.stroke();
      raf = requestAnimationFrame(drawWave);
      return;
    }
    const buf = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(buf);
    const barW = w / buf.length * 1.8;
    for (let i = 0; i < buf.length; i++) {
      const v = buf[i] / 255;
      const bh = v * (h - 4);
      const g = ctx.createLinearGradient(0, h - bh, 0, h);
      g.addColorStop(0, 'rgba(0,240,255,.9)');
      g.addColorStop(0.5, 'rgba(176,107,255,.7)');
      g.addColorStop(1, 'rgba(212,175,55,.5)');
      ctx.fillStyle = g;
      ctx.fillRect(i * barW, h - bh, barW - 1, bh);
    }
    raf = requestAnimationFrame(drawWave);
  }
  drawWave();
  audio.addEventListener('play', () => {
    ensureAnalyser();
    if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
  });

  // --- Mini player ---
  function updateMini() {
    const mini = document.getElementById('mini-player');
    const t = current >= 0 ? tracks[current] : null;
    if (!mini) return;
    if (t && !audio.paused) {
      mini.classList.add('show');
      document.body.classList.add('has-mini');
      const mt = document.getElementById('mp-title');
      const ms = document.getElementById('mp-sub');
      if (mt) mt.textContent = t.title || '—';
      if (ms) {
        const m = meta[current] || {};
        const bits = ['Excavationpro'];
        if (m.bpm) bits.push(m.bpm + ' BPM');
        if (m.vocals) bits.push('vocals');
        if (m.instrumental) bits.push('instrumental');
        ms.textContent = bits.join(' · ');
      }
      const pb = document.getElementById('mp-play');
      if (pb) pb.textContent = '⏸';
    } else if (t && audio.paused) {
      mini.classList.add('show');
      document.body.classList.add('has-mini');
      const pb = document.getElementById('mp-play');
      if (pb) pb.textContent = '▶';
    } else {
      mini.classList.remove('show');
      document.body.classList.remove('has-mini');
    }
  }
  audio.addEventListener('play', updateMini);
  audio.addEventListener('pause', updateMini);
  document.getElementById('mp-play')?.addEventListener('click', () => {
    if (audio.paused) audio.play().catch(() => {});
    else audio.pause();
  });
  document.getElementById('mp-next')?.addEventListener('click', () => { if (typeof nextTrack === 'function') nextTrack(1); });
  document.getElementById('mp-prev')?.addEventListener('click', () => { if (typeof nextTrack === 'function') nextTrack(-1); });
  document.getElementById('mp-expand')?.addEventListener('click', () => {
    document.querySelector('.dock')?.scrollIntoView({ behavior: 'smooth', block: 'end' });
    document.body.classList.remove('has-mini');
  });

  // --- Donation progress (cheer units — honest local progress, not claimed $) ---
  function renderDonate() {
    let n = 0;
    try { n = parseInt(localStorage.getItem(LS_DONATE) || '0', 10) || 0; } catch (e) {}
    const pct = Math.min(100, Math.round((n / DONATE_GOAL) * 100));
    const bar = document.getElementById('donate-bar');
    const lab = document.getElementById('donate-pct');
    if (bar) bar.style.width = pct + '%';
    if (lab) lab.textContent = pct + '% · ' + n + ' cheers';
  }
  document.getElementById('donate-cheer')?.addEventListener('click', () => {
    let n = 0;
    try { n = parseInt(localStorage.getItem(LS_DONATE) || '0', 10) || 0; } catch (e) {}
    n += 1;
    try { localStorage.setItem(LS_DONATE, String(n)); } catch (e) {}
    renderDonate();
    toast('Thank you — cheer logged on this device');
  });
  renderDonate();

  // Highlight BPM in nav
  const nav = document.getElementById('nav-main');
  if (nav && !nav.innerHTML.includes('BPMFINDER')) {
    const a = document.createElement('a');
    a.href = 'https://bpmfinder.ca/';
    a.target = '_blank';
    a.rel = 'noopener';
    a.className = 'tool';
    a.textContent = '♪ BPMFINDER.CA';
    nav.insertBefore(a, nav.firstChild?.nextSibling || null);
  }
  // live pills
  const pills = document.querySelector('.live-pills');
  if (pills && !pills.innerHTML.includes('BPMFINDER')) {
    const a = document.createElement('a');
    a.href = 'https://bpmfinder.ca/';
    a.target = '_blank';
    a.rel = 'noopener';
    a.className = 'bpm-pill';
    a.textContent = '♪ BPMFINDER.CA';
    pills.appendChild(a);
  }

  // Rebind search
  const qEl = document.getElementById('q');
  if (qEl) {
    qEl.placeholder = 'Search title, ISRC, hash, vocals, instrumental, feat, BPM…';
    qEl.oninput = () => window.rebuildFilter();
  }
  const sortEl = document.getElementById('sort');
  const filterEl = document.getElementById('filter');
  if (sortEl) sortEl.onchange = () => window.rebuildFilter();
  if (filterEl) filterEl.onchange = () => window.rebuildFilter();
  document.querySelectorAll('#filter-chips [data-lib]').forEach(btn => {
    btn.addEventListener('click', () => setTimeout(() => window.rebuildFilter(), 0));
  });

  // Soft-hide duplicate old hero h1 if sticky present
  const hero = document.querySelector('header.hero');
  if (hero && document.getElementById('sticky-top')) {
    const h1 = hero.querySelector('h1');
    if (h1) h1.style.display = 'none';
    const sub = hero.querySelector('p.sub');
    if (sub) sub.style.display = 'none';
  }

  favs = loadFavs();
  window.rebuildFilter();
  console.info('[listen-v3] sticky · smart filters · waveform · fav export · mini player · donate · BPMFINDER.CA');
})();
/* ===== END v3 ===== */
"""


def inject_css(html: str) -> str:
    if "LISTEN PORTAL v3" in html and "sticky-top" in html and "/* ===== LISTEN PORTAL v3 ===== */" in html:
        # replace CSS block
        html = re.sub(
            r"/\* ===== LISTEN PORTAL v3 ===== \*/[\s\S]*?(?=\n</style>)",
            V3_CSS.strip() + "\n",
            html,
            count=1,
        )
        return html
    idx = html.find("</style>")
    if idx < 0:
        raise SystemExit("no style")
    return html[:idx] + "\n" + V3_CSS + "\n" + html[idx:]


def inject_header(html: str) -> str:
    if 'id="sticky-top"' in html:
        html = re.sub(
            r'<div class="sticky-top" id="sticky-top">[\s\S]*?</div>\s*</div>\s*',
            V3_HEADER_HTML.strip() + "\n",
            html,
            count=1,
        )
        return html
    # after <body>
    return html.replace("<body>", "<body>\n" + V3_HEADER_HTML, 1)


def inject_wave_and_filters(html: str) -> str:
    if 'id="smart-filters"' in html:
        # replace smart filters block
        html = re.sub(
            r'<div class="wave-shell"[\s\S]*?<div class="fav-panel"[\s\S]*?</div>\s*',
            V3_WAVE_HTML.strip() + "\n" + V3_SMART_FILTERS.strip() + "\n",
            html,
            count=1,
        )
        return html
    # after filter-chips or before list
    if 'id="filter-chips"' in html:
        html = html.replace(
            'id="filter-chips"',
            'id="filter-chips"',
            1,
        )
        # insert after filter-chips closing div — find first filter-chips block end
        m = re.search(r'(<div class="filter-chips"[\s\S]*?</div>)', html)
        if m:
            insert_at = m.end()
            return html[:insert_at] + "\n" + V3_WAVE_HTML + "\n" + V3_SMART_FILTERS + html[insert_at:]
    needle = '<div class="list" id="list">'
    if needle in html:
        return html.replace(
            needle,
            V3_WAVE_HTML + "\n" + V3_SMART_FILTERS + "\n" + needle,
            1,
        )
    raise SystemExit("cannot place filters")


def inject_mini(html: str) -> str:
    if 'id="mini-player"' in html:
        html = re.sub(
            r'<div class="mini-player"[\s\S]*?</div>\s*',
            V3_MINI_HTML.strip() + "\n",
            html,
            count=1,
        )
        return html
    return html.replace("</body>", V3_MINI_HTML + "\n</body>", 1)


def inject_js(html: str) -> str:
    if "LISTEN PORTAL v3" in html:
        html = re.sub(
            r"/\* ===== LISTEN PORTAL v3 ===== \*/[\s\S]*?/\* ===== END v3 ===== \*/\s*",
            "",
            html,
            count=1,
        )
    end = html.rfind("</script>")
    if end < 0:
        raise SystemExit("no script end")
    return html[:end] + "\n" + V3_JS + "\n" + html[end:]


def inject_live_pills_bpm(html: str) -> str:
    old = """  <div class="live-pills" aria-label="Live streaming portals">
    <a href="https://kick.com/excavationpro" target="_blank" rel="noopener">● Kick Live</a>
    <a href="https://rumble.com/user/excavationpro/live" target="_blank" rel="noopener">● Rumble Live</a>
    <a href="https://twitch.tv/excavationpro" target="_blank" rel="noopener">● Twitch Live</a>
  </div>"""
    new = """  <div class="live-pills" aria-label="Live streaming portals and tools">
    <a href="https://kick.com/excavationpro" target="_blank" rel="noopener">● Kick Live</a>
    <a href="https://rumble.com/user/excavationpro/live" target="_blank" rel="noopener">● Rumble Live</a>
    <a href="https://twitch.tv/excavationpro" target="_blank" rel="noopener">● Twitch Live</a>
    <a class="bpm-pill" href="https://bpmfinder.ca/" target="_blank" rel="noopener">♪ BPMFINDER.CA</a>
  </div>"""
    if "BPMFINDER.CA" not in html.split("live-pills")[1][:800] if "live-pills" in html else True:
        if old in html:
            html = html.replace(old, new, 1)
        elif "bpmfinder.ca" not in html.lower() or "live-pills" in html:
            # try inject into live-pills before close
            html = re.sub(
                r'(<div class="live-pills"[^>]*>)([\s\S]*?)(</div>)',
                lambda m: m.group(1)
                + m.group(2)
                + (
                    ""
                    if "bpmfinder.ca" in m.group(2).lower()
                    else '\n    <a class="bpm-pill" href="https://bpmfinder.ca/" target="_blank" rel="noopener">♪ BPMFINDER.CA</a>\n    '
                )
                + m.group(3),
                html,
                count=1,
            )
    return html


def main() -> int:
    html = LISTEN.read_text(encoding="utf-8")
    html = inject_css(html)
    html = inject_header(html)
    html = inject_live_pills_bpm(html)
    html = inject_wave_and_filters(html)
    html = inject_mini(html)
    html = inject_js(html)
    LISTEN.write_text(html, encoding="utf-8")
    print(f"[ok] {LISTEN} ({len(html):,})")
    DOCS.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(LISTEN, DOCS)
    print(f"[ok] synced {DOCS}")
    checks = [
        "sticky-top",
        "Sovereign Vault",
        "BPMFINDER.CA",
        "smart-filters",
        "wave-canvas",
        "fav-export-json",
        "mini-player",
        "donate-progress",
        "LISTEN PORTAL v3",
    ]
    t = LISTEN.read_text(encoding="utf-8")
    for c in checks:
        ok = c in t
        print(("OK" if ok else "FAIL"), c)
        if not ok:
            return 1
    print("V3 READY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
