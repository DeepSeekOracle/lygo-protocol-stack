#!/usr/bin/env python3
"""
Global multi-listener play counts for static Pages.

Write path (no HF Space PRO needed):
  1) hits.dwyl.com — atomic-ish global increment on real plays
  2) jsonblob.com — public leaderboard JSON (GET free, PUT merge after play)

Read path:
  jsonblob aggregate → trophy, most/least/never/recent, row badges
  Poll every 20s for live growth
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

EXCAV = Path(r"I:\E Drive\Excavationpro")
STACK = Path(r"I:\E Drive\lygo-protocol-stack")
LISTEN = EXCAV / "excavationpro-listen.html"
DOCS = STACK / "docs" / "excavationpro-listen.html"

# Public shared aggregate (created for Excavationpro listen)
JSONBLOB_ID = "019f7611-e28e-7de6-87df-5f5e4e8c4690"
JSONBLOB_URL = f"https://jsonblob.com/api/jsonBlob/{JSONBLOB_ID}"
DWYL_NS = "excavationpro"

CSS = r"""
/* ===== GLOBAL PLAYS BOARD ===== */
.plays-board {
  margin: 12px 0 14px; display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 10px;
}
.plays-board .box {
  border-radius: 12px; padding: 12px 14px;
  border: 1px solid rgba(0,240,255,.25);
  background: rgba(12,12,22,.88);
  min-height: 150px;
}
.plays-board .box h3 {
  margin: 0 0 8px; font-size: .8rem; letter-spacing: .06em;
  text-transform: uppercase; color: var(--gold); font-family: Cinzel, serif;
}
.plays-board .box.most { border-color: rgba(212,175,55,.5); box-shadow: 0 0 16px rgba(212,175,55,.12); }
.plays-board .box.least { border-color: rgba(176,107,255,.4); }
.plays-board .box.never { border-color: rgba(255,255,255,.14); }
.plays-board .box.recent { border-color: rgba(61,214,140,.45); }
.plays-board ol, .plays-board ul {
  margin: 0; padding-left: 1.15rem; font-size: .78rem; color: var(--muted);
  max-height: 190px; overflow: auto;
}
.plays-board li { margin: 5px 0; cursor: pointer; color: var(--text); line-height: 1.35; }
.plays-board li:hover { color: var(--cyan); }
.plays-board li .n { color: var(--gold); font-weight: 700; font-variant-numeric: tabular-nums; }
.plays-board .empty { font-size: .78rem; color: var(--muted); font-style: italic; }
.live-pulse { font-size: .7rem; color: var(--ok); font-weight: 600; text-transform: none; letter-spacing: 0; }
"""

BOARD_HTML = r"""
<div class="plays-board" id="plays-board" aria-label="Global play charts">
  <div class="box most">
    <h3>Most played <span class="live-pulse" id="plays-live">live</span></h3>
    <ol id="most-played-list"><li class="empty">Loading global tallies…</li></ol>
  </div>
  <div class="box least">
    <h3>Least played</h3>
    <ol id="least-played-list"><li class="empty">Need a few public listens…</li></ol>
  </div>
  <div class="box never">
    <h3>Not played yet</h3>
    <ul id="never-played-list"><li class="empty">Scanning catalog…</li></ul>
  </div>
  <div class="box recent">
    <h3>Recent global listens</h3>
    <ul id="recent-played-list"><li class="empty">Be the first pulse…</li></ul>
  </div>
