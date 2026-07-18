/**
 * LYGO Play Listing — ADDITIVE plugin (never touches playIndex / audio.src).
 * Signature: Δ9Φ963-PLAY-LISTING-ADDITIVE-v1
 *
 * Load: <script src="listen-plugins/play-listing.js?v=1" defer></script>
 * Mount: #play-listing-mount
 *
 * If this file fails to load or throws, core player keeps working.
 */
(function () {
  "use strict";

  try {
    initPlayListing();
  } catch (err) {
    console.error("[play-listing] init failed (player unaffected)", err);
  }

  function initPlayListing() {
    var BLOB =
      "https://jsonblob.com/api/jsonBlob/019f7611-e28e-7de6-87df-5f5e4e8c4690";
    var DWYL = "https://hits.dwyl.com/excavationpro/";
    var TOTAL_KEY = "listen-total-plays-v2";
    var HF_COUNTS =
      "https://huggingface.co/datasets/DeepSeekOracle/excavationpro-music-stream/resolve/main/play/play_counts.json";
    var LS_CLIENT = "lygo_play_listing_client_v1";
    var LS_SESSION = "lygo_play_listing_session_v1";
    var LS_CHAIN = "lygo_play_listing_chain_v1";
    var MIN_SEC = 20;
    var MIN_RATIO = 0.35;
    var POLL_MS = 25000;

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

    injectStyles();
    injectUI(mount);
    bindAudio();
    refreshBoard();
    setInterval(function () {
      if (document.visibilityState === "visible") refreshBoard();
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
        '<div class="sub">Global listens · counts after ~20s play · does not affect the player</div></div></div>' +
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
      var src = "";
      try {
        src = audio.currentSrc || audio.src || "";
      } catch (e) {
        src = "";
      }
      if (!src) return null;
      for (var i = 0; i < tracks.length; i++) {
        var u = tracks[i].stream_url || "";
        if (!u) continue;
        if (src.indexOf(tracks[i].sha256) >= 0) return tracks[i];
        // strip query
        var base = u.split("?")[0];
        if (src.indexOf(base) >= 0 || src === u) return tracks[i];
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

    function getBlob() {
      return fetch(BLOB, {
        cache: "no-store",
        mode: "cors",
        headers: { Accept: "application/json" },
      }).then(function (r) {
        if (!r.ok) throw new Error("blob " + r.status);
        return r.json();
      });
    }

    function putBlob(agg) {
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

    function rank(by) {
      var arr = [];
      Object.keys(by || {}).forEach(function (s) {
        var n = by[s] || 0;
        if (n > 0) arr.push({ sha256: s, plays: n, title: titleOf(s) });
      });
      var most = arr.slice().sort(function (a, b) {
        return b.plays - a.plays || a.sha256.localeCompare(b.sha256);
      }).slice(0, 15);
      var least = arr.slice().sort(function (a, b) {
        return a.plays - b.plays || a.sha256.localeCompare(b.sha256);
      }).slice(0, 15);
      return { most: most, least: least };
    }

    function renderBoard(agg) {
      var by = agg.by_track || {};
      var total = typeof agg.total_plays === "number" ? agg.total_plays : 0;
      var elTot = document.getElementById("pl-total");
      if (elTot) elTot.textContent = fmt(total) + " plays";

      var ranks = rank(by);
      var most = (agg.most_played && agg.most_played.length ? agg.most_played : ranks.most).slice(0, 15);
      var least = (agg.least_played && agg.least_played.length ? agg.least_played : ranks.least).slice(0, 15);
      var recent = (agg.recent || []).slice(0, 15);

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
          (mode === "never" ? "All listed tracks have plays" : "No public plays yet — listen ≥20s") +
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
      // Prefer public board; fallback HF
      getBlob()
        .then(function (agg) {
          if (!agg.by_track) agg.by_track = {};
          renderBoard(agg);
        })
        .catch(function () {
          return fetch(HF_COUNTS, { cache: "no-store", mode: "cors" })
            .then(function (r) {
              if (!r.ok) throw new Error("hf");
              return r.json();
            })
            .then(function (agg) {
              if (!agg.by_track) agg.by_track = {};
              renderBoard(agg);
            })
            .catch(function () {
              var el = document.getElementById("pl-total");
              if (el) el.textContent = "▶ plays";
            });
        });
    }

    // Observe list re-renders to re-badge
    var list = document.getElementById("list");
    if (list && window.MutationObserver) {
      var moTimer = null;
      new MutationObserver(function () {
        if (moTimer) clearTimeout(moTimer);
        moTimer = setTimeout(function () {
          // re-apply badges from last board if we have blob cached in DOM total
          refreshBoard();
        }, 400);
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

    function qualifyAndRecord(t) {
      if (!t || !t.sha256 || sessionCounted.has(t.sha256) || pending) return;
      pending = true;
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

      // Global increment + board merge (async; never blocks UI)
      Promise.resolve()
        .then(function () {
          return Promise.all([
            hitDwyl("stream-" + t.sha256.slice(0, 24)).catch(function () {
              return 0;
            }),
            hitDwyl(TOTAL_KEY).catch(function () {
              return 0;
            }),
          ]);
        })
        .then(function (pair) {
          var trackN = pair[0];
          var totalN = pair[1];
          return mergeBoard(t.sha256, t.title, trackN, totalN);
        })
        .then(function () {
          console.info("[play-listing] counted", (t.title || "").slice(0, 40));
        })
        .catch(function (e) {
          console.warn("[play-listing] count pipeline", e);
        })
        .then(function () {
          pending = false;
        });
    }

    function mergeBoard(sha, title, trackN, totalN) {
      if (writing) return Promise.resolve();
      writing = true;
      var attempt = 0;
      function once() {
        return getBlob()
          .then(function (agg) {
            if (!agg.by_track) agg.by_track = {};
            if (!agg.recent) agg.recent = [];
            var prev = agg.by_track[sha] || 0;
            // Prefer durable dwyl count; else bump by 1 from previous board value
            agg.by_track[sha] = Math.max(prev, trackN || prev + 1);
            var sum = 0;
            Object.keys(agg.by_track).forEach(function (k) {
              sum += Number(agg.by_track[k]) || 0;
            });
            agg.total_plays = Math.max(agg.total_plays || 0, totalN || 0, sum);
            agg.unique_tracks_played = Object.keys(agg.by_track).length;
            agg.updated_at = new Date().toISOString();
            agg.signature = "LYGO-PLAY-AGGREGATE-v1";
            agg.recent.unshift({
              sha256: sha,
              title: title || titleOf(sha),
              plays: agg.by_track[sha],
              ts: agg.updated_at,
            });
            if (agg.recent.length > 40) agg.recent = agg.recent.slice(0, 40);
            var r = rank(agg.by_track);
            agg.most_played = r.most;
            agg.least_played = r.least;
            return putBlob(agg).then(function () {
              renderBoard(agg);
            });
          })
          .catch(function (e) {
            attempt++;
            if (attempt < 3) {
              return new Promise(function (res) {
                setTimeout(res, 200 * attempt);
              }).then(once);
            }
            throw e;
          });
      }
      return once().then(
        function () {
          writing = false;
        },
        function () {
          writing = false;
        }
      );
    }
  }
})();
