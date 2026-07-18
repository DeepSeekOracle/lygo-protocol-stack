#!/usr/bin/env python3
"""Inject LYGO Play Lattice client into excavationpro-listen.html."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

EXCAV = Path(r"I:\E Drive\Excavationpro")
STACK = Path(r"I:\E Drive\lygo-protocol-stack")
LISTEN = EXCAV / "excavationpro-listen.html"
DOCS = STACK / "docs" / "excavationpro-listen.html"


def build_js() -> str:
    return r'''
/* ===== LYGO PLAY LATTICE CLIENT ===== */
(function lygoPlayLatticeClient() {
  const HF_COUNTS = "https://huggingface.co/datasets/DeepSeekOracle/excavationpro-music-stream/resolve/main/play/play_counts.json";
  const LS_CHAIN = "lygo_play_lattice_chain_v1";
  const LS_CLIENT = "lygo_play_lattice_client_id_v1";
  const LS_SESSION = "lygo_play_lattice_session_v1";
  const LS_CACHE = "lygo_play_lattice_cache_v1";
  const LS_TOTAL = "lygo_play_lattice_total_v1";
  const MIN_SECONDS = 20;
  const MIN_RATIO = 0.35;

  const LATTICE = (typeof DATA !== "undefined" && DATA.lattice) ? DATA.lattice : {};
  const PLAY_CFG = LATTICE.play_lattice || {};
  const INGEST = (
    window.LYGO_PLAY_INGEST ||
    PLAY_CFG.ingest_url ||
    PLAY_CFG.ingest ||
    (function(){ try { return localStorage.getItem("lygo_play_ingest_url") || ""; } catch(e){ return ""; } })()
  ).replace(/\/$/, "");
  const COUNTS_URLS = [INGEST ? INGEST + "/v1/counts" : null, PLAY_CFG.counts_url || HF_COUNTS, HF_COUNTS].filter(Boolean);

  let playCache = {};
  let sessionCounted = new Set();
  let accumSeconds = 0;
  let lastTick = 0;
  let listenSha = null;
  let pending = false;
  let chain = loadChain();
  let clientId = loadClientId();

  try { playCache = JSON.parse(localStorage.getItem(LS_CACHE) || "{}") || {}; } catch (e) {}
  try { sessionCounted = new Set(JSON.parse(sessionStorage.getItem(LS_SESSION) || "[]")); } catch (e) {}

  function loadClientId() {
    try {
      let id = localStorage.getItem(LS_CLIENT);
      if (id) return id;
      id = "web-" + Math.random().toString(36).slice(2) + Date.now().toString(36);
      localStorage.setItem(LS_CLIENT, id);
      return id;
    } catch (e) { return "web-anon"; }
  }
  function loadChain() {
    try {
      const c = JSON.parse(localStorage.getItem(LS_CHAIN) || "null");
      if (c && Array.isArray(c.events)) return c;
    } catch (e) {}
    return { signature: "Δ9Φ963-PLAY-LATTICE-v1", append_only: true, events: [], tip_hash: "0".repeat(64) };
  }
  function saveChain() {
    try {
      chain.updated_at = new Date().toISOString();
      chain.event_count = chain.events.length;
      localStorage.setItem(LS_CHAIN, JSON.stringify(chain));
    } catch (e) {}
  }
  function saveCache() { try { localStorage.setItem(LS_CACHE, JSON.stringify(playCache)); } catch (e) {} }
  function saveSession() { try { sessionStorage.setItem(LS_SESSION, JSON.stringify([...sessionCounted])); } catch (e) {} }

  async function sha256Hex(str) {
    const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(str));
    return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, "0")).join("");
  }
  async function computeEventHash(ev) {
    const body = Object.assign({}, ev);
    delete body.event_hash;
    const ordered = {};
    Object.keys(body).sort().forEach(k => { ordered[k] = body[k]; });
    return sha256Hex(JSON.stringify(ordered));
  }
  function uuid() {
    if (crypto.randomUUID) return crypto.randomUUID();
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, c => {
      const r = Math.random() * 16 | 0;
      return (c === "x" ? r : (r & 0x3 | 0x8)).toString(16);
    });
  }
  function fmt(n) {
    if (n == null || isNaN(n)) return "—";
    if (n >= 1e6) return (n / 1e6).toFixed(1) + "M";
    if (n >= 1e4) return (n / 1e3).toFixed(1) + "k";
    return String(n);
  }
  function updateTrophy(n) {
    const el = document.getElementById("trophy-total");
    if (el) el.textContent = fmt(n) + " plays";
    try { localStorage.setItem(LS_TOTAL, String(n)); } catch (e) {}
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
      const c = playCache[t.sha256];
      if (c != null) {
        badge.innerHTML = "<b>" + fmt(c) + "</b> ▶";
        badge.classList.toggle("hot", c >= 10);
        badge.title = c + " plays (LYGO play lattice)";
      } else {
        badge.textContent = "·";
        badge.title = "Play ≥20s to count on the lattice";
      }
    });
  }

  async function buildEvent(trackSha, title, listenSec) {
    const ev = {
      v: 1,
      signature: "Δ9Φ963-PLAY-EVENT-v1",
      event_id: uuid(),
      track_sha256: trackSha,
      title: title || null,
      ts: new Date().toISOString(),
      client_id: clientId,
      listen_sec: listenSec || MIN_SECONDS,
      prev_hash: chain.tip_hash || "0".repeat(64),
    };
    ev.event_hash = await computeEventHash(ev);
    return ev;
  }
  function appendLocal(ev) {
    chain.events.push(ev);
    if (chain.events.length > 3000) chain.events = chain.events.slice(-3000);
    chain.tip_hash = ev.event_hash;
    saveChain();
  }

  async function refreshCountsFromNetwork() {
    for (const url of COUNTS_URLS) {
      try {
        const r = await fetch(url, { cache: "no-store", mode: "cors" });
        if (!r.ok) continue;
        const j = await r.json();
        if (j.by_track && typeof j.by_track === "object") {
          Object.keys(j.by_track).forEach(k => {
            playCache[k] = Math.max(playCache[k] || 0, j.by_track[k] || 0);
          });
          saveCache();
        }
        if (typeof j.total_plays === "number") updateTrophy(j.total_plays);
        updateRowPlays();
        console.info("[play-lattice] counts", url, j.total_plays);
        return j;
      } catch (e) {}
    }
    try {
      const last = parseInt(localStorage.getItem(LS_TOTAL) || "0", 10);
      if (last > 0) updateTrophy(last);
      else {
        const sum = Object.values(playCache).reduce((a, b) => a + (Number(b) || 0), 0);
        if (sum > 0) updateTrophy(sum);
        else {
          const el = document.getElementById("trophy-total");
          if (el) el.textContent = "▶ plays";
        }
      }
    } catch (e) {}
    updateRowPlays();
    return null;
  }

  async function submitEvent(ev) {
    appendLocal(ev);
    playCache[ev.track_sha256] = (playCache[ev.track_sha256] || 0) + 1;
    saveCache();
    updateRowPlays();
    if (!INGEST) {
      updateTrophy(Object.values(playCache).reduce((a, b) => a + (Number(b) || 0), 0));
      return;
    }
    try {
      const r = await fetch(INGEST + "/v1/play", {
        method: "POST", mode: "cors",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ event: ev }),
      });
      if (!r.ok) throw new Error("ingest " + r.status);
      const j = await r.json();
      if (typeof j.total_plays === "number") updateTrophy(j.total_plays);
      if (typeof j.track_plays === "number") {
        playCache[ev.track_sha256] = Math.max(playCache[ev.track_sha256] || 0, j.track_plays);
        saveCache(); updateRowPlays();
      }
    } catch (e) {
      console.warn("[play-lattice] ingest fail, local chain kept", e);
      updateTrophy(Object.values(playCache).reduce((a, b) => a + (Number(b) || 0), 0));
    }
  }

  async function recordPlay(sha, title) {
    if (!sha || sessionCounted.has(sha) || pending) return;
    pending = true;
    sessionCounted.add(sha);
    saveSession();
    try {
      const played = accumSeconds + (lastTick ? (Date.now() - lastTick) / 1000 : 0);
      const ev = await buildEvent(sha, title, Math.max(played, MIN_SECONDS));
      await submitEvent(ev);
    } finally { pending = false; }
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
    if (current >= 0 && tracks[current] && tracks[current].sha256) recordPlay(tracks[current].sha256, tracks[current].title);
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

  function ensureExport() {
    const host = document.querySelector(".fav-actions") || document.getElementById("smart-filters");
    if (!host || document.getElementById("btn-export-play-lattice")) return;
    const b = document.createElement("button");
    b.type = "button";
    b.id = "btn-export-play-lattice";
    b.textContent = "Export play lattice";
    b.title = "Hash-chained events — import: lygo_play_lattice.py --import-ledger";
    b.style.cssText = "cursor:pointer;border-radius:999px;padding:7px 12px;font-size:.76rem;font-weight:600;border:1px solid rgba(212,175,55,.45);background:rgba(212,175,55,.12);color:var(--gold)";
    b.onclick = () => {
      const payload = Object.assign({}, chain, { exported_at: new Date().toISOString(), client_id: clientId });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" }));
      a.download = "excavationpro-play-lattice-export.json";
      a.click();
    };
    host.appendChild(b);
  }
  ensureExport();
  setTimeout(ensureExport, 800);

  const sub = document.querySelector("#play-trophy .sub");
  if (sub) {
    sub.textContent = INGEST
      ? "LYGO play lattice · multi-listener live · hash-chained"
      : "LYGO play lattice · local chain on · deploy ingest for global live tally";
  }

  const list = document.getElementById("list");
  if (list) new MutationObserver(() => updateRowPlays()).observe(list, { childList: true, subtree: true });

  refreshCountsFromNetwork();
  console.info("[play-lattice] ready · ingest=", INGEST || "(local-only)");
})();
/* ===== END LYGO PLAY LATTICE CLIENT ===== */
'''


def main() -> int:
    if not LISTEN.exists():
        raise SystemExit(f"missing {LISTEN}")
    html = LISTEN.read_text(encoding="utf-8")
    before = len(html)
    html = re.sub(
        r"/\* ===== PLAY COUNTS[\s\S]*?/\* ===== END PLAY COUNTS ===== \*/\s*",
        "",
        html,
        count=1,
    )
    html = re.sub(
        r"/\* ===== LYGO PLAY LATTICE CLIENT ===== \*/[\s\S]*?/\* ===== END LYGO PLAY LATTICE CLIENT ===== \*/\s*",
        "",
        html,
        count=1,
    )
    end = html.rfind("</script>")
    if end < 0:
        raise SystemExit("no script end")
    html = html[:end] + "\n" + build_js() + "\n" + html[end:]
    if before > 500_000 and len(html) < 500_000:
        raise SystemExit(f"abort: page shrank {before} → {len(html)}")
    LISTEN.write_text(html, encoding="utf-8")
    shutil.copy2(LISTEN, DOCS)
    print(f"ok len={len(html)} lattice_client={('LYGO PLAY LATTICE CLIENT' in html)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
