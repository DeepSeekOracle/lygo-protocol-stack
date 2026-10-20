/**
 * Excavationpro Listen — Lyrics panel plugin
 * Loads data/lyrics_index.json (by_sha256). Clean lyrics only.
 * License: LYGO Music License v1.0
 * Signature: Delta9Phi963-LYRICS-PANEL-v1
 */
(function () {
  "use strict";
  const SIG = "Delta9Phi963-LYRICS-PANEL-v1";
  const INDEX_URLS = [
    "data/lyrics_index.json",
    "https://huggingface.co/datasets/DeepSeekOracle/excavationpro-music-stream/resolve/main/lyrics/lyrics_index.json",
  ];

  let index = null;
  let loaded = false;

  function el(tag, cls, html) {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (html != null) n.innerHTML = html;
    return n;
  }

  function ensureUi() {
    if (document.getElementById("lyrics-panel-root")) return;

    // Tab button
    const tabs = document.querySelector(".tabs");
    if (tabs && !tabs.querySelector('[data-tab="lyrics"]')) {
      const b = el("button", "", "Lyrics");
      b.type = "button";
      b.setAttribute("data-tab", "lyrics");
      b.title = "Song lyrics · LYGO Music License";
      tabs.appendChild(b);
    }

    // Panel section (hidden until tab active — reuse existing tab system if present)
    let panel = document.getElementById("panel-lyrics");
    if (!panel) {
      panel = el("div", "");
      panel.id = "panel-lyrics";
      panel.style.display = "none";
      panel.innerHTML = `
        <div id="lyrics-panel-root" class="lyrics-panel">
          <style>
            .lyrics-panel{margin:1rem 0 2rem;padding:1rem 1.1rem;border:1px solid rgba(0,240,255,.28);border-radius:12px;background:rgba(0,20,32,.55)}
            .lyrics-panel h2{margin:0 0 .35rem;font-size:1.05rem;color:#7df9ff}
            .lyrics-panel .ly-meta{color:#9ab;font-size:.78rem;margin:0 0 .75rem;line-height:1.45}
            .lyrics-panel .ly-toolbar{display:flex;flex-wrap:wrap;gap:.5rem;margin:0 0 .75rem;align-items:center}
            .lyrics-panel input[type=search]{flex:1;min-width:180px;padding:.45rem .65rem;border-radius:8px;border:1px solid rgba(255,255,255,.12);background:#0a0e14;color:#e8f0ff}
            .lyrics-panel select{padding:.45rem .55rem;border-radius:8px;border:1px solid rgba(255,255,255,.12);background:#0a0e14;color:#e8f0ff}
            .lyrics-panel .ly-body{white-space:pre-wrap;font-family:ui-monospace,Consolas,monospace;font-size:.82rem;line-height:1.55;color:#dce7f5;max-height:52vh;overflow:auto;padding:.75rem;border-radius:8px;background:rgba(0,0,0,.35);border:1px solid rgba(255,255,255,.06)}
            .lyrics-panel .ly-empty{color:#889;font-style:italic}
            .lyrics-panel .ly-license{margin-top:.75rem;font-size:.68rem;color:#8a9;line-height:1.4}
            .lyrics-panel .ly-license a{color:#7df9ff}
            .lyrics-panel .ly-now{color:#ffd76a;font-weight:600}
            .lyrics-panel button.ly-btn{padding:.4rem .7rem;border-radius:8px;border:1px solid rgba(0,240,255,.35);background:rgba(0,240,255,.08);color:#cfefff;cursor:pointer;font-size:.75rem}
            .lyrics-panel button.ly-btn:hover{background:rgba(0,240,255,.18)}
          </style>
          <h2>Lyrics</h2>
          <p class="ly-meta">Clean steward lyrics only · no AI style/production notes · © Excavationpro / Lightfather</p>
          <div class="ly-toolbar">
            <input type="search" id="ly-search" placeholder="Search lyrics by title / moniker…" autocomplete="off" />
            <select id="ly-select" aria-label="Song with lyrics"></select>
            <button type="button" class="ly-btn" id="ly-from-now">Now playing</button>
          </div>
          <p class="ly-meta" id="ly-head">Select a song…</p>
          <div class="ly-body ly-empty" id="ly-body">Lyrics appear here when available for the track.</div>
          <p class="ly-license" id="ly-license"></p>
        </div>`;
      const wrap = document.querySelector(".wrap") || document.body;
      wrap.appendChild(panel);
    }

    // Hook tab switching if site uses data-tab buttons
    document.querySelectorAll(".tabs [data-tab]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const tab = btn.getAttribute("data-tab");
        document.querySelectorAll(".tabs [data-tab]").forEach((b) => b.classList.toggle("active", b === btn));
        ["player", "ledger", "lattice", "radio", "support", "lyrics"].forEach((id) => {
          const p = document.getElementById("panel-" + id);
          if (p) p.style.display = id === tab ? "" : "none";
        });
        // player panel is default id panel-player
        if (tab === "player") {
          const pp = document.getElementById("panel-player");
          if (pp) pp.style.display = "";
        } else {
          const pp = document.getElementById("panel-player");
          if (pp && tab !== "player") pp.style.display = "none";
        }
      });
    });

    document.getElementById("ly-from-now")?.addEventListener("click", showNowPlaying);
    document.getElementById("ly-select")?.addEventListener("change", (e) => {
      showSha(e.target.value);
    });
    document.getElementById("ly-search")?.addEventListener("input", (e) => {
      fillSelect(e.target.value || "");
    });
  }

  function fillSelect(q) {
    const sel = document.getElementById("ly-select");
    if (!sel || !index) return;
    const qq = (q || "").toLowerCase().trim();
    const entries = Object.entries(index.by_sha256 || {});
    const filtered = entries.filter(([sha, v]) => {
      if (!qq) return true;
      const blob = `${v.title || ""} ${v.moniker || ""} ${v.chapter_title || ""} ${v.album || ""}`.toLowerCase();
      return blob.includes(qq);
    });
    filtered.sort((a, b) => (a[1].title || "").localeCompare(b[1].title || ""));
    sel.innerHTML = "";
    const opt0 = document.createElement("option");
    opt0.value = "";
    opt0.textContent = filtered.length ? `Songs with lyrics (${filtered.length})` : "No lyrics match";
    sel.appendChild(opt0);
    for (const [sha, v] of filtered) {
      const o = document.createElement("option");
      o.value = sha;
      const mon = v.moniker ? ` · ${v.moniker}` : "";
      o.textContent = `${v.title || sha.slice(0, 8)}${mon}`;
      sel.appendChild(o);
    }
  }

  function showSha(sha) {
    const body = document.getElementById("ly-body");
    const head = document.getElementById("ly-head");
    const lic = document.getElementById("ly-license");
    if (!body || !index) return;
    if (!sha || !index.by_sha256[sha]) {
      body.className = "ly-body ly-empty";
      body.textContent = "Lyrics appear here when available for the track.";
      if (head) head.textContent = "Select a song…";
      return;
    }
    const v = index.by_sha256[sha];
    if (head) {
      head.innerHTML = `<span class="ly-now">${escapeHtml(v.title || "")}</span>` +
        (v.moniker ? ` · <em>${escapeHtml(v.moniker)}</em>` : "") +
        (v.album ? ` · ${escapeHtml(v.album)}` : "") +
        ` · ${escapeHtml(v.artist || "Excavationpro")}`;
    }
    body.className = "ly-body";
    body.textContent = v.lyrics || "";
    if (lic) {
      lic.innerHTML =
        escapeHtml(v.copyright || index.copyright || "") +
        "<br>" +
        escapeHtml(v.license || index.license || "") +
        ' · <a href="https://eternalhaven.ca/lygo-music-license.html" target="_blank" rel="noopener">LYGO Music License v1.0</a>';
    }
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function currentSha() {
    try {
      if (typeof tracks !== "undefined" && typeof current !== "undefined" && tracks[current]) {
        return tracks[current].sha256 || tracks[current].sha || "";
      }
      if (window.LYGO_NOW && window.LYGO_NOW.sha256) return window.LYGO_NOW.sha256;
    } catch (e) {}
    return "";
  }

  function showNowPlaying() {
    const sha = currentSha();
    if (!sha) {
      const body = document.getElementById("ly-body");
      if (body) {
        body.className = "ly-body ly-empty";
        body.textContent = "Nothing playing — start a track, then click Now playing.";
      }
      return;
    }
    const sel = document.getElementById("ly-select");
    if (sel) {
      // ensure option exists
      if (![...sel.options].some((o) => o.value === sha)) {
        fillSelect("");
      }
      sel.value = sha;
    }
    showSha(sha);
    // switch to lyrics tab
    document.querySelector('.tabs [data-tab="lyrics"]')?.click();
  }

  async function loadIndex() {
    for (const url of INDEX_URLS) {
      try {
        const r = await fetch(url, { cache: "no-cache" });
        if (!r.ok) continue;
        index = await r.json();
        loaded = true;
        console.info(SIG, "loaded", url, Object.keys(index.by_sha256 || {}).length, "lyrics");
        fillSelect("");
        const lic = document.getElementById("ly-license");
        if (lic && index.license) {
          lic.innerHTML =
            escapeHtml(index.copyright || "") +
            "<br>" +
            escapeHtml(index.license) +
            ' · <a href="https://eternalhaven.ca/lygo-music-license.html" target="_blank" rel="noopener">License</a>';
        }
        // auto-show if now playing has lyrics
        const sha = currentSha();
        if (sha && index.by_sha256[sha]) showSha(sha);
        return;
      } catch (e) {
        /* try next */
      }
    }
    console.warn(SIG, "lyrics_index.json not found");
  }

  function boot() {
    ensureUi();
    loadIndex();
    // when track changes, soft-update if lyrics tab visible
    document.addEventListener("lygo-track-change", () => {
      const panel = document.getElementById("panel-lyrics");
      if (panel && panel.style.display !== "none") showNowPlaying();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
  window.LYGO_LYRICS = { showNowPlaying, reload: loadIndex, sig: SIG };
})();
