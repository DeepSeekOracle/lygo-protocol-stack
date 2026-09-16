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
  const PROVIDERS = {
    lygo: { label: "On-page LYGO steward (works now)", kind: "local", url: "", model: "lygo-steward", key: false, help: "No key. Built into this page." },
    hosted: { label: "LYGO stream PC (qwen2.5:3b)", kind: "openai", url: "", model: "qwen2.5:3b", key: false, help: "Our always-on node. On the home LAN open http://10.0.0.209:8080/portal/" },
    groq: { label: "Groq (free tier)", kind: "openai", url: "https://api.groq.com/openai/v1/chat/completions", model: "llama-3.1-8b-instant", key: true, help: "console.groq.com → API keys" },
    openrouter: { label: "OpenRouter (many models)", kind: "openai", url: "https://openrouter.ai/api/v1/chat/completions", model: "openai/gpt-4o-mini", key: true, help: "openrouter.ai/keys", extra: { "HTTP-Referer": "https://chatagent.ca/portal/", "X-Title": "LYGO LLM Portal" } },
    openai: { label: "OpenAI", kind: "openai", url: "https://api.openai.com/v1/chat/completions", model: "gpt-4o-mini", key: true, help: "platform.openai.com/api-keys" },
    xai: { label: "xAI Grok", kind: "openai", url: "https://api.x.ai/v1/chat/completions", model: "grok-4-fast-non-reasoning", key: true, help: "console.x.ai" },
    deepseek: { label: "DeepSeek", kind: "openai", url: "https://api.deepseek.com/v1/chat/completions", model: "deepseek-chat", key: true, help: "platform.deepseek.com" },
    mistral: { label: "Mistral", kind: "openai", url: "https://api.mistral.ai/v1/chat/completions", model: "mistral-small-latest", key: true, help: "console.mistral.ai" },
    together: { label: "Together AI", kind: "openai", url: "https://api.together.xyz/v1/chat/completions", model: "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", key: true, help: "api.together.xyz" },
    fireworks: { label: "Fireworks", kind: "openai", url: "https://api.fireworks.ai/inference/v1/chat/completions", model: "accounts/fireworks/models/llama-v3p1-8b-instruct", key: true, help: "fireworks.ai" },
    gemini: { label: "Google Gemini (OpenAI-compat)", kind: "openai", url: "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", model: "gemini-2.0-flash", key: true, help: "aistudio.google.com/apikey" },
    anthropic: { label: "Anthropic Claude", kind: "anthropic", url: "https://api.anthropic.com/v1/messages", model: "claude-3-5-haiku-latest", key: true, help: "console.anthropic.com" },
    huggingface: { label: "Hugging Face router", kind: "openai", url: "https://router.huggingface.co/v1/chat/completions", model: "Qwen/Qwen2.5-1.5B-Instruct", key: true, help: "huggingface.co/settings/tokens" },
    ollama: { label: "Local Ollama :11434", kind: "ollama", url: "http://127.0.0.1:11434/api/chat", model: "qwen2.5:3b", key: false, help: "Run ollama serve. HTTPS pages often block localhost." },
    lygo_console: { label: "Local LYGO console :9641", kind: "console", url: "http://127.0.0.1:9641/api/chat", model: "qwen2.5:3b", key: false, help: "Run LYGO_LLM_CONSOLE.bat. Full limbs stay local." },
    custom: { label: "Custom OpenAI-compatible URL", kind: "openai", url: "", model: "", key: true, help: "Paste base or …/v1/chat/completions" },
  };

  const cfg = { hosted_base: "" };
  const log = document.getElementById("log");
  const healthEl = document.getElementById("health");
  const limb = document.getElementById("limb-out");
  const msg = document.getElementById("msg");
  const modeEl = document.getElementById("mode");
  const endpointEl = document.getElementById("endpoint");
  const tokenEl = document.getElementById("hf-token") || document.getElementById("api-key");
  const modelEl = document.getElementById("model");
  let history = [];

  function bubble(role, text) {
    const d = document.createElement("div");
    d.className = "bubble " + role;
    d.textContent = text;
    log.appendChild(d);
    log.scrollTop = log.scrollHeight;
  }
  function setHealth(t) {
    if (healthEl) healthEl.textContent = t;
  }
  function provider() {
    return PROVIDERS[modeEl.value] || PROVIDERS.lygo;
  }
  function fillProvider() {
    const p = provider();
    if (modelEl && (p.model || modeEl.value !== "custom")) modelEl.value = p.model || modelEl.value;
    if (endpointEl) endpointEl.value = p.url || endpointEl.value;
    if (tokenEl) {
      tokenEl.style.display = p.key ? "" : "none";
      tokenEl.placeholder = p.key ? "API key stays in this browser" : "";
    }
    const help = document.getElementById("mode-help");
    if (help) help.innerHTML = p.help + ' · <a href="/guides/how-to-lygo-llm-portal.html">How to hook an LLM</a>';
    setHealth("provider=" + modeEl.value + (p.model ? " · " + p.model : ""));
  }

  function systemPrompt(invoked) {
    let s = "You are the public LYGO LLM portal. Assist; never replace the human. Dual ledgers/Star Chart=CANON. This chat=RESOURCE. No passwords, no OS wipe.";
    if (invoked) s += " The operator invoked champion " + invoked + ". Use Observed/Inferred/Unknown.";
    return s;
  }

  function invokedOf(text) {
    const u = (text || "").toUpperCase();
    return CHAMPS.find(function (c) {
      return u.indexOf(c[0].toUpperCase()) >= 0 || text.indexOf(c[0]) >= 0;
    });
  }

  async function wiki(q) {
    const u = "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=" + encodeURIComponent(q) + "&format=json&origin=*";
    const r = await fetch(u);
    const j = await r.json();
    return ((j.query && j.query.search) || []).slice(0, 5).map(function (x) {
      return x.title + " — " + (x.snippet || "").replace(/<[^>]+>/g, "");
    });
  }

  async function lygoSteward(text) {
    const low = text.toLowerCase();
    const ch = invokedOf(text);
    if (ch) {
      return (
        ch[0] + " (on-page steward, RESOURCE)\n\nObserved: you invoked this Δ9 seat — " + ch[1] + ".\nInferred: use this lens on your task; do not treat myth as authority.\nUnknown: I am not a hosted 7B model until you connect a provider.\n\nNext: paste your goal + constraints. Directory: https://chatagent.ca/champions.html\nHow to hook a real LLM: https://chatagent.ca/guides/how-to-lygo-llm-portal.html"
      );
    }
    if (/\b(weather|forecast)\b/.test(low)) {
      try {
        const t = await (await fetch("https://wttr.in/?format=3")).text();
        return t + "\n\nRESOURCE. Connect Groq/OpenAI/local for a fuller model.";
      } catch (e) {
        return "Weather fetch failed: " + e;
      }
    }
    if (/\b(wiki|what is|who is|look up)\b/.test(low) || /\?$/.test(text)) {
      try {
        const hits = await wiki(text);
        if (hits.length) return "Wikipedia (RESOURCE):\n" + hits.join("\n") + "\n\nFor a real LLM, pick Groq (free key) or local console. Guide: /guides/how-to-lygo-llm-portal.html";
      } catch (_) {}
    }
    if (/\b(connect|api|groq|openai|ollama|hook|key|provider)\b/.test(low)) {
      return "Hook-up in 3 steps:\n1) Provider dropdown (Groq is the usual free start).\n2) Paste the API key — it never leaves this browser.\n3) Connect, then chat.\n\nLocal full limbs: run LYGO_LLM_CONSOLE.bat and choose Local LYGO console. HTTPS sites often cannot reach 127.0.0.1 — use the local window.\nGuide: https://chatagent.ca/guides/how-to-lygo-llm-portal.html";
    }
    return (
      "On-page LYGO steward (always on). I can: Δ9 champion frames, Wikipedia, weather, and hook-up help. I am not a large hosted model.\n\nTo talk to Groq / OpenAI / Claude / Grok / Ollama / your console: pick a provider above, paste a key if needed, Connect.\n\nYou said: “" +
      text.slice(0, 240) +
      "”\n\nGuide: https://chatagent.ca/guides/how-to-lygo-llm-portal.html · Donate: https://www.paypal.com/paypalme/ExcavationPro"
    );
  }

  function openaiUrl() {
    const p = provider();
    let e = (endpointEl.value || p.url || "").replace(/\/$/, "");
    if (!e) return "";
    if (p.kind === "ollama") {
      if (e.indexOf("/api/chat") >= 0 || e.indexOf("/v1/") >= 0) return e;
      return e + "/api/chat";
    }
    if (p.kind === "console") return e.indexOf("/api/") >= 0 ? e : e + "/api/chat";
    if (p.kind === "anthropic") return e;
    if (e.indexOf("/chat") >= 0 || e.indexOf("/v1/") >= 0 || e.indexOf("/messages") >= 0) return e;
    return e + "/v1/chat/completions";
  }

  async function callRemote(text) {
    const p = provider();
    const url = openaiUrl();
    const model = modelEl.value || p.model;
    const key = (tokenEl && tokenEl.value) || "";
    const invoked = invokedOf(text);
    const msgs = [{ role: "system", content: systemPrompt(invoked && invoked[0]) }].concat(history.slice(-8));
    const headers = { "Content-Type": "application/json" };
    if (key) {
      if (p.kind === "anthropic") {
        headers["x-api-key"] = key;
        headers["anthropic-version"] = "2023-06-01";
      } else headers.Authorization = "Bearer " + key;
    }
    if (p.extra) Object.keys(p.extra).forEach(function (k) { headers[k] = p.extra[k]; });

    let payload;
    if (p.kind === "anthropic") {
      payload = { model: model, max_tokens: 512, system: msgs[0].content, messages: msgs.slice(1).filter(function (m) { return m.role !== "system"; }) };
    } else if (p.kind === "ollama") {
      payload = { model: model, messages: msgs, stream: false };
    } else {
      payload = { model: model, messages: msgs, max_tokens: 512, stream: false };
    }

    const r = await fetch(url, { method: "POST", headers: headers, body: JSON.stringify(payload) });
    const j = await r.json().catch(function () { return {}; });
    let out =
      j.text ||
      (j.message && j.message.content) ||
      (((j.choices || [])[0] || {}).message || {}).content ||
      ((((j.content || [])[0] || {}).text)) ||
      (typeof j.error === "string" ? j.error : (j.error && (j.error.message || JSON.stringify(j.error)))) ||
      ("http " + r.status);
    if (typeof out !== "string") out = JSON.stringify(out);
    limb.textContent = JSON.stringify({ status: r.status, provider: modeEl.value, model: model }, null, 2);
    if (!r.ok && r.status) out = "Provider error " + r.status + ": " + out;
    return out;
  }

  function corsHint() {
    return "This provider likely blocks browser CORS. Fixes: (1) Groq/OpenRouter sometimes work from a page — try another key. (2) Run local LYGO console or Ollama and pick that provider. (3) Paste a CORS-open custom URL. Guide: /guides/how-to-lygo-llm-portal.html";
  }

  async function findHosted() {
    const tries = [];
    if (cfg.hosted_base) tries.push(String(cfg.hosted_base).replace(/\/$/, ""));
    if (location.protocol === "http:" && location.hostname && location.hostname !== "chatagent.ca") {
      tries.push(location.origin.replace(/\/$/, "") + "/llm");
    }
    tries.push("http://10.0.0.209:8080/llm");
    for (let i = 0; i < tries.length; i++) {
      const b = tries[i];
      if (!b) continue;
      try {
        const r = await fetch(b + "/health", { mode: "cors", cache: "no-store" });
        if (r.ok) return b;
      } catch (_) {}
    }
    return "";
  }

  document.getElementById("connect").onclick = function () {
    fillProvider();
    const p = provider();
    if (p.key && !(tokenEl && tokenEl.value)) {
      setHealth("paste an API key (this browser only) — see " + p.help);
      return;
    }
    if (p.kind !== "local" && !openaiUrl() && modeEl.value !== "lygo") {
      setHealth("paste an endpoint URL");
      return;
    }
    try {
      sessionStorage.setItem("lygo_portal_provider", modeEl.value);
      sessionStorage.setItem("lygo_portal_model", modelEl.value || "");
    } catch (_) {}
    setHealth("ready · " + p.label);
    bubble("assistant", "Connected: " + p.label + (p.kind === "local" ? " (on-page, no key)." : " Keys stay in this tab."));
  };

  if (modeEl) {
    Object.keys(PROVIDERS).forEach(function (id) {
      if ([].some.call(modeEl.options, function (o) { return o.value === id; })) return;
      const o = document.createElement("option");
      o.value = id;
      o.textContent = PROVIDERS[id].label;
      modeEl.appendChild(o);
    });
    try {
      const saved = sessionStorage.getItem("lygo_portal_provider");
      if (saved && PROVIDERS[saved]) modeEl.value = saved;
      else modeEl.value = "lygo";
      const sm = sessionStorage.getItem("lygo_portal_model");
      if (sm && modelEl) modelEl.value = sm;
    } catch (_) {
      modeEl.value = "lygo";
    }
    modeEl.onchange = fillProvider;
    fillProvider();
  }

  fetch("portal.json", { cache: "no-store" })
    .then(function (r) { return r.json(); })
    .then(function (j) { Object.assign(cfg, j); })
    .catch(function () {})
    .then(function () { return findHosted(); })
    .then(function (base) {
      if (base) {
        cfg.hosted_base = base;
        PROVIDERS.hosted.url = base.replace(/\/$/, "") + "/v1/chat/completions";
        if (modeEl && (modeEl.value === "lygo" || !modeEl.value)) {
          modeEl.value = "hosted";
          fillProvider();
        }
        setHealth("stream PC model online · qwen2.5:3b · " + base);
        bubble("assistant", "Live backend: stream PC qwen2.5:3b at " + base + "\nChat should work now. Stronger models: pick Groq/OpenAI/etc and paste a key.\nHow-to: https://chatagent.ca/guides/how-to-lygo-llm-portal.html");
      } else {
        setHealth("no public GPU from here · on-page steward ready · hook Groq for a real LLM");
      }
    });

  const box = document.getElementById("champs");
  if (box) {
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
  }

  document.querySelectorAll("[data-limb]").forEach(function (b) {
    b.onclick = async function () {
      const n = b.getAttribute("data-limb");
      if (n === "wiki") {
        const hits = await wiki(msg.value || "LYGO");
        limb.textContent = hits.join("\n");
        bubble("assistant", "Wikipedia (RESOURCE):\n" + hits.join("\n"));
      } else if (n === "weather") {
        const t = await (await fetch("https://wttr.in/?format=3")).text();
        bubble("assistant", t);
      } else if (n === "skillhub") window.open("https://chatagent.ca/lygoskillhub.html", "_blank", "noopener");
      else if (n === "howto") window.open("/guides/how-to-lygo-llm-portal.html", "_blank", "noopener");
    };
  });

  const npBody = document.getElementById("np-body");
  const npSt = document.getElementById("np-status");
  if (npBody) {
    try { npBody.value = localStorage.getItem("lygo_public_notepad") || ""; } catch (_) {}
  }
  const npSave = document.getElementById("np-save");
  if (npSave) {
    npSave.onclick = function () {
      try {
        localStorage.setItem("lygo_public_notepad", npBody.value || "");
        npSt.textContent = "saved in browser";
      } catch (_) { npSt.textContent = "blocked"; }
    };
  }

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
    let out;
    try {
      if (provider().kind === "local") out = await lygoSteward(text);
      else out = await callRemote(text);
    } catch (e) {
      out = corsHint() + "\n\n" + String(e);
    }
    if (P0.test(out || "")) out = "[output quarantined]";
    history.push({ role: "assistant", content: out });
    bubble("assistant", out);
  };

  bubble(
    "assistant",
    "LYGO portal is live. You are talking to the on-page steward until you hook a model.\n\nFastest LLM: Provider → Groq (free tier) → paste key → Connect.\nLocal full limbs: LYGO_LLM_CONSOLE.bat → provider “Local LYGO console”.\nHow-to: https://chatagent.ca/guides/how-to-lygo-llm-portal.html"
  );

  const worldLocal = document.getElementById("world-local");
  const worldUtc = document.getElementById("world-utc");
  function paintWorld() {
    const now = new Date();
    if (worldLocal) worldLocal.textContent = now.toLocaleString(undefined, { weekday: "short", hour: "2-digit", minute: "2-digit", second: "2-digit" });
    if (worldUtc) worldUtc.textContent = "UTC " + now.toISOString().slice(0, 19).replace("T", " ");
  }
  paintWorld();
  setInterval(paintWorld, 1000);
  document.querySelectorAll(".y").forEach(function (el) {
    el.textContent = String(new Date().getFullYear());
  });
})();
