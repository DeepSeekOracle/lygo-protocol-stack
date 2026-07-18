#!/usr/bin/env python3
"""
Enhance excavationpro-listen.html with:
  Media Session, sleep timer, crossfade, favorites/queue,
  Haven filter, share card, PWA install.
Also writes PWA assets and syncs docs + generator markers.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

EXCAV = Path(r"I:\E Drive\Excavationpro")
STACK = Path(r"I:\E Drive\lygo-protocol-stack")
LISTEN = EXCAV / "excavationpro-listen.html"
DOCS = STACK / "docs" / "excavationpro-listen.html"

# ---------------------------------------------------------------------------
# Extra CSS
# ---------------------------------------------------------------------------
EXTRA_CSS = r"""
/* --- v2 enhancements: radio polish / favs / PWA --- */
.filter-chips { display:flex; flex-wrap:wrap; gap:8px; margin:0 0 10px; align-items:center; }
.filter-chips button {
  cursor:pointer; border-radius:999px; padding:7px 12px; font-size:.78rem; font-weight:600;
  border:1px solid rgba(0,240,255,.28); background:rgba(12,12,22,.9); color:var(--muted);
}
.filter-chips button.on { border-color:var(--gold); color:var(--gold); background:rgba(212,175,55,.12); }
.filter-chips button.haven.on { border-color:var(--mag); color:var(--mag); background:rgba(176,107,255,.14); }
.filter-chips button.fav.on { border-color:#ff6b9d; color:#ff6b9d; background:rgba(255,107,157,.12); }
.row button.heart {
  cursor:pointer; border:none; background:transparent; color:var(--muted); font-size:1.05rem; padding:4px 6px;
}
.row button.heart.on { color:#ff6b9d; }
.row { grid-template-columns:44px 1fr auto auto auto; }
.dock { padding-bottom: env(safe-area-inset-bottom, 0); }
.dock-extra {
  display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin:6px 0 4px;
  font-size:.78rem; color:var(--muted);
}
.dock-extra label { display:inline-flex; align-items:center; gap:6px; cursor:pointer; user-select:none; }
.dock-extra select, .dock-extra button.mini {
  cursor:pointer; border-radius:8px; border:1px solid rgba(0,240,255,.3);
  background:#0c0c16; color:var(--text); padding:6px 10px; font-size:.78rem;
}
.dock-extra button.mini.on { border-color:var(--gold); color:var(--gold); }
.dock-extra button.mini.hot.on { border-color:#ff6b9d; color:#ff6b9d; }
.progress-wrap { display:flex; align-items:center; gap:8px; margin-top:4px; }
.progress-wrap input[type=range] { flex:1; accent-color:var(--cyan); }
.progress-wrap .t { font-size:.72rem; color:var(--muted); font-variant-numeric:tabular-nums; min-width:88px; text-align:right; }
.vol-wrap { display:inline-flex; align-items:center; gap:6px; }
.vol-wrap input[type=range] { width:90px; accent-color:var(--gold); }
.share-modal, .toast-host {
  position:fixed; z-index:80; left:50%; transform:translateX(-50%);
}
.share-modal {
  bottom:120px; width:min(440px,92vw); background:rgba(12,12,22,.98);
  border:1px solid rgba(212,175,55,.45); border-radius:14px; padding:16px 18px;
  box-shadow:0 12px 40px rgba(0,0,0,.55); display:none;
}
.share-modal.open { display:block; }
.share-modal h3 { margin:0 0 8px; font-family:Cinzel,serif; color:var(--gold); font-size:1rem; }
.share-modal p { margin:0 0 10px; color:var(--muted); font-size:.84rem; line-height:1.45; word-break:break-word; }
.share-modal .actions { display:flex; flex-wrap:wrap; gap:8px; }
.share-modal .actions button {
  cursor:pointer; border-radius:8px; padding:8px 12px; font-weight:600; font-size:.82rem;
  border:1px solid rgba(0,240,255,.35); background:rgba(0,240,255,.12); color:var(--text);
}
.share-modal .actions button.pri { border-color:rgba(212,175,55,.5); color:var(--gold); }
.toast-host { bottom:100px; pointer-events:none; }
.toast {
  background:rgba(18,18,31,.96); border:1px solid rgba(0,240,255,.35); color:var(--text);
  padding:10px 14px; border-radius:10px; font-size:.82rem; margin-top:6px;
  box-shadow:0 6px 20px rgba(0,0,0,.4); animation:fadeToast 2.8s ease forwards;
}
@keyframes fadeToast { 0%{opacity:0;transform:translateY(8px)} 12%{opacity:1;transform:none} 80%{opacity:1} 100%{opacity:0} }
.pwa-install {
  display:none; cursor:pointer; border-radius:8px; padding:7px 12px; font-size:.78rem; font-weight:700;
  border:1px solid rgba(61,214,140,.45); background:rgba(61,214,140,.12); color:var(--ok);
}
.pwa-install.show { display:inline-flex; align-items:center; gap:6px; }
.sleep-bar {
  height:3px; background:rgba(255,255,255,.08); border-radius:2px; margin-top:6px; overflow:hidden; display:none;
}
.sleep-bar.on { display:block; }
.sleep-bar i { display:block; height:100%; width:100%; background:linear-gradient(90deg,var(--mag),var(--cyan)); transform-origin:left; }
"""

# ---------------------------------------------------------------------------
# Extra HTML (injected before dock / after toolbar)
# ---------------------------------------------------------------------------
FILTER_CHIPS_HTML = r"""
    <div class="filter-chips" id="filter-chips" role="toolbar" aria-label="Library filters">
      <button type="button" class="on" data-lib="all">All</button>
      <button type="button" data-lib="music">Music</button>
      <button type="button" class="haven" data-lib="haven">Haven books</button>
      <button type="button" class="fav" data-lib="favorites">♥ Favorites</button>
      <button type="button" data-lib="queue">Queue</button>
      <button type="button" id="btn-pwa-install" class="pwa-install" title="Install app">⬇ Install</button>
    </div>
"""

DOCK_EXTRA_HTML = r"""
    <div class="dock-extra">
      <button type="button" class="mini" id="btn-fav" title="Favorite (F)">♡ Fav</button>
      <button type="button" class="mini" id="btn-queue-add" title="Add to queue">＋ Queue</button>
      <button type="button" class="mini" id="btn-share" title="Share track">Share</button>
      <label class="vol-wrap" title="Volume">🔊 <input type="range" id="vol" min="0" max="1" step="0.01" value="1"></label>
      <label title="Crossfade between tracks"><input type="checkbox" id="xfade"> Crossfade</label>
      <label title="Sleep timer">Sleep
        <select id="sleep-sel">
          <option value="0">Off</option>
          <option value="15">15 min</option>
          <option value="30">30 min</option>
          <option value="45">45 min</option>
          <option value="60">60 min</option>
          <option value="90">90 min</option>
        </select>
      </label>
      <button type="button" class="mini hot" id="btn-radio-fav" title="Radio from favorites only">♥ Radio</button>
    </div>
    <div class="progress-wrap">
      <input type="range" id="seek" min="0" max="1000" value="0" aria-label="Seek">
      <span class="t" id="time-label">0:00 / 0:00</span>
    </div>
    <div class="sleep-bar" id="sleep-bar"><i id="sleep-fill"></i></div>
"""

MODALS_HTML = r"""
<div class="share-modal" id="share-modal" role="dialog" aria-label="Share track">
  <h3 id="share-title">Share track</h3>
  <p id="share-body"></p>
  <div class="actions">
    <button type="button" class="pri" id="share-copy-page">Copy page link</button>
    <button type="button" id="share-copy-stream">Copy stream URL</button>
    <button type="button" id="share-native">System share…</button>
    <button type="button" id="share-close">Close</button>
  </div>
</div>
<div class="toast-host" id="toast-host" aria-live="polite"></div>
"""

# ---------------------------------------------------------------------------
# Enhancement JS — appended before final </script> of main player
# Uses window hooks and monkey-patches existing functions carefully
# ---------------------------------------------------------------------------
ENHANCE_JS = r"""
/* ===== LISTEN PORTAL v2 ENHANCEMENTS ===== */
(function enhanceListenV2() {
  const LS_FAV = 'lygo_listen_favorites_v1';
  const LS_QUEUE = 'lygo_listen_queue_v1';
  const LS_XFADE = 'lygo_listen_xfade_v1';
  const LS_VOL = 'lygo_listen_vol_v1';

  const HAVEN_RE = /haven|eternal\s*haven|audiobook|audio\s*book|book\s*\d|chapter\s*\d|lightfather|ascension\s*war|eternal\s*dawn|shattered\s*accord|rise\s*of\s*eleven|void\s*atlas|mathematical\s*ascen|matrix\s*website|lygo\s*book|codex\s*(volume|vol)|enoch\s*codex|trauma\s*codex/i;

  let libFilter = 'all'; // all | music | haven | favorites | queue
  let favs = loadSet(LS_FAV);
  let queue = loadList(LS_QUEUE);
  let sleepTimer = null;
  let sleepEndsAt = 0;
  let sleepRaf = 0;
  let xfadeOn = localStorage.getItem(LS_XFADE) === '1';
  let seeking = false;
  let radioFavOnly = false;
  let audioB = null; // secondary for crossfade
  let fading = false;

  function loadSet(k) {
    try { return new Set(JSON.parse(localStorage.getItem(k) || '[]')); } catch (e) { return new Set(); }
  }
  function saveSet(k, s) {
    try { localStorage.setItem(k, JSON.stringify([...s])); } catch (e) {}
  }
  function loadList(k) {
    try { return JSON.parse(localStorage.getItem(k) || '[]'); } catch (e) { return []; }
  }
  function saveList(k, a) {
    try { localStorage.setItem(k, JSON.stringify(a)); } catch (e) {}
  }

  function toast(msg) {
    const host = document.getElementById('toast-host');
    if (!host) return;
    const el = document.createElement('div');
    el.className = 'toast';
    el.textContent = msg;
    host.appendChild(el);
    setTimeout(() => el.remove(), 3000);
  }

  function isHavenTrack(t) {
    if (!t) return false;
    const blob = [t.title, ...(t.aliases || []), t.sha256 || ''].join(' ');
    return HAVEN_RE.test(blob);
  }

  function trackKey(t) {
    return (t && (t.sha256 || t.stream_url || t.title)) || '';
  }

  function isFav(t) {
    return t && favs.has(trackKey(t));
  }

  // --- wrap rebuildFilter to apply lib filter ---
  const _rebuildFilter = window.rebuildFilter || rebuildFilter;
  window.rebuildFilter = function rebuildFilterWrapped() {
    // call original logic by re-implementing with lib filter
    const q = (document.getElementById('q').value || '').toLowerCase().trim();
    const f = document.getElementById('filter').value;
    const sort = document.getElementById('sort').value;
    let idx = tracks.map((_, i) => i);
    if (f === 'isrc') idx = idx.filter(i => (tracks[i].isrcs || []).length);
    if (f === 'playable') idx = idx.filter(i => tracks[i].stream_url);

    if (libFilter === 'haven') idx = idx.filter(i => isHavenTrack(tracks[i]));
    else if (libFilter === 'music') idx = idx.filter(i => !isHavenTrack(tracks[i]));
    else if (libFilter === 'favorites') idx = idx.filter(i => isFav(tracks[i]));
    else if (libFilter === 'queue') {
      const order = queue.slice();
      const byKey = new Map(tracks.map((t, i) => [trackKey(t), i]));
      idx = order.map(k => byKey.get(k)).filter(i => i != null);
    }

    if (q) {
      idx = idx.filter(i => {
        const t = tracks[i];
        return [t.title, t.sha256, ...(t.isrcs || []), ...(t.aliases || [])].join(' ').toLowerCase().includes(q);
      });
    }
    if (libFilter !== 'queue') {
      idx.sort((a, b) => {
        const ta = tracks[a], tb = tracks[b];
        if (sort === 'title-desc') return (tb.title || '').localeCompare(ta.title || '');
        if (sort === 'size') return (tb.size || 0) - (ta.size || 0);
        if (sort === 'isrc') return ((tb.isrcs || []).length ? 1 : 0) - ((ta.isrcs || []).length ? 1 : 0) || (ta.title || '').localeCompare(tb.title || '');
        return (ta.title || '').localeCompare(tb.title || '');
      });
    }
    filteredIdx = idx;
    if (typeof radio !== 'undefined' && (radio || shuffle)) {
      if (typeof refillBag === 'function') refillBag(current);
    }
    renderListEnhanced();
  };

  // --- enhanced list with hearts ---
  function renderListEnhanced() {
    const el = document.getElementById('list');
    if (!el) return;
    el.innerHTML = filteredIdx.map((i, n) => {
      const t = tracks[i];
      const on = i === current ? 'on' : '';
      const can = !!t.stream_url;
      const heart = isFav(t) ? '♥' : '♡';
      const hon = isFav(t) ? 'on' : '';
      return `<div class="row ${on}" data-i="${i}">
      <div class="n">${n + 1}</div>
      <div>
        <div class="title">${esc(t.title)}</div>
        <div class="meta">${(t.isrcs || []).slice(0, 2).map(x => `<span class="badge">${esc(x)}</span>`).join('')}${t.sha256 ? esc(t.sha256.slice(0, 12)) + '…' : ''}${isHavenTrack(t) ? ' <span class="badge" style="background:rgba(176,107,255,.15);color:var(--mag)">Haven</span>' : ''}</div>
      </div>
      <button type="button" class="heart ${hon}" data-heart="${i}" title="Favorite">${heart}</button>
      <div class="meta sz">${fmtSize(t.size)}</div>
      <button type="button" class="play" ${can ? '' : 'disabled'} data-play="${i}">${i === current && !audio.paused ? 'Pause' : 'Play'}</button>
    </div>`;
    }).join('') || '<p class="sub" style="padding:16px">No matches — try All, or add favorites with ♥</p>';

    el.querySelectorAll('[data-play]').forEach(b => b.addEventListener('click', e => {
      e.stopPropagation();
      const i = +b.getAttribute('data-play');
      if (i === current && !audio.paused) { audio.pause(); updatePlayBtn(); renderListEnhanced(); return; }
      playIndex(i);
    }));
    el.querySelectorAll('.row').forEach(r => r.addEventListener('click', e => {
      if (e.target.closest('[data-heart]')) return;
      playIndex(+r.dataset.i);
    }));
    el.querySelectorAll('[data-heart]').forEach(b => b.addEventListener('click', e => {
      e.stopPropagation();
      toggleFav(+b.getAttribute('data-heart'));
    }));
  }
  // override global renderList used by player
  window.renderList = renderListEnhanced;
  if (typeof renderList === 'function') {
    // reassign binding used in outer scope if const/let - already function declarations hoist
  }
  // Patch function in outer scope via assignment on function name when declared as function
  try { renderList = renderListEnhanced; } catch (e) { /* ok */ }

  function toggleFav(i) {
    const t = tracks[i];
    if (!t) return;
    const k = trackKey(t);
    if (favs.has(k)) { favs.delete(k); toast('Removed favorite'); }
    else { favs.add(k); toast('Saved favorite (this device only)'); }
    saveSet(LS_FAV, favs);
    updateFavBtn();
    if (libFilter === 'favorites') window.rebuildFilter();
    else renderListEnhanced();
  }

  function updateFavBtn() {
    const btn = document.getElementById('btn-fav');
    const t = current >= 0 ? tracks[current] : null;
    if (!btn) return;
    const on = t && isFav(t);
    btn.classList.toggle('on', !!on);
    btn.classList.toggle('hot', !!on);
    btn.textContent = on ? '♥ Fav' : '♡ Fav';
  }

  function addToQueue(i) {
    const t = tracks[i];
    if (!t) return;
    const k = trackKey(t);
    if (!queue.includes(k)) queue.push(k);
    saveList(LS_QUEUE, queue);
    toast('Added to queue');
    if (libFilter === 'queue') window.rebuildFilter();
  }

  // --- chips ---
  document.querySelectorAll('#filter-chips [data-lib]').forEach(btn => {
    btn.addEventListener('click', () => {
      libFilter = btn.getAttribute('data-lib');
      document.querySelectorAll('#filter-chips [data-lib]').forEach(b => b.classList.toggle('on', b === btn));
      window.rebuildFilter();
    });
  });

  // --- volume ---
  const volEl = document.getElementById('vol');
  if (volEl) {
    const saved = parseFloat(localStorage.getItem(LS_VOL) || '1');
    if (!isNaN(saved)) { volEl.value = String(saved); audio.volume = saved; }
    volEl.addEventListener('input', () => {
      const v = parseFloat(volEl.value);
      audio.volume = v;
      if (audioB) audioB.volume = v;
      localStorage.setItem(LS_VOL, String(v));
    });
  }

  // --- crossfade toggle ---
  const xf = document.getElementById('xfade');
  if (xf) {
    xf.checked = xfadeOn;
    xf.addEventListener('change', () => {
      xfadeOn = xf.checked;
      localStorage.setItem(LS_XFADE, xfadeOn ? '1' : '0');
      toast(xfadeOn ? 'Crossfade on (~3s)' : 'Crossfade off');
    });
  }

  // --- seek ---
  const seek = document.getElementById('seek');
  const timeLabel = document.getElementById('time-label');
  function fmtTime(s) {
    if (!isFinite(s) || s < 0) return '0:00';
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return m + ':' + String(sec).padStart(2, '0');
  }
  function updateSeekUI() {
    if (!seek || seeking) return;
    const d = audio.duration || 0;
    const c = audio.currentTime || 0;
    if (d > 0) seek.value = String(Math.floor((c / d) * 1000));
    if (timeLabel) timeLabel.textContent = fmtTime(c) + ' / ' + fmtTime(d);
  }
  if (seek) {
    seek.addEventListener('pointerdown', () => { seeking = true; });
    seek.addEventListener('pointerup', () => {
      const d = audio.duration || 0;
      if (d > 0) audio.currentTime = (parseInt(seek.value, 10) / 1000) * d;
      seeking = false;
    });
    seek.addEventListener('change', () => {
      const d = audio.duration || 0;
      if (d > 0) audio.currentTime = (parseInt(seek.value, 10) / 1000) * d;
      seeking = false;
    });
  }
  audio.addEventListener('timeupdate', () => {
    updateSeekUI();
    maybeCrossfade();
  });
  audio.addEventListener('loadedmetadata', updateSeekUI);

  // --- crossfade engine ---
  function ensureAudioB() {
    if (audioB) return audioB;
    audioB = new Audio();
    audioB.preload = 'auto';
    return audioB;
  }

  function maybeCrossfade() {
    if (!xfadeOn || fading || audio.paused) return;
    const d = audio.duration;
    const c = audio.currentTime;
    if (!isFinite(d) || d < 8) return;
    if (d - c > 3.2) return;
    // start next early
    fading = true;
    const nextI = peekNextIndex();
    if (nextI < 0 || nextI === current) { fading = false; return; }
    const t = tracks[nextI];
    if (!t || !t.stream_url) { fading = false; return; }
    const b = ensureAudioB();
    const targetVol = parseFloat((document.getElementById('vol') || {}).value || audio.volume || 1);
    b.src = t.stream_url;
    b.volume = 0;
    b.play().then(() => {
      const steps = 12;
      let step = 0;
      const iv = setInterval(() => {
        step++;
        const p = step / steps;
        audio.volume = targetVol * (1 - p);
        b.volume = targetVol * p;
        if (step >= steps) {
          clearInterval(iv);
          try { audio.pause(); } catch (e) {}
          // swap: make b the main by transferring - simpler: set current and replace audio src mid-stream is hard
          // Instead: set main audio to same position as B and stop B
          current = nextI;
          audio.src = t.stream_url;
          audio.currentTime = b.currentTime;
          audio.volume = targetVol;
          audio.play().catch(() => {});
          try { b.pause(); b.removeAttribute('src'); b.load(); } catch (e) {}
          fading = false;
          if (typeof updateNow === 'function') updateNow();
          updatePlayBtn();
          updateFavBtn();
          updateMediaSession();
          renderListEnhanced();
          try { history.replaceState(null, '', '#' + (t.sha256 || nextI)); } catch (e) {}
        }
      }, 250);
    }).catch(() => { fading = false; });
  }

  function peekNextIndex() {
    // Use same rules as pickNext(+1) without advancing bag permanently if possible
    if (typeof pickNext === 'function') {
      // pickNext mutates bag — acceptable
      // Don't call if repeatOne
      if (typeof repeatOne !== 'undefined' && repeatOne) return current;
    }
    const pool = (typeof playablePool === 'function') ? playablePool() : filteredIdx.filter(i => tracks[i] && tracks[i].stream_url);
    if (!pool.length) return -1;
    if (typeof radio !== 'undefined' && (radio || radioFavOnly || shuffle) && typeof refillBag === 'function') {
      // random peek
      const opts = pool.filter(i => i !== current);
      if (!opts.length) return pool[0];
      return opts[Math.floor(Math.random() * opts.length)];
    }
    let pos = pool.indexOf(current);
    if (pos < 0) pos = -1;
    let npos = pos + 1;
    if (npos >= pool.length) npos = 0;
    return pool[npos];
  }

  // --- sleep timer ---
  const sleepSel = document.getElementById('sleep-sel');
  const sleepBar = document.getElementById('sleep-bar');
  const sleepFill = document.getElementById('sleep-fill');

  function clearSleep() {
    if (sleepTimer) clearTimeout(sleepTimer);
    sleepTimer = null;
    sleepEndsAt = 0;
    if (sleepRaf) cancelAnimationFrame(sleepRaf);
    if (sleepBar) sleepBar.classList.remove('on');
    if (sleepSel && sleepSel.value !== '0' && !sleepEndsAt) { /* keep */ }
  }

  function tickSleepBar() {
    if (!sleepEndsAt) return;
    const total = parseFloat(sleepSel.value) * 60 * 1000;
    const left = sleepEndsAt - Date.now();
    if (sleepBar) sleepBar.classList.add('on');
    if (sleepFill && total > 0) {
      const p = Math.max(0, Math.min(1, left / total));
      sleepFill.style.transform = 'scaleX(' + p + ')';
    }
    if (left > 0) sleepRaf = requestAnimationFrame(tickSleepBar);
  }

  async function fadeOutAndStop() {
    const start = audio.volume;
    const steps = 20;
    for (let i = 1; i <= steps; i++) {
      audio.volume = start * (1 - i / steps);
      await new Promise(r => setTimeout(r, 150));
    }
    audio.pause();
    audio.volume = parseFloat((document.getElementById('vol') || {}).value || 1);
    toast('Sleep timer — good night');
    if (sleepSel) sleepSel.value = '0';
    clearSleep();
  }

  if (sleepSel) {
    sleepSel.addEventListener('change', () => {
      clearSleep();
      const mins = parseInt(sleepSel.value, 10) || 0;
      if (!mins) { toast('Sleep timer off'); return; }
      sleepEndsAt = Date.now() + mins * 60 * 1000;
      sleepTimer = setTimeout(() => { fadeOutAndStop(); }, mins * 60 * 1000);
      tickSleepBar();
      toast('Sleep timer: ' + mins + ' min');
    });
  }

  // --- Media Session ---
  function updateMediaSession() {
    if (!('mediaSession' in navigator)) return;
    const t = current >= 0 ? tracks[current] : null;
    if (!t) return;
    try {
      navigator.mediaSession.metadata = new MediaMetadata({
        title: t.title || 'Excavationpro',
        artist: 'Excavationpro',
        album: isHavenTrack(t) ? 'Eternal Haven' : 'Sovereign Streams',
        artwork: [
          { src: 'assets/listen-icon-512.svg', sizes: '512x512', type: 'image/svg+xml' },
          { src: 'assets/og-haven-star-chart.jpg', sizes: '1200x630', type: 'image/jpeg' },
        ],
      });
      navigator.mediaSession.playbackState = audio.paused ? 'paused' : 'playing';
    } catch (e) {}
  }

  function bindMediaSession() {
    if (!('mediaSession' in navigator)) return;
    const h = (action, fn) => {
      try { navigator.mediaSession.setActionHandler(action, fn); } catch (e) {}
    };
    h('play', () => { audio.play().catch(() => {}); updateMediaSession(); });
    h('pause', () => { audio.pause(); updateMediaSession(); });
    h('previoustrack', () => { if (typeof nextTrack === 'function') nextTrack(-1); });
    h('nexttrack', () => { if (typeof nextTrack === 'function') nextTrack(1); });
    h('stop', () => { audio.pause(); audio.currentTime = 0; updateMediaSession(); });
    h('seekto', (d) => {
      if (d && d.seekTime != null && isFinite(audio.duration)) audio.currentTime = d.seekTime;
    });
    h('seekbackward', (d) => { audio.currentTime = Math.max(0, audio.currentTime - (d.seekOffset || 10)); });
    h('seekforward', (d) => { audio.currentTime = Math.min(audio.duration || 0, audio.currentTime + (d.seekOffset || 10)); });
  }
  bindMediaSession();
  audio.addEventListener('play', () => { updateMediaSession(); updateFavBtn(); });
  audio.addEventListener('pause', updateMediaSession);
  audio.addEventListener('ended', () => { fading = false; });

  // Patch playIndex after definition — wrap
  const _playIndex = playIndex;
  window.playIndex = function playIndexWrapped(i) {
    fading = false;
    const ok = _playIndex(i);
    updateMediaSession();
    updateFavBtn();
    return ok;
  };
  try { playIndex = window.playIndex; } catch (e) {}

  // --- Share card ---
  function openShare() {
    const t = current >= 0 ? tracks[current] : null;
    const modal = document.getElementById('share-modal');
    if (!modal) return;
    if (!t) { toast('Play a track first'); return; }
    const pageUrl = location.origin + location.pathname + '#' + (t.sha256 || current);
    document.getElementById('share-title').textContent = t.title || 'Excavationpro';
    document.getElementById('share-body').textContent =
      'Excavationpro — free sovereign stream\n' + pageUrl +
      (t.isrcs && t.isrcs[0] ? '\nISRC ' + t.isrcs[0] : '');
    modal.dataset.page = pageUrl;
    modal.dataset.stream = t.stream_url || '';
    modal.classList.add('open');
  }
  function closeShare() {
    const modal = document.getElementById('share-modal');
    if (modal) modal.classList.remove('open');
  }
  document.getElementById('btn-share')?.addEventListener('click', openShare);
  document.getElementById('share-close')?.addEventListener('click', closeShare);
  document.getElementById('share-copy-page')?.addEventListener('click', async () => {
    const u = document.getElementById('share-modal')?.dataset.page || location.href;
    try { await navigator.clipboard.writeText(u); toast('Page link copied'); } catch (e) { prompt('Copy', u); }
  });
  document.getElementById('share-copy-stream')?.addEventListener('click', async () => {
    const u = document.getElementById('share-modal')?.dataset.stream || '';
    if (!u) return toast('No stream URL');
    try { await navigator.clipboard.writeText(u); toast('Stream URL copied'); } catch (e) { prompt('Copy', u); }
  });
  document.getElementById('share-native')?.addEventListener('click', async () => {
    const modal = document.getElementById('share-modal');
    const title = document.getElementById('share-title')?.textContent || 'Excavationpro';
    const url = modal?.dataset.page || location.href;
    if (navigator.share) {
      try { await navigator.share({ title, text: 'Listen free — Excavationpro', url }); } catch (e) {}
    } else {
      try { await navigator.clipboard.writeText(url); toast('Link copied (share API N/A)'); } catch (e) {}
    }
  });

  document.getElementById('btn-fav')?.addEventListener('click', () => {
    if (current < 0) return toast('Play a track first');
    toggleFav(current);
  });
  document.getElementById('btn-queue-add')?.addEventListener('click', () => {
    if (current < 0) return toast('Play a track first');
    addToQueue(current);
  });

  // Radio from favorites only
  document.getElementById('btn-radio-fav')?.addEventListener('click', () => {
    radioFavOnly = true;
    libFilter = 'favorites';
    document.querySelectorAll('#filter-chips [data-lib]').forEach(b => {
      b.classList.toggle('on', b.getAttribute('data-lib') === 'favorites');
    });
    window.rebuildFilter();
    if (!filteredIdx.length) {
      toast('No favorites yet — heart some tracks first');
      radioFavOnly = false;
      return;
    }
    // enable radio mode
    if (typeof radio !== 'undefined') {
      if (!radio && typeof toggleRadio === 'function') toggleRadio();
      else if (typeof nextTrack === 'function') nextTrack(1);
    } else if (typeof nextTrack === 'function') nextTrack(1);
    toast('♥ Radio — favorites only');
  });

  // When radio toggles off, clear fav-only
  const _tr = typeof toggleRadio === 'function' ? toggleRadio : null;
  if (_tr) {
    window.toggleRadio = function () {
      _tr();
      if (typeof radio !== 'undefined' && !radio) radioFavOnly = false;
    };
    try { toggleRadio = window.toggleRadio; } catch (e) {}
  }

  // Keyboard extras
  document.addEventListener('keydown', e => {
    if (e.target.matches('input,textarea,select')) return;
    if (e.key === 'f' || e.key === 'F') {
      if (current >= 0) toggleFav(current);
    }
    if (e.key === 'Share' || (e.key === 's' && e.shiftKey)) openShare();
  });

  // --- PWA install ---
  let deferredPrompt = null;
  const pwaBtn = document.getElementById('btn-pwa-install');
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    if (pwaBtn) pwaBtn.classList.add('show');
  });
  pwaBtn?.addEventListener('click', async () => {
    if (deferredPrompt) {
      deferredPrompt.prompt();
      try { await deferredPrompt.userChoice; } catch (e) {}
      deferredPrompt = null;
      pwaBtn.classList.remove('show');
    } else {
      toast('Use browser menu → Install / Add to Home Screen');
    }
  });
  window.addEventListener('appinstalled', () => {
    toast('Installed — open from home screen anytime');
    if (pwaBtn) pwaBtn.classList.remove('show');
  });

  // Register service worker
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('./sw-listen.js', { scope: './' }).catch(() => {});
  }

  // Manifest link if missing
  if (!document.querySelector('link[rel="manifest"]')) {
    const l = document.createElement('link');
    l.rel = 'manifest';
    l.href = 'manifest-listen.webmanifest';
    document.head.appendChild(l);
  }
  if (!document.querySelector('meta[name="theme-color"]')) {
    const m = document.createElement('meta');
    m.name = 'theme-color';
    m.content = '#0a0a12';
    document.head.appendChild(m);
  }
  if (!document.querySelector('link[rel="apple-touch-icon"]')) {
    const a = document.createElement('link');
    a.rel = 'apple-touch-icon';
    a.href = 'assets/listen-icon-512.svg';
    document.head.appendChild(a);
  }

  // Re-bind toolbar to wrapped filter (original listeners pointed at old rebuildFilter)
  const qEl = document.getElementById('q');
  const sortEl = document.getElementById('sort');
  const filterEl = document.getElementById('filter');
  if (qEl) {
    qEl.oninput = () => window.rebuildFilter();
  }
  if (sortEl) sortEl.onchange = () => window.rebuildFilter();
  if (filterEl) filterEl.onchange = () => window.rebuildFilter();

  // Initial paint with hearts
  updateFavBtn();
  window.rebuildFilter();
  console.info('[listen-v2] Media Session · sleep · crossfade · favorites · Haven filter · share · PWA ready');
})();
"""


def inject_css(html: str) -> str:
    marker = "</style>"
    if "filter-chips" in html and "lygo_listen_favorites_v1" in html:
        print("[css] already enhanced")
        return html
    # insert before last </style> in head-ish first style block
    idx = html.find(marker)
    if idx < 0:
        raise SystemExit("no </style>")
    return html[:idx] + "\n" + EXTRA_CSS + "\n" + html[idx:]


def inject_filter_chips(html: str) -> str:
    if 'id="filter-chips"' in html:
        return html
    # after toolbar opening or before list
    needle = '<div class="list" id="list">'
    if needle not in html:
        raise SystemExit("list not found")
    return html.replace(needle, FILTER_CHIPS_HTML + "\n    " + needle, 1)


def inject_dock_extra(html: str) -> str:
    if 'id="sleep-sel"' in html:
        return html
    needle = '<audio id="audio" controls preload="none"></audio>'
    if needle not in html:
        raise SystemExit("audio not found")
    return html.replace(needle, DOCK_EXTRA_HTML + "\n    " + needle, 1)


def inject_modals(html: str) -> str:
    if 'id="share-modal"' in html:
        return html
    needle = '<div class="dock">'
    if needle not in html:
        raise SystemExit("dock not found")
    return html.replace(needle, MODALS_HTML + "\n" + needle, 1)


def inject_js(html: str) -> str:
    if "LISTEN PORTAL v2 ENHANCEMENTS" in html:
        # replace existing enhance block
        html = re.sub(
            r"/\* ===== LISTEN PORTAL v2 ENHANCEMENTS ===== \*/[\s\S]*?/\* ===== END v2 ===== \*/\s*",
            "",
            html,
        )
    # append before last </script>
    end = html.rfind("</script>")
    if end < 0:
        raise SystemExit("no script end")
    block = ENHANCE_JS + "\n/* ===== END v2 ===== */\n"
    return html[:end] + "\n" + block + html[end:]


def patch_kb_hint(html: str) -> str:
    old = "Keys: <b>Space</b> play/pause · <b>N</b> next · <b>P</b> prev · <b>S</b> shuffle · <b>R</b> radio · <b>/</b> search · continuous auto-next always on"
    new = "Keys: <b>Space</b> play/pause · <b>N</b>/<b>P</b> next/prev · <b>S</b> shuffle · <b>R</b> radio · <b>F</b> favorite · <b>/</b> search · continuous on · sleep &amp; crossfade in dock"
    if old in html:
        return html.replace(old, new, 1)
    return html


def write_pwa_assets() -> None:
    assets = EXCAV / "assets"
    assets.mkdir(exist_ok=True)
    icon = assets / "listen-icon-512.svg"
    icon.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#00f0ff"/>
      <stop offset="50%" stop-color="#b06bff"/>
      <stop offset="100%" stop-color="#d4af37"/>
    </linearGradient>
  </defs>
  <rect width="512" height="512" rx="96" fill="#0a0a12"/>
  <circle cx="256" cy="256" r="168" fill="none" stroke="url(#g)" stroke-width="28"/>
  <circle cx="256" cy="256" r="48" fill="#d4af37"/>
  <path d="M300 180v140c0 28-22 44-48 44s-48-16-48-44" fill="none" stroke="#00f0ff" stroke-width="22" stroke-linecap="round"/>
  <text x="256" y="455" text-anchor="middle" fill="#d4af37" font-family="Georgia,serif" font-size="36">Δ9</text>
</svg>
""",
        encoding="utf-8",
    )

    manifest = {
        "name": "Excavationpro Listen Free",
        "short_name": "Excavationpro",
        "description": "Free sovereign music player — Excavationpro / Eternal Haven streams, radio mode, offline shell.",
        "start_url": "./excavationpro-listen.html",
        "scope": "./",
        "display": "standalone",
        "orientation": "any",
        "background_color": "#0a0a12",
        "theme_color": "#0a0a12",
        "categories": ["music", "entertainment"],
        "icons": [
            {
                "src": "assets/listen-icon-512.svg",
                "sizes": "any",
                "type": "image/svg+xml",
                "purpose": "any maskable",
            }
        ],
    }
    (EXCAV / "manifest-listen.webmanifest").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    sw = r"""/* Excavationpro Listen — shell cache only (streams stay network) */
const CACHE = 'excavationpro-listen-shell-v2';
const SHELL = [
  './excavationpro-listen.html',
  './manifest-listen.webmanifest',
  './assets/listen-icon-512.svg',
];
self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  // never cache HF audio streams
  if (url.hostname.includes('huggingface.co') || url.pathname.includes('/stream/')) {
    return;
  }
  if (e.request.method !== 'GET') return;
  e.respondWith(
    caches.match(e.request).then((hit) => {
      const net = fetch(e.request).then((res) => {
        if (res && res.ok && url.origin === self.location.origin) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(e.request, copy));
        }
        return res;
      }).catch(() => hit);
      return hit || net;
    })
  );
});
"""
    (EXCAV / "sw-listen.js").write_text(sw, encoding="utf-8")
    print("[pwa] wrote manifest-listen.webmanifest, sw-listen.js, icon")


