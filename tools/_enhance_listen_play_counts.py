#!/usr/bin/env python3
"""
Add immutable-style play counts to excavationpro-listen.html:
  - Per-track play counts (global via hits.dwyl.com + local ledger)
  - Total plays trophy on sticky header
  - Append-only local event log (exportable)
Counts fire after real listening (not page load spam).
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

EXCAV = Path(r"I:\E Drive\Excavationpro")
STACK = Path(r"I:\E Drive\lygo-protocol-stack")
LISTEN = EXCAV / "excavationpro-listen.html"
DOCS = STACK / "docs" / "excavationpro-listen.html"

CSS = r"""
/* ===== PLAY COUNTS / TROPHY ===== */
.play-trophy {
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
  margin: 8px 0 0; padding: 10px 14px; border-radius: 12px;
  border: 1px solid rgba(212,175,55,.55);
  background: linear-gradient(135deg, rgba(212,175,55,.18), rgba(176,107,255,.12), rgba(0,240,255,.08));
  box-shadow: 0 0 24px rgba(212,175,55,.2);
}
.play-trophy .cup {
  font-size: 1.75rem; line-height: 1; filter: drop-shadow(0 0 8px rgba(212,175,55,.5));
}
.play-trophy .nums { flex: 1; min-width: 140px; }
.play-trophy .nums .big {
  font-family: Cinzel, serif; font-size: clamp(1.4rem, 3vw, 1.85rem);
  font-weight: 700; color: var(--gold); letter-spacing: .02em;
  font-variant-numeric: tabular-nums;
}
.play-trophy .nums .sub { font-size: .72rem; color: var(--muted); margin-top: 2px; }
.play-trophy .live-dot {
  width: 8px; height: 8px; border-radius: 50%; background: var(--ok);
  box-shadow: 0 0 8px var(--ok); animation: pulseDot 1.6s ease infinite;
}
@keyframes pulseDot { 0%,100%{opacity:1} 50%{opacity:.35} }
.row .plays {
  font-size: .68rem; color: var(--muted); font-variant-numeric: tabular-nums;
  white-space: nowrap; min-width: 3.2rem; text-align: right;
}
.row .plays b { color: var(--cyan); font-weight: 700; }
.row .plays.hot b { color: var(--gold); }
.now .plays-inline { color: var(--gold); font-size: .78rem; margin-left: 6px; }
"""

TROPHY_HTML = r"""
<div class="play-trophy" id="play-trophy" title="Global play tally · increments when listeners actually play tracks">
  <span class="cup" aria-hidden="true">🏆</span>
  <div class="nums">
    <div class="big" id="trophy-total">—</div>
    <div class="sub">Total plays · sovereign stream trophy · live across listeners</div>
  </div>
  <span class="live-dot" title="Live counter"></span>
