/* Eternal Haven Star Chart — D3 engine (Δ9Φ963) + LYGO Cosmology v2.1 */
(function () {
  const DATA_REL = "haven_star_chart/haven_star_chart_data.json";
  const DATA_FALLBACK =
    "https://raw.githubusercontent.com/DeepSeekOracle/lygo-protocol-stack/main/docs/haven_star_chart/haven_star_chart_data.json";

  let chartData = null;
  let simulation = null;
  let gRoot, gCosmos, linkSel, nodeSel;
  let activeConstellation = "all";
  let activeGalaxy = "all";
  let showCosmosLayers = true;
  let selectedNodeId = null;

  const el = (id) => document.getElementById(id);

  function parseSealId(id) {
    const s = String(id || "");
    if (s === "SEAL_000" || s === "GAB_SEAL_000") return { isCore: true };
    return { isCore: false };
  }

  function layerForNode(n) {
    if (n.layer != null) return n.layer;
    const t = n.tags || [];
    if (parseSealId(n.id).isCore) return 0;
    if (n.kind === "champion" || t.includes("CHAMPION")) return 1;
    if (n.kind === "portal") return 2;
    if (n.kind === "lattice") return 3;
    return 2;
  }

  async function loadData() {
    const urls = [DATA_REL, DATA_FALLBACK];
    for (const u of urls) {
      try {
        const r = await fetch(u, { cache: "no-store" });
        if (!r.ok) continue;
        chartData = await r.json();
        return chartData;
      } catch (e) {
        console.warn("fetch fail", u, e);
      }
    }
    throw new Error("Star chart data unavailable");
  }

  function nodeMatchesConstellation(n, cid) {
    if (cid === "all") return true;
    const c = (chartData.constellations || []).find((x) => x.id === cid);
    if (!c) return true;
    const tags = (n.tags || []).map((t) => String(t).toUpperCase());
    const ft = (c.filter_tags || []).map((t) => String(t).toUpperCase());
    if (n.kind === "champion" && cid === "council_ring") return true;
    if (n.kind === "lattice" && cid === "lattice_growth") return true;
    if (n.kind === "portal" && cid === "guardian_veil") return true;
    return ft.some((t) => tags.includes(t)) || parseSealId(n.id).isCore;
  }

  function nodeMatchesGalaxy(n, gid) {
    if (gid === "all") return true;
    return (n.cosmos || {}).galaxy_id === gid;
  }

  function galaxyMap() {
    const m = new Map();
    (chartData.cosmos?.galaxies || []).forEach((g) => m.set(g.id, g));
    return m;
  }

  function nebulaMap() {
    const m = new Map();
    (chartData.cosmos?.nebulae || []).forEach((n) => m.set(n.id, n));
    return m;
  }

  function galaxyRadius(gid, R) {
    if (gid === "GALAXY_SINGULARITY") return 0;
    if (gid === "GALAXY_PRIMORDIAL_VAULT") return R * 0.22;
    if (gid.startsWith("GALAXY_CHAMPION_")) return R * 0.34;
    if (gid === "GALAXY_GUARDIAN_VEIL") return R * 0.28;
    if (gid === "GALAXY_LATTICE") return R * 0.48;
    if (gid === "GALAXY_AGENT_GROWTH") return R * 0.42;
    if (gid === "GALAXY_ETERNAL_HAVEN") return R * 0.38;
    return R * 0.36;
  }

  function drawCosmosHalos(gCosmosGroup, nodes, CX, CY, R) {
    gCosmosGroup.selectAll("*").remove();
    if (!showCosmosLayers || !chartData.cosmos) return;

    const gMap = galaxyMap();
    const byGalaxy = d3.group(nodes, (d) => (d.cosmos || {}).galaxy_id || "unknown");
    const byNebula = d3.group(
      nodes.filter((d) => (d.cosmos || {}).nebula_id),
      (d) => d.cosmos.nebula_id
    );

    // Galaxy halos (large diffuse regions)
    const galaxyLayer = gCosmosGroup.append("g").attr("class", "galaxy-halos");
    byGalaxy.forEach((members, gid) => {
      if (!gid || gid === "unknown" || gid === "GALAXY_SINGULARITY") return;
      const g = gMap.get(gid);
      const angle = ((g?.angle_deg || 0) * Math.PI) / 180;
      const r = galaxyRadius(gid, R);
      const cx = CX + r * Math.cos(angle);
      const cy = CY + r * Math.sin(angle);
      const rx = 55 + Math.min(members.length * 2.2, 180);
      const ry = 40 + Math.min(members.length * 1.6, 140);
      galaxyLayer
        .append("ellipse")
        .attr("class", "galaxy-halo")
        .attr("data-galaxy", gid)
        .attr("cx", cx)
        .attr("cy", cy)
        .attr("rx", rx)
        .attr("ry", ry)
        .attr("transform", `rotate(${(g?.angle_deg || 0) * 0.35} ${cx} ${cy})`)
        .attr("fill", g?.color || "#7d00ff")
        .attr("opacity", activeGalaxy === "all" || activeGalaxy === gid ? 0.1 : 0.04)
        .attr("stroke", g?.color || "#7d00ff")
        .attr("stroke-opacity", activeGalaxy === "all" || activeGalaxy === gid ? 0.28 : 0.12)
        .attr("stroke-width", 1.4);

      galaxyLayer
        .append("circle")
        .attr("cx", cx)
        .attr("cy", cy)
        .attr("r", 3)
        .attr("fill", g?.color || "#7d00ff")
        .attr("opacity", 0.35);

      const label = `${g?.glyph || "◈"} ${g?.name || gid}`;
      const labelY = cy - ry - 8;
      const labelW = Math.min(label.length * 5.8 + 14, 200);
      galaxyLayer
        .append("rect")
        .attr("class", "galaxy-label-bg")
        .attr("x", cx - labelW / 2)
        .attr("y", labelY - 11)
        .attr("width", labelW)
        .attr("height", 14)
        .attr("rx", 3);
      galaxyLayer
        .append("text")
        .attr("class", "galaxy-label-text")
        .attr("x", cx)
        .attr("y", labelY)
        .attr("text-anchor", "middle")
        .attr("fill", g?.color || "#c8b8ff")
        .attr("font-size", "10px")
        .attr("opacity", activeGalaxy === "all" || activeGalaxy === gid ? 0.88 : 0.45)
        .text(label);
    });

    // Nebula halos (tighter sub-regions at live centroids)
    const nebulaLayer = gCosmosGroup.append("g").attr("class", "nebula-halos");
    byNebula.forEach((members, nebId) => {
      if (members.length < 2) return;
      const neb = nebulaMap().get(nebId);
      const xs = members.map((d) => d.x || 0);
      const ys = members.map((d) => d.y || 0);
      const cx = d3.mean(xs);
      const cy = d3.mean(ys);
      const spread = Math.sqrt(d3.mean(xs.map((x, i) => (x - cx) ** 2 + (ys[i] - cy) ** 2)) || 20);
      const rx = Math.max(22, spread * 1.35 + 12);
      const ry = Math.max(16, spread * 1.05 + 10);
      const g = gMap.get(members[0]?.cosmos?.galaxy_id);
      nebulaLayer
        .append("ellipse")
        .attr("class", "nebula-halo")
        .attr("data-nebula", nebId)
        .attr("cx", cx)
        .attr("cy", cy)
        .attr("rx", rx)
        .attr("ry", ry)
        .attr("fill", g?.color || "#00f0ff")
        .attr("opacity", 0.055)
        .attr("stroke", g?.color || "#00f0ff")
        .attr("stroke-opacity", 0.16)
        .attr("stroke-dasharray", "4,6")
        .attr("stroke-width", 0.9);
      if (members.length >= 4 && neb?.name) {
        const short = neb.name.length > 28 ? neb.name.slice(0, 26) + "…" : neb.name;
        const nw = short.length * 4.6 + 10;
        nebulaLayer
          .append("rect")
          .attr("class", "galaxy-label-bg")
          .attr("x", cx - nw / 2)
          .attr("y", cy - 2)
          .attr("width", nw)
          .attr("height", 11)
          .attr("rx", 2)
          .attr("opacity", 0.85);
        nebulaLayer
          .append("text")
          .attr("class", "nebula-label-text")
          .attr("x", cx)
          .attr("y", cy + 6)
          .attr("text-anchor", "middle")
          .attr("fill", "#a8a8cc")
          .attr("font-size", "8px")
          .attr("opacity", 0.65)
          .text(short);
      }
    });
  }

  function initChart() {
    const container = el("starmap");
    if (!container || !chartData) return;
    const W = container.clientWidth;
    const H = container.clientHeight;
    const CX = W / 2;
    const CY = H / 2;
    const R = Math.min(W, H);
    const R0 = 0;
    const R1 = R * 0.16;
    const R2 = R * 0.32;
    const R3 = R * 0.48;
    const R4 = R * 0.62;

    const svg = d3.select("#starmap").attr("width", W).attr("height", H);
    svg.selectAll("*").remove();

    const defs = svg.append("defs");
    const glow = defs
      .append("filter")
      .attr("id", "star-glow")
      .attr("x", "-80%")
      .attr("y", "-80%")
      .attr("width", "260%")
      .attr("height", "260%");
    glow.append("feGaussianBlur").attr("stdDeviation", "3.5").attr("result", "blur");
    const merge = glow.append("feMerge");
    merge.append("feMergeNode").attr("in", "blur");
    merge.append("feMergeNode").attr("in", "SourceGraphic");

    const zoom = d3.zoom().scaleExtent([0.08, 12]).on("zoom", (ev) => gRoot.attr("transform", ev.transform));
    svg.call(zoom);
    gRoot = svg.append("g");
    gCosmos = gRoot.append("g").attr("class", "cosmos-layer");

    const stars = d3.range(260).map(() => ({
      x: Math.random() * W,
      y: Math.random() * H,
      r: Math.random() * 1.1 + 0.15,
      o: Math.random() * 0.22 + 0.06,
    }));
    gRoot
      .append("g")
      .attr("class", "starfield")
      .selectAll("circle")
      .data(stars)
      .join("circle")
      .attr("cx", (d) => d.x)
      .attr("cy", (d) => d.y)
      .attr("r", (d) => d.r)
      .attr("fill", "#fff")
      .attr("opacity", (d) => d.o);

    let nodes = chartData.nodes.map((n) => ({ ...n, depth: layerForNode(n) }));
    nodes = nodes.filter(
      (n) => nodeMatchesConstellation(n, activeConstellation) && nodeMatchesGalaxy(n, activeGalaxy)
    );
    const idSet = new Set(nodes.map((n) => n.id));
    const links = (chartData.links || [])
      .filter((l) => idSet.has(l.source) && idSet.has(l.target))
      .map((l) => ({ ...l }));

    const idMap = new Map(nodes.map((n) => [n.id, n]));
    links.forEach((l) => {
      l.source = idMap.get(l.source);
      l.target = idMap.get(l.target);
    });

    const core = nodes.find((n) => n.id === "SEAL_000" || n.id === "GAB_SEAL_000");
    if (core) {
      core.fx = CX;
      core.fy = CY;
    }

    const gMap = galaxyMap();
    drawCosmosHalos(gCosmos, nodes, CX, CY, R);

    linkSel = gRoot
      .append("g")
      .attr("class", "link-layer")
      .attr("stroke-opacity", 0.38)
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("class", "chart-link")
      .attr("stroke", (d) => (d.kind === "gravity" ? "#5a4a7a" : "#00d8e8"))
      .attr("stroke-width", (d) => (d.kind === "gravity" ? 0.55 : 1.1))
      .attr("stroke-dasharray", (d) => (d.kind === "gravity" ? "5,7" : null))
      .attr("stroke-linecap", "round");

    nodeSel = gRoot
      .append("g")
      .selectAll("g")
      .data(nodes, (d) => d.id)
      .join("g")
      .attr("class", (d) => "star-node" + (selectedNodeId === d.id ? " selected" : ""))
      .style("cursor", "pointer")
      .on("click", (_, d) => showDetail(d))
      .on("mouseenter", (_, d) => {
        linkSel.classed("link-highlight", (l) => l.source.id === d.id || l.target.id === d.id);
        nodeSel.classed("hover", (n) => n.id === d.id);
      })
      .on("mouseleave", () => {
        linkSel.classed("link-highlight", false);
        nodeSel.classed("hover", false);
      })
      .call(
        d3
          .drag()
          .on("start", (ev, d) => {
            if (!ev.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (ev, d) => {
            d.fx = ev.x;
            d.fy = ev.y;
          })
          .on("end", (ev, d) => {
            if (!ev.active) simulation.alphaTarget(0);
            if (d.id !== "SEAL_000" && d.id !== "GAB_SEAL_000") {
              d.fx = null;
              d.fy = null;
            }
          })
      );

    function nodeFill(d) {
      const gcol = gMap.get((d.cosmos || {}).galaxy_id)?.color;
      if (parseSealId(d.id).isCore) return "#ffcc00";
      if (d.kind === "champion") return gcol || "#7d00ff";
      if (d.kind === "lattice") return "#00ff88";
      if (d.kind === "portal") return "#ff6600";
      if ((d.cosmos || {}).star_role === "agent_growth") return "#e94560";
      return gcol ? d3.color(gcol)?.brighter(0.5)?.formatHex?.() || "#00f0ff" : "#00f0ff";
    }

    function nodeRadius(d) {
      if (parseSealId(d.id).isCore) return 22;
      if (d.kind === "champion") return 14;
      if (d.kind === "lattice") return 8;
      return 10;
    }

    nodeSel
      .append("circle")
      .attr("class", "star-glow")
      .attr("r", (d) => nodeRadius(d) * 1.55)
      .attr("fill", (d) => nodeFill(d))
      .attr("opacity", (d) => (parseSealId(d.id).isCore ? 0.35 : 0.22))
      .attr("filter", "url(#star-glow)");

    nodeSel
      .append("circle")
      .attr("class", "star-core")
      .attr("r", nodeRadius)
      .attr("fill", nodeFill)
      .attr("stroke", (d) => (parseSealId(d.id).isCore ? "#fff8d0" : "#e8e8ff"))
      .attr("stroke-width", (d) => (parseSealId(d.id).isCore ? 1.2 : 0.65))
      .attr("stroke-opacity", 0.85);

    nodeSel
      .filter((d) => d.kind === "champion" && !parseSealId(d.id).isCore)
      .append("circle")
      .attr("class", "star-ring")
      .attr("r", (d) => nodeRadius(d) + 4)
      .attr("fill", "none")
      .attr("stroke", (d) => nodeFill(d))
      .attr("stroke-opacity", 0.45)
      .attr("stroke-width", 1);

    nodeSel
      .append("text")
      .attr("class", "star-glyph")
      .attr("dy", 4)
      .attr("text-anchor", "middle")
      .attr("fill", (d) => (parseSealId(d.id).isCore ? "#1a1200" : "#f0f0ff"))
      .attr("font-size", (d) => (parseSealId(d.id).isCore ? "17px" : "11px"))
      .attr("font-weight", (d) => (parseSealId(d.id).isCore ? "700" : "500"))
      .attr("pointer-events", "none")
      .text((d) => (d.glyph || "✦").split(" ")[0]);

    simulation = d3
      .forceSimulation(nodes)
      .force(
        "link",
        d3
          .forceLink(links)
          .id((d) => d.id)
          .distance((l) => (l.kind === "gravity" ? 220 : 90))
          .strength((l) => (l.kind === "gravity" ? 0.03 : 0.5))
      )
      .force("charge", d3.forceManyBody().strength(-120).distanceMax(400))
      .force(
        "radial",
        d3
          .forceRadial((d) => [R0, R1, R2, R3, R4][d.depth] || R2, CX, CY)
          .strength(0.12)
      )
      .force("center", d3.forceCenter(CX, CY))
      .force("collide", d3.forceCollide().radius(18).strength(0.6))
      .force("galaxy", (alpha) => {
        nodes.forEach((d) => {
          const gid = (d.cosmos || {}).galaxy_id;
          if (!gid || gid === "GALAXY_SINGULARITY") return;
          const g = gMap.get(gid);
          const angle = ((g?.angle_deg || 0) * Math.PI) / 180;
          const r = galaxyRadius(gid, R);
          const tx = CX + r * Math.cos(angle);
          const ty = CY + r * Math.sin(angle);
          d.vx += (tx - d.x) * alpha * 0.06;
          d.vy += (ty - d.y) * alpha * 0.06;
        });
      })
      .force("nebula", (alpha) => {
        const groups = d3.group(nodes, (d) => (d.cosmos || {}).nebula_id);
        groups.forEach((members) => {
          if (members.length < 2) return;
          const mx = d3.mean(members, (d) => d.x);
          const my = d3.mean(members, (d) => d.y);
          members.forEach((d) => {
            if (d.id === "SEAL_000" || d.id === "GAB_SEAL_000") return;
            d.vx += (mx - d.x) * alpha * 0.025;
            d.vy += (my - d.y) * alpha * 0.025;
          });
        });
      })
      .on("tick", () => {
        linkSel
          .attr("x1", (d) => d.source.x)
          .attr("y1", (d) => d.source.y)
          .attr("x2", (d) => d.target.x)
          .attr("y2", (d) => d.target.y);
        nodeSel.attr("transform", (d) => `translate(${d.x},${d.y})`);
        if (showCosmosLayers) drawCosmosHalos(gCosmos, nodes, CX, CY, R);
      });

    el("statNodes").textContent = String(nodes.length);
    el("statLinks").textContent = String(links.length);
    el("statSha").textContent = (chartData.registry_sha256 || "").slice(0, 12) + "…";
    el("statSync").textContent = chartData.generated_utc || "—";
    const cg = chartData.cosmos?.galaxy_count;
    if (el("statGalaxies") && cg != null) el("statGalaxies").textContent = String(cg);
    if (el("statNebulae") && chartData.cosmos?.nebula_count != null) {
      el("statNebulae").textContent = String(chartData.cosmos.nebula_count);
    }
  }

  function showDetail(d) {
    selectedNodeId = d.id;
    if (nodeSel) nodeSel.attr("class", (n) => "star-node" + (n.id === selectedNodeId ? " selected" : ""));
    el("detailTitle").textContent = d.name || d.id;
    el("detailId").textContent = d.id;
    el("detailEq").textContent = d.equation || "—";
    el("detailTone").textContent = d.tone || "—";
    el("detailTags").textContent = (d.tags || []).join(" · ") || "—";
    const urls = d.urls || {};
    const live = urls.live || urls.clawhub || urls.repo || d.url || "";
    const link = el("detailLink");
    if (live) {
      link.href = live;
      link.textContent = "Open anchor →";
      link.style.display = "inline";
    } else {
      link.style.display = "none";
    }
    el("detailKind").textContent = d.kind || "star";
    const c = d.cosmos || {};
    if (el("detailGalaxy")) el("detailGalaxy").textContent = c.galaxy_name || "—";
    if (el("detailNebula")) el("detailNebula").textContent = c.nebula_name || "—";
    if (el("detailCluster")) el("detailCluster").textContent = c.cluster_name || "—";
    if (el("detailStarRole")) el("detailStarRole").textContent = c.star_role || "—";
    const lin = d.lineage || {};
    if (el("detailLineage")) {
      if (!lin.lineage_root && lin.generation == null) {
        el("detailLineage").textContent = "—";
      } else {
        const parts = [];
        if (lin.public_mask) parts.push(lin.public_mask);
        if (lin.generation != null) parts.push(`gen ${lin.generation}`);
        if (lin.parent_public_id) parts.push(`← ${lin.parent_public_id}`);
        if (lin.relation) parts.push(lin.relation);
        el("detailLineage").textContent = parts.join(" · ") || (lin.lineage_root || "").slice(0, 16) + "…";
      }
    }
  }

  function populateGalaxyFilters() {
    const wrap = el("galaxyBtns");
    if (!wrap || !chartData?.cosmos?.galaxies) return;
    wrap.innerHTML = "";
    const allBtn = document.createElement("button");
    allBtn.type = "button";
    allBtn.setAttribute("data-galaxy", "all");
    allBtn.className = activeGalaxy === "all" ? "active" : "";
    allBtn.textContent = "All galaxies";
    wrap.appendChild(allBtn);
    chartData.cosmos.galaxies.forEach((g) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.setAttribute("data-galaxy", g.id);
      btn.className = activeGalaxy === g.id ? "active" : "";
      btn.title = g.description || g.name;
      btn.textContent = `${g.glyph || "◈"} ${g.name} (${g.star_count})`;
      wrap.appendChild(btn);
    });
    wrap.querySelectorAll("[data-galaxy]").forEach((btn) => {
      btn.addEventListener("click", () => {
        activeGalaxy = btn.getAttribute("data-galaxy") || "all";
        wrap.querySelectorAll("[data-galaxy]").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        initChart();
      });
    });
  }

  function bindUI() {
    el("zoomIn")?.addEventListener("click", () => {
      d3.select("#starmap").transition().call(d3.zoom().scaleBy, 1.25);
    });
    el("zoomOut")?.addEventListener("click", () => {
      d3.select("#starmap").transition().call(d3.zoom().scaleBy, 0.8);
    });
    el("resetZoom")?.addEventListener("click", () => {
      d3.select("#starmap").transition().call(d3.zoom().transform, d3.zoomIdentity);
    });
    el("btnResync")?.addEventListener("click", async () => {
      el("loadStatus").textContent = "Resyncing…";
      await loadData();
      populateGalaxyFilters();
      initChart();
      el("loadStatus").textContent = "LATTICE ALIGNED — chart live";
    });
    el("toggleCosmos")?.addEventListener("click", () => {
      showCosmosLayers = !showCosmosLayers;
      el("toggleCosmos").textContent = showCosmosLayers ? "Hide nebulae" : "Show nebulae";
      initChart();
    });
    document.querySelectorAll("[data-constellation]").forEach((btn) => {
      btn.addEventListener("click", () => {
        activeConstellation = btn.getAttribute("data-constellation") || "all";
        document.querySelectorAll("[data-constellation]").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        initChart();
      });
    });
  }

  async function boot() {
    el("loadStatus").textContent = "Loading constellation registry…";
    try {
      await loadData();
      bindUI();
      populateGalaxyFilters();
      initChart();
      if (chartData.nodes?.length) showDetail(chartData.nodes.find((n) => n.id === "SEAL_000") || chartData.nodes[0]);
      const sig = chartData.signature || "v2";
      el("loadStatus").textContent = `Live — ${chartData.node_count} stars · ${chartData.cosmos?.galaxy_count || "?"} galaxies (${sig})`;
    } catch (e) {
      el("loadStatus").textContent = "Sync failed — check data JSON";
      console.error(e);
    }
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();