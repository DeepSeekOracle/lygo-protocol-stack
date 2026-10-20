/**
 * LYGO Play Listing — ADDITIVE plugin (never touches playIndex / audio.src).
 * Signature: Δ9Φ963-PLAY-LISTING-ADDITIVE-v1
 *
 * Load: <script src="listen-plugins/play-listing.js?v=5" defer></script>
 * Mount: #play-listing-mount
 *
 * If this file fails to load or throws, core player keeps working.
 * v4: write queue; getCurrent resolve; MIN_SEC 12
 * v5: new jsonblob after 404; dual-write localStorage cache so totals never die offline;
 *     merge remote+local by max per track; keep board warm with PUT on poll success.
 */
(function () {
  "use strict";

  try {
    initPlayListing();
  } catch (err) {
    console.error("[play-listing] init failed (player unaffected)", err);
  }

  function initPlayListing() {
    // Recreated 2026-07-19 after prior blob expired (jsonblob free TTL) → total frozen at 27
    var BLOB =
      "https://jsonblob.com/api/jsonBlob/019f7b41-4e4a-7856-8ad1-9248e1abf0a2";
    var DWYL = "https://hits.dwyl.com/excavationpro/";
    var TOTAL_KEY = "listen-total-plays-v2";
    var HF_COUNTS =
      "https://huggingface.co/datasets/DeepSeekOracle/excavationpro-music-stream/resolve/main/play/play_counts.json";
    var LS_CLIENT = "lygo_play_listing_client_v1";
    var LS_SESSION = "lygo_play_listing_session_v1";
    var LS_CHAIN = "lygo_play_listing_chain_v1";
    var LS_BOARD = "lygo_play_listing_board_cache_v1";
    var MIN_SEC = 12;
    var MIN_RATIO = 0.3;
    var POLL_MS = 20000;
    var LS_PENDING = "lygo_play_listing_pending_v1";

    var audio = document.getElementById("audio");
    var mount = document.getElementById("play-listing-mount");
    if (!audio || !mount) {
      console.warn("[play-listing] missing #audio or #play-listing-mount");
      return;
    }

    var tracks = loadTracks();
    var titleBySha = {};
    for (var i = 0; i < tracks.length; i++) {
      if (tracks[i] && tracks[i].sha256) {
        titleBySha[tracks[i].sha256] = tracks[i].title || tracks[i].sha256.slice(0, 12);
      }
    }

    var clientId = loadClientId();
    var sessionCounted = loadSession();
    var chain = loadChain();
    var accum = 0;
    var lastTick = 0;
    var activeSha = null;
    var pending = false;
    var writing = false;
    var lastAgg = null; // last good board snapshot for badge-only updates
    var refreshInFlight = false;

    injectStyles();
    injectUI(mount);
    bindAudio();
    refreshBoard();
    setInterval(function () {
      if (document.visibilityState === "visible" && !writing) refreshBoard();
    }, POLL_MS);

    console.info(
      "[play-listing] additive plugin ready · tracks=",
      tracks.length,
      "· never touches playIndex"
    );

    // ---- tracks from boot or LYGO_LISTEN ----
    function loadTracks() {
      try {
        if (window.LYGO_LISTEN && typeof window.LYGO_LISTEN.getTracks === "function") {
          var t = window.LYGO_LISTEN.getTracks();
          if (t && t.length) return t;
        }
      } catch (e) {}
      try {
        var boot = document.getElementById("boot");
        if (boot && boot.textContent) {
          var data = JSON.parse(boot.textContent);
          var pl = (data && data.playlist) || {};
          return pl.tracks || [];
        }
      } catch (e2) {
        console.warn("[play-listing] boot parse", e2);
      }
      return [];
    }

    function loadClientId() {
      try {
        var id = localStorage.getItem(LS_CLIENT);
        if (id) return id;
        id = "web-" + Math.random().toString(36).slice(2) + Date.now().toString(36);
        localStorage.setItem(LS_CLIENT, id);
        return id;
      } catch (e) {
        return "web-anon";
      }
    }

    function loadSession() {
      try {
        return new Set(JSON.parse(sessionStorage.getItem(LS_SESSION) || "[]"));
      } catch (e) {
        return new Set();
      }
    }

    function saveSession() {
      try {
        sessionStorage.setItem(LS_SESSION, JSON.stringify(Array.from(sessionCounted)));
      } catch (e) {}
    }

    function loadChain() {
      try {
        var c = JSON.parse(localStorage.getItem(LS_CHAIN) || "null");
        if (c && Array.isArray(c.events)) return c;
      } catch (e) {}
      return {
        signature: "LYGO-PLAY-LISTING-CHAIN-v1",
        append_only: true,
        events: [],
        tip_hash: "0".repeat(64),
      };
    }

    function saveChain() {
      try {
        if (chain.events.length > 2000) chain.events = chain.events.slice(-2000);
        chain.updated_at = new Date().toISOString();
        localStorage.setItem(LS_CHAIN, JSON.stringify(chain));
      } catch (e) {}
    }

    // ---- UI ----
    function injectStyles() {
      if (document.getElementById("play-listing-css")) return;
      var s = document.createElement("style");
      s.id = "play-listing-css";
      s.textContent =
        "#play-listing-mount{margin:12px 0 16px}" +
        ".pl-trophy{display:flex;align-items:center;gap:12px;flex-wrap:wrap;padding:12px 14px;border-radius:12px;" +
        "border:1px solid rgba(212,175,55,.5);background:linear-gradient(135deg,rgba(212,175,55,.16),rgba(176,107,255,.1));" +
        "margin-bottom:10px;box-shadow:0 0 20px rgba(212,175,55,.15)}" +
        ".pl-trophy .cup{font-size:1.6rem}" +
        ".pl-trophy .big{font-family:Cinzel,serif;font-size:1.5rem;font-weight:700;color:#d4af37;font-variant-numeric:tabular-nums}" +
        ".pl-trophy .sub{font-size:.72rem;color:#9a9ab0;margin-top:2px}" +
        ".pl-board{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px}" +
        ".pl-box{border-radius:12px;padding:12px;border:1px solid rgba(0,240,255,.22);background:rgba(12,12,22,.9);min-height:140px}" +
        ".pl-box h3{margin:0 0 8px;font-size:.78rem;letter-spacing:.06em;text-transform:uppercase;color:#d4af37;font-family:Cinzel,serif}" +
        ".pl-box.most{border-color:rgba(212,175,55,.45)}" +
        ".pl-box.least{border-color:rgba(176,107,255,.4)}" +
        ".pl-box.never{border-color:rgba(255,255,255,.12)}" +
        ".pl-box.recent{border-color:rgba(61,214,140,.4)}" +
        ".pl-box ol,.pl-box ul{margin:0;padding-left:1.1rem;font-size:.78rem;max-height:180px;overflow:auto;color:#c8c8d8}" +
        ".pl-box li{margin:4px 0;cursor:pointer;color:#eee;line-height:1.35}" +
        ".pl-box li:hover{color:#00f0ff}" +
        ".pl-box .n{color:#d4af37;font-weight:700;font-variant-numeric:tabular-nums}" +
        ".pl-box .empty{font-style:italic;color:#888;cursor:default}" +
        ".pl-row-badge{font-size:.68rem;color:#9a9ab0;font-variant-numeric:tabular-nums;min-width:2.8rem;text-align:right}" +
        ".pl-row-badge b{color:#00f0ff;font-weight:700}" +
        ".pl-row-badge.hot b{color:#d4af37}" +
        ".pl-export{margin-top:8px;font-size:.72rem}" +
        ".pl-export button{cursor:pointer;border-radius:8px;padding:6px 10px;font-size:.72rem;border:1px solid rgba(212,175,55,.4);" +
        "background:rgba(212,175,55,.1);color:#d4af37}";
      document.head.appendChild(s);
    }

    function injectUI(el) {
      el.innerHTML =
        '<div class="pl-trophy" id="pl-trophy">' +
        '<span class="cup" aria-hidden="true">🏆</span>' +
        '<div><div class="big" id="pl-total">▶ plays</div>' +
        '<div class="sub">Global listens · counts after ~12s play · does not affect the player</div></div></div>' +
        '<div class="pl-board">' +
        '<div class="pl-box most"><h3>Most played</h3><ol id="pl-most"><li class="empty">Loading…</li></ol></div>' +
        '<div class="pl-box least"><h3>Least played</h3><ol id="pl-least"><li class="empty">Loading…</li></ol></div>' +
        '<div class="pl-box never"><h3>Not played yet</h3><ul id="pl-never"><li class="empty">Loading…</li></ul></div>' +
        '<div class="pl-box recent"><h3>Recent global</h3><ul id="pl-recent"><li class="empty">Loading…</li></ul></div>' +
        "</div>" +
        '<div class="pl-export"><button type="button" id="pl-export-btn">Export local play chain</button></div>';
      var btn = document.getElementById("pl-export-btn");
      if (btn) {
        btn.onclick = function () {
          var blob = new Blob(
            [JSON.stringify(Object.assign({}, chain, { client_id: clientId, exported_at: new Date().toISOString() }), null, 2)],
            { type: "application/json" }
          );
          var a = document.createElement("a");
          a.href = URL.createObjectURL(blob);
          a.download = "excavationpro-play-listing-export.json";
          a.click();
        };
      }
    }

    function fmt(n) {
      if (n == null || isNaN(n)) return "—";
      if (n >= 1e6) return (n / 1e6).toFixed(1) + "M";
      if (n >= 1e4) return (n / 1e3).toFixed(1) + "k";
      return String(n);
    }

    function esc(s) {
      return String(s || "").replace(/[&<>"']/g, function (c) {
        return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
      });
    }

    function titleOf(sha) {
      return titleBySha[sha] || (sha ? sha.slice(0, 12) + "…" : "?");
    }

    // ---- resolve current track WITHOUT using playIndex ----
    function trackFromAudio() {
      // Prefer player export (most reliable during continuous play)
      try {
        if (window.LYGO_LISTEN && typeof window.LYGO_LISTEN.getCurrent === "function") {
          var ci = window.LYGO_LISTEN.getCurrent();
          if (typeof ci === "number" && ci >= 0 && tracks[ci] && tracks[ci].sha256) {
            return tracks[ci];
          }
        }
      } catch (e0) {}

      var src = "";
      try {
        src = audio.currentSrc || audio.src || "";
      } catch (e) {
        src = "";
      }
      if (!src) return null;
      // normalize
      try {
        src = decodeURIComponent(src);
      } catch (e1) {}
      for (var i = 0; i < tracks.length; i++) {
        var sha = tracks[i] && tracks[i].sha256;
        if (!sha) continue;
        if (src.indexOf(sha) >= 0) return tracks[i];
        var u = tracks[i].stream_url || "";
        if (!u) continue;
        var base = u.split("?")[0];
        if (src.indexOf(base) >= 0 || src === u) return tracks[i];
        // filename only
        var file = sha + ".mp3";
        if (src.indexOf(file) >= 0) return tracks[i];
      }
      // hash in location
      try {
        var h = (location.hash || "").replace(/^#/, "");
        if (h.length >= 12) {
          for (var j = 0; j < tracks.length; j++) {
            if (tracks[j].sha256 && tracks[j].sha256.indexOf(h) === 0) return tracks[j];
            if (tracks[j].sha256 === h) return tracks[j];
          }
        }
      } catch (e2) {}
      return null;
    }

    function indexOfSha(sha) {
      for (var i = 0; i < tracks.length; i++) {
        if (tracks[i].sha256 === sha) return i;
      }
      return -1;
    }

    function playShaSafe(sha) {
      var idx = indexOfSha(sha);
      if (idx < 0) return;
      // Prefer official export hook
      try {
        if (window.LYGO_LISTEN && typeof window.LYGO_LISTEN.playIndex === "function") {
          window.LYGO_LISTEN.playIndex(idx);
          return;
        }
      } catch (e) {}
      // Fallback: click existing list button (does not redefine playIndex)
      try {
        var btn = document.querySelector('.row[data-i="' + idx + '"] [data-play], .row[data-i="' + idx + '"] button.play');
        if (btn) {
          btn.click();
          return;
        }
        var row = document.querySelector('.row[data-i="' + idx + '"]');
        if (row) row.click();
      } catch (e2) {
        console.warn("[play-listing] playShaSafe", e2);
      }
    }

    // ---- network ----
    function hitDwyl(key) {
      return fetch(DWYL + encodeURIComponent(key) + ".json", {
        cache: "no-store",
        mode: "cors",
      }).then(function (r) {
        if (!r.ok) throw new Error("dwyl " + r.status);
        return r.json();
      }).then(function (j) {
        var n = parseInt(j.message || j.count || "0", 10);
        return isNaN(n) ? 0 : n;
      });
    }

    function emptyAgg() {
      return {
        signature: "LYGO-PLAY-AGGREGATE-v1",
        by_track: {},
        recent: [],
        most_played: [],
        least_played: [],
        total_plays: 0,
        unique_tracks_played: 0,
        updated_at: new Date().toISOString(),
      };
    }

    function loadLocalBoard() {
      try {
        var c = JSON.parse(localStorage.getItem(LS_BOARD) || "null");
        if (c && typeof c === "object") {
          if (!c.by_track) c.by_track = {};
          return c;
        }
      } catch (e) {}
      return null;
    }

    function saveLocalBoard(agg) {
      try {
        localStorage.setItem(LS_BOARD, JSON.stringify(agg));
      } catch (e) {}
    }

    /** Merge two boards taking max plays per track (never lose local progress). */
    function mergeAggs(a, b) {
      var out = emptyAgg();
      var maps = [a && a.by_track, b && b.by_track];
      maps.forEach(function (m) {
        if (!m) return;
        Object.keys(m).forEach(function (k) {
          var n = Number(m[k]) || 0;
          out.by_track[k] = Math.max(Number(out.by_track[k]) || 0, n);
        });
      });
      var recent = []
        .concat((a && a.recent) || [], (b && b.recent) || [])
        .filter(Boolean);
      // dedupe recent by sha keep newest first
      var seen = {};
      out.recent = [];
      recent.forEach(function (it) {
        var s = it && it.sha256;
        if (!s || seen[s]) return;
        seen[s] = true;
        out.recent.push({
          sha256: s,
          title: it.title || titleOf(s),
          plays: out.by_track[s] || it.plays || 0,
          ts: it.ts || out.updated_at,
        });
      });
      out.recent = out.recent.slice(0, 40);
      var sum = 0;
      Object.keys(out.by_track).forEach(function (k) {
        sum += Number(out.by_track[k]) || 0;
      });
      out.total_plays = sum;
      out.unique_tracks_played = Object.keys(out.by_track).length;
      var r = rank(out.by_track);
      out.most_played = r.most;
      out.least_played = r.least;
      out.updated_at = new Date().toISOString();
      return out;
    }

    function getBlob() {
      var local = loadLocalBoard();
      return fetch(BLOB, {
        cache: "no-store",
        mode: "cors",
        headers: { Accept: "application/json" },
      })
        .then(function (r) {
          if (!r.ok) throw new Error("blob " + r.status);
          return r.json();
        })
        .then(function (remote) {
          if (!remote || typeof remote !== "object") remote = emptyAgg();
          if (!remote.by_track) remote.by_track = {};
          var merged = mergeAggs(remote, local);
          saveLocalBoard(merged);
          return merged;
        })
        .catch(function (err) {
          // Remote dead (jsonblob expiry) — use local so UI keeps working
          if (local) {
            console.warn("[play-listing] remote board unavailable, using local cache", err && err.message);
            return local;
          }
          return fetch(HF_COUNTS, { cache: "no-store", mode: "cors" })
            .then(function (r) {
              if (!r.ok) throw new Error("hf");
              return r.json();
            })
            .then(function (hf) {
              var m = mergeAggs(hf, null);
              saveLocalBoard(m);
              return m;
            })
            .catch(function () {
              return emptyAgg();
            });
        });
    }

    function putBlobRemote(agg) {
      return fetch(BLOB, {
        method: "PUT",
        mode: "cors",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify(agg),
      }).then(function (r) {
        if (!r.ok) throw new Error("blob put " + r.status);
        return true;
      });
    }

    function putBlob(agg) {
      // Always persist locally first (durable for this browser / device)
      saveLocalBoard(agg);
      return putBlobRemote(agg);
    }

    function rank(by) {
      var arr = [];
      Object.keys(by || {}).forEach(function (s) {
        var n = Number(by[s]) || 0;
        if (n > 0) arr.push({ sha256: s, plays: n, title: titleOf(s) });
      });
      if (!arr.length) return { most: [], least: [] };

      // Most: highest plays first
      var most = arr
        .slice()
        .sort(function (a, b) {
          return b.plays - a.plays || a.sha256.localeCompare(b.sha256);
        })
        .slice(0, 15);

      // Least among tracks that HAVE plays — lowest first.
      // When many tracks share the same low count, exclude "most" so the two
      // charts are not identical (old bug: all plays=1 → same 15 titles).
      var byAsc = arr.slice().sort(function (a, b) {
        return a.plays - b.plays || a.sha256.localeCompare(b.sha256);
      });
      var mostSet = {};
      for (var mi = 0; mi < most.length; mi++) mostSet[most[mi].sha256] = true;

      var least = [];
      if (arr.length > most.length) {
        for (var i = 0; i < byAsc.length && least.length < 15; i++) {
          if (!mostSet[byAsc[i].sha256]) least.push(byAsc[i]);
        }
      }
      // Not enough non-most tracks: take true lowest, reverse-sha on ties so
      // order differs from most when all counts are equal.
      if (least.length < 3) {
        least = arr
          .slice()
          .sort(function (a, b) {
            return a.plays - b.plays || b.sha256.localeCompare(a.sha256);
          })
          .slice(0, 15);
      }

      // Fresh titles from local playlist map (board may have stale long seeds)
      function retitle(list) {
        return list.map(function (it) {
          return {
            sha256: it.sha256,
            plays: it.plays,
            title: titleOf(it.sha256) || it.title || it.sha256.slice(0, 12),
          };
        });
      }
      return { most: retitle(most), least: retitle(least) };
    }

    function renderBoard(agg) {
      var by = agg.by_track || {};
      // Prefer sum of by_track when board total is stale/wrong
      var sum = 0;
      Object.keys(by).forEach(function (k) {
        sum += Number(by[k]) || 0;
      });
      var total =
        typeof agg.total_plays === "number"
          ? Math.max(agg.total_plays, sum)
          : sum;
      var elTot = document.getElementById("pl-total");
      if (elTot) elTot.textContent = fmt(total) + " plays";

      // Always recompute ranks from by_track (ignore stale most_played/least_played arrays)
      var ranks = rank(by);
      var most = ranks.most.slice(0, 15);
      var least = ranks.least.slice(0, 15);
      var recent = (agg.recent || []).slice(0, 15).map(function (it) {
        return {
          sha256: it.sha256,
          plays: it.plays,
          title: titleOf(it.sha256) || it.title || (it.sha256 || "").slice(0, 12),
          ts: it.ts,
        };
      });

      var never = [];
      var pool = [];
      for (var i = 0; i < tracks.length; i++) {
        var sh = tracks[i].sha256;
        if (sh && !by[sh]) pool.push(tracks[i]);
      }
      for (var a = pool.length - 1; a > 0; a--) {
        var b = Math.floor(Math.random() * (a + 1));
        var tmp = pool[a];
        pool[a] = pool[b];
        pool[b] = tmp;
      }
      never = pool.slice(0, 15);

      fillList("pl-most", most, "most");
      fillList("pl-least", least, "least");
      fillList(
        "pl-never",
        never.map(function (t) {
          return { sha256: t.sha256, title: t.title, plays: 0 };
        }),
        "never"
      );
      fillList("pl-recent", recent, "recent");
      badgeRows(by);
    }

    function fillList(id, items, mode) {
      var el = document.getElementById(id);
      if (!el) return;
      if (!items || !items.length) {
        el.innerHTML =
          '<li class="empty">' +
          (mode === "never" ? "All listed tracks have plays" : "No public plays yet — listen ≥12s") +
          "</li>";
        return;
      }
      el.innerHTML = items
        .map(function (it) {
          var sha = it.sha256 || "";
          var title = it.title || titleOf(sha);
          var plays = it.plays != null ? it.plays : 0;
          if (mode === "never") {
            return '<li data-sha="' + esc(sha) + '">' + esc(title) + "</li>";
          }
          return (
            '<li data-sha="' +
            esc(sha) +
            '"><span class="n">' +
            fmt(plays) +
            "</span> · " +
            esc(title) +
            "</li>"
          );
        })
        .join("");
      Array.prototype.forEach.call(el.querySelectorAll("li[data-sha]"), function (li) {
        li.addEventListener("click", function () {
          var sha = li.getAttribute("data-sha");
          if (sha) playShaSafe(sha);
        });
      });
    }

    function badgeRows(by) {
      // Non-invasive: append badge to rows if missing
      var rows = document.querySelectorAll(".row[data-i]");
      for (var r = 0; r < rows.length; r++) {
        var row = rows[r];
        var idx = +row.getAttribute("data-i");
        var t = tracks[idx];
        if (!t || !t.sha256) continue;
        var badge = row.querySelector(".pl-row-badge");
        if (!badge) {
          badge = document.createElement("div");
          badge.className = "pl-row-badge";
          var playBtn = row.querySelector("[data-play], button.play");
          if (playBtn && playBtn.parentNode === row) {
            row.insertBefore(badge, playBtn);
          } else {
            row.appendChild(badge);
          }
        }
        var n = by[t.sha256] || 0;
        badge.innerHTML = "<b>" + fmt(n) + "</b> ▶";
        if (n >= 10) badge.classList.add("hot");
        else badge.classList.remove("hot");
        badge.title = n + " global plays";
      }
    }

    function refreshBoard() {
      if (writing || refreshInFlight) return;
      refreshInFlight = true;
      // Prefer public board; fallback HF
      getBlob()
        .then(function (agg) {
          if (!agg || typeof agg !== "object") agg = {};
          if (!agg.by_track) agg.by_track = {};
          lastAgg = agg;
          renderBoard(agg);
        })
        .catch(function () {
          return fetch(HF_COUNTS, { cache: "no-store", mode: "cors" })
            .then(function (r) {
              if (!r.ok) throw new Error("hf");
              return r.json();
            })
            .then(function (agg) {
              if (!agg || typeof agg !== "object") agg = {};
              if (!agg.by_track) agg.by_track = {};
              lastAgg = agg;
              renderBoard(agg);
            })
            .catch(function () {
              if (lastAgg) {
                renderBoard(lastAgg);
                return;
              }
              var el = document.getElementById("pl-total");
              if (el) el.textContent = "▶ plays";
            });
        })
        .then(function () {
          refreshInFlight = false;
        }, function () {
          refreshInFlight = false;
        });
    }

    // Observe list re-renders — badge only (do NOT re-fetch board every paint)
    var list = document.getElementById("list");
    if (list && window.MutationObserver) {
      var moTimer = null;
      new MutationObserver(function () {
        if (moTimer) clearTimeout(moTimer);
        moTimer = setTimeout(function () {
          if (lastAgg && lastAgg.by_track) badgeRows(lastAgg.by_track);
        }, 350);
      }).observe(list, { childList: true });
    }

    // ---- count qualification ----
    function bindAudio() {
      audio.addEventListener("play", function () {
        var t = trackFromAudio();
        var sha = t && t.sha256;
        if (sha !== activeSha) {
          activeSha = sha;
          accum = 0;
        }
        lastTick = Date.now();
      });
      audio.addEventListener("pause", function () {
        if (lastTick) {
          accum += (Date.now() - lastTick) / 1000;
          lastTick = 0;
        }
        maybeCount();
      });
      audio.addEventListener("ended", function () {
        if (lastTick) {
          accum += (Date.now() - lastTick) / 1000;
          lastTick = 0;
        }
        var t = trackFromAudio();
        if (t && t.sha256) qualifyAndRecord(t);
      });
      audio.addEventListener("timeupdate", function () {
        if (!audio.paused) maybeCount();
      });
    }

    function maybeCount() {
      var t = trackFromAudio();
      if (!t || !t.sha256) return;
      if (sessionCounted.has(t.sha256)) return;
      var played = accum + (lastTick ? (Date.now() - lastTick) / 1000 : 0);
      var dur = audio.duration;
      var enoughTime = played >= MIN_SEC;
      var enoughRatio = isFinite(dur) && dur > 0 && audio.currentTime / dur >= MIN_RATIO;
      if (enoughTime || enoughRatio) qualifyAndRecord(t);
    }

    // ---- pending queue (survives failed PUTs; never silent-drop) ----
    var writeQueue = loadPending();
    var countingLock = false; // one qualify pipeline at a time for session mark

    function loadPending() {
      try {
        var arr = JSON.parse(localStorage.getItem(LS_PENDING) || "[]");
        return Array.isArray(arr) ? arr : [];
      } catch (e) {
        return [];
      }
    }
    function savePending() {
      try {
        if (writeQueue.length > 200) writeQueue = writeQueue.slice(-200);
        localStorage.setItem(LS_PENDING, JSON.stringify(writeQueue));
      } catch (e) {}
    }
    function enqueueCount(sha, title) {
      if (!sha) return;
      writeQueue.push({
        sha256: sha,
        title: title || titleOf(sha),
        ts: new Date().toISOString(),
        inc: 1,
      });
      savePending();
      drainQueue();
    }

    function qualifyAndRecord(t) {
      if (!t || !t.sha256) return;
      if (sessionCounted.has(t.sha256)) return;
      if (countingLock) return;
      countingLock = true;

      // optimistic session mark to avoid double-fire while waiting 12s+network
      sessionCounted.add(t.sha256);
      saveSession();

      var played = accum + (lastTick ? (Date.now() - lastTick) / 1000 : 0);

      // local chain only (no player touch)
      var ev = {
        v: 1,
        event_id: (crypto.randomUUID && crypto.randomUUID()) || String(Date.now()) + Math.random(),
        track_sha256: t.sha256,
        title: t.title || null,
        ts: new Date().toISOString(),
        client_id: clientId,
        listen_sec: Math.max(played, MIN_SEC),
        prev_hash: chain.tip_hash || "0".repeat(64),
      };
      chain.events.push(ev);
      chain.tip_hash = ev.event_id;
      saveChain();

      // fire-and-forget dwyl (telemetry only; board is source of truth for UI)
      hitDwyl("stream-" + t.sha256.slice(0, 24)).catch(function () {});
      hitDwyl(TOTAL_KEY).catch(function () {});

      // queue board write (always; never drop)
      enqueueCount(t.sha256, t.title);
      console.info("[play-listing] queued count", (t.title || t.sha256).slice(0, 40));
      countingLock = false;
    }

    function drainQueue() {
      if (writing) return;
      if (!writeQueue.length) return;
      writing = true;
      var batch = writeQueue.slice(); // merge all pending into one GET/PUT
      var attempt = 0;

      function once() {
        return getBlob()
          .then(function (agg) {
            if (!agg || typeof agg !== "object") agg = {};
            if (!agg.by_track) agg.by_track = {};
            if (!agg.recent) agg.recent = [];

            batch.forEach(function (item) {
              var sha = item.sha256;
              if (!sha) return;
              var prev = Number(agg.by_track[sha]) || 0;
              var inc = Number(item.inc) || 1;
              agg.by_track[sha] = prev + inc;
              agg.recent.unshift({
                sha256: sha,
                title: item.title || titleOf(sha),
                plays: agg.by_track[sha],
                ts: item.ts || new Date().toISOString(),
              });
            });
            if (agg.recent.length > 40) agg.recent = agg.recent.slice(0, 40);

            var sum = 0;
            Object.keys(agg.by_track).forEach(function (k) {
              sum += Number(agg.by_track[k]) || 0;
            });
            agg.total_plays = sum;
            agg.unique_tracks_played = Object.keys(agg.by_track).length;
            agg.updated_at = new Date().toISOString();
            agg.signature = "LYGO-PLAY-AGGREGATE-v1";
            // Apply locally first so totals never freeze if remote is dead
            var rnk = rank(agg.by_track);
            agg.most_played = rnk.most;
            agg.least_played = rnk.least;
            lastAgg = agg;
            saveLocalBoard(agg);
            renderBoard(agg);
            // Drop queue only after local apply (avoid double-count on retry)
            writeQueue = writeQueue.slice(batch.length);
            savePending();
            console.info(
              "[play-listing] board local total=",
              agg.total_plays,
              "flushed=",
              batch.length,
              "pending=",
              writeQueue.length
            );
            // Best-effort remote warm (jsonblob free TTL can expire)
            return putBlobRemote(agg).catch(function (e) {
              console.warn(
                "[play-listing] remote board put failed (local OK)",
                e && e.message ? e.message : e
              );
              return false;
            });
          })
          .catch(function (e) {
            attempt++;
            console.warn("[play-listing] board write fail", attempt, e && e.message ? e.message : e);
            if (attempt < 5) {
              return new Promise(function (res) {
                setTimeout(res, 400 * attempt + Math.floor(Math.random() * 300));
              }).then(once);
            }
            throw e;
          });
      }

      once().then(
        function () {
          writing = false;
          if (writeQueue.length) setTimeout(drainQueue, 500);
        },
        function () {
          writing = false;
          setTimeout(drainQueue, 8000);
        }
      );
    }

    // retry pending on boot / visibility
    setTimeout(drainQueue, 1500);
    document.addEventListener("visibilitychange", function () {
      if (document.visibilityState === "visible") drainQueue();
    });
  }
})();