</div>
"""

CLIENT_JS = r'''
/* ===== LYGO GLOBAL PLAYS (jsonblob + hits.dwyl) ===== */
(function lygoGlobalPlaysPublic() {
  const BLOB = "https://jsonblob.com/api/jsonBlob/019f7611-e28e-7de6-87df-5f5e4e8c4690";
  const DWYL = "https://hits.dwyl.com/excavationpro/";
  const TOTAL_KEY = "listen-total-plays-v2";
  const LS_CLIENT = "lygo_play_client_id_v2";
  const LS_SESSION = "lygo_play_session_v2";
  const LS_CACHE = "lygo_play_cache_v2";
  const LS_CHAIN = "lygo_play_chain_v2";
  const LS_TOTAL = "lygo_play_total_v2";
  const MIN_SECONDS = 20;
  const MIN_RATIO = 0.35;
  const POLL_MS = 20000;

  let playCache = {};
  let titleBySha = {};
  let sessionCounted = new Set();
  let accumSeconds = 0, lastTick = 0, listenSha = null, pending = false;
  let clientId = loadClientId();
  let chain = loadChain();
  let writing = false;

  try { playCache = JSON.parse(localStorage.getItem(LS_CACHE) || "{}") || {}; } catch (e) {}
  try { sessionCounted = new Set(JSON.parse(sessionStorage.getItem(LS_SESSION) || "[]")); } catch (e) {}
  (tracks || []).forEach(t => { if (t && t.sha256) titleBySha[t.sha256] = t.title || t.sha256.slice(0, 12); });

  function loadClientId() {
    try {
      let id = localStorage.getItem(LS_CLIENT);
      if (!id) { id = "web-" + Math.random().toString(36).slice(2) + Date.now().toString(36); localStorage.setItem(LS_CLIENT, id); }
      return id;
    } catch (e) { return "web-anon"; }
  }
  function loadChain() {
    try {
      const c = JSON.parse(localStorage.getItem(LS_CHAIN) || "null");
      if (c && Array.isArray(c.events)) return c;
    } catch (e) {}
    return { signature: "LYGO-PLAY-LATTICE-v1", append_only: true, events: [], tip_hash: "0".repeat(64) };
  }
  function saveChain() {
    try {
      chain.updated_at = new Date().toISOString();
      chain.event_count = chain.events.length;
      if (chain.events.length > 2500) chain.events = chain.events.slice(-2500);
      localStorage.setItem(LS_CHAIN, JSON.stringify(chain));
    } catch (e) {}
  }
  function saveCache() { try { localStorage.setItem(LS_CACHE, JSON.stringify(playCache)); } catch (e) {} }
  function saveSession() { try { sessionStorage.setItem(LS_SESSION, JSON.stringify([...sessionCounted])); } catch (e) {} }

  async function sha256Hex(str) {
    const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(str));
    return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, "0")).join("");
  }
  function uuid() {
    return crypto.randomUUID ? crypto.randomUUID() :
      "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, c => {
        const r = Math.random() * 16 | 0; return (c === "x" ? r : (r & 0x3 | 0x8)).toString(16);
      });
  }
  function fmt(n) {
    if (n == null || isNaN(n)) return "—";
    if (n >= 1e6) return (n / 1e6).toFixed(1) + "M";
    if (n >= 10000) return (n / 1e3).toFixed(1) + "k";
    return String(n);
  }
  function esc(s) {
    return String(s || "").replace(/[&<>"']/g, c => ({ "&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;" }[c]));
  }
  function titleOf(sha) { return titleBySha[sha] || (sha ? sha.slice(0, 12) + "…" : "?"); }

  function updateTrophy(n) {
    const el = document.getElementById("trophy-total");
    if (el) el.textContent = fmt(n) + " plays";
    try { localStorage.setItem(LS_TOTAL, String(n)); } catch (e) {}
    const live = document.getElementById("plays-live");
    if (live) live.textContent = "live · " + fmt(n);
  }

  async function hitDwyl(key) {
    const url = DWYL + encodeURIComponent(key) + ".json";
    const r = await fetch(url, { cache: "no-store", mode: "cors" });
    if (!r.ok) throw new Error("dwyl " + r.status);
    const j = await r.json();
    const n = parseInt(j.message || j.count || "0", 10);
    return isNaN(n) ? 0 : n;
  }

  async function getBlob() {
    const r = await fetch(BLOB, { cache: "no-store", mode: "cors", headers: { "Accept": "application/json" } });
    if (!r.ok) throw new Error("blob get " + r.status);
    return r.json();
  }
  async function putBlob(agg) {
    const r = await fetch(BLOB, {
      method: "PUT",
      mode: "cors",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify(agg),
    });
    if (!r.ok) throw new Error("blob put " + r.status);
    return true;
  }

  function rankBoard(by) {
    const ranked = Object.keys(by).map(s => ({ sha256: s, plays: by[s] || 0 }))
      .filter(x => x.plays > 0);
    const most = ranked.slice().sort((a, b) => b.plays - a.plays || a.sha256.localeCompare(b.sha256)).slice(0, 15);
    const least = ranked.slice().sort((a, b) => a.plays - b.plays || a.sha256.localeCompare(b.sha256)).slice(0, 15);
    return { most, least };
  }

  function renderBoard(agg) {
    const by = agg.by_track || {};
    Object.keys(by).forEach(s => { playCache[s] = Math.max(playCache[s] || 0, by[s] || 0); });
    saveCache();
    if (typeof agg.total_plays === "number") updateTrophy(agg.total_plays);

    const { most, least } = rankBoard(by);
    const recent = (agg.recent || []).slice(0, 15);

    // never played sample from catalog
    const never = [];
    const pool = tracks.map((t, i) => i).filter(i => tracks[i].sha256 && !by[tracks[i].sha256]);
    for (let i = pool.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      const tmp = pool[i]; pool[i] = pool[j]; pool[j] = tmp;
    }
    pool.slice(0, 15).forEach(i => never.push(tracks[i]));

    function fill(id, items, mode) {
      const el = document.getElementById(id);
      if (!el) return;
      if (!items.length) {
        el.innerHTML = '<li class="empty">' + (mode === "never" ? "All catalog tracks have plays!" : "No public plays yet — listen ≥20s") + "</li>";
        return;
      }
      el.innerHTML = items.map(it => {
        const sha = it.sha256 || (it.sha) || "";
        const title = it.title || titleOf(sha);
        const plays = it.plays != null ? it.plays : (by[sha] || 0);
        if (mode === "never") {
          return `<li data-sha="${esc(sha)}">${esc(title)}</li>`;
        }
        if (mode === "recent") {
          return `<li data-sha="${esc(sha)}"><span class="n">${fmt(plays)}</span> · ${esc(title)}</li>`;
        }
        return `<li data-sha="${esc(sha)}"><span class="n">${fmt(plays)}</span> · ${esc(title)}</li>`;
      }).join("");
      el.querySelectorAll("li[data-sha]").forEach(li => {
        li.onclick = () => {
          const sha = li.getAttribute("data-sha");
          const i = tracks.findIndex(t => t.sha256 === sha);
          if (i >= 0 && typeof playIndex === "function") playIndex(i);
        };
      });
    }
    fill("most-played-list", most, "most");
    fill("least-played-list", least, "least");
    fill("never-played-list", never.map(t => ({ sha256: t.sha256, title: t.title, plays: 0 })), "never");
    fill("recent-played-list", recent, "recent");
    updateRowPlays();
  }

  function updateRowPlays() {
    document.querySelectorAll(".row[data-i]").forEach(row => {
      const i = +row.dataset.i;
      const t = tracks[i];
      if (!t || !t.sha256) return;
      let badge = row.querySelector(".plays");
      if (!badge) {
        badge = document.createElement("div");
        badge.className = "plays";
        const heart = row.querySelector("[data-heart]");
        const play = row.querySelector("[data-play]");
        if (heart) row.insertBefore(badge, heart);
        else if (play) row.insertBefore(badge, play);
        else row.appendChild(badge);
      }
      const c = playCache[t.sha256] || 0;
      badge.innerHTML = "<b>" + fmt(c) + "</b> ▶";
      badge.classList.toggle("hot", c >= 10);
      badge.title = c + " global plays";
    });
  }

  async function refreshPublic() {
    try {
      const agg = await getBlob();
      // normalize
      if (!agg.by_track) agg.by_track = {};
      if (!agg.recent) agg.recent = [];
      renderBoard(agg);
      return agg;
    } catch (e) {
      console.warn("[plays] public refresh", e);
      try {
        const last = parseInt(localStorage.getItem(LS_TOTAL) || "0", 10);
        if (last > 0) updateTrophy(last);
      } catch (e2) {}
      updateRowPlays();
      return null;
    }
  }

  async function mergeAndPublish(sha, title, trackCount, totalCount) {
    // retry loop for mild race safety
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        const agg = await getBlob();
        if (!agg.by_track) agg.by_track = {};
        if (!agg.recent) agg.recent = [];
        agg.by_track[sha] = Math.max(agg.by_track[sha] || 0, trackCount || 0);
        // total: use max of dwyl total and sum of tracks (sum can lag if races)
        const sumTracks = Object.values(agg.by_track).reduce((a, b) => a + (Number(b) || 0), 0);
        agg.total_plays = Math.max(agg.total_plays || 0, totalCount || 0, sumTracks);
        agg.unique_tracks_played = Object.keys(agg.by_track).length;
        agg.updated_at = new Date().toISOString();
        agg.signature = "LYGO-PLAY-AGGREGATE-v1";
        agg.lattice = "LYGO-PLAY-LATTICE-v1";
        agg.recent.unshift({
          sha256: sha,
          title: title || titleOf(sha),
          plays: agg.by_track[sha],
          ts: agg.updated_at,
          client: clientId.slice(0, 12),
        });
        if (agg.recent.length > 40) agg.recent = agg.recent.slice(0, 40);
        const ranks = rankBoard(agg.by_track);
        agg.most_played = ranks.most;
        agg.least_played = ranks.least;
        await putBlob(agg);
        renderBoard(agg);
        return agg;
      } catch (e) {
        console.warn("[plays] merge retry", attempt, e);
        await new Promise(r => setTimeout(r, 200 + attempt * 300));
      }
    }
    return null;
  }

  async function recordPlay(sha, title) {
    if (!sha || sessionCounted.has(sha) || pending) return;
    pending = true;
    sessionCounted.add(sha);
    saveSession();
    try {
      const played = accumSeconds + (lastTick ? (Date.now() - lastTick) / 1000 : 0);
      // local chain event
      const prev = chain.tip_hash || "0".repeat(64);
      const ev = {
        v: 1,
        event_id: uuid(),
        track_sha256: sha,
        title: title || null,
        ts: new Date().toISOString(),
        client_id: clientId,
        listen_sec: Math.max(played, MIN_SECONDS),
        prev_hash: prev,
      };
      const body = Object.assign({}, ev);
      const ordered = {};
      Object.keys(body).sort().forEach(k => ordered[k] = body[k]);
      ev.event_hash = await sha256Hex(JSON.stringify(ordered));
      chain.events.push(ev);
      chain.tip_hash = ev.event_hash;
      saveChain();

      // GLOBAL increment (hits.dwyl)
      let trackN = 0, totalN = 0;
      try {
        trackN = await hitDwyl("stream-" + sha.slice(0, 24));
        totalN = await hitDwyl(TOTAL_KEY);
      } catch (e) {
        // offline: local only
        trackN = (playCache[sha] || 0) + 1;
        totalN = Object.values(playCache).reduce((a, b) => a + (Number(b) || 0), 0) + 1;
      }
      playCache[sha] = Math.max(playCache[sha] || 0, trackN);
      saveCache();
      updateTrophy(totalN);
      updateRowPlays();

      // GLOBAL leaderboard (jsonblob) for most/least/recent — everyone sees
      if (!writing) {
        writing = true;
        try { await mergeAndPublish(sha, title, trackN, totalN); }
        finally { writing = false; }
      }
      console.info("[plays] GLOBAL", title, "track=", trackN, "total=", totalN);
    } finally {
      pending = false;
    }
  }

  function maybeCount() {
    if (current < 0 || !tracks[current]) return;
    const t = tracks[current];
    if (!t.sha256 || sessionCounted.has(t.sha256)) return;
    const dur = audio.duration;
    const played = accumSeconds + (lastTick ? (Date.now() - lastTick) / 1000 : 0);
    if (played >= MIN_SECONDS || (isFinite(dur) && dur > 0 && audio.currentTime / dur >= MIN_RATIO)) {
      recordPlay(t.sha256, t.title);
    }
  }

  audio.addEventListener("play", () => {
    const t = current >= 0 ? tracks[current] : null;
    const sha = t && t.sha256;
    if (sha !== listenSha) { listenSha = sha; accumSeconds = 0; }
    lastTick = Date.now();
  });
  audio.addEventListener("pause", () => {
    if (lastTick) { accumSeconds += (Date.now() - lastTick) / 1000; lastTick = 0; }
    maybeCount();
  });
  audio.addEventListener("ended", () => {
    if (lastTick) { accumSeconds += (Date.now() - lastTick) / 1000; lastTick = 0; }
    if (current >= 0 && tracks[current] && tracks[current].sha256) {
      recordPlay(tracks[current].sha256, tracks[current].title);
    }
  });
  audio.addEventListener("timeupdate", () => { if (!audio.paused) maybeCount(); });

  const _pi = window.playIndex || (typeof playIndex === "function" ? playIndex : null);
  if (_pi) {
    window.playIndex = function (i) {
      if (lastTick) { accumSeconds += (Date.now() - lastTick) / 1000; lastTick = 0; }
      maybeCount();
      accumSeconds = 0; listenSha = null;
      const r = _pi(i);
      listenSha = tracks[i] && tracks[i].sha256;
      lastTick = Date.now();
      setTimeout(updateRowPlays, 40);
      return r;
    };
    try { playIndex = window.playIndex; } catch (e) {}
  }

  const list = document.getElementById("list");
  if (list) new MutationObserver(() => updateRowPlays()).observe(list, { childList: true, subtree: true });

  const sub = document.querySelector("#play-trophy .sub");
  if (sub) sub.textContent = "GLOBAL multi-listener plays · most / least / unheard · live";

  // export chain button
  function ensureExport() {
    const host = document.querySelector(".fav-actions") || document.getElementById("smart-filters");
    if (!host || document.getElementById("btn-export-play-lattice")) return;
    const b = document.createElement("button");
    b.type = "button"; b.id = "btn-export-play-lattice";
    b.textContent = "Export play lattice";
    b.style.cssText = "cursor:pointer;border-radius:999px;padding:7px 12px;font-size:.76rem;font-weight:600;border:1px solid rgba(212,175,55,.45);background:rgba(212,175,55,.12);color:var(--gold)";
    b.onclick = () => {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([JSON.stringify(Object.assign({}, chain, { client_id: clientId, exported_at: new Date().toISOString() }), null, 2)], { type: "application/json" }));
      a.download = "excavationpro-play-lattice-export.json";
      a.click();
    };
    host.appendChild(b);
  }
  ensureExport(); setTimeout(ensureExport, 600);

  refreshPublic();
  setInterval(refreshPublic, POLL_MS);
  console.info("[plays] GLOBAL public board ready (jsonblob + dwyl)");
})();
/* ===== END LYGO GLOBAL PLAYS ===== */
'''


def main() -> int:
    html = LISTEN.read_text(encoding="utf-8")
    before = len(html)

    if "GLOBAL PLAYS BOARD" not in html:
        if "</style>" not in html:
            raise SystemExit("no style close")
        html = html.replace("</style>", CSS + "\n</style>", 1)

    if 'id="plays-board"' not in html:
        if 'id="wave-shell"' in html:
            m = re.search(r'<div class="wave-shell"[\s\S]*?</div>\s*<div class="wave-meta"[\s\S]*?</div>\s*</div>', html)
            # simpler insert after sticky or before list
            pass
        if '<div class="list" id="list">' in html:
            html = html.replace(
                '<div class="list" id="list">',
                BOARD_HTML + "\n" + '<div class="list" id="list">',
                1,
            )
        elif 'id="smart-filters"' in html:
            html = re.sub(
                r'(id="smart-filters"[\s\S]*?</div>)',
                r"\1\n" + BOARD_HTML,
                html,
                count=1,
            )
        else:
            html = html.replace("<body>", "<body>\n" + BOARD_HTML + "\n", 1)

    # strip old clients carefully
    for pat in (
        r"/\* ===== LYGO GLOBAL PLAYS[\s\S]*?/\* ===== END LYGO GLOBAL PLAYS ===== \*/\s*",
        r"/\* ===== LYGO GLOBAL PLAY LATTICE[\s\S]*?/\* ===== END LYGO GLOBAL PLAY LATTICE ===== \*/\s*",
        r"/\* ===== LYGO PLAY LATTICE CLIENT ===== \*/[\s\S]*?/\* ===== END LYGO PLAY LATTICE CLIENT ===== \*/\s*",
        r"/\* ===== PLAY COUNTS[\s\S]*?/\* ===== END PLAY COUNTS ===== \*/\s*",
    ):
        html2 = re.sub(pat, "", html, count=1)
        if len(html2) >= before * 0.5:
            html = html2
            before = len(html)

    idx = html.rfind("</script>")
    if idx < 0:
        raise SystemExit("no script")
    html = html[:idx] + "\n" + CLIENT_JS + "\n" + html[idx:]

    if len(html) < 500000 and before > 500000:
        raise SystemExit(f"abort shrink {before}->{len(html)}")

    # trophy ensure — only inside hero header (never raw <body> prepend; that broke the header)
    if 'id="play-trophy"' not in html:
        trophy = '''
  <div class="play-trophy" id="play-trophy" title="Global play tally">
    <span class="cup" aria-hidden="true">🏆</span>
    <div class="nums">
      <div class="big" id="trophy-total">—</div>
      <div class="sub">Total plays · live across listeners</div>
    </div>
    <span class="live-dot" title="Live counter"></span>
  </div>
'''
        if "<h1>Excavationpro — Listen Free</h1>" in html:
            html = html.replace(
                "<h1>Excavationpro — Listen Free</h1>",
                "<h1>Excavationpro — Listen Free</h1>\n" + trophy,
                1,
            )
        elif '<header class="hero wrap">' in html:
            html = html.replace(
                '<header class="hero wrap">',
                '<header class="hero wrap">\n' + trophy,
                1,
            )
        elif '<div class="tools">' in html:
            html = html.replace('<div class="tools">', '<div class="tools">\n' + trophy + "\n", 1)

    LISTEN.write_text(html, encoding="utf-8")
    shutil.copy2(LISTEN, DOCS)
    print(f"ok {before} -> {len(html)}")
    for c in (
        "plays-board",
        "most-played-list",
        "least-played-list",
        "never-played-list",
        "recent-played-list",
        "LYGO GLOBAL PLAYS",
        "jsonblob.com",
        "hits.dwyl.com",
        "play-trophy",
    ):
        print(("OK" if c in html else "MISS"), c)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
