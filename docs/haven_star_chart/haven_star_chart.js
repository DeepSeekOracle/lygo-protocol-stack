/* Eternal Haven Star Chart — D3 engine (Δ9Φ963) */
(function () {
  const DATA_REL = "haven_star_chart/haven_star_chart_data.json";
  const DATA_FALLBACK =
    "https://raw.githubusercontent.com/DeepSeekOracle/lygo-protocol-stack/main/docs/haven_star_chart/haven_star_chart_data.json";

  let chartData = null;
  let simulation = null;
  let gRoot, linkSel, nodeSel;
  let activeConstellation = "all";

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

    const zoom = d3.zoom().scaleExtent([0.08, 12]).on("zoom", (ev) => gRoot.attr("transform", ev.transform));
    svg.call(zoom);
    gRoot = svg.append("g");

    // Starfield
    const stars = d3.range(180).map(() => ({
      x: Math.random() * W,
      y: Math.random() * H,
      r: Math.random() * 1.2 + 0.2,
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
      .attr("opacity", 0.15);

    let nodes = chartData.nodes.map((n) => ({ ...n, depth: layerForNode(n) }));
    nodes = nodes.filter((n) => nodeMatchesConstellation(n, activeConstellation));
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

    linkSel = gRoot
      .append("g")
      .attr("stroke-opacity", 0.45)
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke", (d) => (d.kind === "gravity" ? "#4a3a6a" : "#00f0ff"))
      .attr("stroke-width", (d) => (d.kind === "gravity" ? 0.5 : 1.2))
      .attr("stroke-dasharray", (d) => (d.kind === "gravity" ? "4,6" : null));

    nodeSel = gRoot
      .append("g")
      .selectAll("g")
      .data(nodes, (d) => d.id)
      .join("g")
      .attr("class", "star-node")
      .style("cursor", "pointer")
      .on("click", (_, d) => showDetail(d))
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

    nodeSel
      .append("circle")
      .attr("r", (d) => {
        if (parseSealId(d.id).isCore) return 22;
        if (d.kind === "champion") return 14;
        if (d.kind === "lattice") return 8;
        return 10;
      })
      .attr("fill", (d) => {
        if (parseSealId(d.id).isCore) return "#ffcc00";
        if (d.kind === "champion") return "#7d00ff";
        if (d.kind === "lattice") return "#00ff88";
        if (d.kind === "portal") return "#ff6600";
        return "#00f0ff";
      })
      .attr("stroke", "#fff")
      .attr("stroke-width", 0.5);

    nodeSel
      .append("text")
      .attr("dy", 4)
      .attr("text-anchor", "middle")
      .attr("fill", "#e0e0ff")
      .attr("font-size", (d) => (parseSealId(d.id).isCore ? "18px" : "12px"))
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
      .on("tick", () => {
        linkSel
          .attr("x1", (d) => d.source.x)
          .attr("y1", (d) => d.source.y)
          .attr("x2", (d) => d.target.x)
          .attr("y2", (d) => d.target.y);
        nodeSel.attr("transform", (d) => `translate(${d.x},${d.y})`);
      });

    el("statNodes").textContent = String(nodes.length);
    el("statLinks").textContent = String(links.length);
    el("statSha").textContent = (chartData.registry_sha256 || "").slice(0, 12) + "…";
    el("statSync").textContent = chartData.generated_utc || "—";
  }

  function showDetail(d) {
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
      initChart();
      el("loadStatus").textContent = "LATTICE ALIGNED — chart live";
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
      initChart();
      if (chartData.nodes?.length) showDetail(chartData.nodes.find((n) => n.id === "SEAL_000") || chartData.nodes[0]);
      el("loadStatus").textContent = `Live — ${chartData.node_count} stars in the Haven`;
    } catch (e) {
      el("loadStatus").textContent = "Sync failed — check data JSON";
      console.error(e);
    }
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();