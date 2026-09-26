/* LYGO Public Witness — flat disc module. Own camera. Click never resets view. */
(function () {
  "use strict";
  const canvas = document.getElementById("disc");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const cam = {
    zoom: 1, panX: 0, panY: 0, rot: 0,
    dragging: false, lastX: 0, lastY: 0, moved: 0, tick: 0
  };

  function W() { return window.LYGO_WITNESS || null; }

  function size() {
    const r = canvas.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.max(320, r.width) * dpr;
    canvas.height = Math.max(280, r.height) * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function layout() {
    const w = canvas.getBoundingClientRect().width;
    const h = canvas.getBoundingClientRect().height;
    return {
      w: w, h: h,
      cx: w / 2 + cam.panX,
      cy: h * 0.5 + cam.panY,
      R: Math.min(w, h) * 0.42 * cam.zoom,
      rot: cam.rot
    };
  }

  function project(lat, lon, L) {
    const colat = ((90 - lat) * Math.PI) / 180;
    const rho = (L.R * colat) / Math.PI;
    const th = (lon * Math.PI) / 180 + L.rot;
    return {
      x: L.cx + rho * Math.sin(th),
      y: L.cy - rho * Math.cos(th),
      rho: rho,
      vis: rho <= L.R + 1
    };
  }

  function unproject(sx, sy, L) {
    const dx = sx - L.cx;
    const dy = L.cy - sy;
    const rho = Math.sqrt(dx * dx + dy * dy);
    if (rho > L.R * 1.08) return null;
    const lat = 90 - (rho / L.R) * 180;
    let lon = ((Math.atan2(dx, dy) - L.rot) * 180) / Math.PI;
    while (lon > 180) lon -= 360;
    while (lon < -180) lon += 360;
    return { lat: lat, lon: lon };
  }

  function segOk(a, b, R) {
    if (!a || !b || !a.vis || !b.vis) return false;
    const dx = a.x - b.x;
    const dy = a.y - b.y;
    const lim = R * 0.32;
    return dx * dx + dy * dy < lim * lim;
  }

  function setZoom(nz, mx, my) {
    const L = layout();
    const old = cam.zoom;
    cam.zoom = Math.max(0.85, Math.min(6, nz));
    const k = cam.zoom / old;
    const px = mx == null ? L.w / 2 : mx;
    const py = my == null ? L.h * 0.5 : my;
    cam.panX = px - L.w / 2 - (px - L.cx) * k;
    cam.panY = py - L.h * 0.5 - (py - L.cy) * k;
  }

  function meta(ll) {
    const el = document.getElementById("d-meta");
    if (!el) return;
    const bits = ["FLAT EARTH", cam.zoom.toFixed(1) + "×", "drag pan · shift-drag rotate"];
    const api = W();
    if (ll && api && api.fmtLL) {
      bits.push(api.fmtLL(ll) + (api.isLand && api.isLand(ll.lat, ll.lon) ? " · land" : " · ocean"));
    }
    el.textContent = bits.join(" · ");
  }

  function landFill(L) {
    const api = W();
    if (!api || !api.isLand) return;
    const step = cam.zoom > 2.4 ? 1.7 : (cam.zoom > 1.4 ? 2.3 : 3.2);
    ctx.fillStyle = "rgba(22, 90, 48, 0.9)";
    for (let lat = -84; lat <= 84; lat += step) {
      const lonStep = Math.max(1.05, step * Math.max(Math.cos((lat * Math.PI) / 180), 0.16));
      for (let lon = -180; lon < 180; lon += lonStep) {
        if (!api.isLand(lat, lon)) continue;
        const p = project(lat, lon, L);
        if (!p.vis) continue;
        const s = Math.max(2.0, (step / 76) * L.R * 1.4);
        ctx.fillRect(p.x - s / 2, p.y - s / 2, s + 0.5, s + 0.5);
      }
    }
  }

  function strokeLand(L) {
    const api = W();
    const rings = api && api.state && api.state.world;
    if (!rings || !rings.length) return;
    ctx.beginPath();
    rings.forEach(function (ring) {
      let prev = null;
      for (let i = 0; i < ring.length; i++) {
        const p = project(ring[i][1], ring[i][0], L);
        if (segOk(prev, p, L.R)) ctx.lineTo(p.x, p.y);
        else if (p.vis) ctx.moveTo(p.x, p.y);
        prev = p.vis ? p : null;
      }
    });
    ctx.strokeStyle = "rgba(167, 243, 208, 0.92)";
    ctx.lineWidth = cam.zoom > 1.6 ? 1.15 : 0.8;
    ctx.stroke();
  }

  function dots(L) {
    const api = W();
    if (!api || !api.state) return;
    const S = api.state;
    const layers = S.layers || {};
    function mark(list, color, r) {
      (list || []).forEach(function (e) {
        if (typeof e.lat !== "number") return;
        const p = project(e.lat, e.lon, L);
        if (!p.vis) return;
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
        ctx.fill();
      });
    }
    if (layers.quakes) mark(S.ref.quakes, "rgba(245,158,11,0.92)", 3);
    if (layers.events) {
      (S.ref.events || []).forEach(function (e) {
        const p = project(e.lat, e.lon, L);
        if (!p.vis) return;
        ctx.strokeStyle = "#fb7185";
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.arc(p.x, p.y, 5, 0, Math.PI * 2);
        ctx.stroke();
      });
    }
    if (layers.iss && S.issTrail && S.issTrail.length > 1) {
      ctx.beginPath();
      let prev = null;
      S.issTrail.forEach(function (pt) {
        const p = project(pt.lat, pt.lon, L);
        if (segOk(prev, p, L.R)) ctx.lineTo(p.x, p.y);
        else if (p.vis) ctx.moveTo(p.x, p.y);
        prev = p.vis ? p : null;
      });
      ctx.strokeStyle = "rgba(125,211,252,0.55)";
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }
    if (layers.iss && S.ref.iss) {
      const p = project(S.ref.iss.lat, S.ref.iss.lon, L);
      if (p.vis) {
        ctx.fillStyle = "#e0f2fe";
        ctx.beginPath();
        ctx.arc(p.x, p.y, 4.2, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = "#7dd3fc";
        ctx.font = "10px IBM Plex Mono, monospace";
        ctx.textAlign = "left";
        ctx.fillText("ISS", p.x + 7, p.y - 4);
      }
    }
    if (layers.alerts) mark(S.ref.alerts, "rgba(251,191,36,0.9)", 3);
    if (layers.alerts) mark(S.ref.world_alerts, "rgba(251,146,60,0.9)", 3);
    if (layers.floods) mark(S.ref.floods, "rgba(56,189,248,0.9)", 3);
    if (layers.launches) mark(S.ref.launches, "rgba(244,114,182,0.95)", 4);
    if (layers.aurora) mark(S.ref.aurora, "rgba(52,211,153,0.55)", 2);
    if (layers.flights) mark(S.ref.flights, "rgba(125,211,252,0.7)", 1.7);
    if (layers.weather) mark(S.ref.weather, "rgba(250,250,250,0.85)", 3.2);
    if (layers.radar) mark(S.ref.radar, "rgba(96,165,250,0.85)", 3.8);
    if (layers.air) mark(S.ref.air, "rgba(192,132,252,0.9)", 3.4);
    if (layers.marine) mark(S.ref.marine, "rgba(45,212,191,0.9)", 3.2);
    if (layers.shadow && api.nodeLL) {
      (S.shadows || []).forEach(function (n) {
        const ll = api.nodeLL(n);
        const p = project(ll.lat, ll.lon, L);
        if (!p.vis) return;
        const live = api.resourceLive && api.resourceLive(n.id);
        if (live) {
          ctx.fillStyle = "#34d399";
          ctx.beginPath();
          ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
          ctx.fill();
        } else {
          ctx.strokeStyle = "#a78bfa";
          ctx.setLineDash([3, 3]);
          ctx.beginPath();
          ctx.arc(p.x, p.y, 8, 0, Math.PI * 2);
          ctx.stroke();
          ctx.setLineDash([]);
        }
      });
    }
    const pick = S.pick;
    if (pick && typeof pick.lat === "number") {
      const p = project(pick.lat, pick.lon, L);
      if (p.vis) {
        ctx.strokeStyle = "#fbbf24";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(p.x, p.y, 13, 0, Math.PI * 2);
        ctx.stroke();
      }
    }
  }

  function labels(L) {
    if (cam.zoom < 1.55) return;
    const api = W();
    const places = api && api.PLACES;
    if (!places) return;
    ctx.font = (cam.zoom > 2.6 ? 11 : 9) + "px IBM Plex Sans, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "bottom";
    const used = [];
    places.forEach(function (pl) {
      const p = project(pl.lat, pl.lon, L);
      if (!p.vis) return;
      let ok = true;
      for (let i = 0; i < used.length; i++) {
        const dx = used[i].x - p.x, dy = used[i].y - p.y;
        if (dx * dx + dy * dy < 1400) { ok = false; break; }
      }
      if (!ok) return;
      used.push(p);
      const w = ctx.measureText(pl.n).width;
      ctx.fillStyle = "rgba(8,14,24,0.62)";
      ctx.fillRect(p.x - w / 2 - 3, p.y - 13, w + 6, 14);
      ctx.fillStyle = "#e2e8f0";
      ctx.fillText(pl.n, p.x, p.y - 1);
    });
  }

  function draw() {
    const L = layout();
    ctx.clearRect(0, 0, L.w, L.h);
    ctx.fillStyle = "#030604";
    ctx.fillRect(0, 0, L.w, L.h);
    const halo = ctx.createRadialGradient(L.cx, L.cy, L.R * 0.15, L.cx, L.cy, L.R * 1.18);
    halo.addColorStop(0, "rgba(52,211,153,0.16)");
    halo.addColorStop(1, "rgba(0,0,0,0)");
    ctx.beginPath();
    ctx.arc(L.cx, L.cy, L.R * 1.18, 0, Math.PI * 2);
    ctx.fillStyle = halo;
    ctx.fill();
    const ocean = ctx.createRadialGradient(L.cx, L.cy, 0, L.cx, L.cy, L.R);
    ocean.addColorStop(0, "#1a4a3a");
    ocean.addColorStop(0.5, "#0c2830");
    ocean.addColorStop(1, "#c8e7f0");
    ctx.beginPath();
    ctx.arc(L.cx, L.cy, L.R, 0, Math.PI * 2);
    ctx.fillStyle = ocean;
    ctx.fill();
    ctx.save();
    ctx.beginPath();
    ctx.arc(L.cx, L.cy, L.R, 0, Math.PI * 2);
    ctx.clip();
    ctx.strokeStyle = "rgba(134,239,172,0.28)";
    ctx.lineWidth = 0.7;
    [0, 30, 60, -30, -60].forEach(function (lat) {
      const p = project(lat, 0, L);
      ctx.beginPath();
      ctx.arc(L.cx, L.cy, Math.hypot(p.x - L.cx, p.y - L.cy), 0, Math.PI * 2);
      ctx.stroke();
    });
    ctx.beginPath();
    for (let lon = 0; lon < 360; lon += 15) {
      const p = project(-90, lon, L);
      ctx.moveTo(L.cx, L.cy);
      ctx.lineTo(p.x, p.y);
    }
    ctx.strokeStyle = "rgba(125,211,252,0.22)";
    ctx.stroke();
    landFill(L);
    strokeLand(L);
    ctx.beginPath();
    ctx.arc(L.cx, L.cy, L.R * 0.965, 0, Math.PI * 2);
    ctx.arc(L.cx, L.cy, L.R, 0, Math.PI * 2, true);
    ctx.fillStyle = "rgba(226,247,255,0.55)";
    ctx.fill();
    dots(L);
    labels(L);
    ctx.restore();
    ctx.beginPath();
    ctx.arc(L.cx, L.cy, L.R, 0, Math.PI * 2);
    ctx.strokeStyle = "rgba(226,247,255,0.7)";
    ctx.lineWidth = 3;
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(L.cx, L.cy, 4, 0, Math.PI * 2);
    ctx.fillStyle = "#f8fafc";
    ctx.fill();
    ctx.fillStyle = "#bbf7d0";
    ctx.font = "11px IBM Plex Mono, monospace";
    ctx.textAlign = "center";
    ctx.fillText("FLAT EARTH · north disc · drag to pan · click a pin (view stays)", L.cx, L.cy + L.R + 22);
    ctx.fillStyle = "#86efac";
    ctx.font = "10px IBM Plex Mono, monospace";
    ctx.fillText("N", L.cx, L.cy - 10);
    ctx.fillText("ICE RIM", L.cx, L.cy + L.R - 14);
  }

  function pickAt(mx, my) {
    const api = W();
    if (!api || !api.nearestPin || !api.showPick) return;
    const L = layout();
    const ll = unproject(mx, my, L);
    if (!ll) return;
    api.showPick(api.nearestPin(ll.lat, ll.lon));
  }

  function bind() {
    canvas.addEventListener("pointerdown", function (e) {
      cam.dragging = true;
      cam.moved = 0;
      cam.lastX = e.clientX;
      cam.lastY = e.clientY;
      canvas.setPointerCapture(e.pointerId);
    });
    canvas.addEventListener("pointerup", function (e) {
      const moved = cam.moved;
      cam.dragging = false;
      if (moved < 10) {
        const rect = canvas.getBoundingClientRect();
        pickAt(e.clientX - rect.left, e.clientY - rect.top);
      }
    });
    canvas.addEventListener("pointermove", function (e) {
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      const ll = unproject(mx, my, layout());
      meta(ll);
      if (!cam.dragging) return;
      const dx = e.clientX - cam.lastX;
      const dy = e.clientY - cam.lastY;
      cam.moved += Math.abs(dx) + Math.abs(dy);
      if (e.shiftKey || e.altKey || e.buttons === 2) cam.rot += dx * 0.008;
      else {
        cam.panX += dx;
        cam.panY += dy;
      }
      cam.lastX = e.clientX;
      cam.lastY = e.clientY;
    });
    canvas.addEventListener("wheel", function (e) {
      e.preventDefault();
      const rect = canvas.getBoundingClientRect();
      setZoom(cam.zoom * (e.deltaY < 0 ? 1.12 : 1 / 1.12), e.clientX - rect.left, e.clientY - rect.top);
      meta(unproject(e.clientX - rect.left, e.clientY - rect.top, layout()));
    }, { passive: false });
    canvas.addEventListener("dblclick", function (e) {
      e.preventDefault();
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      setZoom(Math.min(6, cam.zoom * 1.35), mx, my);
      meta(unproject(mx, my, layout()));
    });
    canvas.addEventListener("contextmenu", function (e) { e.preventDefault(); });
    const zin = document.getElementById("d-zin");
    const zout = document.getElementById("d-zout");
    const zreset = document.getElementById("d-reset");
    if (zin) zin.addEventListener("click", function () {
      const r = canvas.getBoundingClientRect();
      setZoom(cam.zoom * 1.22, r.width / 2, r.height * 0.5);
      meta();
    });
    if (zout) zout.addEventListener("click", function () {
      const r = canvas.getBoundingClientRect();
      setZoom(cam.zoom / 1.22, r.width / 2, r.height * 0.5);
      meta();
    });
    if (zreset) zreset.addEventListener("click", function () {
      cam.zoom = 1; cam.panX = 0; cam.panY = 0; cam.rot = 0;
      meta();
    });
  }

  function loop() {
    cam.tick++;
    draw();
    requestAnimationFrame(loop);
  }

  window.addEventListener("resize", size);
  size();
  bind();
  loop();
  meta();
})();