def main() -> int:
    html = LISTEN.read_text(encoding="utf-8")
    html = inject_css(html)
    html = inject_filter_chips(html)
    html = inject_dock_extra(html)
    html = inject_modals(html)
    html = inject_js(html)
    html = patch_kb_hint(html)
    LISTEN.write_text(html, encoding="utf-8")
    print(f"[ok] {LISTEN} ({len(html):,} chars)")

    write_pwa_assets()

    # sync docs
    shutil.copy2(LISTEN, DOCS)
    print(f"[ok] synced {DOCS}")

    # copy pwa to docs for stack pages if served from there
    for name in ("manifest-listen.webmanifest", "sw-listen.js"):
        src = EXCAV / name
        dst = STACK / "docs" / name
        shutil.copy2(src, dst)
    assets_docs = STACK / "docs" / "assets"
    assets_docs.mkdir(exist_ok=True)
    shutil.copy2(EXCAV / "assets" / "listen-icon-512.svg", assets_docs / "listen-icon-512.svg")

    # verify markers
    t = LISTEN.read_text(encoding="utf-8")
    for s in (
        "filter-chips",
        "sleep-sel",
        "share-modal",
        "LISTEN PORTAL v2 ENHANCEMENTS",
        "mediaSession",
        "lygo_listen_favorites_v1",
        "Crossfade",
        "btn-pwa-install",
    ):
        assert s in t, s
        print("  OK", s)
    print("ALL ENHANCEMENTS APPLIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
