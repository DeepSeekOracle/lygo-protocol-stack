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
  const discCanvas = document.getElementById("disc");
  const dctx = discCanvas ? discCanvas.getContext("2d") : null;
  const state = {
    mode: "earth",
    filter: "all",
    rot: 0.4,
    tilt: 0.18,
    dragging: false,
    lastX: 0,
    lastY: 0,
    zoom: 1,
    panX: 0,
    panY: 0,
    hover: null,
    cursor: null,
    pick: null,
    followIss: false,
    issTrail: [],
    dragMoved: 0,
    q: "",
    disc: { zoom: 1, panX: 0, panY: 0, rot: 0, dragging: false, lastX: 0, lastY: 0, hover: null, dragMoved: 0 },
    world: [],
    landMask: null,
    rain: [],
    stars: [],
    tick: 0,
    layers: { quakes: true, events: true, iss: true, alerts: true, floods: true, launches: true, aurora: true, flights: true, weather: true, radar: true, air: true, marine: true, canon: true, shadow: true, matrix: true },
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
  const PLACES = [
    { n: "Canada", lat: 56.1, lon: -106.3 }, { n: "USA", lat: 39.8, lon: -98.6 },
    { n: "Mexico", lat: 23.6, lon: -102.5 }, { n: "Greenland", lat: 71.7, lon: -42.6 },
    { n: "Brazil", lat: -14.2, lon: -51.9 }, { n: "Argentina", lat: -38.4, lon: -63.6 },
    { n: "Chile", lat: -35.7, lon: -71.5 }, { n: "Peru", lat: -9.2, lon: -75.0 },
    { n: "Colombia", lat: 4.6, lon: -74.3 }, { n: "UK", lat: 54.5, lon: -2.0 },
    { n: "France", lat: 46.2, lon: 2.2 }, { n: "Germany", lat: 51.2, lon: 10.4 },
    { n: "Spain", lat: 40.5, lon: -3.7 }, { n: "Italy", lat: 41.9, lon: 12.6 },
    { n: "Norway", lat: 60.5, lon: 8.5 }, { n: "Sweden", lat: 60.1, lon: 18.6 },
    { n: "Iceland", lat: 64.9, lon: -19.0 }, { n: "Poland", lat: 51.9, lon: 19.1 },
    { n: "Ukraine", lat: 48.4, lon: 31.2 }, { n: "Russia", lat: 61.5, lon: 105.3 },
    { n: "Turkey", lat: 38.96, lon: 35.2 }, { n: "Egypt", lat: 26.8, lon: 30.8 },
    { n: "Nigeria", lat: 9.1, lon: 8.7 }, { n: "Kenya", lat: 0.02, lon: 37.9 },
    { n: "South Africa", lat: -30.6, lon: 22.9 }, { n: "DRC", lat: -4.0, lon: 21.8 },
    { n: "Morocco", lat: 31.8, lon: -7.1 }, { n: "Ethiopia", lat: 9.1, lon: 40.5 },
    { n: "India", lat: 20.6, lon: 79.0 }, { n: "China", lat: 35.9, lon: 104.2 },
    { n: "Japan", lat: 36.2, lon: 138.3 }, { n: "Korea", lat: 35.9, lon: 127.8 },
    { n: "Indonesia", lat: -2.5, lon: 118.0 }, { n: "Australia", lat: -25.3, lon: 133.8 },
    { n: "New Zealand", lat: -40.9, lon: 174.9 }, { n: "Philippines", lat: 12.9, lon: 121.8 },
    { n: "Thailand", lat: 15.9, lon: 100.99 }, { n: "Vietnam", lat: 14.1, lon: 108.3 },
    { n: "Pakistan", lat: 30.4, lon: 69.3 }, { n: "Iran", lat: 32.4, lon: 53.7 },
    { n: "Saudi Arabia", lat: 23.9, lon: 45.1 }, { n: "Iraq", lat: 33.2, lon: 43.7 },
    { n: "Kazakhstan", lat: 48.0, lon: 66.9 }, { n: "Mongolia", lat: 46.9, lon: 103.8 },
    { n: "Alaska", lat: 64.2, lon: -153.4 }, { n: "Antarctica", lat: -82.0, lon: 0 }
  ];

  function sizeCanvas(cv, c) {
    if (!cv || !c) return;
    const r = cv.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    cv.width = Math.max(320, r.width) * dpr;
    cv.height = Math.max(280, r.height) * dpr;
    c.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function resize() {
    sizeCanvas(canvas, ctx);
  }

  function project(lat, lon, cx, cy, R, rot) {
    const phi = (lat * Math.PI) / 180;
    const lam = (lon * Math.PI) / 180 + rot;
    const x = Math.cos(phi) * Math.sin(lam);
    const y = Math.sin(phi) * Math.cos(state.tilt) + Math.cos(phi) * Math.cos(lam) * Math.sin(state.tilt);
    const z = Math.cos(phi) * Math.cos(lam) * Math.cos(state.tilt) - Math.sin(phi) * Math.sin(state.tilt);
    return { x: cx + x * R, y: cy - y * R, z: z, nx: x, ny: y, nz: z, vis: z > 0.06 };
  }

  function projectDisc(lat, lon, cx, cy, R, rot) {
    const colat = ((90 - lat) * Math.PI) / 180;
    const rho = (R * colat) / Math.PI;
    const th = (lon * Math.PI) / 180 + rot;
    return {
      x: cx + rho * Math.sin(th),
      y: cy - rho * Math.cos(th),
      z: 1 - Math.min(1, rho / R),
      vis: rho <= R + 0.8
    };
  }

  function unprojectDisc(sx, sy, cx, cy, R, rot) {
    const dx = sx - cx;
    const dy = cy - sy;
    const rho = Math.sqrt(dx * dx + dy * dy);
    if (rho > R + 0.5) return null;
    const lat = 90 - (rho / R) * 180;
    let lon = ((Math.atan2(dx, dy) - rot) * 180) / Math.PI;
    while (lon > 180) lon -= 360;
    while (lon < -180) lon += 360;
    return { lat: lat, lon: lon };
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

  const GLYPHS = "01Δ9Φ963LYGOﾊﾐﾋｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍ";

  function seedDecor() {
    if (state.stars.length) return;
    for (let i = 0; i < 140; i++) {
      state.stars.push({ x: Math.random(), y: Math.random(), s: 0.4 + Math.random() * 1.4, a: 0.25 + Math.random() * 0.7 });
    }
    for (let i = 0; i < 42; i++) {
      state.rain.push({
        x: Math.random(),
        y: Math.random() * -1.2,
        sp: 0.0016 + Math.random() * 0.004,
        len: 8 + ((Math.random() * 14) | 0)
      });
    }
  }

  function isLand(lat, lon) {
    if (!state.landMask) return false;
    let x = Math.round(lon + 180);
    const y = Math.round(90 - lat);
    if (y < 0 || y >= 180) return false;
    x = ((x % 360) + 360) % 360;
    return state.landMask[y * 360 + x] === 1;
  }

  function buildLandMask(rings) {
    const c = document.createElement("canvas");
    c.width = 360;
    c.height = 180;
    const g = c.getContext("2d");
    g.fillStyle = "#000";
    g.fillRect(0, 0, 360, 180);
    g.fillStyle = "#fff";
    rings.forEach(function (ring) {
      if (ring.length < 4) return;
      g.beginPath();
      for (let i = 0; i < ring.length; i++) {
        const x = ring[i][0] + 180;
        const y = 90 - ring[i][1];
        if (i === 0) g.moveTo(x, y);
        else g.lineTo(x, y);
      }
      g.closePath();
      g.fill();
    });
    const data = g.getImageData(0, 0, 360, 180).data;
    const mask = new Uint8Array(360 * 180);
    for (let i = 0; i < mask.length; i++) mask[i] = data[i * 4] > 20 ? 1 : 0;
    state.landMask = mask;
  }

  async function loadWorld() {
    try {
      const pack = await getJson("world-land.json");
      const q = pack.q || 10;
      state.world = (pack.rings || []).map(function (ring) {
        return ring.map(function (p) { return [p[0] / q, p[1] / q]; });
      });
      buildLandMask(state.world);
    } catch (e) {
      state.world = [];
    }
  }

  function unproject(sx, sy, cx, cy, R, rot) {
    const nx = (sx - cx) / R;
    const ny = (cy - sy) / R;
    const rr = nx * nx + ny * ny;
    if (rr > 0.995) return null;
    const nz = Math.sqrt(Math.max(0, 1 - rr));
    const sinT = Math.sin(state.tilt);
    const cosT = Math.cos(state.tilt);
    const sinPhi = ny * cosT - nz * sinT;
    const cphiClam = ny * sinT + nz * cosT;
    const phi = Math.asin(Math.max(-1, Math.min(1, sinPhi)));
    const cosPhi = Math.cos(phi);
    let lam;
    if (Math.abs(cosPhi) < 1e-6) lam = 0;
    else lam = Math.atan2(nx / cosPhi, cphiClam / cosPhi) - rot;
    while (lam > Math.PI) lam -= Math.PI * 2;
    while (lam < -Math.PI) lam += Math.PI * 2;
    return { lat: (phi * 180) / Math.PI, lon: (lam * 180) / Math.PI };
  }

  function fmtLL(ll) {
    if (!ll) return "";
    const ns = ll.lat >= 0 ? "N" : "S";
    const ew = ll.lon >= 0 ? "E" : "W";
    return Math.abs(ll.lat).toFixed(1) + "°" + ns + " " + Math.abs(ll.lon).toFixed(1) + "°" + ew;
  }

  function haversine(a, b, c, d) {
    const p = Math.PI / 180;
    const dlat = (c - a) * p;
    const dlon = (d - b) * p;
    const s = Math.sin(dlat / 2) ** 2 + Math.cos(a * p) * Math.cos(c * p) * Math.sin(dlon / 2) ** 2;
    return 12742 * Math.asin(Math.min(1, Math.sqrt(s)));
  }

  function listPins() {
    const out = [];
    function add(lat, lon, title, cls, body, layer) {
      if (typeof lat !== "number" || typeof lon !== "number" || isNaN(lat) || isNaN(lon)) return;
      out.push({ lat: lat, lon: lon, title: title, cls: cls, body: body, layer: layer || (body && body.layer) });
    }
    if (state.layers.quakes) {
      (state.ref.quakes || []).forEach(function (q) {
        add(q.lat, q.lon, "M" + (q.mag || 0).toFixed(1) + " " + (q.place || "quake"), "ref", q, "quakes");
      });
    }
    if (state.layers.events) {
      (state.ref.events || []).forEach(function (e) {
        add(e.lat, e.lon, e.title || "EONET", "ref", e, "events");
      });
    }
    if (state.layers.iss && state.ref.iss) add(state.ref.iss.lat, state.ref.iss.lon, "ISS", "ref", state.ref.iss, "iss");
    [
      ["alerts", state.ref.alerts], ["floods", state.ref.floods], ["launches", state.ref.launches],
      ["aurora", state.ref.aurora], ["flights", state.ref.flights], ["weather", state.ref.weather],
      ["radar", state.ref.radar], ["air", state.ref.air], ["marine", state.ref.marine]
    ].forEach(function (pair) {
      if (!state.layers[pair[0]]) return;
      (pair[1] || []).forEach(function (e) {
        add(e.lat, e.lon, e.title || pair[0], "ref", e, pair[0]);
      });
    });
    if (state.layers.alerts) {
      (state.ref.world_alerts || []).forEach(function (e) {
        add(e.lat, e.lon, e.title || "alert", "ref", e, "alerts");
      });
    }
    if (state.layers.shadow) {
      (state.shadows || []).forEach(function (n) {
        const ll = nodeLL(n);
        add(ll.lat, ll.lon, n.label || n.id, resourceLive(n.id) ? "ref" : "shadow", n, n.kind === "resource" ? "resource" : "shadow");
      });
    }
    return out;
  }

  function nearestPin(lat, lon) {
    const pins = listPins();
    let best = null;
    let bestD = 1e9;
    pins.forEach(function (p) {
      const d = haversine(lat, lon, p.lat, p.lon);
      if (d < bestD) { bestD = d; best = p; }
    });
    const maxKm = Math.max(220, 1600 / Math.max(1, state.zoom));
    if (!best || bestD > maxKm) {
      return {
        lat: lat, lon: lon, title: fmtLL({ lat: lat, lon: lon }), cls: "ref", miss: true, km: bestD,
        body: { class: "LOOK", note: "No public pin in range. Coordinates only.", lat: lat, lon: lon, land: isLand(lat, lon), payload: null }
      };
    }
    best.km = bestD;
    return best;
  }

  function lookAt(ll) {
    if (!ll) return;
    state.rot = -(ll.lon * Math.PI) / 180;
    state.tilt = Math.max(-1.05, Math.min(1.05, (ll.lat * Math.PI) / 180 * 0.9));
  }

  function flyTo(ll, title, cls, body, follow) {
    if (!ll || typeof ll.lat !== "number") return;
    lookAt(ll);
    const rect = canvas.getBoundingClientRect();
    setZoom(Math.max(state.zoom, 2.45), rect.width / 2, rect.height * 0.48, rect.width, rect.height);
    showPick({
      lat: ll.lat, lon: ll.lon, title: title || fmtLL(ll), cls: cls || "ref",
      body: body || ll, km: 0, layer: (body && body.layer) || (follow ? "iss" : "")
    });
    if (follow) {
      state.followIss = true;
      const btn = document.getElementById("btn-follow-iss");
      if (btn) btn.classList.add("on");
    }
  }

  function pinLayer(pin) {
    const b = (pin && pin.body) || {};
    if (pin.layer) return pin.layer;
    if (b.layer) return b.layer;
    if (b.name === "ISS" || pin.title === "ISS") return "iss";
    if (typeof b.mag === "number") return "quakes";
    if (b.public_checks) return pin.cls === "shadow" ? "shadow" : "resource";
    return "";
  }

  function describePin(pin) {
    const b = pin.body || {};
    const layer = pinLayer(pin);
    const catalog = {
      quakes: { agency: "USGS", what: "Public earthquake from the USGS catalog. Not a prediction. Open the USGS page for magnitude, time, and the official map." },
      events: { agency: "NASA EONET", what: "Public natural event (fire, volcano, storm, ice). NASA indexes it. Open EONET for the source record." },
      iss: { agency: "Where The ISS At / NASA", what: "Live public ISS telemetry. The station is a resource ping, not classified tracking. Open the tracker for the current pass." },
      alerts: { agency: "NWS / public CAP", what: "Public weather or hazard alert. Open the agency page. We do not invent the interior of a private forecast desk." },
      floods: { agency: "UK flood monitoring", what: "Public flood-monitor point. Open the official flood page." },
      launches: { agency: "Launch Library", what: "Upcoming public launch pad. Open the listing for vehicle, pad, and time." },
      aurora: { agency: "NOAA SWPC", what: "Public space-weather / aurora index. Open NOAA for the forecast product." },
      flights: { agency: "OpenSky / ADS-B", what: "Public aircraft sample from an ADS-B box. Not a classified radar picture." },
      weather: { agency: "Open-Meteo", what: "Public weather hub (temperature / wind). Open-Meteo is CC BY 4.0." },
      radar: { agency: "RainViewer", what: "Public radar mosaic (educational). Open RainViewer. Not NEXRAD internals." },
      air: { agency: "Open-Meteo AQ", what: "Public air-quality sample. Open the Open-Meteo air page." },
      marine: { agency: "Open-Meteo marine", what: "Public marine weather sample. Open Open-Meteo marine." },
      resource: { agency: "Public feed", what: (b.why || "Named public resource. If the GET failed, the node still exists — use the official check link.") },
      shadow: { agency: "Named shadow", what: (b.why || "This room is private. We keep the silhouette and the legal public links. Payload stays empty.") }
    };
    const row = catalog[layer] || {
      agency: pin.miss ? "Look-at" : "Public overlay",
      what: pin.miss
        ? "No public pin in range. Coordinates only — we do not invent a source here."
        : "A public overlay point. Use the official link when present."
    };
    const links = [];
    function pushLink(label, url) {
      if (!url) return;
      for (let i = 0; i < links.length; i++) if (links[i].url === url) return;
      links.push({ label: label, url: url });
    }
    if (b.url) pushLink("Open official source", b.url);
    (b.public_checks || []).forEach(function (c) { pushLink(c.label || "Public check", c.url); });
    if (layer === "quakes") {
      if (b.id) pushLink("USGS event page", "https://earthquake.usgs.gov/earthquakes/eventpage/" + encodeURIComponent(b.id));
      pushLink("USGS earthquake map", "https://earthquake.usgs.gov/earthquakes/map/");
    }
    if (layer === "events") {
      pushLink("NASA EONET", b.id ? "https://eonet.gsfc.nasa.gov/api/v3/events/" + encodeURIComponent(b.id) : "https://eonet.gsfc.nasa.gov/");
    }
    if (layer === "iss") {
      pushLink("Where The ISS At", "https://wheretheiss.at/");
      pushLink("NASA Spot The Station", "https://spotthestation.nasa.gov/");
    }
    if (layer === "weather" || layer === "air" || layer === "marine") {
      pushLink("Open-Meteo at this point", "https://open-meteo.com/en/docs#latitude=" + pin.lat + "&longitude=" + pin.lon);
    }
    if (layer === "radar") pushLink("RainViewer", "https://www.rainviewer.com/");
    if (layer === "alerts") pushLink("NWS alerts", "https://api.weather.gov/alerts/active?status=actual");
    if (layer === "launches") pushLink("Launch Library", "https://ll.thespacedevs.com/");
    pushLink("OSM map", "https://www.openstreetmap.org/?mlat=" + pin.lat + "&mlon=" + pin.lon + "#map=6/" + pin.lat + "/" + pin.lon);
    return {
      tag: pin.miss ? "LOOK" : (pin.cls === "shadow" ? "SHADOW" : (pin.cls === "canon" ? "CANON" : "RESOURCE")),
      cls: pin.miss ? "ref" : pin.cls,
      agency: row.agency,
      what: row.what,
      links: links
    };
  }

  function briefHtml(pin) {
    const d = describePin(pin);
    const km = pin.km != null && !pin.miss ? Math.round(pin.km) + " km from click" : "";
    const extra = [];
    const b = pin.body || {};
    if (typeof b.mag === "number") extra.push("M" + b.mag.toFixed(1));
    if (b.place) extra.push(b.place);
    if (b.alt != null) extra.push("alt " + (typeof b.alt === "number" ? b.alt.toFixed(0) + " km" : b.alt));
    const linkHtml = d.links.map(function (l) {
      const href = safeHref(l.url);
      return href ? "<a class=\"btn ghost\" href=\"" + escapeHtml(href) + "\" target=\"_blank\" rel=\"noopener noreferrer\">" + escapeHtml(l.label) + "</a>" : "";
    }).join(" ");
    return "<p class=\"kicker\">Selected node · " + escapeHtml(d.agency) + "</p>" +
      "<h2>" + "<span class=\"tag " + d.cls + "\">" + d.tag + "</span> " + escapeHtml(pin.title) + "</h2>" +
      "<p>" + escapeHtml(d.what) + "</p>" +
      "<p class=\"legend\">" + fmtLL(pin) + (isLand(pin.lat, pin.lon) ? " · land" : " · ocean") +
      (km ? " · " + km : "") + (extra.length ? " · " + escapeHtml(extra.join(" · ")) : "") + "</p>" +
      (d.tag === "SHADOW" ? "<p class=\"legend\">Payload is null on purpose. Follow public checks only.</p>" : "") +
      "<div class=\"brief-links\">" + linkHtml + "</div>";
  }

  function showPick(pin) {
    if (!pin) return;
    state.pick = pin;
    state.cursor = { lat: pin.lat, lon: pin.lon };
    const d = describePin(pin);
    const html = briefHtml(pin);
    const brief = document.getElementById("brief");
    const mapBrief = document.getElementById("map-brief");
    if (brief) {
      brief.innerHTML = html;
      brief.classList.remove("empty");
      try { brief.scrollIntoView({ block: "nearest", behavior: "smooth" }); } catch (e) {}
    }
    if (mapBrief) {
      mapBrief.innerHTML = html + "<button type=\"button\" class=\"btn ghost\" id=\"brief-close\">Hide overlay</button>";
      mapBrief.hidden = false;
      const close = document.getElementById("brief-close");
      if (close) close.onclick = function () { mapBrief.hidden = true; };
    }
    const card = document.getElementById("pick-card");
    if (card) card.innerHTML = html;
    const detail = document.getElementById("detail");
    if (detail) {
      detail.textContent = JSON.stringify({
        class: d.tag, agency: d.agency, what: d.what, km: pin.km != null ? Math.round(pin.km) : null,
        links: d.links, body: pin.body, payload: pin.cls === "shadow" ? null : undefined
      }, null, 2);
    }
    try {
      history.replaceState(null, "", "#ll=" + pin.lat.toFixed(3) + "," + pin.lon.toFixed(3));
    } catch (e) {}
    updateMeta();
    updateDiscMeta();
  }

  function tryPick(ll) {
    if (!ll) return;
    showPick(nearestPin(ll.lat, ll.lon));
  }

  function pushIss(iss) {
    if (!iss || typeof iss.lat !== "number") return;
    const last = state.issTrail[state.issTrail.length - 1];
    if (last && Math.abs(last.lat - iss.lat) < 0.02 && Math.abs(last.lon - iss.lon) < 0.02) return;
    state.issTrail.push({ lat: iss.lat, lon: iss.lon, t: Date.now() });
    if (state.issTrail.length > 56) state.issTrail.shift();
  }

  function drawIssTrail(c, projectFn, cx, cy, R, rot) {
    if (!state.layers.iss || state.issTrail.length < 2) return;
    c.beginPath();
    let prev = null;
    let prevPt = null;
    state.issTrail.forEach(function (pt) {
      if (prevPt) {
        let d = pt.lon - prevPt.lon;
        while (d > 180) d -= 360;
        while (d < -180) d += 360;
        if (Math.abs(d) > 50) prev = null;
      }
      const p = projectFn(pt.lat, pt.lon, cx, cy, R, rot);
      if (segOk(prev, p, R)) c.lineTo(p.x, p.y);
      else if (p.vis && p.z >= 0.07) c.moveTo(p.x, p.y);
      prev = p.vis ? p : null;
      prevPt = pt;
    });
    c.strokeStyle = "rgba(125,211,252,0.55)";
    c.lineWidth = 1.6;
    c.stroke();
  }

  function subsolar(date) {
    const d = date || new Date();
    const start = Date.UTC(d.getUTCFullYear(), 0, 0);
    const doy = (d.getTime() - start) / 86400000;
    const decl = 23.44 * Math.sin((2 * Math.PI / 365) * (doy - 81));
    const utc = d.getUTCHours() + d.getUTCMinutes() / 60 + d.getUTCSeconds() / 3600;
    let lon = 15 * (12 - utc);
    while (lon > 180) lon -= 360;
    while (lon < -180) lon += 360;
    return { lat: decl, lon: lon };
  }

  function sunCos(lat, lon, sun) {
    const p = Math.PI / 180;
    return Math.sin(lat * p) * Math.sin(sun.lat * p) + Math.cos(lat * p) * Math.cos(sun.lat * p) * Math.cos((lon - sun.lon) * p);
  }

  function destPoint(lat, lon, bearingDeg, distDeg) {
    const p = Math.PI / 180;
    const ph1 = lat * p;
    const la1 = lon * p;
    const th = bearingDeg * p;
    const d = distDeg * p;
    const ph2 = Math.asin(Math.sin(ph1) * Math.cos(d) + Math.cos(ph1) * Math.sin(d) * Math.cos(th));
    const la2 = la1 + Math.atan2(Math.sin(th) * Math.sin(d) * Math.cos(ph1), Math.cos(d) - Math.sin(ph1) * Math.sin(ph2));
    let lon2 = la2 / p;
    while (lon2 > 180) lon2 -= 360;
    while (lon2 < -180) lon2 += 360;
    return { lat: ph2 / p, lon: lon2 };
  }

  function drawNight(c, projectFn, cx, cy, R, rot) {
    const sun = subsolar();
    const step = state.zoom > 2.2 ? 3 : 5;
    for (let lat = -80; lat <= 80; lat += step) {
      for (let lon = -180; lon < 180; lon += step) {
        const cz = sunCos(lat, lon, sun);
        if (cz > 0.05) continue;
        const p = projectFn(lat, lon, cx, cy, R, rot);
        if (!p.vis || p.z < 0.1) continue;
        c.globalAlpha = cz > -0.14 ? 0.16 : 0.4;
        c.fillStyle = "#020618";
        const s = Math.max(2.4, (step / 88) * R * 1.35);
        c.fillRect(p.x - s / 2, p.y - s / 2, s, s);
      }
    }
    c.globalAlpha = 1;
    c.beginPath();
    strokeLL(c, projectFn, cx, cy, R, rot, function (i) {
      return destPoint(sun.lat, sun.lon, i * 3, 90);
    }, 120);
    c.strokeStyle = "rgba(253,224,71,0.5)";
    c.lineWidth = 1.25;
    c.stroke();
  }

  function drawLabels(c, projectFn, cx, cy, R, rot, zoom) {
    if (zoom < 1.65) return;
    c.font = (zoom > 2.6 ? 11 : 9) + "px IBM Plex Sans, sans-serif";
    c.textAlign = "center";
    c.textBaseline = "bottom";
    const used = [];
    PLACES.forEach(function (pl) {
      const p = projectFn(pl.lat, pl.lon, cx, cy, R, rot);
      if (!p.vis || p.z < 0.38) return;
      let ok = true;
      for (let i = 0; i < used.length; i++) {
        const dx = used[i].x - p.x;
        const dy = used[i].y - p.y;
        if (dx * dx + dy * dy < 1400) { ok = false; break; }
      }
      if (!ok) return;
      used.push(p);
      const w = c.measureText(pl.n).width;
      c.fillStyle = "rgba(8,14,24,0.62)";
      c.fillRect(p.x - w / 2 - 3, p.y - 13, w + 6, 14);
      c.fillStyle = "#e2e8f0";
      c.fillText(pl.n, p.x, p.y - 1);
    });
  }

  function drawMarks(c, projectFn, cx, cy, R, rot) {
    const ll = state.cursor;
    if (ll) {
      const p = projectFn(ll.lat, ll.lon, cx, cy, R, rot);
      if (p.vis) {
        c.strokeStyle = "#ecfccb";
        c.lineWidth = 1.1;
        c.beginPath();
        c.arc(p.x, p.y, 9, 0, Math.PI * 2);
        c.stroke();
      }
    }
    if (state.pick && typeof state.pick.lat === "number") {
      const p = projectFn(state.pick.lat, state.pick.lon, cx, cy, R, rot);
      if (p.vis) {
        c.strokeStyle = "#fbbf24";
        c.lineWidth = 2;
        c.beginPath();
        c.arc(p.x, p.y, 13, 0, Math.PI * 2);
        c.stroke();
      }
    }
  }

  function tickClock() {
    const el = document.getElementById("utc-clock");
    if (el) el.textContent = new Date().toISOString().replace("T", " ").replace(/\.\d+Z$/, "Z");
  }

  function parseHash() {
    const m = String(location.hash || "").match(/ll=(-?\d+\.?\d*),(-?\d+\.?\d*)/);
    if (!m) return;
    const lat = parseFloat(m[1]);
    const lon = parseFloat(m[2]);
    if (isNaN(lat) || isNaN(lon)) return;
    lookAt({ lat: lat, lon: lon });
    tryPick({ lat: lat, lon: lon });
  }

  function segOk(a, b, R) {
    if (!a || !b || !a.vis || !b.vis) return false;
    if (a.z < 0.07 || b.z < 0.07) return false;
    if (a.nz != null && b.nz != null && (a.nz + b.nz) <= 0.05) return false;
    const dx = a.x - b.x;
    const dy = a.y - b.y;
    const lim = R * 0.26;
    return dx * dx + dy * dy < lim * lim;
  }

  function drawLandFill(c, projectFn, cx, cy, R, rot, fill) {
    if (!state.landMask) return;
    const step = state.zoom > 2.5 ? 1.8 : (state.zoom > 1.6 ? 2.4 : 3.4);
    c.fillStyle = fill || "rgba(16, 64, 42, 0.9)";
    for (let lat = -84; lat <= 84; lat += step) {
      const lonStep = Math.max(1.15, step * Math.max(Math.cos((lat * Math.PI) / 180), 0.18));
      for (let lon = -180; lon < 180; lon += lonStep) {
        if (!isLand(lat, lon)) continue;
        const p = projectFn(lat, lon, cx, cy, R, rot);
        if (!p.vis || p.z < 0.08) continue;
        const s = Math.max(2.1, (step / 78) * R * 1.45);
        c.fillRect(p.x - s / 2, p.y - s / 2, s + 0.5, s + 0.5);
      }
    }
  }

  function strokeLand(c, projectFn, cx, cy, R, rot) {
    const rings = state.world;
    if (!rings.length) return;
    c.beginPath();
    rings.forEach(function (ring) {
      let prev = null;
      for (let i = 0; i < ring.length; i++) {
        const p = projectFn(ring[i][1], ring[i][0], cx, cy, R, rot);
        if (segOk(prev, p, R)) c.lineTo(p.x, p.y);
        else if (p.vis && p.z >= 0.07) c.moveTo(p.x, p.y);
        prev = p.vis ? p : null;
      }
    });
  }

  function strokeLL(c, projectFn, cx, cy, R, rot, getLL, n) {
    let prev = null;
    for (let i = 0; i <= n; i++) {
      const ll = getLL(i);
      const p = projectFn(ll.lat, ll.lon, cx, cy, R, rot);
      if (segOk(prev, p, R)) c.lineTo(p.x, p.y);
      else if (p.vis && p.z >= 0.07) c.moveTo(p.x, p.y);
      prev = p.vis ? p : null;
    }
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

  function pathLand(cx, cy, R, rot) {
    drawLandFill(ctx, project, cx, cy, R, rot, "rgba(16, 64, 42, 0.9)");
    ctx.beginPath();
    strokeLand(ctx, project, cx, cy, R, rot);
  }

  function drawGraticule(cx, cy, R, rot, color, step) {
    ctx.strokeStyle = color;
    ctx.lineWidth = 0.55;
    ctx.beginPath();
    for (let lat = -75; lat <= 75; lat += step) {
      strokeLL(ctx, project, cx, cy, R, rot, function (i) {
        return { lat: lat, lon: -180 + i * 4 };
      }, 90);
    }
    for (let lon = -180; lon < 180; lon += step) {
      strokeLL(ctx, project, cx, cy, R, rot, function (i) {
        return { lat: -80 + i * 4, lon: lon };
      }, 40);
    }
    ctx.stroke();
  }

  function drawMatrixSkin(cx, cy, R, rot, kind) {
    if (!state.layers.matrix) return;
    const step = Math.max(3.2, 11 / state.zoom);
    const t = (state.tick / 7) | 0;
    ctx.font = Math.max(7, Math.min(12, R * 0.028)) + "px IBM Plex Mono, monospace";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    let n = 0;
    const cap = 520;
    for (let lat = -70; lat <= 70; lat += step) {
      for (let lon = -180; lon < 180; lon += step * 1.35) {
        if (n > cap) return;
        const land = isLand(lat, lon);
        if (kind === "earth" && !land && (Math.abs((lat * 97 + lon * 13) | 0) % 22) > 1) continue;
        const p = project(lat, lon, cx, cy, R, rot);
        if (!p.vis || p.z < 0.18) continue;
        const gi = Math.abs((lat * 13 + lon * 7 + t) | 0) % GLYPHS.length;
        ctx.globalAlpha = land ? 0.22 + p.z * 0.35 : 0.08 + p.z * 0.12;
        ctx.fillStyle = kind === "earth" ? (land ? "#86efac" : "#22d3ee") : "#fbbf24";
        ctx.fillText(GLYPHS.charAt(gi), p.x, p.y);
        n++;
      }
    }
    ctx.globalAlpha = 1;
  }

  function drawScan(cx, cy, R, rot, kind) {
    const lat = Math.sin(state.tick * 0.012) * 55;
    ctx.beginPath();
    strokeLL(ctx, project, cx, cy, R, rot, function (i) {
      return { lat: lat, lon: -180 + i * 3 };
    }, 120);
    ctx.strokeStyle = kind === "earth" ? "rgba(52,211,153,0.55)" : "rgba(251,191,36,0.5)";
    ctx.lineWidth = 1.4;
    ctx.stroke();
  }

  function drawRain(w, h) {
    if (!state.layers.matrix) return;
    ctx.font = "11px IBM Plex Mono, monospace";
    ctx.textAlign = "left";
    state.rain.forEach(function (col) {
      col.y += col.sp;
      if (col.y > 1.2) {
        col.y = -0.3;
        col.x = Math.random();
      }
      for (let i = 0; i < col.len; i++) {
        const yy = (col.y - i * 0.028) * h;
        if (yy < 0 || yy > h) continue;
        ctx.globalAlpha = Math.max(0.04, 0.42 - i * 0.03);
        ctx.fillStyle = i === 0 ? "#ecfccb" : "#22c55e";
        const gi = Math.abs((col.x * 997 + i * 17 + (state.tick / 4) | 0) | 0) % GLYPHS.length;
        ctx.fillText(GLYPHS.charAt(gi), col.x * w, yy);
      }
    });
    ctx.globalAlpha = 1;
  }

  function drawGlobe(cx, cy, R, rot, kind) {
    const halo = ctx.createRadialGradient(cx, cy, R * 0.92, cx, cy, R * 1.22);
    halo.addColorStop(0, kind === "earth" ? "rgba(45,212,191,0.18)" : "rgba(212,160,23,0.16)");
    halo.addColorStop(1, "rgba(0,0,0,0)");
    ctx.beginPath();
    ctx.arc(cx, cy, R * 1.22, 0, Math.PI * 2);
    ctx.fillStyle = halo;
    ctx.fill();

    const g = ctx.createRadialGradient(cx - R * 0.35, cy - R * 0.38, R * 0.12, cx, cy, R * 1.02);
    if (kind === "earth") {
      g.addColorStop(0, "#1a4a63");
      g.addColorStop(0.45, "#0b2a3c");
      g.addColorStop(0.82, "#07131f");
      g.addColorStop(1, "#02060b");
    } else {
      g.addColorStop(0, "#3a2a0c");
      g.addColorStop(0.55, "#1a1408");
      g.addColorStop(1, "#07050a");
    }
    ctx.beginPath();
    ctx.arc(cx, cy, R, 0, Math.PI * 2);
    ctx.fillStyle = g;
    ctx.fill();

    ctx.save();
    ctx.beginPath();
    ctx.arc(cx, cy, R, 0, Math.PI * 2);
    ctx.clip();

    const gstep = state.zoom > 2 ? 10 : 15;
    ctx.globalAlpha = 0.22;
    drawGraticule(cx, cy, R, rot, kind === "earth" ? "#67e8f9" : "#fbbf24", gstep);
    ctx.globalAlpha = 1;

    if (kind === "earth") {
      pathLand(cx, cy, R, rot);
      ctx.strokeStyle = "rgba(110, 231, 183, 0.85)";
      ctx.lineWidth = state.zoom > 1.8 ? 1.15 : 0.8;
      ctx.stroke();
    } else {
      ctx.beginPath();
      strokeLand(ctx, project, cx, cy, R, rot);
      ctx.strokeStyle = "rgba(251, 191, 36, 0.55)";
      ctx.lineWidth = 0.7;
      ctx.stroke();
    }

    drawNight(ctx, project, cx, cy, R, rot);
    drawMatrixSkin(cx, cy, R, rot, kind);
    drawScan(cx, cy, R, rot, kind);

    const shade = ctx.createLinearGradient(cx - R, cy - R, cx + R, cy + R);
    shade.addColorStop(0, "rgba(255,255,255,0.10)");
    shade.addColorStop(0.45, "rgba(0,0,0,0)");
    shade.addColorStop(1, "rgba(0,0,0,0.38)");
    ctx.fillStyle = shade;
    ctx.beginPath();
    ctx.arc(cx, cy, R, 0, Math.PI * 2);
    ctx.fill();

    if (kind === "earth") {
      if (state.layers.quakes) {
        state.ref.quakes.forEach(function (q) {
          const p = project(q.lat, q.lon, cx, cy, R, rot);
          if (!p.vis) return;
          const rad = (1.4 + Math.max(2, q.mag || 2) * 0.7) * Math.min(1.6, 0.7 + state.zoom * 0.3);
          ctx.fillStyle = "rgba(245,158,11,0.9)";
          ctx.beginPath();
          ctx.arc(p.x, p.y, rad, 0, Math.PI * 2);
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
          ctx.arc(p.x, p.y, 5 * (0.8 + state.zoom * 0.15), 0, Math.PI * 2);
          ctx.stroke();
        });
      }
      if (state.layers.iss && state.ref.iss) {
        drawIssTrail(ctx, project, cx, cy, R, rot);
        const p = project(state.ref.iss.lat, state.ref.iss.lon, cx, cy, R, rot);
        if (p.vis) {
          ctx.shadowColor = "#7dd3fc";
          ctx.shadowBlur = 12;
          ctx.fillStyle = "#e0f2fe";
          ctx.beginPath();
          ctx.arc(p.x, p.y, 4.2, 0, Math.PI * 2);
          ctx.fill();
          ctx.shadowBlur = 0;
          ctx.fillStyle = "#7dd3fc";
          ctx.font = "10px IBM Plex Mono, monospace";
          ctx.textAlign = "left";
          ctx.fillText("ISS", p.x + 7, p.y - 4);
        }
      }
      function dots(list, color, r) {
        (list || []).forEach(function (e) {
          const p = project(e.lat, e.lon, cx, cy, R, rot);
          if (!p.vis) return;
          ctx.fillStyle = color;
          ctx.beginPath();
          ctx.arc(p.x, p.y, r * (0.85 + state.zoom * 0.12), 0, Math.PI * 2);
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

    drawLabels(ctx, project, cx, cy, R, rot, state.zoom);
    drawMarks(ctx, project, cx, cy, R, rot);

    ctx.restore();

    ctx.beginPath();
    ctx.arc(cx, cy, R, 0, Math.PI * 2);
    ctx.strokeStyle = kind === "earth" ? "rgba(125,211,252,0.45)" : "rgba(212,160,23,0.5)";
    ctx.lineWidth = 1.6;
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(cx, cy, R + 6, 0, Math.PI * 2);
    ctx.strokeStyle = kind === "earth" ? "rgba(52,211,153,0.18)" : "rgba(251,191,36,0.16)";
    ctx.lineWidth = 5;
    ctx.stroke();

    ctx.fillStyle = "#86efac";
    ctx.font = "11px IBM Plex Mono, monospace";
    ctx.textAlign = "center";
    ctx.fillText(
      kind === "earth" ? "EARTH · public map · resources + named shadows" : "LATTICE · canon mesh · world ghost",
      cx,
      cy + R + 20
    );
  }

  function pathLandOn(c, projectFn, cx, cy, R, rot) {
    drawLandFill(c, projectFn, cx, cy, R, rot, "rgba(22, 90, 48, 0.88)");
    c.beginPath();
    strokeLand(c, projectFn, cx, cy, R, rot);
  }

  function overlayEarth(c, projectFn, cx, cy, R, rot) {
    if (state.layers.quakes) {
      state.ref.quakes.forEach(function (q) {
        const p = projectFn(q.lat, q.lon, cx, cy, R, rot);
        if (!p.vis) return;
        c.fillStyle = "rgba(245,158,11,0.92)";
        c.beginPath();
        c.arc(p.x, p.y, 1.5 + Math.max(2, q.mag || 2) * 0.55, 0, Math.PI * 2);
        c.fill();
      });
    }
    if (state.layers.events) {
      state.ref.events.forEach(function (e) {
        const p = projectFn(e.lat, e.lon, cx, cy, R, rot);
        if (!p.vis) return;
        c.strokeStyle = "#fb7185";
        c.lineWidth = 1.2;
        c.beginPath();
        c.arc(p.x, p.y, 5, 0, Math.PI * 2);
        c.stroke();
      });
    }
    if (state.layers.iss && state.ref.iss) {
      drawIssTrail(c, projectFn, cx, cy, R, rot);
      const p = projectFn(state.ref.iss.lat, state.ref.iss.lon, cx, cy, R, rot);
      if (p.vis) {
        c.shadowColor = "#7dd3fc";
        c.shadowBlur = 10;
        c.fillStyle = "#e0f2fe";
        c.beginPath();
        c.arc(p.x, p.y, 4.2, 0, Math.PI * 2);
        c.fill();
        c.shadowBlur = 0;
        c.fillStyle = "#7dd3fc";
        c.font = "10px IBM Plex Mono, monospace";
        c.textAlign = "left";
        c.fillText("ISS", p.x + 7, p.y - 4);
      }
    }
    function dots(list, color, r) {
      (list || []).forEach(function (e) {
        const p = projectFn(e.lat, e.lon, cx, cy, R, rot);
        if (!p.vis) return;
        c.fillStyle = color;
        c.beginPath();
        c.arc(p.x, p.y, r, 0, Math.PI * 2);
        c.fill();
      });
    }
    if (state.layers.alerts) dots(state.ref.alerts, "rgba(251,191,36,0.9)", 3.0);
    if (state.layers.floods) dots(state.ref.floods, "rgba(56,189,248,0.9)", 3.0);
    if (state.layers.launches) dots(state.ref.launches, "rgba(244,114,182,0.95)", 4.0);
    if (state.layers.aurora) dots(state.ref.aurora, "rgba(52,211,153,0.55)", 2.0);
    if (state.layers.flights) dots(state.ref.flights, "rgba(125,211,252,0.7)", 1.7);
    if (state.layers.weather) dots(state.ref.weather, "rgba(250,250,250,0.85)", 3.2);
    if (state.layers.radar) dots(state.ref.radar, "rgba(96,165,250,0.85)", 3.8);
    if (state.layers.air) dots(state.ref.air, "rgba(192,132,252,0.9)", 3.4);
    if (state.layers.marine) dots(state.ref.marine, "rgba(45,212,191,0.9)", 3.2);
    if (state.layers.alerts) dots(state.ref.world_alerts, "rgba(251,146,60,0.9)", 3.1);
    if (state.layers.shadow) {
      state.shadows.filter(function (n) { return n.sphere !== "lattice"; }).forEach(function (n) {
        const ll = nodeLL(n);
        const p = projectFn(ll.lat, ll.lon, cx, cy, R, rot);
        if (!p.vis) return;
        const live = n.kind === "resource" && resourceLive(n.id);
        if (live) {
          c.fillStyle = "#34d399";
          c.beginPath();
          c.arc(p.x, p.y, 4, 0, Math.PI * 2);
          c.fill();
        } else {
          c.strokeStyle = "#a78bfa";
          c.lineWidth = 1.4;
          c.setLineDash([3, 3]);
          c.beginPath();
          c.arc(p.x, p.y, n.kind === "resource" ? 7 : 9, 0, Math.PI * 2);
          c.stroke();
          c.setLineDash([]);
        }
      });
    }
    drawMarks(c, projectFn, cx, cy, R, rot);
  }

  function drawDisc(cx, cy, R, rot) {
    if (!dctx) return;
    const c = dctx;
    const halo = c.createRadialGradient(cx, cy, R * 0.15, cx, cy, R * 1.18);
    halo.addColorStop(0, "rgba(52,211,153,0.16)");
    halo.addColorStop(0.72, "rgba(20,40,10,0.05)");
    halo.addColorStop(1, "rgba(0,0,0,0)");
    c.beginPath();
    c.arc(cx, cy, R * 1.18, 0, Math.PI * 2);
    c.fillStyle = halo;
    c.fill();

    const ocean = c.createRadialGradient(cx, cy, 0, cx, cy, R);
    ocean.addColorStop(0, "#1a4a3a");
    ocean.addColorStop(0.48, "#0c2830");
    ocean.addColorStop(0.82, "#0a1c28");
    ocean.addColorStop(1, "#c8e7f0");
    c.beginPath();
    c.arc(cx, cy, R, 0, Math.PI * 2);
    c.fillStyle = ocean;
    c.fill();

    c.save();
    c.beginPath();
    c.arc(cx, cy, R, 0, Math.PI * 2);
    c.clip();

    c.strokeStyle = "rgba(134,239,172,0.28)";
    c.lineWidth = 0.7;
    [0, 30, 60, -30, -60].forEach(function (lat) {
      const p = projectDisc(lat, 0, cx, cy, R, rot);
      const rho = Math.hypot(p.x - cx, p.y - cy);
      c.beginPath();
      c.arc(cx, cy, rho, 0, Math.PI * 2);
      c.stroke();
    });
    c.beginPath();
    for (let lon = 0; lon < 360; lon += 15) {
      const p = projectDisc(-90, lon, cx, cy, R, rot);
      c.moveTo(cx, cy);
      c.lineTo(p.x, p.y);
    }
    c.strokeStyle = "rgba(125,211,252,0.22)";
    c.stroke();

    pathLandOn(c, projectDisc, cx, cy, R, rot);
    c.strokeStyle = "rgba(167, 243, 208, 0.9)";
    c.lineWidth = state.disc.zoom > 1.6 ? 1.2 : 0.85;
    c.stroke();

    drawNight(c, projectDisc, cx, cy, R, rot);

    c.beginPath();
    c.arc(cx, cy, R * 0.965, 0, Math.PI * 2);
    c.arc(cx, cy, R, 0, Math.PI * 2, true);
    c.fillStyle = "rgba(226, 247, 255, 0.55)";
    c.fill();

    if (state.layers.matrix) {
      c.font = Math.max(7, Math.min(11, R * 0.026)) + "px IBM Plex Mono, monospace";
      c.textAlign = "center";
      c.textBaseline = "middle";
      const step = Math.max(4, 12 / state.disc.zoom);
      const t = (state.tick / 8) | 0;
      let n = 0;
      for (let lat = 80; lat >= -70; lat -= step) {
        for (let lon = -180; lon < 180; lon += step * 1.4) {
          if (n > 480) break;
          if (!isLand(lat, lon) && (Math.abs((lat * 41 + lon) | 0) % 18) > 1) continue;
          const p = projectDisc(lat, lon, cx, cy, R, rot);
          if (!p.vis) continue;
          const gi = Math.abs((lat * 13 + lon * 7 + t) | 0) % GLYPHS.length;
          c.globalAlpha = isLand(lat, lon) ? 0.28 : 0.1;
          c.fillStyle = isLand(lat, lon) ? "#bbf7d0" : "#67e8f9";
          c.fillText(GLYPHS.charAt(gi), p.x, p.y);
          n++;
        }
      }
      c.globalAlpha = 1;
    }

    overlayEarth(c, projectDisc, cx, cy, R, rot);
    drawLabels(c, projectDisc, cx, cy, R, rot, state.disc.zoom);

    c.restore();

    c.beginPath();
    c.arc(cx, cy, R, 0, Math.PI * 2);
    c.strokeStyle = "rgba(226,247,255,0.7)";
    c.lineWidth = 3;
    c.stroke();
    c.beginPath();
    c.arc(cx, cy, 4, 0, Math.PI * 2);
    c.fillStyle = "#f8fafc";
    c.fill();

    c.fillStyle = "#bbf7d0";
    c.font = "11px IBM Plex Mono, monospace";
    c.textAlign = "center";
    c.fillText("FLAT EARTH · north disc · ice rim south · same public resources", cx, cy + R + 22);
    c.fillStyle = "#86efac";
    c.font = "10px IBM Plex Mono, monospace";
    c.fillText("N", cx, cy - 10);
    c.fillText("ICE RIM", cx, cy + R - 14);
  }

  function discLayout(w, h) {
    return {
      cx: w / 2 + state.disc.panX,
      cy: h * 0.5 + state.disc.panY,
      R: Math.min(w, h) * 0.42 * state.disc.zoom,
      rot: state.disc.rot
    };
  }

  function setDiscZoom(nz, mx, my, w, h) {
    const old = state.disc.zoom;
    state.disc.zoom = Math.max(1, Math.min(5.2, nz));
    const k = state.disc.zoom / old;
    const cx = w / 2 + state.disc.panX;
    const cy = h * 0.5 + state.disc.panY;
    const px = mx == null ? w / 2 : mx;
    const py = my == null ? h * 0.5 : my;
    state.disc.panX = px - w / 2 - (px - cx) * k;
    state.disc.panY = py - h * 0.5 - (py - cy) * k;
    if (state.disc.zoom <= 1.02) {
      state.disc.zoom = 1;
      state.disc.panX *= 0.4;
      state.disc.panY *= 0.4;
    }
  }

  function resetDisc() {
    state.disc.zoom = 1;
    state.disc.panX = 0;
    state.disc.panY = 0;
    state.disc.rot = 0;
  }

  function updateDiscMeta() {
    const el = document.getElementById("d-meta");
    if (!el) return;
    const bits = ["FLAT EARTH", state.disc.zoom.toFixed(1) + "×"];
    if (state.cursor) bits.push(fmtLL(state.cursor) + (isLand(state.cursor.lat, state.cursor.lon) ? " · land" : " · ocean"));
    else bits.push("click a pin · wheel zoom · double-click focus");
    el.textContent = bits.join(" · ");
  }

  function viewLayout(w, h) {
    const base = Math.min(w, h) * 0.38 * state.zoom;
    if (state.mode === "split") {
      return [
        { cx: w * 0.28 + state.panX, cy: h * 0.48 + state.panY, R: Math.min(w, h) * 0.28 * state.zoom, rot: state.rot, kind: "earth" },
        { cx: w * 0.72 + state.panX, cy: h * 0.48 + state.panY, R: Math.min(w, h) * 0.28 * state.zoom, rot: state.rot + 0.35, kind: "lattice" }
      ];
    }
    if (state.mode === "lattice") {
      return [{ cx: w / 2 + state.panX, cy: h * 0.48 + state.panY, R: base, rot: state.rot, kind: "lattice" }];
    }
    return [{ cx: w / 2 + state.panX, cy: h * 0.48 + state.panY, R: base, rot: state.rot, kind: "earth" }];
  }

  function hitGlobe(mx, my, w, h) {
    const views = viewLayout(w, h);
    for (let i = 0; i < views.length; i++) {
      const v = views[i];
      const ll = unproject(mx, my, v.cx, v.cy, v.R, v.rot);
      if (ll) return { ll: ll, view: v };
    }
    return null;
  }

  function setZoom(nz, mx, my, w, h) {
    const old = state.zoom;
    state.zoom = Math.max(1, Math.min(5.2, nz));
    if (old === 1 && state.zoom === 1) {
      state.panX *= 0.7;
      state.panY *= 0.7;
      return;
    }
    const k = state.zoom / old;
    const cx = w / 2 + state.panX;
    const cy = h * 0.48 + state.panY;
    const px = mx == null ? w / 2 : mx;
    const py = my == null ? h * 0.48 : my;
    state.panX = px - w / 2 - (px - cx) * k;
    state.panY = py - h * 0.48 - (py - cy) * k;
    if (state.zoom <= 1.02) {
      state.zoom = 1;
      state.panX *= 0.4;
      state.panY *= 0.4;
    }
  }

  function resetView() {
    state.zoom = 1;
    state.panX = 0;
    state.panY = 0;
    state.rot = 0.4;
    state.tilt = 0.18;
  }

  function updateMeta() {
    const el = document.getElementById("g-meta");
    if (!el) return;
    const bits = [state.zoom.toFixed(1) + "×"];
    if (state.cursor) bits.push(fmtLL(state.cursor) + (isLand(state.cursor.lat, state.cursor.lon) ? " · land" : " · ocean"));
    else bits.push("click a pin · wheel zoom · double-click focus");
    el.textContent = bits.join(" · ");
  }

  function frame() {
    const w = canvas.getBoundingClientRect().width;
    const h = canvas.getBoundingClientRect().height;
    ctx.clearRect(0, 0, w, h);
    seedDecor();
    state.tick++;
    state.stars.forEach(function (s) {
      ctx.globalAlpha = s.a * (0.65 + 0.35 * Math.sin(state.tick * 0.02 + s.x * 8));
      ctx.fillStyle = "#a7f3d0";
      ctx.fillRect(s.x * w, s.y * h, s.s, s.s);
    });
    ctx.globalAlpha = 1;
    drawRain(w, h);
    viewLayout(w, h).forEach(function (v) {
      drawGlobe(v.cx, v.cy, v.R, v.rot, v.kind);
    });
    if (!state.dragging && state.zoom < 1.2 && !state.followIss) state.rot += 0.0018;
    requestAnimationFrame(frame);
  }

  function resourceLive(id) {
    if (id === "resource_usgs") return !!state.ref.live.usgs;
    if (id === "resource_eonet") return !!state.ref.live.eonet;
    if (id === "resource_iss") return !!state.ref.live.iss;
    return false;
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
    return String(s || "").replace(/[&<>"']/g, function (c) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" })[c];
    });
  }

  function safeHref(u) {
    const raw = String(u || "").trim();
    if (!raw || /^(javascript|data|vbscript|file|blob):/i.test(raw.replace(/\s/g, ""))) return "";
    if (raw.charAt(0) === "/" && raw.charAt(1) !== "/") return raw;
    try {
      const p = new URL(raw, location.origin);
      if (p.protocol !== "https:" && p.protocol !== "http:") return "";
      if (p.username || p.password) return "";
      return p.href;
    } catch (e) { return ""; }
  }

  function feedItems() {
    const items = [];
    state.shadows.forEach(function (n) {
      const live = n.kind === "resource" && resourceLive(n.id);
      const ll = nodeLL(n);
      items.push({
        cls: live ? "ref" : "shadow",
        title: n.label,
        sub: (live ? "RESOURCE live · " : "SHADOW · ") + n.why,
        lat: ll.lat, lon: ll.lon,
        body: { class: live ? "RESOURCE" : "SHADOW", payload: null, why: n.why, public_checks: n.public_checks, id: n.id, lat: ll.lat, lon: ll.lon }
      });
    });
    if (state.ref.iss) {
      items.push({
        cls: "ref",
        title: "ISS " + state.ref.iss.lat.toFixed(2) + ", " + state.ref.iss.lon.toFixed(2),
        sub: "RESOURCE ping · click to fly both maps · public telemetry",
        lat: state.ref.iss.lat, lon: state.ref.iss.lon, follow: true,
        body: state.ref.iss
      });
    }
    if (state.ref.markets) {
      items.push({ cls: "ref", title: "Public markets " + JSON.stringify(state.ref.markets).slice(0, 80), sub: "RESOURCE · CoinGecko public prices", body: state.ref.markets });
    }
    (state.ref.launches || []).slice(0, 6).forEach(function (e) {
      items.push({ cls: "ref", title: e.title, sub: "RESOURCE · upcoming launch pad", lat: e.lat, lon: e.lon, body: e });
    });
    (state.ref.alerts || []).slice(0, 5).forEach(function (e) {
      items.push({ cls: "ref", title: e.title, sub: "RESOURCE · NWS public alert", lat: e.lat, lon: e.lon, body: e });
    });
    (state.ref.floods || []).slice(0, 4).forEach(function (e) {
      items.push({ cls: "ref", title: e.title, sub: "RESOURCE · UK flood monitoring", lat: e.lat, lon: e.lon, body: e });
    });
    (state.ref.weather || []).forEach(function (e) {
      items.push({ cls: "ref", title: e.title, sub: "RESOURCE · Open-Meteo (CC BY 4.0)", lat: e.lat, lon: e.lon, body: e });
    });
    (state.ref.world_alerts || []).slice(0, 8).forEach(function (e) {
      items.push({ cls: "ref", title: e.title, sub: "RESOURCE · public CAP/WMO-style alert", lat: e.lat, lon: e.lon, body: e });
    });
    (state.ref.radar || []).slice(0, 5).forEach(function (e) {
      items.push({ cls: "ref", title: e.title, sub: "RESOURCE · RainViewer public mosaic (educational)", lat: e.lat, lon: e.lon, body: e });
    });
    (state.ref.air || []).forEach(function (e) {
      items.push({ cls: "ref", title: e.title, sub: "RESOURCE · Open-Meteo air quality", lat: e.lat, lon: e.lon, body: e });
    });
    (state.ref.marine || []).forEach(function (e) {
      items.push({ cls: "ref", title: e.title, sub: "RESOURCE · Open-Meteo marine", lat: e.lat, lon: e.lon, body: e });
    });
    state.ref.quakes.slice(0, 8).forEach(function (q) {
      items.push({ cls: "ref", title: "M" + q.mag.toFixed(1) + " " + q.place, sub: "RESOURCE · USGS · click to fly", lat: q.lat, lon: q.lon, body: q });
    });
    state.ref.events.slice(0, 6).forEach(function (e) {
      items.push({ cls: "ref", title: e.title, sub: "RESOURCE · EONET · click to fly", lat: e.lat, lon: e.lon, body: e });
    });
    state.canon.star.slice(0, 6).forEach(function (n) {
      items.push({ cls: "canon", title: n.node_name || n.node_id, sub: "CANON · Star Chart " + (n.status || ""), body: n });
    });
    state.canon.eggs.slice(0, 5).forEach(function (n) {
      items.push({ cls: "canon", title: n.id, sub: "CANON · lattice system", body: n });
    });
    const f = state.filter;
    const q = (state.q || "").toLowerCase();
    return items.filter(function (it) {
      if (f === "resource" && it.cls !== "ref") return false;
      if (f === "canon" && it.cls !== "canon") return false;
      if (f === "shadow" && it.cls !== "shadow") return false;
      if (q && (it.title + " " + it.sub).toLowerCase().indexOf(q) < 0) return false;
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
        const it = items[i];
        state.selected = it;
        if (typeof it.lat === "number" && typeof it.lon === "number") {
          flyTo({ lat: it.lat, lon: it.lon }, it.title, it.cls, it.body, !!it.follow);
          return;
        }
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
        const id = f.id || (f.properties && f.properties.code) || "";
        return {
          lon: c[0], lat: c[1], mag: (f.properties && f.properties.mag) || 0,
          place: (f.properties && f.properties.place) || "quake",
          id: id, layer: "quakes",
          url: id ? "https://earthquake.usgs.gov/earthquakes/eventpage/" + encodeURIComponent(id) : "https://earthquake.usgs.gov/earthquakes/map/"
        };
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
        state.ref.events.push({
          title: e.title, lon: geo.coordinates[0], lat: geo.coordinates[1], id: e.id, layer: "events",
          url: e.id ? "https://eonet.gsfc.nasa.gov/api/v3/events/" + encodeURIComponent(e.id) : "https://eonet.gsfc.nasa.gov/"
        });
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
      state.ref.iss = { lat: Number(iss.latitude), lon: Number(iss.longitude), alt: iss.altitude, name: "ISS", layer: "iss", url: "https://wheretheiss.at/" };
      state.ref.live.iss = true;
      pushIss(state.ref.iss);
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
          return {
            lat: row.latitude, lon: row.longitude, title: hubs[i] + " " + cur.temperature_2m + "°", layer: "weather",
            url: "https://open-meteo.com/en/docs#latitude=" + row.latitude + "&longitude=" + row.longitude
          };
        });
        setStatus("st-wx", true);
      }
    } catch (e) { state.ref.errors.wx = String(e); }
    try {
      state.ref.markets = await getJson("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd");
    } catch (e) { state.ref.errors.markets = String(e); }
    try {
      const nws = await getJson("https://api.weather.gov/alerts/active?status=actual");
      const alerts = [];
      (nws.features || []).slice(0, 40).forEach(function (f) {
        const p = f.properties || {};
        const g = f.geometry;
        let lat = null, lon = null;
        const coords = g && g.coordinates;
        function firstPair(x) {
          if (!Array.isArray(x) || !x.length) return null;
          if (typeof x[0] === "number" && typeof x[1] === "number") return x;
          return firstPair(x[0]);
        }
        const pair = firstPair(coords);
        if (pair) { lon = pair[0]; lat = pair[1]; }
        const href = (p["@id"] && String(p["@id"]).indexOf("https://") === 0) ? p["@id"] : "https://api.weather.gov/alerts/active?status=actual";
        const row = { title: p.headline || p.event || "NWS alert", url: href, layer: "alerts", source: "nws_live" };
        if (lat != null && lon != null) { row.lat = lat; row.lon = lon; }
        alerts.push(row);
      });
      if (alerts.length) {
        state.ref.world_alerts = alerts;
        state.ref.live.nws = true;
        setStatus("st-nws", true);
      } else {
        setStatus("st-nws", "shadow", "named");
      }
    } catch (e) {
      state.ref.errors.nws = String(e);
      state.ref.live.nws = false;
      setStatus("st-nws", "shadow", "named");
    }
    try {
      const L = await getJson("https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=8&mode=list");
      const pads = [];
      (L.results || []).forEach(function (row) {
        const pad = row.pad || {};
        const lat = parseFloat(pad.latitude), lon = parseFloat(pad.longitude);
        if (!isNaN(lat) && !isNaN(lon)) {
          pads.push({
            lat: lat, lon: lon, title: row.name || "launch", layer: "launches",
            url: row.url || (pad.name ? "https://en.wikipedia.org/wiki/" + encodeURIComponent(pad.name) : "https://ll.thespacedevs.com/")
          });
        }
      });
      if (pads.length) state.ref.launches = pads;
    } catch (e) { state.ref.errors.launches = String(e); }
  }

  async function refreshIss() {
    try {
      const iss = await getJson(REF_URLS.iss);
      state.ref.iss = { lat: Number(iss.latitude), lon: Number(iss.longitude), alt: iss.altitude, name: "ISS", layer: "iss", url: "https://wheretheiss.at/" };
      state.ref.live.iss = true;
      pushIss(state.ref.iss);
      if (state.followIss) lookAt(state.ref.iss);
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

  async function hfSummary() {
    const out = document.getElementById("ollama-out");
    const payload = {
      doctrine: "RESOURCE vs CANON vs SHADOW. Never invent private payloads.",
      quakes: (state.ref.quakes || []).length,
      alerts: (state.ref.world_alerts || []).length,
      iss: state.ref.iss,
      markets: state.ref.markets
    };
    let token = "";
    try { token = localStorage.getItem("lygo_hf_token") || ""; } catch (e) {}
    if (!token) {
      token = window.prompt("Paste a free Hugging Face token (hf_...) to call SmolLM2. Stored only in this browser. Cancel to skip.") || "";
      if (token) {
        try { localStorage.setItem("lygo_hf_token", token); } catch (e) {}
      }
    }
    if (!token) {
      out.textContent = "No HF token. Get a free one at huggingface.co/settings/tokens — or use Ollama. The globe still runs without a model.";
      return;
    }
    out.textContent = "Asking HuggingFaceTB/SmolLM2-1.7B-Instruct via HF Inference…";
    try {
      const res = await fetch("https://router.huggingface.co/v1/chat/completions", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": "Bearer " + token },
        body: JSON.stringify({
          model: "HuggingFaceTB/SmolLM2-1.7B-Instruct",
          max_tokens: 280,
          messages: [
            { role: "system", content: "You summarize LYGO Public Witness overlays. Public=RESOURCE, lattice=CANON, private=named SHADOW. Six short bullets. No invented intel." },
            { role: "user", content: JSON.stringify(payload) }
          ]
        })
      });
      const j = await res.json();
      const txt = (j.choices && j.choices[0] && j.choices[0].message && j.choices[0].message.content) || JSON.stringify(j).slice(0, 800);
      out.textContent = txt;
    } catch (e) {
      out.textContent = "HF Inference named shadow this run. Globe still live. (" + e + ")";
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
      state.dragging = true;
      state.dragMoved = 0;
      state.lastX = e.clientX;
      state.lastY = e.clientY;
      canvas.setPointerCapture(e.pointerId);
    });
    canvas.addEventListener("pointerup", function (e) {
      const moved = state.dragMoved;
      state.dragging = false;
      if (moved < 8) {
        const rect = canvas.getBoundingClientRect();
        const hit = hitGlobe(e.clientX - rect.left, e.clientY - rect.top, rect.width, rect.height);
        if (hit) tryPick(hit.ll);
      }
    });
    canvas.addEventListener("pointerleave", function () { state.cursor = null; updateMeta(); });
    canvas.addEventListener("pointermove", function (e) {
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      const hit = hitGlobe(mx, my, rect.width, rect.height);
      state.cursor = hit ? hit.ll : null;
      state.hover = state.cursor;
      updateMeta();
      updateDiscMeta();
      if (!state.dragging) return;
      const dx = e.clientX - state.lastX;
      const dy = e.clientY - state.lastY;
      state.dragMoved += Math.abs(dx) + Math.abs(dy);
      if (e.shiftKey || e.buttons === 2) {
        state.panX += dx;
        state.panY += dy;
      } else {
        state.rot += dx * 0.008;
        state.tilt = Math.max(-1.05, Math.min(1.05, state.tilt + dy * 0.004));
        if (state.zoom > 1.15) {
          state.panX += dx * 0.35;
          state.panY += dy * 0.35;
        }
      }
      state.lastX = e.clientX;
      state.lastY = e.clientY;
    });
    canvas.addEventListener("wheel", function (e) {
      e.preventDefault();
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      const factor = e.deltaY < 0 ? 1.12 : 1 / 1.12;
      setZoom(state.zoom * factor, mx, my, rect.width, rect.height);
      updateMeta();
    }, { passive: false });
    canvas.addEventListener("dblclick", function (e) {
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      const hit = hitGlobe(mx, my, rect.width, rect.height);
      if (!hit) { resetView(); updateMeta(); return; }
      state.rot = -(hit.ll.lon * Math.PI) / 180;
      state.tilt = Math.max(-1.05, Math.min(1.05, (hit.ll.lat * Math.PI) / 180 * 0.9));
      state.panX = 0;
      state.panY = 0;
      setZoom(Math.min(5.2, state.zoom < 1.4 ? 2.4 : state.zoom * 1.35), rect.width / 2, rect.height * 0.48, rect.width, rect.height);
      updateMeta();
    });
    canvas.addEventListener("contextmenu", function (e) { e.preventDefault(); });
    function zin() {
      const r = canvas.getBoundingClientRect();
      setZoom(state.zoom * 1.22, r.width / 2, r.height * 0.48, r.width, r.height);
      updateMeta();
    }
    function zout() {
      const r = canvas.getBoundingClientRect();
      setZoom(state.zoom / 1.22, r.width / 2, r.height * 0.48, r.width, r.height);
      updateMeta();
    }
    const zinEl = document.getElementById("g-zin");
    const zoutEl = document.getElementById("g-zout");
    const zreset = document.getElementById("g-reset");
    if (zinEl) zinEl.addEventListener("click", zin);
    if (zoutEl) zoutEl.addEventListener("click", zout);
    if (zreset) zreset.addEventListener("click", function () { resetView(); updateMeta(); });
    function toggleFs(node) {
      if (!node) return;
      if (document.fullscreenElement) document.exitFullscreen().catch(function () {});
      else node.requestFullscreen().catch(function () {});
    }
    const gfull = document.getElementById("g-full");
    const dfull = document.getElementById("d-full");
    const maps = document.querySelector(".maps");
    if (gfull) gfull.addEventListener("click", function () { toggleFs(document.querySelector(".globe-wrap") || maps); });
    if (dfull) dfull.addEventListener("click", function () { toggleFs(document.querySelector(".disc-wrap") || maps); });
    const follow = document.getElementById("btn-follow-iss");
    if (follow) {
      follow.addEventListener("click", function () {
        state.followIss = !state.followIss;
        follow.classList.toggle("on", state.followIss);
        if (state.followIss && state.ref.iss) {
          lookAt(state.ref.iss);
          showPick({ lat: state.ref.iss.lat, lon: state.ref.iss.lon, title: "ISS", cls: "ref", body: state.ref.iss, km: 0 });
        }
      });
    }
    const copyBtn = document.getElementById("btn-copy-ll");
    if (copyBtn) {
      copyBtn.addEventListener("click", function () {
        const ll = state.pick || state.cursor;
        if (!ll) return;
        const txt = ll.lat.toFixed(4) + ", " + ll.lon.toFixed(4);
        if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(txt).catch(function () {});
      });
    }
    const qel = document.getElementById("feed-q");
    if (qel) {
      qel.addEventListener("input", function () {
        state.q = qel.value || "";
        renderFeeds();
      });
    }
    window.addEventListener("keydown", function (e) {
      if (e.target && /input|textarea/i.test(e.target.tagName)) return;
      if (e.key === "+" || e.key === "=") zin();
      if (e.key === "-" || e.key === "_") zout();
      if (e.key === "0") { resetView(); updateMeta(); }
      if (e.key === "ArrowLeft") state.rot -= 0.08;
      if (e.key === "ArrowRight") state.rot += 0.08;
      if (e.key === "ArrowUp") state.tilt = Math.min(1.05, state.tilt + 0.05);
      if (e.key === "ArrowDown") state.tilt = Math.max(-1.05, state.tilt - 0.05);
    });
    document.getElementById("btn-refresh").addEventListener("click", function () { boot(); });
    document.getElementById("btn-ollama").addEventListener("click", ollamaSummary);
    var hfb = document.getElementById("btn-hf");
    if (hfb) hfb.addEventListener("click", hfSummary);
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
    function fill(id, rows, st, cap) {
      const ul = document.getElementById(id);
      const tag = document.getElementById(st);
      if (!ul) return;
      ul.innerHTML = (rows || []).slice(0, cap || 18).map(function (r) {
        const when = r.date || r.last_seen_utc || r.first_seen_utc || "";
        return "<li><a href=\"" + escapeHtml(r.url) + "\" target=\"_blank\" rel=\"noopener\">" + escapeHtml(r.title) + "</a><div class=\"src\">" + escapeHtml(r.source || "") + (when ? " · " + escapeHtml(String(when).slice(0, 22)) : "") + "</div></li>";
      }).join("") || "<li>No public items in this lane.</li>";
      if (tag) { tag.textContent = String((rows || []).length); tag.className = "tag ok"; }
    }
    fill("news-severe", pack.severe, "st-news-sev", 18);
    fill("news-world", pack.world, "st-news-world", 18);
    const meta = document.getElementById("news-meta");
    if (meta) {
      const failed = (pack.sources || []).filter(function (s) { return !s.ok; }).map(function (s) { return s.id; });
      meta.textContent = "Monitor " + (pack.utc || "") + " · " + ((pack.sources || []).filter(function (s) { return s.ok; }).length) + " live wires" + (failed.length ? " · named miss: " + failed.join(", ") : "");
    }
  }

  async function loadNews() {
    try {
      const pack = await getJson("news-monitor.json");
      const extra = [];
      (state.ref.quakes || []).filter(function (q) { return (q.mag || 0) >= 5.5; }).forEach(function (q) {
        extra.push({ title: "M" + q.mag + " " + (q.title || q.place || "quake"), url: q.url || "https://earthquake.usgs.gov/", source: "usgs_live", lane: "severe", date: "", class: "RESOURCE" });
      });
      (state.ref.events || []).slice(0, 8).forEach(function (e) {
        extra.push({ title: e.title || "EONET", url: e.url || "https://eonet.gsfc.nasa.gov/", source: "eonet_live", lane: "severe", date: "", class: "RESOURCE" });
      });
      (state.ref.world_alerts || []).slice(0, 8).forEach(function (a) {
        extra.push({ title: a.title, url: a.url || "https://api.weather.gov/alerts/active?status=actual", source: "nws_live", lane: "severe", date: "", class: "RESOURCE" });
      });
      pack.severe = extra.concat(pack.severe || []);
      renderNews(pack);
    } catch (e) {
      const tag = document.getElementById("st-news-sev");
      if (tag) { tag.textContent = "named"; tag.className = "tag shadow"; }
    }
    try {
      const led = await getJson("event-ledger.json");
      const ul = document.getElementById("news-ledger");
      const tag = document.getElementById("st-news-led");
      const tip = document.getElementById("ledger-tip");
      if (ul) {
        ul.innerHTML = (led.entries || []).slice(0, 18).map(function (r) {
          return "<li><a href=\"" + escapeHtml(r.url) + "\" target=\"_blank\" rel=\"noopener\">" + escapeHtml(r.title) + "</a><div class=\"src\">" + escapeHtml(r.source || "") + " · " + escapeHtml(String(r.last_seen_utc || "").slice(0, 19)) + "</div></li>";
        }).join("") || "<li>Ledger empty this run.</li>";
      }
      if (tag) { tag.textContent = String(led.count || (led.entries || []).length); tag.className = "tag ok"; }
      if (tip) tip.textContent = "RESOURCE log · tip " + String(led.tip_sha256 || "").slice(0, 16) + " · not Star Chart";
    } catch (e) {
      const tag = document.getElementById("st-news-led");
      if (tag) { tag.textContent = "named"; tag.className = "tag shadow"; }
    }
  }

  async function boot() {
    document.getElementById("sig").textContent = SIG;
    await loadShadows();
    await Promise.all([loadWorld(), loadCanon(), loadRef(), loadHfFeed(), loadCameras()]);
    renderFeeds();
    await loadNews();
    parseHash();
    tickClock();
  }

  window.LYGO_WITNESS = {
    state: state,
    showPick: showPick,
    nearestPin: nearestPin,
    isLand: isLand,
    fmtLL: fmtLL,
    nodeLL: nodeLL,
    resourceLive: resourceLive,
    PLACES: PLACES
  };

  window.addEventListener("resize", resize);
  window.addEventListener("hashchange", parseHash);
  resize();
  bind();
  boot();
  frame();
  setInterval(tickClock, 1000);
  setInterval(refreshIss, 12000);
  setInterval(loadCameras, 300000);
})();
