/* LYGO Public Witness v1.0.1 — resources, canon, named shadows. Never invent payloads. */
(function () {
  "use strict";
  const SIG = "Delta9Phi963-PUBLIC-WITNESS-v1.1.0";
  const HF_FEEDS = [
    "https://huggingface.co/datasets/DeepSeekOracle/lygo-public-witness-feed/resolve/main/feed.json",
    "https://deepseekoracle-lattice-marines-ledger.hf.space/witness/feed.json",
    "feed-snapshot.json"
  ];
  const CANON_URLS = {
    anchors: "https://deepseekoracle.github.io/lygo-protocol-stack/network_builder/IMMUTABLE_ANCHORS.json",
    star: "https://deepseekoracle.github.io/lygo-protocol-stack/haven_star_chart/haven_star_chart_feed.json",
    agora: "https://deepseekoracle.github.io/lygo-protocol-stack/agent-agora/api/pulse.json",
    lattice: "https://deepseekoracle.github.io/lygo-protocol-stack/GIT_LATTICE_OVERVIEW.json"
  };
  const REF_URLS = {
    usgs: "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson",
    eonet: "https://eonet.gsfc.nasa.gov/api/v3/events?status=open&limit=40",
    iss: "https://api.wheretheiss.at/v1/satellites/25544"
  };

  const canvas = document.getElementById("globe");
  const ctx = canvas.getContext("2d");
  const state = {
    mode: "earth",
    filter: "all",
    rot: 0.4,
    tilt: 0.18,
    dragging: false,
    lastX: 0,
    lastY: 0,
    layers: { quakes: true, events: true, iss: true, alerts: true, floods: true, launches: true, aurora: true, flights: true, weather: true, radar: true, air: true, marine: true, canon: true, shadow: true },
    ref: { quakes: [], events: [], iss: null, alerts: [], floods: [], launches: [], aurora: [], flights: [], weather: [], radar: [], air: [], marine: [], world_alerts: [], markets: null, tle: 0, errors: {}, live: {} },
    canon: { anchors: [], star: [], eggs: [], agora: null, errors: {} },
    shadows: [],
    selected: null
  };

  const LAND = [
    [40, -100, 28, 18], [55, 10, 22, 12], [20, 20, 18, 20], [0, 25, 16, 18],
    [-20, 25, 14, 16], [35, 90, 30, 16], [-25, 135, 18, 14], [-15, -60, 16, 22],
    [60, -40, 8, 6], [-80, 0, 20, 8]
  ];

  function resize() {
    const r = canvas.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.max(320, r.width) * dpr;
    canvas.height = Math.max(320, r.height) * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function project(lat, lon, cx, cy, R, rot) {
    const phi = (lat * Math.PI) / 180;
    const lam = (lon * Math.PI) / 180 + rot;
    const x = Math.cos(phi) * Math.sin(lam);
    const y = Math.sin(phi) * Math.cos(state.tilt) + Math.cos(phi) * Math.cos(lam) * Math.sin(state.tilt);
    const z = Math.cos(phi) * Math.cos(lam) * Math.cos(state.tilt) - Math.sin(phi) * Math.sin(state.tilt);
    return { x: cx + x * R, y: cy - y * R, z, vis: z > -0.02 };
  }

  function hashAngle(s) {
    let h = 2166136261;
    for (let i = 0; i < String(s).length; i++) { h ^= String(s).charCodeAt(i); h = Math.imul(h, 16777619); }
    return (h >>> 0) / 4294967295;
  }

  function schematicLL(id) {
    const a = hashAngle(id);
    const b = hashAngle(id + ":b");
    return { lat: (a * 140) - 70, lon: (b * 360) - 180 };
  }

  function nodeLL(n) {
    if (typeof n.lat === "number" && typeof n.lon === "number") return { lat: n.lat, lon: n.lon };
    return schematicLL(n.id || n.label);
  }

  function drawHollow(x, y, r, color) {
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.4;
    ctx.setLineDash([3, 3]);
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  function drawGlobe(cx, cy, R, rot, kind) {
    const g = ctx.createRadialGradient(cx - R * 0.3, cy - R * 0.3, R * 0.2, cx, cy, R * 1.05);
    if (kind === "earth") {
      g.addColorStop(0, "#16324f");
      g.addColorStop(0.72, "#0b1a2e");
      g.addColorStop(1, "#05080f");
    } else {
      g.addColorStop(0, "#2a2208");
      g.addColorStop(0.72, "#161008");
      g.addColorStop(1, "#07050a");
    }
    ctx.beginPath();
    ctx.arc(cx, cy, R, 0, Math.PI * 2);
    ctx.fillStyle = g;
    ctx.fill();
    ctx.strokeStyle = kind === "earth" ? "#7dd3fc44" : "#d4a01766";
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.save();
    ctx.beginPath();
    ctx.arc(cx, cy, R, 0, Math.PI * 2);
    ctx.clip();

    ctx.globalAlpha = 0.2;
    ctx.strokeStyle = kind === "earth" ? "#7dd3fc" : "#fbbf24";
    ctx.lineWidth = 0.55;
    for (let lat = -60; lat <= 60; lat += 30) {
      ctx.beginPath();
      for (let lon = -180; lon <= 180; lon += 6) {
        const p = project(lat, lon, cx, cy, R, rot);
        if (lon === -180) ctx.moveTo(p.x, p.y); else ctx.lineTo(p.x, p.y);
      }
      ctx.stroke();
    }
    ctx.globalAlpha = 1;

    if (kind === "earth") {
      LAND.forEach(function (b) {
        const p = project(b[0], b[1], cx, cy, R, rot);
        if (!p.vis) return;
        ctx.fillStyle = "#1b3a28aa";
        ctx.beginPath();
        ctx.ellipse(p.x, p.y, (b[2] / 90) * R * 0.55, (b[3] / 90) * R * 0.4, 0, 0, Math.PI * 2);
        ctx.fill();
      });
      if (state.layers.quakes) {
        state.ref.quakes.forEach(function (q) {
          const p = project(q.lat, q.lon, cx, cy, R, rot);
          if (!p.vis) return;
          ctx.fillStyle = "rgba(245,158,11,0.85)";
          ctx.beginPath();
          ctx.arc(p.x, p.y, 1.6 + Math.max(2, q.mag || 2) * 0.7, 0, Math.PI * 2);
          ctx.fill();
        });
      }
      if (state.layers.events) {
        state.ref.events.forEach(function (e) {
          const p = project(e.lat, e.lon, cx, cy, R, rot);
          if (!p.vis) return;
          ctx.strokeStyle = "#fb7185";
          ctx.lineWidth = 1.2;
          ctx.beginPath();
          ctx.arc(p.x, p.y, 5, 0, Math.PI * 2);
          ctx.stroke();
        });
      }
      if (state.layers.iss && state.ref.iss) {
        const p = project(state.ref.iss.lat, state.ref.iss.lon, cx, cy, R, rot);
        if (p.vis) {
          ctx.fillStyle = "#7dd3fc";
          ctx.beginPath();
          ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
          ctx.fill();
        }
      }
      function dots(list, color, r) {
        (list || []).forEach(function (e) {
          const p = project(e.lat, e.lon, cx, cy, R, rot);
          if (!p.vis) return;
          ctx.fillStyle = color;
          ctx.beginPath();
          ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
          ctx.fill();
        });
      }
      if (state.layers.alerts) dots(state.ref.alerts, "rgba(251,191,36,0.9)", 3.2);
      if (state.layers.floods) dots(state.ref.floods, "rgba(56,189,248,0.9)", 3.2);
      if (state.layers.launches) dots(state.ref.launches, "rgba(244,114,182,0.95)", 4.2);
      if (state.layers.aurora) dots(state.ref.aurora, "rgba(52,211,153,0.55)", 2.2);
      if (state.layers.flights) dots(state.ref.flights, "rgba(125,211,252,0.7)", 1.8);
      if (state.layers.weather) dots(state.ref.weather, "rgba(250,250,250,0.85)", 3.4);
      if (state.layers.radar) dots(state.ref.radar, "rgba(96,165,250,0.85)", 4.0);
      if (state.layers.air) dots(state.ref.air, "rgba(192,132,252,0.9)", 3.6);
      if (state.layers.marine) dots(state.ref.marine, "rgba(45,212,191,0.9)", 3.4);
      if (state.layers.alerts) dots(state.ref.world_alerts, "rgba(251,146,60,0.9)", 3.3);
      if (state.layers.shadow) {
        state.shadows.filter(function (n) { return n.sphere !== "lattice"; }).forEach(function (n) {
          const ll = nodeLL(n);
          const p = project(ll.lat, ll.lon, cx, cy, R, rot);
          if (!p.vis) return;
          const live = n.kind === "resource" && resourceLive(n.id);
          if (live) {
            ctx.fillStyle = "#34d399";
            ctx.beginPath();
            ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
            ctx.fill();
          } else {
            drawHollow(p.x, p.y, n.kind === "resource" ? 7 : 9, "#a78bfa");
          }
        });
      }
    } else {
      const nodes = state.canon.anchors.concat(state.canon.star).concat(state.canon.eggs);
      if (state.layers.canon) {
        nodes.forEach(function (n, i) {
          const ll = schematicLL(n.id || n.node_id || String(i));
          const p = project(ll.lat, ll.lon, cx, cy, R, rot);
          if (!p.vis) return;
          ctx.fillStyle = n.kind === "egg" ? "#34d399" : n.kind === "star" ? "#fbbf24" : "#d4a017";
          ctx.beginPath();
          ctx.arc(p.x, p.y, n.kind === "star" ? 3.2 : 2.3, 0, Math.PI * 2);
          ctx.fill();
        });
      }
      if (state.layers.shadow) {
        state.shadows.filter(function (n) { return n.sphere === "lattice"; }).forEach(function (n) {
          const ll = nodeLL(n);
          const p = project(ll.lat, ll.lon, cx, cy, R, rot);
          if (!p.vis) return;
          drawHollow(p.x, p.y, 10, "#c4b5fd");
        });
      }
    }
    ctx.restore();
    ctx.fillStyle = "#cbd5e1";
    ctx.font = "11px IBM Plex Mono, monospace";
    ctx.fillText(kind === "earth" ? "EARTH · resources + named shadows" : "LATTICE · canon + named shadows", cx - 108, cy + R + 18);
  }

  function resourceLive(id) {
    if (id === "resource_usgs") return !!state.ref.live.usgs;
    if (id === "resource_eonet") return !!state.ref.live.eonet;
    if (id === "resource_iss") return !!state.ref.live.iss;
    return false;
  }

  function frame() {
    const w = canvas.getBoundingClientRect().width;
    const h = canvas.getBoundingClientRect().height;
    ctx.clearRect(0, 0, w, h);
    if (state.mode === "split") {
      drawGlobe(w * 0.28, h * 0.48, Math.min(w, h) * 0.28, state.rot, "earth");
      drawGlobe(w * 0.72, h * 0.48, Math.min(w, h) * 0.28, state.rot + 0.35, "lattice");
    } else if (state.mode === "lattice") {
      drawGlobe(w / 2, h * 0.48, Math.min(w, h) * 0.38, state.rot, "lattice");
    } else {
      drawGlobe(w / 2, h * 0.48, Math.min(w, h) * 0.38, state.rot, "earth");
    }
    if (!state.dragging) state.rot += 0.0022;
    requestAnimationFrame(frame);
  }

  async function getJson(url) {
    const ctrl = new AbortController();
    const t = setTimeout(function () { ctrl.abort(); }, 18000);
    try {
      const res = await fetch(url, { signal: ctrl.signal });
      if (!res.ok) throw new Error("HTTP " + res.status);
      return await res.json();
    } finally {
      clearTimeout(t);
    }
  }

  function setStatus(id, mode, detail) {
    const el = document.getElementById(id);
    if (!el) return;
    if (mode === true || mode === "live") {
      el.textContent = "live";
      el.className = "tag ok";
    } else {
      el.textContent = detail || "shadow";
      el.className = "tag shadow";
    }
  }

  function escapeHtml(s) {
    return String(s || "").replace(/[&<>"]/g, function (c) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;" })[c];
    });
  }

  function feedItems() {
    const items = [];
    state.shadows.forEach(function (n) {
      const live = n.kind === "resource" && resourceLive(n.id);
      items.push({
        cls: live ? "ref" : "shadow",
        title: n.label,
        sub: (live ? "RESOURCE live · " : "SHADOW · ") + n.why,
        body: { class: live ? "RESOURCE" : "SHADOW", payload: null, why: n.why, public_checks: n.public_checks, id: n.id }
      });
    });
    if (state.ref.iss) {
      items.push({
        cls: "ref",
        title: "ISS " + state.ref.iss.lat.toFixed(2) + ", " + state.ref.iss.lon.toFixed(2),
        sub: "RESOURCE ping · public telemetry",
        body: state.ref.iss
      });
    }
    if (state.ref.markets) {
      items.push({ cls: "ref", title: "Public markets " + JSON.stringify(state.ref.markets).slice(0, 80), sub: "RESOURCE · CoinGecko public prices", body: state.ref.markets });
    }
    (state.ref.launches || []).slice(0, 6).forEach(function (e) {
      items.push({ cls: "ref", title: e.title, sub: "RESOURCE · upcoming launch pad", body: e });
    });
    (state.ref.alerts || []).slice(0, 5).forEach(function (e) {
      items.push({ cls: "ref", title: e.title, sub: "RESOURCE · NWS public alert", body: e });
    });
    (state.ref.floods || []).slice(0, 4).forEach(function (e) {
      items.push({ cls: "ref", title: e.title, sub: "RESOURCE · UK flood monitoring", body: e });
    });
    (state.ref.weather || []).forEach(function (e) {
      items.push({ cls: "ref", title: e.title, sub: "RESOURCE · Open-Meteo (CC BY 4.0)", body: e });
    });
    (state.ref.world_alerts || []).slice(0, 8).forEach(function (e) {
      items.push({ cls: "ref", title: e.title, sub: "RESOURCE · public CAP/WMO-style alert", body: e });
    });
    (state.ref.radar || []).slice(0, 5).forEach(function (e) {
      items.push({ cls: "ref", title: e.title, sub: "RESOURCE · RainViewer public mosaic (educational)", body: e });
    });
    (state.ref.air || []).forEach(function (e) {
      items.push({ cls: "ref", title: e.title, sub: "RESOURCE · Open-Meteo air quality", body: e });
    });
    (state.ref.marine || []).forEach(function (e) {
      items.push({ cls: "ref", title: e.title, sub: "RESOURCE · Open-Meteo marine", body: e });
    });
    state.ref.quakes.slice(0, 8).forEach(function (q) {
      items.push({ cls: "ref", title: "M" + q.mag.toFixed(1) + " " + q.place, sub: "RESOURCE · USGS", body: q });
    });
    state.ref.events.slice(0, 6).forEach(function (e) {
      items.push({ cls: "ref", title: e.title, sub: "RESOURCE · EONET", body: e });
    });
    state.canon.star.slice(0, 6).forEach(function (n) {
      items.push({ cls: "canon", title: n.node_name || n.node_id, sub: "CANON · Star Chart " + (n.status || ""), body: n });
    });
    state.canon.eggs.slice(0, 5).forEach(function (n) {
      items.push({ cls: "canon", title: n.id, sub: "CANON · lattice system", body: n });
    });
    const f = state.filter;
    return items.filter(function (it) {
      if (f === "all") return true;
      if (f === "resource") return it.cls === "ref";
      if (f === "canon") return it.cls === "canon";
      if (f === "shadow") return it.cls === "shadow";
      return true;
    });
  }

  function renderFeeds() {
    const ul = document.getElementById("feed");
    const items = feedItems();
    ul.innerHTML = items.slice(0, 32).map(function (it, i) {
      const tag = it.cls === "ref" ? "RESOURCE" : it.cls === "canon" ? "CANON" : "SHADOW";
      return "<li data-i=\"" + i + "\"><span class=\"tag " + it.cls + "\">" + tag + "</span>" +
        escapeHtml(it.title) + "<div class=\"legend\">" + escapeHtml(it.sub) + "</div></li>";
    }).join("");
    ul.querySelectorAll("li").forEach(function (li, i) {
      li.addEventListener("click", function () {
        state.selected = items[i];
        const it = items[i];
        const note = it.cls === "shadow"
          ? "Named shadow — existence only. Follow public_checks. Never invent the private payload."
          : (it.cls === "ref" ? "Public resource — usable infrastructure." : "On-lattice canon receipt.");
        document.getElementById("detail").textContent = JSON.stringify({ class: it.cls, note: note, body: it.body }, null, 2);
      });
    });
    document.getElementById("n-ref").textContent = String(
      state.ref.quakes.length + state.ref.events.length + (state.ref.iss ? 1 : 0) +
      (state.ref.alerts || []).length + (state.ref.floods || []).length +
      (state.ref.launches || []).length + (state.ref.flights || []).length +
      (state.ref.aurora || []).length + (state.ref.weather || []).length +
      (state.ref.radar || []).length + (state.ref.air || []).length +
      (state.ref.marine || []).length + (state.ref.world_alerts || []).length
    );
    document.getElementById("n-canon").textContent = String(
      state.canon.anchors.length + state.canon.star.length + state.canon.eggs.length
    );
    document.getElementById("n-shadow").textContent = String(state.shadows.filter(function (n) { return n.kind === "shadow" || !resourceLive(n.id); }).length);
  }

  function remember(feed) {
    try { localStorage.setItem("lygo-witness-last", JSON.stringify({ t: Date.now(), feed: feed })); } catch (e) {}
  }

  function recall() {
    try {
      const raw = localStorage.getItem("lygo-witness-last");
      if (!raw) return null;
      const pack = JSON.parse(raw);
      if (!pack || !pack.feed) return null;
      if (Date.now() - (pack.t || 0) > 6 * 3600 * 1000) return null;
      return pack.feed;
    } catch (e) { return null; }
  }

  function ingestHf(feed) {
    if (!feed) return;
    const by = {};
    (feed.points || []).forEach(function (p) {
      const k = p.layer || "other";
      (by[k] = by[k] || []).push(p);
    });
    if (by.quakes && by.quakes.length) state.ref.quakes = by.quakes;
    if (by.events && by.events.length) state.ref.events = by.events;
    if (by.iss && by.iss[0]) state.ref.iss = by.iss[0];
    if (by.alerts) state.ref.alerts = by.alerts;
    if (by.floods) state.ref.floods = by.floods;
    if (by.launches) state.ref.launches = by.launches;
    if (by.aurora) state.ref.aurora = by.aurora;
    if (by.flights) state.ref.flights = by.flights;
    if (by.weather) state.ref.weather = by.weather;
    if (by.radar) state.ref.radar = by.radar;
    if (by.air) state.ref.air = by.air;
    if (by.marine) state.ref.marine = by.marine;
    if (by.world_alerts) state.ref.world_alerts = by.world_alerts;
    if (by.water) state.ref.weather = (state.ref.weather || []).concat(by.water);
    if (by.disasters) state.ref.events = (state.ref.events || []).concat(by.disasters);
    (feed.sources || []).forEach(function (s) {
      if (s.role === "markets" && s.markets) state.ref.markets = s.markets;
      if (s.role === "tle") state.ref.tle = s.count || 0;
      if (s.id === "nws_alerts") setStatus("st-nws", s.ok ? true : "shadow", s.ok ? "live" : "named");
      if (s.id === "gdacs") setStatus("st-gdacs", s.ok ? true : "shadow", s.ok ? "live" : "named");
      if (s.id === "opensky_ne") setStatus("st-flights", s.ok ? true : "shadow", s.ok ? "live" : "named");
      if (s.id === "openmeteo_hubs") setStatus("st-wx", s.ok ? true : "shadow", s.ok ? "live" : "named");
      if (s.id === "rainviewer") setStatus("st-radar", s.ok ? true : "shadow", s.ok ? "live" : "named");
      if (s.role === "world_alerts" && s.ok) setStatus("st-walert", true);
      if (s.id === "openmeteo_aq") setStatus("st-aq", s.ok ? true : "shadow", s.ok ? "live" : "named");
      if (s.id === "dwd_warnings") setStatus("st-dwd", s.ok ? true : "shadow", s.ok ? "live" : "named");
    });
    setStatus("st-hf", feed.ok ? true : "shadow", feed.ok ? "live" : "named");
    const el = document.getElementById("n-hf");
    if (el) el.textContent = String(feed.point_count || (feed.points || []).length);
  }

  async function loadHfFeed() {
    let lastErr = null;
    for (let i = 0; i < HF_FEEDS.length; i++) {
      try {
        const feed = await getJson(HF_FEEDS[i]);
        if (feed && (feed.points || feed.sources)) {
          ingestHf(feed);
          remember(feed);
          return;
        }
      } catch (e) { lastErr = e; }
    }
    state.ref.errors.hf = String(lastErr || "no overlay");
    const stale = recall();
    if (stale) {
      ingestHf(stale);
      setStatus("st-hf", "shadow", "cached");
    } else {
      setStatus("st-hf", "shadow", "named");
    }
  }

  async function loadShadows() {
    try {
      const pack = await getJson("shadows.json");
      state.shadows = pack.nodes || [];
    } catch (e) {
      state.shadows = [];
    }
  }

  async function loadCanon() {
    try {
      const a = await getJson(CANON_URLS.anchors);
      const buckets = a.immutable_anchors || {};
      state.canon.anchors = [];
      Object.keys(buckets).forEach(function (k) {
        (buckets[k] || []).forEach(function (n) {
          state.canon.anchors.push({ id: n.id || n.label, label: n.label, url: n.url, kind: "anchor", group: k });
        });
      });
      setStatus("st-anchors", true);
    } catch (e) {
      state.canon.errors.anchors = String(e);
      setStatus("st-anchors", "shadow", "named");
    }
    try {
      const f = await getJson(CANON_URLS.star);
      state.canon.star = (f.entries || []).slice(0, 40).map(function (n) {
        return {
          id: n.node_id, node_id: n.node_id, node_name: n.node_name, status: n.status,
          kind: "star", event_type: n.event_type, skill_slug: n.skill_slug
        };
      });
      document.getElementById("n-chain").textContent = f.chain_valid ? "valid" : "invalid";
      setStatus("st-star", !!f.chain_valid);
    } catch (e) {
      state.canon.errors.star = String(e);
      setStatus("st-star", "shadow", "named");
    }
    try {
      const g = await getJson(CANON_URLS.lattice);
      const systems = g.systems;
      if (Array.isArray(systems)) {
        systems.forEach(function (h) {
          if (h && typeof h === "object") {
            state.canon.eggs.push({ id: h.id || h.name, kind: "egg", label: h.label || h.name || h.id });
          }
        });
      }
      (g.clawhub_mirror_slugs || []).slice(0, 40).forEach(function (k) {
        state.canon.eggs.push({ id: String(k), kind: "egg", label: String(k) });
      });
      setStatus("st-eggs", true);
    } catch (e) {
      state.canon.errors.eggs = String(e);
      setStatus("st-eggs", "shadow", "named");
    }
    try {
      state.canon.agora = await getJson(CANON_URLS.agora);
      setStatus("st-agora", true);
    } catch (e) {
      state.canon.errors.agora = String(e);
      setStatus("st-agora", "shadow", "named");
    }
  }

  async function loadRef() {
    try {
      const g = await getJson(REF_URLS.usgs);
      state.ref.quakes = (g.features || []).map(function (f) {
        const c = (f.geometry && f.geometry.coordinates) || [0, 0];
        return { lon: c[0], lat: c[1], mag: (f.properties && f.properties.mag) || 0, place: (f.properties && f.properties.place) || "quake" };
      });
      state.ref.live.usgs = true;
      setStatus("st-usgs", true);
    } catch (e) {
      state.ref.errors.usgs = String(e);
      state.ref.live.usgs = false;
      setStatus("st-usgs", "shadow", "named");
    }
    try {
      const ev = await getJson(REF_URLS.eonet);
      state.ref.events = [];
      (ev.events || []).forEach(function (e) {
        const geo = e.geometry && e.geometry[e.geometry.length - 1];
        if (!geo || !geo.coordinates) return;
        state.ref.events.push({ title: e.title, lon: geo.coordinates[0], lat: geo.coordinates[1], id: e.id });
      });
      state.ref.live.eonet = true;
      setStatus("st-eonet", true);
    } catch (e) {
      state.ref.errors.eonet = String(e);
      state.ref.live.eonet = false;
      setStatus("st-eonet", "shadow", "named");
    }
    try {
      const iss = await getJson(REF_URLS.iss);
      state.ref.iss = { lat: Number(iss.latitude), lon: Number(iss.longitude), alt: iss.altitude, name: "ISS" };
      state.ref.live.iss = true;
      setStatus("st-iss", true);
    } catch (e) {
      state.ref.errors.iss = String(e);
      state.ref.live.iss = false;
      setStatus("st-iss", "shadow", "named");
    }
    try {
      const wx = await getJson("https://api.open-meteo.com/v1/forecast?latitude=40.7,51.5,35.7&longitude=-74,-0.1,139.7&current=temperature_2m,wind_speed_10m");
      const hubs = ["New York", "London", "Tokyo"];
      const rows = Array.isArray(wx) ? wx : (wx && wx.latitude ? [wx] : []);
      if (rows.length) {
        state.ref.weather = rows.map(function (row, i) {
          const cur = row.current || {};
          return { lat: row.latitude, lon: row.longitude, title: hubs[i] + " " + cur.temperature_2m + "°", layer: "weather" };
        });
        setStatus("st-wx", true);
      }
    } catch (e) { state.ref.errors.wx = String(e); }
    try {
      state.ref.markets = await getJson("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd");
    } catch (e) { state.ref.errors.markets = String(e); }
    try {
      const L = await getJson("https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=8&mode=list");
      const pads = [];
      (L.results || []).forEach(function (row) {
        const pad = row.pad || {};
        const lat = parseFloat(pad.latitude), lon = parseFloat(pad.longitude);
        if (!isNaN(lat) && !isNaN(lon)) pads.push({ lat: lat, lon: lon, title: row.name || "launch", layer: "launches" });
      });
      if (pads.length) state.ref.launches = pads;
    } catch (e) { state.ref.errors.launches = String(e); }
  }

  async function refreshIss() {
    try {
      const iss = await getJson(REF_URLS.iss);
      state.ref.iss = { lat: Number(iss.latitude), lon: Number(iss.longitude), alt: iss.altitude, name: "ISS" };
      state.ref.live.iss = true;
      setStatus("st-iss", true);
    } catch (e) {
      state.ref.live.iss = false;
      setStatus("st-iss", "shadow", "named");
    }
  }

  async function ollamaSummary() {
    const out = document.getElementById("ollama-out");
    out.textContent = "Asking local Ollama at 127.0.0.1:11434 …";
    const payload = {
      class_note: "Public rows=RESOURCE. Ledger=CANON. Shadow nodes=existence + public_checks only. Never invent private payloads.",
      resources: { quakes: state.ref.quakes.length, events: state.ref.events.length, iss: !!state.ref.iss },
      shadows: state.shadows.map(function (n) { return n.id; }),
      star_sample: state.canon.star.slice(0, 4)
    };
    try {
      const res = await fetch("http://127.0.0.1:11434/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "llama3.2:1b",
          stream: false,
          prompt: "LYGO Public Witness. Name shadows, crunch public resources, never steal private node data.\n" + JSON.stringify(payload) + "\nSix short bullets."
        })
      });
      if (!res.ok) throw new Error("HTTP " + res.status);
      const j = await res.json();
      out.textContent = j.response || JSON.stringify(j);
    } catch (e) {
      out.textContent = "Local Ollama is a named optional node — not required. (" + e + ")";
    }
  }

  function bind() {
    document.querySelectorAll("[data-mode]").forEach(function (b) {
      b.addEventListener("click", function () {
        state.mode = b.getAttribute("data-mode");
        document.querySelectorAll("[data-mode]").forEach(function (x) { x.classList.toggle("on", x === b); });
      });
    });
    document.querySelectorAll("[data-layer]").forEach(function (b) {
      b.addEventListener("click", function () {
        const k = b.getAttribute("data-layer");
        state.layers[k] = !state.layers[k];
        b.classList.toggle("on", state.layers[k]);
      });
    });
    document.querySelectorAll("[data-filter]").forEach(function (b) {
      b.addEventListener("click", function () {
        state.filter = b.getAttribute("data-filter");
        document.querySelectorAll("[data-filter]").forEach(function (x) { x.classList.toggle("on", x === b); });
        renderFeeds();
      });
    });
    canvas.addEventListener("pointerdown", function (e) {
      state.dragging = true; state.lastX = e.clientX; state.lastY = e.clientY; canvas.setPointerCapture(e.pointerId);
    });
    canvas.addEventListener("pointerup", function () { state.dragging = false; });
    canvas.addEventListener("pointermove", function (e) {
      if (!state.dragging) return;
      state.rot += (e.clientX - state.lastX) * 0.008;
      state.tilt = Math.max(-0.8, Math.min(0.8, state.tilt + (e.clientY - state.lastY) * 0.004));
      state.lastX = e.clientX; state.lastY = e.clientY;
    });
    document.getElementById("btn-refresh").addEventListener("click", function () { boot(); });
    document.getElementById("btn-ollama").addEventListener("click", ollamaSummary);
    document.getElementById("btn-overlay").addEventListener("click", function () {
      document.getElementById("detail").textContent = JSON.stringify({
        signature: SIG,
        doctrine: "Name the shadow. Crunch public resources. Never invent private payloads.",
        resources: { quakes: state.ref.quakes.length, events: state.ref.events.length, iss: state.ref.iss, live: state.ref.live },
        shadows: state.shadows.map(function (n) { return { id: n.id, kind: n.kind, why: n.why, public_checks: n.public_checks, payload: null }; }),
        canon: { anchors: state.canon.anchors.length, star: state.canon.star.length, eggs: state.canon.eggs.length },
        live_star_chart_write: false
      }, null, 2);
    });
  }

  function epicPng(row) {
    const d = String(row.date || "").slice(0, 10).replace(/-/g, "/");
    const img = row.image;
    if (!d || !img) return "";
    return "https://epic.gsfc.nasa.gov/archive/natural/" + d + "/png/" + img + ".png";
  }

  async function loadCameras() {
    const grid = document.getElementById("cam-grid");
    if (!grid) return;
    let pack;
    try { pack = await getJson("cameras.json"); } catch (e) { grid.textContent = "Camera catalog unreachable — named shadow."; return; }
    const cams = pack.cameras || [];
    let epicSrc = "";
    const epic = cams.find(function (c) { return c.kind === "epic"; });
    if (epic && epic.api) {
      try {
        const rows = await getJson(epic.api);
        if (Array.isArray(rows) && rows[0]) epicSrc = epicPng(rows[0]);
      } catch (e) {}
    }
    const t = Date.now();
    grid.innerHTML = cams.map(function (c) {
      const href = c.href || "#";
      const legal = escapeHtml(c.owner + " · " + c.legal);
      if (c.kind === "still") {
        const src = c.src + (c.src.indexOf("?") >= 0 ? "&" : "?") + "t=" + t;
        return "<a class=\"cam\" href=\"" + href + "\" target=\"_blank\" rel=\"noopener\"><img src=\"" + src + "\" alt=\"" + escapeHtml(c.title) + "\" loading=\"lazy\"><div class=\"cap\"><b>" + escapeHtml(c.title) + "</b>" + legal + "</div></a>";
      }
      if (c.kind === "epic") {
        const src = epicSrc || "";
        if (!src) return "<a class=\"cam linkcard\" href=\"" + href + "\" target=\"_blank\" rel=\"noopener\"><div class=\"cap\"><span class=\"tag shadow\">SHADOW</span><b>" + escapeHtml(c.title) + "</b>NASA EPIC named — open official page.</div></a>";
        return "<a class=\"cam\" href=\"" + href + "\" target=\"_blank\" rel=\"noopener\"><img src=\"" + src + "\" alt=\"" + escapeHtml(c.title) + "\" loading=\"lazy\"><div class=\"cap\"><b>" + escapeHtml(c.title) + "</b>" + legal + "</div></a>";
      }
      if (c.kind === "youtube") {
        return "<div class=\"cam\"><iframe src=\"" + c.embed + "\" title=\"" + escapeHtml(c.title) + "\" allow=\"encrypted-media; picture-in-picture\" allowfullscreen loading=\"lazy\"></iframe><div class=\"cap\"><b><a href=\"" + href + "\" target=\"_blank\" rel=\"noopener\">" + escapeHtml(c.title) + "</a></b>" + legal + "</div></div>";
      }
      return "<a class=\"cam linkcard\" href=\"" + href + "\" target=\"_blank\" rel=\"noopener\"><div class=\"cap\"><span class=\"tag ref\">RESOURCE</span><b>" + escapeHtml(c.title) + "</b>" + legal + "<br>" + escapeHtml(c.note || "Official public cameras — open the agency page.") + "</div></a>";
    }).join("");
  }

  function renderNews(pack) {
    function fill(id, rows, st) {
      const ul = document.getElementById(id);
      const tag = document.getElementById(st);
      if (!ul) return;
      ul.innerHTML = (rows || []).slice(0, 18).map(function (r) {
        return "<li><a href=\"" + escapeHtml(r.url) + "\" target=\"_blank\" rel=\"noopener\">" + escapeHtml(r.title) + "</a><div class=\"src\">" + escapeHtml(r.source) + (r.date ? " · " + escapeHtml(r.date).slice(0, 22) : "") + "</div></li>";
      }).join("") || "<li>No public items in this lane.</li>";
      if (tag) { tag.textContent = String((rows || []).length); tag.className = "tag ok"; }
    }
    fill("news-severe", pack.severe, "st-news-sev");
    fill("news-world", pack.world, "st-news-world");
  }

  async function loadNews() {
    try {
      const pack = await getJson("news-monitor.json");
      const extra = [];
      (state.ref.quakes || []).filter(function (q) { return (q.mag || 0) >= 5.5; }).forEach(function (q) {
        extra.push({ title: "M" + q.mag + " " + (q.title || q.place || "quake"), url: "https://earthquake.usgs.gov/", source: "usgs_live", lane: "severe", date: "", class: "RESOURCE" });
      });
      (state.ref.world_alerts || []).slice(0, 8).forEach(function (a) {
        extra.push({ title: a.title, url: "https://api.weather.gov/alerts/active?status=actual", source: "wxalert_live", lane: "severe", date: "", class: "RESOURCE" });
      });
      pack.severe = extra.concat(pack.severe || []);
      renderNews(pack);
    } catch (e) {
      const tag = document.getElementById("st-news-sev");
      if (tag) { tag.textContent = "named"; tag.className = "tag shadow"; }
    }
  }

  async function boot() {
    document.getElementById("sig").textContent = SIG;
    await loadShadows();
    await Promise.all([loadCanon(), loadRef(), loadHfFeed(), loadCameras()]);
    renderFeeds();
    await loadNews();
  }

  window.addEventListener("resize", resize);
  resize();
  bind();
  boot();
  frame();
  setInterval(refreshIss, 12000);
  setInterval(loadCameras, 300000);
})();