</div>
"""

JS = r"""
/* ===== PLAY COUNTS (global + local immutable ledger) ===== */
(function playCounts() {
  // Global counters via hits.dwyl.com (public badge API — works on static Pages)
  // Local append-only ledger in localStorage for export / device truth
  const NS = 'excavationpro';
  const TOTAL_KEY = 'listen-total-plays-v1';
  const LS_LEDGER = 'lygo_listen_play_ledger_v1';
  const LS_CACHE = 'lygo_listen_play_cache_v1';
  const LS_SESSION = 'lygo_listen_play_session_v1'; // sha -> counted this tab session
  const MIN_SECONDS = 20; // real listen before count
  const MIN_RATIO = 0.35; // or 35% of duration

  let playCache = {}; // sha -> count
  let sessionCounted = new Set();
  let listenStart = 0;
  let listenSha = null;
  let accumSeconds = 0;
  let lastTick = 0;
  let totalPlays = null;
  let pendingCount = false;

  try { playCache = JSON.parse(localStorage.getItem(LS_CACHE) || '{}') || {}; } catch (e) {}
  try {
    const s = JSON.parse(sessionStorage.getItem(LS_SESSION) || '[]');
    sessionCounted = new Set(s);
  } catch (e) {}

  function saveCache() {
    try { localStorage.setItem(LS_CACHE, JSON.stringify(playCache)); } catch (e) {}
  }
  function saveSession() {
    try { sessionStorage.setItem(LS_SESSION, JSON.stringify([...sessionCounted])); } catch (e) {}
  }
  function loadLedger() {
    try {
      const L = JSON.parse(localStorage.getItem(LS_LEDGER) || 'null');
      if (L && Array.isArray(L.events)) return L;
    } catch (e) {}
    return {
      signature: 'Δ9Φ963-LISTEN-PLAY-LEDGER-v1',
      append_only: true,
      events: [],
      note: 'Local append-only play events. Global counts also hit public counter for multi-listener trophy.',
    };
  }
  function appendLedger(ev) {
    const L = loadLedger();
    L.events.push(ev);
    // keep last 5000 events
    if (L.events.length > 5000) L.events = L.events.slice(-5000);
    L.updated_at = new Date().toISOString();
    L.event_count = L.events.length;
    try { localStorage.setItem(LS_LEDGER, JSON.stringify(L)); } catch (e) {}
    return L;
  }

  function counterUrl(key) {
    // hits.dwyl.com increments on each fetch and returns shields-style JSON
    return 'https://hits.dwyl.com/' + NS + '/' + encodeURIComponent(key) + '.json';
  }
  async function hitCounter(key) {
    const url = counterUrl(key);
    const r = await fetch(url, { cache: 'no-store', mode: 'cors' });
    if (!r.ok) throw new Error('counter ' + r.status);
    const j = await r.json();
    // message is the count as string
    const n = parseInt(j.message || j.count || j.value || '0', 10);
    return isNaN(n) ? 0 : n;
  }
  async function getCounter(key) {
    // same endpoint increments — for display-only we still use cache first
    // Prefer GET without increment: dwyl always increments. So we only hit on real plays,
    // and use cached values for UI; refresh total periodically with care.
    return hitCounter(key);
  }

  function fmt(n) {
    if (n == null || isNaN(n)) return '—';
    if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M';
    if (n >= 1e4) return (n / 1e3).toFixed(1) + 'k';
    return String(n);
  }

  function updateTrophy(n) {
    totalPlays = n;
    const el = document.getElementById('trophy-total');
    if (el) el.textContent = fmt(n) + ' plays';
    try { localStorage.setItem('lygo_listen_total_last', String(n)); } catch (e) {}
  }

  function updateRowPlays() {
    document.querySelectorAll('.row[data-i]').forEach(row => {
      const i = +row.dataset.i;
      const t = tracks[i];
      if (!t || !t.sha256) return;
      let badge = row.querySelector('.plays');
      if (!badge) {
        badge = document.createElement('div');
        badge.className = 'plays';
        // insert before heart or play button
        const heart = row.querySelector('[data-heart]');
        if (heart) row.insertBefore(badge, heart);
        else {
          const play = row.querySelector('[data-play]');
          if (play) row.insertBefore(badge, play);
          else row.appendChild(badge);
        }
      }
      const c = playCache[t.sha256];
      if (c != null) {
        badge.innerHTML = '<b>' + fmt(c) + '</b> ▶';
        badge.classList.toggle('hot', c >= 10);
        badge.title = c + ' plays (global + local cache)';
      } else {
        badge.innerHTML = '·';
        badge.title = 'Play to count';
      }
    });
    // now playing
    if (current >= 0 && tracks[current]) {
      const t = tracks[current];
      const c = playCache[t.sha256];
      const now = document.getElementById('now');
      if (now && c != null) {
        let span = now.querySelector('.plays-inline');
        if (!span) {
          span = document.createElement('span');
          span.className = 'plays-inline';
          now.querySelector('span')?.appendChild(span);
        }
        span.textContent = ' · ' + fmt(c) + ' plays';
      }
    }
  }

  async function recordPlay(sha, title) {
    if (!sha || sessionCounted.has(sha) || pendingCount) return;
    pendingCount = true;
    sessionCounted.add(sha);
    saveSession();
    try {
      // per-track global
      const n = await hitCounter('stream-' + sha.slice(0, 24));
      playCache[sha] = n;
      // total trophy
      const tot = await hitCounter(TOTAL_KEY);
      updateTrophy(tot);
      saveCache();
      appendLedger({
        type: 'play',
        sha256: sha,
        title: title || null,
        global_count_after: n,
        total_after: tot,
        ts: new Date().toISOString(),
        source: 'hits.dwyl.com+local_ledger',
      });
      updateRowPlays();
      console.info('[plays] counted', sha.slice(0, 12), '→', n, 'total', tot);
    } catch (e) {
      // offline fallback: local-only immutable-ish tally
      playCache[sha] = (playCache[sha] || 0) + 1;
      const localTotal = Object.values(playCache).reduce((a, b) => a + (b || 0), 0);
      updateTrophy(localTotal);
      saveCache();
      appendLedger({
        type: 'play_local',
        sha256: sha,
        title: title || null,
        local_count: playCache[sha],
        ts: new Date().toISOString(),
        source: 'local_only_offline',
      });
      updateRowPlays();
      console.warn('[plays] local fallback', e);
    } finally {
      pendingCount = false;
    }
  }

  function maybeCount() {
    if (current < 0 || !tracks[current]) return;
    const t = tracks[current];
    const sha = t.sha256;
    if (!sha || sessionCounted.has(sha)) return;
    const dur = audio.duration;
    const played = accumSeconds + (lastTick ? (Date.now() - lastTick) / 1000 : 0);
    const enoughTime = played >= MIN_SECONDS;
    const enoughRatio = isFinite(dur) && dur > 0 && (audio.currentTime / dur) >= MIN_RATIO;
    if (enoughTime || enoughRatio) {
      recordPlay(sha, t.title);
    }
  }

  // Accumulate listening time only while playing
  audio.addEventListener('play', () => {
    const t = current >= 0 ? tracks[current] : null;
    const sha = t && t.sha256;
    if (sha !== listenSha) {
      listenSha = sha;
      accumSeconds = 0;
    }
    lastTick = Date.now();
  });
  audio.addEventListener('pause', () => {
    if (lastTick) {
      accumSeconds += (Date.now() - lastTick) / 1000;
      lastTick = 0;
    }
    maybeCount();
  });
  audio.addEventListener('ended', () => {
    if (lastTick) {
      accumSeconds += (Date.now() - lastTick) / 1000;
      lastTick = 0;
    }
    // always count on natural end if not yet
    if (current >= 0 && tracks[current] && tracks[current].sha256) {
      recordPlay(tracks[current].sha256, tracks[current].title);
    }
  });
  audio.addEventListener('timeupdate', () => {
    if (!audio.paused) maybeCount();
  });
  // reset accum on track change
  const _pi = window.playIndex || (typeof playIndex === 'function' ? playIndex : null);
  if (_pi) {
    window.playIndex = function (i) {
      if (lastTick) {
        accumSeconds += (Date.now() - lastTick) / 1000;
        lastTick = 0;
      }
      maybeCount(); // previous track
      accumSeconds = 0;
      listenSha = null;
      const r = _pi(i);
      const t = tracks[i];
      listenSha = t && t.sha256;
      lastTick = Date.now();
      // prefetch cached count display
      setTimeout(updateRowPlays, 50);
      return r;
    };
    try { playIndex = window.playIndex; } catch (e) {}
  }

  // Do NOT hit TOTAL_KEY on load (would inflate trophy). Seed from last known total only.
  (function seedTrophy() {
    try {
      const last = parseInt(localStorage.getItem('lygo_listen_total_last') || '0', 10);
      if (last > 0) { updateTrophy(last); return; }
    } catch (e) {}
    const sum = Object.values(playCache).reduce((a, b) => a + (Number(b) || 0), 0);
    if (sum > 0) updateTrophy(sum);
    else {
      const el = document.getElementById('trophy-total');
      if (el) el.textContent = '▶ plays';
    }
  })();

  // Re-render plays after list renders
  const obs = new MutationObserver(() => {
    if (document.querySelector('.row[data-i]')) updateRowPlays();
  });
  const list = document.getElementById('list');
  if (list) obs.observe(list, { childList: true, subtree: true });

  // Export play ledger button in fav panel or create
  function ensureExportBtn() {
    const host = document.querySelector('.fav-actions') || document.getElementById('smart-filters');
    if (!host || document.getElementById('btn-export-plays')) return;
    const b = document.createElement('button');
    b.type = 'button';
    b.id = 'btn-export-plays';
    b.textContent = 'Export play ledger';
    b.style.cssText = host.classList.contains('fav-actions') ? '' :
      'cursor:pointer;border-radius:999px;padding:7px 12px;font-size:.76rem;font-weight:600;border:1px solid rgba(212,175,55,.4);background:rgba(212,175,55,.1);color:var(--gold)';
    b.onclick = () => {
      const L = loadLedger();
      const a = document.createElement('a');
      a.href = URL.createObjectURL(new Blob([JSON.stringify(L, null, 2)], { type: 'application/json' }));
      a.download = 'excavationpro-play-ledger.json';
      a.click();
    };
    host.appendChild(b);
  }
  ensureExportBtn();
  setTimeout(ensureExportBtn, 500);

  // Lazy: when scrolling rows into view, show cached counts only (no network inflate)
  updateRowPlays();
  console.info('[plays] trophy + per-track counts · count after', MIN_SECONDS, 's or', MIN_RATIO * 100, '% · append-only local ledger');
})();
/* ===== END PLAY COUNTS ===== */
"""


def main() -> int:
    html = LISTEN.read_text(encoding="utf-8")

    # CSS
    if "PLAY COUNTS / TROPHY" not in html:
        idx = html.find("</style>")
        if idx < 0:
            raise SystemExit("no style")
        html = html[:idx] + "\n" + CSS + "\n" + html[idx:]
    else:
        html = re.sub(
            r"/\* ===== PLAY COUNTS / TROPHY ===== \*/[\s\S]*?(?=\n/\* =====|\n</style>)",
            CSS.strip() + "\n",
            html,
            count=1,
        )

    # Trophy — inject into sticky tools or after sticky bio
    if 'id="play-trophy"' not in html:
        if 'id="donate-progress"' in html:
            html = html.replace(
                'id="donate-progress"',
                'id="donate-progress"',
                1,
            )
            # after donate-progress block's closing divs — place after tools column open
            html = html.replace(
                '<div class="tools">',
                '<div class="tools">\n' + TROPHY_HTML + "\n",
                1,
            )
        elif 'id="sticky-top"' in html:
            html = html.replace(
                'id="sticky-top"',
                'id="sticky-top"',
                1,
            )
            html = re.sub(
                r'(<div class="sticky-top"[^>]*>[\s\S]*?<div class="wrap sticky-bio">)',
                r"\1\n" + TROPHY_HTML + "\n",
                html,
                count=1,
            )
        else:
            html = html.replace("<body>", "<body>\n" + TROPHY_HTML + "\n", 1)
    else:
        html = re.sub(
            r'<div class="play-trophy"[\s\S]*?</div>\s*',
            TROPHY_HTML.strip() + "\n",
            html,
            count=1,
        )

    # JS
    if "PLAY COUNTS (global + local immutable ledger)" in html:
        html = re.sub(
            r"/\* ===== PLAY COUNTS[\s\S]*?/\* ===== END PLAY COUNTS ===== \*/\s*",
            "",
            html,
            count=1,
        )
    end = html.rfind("</script>")
    if end < 0:
        raise SystemExit("no script")
    html = html[:end] + "\n" + JS + "\n" + html[end:]

    LISTEN.write_text(html, encoding="utf-8")
    shutil.copy2(LISTEN, DOCS)
    print(f"wrote {LISTEN}")
    t = LISTEN.read_text(encoding="utf-8")
    for c in ("play-trophy", "trophy-total", "hits.dwyl.com", "lygo_listen_play_ledger_v1", "MIN_SECONDS"):
        print(("OK" if c in t else "FAIL"), c)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
