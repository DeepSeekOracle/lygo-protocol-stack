(function () {
  const CHAMPS = {
    LYRA: "Memory, song, continuity of theme. Observed / Inferred / Unknown.",
    "Δ9RA": "Boundary vigilance. List risks and what would break first.",
    "ΣRΛΘ": "Shadow sentinel. What is omitted or failing silently?",
    ARKOS: "Ethical Reality Architect. Intent, constraints, blueprint, failure, receipts.",
    KAIROS: "Timing. Ordered steps with why this order.",
    "ÆTHERIS": "Claim vs evidence. RESOURCE vs CANON.",
    "ΣCENΔR": "At least two live scenarios and what would falsify each.",
    SANCORA: "Shared vocabulary and handoff. Not medical advice.",
    SEPHRAEL: "Echoes, fragile items, archive vs discard. No secrets in notes.",
    "OMNIΣIREN": "Constraints only, then the next irreversible-safe step.",
    Lightfather: "Provenance and consent. Never claim to be the human operator.",
    "VΩLARIS": "Criteria, scores, tradeoffs, recommendation.",
    "ZETAΔ9": "Weird inputs and boundary tests. Do not break production.",
    JUSTICAE: "Affected parties, disclosure, consent. No doxxing.",
    "ΣEIDŌN": "Surface vs depth. Witness, do not flatten a long project.",
  };
  const P0 = /format\s+c:|\bdiskpart\b|\bbcdedit\b|rm\s+-rf\s+\/|invoke-expression/i;
  const PROVIDERS = {
    groq: { label: "Groq (free, no card)", kind: "openai", url: "https://api.groq.com/openai/v1/chat/completions", model: "llama-3.1-8b-instant", key: true, help: "console.groq.com/keys" },
    gemini: { label: "Google Gemini (free, no card)", kind: "openai", url: "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", model: "gemini-2.0-flash", key: true, help: "aistudio.google.com/apikey" },
    openrouter: { label: "OpenRouter (many :free models)", kind: "openai", url: "https://openrouter.ai/api/v1/chat/completions", model: "openrouter/auto", key: true, help: "openrouter.ai/keys — use model ids ending :free", extra: { "HTTP-Referer": "https://chatagent.ca/portal/", "X-Title": "LYGO API Portal" } },
    cerebras: { label: "Cerebras (fast, free/trial)", kind: "openai", url: "https://api.cerebras.ai/v1/chat/completions", model: "llama3.1-8b", key: true, help: "cloud.cerebras.ai" },
    huggingface: { label: "Hugging Face router", kind: "openai", url: "https://router.huggingface.co/v1/chat/completions", model: "Qwen/Qwen2.5-1.5B-Instruct", key: true, help: "huggingface.co/settings/tokens" },
    mistral: { label: "Mistral (free / cheap)", kind: "openai", url: "https://api.mistral.ai/v1/chat/completions", model: "mistral-small-latest", key: true, help: "console.mistral.ai" },
    nvidia: { label: "NVIDIA NIM (free catalog)", kind: "openai", url: "https://integrate.api.nvidia.com/v1/chat/completions", model: "meta/llama-3.1-8b-instruct", key: true, help: "build.nvidia.com" },
    cohere: { label: "Cohere (trial)", kind: "openai", url: "https://api.cohere.ai/compatibility/v1/chat/completions", model: "command-r-plus", key: true, help: "dashboard.cohere.com/api-keys" },
    sambanova: { label: "SambaNova Cloud", kind: "openai", url: "https://api.sambanova.ai/v1/chat/completions", model: "Meta-Llama-3.1-8B-Instruct", key: true, help: "cloud.sambanova.ai" },
    llm7: { label: "LLM7.io (free)", kind: "openai", url: "https://api.llm7.io/v1/chat/completions", model: "gpt-4o-mini-2024-07-18", key: true, help: "llm7.io — key optional on some models" },
    zai: { label: "Z.ai / Zhipu GLM", kind: "openai", url: "https://api.z.ai/api/paas/v4/chat/completions", model: "glm-4.5-flash", key: true, help: "z.ai / open.bigmodel.cn" },
    deepinfra: { label: "DeepInfra", kind: "openai", url: "https://api.deepinfra.com/v1/openai/chat/completions", model: "meta-llama/Meta-Llama-3.1-8B-Instruct", key: true, help: "deepinfra.com" },
    hyperbolic: { label: "Hyperbolic", kind: "openai", url: "https://api.hyperbolic.xyz/v1/chat/completions", model: "meta-llama/Meta-Llama-3.1-8B-Instruct", key: true, help: "app.hyperbolic.xyz" },
    novita: { label: "Novita", kind: "openai", url: "https://api.novita.ai/v3/openai/chat/completions", model: "meta-llama/llama-3.1-8b-instruct", key: true, help: "novita.ai" },
    siliconflow: { label: "SiliconFlow", kind: "openai", url: "https://api.siliconflow.cn/v1/chat/completions", model: "Qwen/Qwen2.5-7B-Instruct", key: true, help: "siliconflow.cn / siliconflow.com" },
    openai: { label: "OpenAI (paid)", kind: "openai", url: "https://api.openai.com/v1/chat/completions", model: "gpt-4o-mini", key: true, help: "platform.openai.com/api-keys" },
    xai: { label: "xAI Grok (credits)", kind: "openai", url: "https://api.x.ai/v1/chat/completions", model: "grok-4-fast-non-reasoning", key: true, help: "console.x.ai" },
    deepseek: { label: "DeepSeek V4.1 Flash (token deal)", kind: "openai", url: "https://api.deepseek.com/v1/chat/completions", model: "deepseek-flash", key: true, help: "platform.deepseek.com — model deepseek-flash · off-peak $0.15/$0.60 per 1M · cache-hit $0.003 · 1M context" },
    together: { label: "Together AI", kind: "openai", url: "https://api.together.xyz/v1/chat/completions", model: "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", key: true, help: "api.together.xyz" },
    fireworks: { label: "Fireworks", kind: "openai", url: "https://api.fireworks.ai/inference/v1/chat/completions", model: "accounts/fireworks/models/llama-v3p1-8b-instruct", key: true, help: "fireworks.ai" },
    anthropic: { label: "Anthropic Claude (paid)", kind: "anthropic", url: "https://api.anthropic.com/v1/messages", model: "claude-3-5-haiku-latest", key: true, help: "console.anthropic.com" },
    perplexity: { label: "Perplexity", kind: "openai", url: "https://api.perplexity.ai/chat/completions", model: "sonar", key: true, help: "perplexity.ai/settings/api" },
    github: { label: "GitHub Models (PAT)", kind: "openai", url: "https://models.inference.ai.azure.com/chat/completions", model: "gpt-4o-mini", key: true, help: "github.com/settings/tokens — GitHub Models may be limited" },
    custom: { label: "Any OpenAI-compatible URL", kind: "openai", url: "", model: "", key: true, help: "Paste base (we append /v1/chat/completions) or full chat URL" },
  };
  const AGENT_TOOLS = [
    { type: "function", function: { name: "wiki_search", description: "Search Wikipedia. RESOURCE.", parameters: { type: "object", properties: { q: { type: "string" } }, required: ["q"] } } },
    { type: "function", function: { name: "fetch_page", description: "Readable extract of an HTTPS page via r.jina.ai.", parameters: { type: "object", properties: { url: { type: "string" } }, required: ["url"] } } },
    { type: "function", function: { name: "weather", description: "Current weather. RESOURCE.", parameters: { type: "object", properties: { place: { type: "string" } }, required: ["place"] } } },
    { type: "function", function: { name: "now", description: "Current local and UTC time.", parameters: { type: "object", properties: {} } } },
    { type: "function", function: { name: "calc", description: "Evaluate a numeric expression.", parameters: { type: "object", properties: { expr: { type: "string" } }, required: ["expr"] } } },
    { type: "function", function: { name: "champion", description: "Load a Δ9 champion lens by name (ARKOS, LYRA, …).", parameters: { type: "object", properties: { name: { type: "string" } }, required: ["name"] } } },
    { type: "function", function: { name: "hash_text", description: "SHA-256 of text (WebCrypto).", parameters: { type: "object", properties: { text: { type: "string" } }, required: ["text"] } } },
    { type: "function", function: { name: "skill_list", description: "List LYGO default skills shipped with this portal (SkillHub pack).", parameters: { type: "object", properties: {} } } },
    { type: "function", function: { name: "skill_read", description: "Read one default LYGO skill by slug or name.", parameters: { type: "object", properties: { slug: { type: "string" } }, required: ["slug"] } } },
    { type: "function", function: { name: "hn_search", description: "Hacker News Algolia search. RESOURCE.", parameters: { type: "object", properties: { q: { type: "string" } }, required: ["q"] } } },
    { type: "function", function: { name: "arxiv_search", description: "Search arXiv papers. RESOURCE.", parameters: { type: "object", properties: { q: { type: "string" } }, required: ["q"] } } },
    { type: "function", function: { name: "github_search", description: "Search public GitHub repositories. RESOURCE.", parameters: { type: "object", properties: { q: { type: "string" } }, required: ["q"] } } },
    { type: "function", function: { name: "wayback", description: "Internet Archive availability for a URL.", parameters: { type: "object", properties: { url: { type: "string" } }, required: ["url"] } } },
    { type: "function", function: { name: "geolocate", description: "Browser geolocation. Asks the human first.", parameters: { type: "object", properties: {} } } },
    { type: "function", function: { name: "clipboard_write", description: "Write text to clipboard. Asks the human first.", parameters: { type: "object", properties: { text: { type: "string" } }, required: ["text"] } } },
  ];

  const log = document.getElementById("log");
  const healthEl = document.getElementById("health");
  const limb = document.getElementById("limb-out");
  const msg = document.getElementById("msg");
  const modeEl = document.getElementById("mode");
  const endpointEl = document.getElementById("endpoint");
  const tokenEl = document.getElementById("hf-token");
  const modelEl = document.getElementById("model");
  let history = [];
  let connected = false;
  let SKILLS = [];

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
  async function saveToDisk(filename, text) {
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    if (window.showSaveFilePicker) {
      try {
        const h = await window.showSaveFilePicker({
          suggestedName: filename,
          types: [{ description: "Text", accept: { "text/plain": [".txt", ".md", ".json"] } }],
        });
        const w = await h.createWritable();
        await w.write(blob);
        await w.close();
        return { ok: true, method: "picker", name: filename };
      } catch (e) {
        if (e && e.name === "AbortError") return { ok: false, error: "cancelled" };
      }
    }
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 2000);
    return { ok: true, method: "download", name: filename };
  }
  function sessionPayload() {
    return JSON.stringify({ v: 1, saved: new Date().toISOString(), provider: modeEl && modeEl.value, model: modelEl && modelEl.value, history: history, notepad: (document.getElementById("np-body") || {}).value || "" }, null, 2);
  }
  function provider() {
    return PROVIDERS[modeEl.value] || PROVIDERS.groq;
  }

  function fillProvider() {
    const p = provider();
    if (modelEl) modelEl.value = p.model || modelEl.value;
    if (endpointEl) endpointEl.value = p.url || "";
    if (tokenEl) {
      tokenEl.style.display = p.key ? "" : "none";
      tokenEl.placeholder = "API key stays in this browser — never sent to chatagent.ca";
    }
    const help = document.getElementById("mode-help");
    if (help) {
      help.innerHTML =
        p.help +
        ' · <a href="/guides/how-to-lygo-llm-portal.html">How to connect</a> · Need a local GPU? <a href="https://chatagent.ca/lygoskillhub.html#lygo-llm-kernel">Download FULL console</a>';
    }
    setHealth("API portal · " + p.label + (connected ? " · connected" : " · paste key → Connect"));
  }

  function systemPrompt(invoked) {
    let s =
      "You are a LYGO-aligned agent in the public API portal at https://chatagent.ca/portal/. " +
      "The human is the publisher. Assist; never replace them. Dual ledgers / Haven Star Chart = CANON. This chat = RESOURCE. " +
      "P0: no OS wipe, no secrets in notes, no fabricated receipts. " +
      "You have real browser limbs: wiki_search, fetch_page, weather, now, calc, champion, hash_text, skill_list, skill_read, hn_search, arxiv_search, github_search, wayback, geolocate (asks permission), clipboard_write (asks permission). Use them. Default LYGO skills are loaded — skill_read before acting as a seat. " +
      "If they want disk/skills/local GGUF, send them to https://chatagent.ca/lygoskillhub.html#lygo-llm-kernel and https://chatagent.ca/lygo-llm-console.html — this page is API-only. " +
      "Never invent github.com/user/repo. Real org https://github.com/DeepSeekOracle · HF https://huggingface.co/DeepSeekOracle.";
    if (invoked) s += " Champion lens: " + invoked + ". Observed / Inferred / Unknown.";
    return s;
  }

  async function runTool(name, args) {
    args = args || {};
    try {
      if (name === "wiki_search") {
        const q = args.q || args.query || "";
        const u = "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=" + encodeURIComponent(q) + "&format=json&origin=*";
        const j = await (await fetch(u)).json();
        const hits = ((j.query && j.query.search) || []).slice(0, 5).map(function (x) {
          return { title: x.title, snippet: (x.snippet || "").replace(/<[^>]+>/g, "") };
        });
        return { ok: true, hits: hits, class: "RESOURCE" };
      }
      if (name === "fetch_page") {
        const url = args.url || "";
        if (!/^https:\/\//i.test(url)) return { ok: false, error: "https_only" };
        const t = await (await fetch("https://r.jina.ai/" + url)).text();
        return { ok: true, url: url, text: t.slice(0, 6000), class: "RESOURCE" };
      }
      if (name === "weather") {
        const place = args.place || "";
        const t = await (await fetch("https://wttr.in/" + encodeURIComponent(place) + "?format=3")).text();
        return { ok: true, text: t, class: "RESOURCE" };
      }
      if (name === "now") {
        const d = new Date();
        return { ok: true, local: d.toString(), utc: d.toISOString() };
      }
      if (name === "calc") {
        const expr = String(args.expr || "");
        if (!/^[\d+\-*/().\s]+$/.test(expr)) return { ok: false, error: "unsafe" };
        return { ok: true, value: Function("return (" + expr + ")")() };
      }
      if (name === "champion") {
        const n = String(args.name || "").toUpperCase();
        const key = Object.keys(CHAMPS).find(function (k) { return k.toUpperCase() === n || k.replace(/Δ/g, "D") === n; }) || args.name;
        return { ok: true, name: key, lens: CHAMPS[key] || "Unknown seat. Directory: https://chatagent.ca/champions.html" };
      }
      if (name === "hash_text") {
        const enc = new TextEncoder().encode(String(args.text || ""));
        const buf = await crypto.subtle.digest("SHA-256", enc);
        const hex = Array.from(new Uint8Array(buf)).map(function (b) { return b.toString(16).padStart(2, "0"); }).join("");
        return { ok: true, sha256: hex };
      }
      if (name === "skill_list") {
        return { ok: true, n: SKILLS.length, skills: SKILLS.map(function (s) { return { slug: s.slug, name: s.name, when: s.when }; }) };
      }
      if (name === "skill_read") {
        const q = String(args.slug || args.name || "").toLowerCase();
        const s = SKILLS.find(function (x) { return x.slug === q || (x.name || "").toLowerCase() === q || x.slug.indexOf(q) >= 0; });
        if (!s) return { ok: false, error: "missing", hint: "skill_list" };
        return { ok: true, slug: s.slug, name: s.name, when: s.when, text: s.text };
      }
      if (name === "hn_search") {
        const u = "https://hn.algolia.com/api/v1/search?query=" + encodeURIComponent(args.q || "") + "&hitsPerPage=5";
        const j = await (await fetch(u)).json();
        return { ok: true, hits: (j.hits || []).map(function (h) { return { title: h.title, url: h.url, points: h.points }; }), class: "RESOURCE" };
      }
      if (name === "arxiv_search") {
        const u = "https://export.arxiv.org/api/query?search_query=all:" + encodeURIComponent(args.q || "") + "&start=0&max_results=5";
        const t = await (await fetch(u)).text();
        return { ok: true, text: t.slice(0, 5000), class: "RESOURCE" };
      }
      if (name === "github_search") {
        const u = "https://api.github.com/search/repositories?q=" + encodeURIComponent(args.q || "DeepSeekOracle") + "&per_page=5";
        const j = await (await fetch(u)).json();
        return { ok: true, hits: ((j.items) || []).map(function (i) { return { full_name: i.full_name, html_url: i.html_url, description: i.description }; }), class: "RESOURCE" };
      }
      if (name === "wayback") {
        const u = "https://archive.org/wayback/available?url=" + encodeURIComponent(args.url || "");
        const j = await (await fetch(u)).json();
        return { ok: true, snapshots: j.archived_snapshots || {}, class: "RESOURCE" };
      }
      if (name === "geolocate") {
        if (!confirm("Allow this portal to read your location for weather/maps? (browser permission next)")) return { ok: false, error: "denied" };
        const pos = await new Promise(function (res, rej) { navigator.geolocation.getCurrentPosition(res, rej, { timeout: 8000 }); });
        return { ok: true, lat: pos.coords.latitude, lon: pos.coords.longitude, accuracy: pos.coords.accuracy };
      }
      if (name === "clipboard_write") {
        if (!confirm("Allow this portal to write to your clipboard?")) return { ok: false, error: "denied" };
        await navigator.clipboard.writeText(String(args.text || ""));
        return { ok: true };
      }
    } catch (e) {
      return { ok: false, error: String(e) };
    }
    return { ok: false, error: "unknown_tool" };
  }

  function openaiUrl() {
    const p = provider();
    let e = (endpointEl.value || p.url || "").trim().replace(/\/$/, "");
    if (!e) return "";
    if (/\/chat\/completions$/i.test(e) || /\/messages$/i.test(e) || /\/paas\/v4\/chat\/completions$/i.test(e)) return e;
    if (/\/openai\/v1$/i.test(e) || /\/v1$/i.test(e) || /\/v1beta\/openai$/i.test(e) || /\/compatibility\/v1$/i.test(e)) return e + "/chat/completions";
    if (/\/v1\//i.test(e) && /chat/i.test(e)) return e;
    return e + "/v1/chat/completions";
  }

  async function callApi(messages) {
    const p = provider();
    const url = openaiUrl();
    const model = modelEl.value || p.model;
    const key = (tokenEl && tokenEl.value) || "";
    const headers = { "Content-Type": "application/json" };
    if (key) {
      if (p.kind === "anthropic") {
        headers["x-api-key"] = key;
        headers["anthropic-version"] = "2023-06-01";
      } else {
        headers.Authorization = "Bearer " + key;
        if (modeEl.value === "github") headers["api-key"] = key;
      }
    }
    if (p.extra) Object.keys(p.extra).forEach(function (k) { headers[k] = p.extra[k]; });
    let payload;
    if (p.kind === "anthropic") {
      payload = { model: model, max_tokens: 1024, system: messages[0] && messages[0].content, messages: messages.filter(function (m) { return m.role !== "system"; }) };
    } else {
      payload = { model: model, messages: messages, max_tokens: 1024, stream: false, tools: AGENT_TOOLS };
    }
    let r = await fetch(url, { method: "POST", headers: headers, body: JSON.stringify(payload) });
    let j = await r.json().catch(function () { return {}; });
    if (!r.ok && payload.tools && (r.status === 400 || r.status === 404 || r.status === 422)) {
      delete payload.tools;
      r = await fetch(url, { method: "POST", headers: headers, body: JSON.stringify(payload) });
      j = await r.json().catch(function () { return {}; });
    }
    if (!r.ok) {
      const err = (j.error && (j.error.message || JSON.stringify(j.error))) || j.detail || ("http " + r.status);
      throw new Error(typeof err === "string" ? err : JSON.stringify(err));
    }
    return j;
  }

  function extractMessage(j) {
    const msg = ((j.choices || [])[0] || {}).message || {};
    const text = msg.content || (((j.content || [])[0] || {}).text) || "";
    return { text: typeof text === "string" ? text : JSON.stringify(text), tool_calls: msg.tool_calls || [] };
  }

  document.getElementById("connect").onclick = function () {
    fillProvider();
    const p = provider();
    if (p.key && !(tokenEl && tokenEl.value) && modeEl.value !== "llm7" && modeEl.value !== "custom") {
      setHealth("paste your API key (this tab only) — " + p.help);
      bubble("assistant", "This is the LYGO API portal. Paste a Groq/OpenAI/Grok/… key, then Connect. Keys never hit chatagent.ca (static GitHub Pages).\n\nWant a local GPU with files and skills? Download the FULL console: https://chatagent.ca/lygoskillhub.html#lygo-llm-kernel");
      return;
    }
    if (!openaiUrl()) {
      setHealth("paste an endpoint URL");
      return;
    }
    connected = true;
    try { sessionStorage.setItem("lygo_portal_provider", modeEl.value); } catch (_) {}
    setHealth("connected · " + p.label + " · tools on");
    bubble("assistant", "Connected to " + p.label + ". Browser limbs: wiki, fetch, weather, time, calc, champions, hash. Disks/GGUF stay on the local kit.\nSkillHub FULL: https://chatagent.ca/lygoskillhub.html#lygo-llm-kernel");
  };

  if (modeEl) {
    modeEl.innerHTML = "";
    Object.keys(PROVIDERS).forEach(function (id) {
      const o = document.createElement("option");
      o.value = id;
      o.textContent = PROVIDERS[id].label;
      modeEl.appendChild(o);
    });
    try {
      const saved = sessionStorage.getItem("lygo_portal_provider");
      modeEl.value = saved && PROVIDERS[saved] ? saved : "groq";
    } catch (_) {
      modeEl.value = "groq";
    }
    modeEl.onchange = fillProvider;
    fillProvider();
  }
  document.querySelectorAll("[data-fill]").forEach(function (a) {
    a.addEventListener("click", function (ev) {
      const id = a.getAttribute("data-fill");
      if (!id || !PROVIDERS[id] || !modeEl) return;
      ev.preventDefault();
      modeEl.value = id;
      fillProvider();
      if (tokenEl && PROVIDERS[id].key) tokenEl.focus();
    });
  });

  const box = document.getElementById("champs");
  if (box) {
    Object.keys(CHAMPS).forEach(function (name) {
      const b = document.createElement("button");
      b.type = "button";
      b.textContent = name;
      b.title = CHAMPS[name];
      b.onclick = function () {
        msg.value = "Invoke " + name + " — " + CHAMPS[name];
        msg.focus();
      };
      box.appendChild(b);
    });
  }

  document.querySelectorAll("[data-limb]").forEach(function (b) {
    b.onclick = async function () {
      const n = b.getAttribute("data-limb");
      if (n === "wiki") {
        const r = await runTool("wiki_search", { q: msg.value || "LYGO" });
        limb.textContent = JSON.stringify(r, null, 2);
        bubble("assistant", "Wikipedia (RESOURCE):\n" + ((r.hits || []).map(function (h) { return h.title + " — " + h.snippet; }).join("\n") || r.error));
      } else if (n === "weather") {
        const r = await runTool("weather", { place: "" });
        bubble("assistant", r.text || r.error);
      } else if (n === "skillhub") window.open("https://chatagent.ca/lygoskillhub.html#lygo-llm-kernel", "_blank", "noopener");
      else if (n === "howto") window.open("/guides/how-to-lygo-llm-portal.html", "_blank", "noopener");
      else if (n === "kit") window.open("https://chatagent.ca/lygo-llm-console.html", "_blank", "noopener");
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
        npSt.textContent = "saved in this browser";
      } catch (_) { npSt.textContent = "blocked"; }
    };
  }
  const npDisk = document.getElementById("np-disk");
  if (npDisk) {
    npDisk.onclick = async function () {
      const r = await saveToDisk("lygo-notepad-" + Date.now() + ".md", (npBody && npBody.value) || "");
      if (npSt) npSt.textContent = r.ok ? ("saved " + r.method) : (r.error || "fail");
    };
  }
  const sessSave = document.getElementById("sess-save");
  if (sessSave) {
    sessSave.onclick = async function () {
      try { localStorage.setItem("lygo_portal_session", sessionPayload()); } catch (_) {}
      const r = await saveToDisk("lygo-session-" + Date.now() + ".json", sessionPayload());
      limb.textContent = JSON.stringify(r, null, 2);
    };
  }
  const sessLoad = document.getElementById("sess-load");
  if (sessLoad) {
    sessLoad.onclick = function () {
      const inp = document.createElement("input");
      inp.type = "file";
      inp.accept = ".json,application/json";
      inp.onchange = function () {
        const f = inp.files && inp.files[0];
        if (!f) return;
        const rd = new FileReader();
        rd.onload = function () {
          try {
            const data = JSON.parse(String(rd.result || "{}"));
            history = data.history || [];
            if (npBody && data.notepad) npBody.value = data.notepad;
            log.innerHTML = "";
            history.forEach(function (m) { bubble(m.role === "user" ? "user" : "assistant", m.content || ""); });
            limb.textContent = "session loaded " + (data.saved || "");
          } catch (e) { limb.textContent = "bad session file"; }
        };
        rd.readAsText(f);
      };
      inp.click();
    };
  }
  const attachBtn = document.getElementById("attach-file");
  if (attachBtn) {
    attachBtn.onclick = function () {
      const inp = document.createElement("input");
      inp.type = "file";
      inp.onchange = function () {
        const f = inp.files && inp.files[0];
        if (!f) return;
        const rd = new FileReader();
        rd.onload = function () {
          const text = String(rd.result || "").slice(0, 20000);
          history.push({ role: "user", content: "Attached file " + f.name + ":\n" + text });
          bubble("user", "Attached " + f.name + " (" + text.length + " chars) into this session.");
        };
        rd.readAsText(f);
      };
      inp.click();
    };
  }
  fetch("lygo-skills.json", { cache: "no-store" })
    .then(function (r) { return r.json(); })
    .then(function (j) {
      SKILLS = j.skills || [];
      const box = document.getElementById("skill-pack");
      if (box) box.textContent = SKILLS.length + " default LYGO skills loaded (SkillHub pack). Agent: skill_list / skill_read.";
    })
    .catch(function () {});
  fetch("https://chatagent.ca/data/lygoskillhub_catalog.json", { cache: "no-store" })
    .then(function (r) { return r.json(); })
    .then(function (j) {
      const extra = (j.skills || []).filter(function (s) { return s && s.slug && s.kind !== "page"; }).slice(0, 40);
      extra.forEach(function (s) {
        if (SKILLS.some(function (x) { return x.slug === s.slug; })) return;
        SKILLS.push({ slug: s.slug, name: s.name || s.slug, when: s.category || "skillhub", text: (s.summary || "") + "\nInstall FULL locally: https://chatagent.ca/lygoskillhub.html  This webpage cannot run skill scripts." });
      });
      const box = document.getElementById("skill-pack");
      if (box) box.textContent = SKILLS.length + " LYGO skills available (default pack + SkillHub catalog). Use skill_list / skill_read.";
    })
    .catch(function () {});

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
    if (!connected) {
      bubble(
        "assistant",
        "This page is the LYGO API portal — not a hosted GPU.\n\n1) Pick Groq (free) or another provider.\n2) Paste the key (stays in this tab).\n3) Connect, then send again.\n\nWant models on your disk, folders, SkillHub FULL, USB CLAW? Download the local console:\nhttps://chatagent.ca/lygoskillhub.html#lygo-llm-kernel\nhttps://chatagent.ca/lygo-llm-console.html\nGuide: https://chatagent.ca/guides/how-to-lygo-llm-portal.html"
      );
      return;
    }
    history.push({ role: "user", content: text });
    const invoked = Object.keys(CHAMPS).find(function (n) { return text.toUpperCase().indexOf(n.toUpperCase()) >= 0; });
    let messages = [{ role: "system", content: systemPrompt(invoked) }].concat(history.slice(-10));
    let out = "";
    try {
      for (let round = 0; round < 4; round++) {
        const j = await callApi(messages);
        const got = extractMessage(j);
        limb.textContent = JSON.stringify({ round: round, tools: (got.tool_calls || []).map(function (t) { return (t.function || t).name; }) }, null, 2);
        if (got.tool_calls && got.tool_calls.length) {
          messages.push({ role: "assistant", content: got.text || "", tool_calls: got.tool_calls });
          for (let i = 0; i < got.tool_calls.length; i++) {
            const tc = got.tool_calls[i];
            const fn = tc.function || tc;
            let args = {};
            try { args = typeof fn.arguments === "string" ? JSON.parse(fn.arguments) : fn.arguments || {}; } catch (_) {}
            const result = await runTool(fn.name, args);
            messages.push({ role: "tool", tool_call_id: tc.id || String(i), content: JSON.stringify(result) });
          }
          continue;
        }
        out = got.text;
        break;
      }
    } catch (e) {
      out =
        "Provider error: " + e.message +
        "\n\nIf this is CORS, the vendor blocks browsers. Try Groq or OpenRouter, or run the local kit.\nSkillHub: https://chatagent.ca/lygoskillhub.html#lygo-llm-kernel";
    }
    if (P0.test(out || "")) out = "[output quarantined]";
    if (!out) out = "(empty model reply — try again or another provider)";
    history.push({ role: "assistant", content: out });
    bubble("assistant", out);
  };

  bubble(
    "assistant",
    "LYGO API Portal. This site does not host a GPU.\n\nBring a free or paid key (Groq is the usual start) → Connect → chat with wiki/weather/fetch/champion limbs in the browser.\n\nNeed a full local LLM (GGUF, folders, SkillHub FULL, USB)? Download the console:\nhttps://chatagent.ca/lygoskillhub.html#lygo-llm-kernel\nDocs: https://chatagent.ca/lygo-llm-console.html\nHow-to: https://chatagent.ca/guides/how-to-lygo-llm-portal.html"
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
