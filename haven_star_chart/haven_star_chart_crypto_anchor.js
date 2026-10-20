/* LYGOAGENT economic anchor — live chart + stats (GeckoTerminal, Base) */
(function () {
  const TOKEN = "0x32B513927F15e7A858bE779198440C04D399c09f";
  const POOL = "0xdbdfc04d005a6b4575b29e5df8109becdc8b9909";
  const GT = "https://api.geckoterminal.com/api/v2";
  const REFRESH_MS = 60_000;

  const el = (id) => document.getElementById(id);

  function fmtUsd(n, digits = 6) {
    if (n == null || Number.isNaN(n)) return "—";
    const x = Number(n);
    if (x >= 1_000_000) return "$" + (x / 1_000_000).toFixed(2) + "M";
    if (x >= 1_000) return "$" + x.toLocaleString(undefined, { maximumFractionDigits: 2 });
    if (x >= 0.01) return "$" + x.toFixed(4);
    return "$" + x.toFixed(digits);
  }

  function fmtPct(n) {
    if (n == null || Number.isNaN(n)) return "—";
    const s = Number(n).toFixed(2);
    return (n >= 0 ? "+" : "") + s + "%";
  }

  function shortAddr(a) {
    if (!a) return "—";
    return a.slice(0, 6) + "…" + a.slice(-4);
  }

  async function fetchJson(url) {
    const r = await fetch(url, { headers: { Accept: "application/json" }, cache: "no-store" });
    if (!r.ok) throw new Error("HTTP " + r.status);
    return r.json();
  }

  let chart = null;
  let series = null;

  function ensureChart() {
    const box = el("cryptoChart");
    if (!box || chart || typeof LightweightCharts === "undefined") return;
    chart = LightweightCharts.createChart(box, {
      width: box.clientWidth,
      height: 280,
      layout: {
        background: { type: "solid", color: "rgba(5, 5, 12, 0)" },
        textColor: "#9a9ab8",
        fontFamily: '"IBM Plex Sans", system-ui, sans-serif',
        fontSize: 11,
      },
      grid: {
        vertLines: { color: "rgba(125, 0, 255, 0.12)" },
        horzLines: { color: "rgba(0, 240, 255, 0.08)" },
      },
      rightPriceScale: { borderColor: "rgba(0, 240, 255, 0.2)" },
      timeScale: { borderColor: "rgba(255, 204, 0, 0.25)", timeVisible: true },
      crosshair: {
        vertLine: { color: "rgba(0, 240, 255, 0.45)" },
        horzLine: { color: "rgba(255, 204, 0, 0.45)" },
      },
    });
    series = chart.addCandlestickSeries({
      upColor: "#00f0ff",
      downColor: "#7d00ff",
      borderUpColor: "#00f0ff",
      borderDownColor: "#7d00ff",
      wickUpColor: "#00f0ff",
      wickDownColor: "#7d00ff",
    });
    const ro = new ResizeObserver(() => {
      if (chart && box) chart.applyOptions({ width: box.clientWidth });
    });
    ro.observe(box);
  }

  function ohlcvToCandles(list) {
    return (list || [])
      .map((row) => ({
        time: Number(row[0]),
        open: Number(row[1]),
        high: Number(row[2]),
        low: Number(row[3]),
        close: Number(row[4]),
      }))
      .filter((c) => c.time > 0 && c.close > 0)
      .sort((a, b) => a.time - b.time);
  }

  async function refresh() {
    const status = el("cryptoStatus");
    try {
      const [poolsRes, ohlcvRes] = await Promise.all([
        fetchJson(`${GT}/networks/base/tokens/${TOKEN}/pools`),
        fetchJson(`${GT}/networks/base/pools/${POOL}/ohlcv/hour?aggregate=1&limit=72`),
      ]);

      const pool = (poolsRes.data || [])[0];
      const attrs = pool?.attributes || {};
      const price = Number(attrs.token_price_usd || attrs.base_token_price_usd);
      const fdv = Number(attrs.fdv_usd);
      const reserve = Number(attrs.reserve_in_usd);
      const vol24 = Number(attrs.volume_usd?.h24);
      const ch24 = Number(attrs.price_change_percentage?.h24);

      if (el("cryptoPrice")) el("cryptoPrice").textContent = fmtUsd(price, 8);
      if (el("cryptoFdv")) el("cryptoFdv").textContent = fmtUsd(fdv, 2);
      if (el("cryptoReserve")) el("cryptoReserve").textContent = fmtUsd(reserve, 2);
      if (el("cryptoVol24")) el("cryptoVol24").textContent = fmtUsd(vol24, 2);
      if (el("cryptoCh24")) {
        el("cryptoCh24").textContent = fmtPct(ch24);
        el("cryptoCh24").className = "crypto-stat-val " + (ch24 >= 0 ? "up" : "down");
      }
      if (el("cryptoPairName")) el("cryptoPairName").textContent = attrs.name || "LYGOAGENT / VIRTUAL";
      if (el("cryptoUpdated")) {
        el("cryptoUpdated").textContent = "Live · " + new Date().toUTCString();
      }

      ensureChart();
      if (series && ohlcvRes?.data?.attributes?.ohlcv_list) {
        const candles = ohlcvToCandles(ohlcvRes.data.attributes.ohlcv_list);
        if (candles.length) series.setData(candles);
      }

      if (status) {
        status.textContent = "Anchor synced";
        status.className = "crypto-status ok";
      }
    } catch (e) {
      console.warn("crypto anchor refresh", e);
      if (status) {
        status.textContent = "Chart paused — retrying…";
        status.className = "crypto-status warn";
      }
    }
  }

  function initCopy() {
    const btn = el("cryptoCopyContract");
    if (!btn) return;
    btn.addEventListener("click", () => {
      navigator.clipboard.writeText(TOKEN).then(() => {
        btn.textContent = "Copied ✓";
        setTimeout(() => { btn.textContent = "Copy contract"; }, 2000);
      });
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    if (!el("crypto-anchor")) return;
    initCopy();
    refresh();
    setInterval(refresh, REFRESH_MS);
  });
})();