(function () {
  const CHAMPS = [
    ["LYRΔ", "memory and continuity"],
    ["Δ9RA", "challenge and risk"],
    ["ΣRΛΘ", "what is omitted"],
    ["ARKOS", "structure and blueprint"],
    ["KAIROS", "order and timing"],
    ["ÆTHERIS", "claim vs evidence"],
    ["ΣCENΔR", "two live scenarios"],
    ["SANCORA", "shared vocabulary"],
    ["SEPHRAEL", "echoes and fragile notes"],
    ["OMNIΣIREN", "fewer words"],
    ["Lightfather", "provenance and consent"],
    ["VΩLARIS", "tradeoffs in the open"],
    ["ZETAΔ9", "edge cases"],
    ["JUSTICAE", "who is affected"],
    ["ΣEIDŌN", "surface vs depth"],
  ];
  const P0 = /format\s+c:|\bdiskpart\b|\bbcdedit\b|rm\s+-rf\s+\/|invoke-expression/i;
  const cfg = { hosted_base: "", hosted_model: "qwen2.5:3b", hf_router: "https://router.huggingface.co/v1/chat/completions", hf_model: "Qwen/Qwen2.5-1.5B-Instruct", local_console: "http://127.0.0.1:9641" };
  const log = document.getElementById("log");
  const healthEl = document.getElementById("health");
  const limb = document.getElementById("limb-out");
  const msg = document.getElementById("msg");
  const modeEl = document.getElementById("mode");
  const endpointEl = document.getElementById("endpoint");
  const tokenEl = document.getElementById("hf-token");
  const modelEl = document.getElementById("model");
  let history = [];
  let full = false;

  fetch("portal.json", { cache: "no-store" }).then((r) => r.json()).then((j) => Object.assign(cfg, j)).catch(() => {});

  function bubble(role, text) {
    const d = document.createElement("div");
    d.className = "bubble " + role;
    d.textContent = text;
    log.appendChild(d);
    log.scrollTop = log.scrollHeight;
  }
  function setHealth(t) { healthEl.textContent = t; }

  function isLoopback(url) {
    try {
      const u = new URL(url, location.href);
      return ["127.0.0.1", "localhost", "::1"].indexOf(u.hostname) >= 0;
    } catch (_) { return false; }
  }

  function chatUrl() {
    const mode = modeEl.value;
    if (mode === "hosted") {
      const base = (endpointEl.value || cfg.hosted_base || "").replace(/\/$/, "");
      if (!base) return "";
      if (base.endsWith("/v1/chat/completions")) return base;
      if (base.endsWith("/api/chat")) return base;
      return base + "/v1/chat/completions";
    }
    if (mode === "hf") return cfg.hf_router;
    if (mode === "local") return (cfg.local_console || "http://127.0.0.1:9641").replace(/\/$/, "") + "/api/chat";
    const e = (endpointEl.value || "").replace(/\/$/, "");
    if (!e) return "";
    if (e.indexOf("/chat") >= 0 || e.indexOf("/v1/") >= 0) return e;
    return e + "/v1/chat/completions";
  }

  function systemPrompt(invoked) {
    let s = "You are the public LYGO LLM portal. Assist; never replace the human. Dual ledgers/Star Chart=CANON. This chat=RESOURCE. No passwords, no OS wipe.";
    if (invoked) s += " The operator invoked champion " + invoked + ". Use Observed/Inferred/Unknown.";
    return s;
  }

  async function connect() {
    const mode = modeEl.value;
    full = !!(document.getElementById("full") && document.getElementById("full").checked);
    document.body.classList.toggle("public-mode", !(mode === "local" && full && isLoopback(cfg.local_console)));
    const url = chatUrl();
    if (mode === "hosted" && !url) {
      setHealth("hosted URL not published yet — use Hugging Face or local console");
      limb.textContent = "Set portal.json hosted_base on the stream node / Caddy, or pick another mode.";
      return;
    }
    if (mode === "hf" && !tokenEl.value) {
      setHealth("paste a Hugging Face token (browser-only)");
      return;
    }
    if (mode === "local") {
      try {
        const r = await fetch((cfg.local_console || "http://127.0.0.1:9641") + "/api/health", { cache: "no-store" });
        const j = await r.json();
        setHealth("local console brain=" + (j.brain || "?") + " full=" + (full && j.ok));
        limb.textContent = JSON.stringify({ ok: j.ok, build: j.build, tools: full }, null, 2);
        return;
      } catch (e) {
        setHealth("cannot reach 127.0.0.1:9641 (HTTPS pages often block it) — open the local BAT instead");
        limb.textContent = String(e);
        return;
      }
    }
    setHealth("mode=" + mode + " model=" + (modelEl.value || cfg.hosted_model));
    limb.textContent = "connected · public limbs only unless local+full";
  }

  async function wiki(q) {
    const u = "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=" + encodeURIComponent(q) + "&format=json&origin=*";
    const r = await fetch(u);
    const j = await r.json();
    return (j.query && j.query.search || []).slice(0, 5).map((x) => x.title + " — " + (x.snippet || "").replace(/<[^>]+>/g, ""));
  }

  document.getElementById("connect").onclick = connect;
  modeEl.onchange = function () {
    tokenEl.style.display = modeEl.value === "hf" ? "" : "none";
    if (modeEl.value === "local") endpointEl.value = cfg.local_console;
    if (modeEl.value === "hf") modelEl.value = cfg.hf_model;
    if (modeEl.value === "hosted") modelEl.value = cfg.hosted_model;
  };
  tokenEl.style.display = "none";
  modeEl.onchange();

  const box = document.getElementById("champs");
  CHAMPS.forEach(function (c) {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = c[0];
    b.title = c[1];
    b.onclick = function () {
      msg.value = "Invoke " + c[0] + " — " + c[1] + ". Observed / Inferred / Unknown.";
      msg.focus();
    };
    box.appendChild(b);
  });

  document.querySelectorAll("[data-limb]").forEach(function (b) {
    b.onclick = async function () {
      const n = b.getAttribute("data-limb");
      if (n === "wiki") {
        const q = msg.value || "LYGO";
        const hits = await wiki(q);
        limb.textContent = hits.join("\n");
        bubble("assistant", "Wikipedia (RESOURCE):\n" + hits.join("\n"));
      } else if (n === "weather") {
        const r = await fetch("https://wttr.in/?format=3");
        const t = await r.text();
        limb.textContent = t;
        bubble("assistant", t);
      } else if (n === "skillhub") {
        window.open("https://chatagent.ca/lygoskillhub.html", "_blank", "noopener");
      }
    };
  });

  const npBody = document.getElementById("np-body");
  const npSt = document.getElementById("np-status");
  try { npBody.value = localStorage.getItem("lygo_public_notepad") || ""; } catch (_) {}
  document.getElementById("np-save").onclick = function () {
    try {
      localStorage.setItem("lygo_public_notepad", npBody.value || "");
      npSt.textContent = "saved in browser";
    } catch (_) { npSt.textContent = "blocked"; }
  };

  document.getElementById("form").onsubmit = async function (ev) {
    ev.preventDefault();
    const text = (msg.value || "").trim();
    if (!text) return;
    if (P0.test(text)) {
      bubble("assistant", "P0 blocked that prompt.");
      return;
    }
    msg.value = "";
    bubble("user", text);
    history.push({ role: "user", content: text });
    const url = chatUrl();
    if (!url) {
      bubble("assistant", "No backend yet. Connect Hugging Face (token stays in this browser), run LYGO_LLM_CONSOLE.bat, or wait for the hosted stream URL in portal.json.");
      return;
    }
    const invoked = CHAMPS.map((c) => c[0]).find((n) => text.toUpperCase().indexOf(n.replace("Δ", "D")) >= 0 || text.indexOf(n) >= 0);
    const payload = {
      model: modelEl.value || cfg.hosted_model,
      messages: [{ role: "system", content: systemPrompt(invoked) }].concat(history.slice(-8)),
      max_tokens: 384,
      stream: false,
    };
    const headers = { "Content-Type": "application/json" };
    if (modeEl.value === "hf" && tokenEl.value) headers.Authorization = "Bearer " + tokenEl.value;
    try {
      const r = await fetch(url, { method: "POST", headers: headers, body: JSON.stringify(payload) });
      const j = await r.json().catch(() => ({}));
      let out = j.text || (((j.choices || [])[0] || {}).message || {}).content || j.error || ("http " + r.status);
      if (typeof out !== "string") out = JSON.stringify(out);
      if (P0.test(out)) out = "[output quarantined]";
      history.push({ role: "assistant", content: out });
      bubble("assistant", out);
      limb.textContent = JSON.stringify({ status: r.status, public: true, full: full }, null, 2);
    } catch (e) {
      bubble("assistant", "Could not reach backend. HTTPS pages cannot always call http://127.0.0.1 — use the local console window, Hugging Face, or a HTTPS gateway.");
      limb.textContent = String(e);
    }
  };

  const worldLocal = document.getElementById("world-local");
  const worldUtc = document.getElementById("world-utc");
  function paintWorld() {
    const now = new Date();
    worldLocal.textContent = now.toLocaleString(undefined, { weekday: "short", hour: "2-digit", minute: "2-digit", second: "2-digit" });
    worldUtc.textContent = "UTC " + now.toISOString().slice(0, 19).replace("T", " ");
  }
  paintWorld();
  setInterval(paintWorld, 1000);
})();
