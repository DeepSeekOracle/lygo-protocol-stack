/* LYGO Public Witness v1.0.0 — public = REFERENCE, lattice = CANON. Never invent missing sources. */
(function () {
  "use strict";
  const SIG = "Delta9Phi963-PUBLIC-WITNESS-v1.0.0";
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
    mode: "earth", // earth | lattice | split
    rot: 0.4,
    tilt: 0.18,
    dragging: false,
    lastX: 0,
    lastY: 0,
    layers: { quakes: true, events: true, iss: true, canon: true },
    ref: { quakes: [], events: [], iss: null, errors: {} },
    canon: { anchors: [], star: [], eggs: [], agora: null, errors: {} },
    selected: null
  };

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

  /* Schematic land masses — orientation only, not a basemap product. */
  const LAND = [
    [40, -100, 28, 18], [55, 10, 22, 12], [20, 20, 18, 20], [0, 25, 16, 18],
    [-20, 25, 14, 16], [35, 90, 30, 16], [-25, 135, 18, 14], [-15, -60, 16, 22],
    [60, -40, 8, 6], [-80, 0, 20, 8]
  ];

  function hashAngle(s) {
    let h = 2166136261;
    for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
    return (h >>> 0) / 4294967295;
  }

  function schematicLL(id) {
    const a = hashAngle(id);
    const b = hashAngle(id + ":b");
    return { lat: (a * 140) - 70, lon: (b * 360) - 180 };
  }

  function drawGlobe(cx, cy, R, rot, kind) {
    const g = ctx.createRadialGradient(cx - R * 0.3, cy - R * 0.3, R * 0.2, cx, cy, R * 1.05);
    if (kind === "earth") {
      g.addColorStop(0, "#16324f");
      g.addColorStop(0.7, "#0b1a2e");
      g.addColorStop(1, "#05080f");
    } else {
      g.addColorStop(0, "#2a2208");
      g.addColorStop(0.7, "#161008");
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

    ctx.globalAlpha = 0.22;
    ctx.strokeStyle = kind === "earth" ? "#7dd3fc" : "#fbbf24";
    ctx.lineWidth = 0.6;
    for (let lat = -60; lat <= 60; lat += 30) {
      ctx.beginPath();
      for (let lon = -180; lon <= 180; lon += 6) {
        const p = project(lat, lon, cx, cy, R, rot);
        if (lon === -180) ctx.moveTo(p.x, p.y); else ctx.lineTo(p.x, p.y);
      }
      ctx.stroke();
    }
    for (let lon = -180; lon < 180; lon += 30) {
      ctx.beginPath();
      for (let lat = -80; lat <= 80; lat += 6) {
        const p = project(lat, lon, cx, cy, R, rot);
        if (lat === -80) ctx.moveTo(p.x, p.y); else ctx.lineTo(p.x, p.y);
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
          const mag = Math.max(2, q.mag || 2);
          ctx.fillStyle = "rgba(245,158,11,0.85)";
          ctx.beginPath();
          ctx.arc(p.x, p.y, 1.6 + mag * 0.7, 0, Math.PI * 2);
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
          ctx.strokeStyle = "#7dd3fc88";
          ctx.beginPath();
          ctx.arc(p.x, p.y, 9, 0, Math.PI * 2);
          ctx.stroke();
        }
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
          ctx.arc(p.x, p.y, n.kind === "star" ? 3.4 : 2.4, 0, Math.PI * 2);
          ctx.fill();
        });
        ctx.globalAlpha = 0.18;
        ctx.strokeStyle = "#fbbf24";
        ctx.beginPath();
        nodes.slice(0, 18).forEach(function (n, i) {
          const ll = schematicLL(n.id || n.node_id || String(i));
          const p = project(ll.lat, ll.lon, cx, cy, R, rot);
          if (i === 0) ctx.moveTo(p.x, p.y); else ctx.lineTo(p.x, p.y);
        });
        ctx.stroke();
        ctx.globalAlpha = 1;
      }
    }
    ctx.restore();

    ctx.fillStyle = "#e8eef7";
    ctx.font = "11px IBM Plex Mono, monospace";
    ctx.fillText(kind === "earth" ? "EARTH · REFERENCE" : "LATTICE · CANON (schematic)", cx - 78, cy + R + 18);
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

  function setStatus(id, ok, detail) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = ok ? "live" : (detail || "unreachable");
    el.className = "tag " + (ok ? "ok" : "miss");
  }

  function renderFeeds() {
    const ul = document.getElementById("feed");
    const items = [];
    state.ref.quakes.slice(0, 12).forEach(function (q) {
      items.push({ cls: "ref", title: "M" + q.mag.toFixed(1) + " " + q.place, sub: "USGS REFERENCE", body: q });
    });
    state.ref.events.slice(0, 8).forEach(function (e) {
      items.push({ cls: "ref", title: e.title, sub: "EONET REFERENCE", body: e });
    });
    if (state.ref.iss) {
      items.unshift({
        cls: "ref",
        title: "ISS " + state.ref.iss.lat.toFixed(2) + ", " + state.ref.iss.lon.toFixed(2),
        sub: "PUBLIC TLE/ADS overlay · REFERENCE",
        body: state.ref.iss
      });
    }
    state.canon.star.slice(0, 8).forEach(function (n) {
      items.push({ cls: "canon", title: n.node_name || n.node_id, sub: "STAR CHART CANON · " + (n.status || ""), body: n });
    });
    state.canon.eggs.slice(0, 6).forEach(function (n) {
      items.push({ cls: "canon", title: n.id, sub: "EGG / LATTICE CANON", body: n });
    });
    ul.innerHTML = items.slice(0, 28).map(function (it, i) {
      return "<li data-i=\"" + i + "\"><span class=\"tag " + it.cls + "\">" + it.cls.toUpperCase() + "</span>" +
        escapeHtml(it.title) + "<div class=\"legend\">" + escapeHtml(it.sub) + "</div></li>";
    }).join("") || "<li>No public sources reached. Empty is honest.</li>";
    ul.querySelectorAll("li").forEach(function (li, i) {
      li.addEventListener("click", function () {
        state.selected = items[i];
        document.getElementById("detail").textContent = JSON.stringify({
          class: items[i].cls,
          note: items[i].cls === "ref" ? "REFERENCE — not lattice canon" : "CANON — on-lattice receipt",
          payload: items[i].body
        }, null, 2);
      });
    });
    document.getElementById("n-ref").textContent = String(state.ref.quakes.length + state.ref.events.length + (state.ref.iss ? 1 : 0));
    document.getElementById("n-canon").textContent = String(state.canon.anchors.length + state.canon.star.length + state.canon.eggs.length);
  }

  function escapeHtml(s) {
    return String(s || "").replace(/[&<>"]/g, function (c) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;" })[c];
    });
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
      setStatus("st-anchors", false, "unreachable");
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
      document.getElementById("n-entries").textContent = String(f.entry_count || state.canon.star.length);
      setStatus("st-star", !!f.chain_valid);
    } catch (e) {
      state.canon.errors.star = String(e);
      setStatus("st-star", false);
    }
    try {
      const g = await getJson(CANON_URLS.lattice);
      const hubs = (g.hubs || g.surfaces || g.groups || []);
      if (Array.isArray(hubs)) {
        hubs.forEach(function (h) {
          state.canon.eggs.push({ id: h.id || h.name, kind: "egg", label: h.label || h.name });
        });
      } else if (hubs && typeof hubs === "object") {
        Object.keys(hubs).forEach(function (k) {
          state.canon.eggs.push({ id: k, kind: "egg", label: k });
        });
      }
      if (g.kernel_eggs) state.canon.eggs.push({ id: "kernel_eggs", kind: "egg" });
      setStatus("st-eggs", true);
    } catch (e) {
      state.canon.errors.eggs = String(e);
      setStatus("st-eggs", false);
    }
    try {
      state.canon.agora = await getJson(CANON_URLS.agora);
      setStatus("st-agora", true);
    } catch (e) {
      state.canon.errors.agora = String(e);
      setStatus("st-agora", false);
    }
  }

  async function loadRef() {
    try {
      const g = await getJson(REF_URLS.usgs);
      state.ref.quakes = (g.features || []).map(function (f) {
        const c = (f.geometry && f.geometry.coordinates) || [0, 0];
        return {
          lon: c[0], lat: c[1], mag: (f.properties && f.properties.mag) || 0,
          place: (f.properties && f.properties.place) || "quake",
          time: f.properties && f.properties.time
        };
      });
      setStatus("st-usgs", true);
    } catch (e) {
      state.ref.errors.usgs = String(e);
      setStatus("st-usgs", false);
    }
    try {
      const ev = await getJson(REF_URLS.eonet);
      state.ref.events = [];
      (ev.events || []).forEach(function (e) {
        const geo = e.geometry && e.geometry[e.geometry.length - 1];
        if (!geo || !geo.coordinates) return;
        state.ref.events.push({
          title: e.title, category: (e.categories && e.categories[0] && e.categories[0].title) || "event",
          lon: geo.coordinates[0], lat: geo.coordinates[1], id: e.id
        });
      });
      setStatus("st-eonet", true);
    } catch (e) {
      state.ref.errors.eonet = String(e);
      setStatus("st-eonet", false);
    }
    try {
      const iss = await getJson(REF_URLS.iss);
      state.ref.iss = { lat: Number(iss.latitude), lon: Number(iss.longitude), alt: iss.altitude, name: "ISS" };
      setStatus("st-iss", true);
    } catch (e) {
      state.ref.errors.iss = String(e);
      setStatus("st-iss", false);
    }
  }

  async function refreshIss() {
    try {
      const iss = await getJson(REF_URLS.iss);
      state.ref.iss = { lat: Number(iss.latitude), lon: Number(iss.longitude), alt: iss.altitude, name: "ISS" };
      setStatus("st-iss", true);
    } catch (e) {
      setStatus("st-iss", false);
    }
  }

  async function ollamaSummary() {
    const out = document.getElementById("ollama-out");
    out.textContent = "Asking local Ollama at 127.0.0.1:11434 …";
    const payload = {
      class_note: "Summarize only. Treat public rows as REFERENCE. Treat ledger rows as CANON. Do not invent sources.",
      ref_count: state.ref.quakes.length + state.ref.events.length,
      iss: state.ref.iss,
      star_sample: state.canon.star.slice(0, 5),
      missing: Object.keys(state.ref.errors).concat(Object.keys(state.canon.errors))
    };
    try {
      const res = await fetch("http://127.0.0.1:11434/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "llama3.2:1b",
          stream: false,
          prompt: "LYGO Public Witness overlay. Public=REFERENCE, lattice=CANON. JSON:\n" + JSON.stringify(payload) + "\nWrite 6 short bullets. Never claim classified data."
        })
      });
      if (!res.ok) throw new Error("HTTP " + res.status);
      const j = await res.json();
      out.textContent = j.response || JSON.stringify(j);
    } catch (e) {
      out.textContent = "Local Ollama not reachable. Optional. Public Witness still works. (" + e + ")";
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
        doctrine: "public=REFERENCE lattice=CANON schematic≠geo",
        reference: { quakes: state.ref.quakes.length, events: state.ref.events.length, iss: state.ref.iss, errors: state.ref.errors },
        canon: {
          anchors: state.canon.anchors.length, star: state.canon.star.length, eggs: state.canon.eggs.length,
          agora: state.canon.agora && (state.canon.agora.signature || true), errors: state.canon.errors
        },
        live_star_chart_write: false
      }, null, 2);
    });
  }

  async function boot() {
    document.getElementById("sig").textContent = SIG;
    await Promise.all([loadCanon(), loadRef()]);
    renderFeeds();
  }

  window.addEventListener("resize", resize);
  resize();
  bind();
  boot();
  frame();
  setInterval(refreshIss, 12000);
})();
