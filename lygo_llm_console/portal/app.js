(function () {
  /* One product name, one build stamp. The header, the document title and every status line read
     from here, so the console cannot drift back into three names and no version in the UI. */
  const LYGO_PRODUCT = "LYGO Local Agent Console";
  const LYGO_BUILD = "1.1.0";
  const BUILD_STAMP = "build " + LYGO_BUILD;
  const TOKEN_KEY = "lygo_llm_token";
  function captureTokenFromUrl() {
    const u = new URL(location.href);
    const t = u.searchParams.get("t") || u.searchParams.get("token");
    if (t) {
      sessionStorage.setItem(TOKEN_KEY, t);
      u.searchParams.delete("t");
      u.searchParams.delete("token");
      window.history.replaceState({}, "", u.pathname + u.search);
    }
    if (typeof window.LYGO_TOKEN === "string" && window.LYGO_TOKEN) {
      sessionStorage.setItem(TOKEN_KEY, window.LYGO_TOKEN);
    }
  }
  captureTokenFromUrl();
  function token() {
    return sessionStorage.getItem(TOKEN_KEY) || window.LYGO_TOKEN || "";
  }
  function headers() {
    return { "Content-Type": "application/json", "X-LYGO-LLM-Token": token(), "Cache-Control": "no-store" };
  }
  let lastScan = -1;
  const healthEl = document.getElementById("health");
  const log = document.getElementById("log");
  const form = document.getElementById("form");
  const msg = document.getElementById("msg");
  const models = document.getElementById("models");
  const limb = document.getElementById("limb-out");
  const img = document.getElementById("img");
  const stopBtn = document.getElementById("stop");
  const sendBtn = document.getElementById("send");
  const emptyState = document.getElementById("empty-state");
  const statusOut = document.getElementById("status-out");
  const traceList = document.getElementById("trace-list");
  const traceCount = document.getElementById("trace-count");
  const ctxNote = document.getElementById("ctx-note");
  let pendingImage = null;
  let bootedOnce = false;
  let chatHistory = [];
  const HIST_KEY = "lygo_llm_chatHistory";
  const MAX_MSGS = 24;        /* history window sent to the engine */
  const MAX_IMAGES = 2;       /* base64 images kept in chatHistory — they are re-sent every turn */
  const MAX_TOKENS = 768;     /* shown in #ctx-note so a cut-off answer is explainable */
  const STREAM_IDLE_MS = 60000;  /* no token for this long = engine not responding */
  const STREAM_CAP_MS = 600000;  /* hard ceiling on one answer */

  /* ---- footer status: its own element, so a trace dump can never erase it -------------- */
  let stickyStatus = "";
  function setStatus(text, warn) {
    if (!statusOut) return;
    statusOut.textContent = text;
    statusOut.classList.toggle("warn", !!warn);
  }
  /* A failed action stays on screen until the user does something about it. */
  function setStickyStatus(text) { stickyStatus = text || ""; setStatus(text, true); }
  function clearStickyStatus() { stickyStatus = ""; }
  function statusSoft(text) { if (!stickyStatus) setStatus(text, false); }

  /* ---- tool traces: compact list in their own collapsible pane ------------------------- */
  function summarizeArgs(args) {
    try {
      const s = JSON.stringify(args || {});
      if (!s || s === "{}" || s === "null") return "";
      return s.length > 72 ? s.slice(0, 69) + "…" : s;
    } catch (_) { return ""; }
  }
  function traceFailed(t) {
    const res = t && (t.result !== undefined ? t.result : t.output);
    if (res && typeof res === "object") return res.ok === false || !!res.error;
    return false;
  }
  function renderTraces(traces) {
    if (!traceList || !traces) return;
    const list = Array.isArray(traces) ? traces : [traces];
    list.forEach((t) => {
      const name = (t && (t.name || t.tool || t.fn || t.function)) || "tool";
      const args = (t && (t.arguments || t.args || t.parameters)) || {};
      const bad = traceFailed(t);
      const li = document.createElement("li");
      li.className = "trace-item " + (bad ? "fail" : "ok");
      const badge = document.createElement("span");
      badge.className = "trace-badge";
      badge.textContent = bad ? "fail" : "ok";
      const nm = document.createElement("b");
      nm.textContent = name;
      const ar = document.createElement("span");
      ar.className = "trace-args";
      ar.textContent = summarizeArgs(args);
      li.appendChild(badge);
      li.appendChild(nm);
      li.appendChild(ar);
      try { li.title = JSON.stringify(t).slice(0, 900); } catch (_) {}
      traceList.appendChild(li);
      while (traceList.children.length > 60) traceList.removeChild(traceList.firstChild);
    });
    if (traceCount) traceCount.textContent = String(traceList.children.length);
    const pane = document.getElementById("trace-pane");
    if (pane) pane.open = true;
  }
  function clearTraces() {
    if (traceList) traceList.innerHTML = "";
    if (traceCount) traceCount.textContent = "0";
  }

  /* ---- transcript helpers ------------------------------------------------------------- */
  function contentText(c) {
    if (typeof c === "string") return c;
    if (!c) return "";
    if (Object.prototype.toString.call(c) === "[object Array]") {
      return c.map((p) => {
        if (!p) return "";
        if (p.type === "image_url") return "[image]";
        return p.text || "";
      }).filter(Boolean).join("\n");
    }
    return JSON.stringify(c);
  }
  function clearTranscript() {
    if (!log) return;
    const kids = log.querySelectorAll(".bubble");
    for (let i = 0; i < kids.length; i++) log.removeChild(kids[i]);
    if (emptyState) emptyState.hidden = false;
    log.scrollTop = 0;
  }
  function renderHistory() {
    if (!log) return;
    const kids = log.querySelectorAll(".bubble");
    for (let i = 0; i < kids.length; i++) log.removeChild(kids[i]);
    if (emptyState) emptyState.hidden = chatHistory.length > 0;
    chatHistory.forEach((m) => {
      bubble(m.role === "user" ? "user" : "assistant", contentText(m.content));
    });
  }
  let lastPruneDropped = false;
  let restoredFromServer = 0;
  function pruneHistory(list) {
    /* Message window first, then images: only the newest MAX_IMAGES base64 payloads survive, or
       every turn re-sends the whole pile of them. */
    let h = list.slice(-MAX_MSGS);
    let kept = 0;
    for (let i = h.length - 1; i >= 0; i--) {
      const m = h[i];
      if (!m || Object.prototype.toString.call(m.content) !== "[object Array]") continue;
      const room = MAX_IMAGES - kept;
      const imgs = m.content.filter((p) => p && p.type === "image_url");
      let seen = 0;
      const next = [];
      m.content.forEach((p) => {
        if (!p || p.type !== "image_url") { next.push(p); return; }
        seen += 1;
        const fromEnd = imgs.length - seen;
        if (fromEnd < room) { kept += 1; next.push(p); }
        else lastPruneDropped = true;
      });
      const text = next.filter((p) => p && p.type !== "image_url" && p.text).map((p) => p.text).join("\n");
      m.content = next.length ? next : [{ type: "text", text: text || "[older image dropped from history]" }];
      if (!next.some((p) => p && p.type === "image_url") && !text) {
        m.content = "[older image dropped from history]";
      }
    }
    return h;
  }
  function paintCtx(dropped) {
    if (!ctxNote) return;
    const msgN = chatHistory.length;
    const imgN = chatHistory.reduce((n, m) => n + (Object.prototype.toString.call(m.content) === "[object Array]" ? m.content.filter((p) => p && p.type === "image_url").length : 0), 0);
    /* Full window = the next turn pushes something out, so say so and keep saying it. */
    const full = msgN >= MAX_MSGS;
    ctxNote.textContent = "context: " + msgN + "/" + MAX_MSGS + " messages · images kept " + imgN + "/" + MAX_IMAGES + " · max_tokens " + MAX_TOKENS +
      (dropped || full ? " · history window full — older turns are dropped from what the engine sees" : "");
    ctxNote.classList.toggle("warn", !!(dropped || full));
  }
  function fillComposerIfEmpty(text) {
    /* Workspace clicks used to overwrite whatever the operator had typed. */
    if (!msg) return false;
    if ((msg.value || "").trim()) {
      setStatus("left your draft alone — the folder is open in the Workspace panel", false);
      return false;
    }
    msg.value = text;
    return true;
  }
  function paintBrand() {
    const nameEl = document.getElementById("brand-name");
    const buildEl = document.getElementById("brand-build");
    if (nameEl) nameEl.textContent = LYGO_PRODUCT;
    if (buildEl) buildEl.textContent = BUILD_STAMP;
    if (typeof document.title === "string") document.title = LYGO_PRODUCT + " · " + BUILD_STAMP;
  }
  paintBrand();

  document.querySelectorAll("[data-prompt]").forEach((btn) => {
    btn.onclick = function () {
      if (!msg) return;
      msg.value = btn.getAttribute("data-prompt") || "";
      msg.focus();
    };
  });

  function setHealth(j) {
    const err = j.error ? " err=" + j.error : "";
    const cloud = j.cloud && j.cloud.mode === "api" ? " brain=API " + (j.cloud.label || j.cloud.provider) + "/" + (j.cloud.model || "") : " brain=LOCAL";
    const hoff = j.fallback && j.fallback.why && j.cloud && j.cloud.degraded ? " handoff=" + j.fallback.why : "";
    healthEl.textContent =
      `build=${j.build || "?"} engine=${j.brain || "?"} selected=${j.selected || "—"} models=${j.scan_n || 0} limbs=${(j.tools||[]).length} up=${j.engine_present} ram=${Math.round((j.ram_avail || 0) / 1e9)}GB${cloud}${hoff}${err}`;
  }

  let healthDown = false;
  async function refreshHealth() {
    try {
      const r = await fetch("/api/health", { headers: headers() });
      if (!r.ok) {
        healthEl.textContent = "health " + r.status + (r.status === 401 ? " unauthorized — open the console from the launcher link that carries the token" : "");
        if (r.status === 401 && !stickyStatus) {
          setStickyStatus("unauthorized (401) — this page has no token; reopen the console from its launcher link (?token=…), which sets it for this tab");
        }
        return null;
      }
      const j = await r.json();
      lastHealth = j;
      setHealth(j);
      healthDown = false;
      if (j.cloud) paintApi(j.cloud);
      document.body.dataset.brain = j.brain || "";
      if (typeof j.scan_n === "number" && j.scan_n !== lastScan) {
        lastScan = j.scan_n;
        try { await refreshModels(); } catch (_) {}
      }
      return j;
    } catch (e) {
      healthEl.textContent = "health failed — console not reachable";
      if (!healthDown) {
        healthDown = true;
        statusSoft("console not reachable (/api/health failed) — is the window still running?");
      }
      return null;
    }
  }
  async function refreshModels() {
    const r = await fetch("/api/models", { headers: headers(), cache: "no-store" });
    if (!r.ok) {
      setStatus("model list " + r.status + " — press Scan drives in the header", true);
      const o = document.createElement("option");
      o.textContent = "(scan failed " + r.status + ")";
      o.value = "";
      models.innerHTML = "";
      models.appendChild(o);
      return;
    }
    const j = await r.json();
    models.innerHTML = "";
    const list = j.models || [];
    if (!list.length) {
      const o = document.createElement("option");
      o.textContent = "(none — click Scan drives)";
      o.value = "";
      models.appendChild(o);
      return;
    }
    list.forEach((m) => {
      const o = document.createElement("option");
      o.value = m.id;
      const gb = m.bytes ? (m.bytes / 1e9).toFixed(1) + "GB" : "";
      o.textContent = `${m.id} [${m.kind || "?"} ${m.runnable ? "ok" : m.status} ${gb}]`;
      if (m.id === j.selected) o.selected = true;
      models.appendChild(o);
    });
  }
  function bubble(role, text) {
    const d = document.createElement("div");
    d.className = "bubble " + role;
    d.textContent = text;
    log.appendChild(d);
    if (emptyState) emptyState.hidden = true;
    log.scrollTop = log.scrollHeight;
    return d;
  }
  function bubbleError(text) {
    const d = document.createElement("div");
    d.className = "bubble assistant error";
    d.textContent = text;
    log.appendChild(d);
    if (emptyState) emptyState.hidden = true;
    log.scrollTop = log.scrollHeight;
    return d;
  }
  let activeAbort = null;   /* AbortController for the answer in flight */
  function stopStream(why) {
    if (!activeAbort) return;
    activeAbort.__stopped = true;
    try { activeAbort.abort(); } catch (_) {}
    setStatus(why || "stopped by user", true);
  }
  function markBrain(el, evn) {
    if (!el || !evn) return;
    const active = evn.active || (evn.brain === "cloud" ? "cloud" : "local");
    el.classList.remove("via-api", "via-local");
    el.classList.add(active === "cloud" ? "via-api" : "via-local");
    const why = evn.fallback && evn.fallback.why ? evn.fallback.why : "";
    el.classList.toggle("takeover", !!why);
    if (why) el.title = "API handoff: " + why;
  }

  async function boot(id) {
    setStatus("booting " + (id || "selected") + " … first load can take a minute");
    limb.textContent = "booting " + (id || "selected") + " …";
    let r;
    try {
      r = await fetch("/api/boot", {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({ id: id || models.value }),
      });
    } catch (e) {
      setStatus("boot request failed — " + ((e && e.message) ? e.message : e), true);
      return null;
    }
    const j = await r.json().catch(function () { return {}; });
    limb.textContent = JSON.stringify(j, null, 2);
    if (!r.ok) setStatus("boot failed — " + (j.error || ("HTTP " + r.status)), true);
    else setStatus("boot: " + (j.brain || j.status || "asked") + " · engine=" + ((j.state && j.state.brain) || lastHealth.brain || "?"));
    await refreshHealth();
    return j;
  }

  document.getElementById("scan").onclick = async () => {
    setStatus("scanning drives…");
    limb.textContent = "scanning…";
    let r;
    try {
      r = await fetch("/api/scan", { method: "POST", headers: headers(), body: "{}" });
    } catch (e) {
      setStatus("scan failed — " + ((e && e.message) ? e.message : e), true);
      return;
    }
    const j = await r.json().catch(function () { return {}; });
    const n = (j.models || (j.registry && j.registry.models) || []).length;
    limb.textContent = JSON.stringify(
      { n: n, truncated: j.scan_truncated, roots: j.roots, selected: (j.registry || {}).selected },
      null,
      2
    );
    setStatus(r.ok ? ("scan found " + n + " model(s)" + (j.scan_truncated ? " · list truncated" : "") + " — pick one and press Boot LLM") : ("scan failed — " + (j.error || r.status)), !r.ok);
    await refreshModels();
    await refreshHealth();
  };
  document.getElementById("select").onclick = async () => {
    await boot(models.value);
  };
  const apiProv = document.getElementById("api-provider");
  const apiKey = document.getElementById("api-key");
  const apiModel = document.getElementById("api-model");
  const apiUrl = document.getElementById("api-url");
  const apiStatus = document.getElementById("api-status");
  const brainStatus = document.getElementById("brain-status");
  const brainLocalBtn = document.getElementById("brain-local");
  const brainApiBtn = document.getElementById("brain-api");
  let brainMode = "local"; /* local (default) | api */
  let lastHealth = {};
  let brainBusy = false;

  function localLabel() {
    return (models && models.value) || (lastHealth && lastHealth.selected) || "engine";
  }
  function paintBrain(j) {
    const cloud = j || lastHealth.cloud || {};
    brainMode = cloud.mode === "api" ? "api" : "local";
    const hasKey = !!cloud.has_key;
    if (brainLocalBtn) {
      brainLocalBtn.classList.toggle("on", brainMode === "local");
      brainLocalBtn.setAttribute("aria-pressed", brainMode === "local" ? "true" : "false");
      brainLocalBtn.disabled = brainBusy;
      brainLocalBtn.title = "Local GGUF engine on this PC — the default, always complete";
    }
    if (brainApiBtn) {
      brainApiBtn.classList.toggle("on", brainMode === "api");
      brainApiBtn.classList.toggle("degraded", !!cloud.degraded);
      brainApiBtn.setAttribute("aria-pressed", brainMode === "api" ? "true" : "false");
      /* No key = no API brain. Say it on the control instead of letting the press do nothing. */
      brainApiBtn.disabled = brainBusy || !hasKey;
      brainApiBtn.setAttribute("aria-disabled", brainApiBtn.disabled ? "true" : "false");
      brainApiBtn.classList.toggle("needs-key", !hasKey);
      brainApiBtn.title = hasKey
        ? "Run the chat on the cloud API. The local engine stays booted as the safety net."
        : "add key first — paste your API key in the row below, press Save key, then press API.";
    }
    document.body.classList.toggle("api-on", brainMode === "api");
    document.body.dataset.brainMode = brainMode;
    if (brainStatus && !stickyStatus) {
      if (brainBusy) {
        brainStatus.textContent = "switching brain…";
      } else if (brainMode === "api") {
        brainStatus.textContent =
          "API · " + (cloud.label || "cloud") + "/" + (cloud.model || "") +
          (cloud.degraded ? " · handed over, local answering" : " · local standby " + localLabel());
      } else {
        brainStatus.textContent = "LOCAL · " + localLabel() +
          (hasKey ? " · API key saved, press the API segment to switch" : " · add key below to enable the API brain");
      }
      brainStatus.classList.toggle("warn", !!cloud.degraded || !hasKey);
    }
    if (apiStatus) {
      if (cloud.degraded) {
        apiStatus.textContent =
          "API handoff " + (cloud.last_code ? "HTTP " + cloud.last_code + " · " : "") + (cloud.last_error || "") +
          " — local answered (" + (cloud.handoffs || 0) + " handoffs). Press API to try the API again.";
      } else if (brainBusy) {
        apiStatus.textContent = "switching brain — waiting on the console…";
      } else if (brainMode === "api") {
        apiStatus.textContent = "API ON · " + (cloud.label || "") + " / " + (cloud.model || "") + " · local engine stays booted as the safety net";
      } else if (cloud.has_key) {
        apiStatus.textContent = "API key saved · press the API segment above to run the chat on the cloud (local is the default)";
      } else {
        apiStatus.textContent = "API: off (local default) — paste a key and press Save key to enable the API brain";
      }
    }
    if (apiKey) apiKey.placeholder = cloud.has_key ? "key saved on this PC — paste to replace" : "paste key then Save key";
  }
  function paintApi(j) {
    if (!j) return;
    if (apiProv && j.provider) apiProv.value = j.provider;
    if (apiModel && j.model) apiModel.value = j.model;
    if (apiUrl) {
      apiUrl.hidden = j.provider !== "custom";
      if (j.provider === "custom" && j.url) apiUrl.value = j.url;
    }
    paintBrain(j);
  }
  async function postCloud(body) {
    const r = await fetch("/api/cloud", { method: "POST", headers: headers(), body: JSON.stringify(body) });
    const j = await r.json().catch(function () { return {}; });
    if (!r.ok && !j.error) j.error = "HTTP " + r.status;
    if (!r.ok) j.ok = false;
    paintApi(j);
    await refreshHealth();
    return j;
  }
  async function refreshCloud() {
    const r = await fetch("/api/cloud", { headers: headers(), cache: "no-store" });
    const j = await r.json().catch(function () { return {}; });
    if (!r.ok) j.error = j.error || ("HTTP " + r.status);
    paintApi(j);
    return j;
  }
  async function postBrain(mode) {
    if (brainBusy) return {};
    brainBusy = true;
    clearStickyStatus();
    setStatus("switching brain to " + mode.toUpperCase() + "…");
    paintBrain(lastHealth.cloud || {}); /* applies the busy/disabled state straight away */
    try {
      const r = await fetch("/api/brain", { method: "POST", headers: headers(), body: JSON.stringify({ mode: mode }) });
      const j = await r.json().catch(function () { return {}; });
      if (!r.ok || j.error) {
        const why = j.hint || j.error || ("HTTP " + r.status);
        /* Sticky: the next 3s health refresh must not wipe the reason off the screen. */
        setStickyStatus("cannot switch to " + mode.toUpperCase() + ": " + why + " (still on " + brainMode.toUpperCase() + ")");
        if (brainStatus) {
          brainStatus.textContent = "cannot switch to " + mode + ": " + why;
          brainStatus.classList.add("warn");
        }
        return j;
      }
      paintApi(j.cloud || {});
      await refreshHealth();
      setStatus("brain = " + j.mode + " · local engine " + (j.brain || "?") + " · selected " + (j.selected || "—"));
      return j;
    } catch (e) {
      setStickyStatus("cannot switch to " + mode.toUpperCase() + ": " + ((e && e.message) ? e.message : e) + " (still on " + brainMode.toUpperCase() + ")");
      return {};
    } finally {
      brainBusy = false;
      paintBrain(lastHealth.cloud || {});
    }
  }
  if (brainLocalBtn) brainLocalBtn.onclick = function () { clearStickyStatus(); postBrain("local"); };
  if (brainApiBtn) {
    brainApiBtn.onclick = async function () {
      clearStickyStatus();
      const j = await refreshCloud();
      if (!j || !j.has_key) {
        setStickyStatus("add key first: paste the API key in the row below, press Save key, then press the API segment");
        if (apiKey) apiKey.focus();
        return;
      }
      postBrain("api");
    };
  }
  const brainBootBtn = document.getElementById("brain-boot");
  if (brainBootBtn) brainBootBtn.onclick = function () { boot(models.value); };

  async function resetSession(label) {
    /* The transcript lives on the server: only clear it after the server agrees it is gone. */
    const text = label || "New chat";
    try {
      const r = await fetch("/api/session", { method: "POST", headers: headers(), body: JSON.stringify({ new: true }) });
      const j = await r.json().catch(function () { return {}; });
      if (!r.ok || j.ok === false) throw new Error(j.error || ("HTTP " + r.status));
      chatHistory = [];
      clearTranscript();
      clearTraces();
      try { sessionStorage.removeItem(HIST_KEY); } catch (_) {}
      clearStickyStatus();
      const cm = (lastHealth.cloud && lastHealth.cloud.model) || "";
      setStatus(text + " · server session reset · now on " + (brainMode === "api" ? "API (" + cm + ")" : "LOCAL (" + localLabel() + ")"));
      paintCtx(false);
      if (msg) msg.focus();
      return true;
    } catch (e) {
      setStickyStatus(text + " failed: " + ((e && e.message) ? e.message : e) + " — nothing was cleared, the engine may still hold the old context");
      return false;
    }
  }
  function confirmNewChat(what) {
    return confirm("Start a " + what + "?\n\nThe whole transcript is cleared and the server-side session is reset. This cannot be undone.");
  }
  const brainNewBtn = document.getElementById("brain-newchat");
  if (brainNewBtn) {
    brainNewBtn.onclick = async function () {
      if (!confirmNewChat("new chat")) return;
      await resetSession("New chat");
    };
  }
  const apiOffBtn = document.getElementById("api-off");
  if (apiOffBtn) apiOffBtn.onclick = function () { clearStickyStatus(); postBrain("local"); };
  if (apiProv) {
    apiProv.onchange = async function () {
      clearStickyStatus();
      if (apiUrl) apiUrl.hidden = apiProv.value !== "custom";
      const defs = { gemini: "gemini-2.0-flash", deepseek: "deepseek-chat", groq: "openai/gpt-oss-20b", openai: "gpt-4o-mini", xai: "grok-2-latest" };
      if (apiModel && defs[apiProv.value]) apiModel.value = defs[apiProv.value];
      await postCloud({ provider: apiProv.value, model: apiModel && apiModel.value, url: apiUrl && apiUrl.value });
    };
  }
  const apiBtn = document.getElementById("api-connect");
  if (apiBtn) {
    apiBtn.onclick = async function () {
      clearStickyStatus();
      const body = {
        enabled: brainMode === "api", /* saving a key must not silently switch the brain */
        provider: apiProv && apiProv.value,
        model: apiModel && apiModel.value,
        url: apiUrl && apiUrl.value,
      };
      if (apiKey && apiKey.value) body.key = apiKey.value;
      apiBtn.disabled = true;
      setStatus("saving API key…");
      try {
        const j = await postCloud(body);
        if (apiKey) apiKey.value = "";
        if (j.has_key) {
          setStatus("Key saved for " + (j.label || "") + " / " + (j.model || "") + " · press the API segment in the brain switch to run on the cloud. Local stays the default.");
        } else {
          setStickyStatus("Save key failed — " + (j.error || j.hint || "paste a key in the row above first"));
        }
      } catch (e) {
        setStickyStatus("Save key failed — " + ((e && e.message) ? e.message : e));
      } finally {
        apiBtn.disabled = false;
        paintBrain(lastHealth.cloud || {});
      }
    };
  }
  if (apiKey) {
    apiKey.addEventListener("keydown", function (ev) {
      if (ev.key === "Enter") { ev.preventDefault(); if (apiBtn) apiBtn.click(); }
    });
  }
  refreshCloud().catch(function () {});
  img.onchange = () => {
    const f = img.files && img.files[0];
    if (!f) {
      pendingImage = null;
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      pendingImage = reader.result;
    };
    reader.readAsDataURL(f);
  };
  if (stopBtn) stopBtn.onclick = function () { stopStream("stopped by user — the answer above may be incomplete"); };
  function setSending(on) {
    if (stopBtn) stopBtn.disabled = !on;
    if (sendBtn) sendBtn.disabled = !!on;
  }
  function failBubble(b, text) {
    if (b) {
      b.classList.add("failed");
      b.textContent = (b.textContent || "").trim() ? b.textContent + "\n\n⚠ " + text : "⚠ " + text;
    }
    setStatus(text, true);
    if (msg) msg.focus();
  }

  async function sendChat() {
    const text = (msg && msg.value ? msg.value : "").trim();
    if (!text && !pendingImage) return;
    if (activeAbort) {
      setStatus("still answering — press Stop before sending again", true);
      return;
    }
    if (msg) msg.value = "";
    const content = pendingImage
      ? [
          { type: "text", text: text },
          { type: "image_url", image_url: { url: pendingImage } },
        ]
      : text;
    pendingImage = null;
    if (img) img.value = "";
    bubble("user", text || "[image]");
    chatHistory.push({ role: "user", content });
    const beforeN = chatHistory.length;
    lastPruneDropped = false;
    chatHistory = pruneHistory(chatHistory);
    paintCtx(lastPruneDropped || beforeN > MAX_MSGS);

    const b = bubble("assistant", "");
    b.classList.add("streaming");
    const ctl = new AbortController();
    activeAbort = ctl;
    setSending(true);
    let idleTimer = null, capTimer = null, timedOut = false, stopped = false, parseFails = 0, done = false;
    const arm = function () {
      if (idleTimer) clearTimeout(idleTimer);
      idleTimer = setTimeout(function () { timedOut = true; try { ctl.abort(); } catch (_) {} }, STREAM_IDLE_MS);
    };
    const say = function (delta) {
      if (!delta) return;
      b.textContent += delta;
      log.scrollTop = log.scrollHeight;
    };
    try {
      const h = await refreshHealth();
      const apiOn = brainMode === "api";
      if (!apiOn && h && h.brain !== "ready" && h.brain !== "booting") {
        setStatus("local engine is " + (h.brain || "down") + " — booting the selected model, then asking…");
        await boot(models.value);
      }
      const body = {
        messages: chatHistory,
        model: models.value || undefined,
        tools: document.getElementById("tools").checked,
        stream: true,
        max_tokens: MAX_TOKENS,
        use_api: apiOn,
      };
      const r = await fetch("/api/chat", {
        method: "POST",
        headers: headers(),
        body: JSON.stringify(body),
        signal: ctl.signal,
      });
      if (!r.ok) {
        const j = await r.json().catch(function () { return {}; });
        const why = j.error || j.hint || ("HTTP " + r.status);
        failBubble(b, "engine error " + r.status + " — " + why +
          (r.status === 401
            ? " · this page has no token: reopen the console from its launcher link"
            : " · press Scan drives then Boot LLM, and check the health box"));
        return;
      }
      const ctype = r.headers.get("content-type") || "";
      if (ctype.includes("event-stream") && r.body && r.body.getReader) {
        const reader = r.body.getReader();
        const dec = new TextDecoder();
        let buf = "";
        arm();
        capTimer = setTimeout(function () { timedOut = true; try { ctl.abort(); } catch (_) {} }, STREAM_CAP_MS);
        const handle = function (raw) {
          const line = raw.replace(/^data:\s*/, "").trim();
          if (!line) return;
          try {
            const evn = JSON.parse(line);
            if (evn.delta) say(evn.delta);
            if (evn.traces) renderTraces(evn.traces);
            if (evn.type === "brain") markBrain(b, evn);
            if (evn.error) failBubble(b, "engine error — " + evn.error);
            if (evn.type === "done") {
              markBrain(b, evn);
              done = true;
              if (b.textContent) chatHistory.push({ role: "assistant", content: b.textContent });
            }
          } catch (_) {
            /* A malformed event used to vanish silently and the answer just stopped mid-sentence. */
            parseFails += 1;
          }
        };
        while (true) {
          const chunk = await reader.read();
          arm();
          if (chunk.done) break;
          buf += dec.decode(chunk.value, { stream: true });
          const parts = buf.split("\n\n");
          buf = parts.pop();
          for (const p of parts) handle(p);
        }
        handle(buf); /* a last event that never got its blank-line terminator */
      } else {
        const j = await r.json().catch(function () { return {}; });
        if (j.error && !j.text) {
          failBubble(b, "engine error — " + j.error);
        } else {
          b.textContent = j.text || "";
          markBrain(b, j);
          if (j.text) chatHistory.push({ role: "assistant", content: j.text });
        }
        if (j.traces) renderTraces(j.traces);
      }
    } catch (e) {
      stopped = !!ctl.__stopped;
      if (stopped && !timedOut) {
        b.classList.add("stopped");
        b.textContent += "\n[stopped by user]";
      } else if (timedOut) {
        b.classList.add("failed");
        b.textContent += "\n⚠ engine not responding — no output for " + Math.round(STREAM_IDLE_MS / 1000) +
          "s, so this answer was stopped. Check the health box, press Boot LLM, then ask again.";
        setStatus("engine not responding — no output for " + Math.round(STREAM_IDLE_MS / 1000) + "s", true);
      } else if (e && e.name === "AbortError") {
        b.classList.add("stopped");
      } else {
        failBubble(b, "chat request failed — " + ((e && e.message) ? e.message : e) +
          " · is the console window still running? (answers are kept in the transcript)");
      }
      const partial = (b.textContent || "").replace(/\[stopped by user\]/g, "").replace(/⚠[^\n]*/g, "").trim();
      if (!done && partial && (stopped || timedOut)) {
        chatHistory.push({ role: "assistant", content: partial + " [answer was cut short]" });
      }
    } finally {
      if (idleTimer) clearTimeout(idleTimer);
      if (capTimer) clearTimeout(capTimer);
      if (parseFails) {
        b.classList.add("failed");
        b.textContent += "\n⚠ stream error — " + parseFails + " malformed event(s) skipped, so this answer may be incomplete.";
        setStatus("stream error — " + parseFails + " malformed event(s) from the engine", true);
      }
      b.classList.remove("streaming");
      if (!(b.textContent || "").trim() && !b.classList.contains("failed") && !b.classList.contains("stopped")) {
        /* The old failure mode: an empty bubble and a rejection in the console. */
        b.classList.add("failed");
        b.textContent = "⚠ the engine sent no text for this turn — press Boot LLM (health box says engine=ready when it is up) and ask again.";
        setStatus("engine returned no text for this turn", true);
      }
      activeAbort = null;
      setSending(false);
      chatHistory = pruneHistory(chatHistory);
      paintCtx(false);
      await persistHistory();
      await refreshHealth();
    }
  }

  form.onsubmit = function (ev) {
    ev.preventDefault();
    sendChat();
  };

  let wsBrowse = "";
  async function refreshWorkspace() {
    const ul = document.getElementById("ws");
    const box = document.getElementById("ws-mounts");
    const st = document.getElementById("ws-status");
    const q = wsBrowse ? ("?path=" + encodeURIComponent(wsBrowse)) : "";
    let r, j = {};
    try {
      r = await fetch("/api/workspace" + q, { headers: headers(), cache: "no-store" });
      j = await r.json().catch(function () { return {}; });
    } catch (e) {
      if (st) st.textContent = "workspace unreachable — " + ((e && e.message) ? e.message : e);
      return;
    }
    if (!r.ok || j.ok === false) {
      /* 403 "denied" used to render as an empty panel, which reads exactly like "no folders". */
      const why = j.error || ("HTTP " + r.status);
      const where = wsBrowse || j.path || "that path";
      if (ul) ul.innerHTML = "";
      if (box) {
        box.innerHTML = "";
        const row = document.createElement("div");
        row.className = "ws-mount ws-error";
        row.textContent = r.status === 403
          ? "denied: " + where + " is not inside a mapped root — add it under Add access first"
          : "workspace error " + r.status + " · " + why + (j.hint ? " · " + j.hint : "");
        box.appendChild(row);
      }
      if (st) {
        st.textContent = r.status === 403 ? ("denied (403) · " + where) : ("workspace " + r.status + " · " + why);
        st.classList.add("warn");
      }
      return;
    }
    if (st) st.classList.remove("warn");
    if (box) {
      box.innerHTML = "";
      (j.mounts || []).forEach((m) => {
        const row = document.createElement("div");
        row.className = "ws-mount";
        const p = document.createElement("span");
        p.className = "p";
        p.textContent = m.path;
        p.title = (m.label || "") + " · " + (m.source || "") + " — click to browse this folder in the panel";
        p.onclick = () => {
          /* Browse in the panel. This used to type "list_dir <path>" over whatever was in the composer. */
          wsBrowse = m.path;
          refreshWorkspace();
        };
        row.appendChild(p);
        ["read", "write", "search"].forEach((k) => {
          const t = document.createElement("span");
          t.className = "tag " + (m[k] ? "on" : "off");
          t.textContent = k === "search" ? "find" : k;
          t.title = (m[k] ? "allowed: " : "not allowed: ") + k + " (" + m.path + ")";
          t.setAttribute("aria-label", k + (m[k] ? " allowed" : " not allowed"));
          row.appendChild(t);
        });
        if (m.pinned) {
          const pin = document.createElement("span");
          pin.className = "tag on";
          pin.textContent = "pin";
          row.appendChild(pin);
        } else if (m.status !== "revoked") {
          const rm = document.createElement("button");
          rm.type = "button";
          rm.textContent = "Remove";
          rm.onclick = async () => {
            let rr;
            try {
              rr = await fetch("/api/workspace", {
                method: "POST",
                headers: headers(),
                body: JSON.stringify({ action: "remove", path: m.path }),
              });
            } catch (e) {
              setStatus("remove failed — " + ((e && e.message) ? e.message : e), true);
              return;
            }
            const rj = await rr.json().catch(function () { return {}; });
            if (!rr.ok || rj.ok === false) {
              setStatus("remove failed — " + (rj.error || ("HTTP " + rr.status)), true);
              return;
            }
            wsBrowse = "";
            refreshWorkspace();
          };
          row.appendChild(rm);
        }
        if (m.status === "revoked") {
          const t = document.createElement("span");
          t.className = "tag off";
          t.textContent = "off";
          row.appendChild(t);
        }
        box.appendChild(row);
      });
    }
    if (st) {
      st.textContent = (j.n_live || 0) + " live maps · browsing " + (j.path || "") +
        (j.truncated || (j.n && j.entries && j.n > j.entries.length)
          ? " · showing first " + (j.entries || []).length + " of " + (j.n || "?")
          : "");
    }
    if (!ul) return;
    ul.innerHTML = "";
    (j.entries || []).forEach((e) => {
      const li = document.createElement("li");
      li.textContent = (e.dir ? "📁 " : "📄 ") + e.name;
      li.onclick = () => {
        if (e.dir) {
          wsBrowse = e.path || ((j.path || "") + "\\" + e.name);
          refreshWorkspace();
          fillComposerIfEmpty("list_dir " + wsBrowse);
        } else {
          fillComposerIfEmpty("Read file " + (e.path || e.name) + " and summarize.");
        }
        if (msg) msg.focus();
      };
      ul.appendChild(li);
    });
  }
  const wsAdd = document.getElementById("ws-add");
  if (wsAdd) {
    wsAdd.onclick = async () => {
      const path = (document.getElementById("ws-path") || {}).value || "";
      const st = document.getElementById("ws-status");
      wsAdd.disabled = true;
      setStatus("adding workspace access to " + (path || "…"));
      try {
        const r = await fetch("/api/workspace", {
          method: "POST",
          headers: headers(),
          body: JSON.stringify({
            action: "add",
            path,
            read: !!(document.getElementById("ws-read") || {}).checked,
            write: !!(document.getElementById("ws-write") || {}).checked,
            search: !!(document.getElementById("ws-search") || {}).checked,
          }),
        });
        const j = await r.json().catch(() => ({}));
        if (!r.ok || j.ok === false) {
          const why = "failed: " + (j.error || ("HTTP " + r.status)) + (j.hint ? " · " + j.hint : "");
          if (st) st.textContent = why;
          setStatus("add access " + why, true);
          return;
        }
        if (st) st.textContent = "added " + (j.path || path);
        setStatus("workspace access added: " + (j.path || path));
        wsBrowse = j.path || path;
        refreshWorkspace();
      } catch (e) {
        setStatus("add access failed — " + ((e && e.message) ? e.message : e), true);
      } finally {
        wsAdd.disabled = false;
      }
    };
  }
  async function refreshLimbs() {
    const box = document.getElementById("limbs");
    if (!box) return;
    const r = await fetch("/api/tools", { headers: headers(), cache: "no-store" });
    const j = await r.json().catch(() => ({}));
    box.innerHTML = "";
    (j.names || []).forEach((n) => {
      const b = document.createElement("button");
      b.type = "button";
      b.textContent = n;
      b.onclick = async () => {
        let args = {};
        if (n === "web_search") args = { q: prompt("search q") || "LYGO" };
        else if (n === "web_fetch") args = { url: prompt("https url") || "https://chatagent.ca/" };
        else if (n === "list_dir") args = { path: "." };
        else if (n === "shell") args = { cmd: prompt("workspace command") || "dir" };
        else if (n === "now" || n === "whoami" || n === "kernel_status" || n === "todo_list" || n === "notepad_list" || n === "skill_list" || n === "self_check" || n === "steward_map") args = {};
        else {
          msg.value = "Use tool " + n + " as needed: ";
          msg.focus();
          return;
        }
        const res = await fetch("/api/limb", { method: "POST", headers: headers(), body: JSON.stringify({ name: n, arguments: args }) });
        const out = await res.json().catch(function () { return {}; });
        limb.textContent = JSON.stringify(out, null, 2);
        const bad = !res.ok || out.ok === false || !!out.error;
        setStatus("limb " + n + (bad ? " failed — " + (out.error || ("HTTP " + res.status)) : " finished"), bad);
        if (out.traces) renderTraces(out.traces);
      };
      box.appendChild(b);
    });
  }
  async function persistHistory() {
    /* sessionStorage is only this tab's draft cache. The server session is the transcript of
       record (see loadContinuity), so a failure here has to be visible. */
    try {
      sessionStorage.setItem(HIST_KEY, JSON.stringify(chatHistory.slice(-40)));
    } catch (_) {}
    try {
      const r = await fetch("/api/session", { method: "POST", headers: headers(), body: JSON.stringify({ messages: chatHistory }) });
      if (!r.ok) setStatus("server session save failed (" + r.status + ") — this transcript is only in this tab now", true);
    } catch (e) {
      setStatus("server session save failed — " + ((e && e.message) ? e.message : e) + " · transcript is only in this tab", true);
    }
  }
  async function loadContinuity() {
    /* Server-side truth: GET /api/session decides what the transcript is, so a second tab cannot
       disagree with the engine about the conversation. sessionStorage is the draft cache. */
    try {
      const s = await fetch("/api/session", { headers: headers(), cache: "no-store" });
      const j = await s.json().catch(function () { return {}; });
      if (!s.ok) throw new Error("HTTP " + s.status);
      const msgs = Object.prototype.toString.call(j.messages) === "[object Array]" ? j.messages : [];
      if (msgs.length) {
        chatHistory = msgs.slice(-40).map((m) => ({ role: m.role === "user" ? "user" : "assistant", content: m.content }));
        restoredFromServer = msgs.length;
        renderHistory();
        statusSoft("session restored from the engine · " + msgs.length + " messages");
      } else {
        let draft = [];
        try {
          const raw = sessionStorage.getItem(HIST_KEY);
          if (raw) draft = JSON.parse(raw) || [];
        } catch (_) { draft = []; }
        if (draft.length) {
          chatHistory = draft;
          renderHistory();
          statusSoft("no server session yet — restored this tab's draft (" + draft.length + " messages); it is saved on the next send");
        } else {
          chatHistory = [];
          renderHistory();
        }
      }
    } catch (e) {
      /* Keep the draft rather than showing an empty transcript, but say the server was not read. */
      setStickyStatus("could not read the engine's session — " + ((e && e.message) ? e.message : e) + " · the transcript below may be this tab's draft only");
      try {
        const raw = sessionStorage.getItem(HIST_KEY);
        if (raw && !chatHistory.length) {
          chatHistory = JSON.parse(raw) || [];
          renderHistory();
        }
      } catch (_) {}
    }
    paintCtx(false);
    try {
      const soul = await (await fetch("/api/soul", { headers: headers(), cache: "no-store" })).json();
      const ident = await (await fetch("/api/identity", { headers: headers(), cache: "no-store" })).json();
      const mem = await (await fetch("/api/memory", { headers: headers(), cache: "no-store" })).json();
      const se = document.getElementById("soul-edit");
      const ie = document.getElementById("id-edit");
      const me = document.getElementById("mem-edit");
      if (se) se.value = soul.text || "";
      if (ie) ie.value = ident.text || "";
      if (me) me.value = mem.memory_md || "";
      const st = document.getElementById("cont-status");
      if (st) st.textContent = "SOUL " + ((soul.text || "").length) + "c · ID " + ((ident.text || "").length) + "c · MEMORY " + ((mem.memory_md || "").length) + "c";
    } catch (_) {}
  }
  const contTabs = Array.prototype.slice.call(document.querySelectorAll("[data-cont]"));
  function selectContTab(btn, focus) {
    contTabs.forEach(function (b) {
      const on = b === btn;
      b.classList.toggle("on", on);
      /* Complete the tab pattern the markup declares: role=tab needs aria-selected + roving tabindex. */
      b.setAttribute("aria-selected", on ? "true" : "false");
      b.tabIndex = on ? 0 : -1;
      const pane = document.getElementById("pane-" + b.getAttribute("data-cont"));
      if (pane) pane.hidden = !on;
    });
    if (focus && btn) btn.focus();
  }
  contTabs.forEach(function (btn, i) {
    btn.onclick = function () { selectContTab(btn, false); };
    btn.onkeydown = function (ev) {
      const k = ev.key;
      if (k !== "ArrowRight" && k !== "ArrowLeft" && k !== "Home" && k !== "End") return;
      ev.preventDefault();
      let next = i;
      if (k === "ArrowRight") next = (i + 1) % contTabs.length;
      if (k === "ArrowLeft") next = (i - 1 + contTabs.length) % contTabs.length;
      if (k === "Home") next = 0;
      if (k === "End") next = contTabs.length - 1;
      selectContTab(contTabs[next], true);
    };
  });
  async function saveCont(kind) {
    const se = document.getElementById("soul-edit");
    const ie = document.getElementById("id-edit");
    const me = document.getElementById("mem-edit");
    const st = document.getElementById("cont-status");
    const path = kind === "soul" ? "/api/soul" : kind === "id" ? "/api/identity" : "/api/memory";
    const text = kind === "soul" ? (se && se.value) : kind === "id" ? (ie && ie.value) : (me && me.value);
    const r = await fetch(path, { method: "POST", headers: headers(), body: JSON.stringify({ text }) });
    const j = await r.json().catch(() => ({}));
    if (st) st.textContent = j.ok ? (kind + " saved") : ("save failed " + (j.error || r.status));
  }
  const ss = document.getElementById("soul-save");
  if (ss) ss.onclick = () => saveCont("soul");
  const ids = document.getElementById("id-save");
  if (ids) ids.onclick = () => saveCont("id");
  const ms = document.getElementById("mem-save");
  if (ms) ms.onclick = () => saveCont("mem");
  const ns = document.getElementById("new-session");
  if (ns) {
    ns.onclick = async function () {
      if (!confirmNewChat("new session")) return;
      await resetSession("New session");
    };
  }
  const wsr = document.getElementById("ws-refresh");
  if (wsr) wsr.onclick = refreshWorkspace;

  async function refreshSkills() {
    const box = document.getElementById("skills-list");
    if (!box) return;
    const r = await fetch("/api/skills", { headers: headers(), cache: "no-store" });
    const j = await r.json().catch(() => ({}));
    box.innerHTML = "";
    (j.skills || []).forEach((s) => {
      const row = document.createElement("label");
      row.className = "skill-row";
      const ck = document.createElement("input");
      ck.type = "checkbox";
      ck.checked = !!s.enabled;
      ck.onchange = async () => {
        await fetch("/api/skills", {
          method: "POST",
          headers: headers(),
          body: JSON.stringify({ action: ck.checked ? "enable" : "disable", slug: s.slug }),
        });
      };
      const name = document.createElement("span");
      name.className = "sn";
      name.textContent = s.slug;
      name.title = s.description || "";
      name.onclick = (ev) => {
        ev.preventDefault();
        msg.value = "Invoke skill " + s.slug + " — read the SKILL.md and follow it.";
        msg.focus();
      };
      const src = document.createElement("span");
      src.className = "src";
      src.textContent = s.source || "";
      row.appendChild(ck);
      row.appendChild(name);
      row.appendChild(src);
      box.appendChild(row);
    });
  }
  async function paintHub(src, q) {
    const hub = document.getElementById("skills-hub");
    if (hub) hub.textContent = "SkillHub…";
    const r = await fetch("/api/skills?src=" + encodeURIComponent(src) + "&q=" + encodeURIComponent(q || ""), { headers: headers(), cache: "no-store" });
    const j = await r.json().catch(() => ({}));
    if (!hub) return;
    hub.innerHTML = "";
    const cap = document.createElement("div");
    cap.className = "src";
    cap.textContent = (j.n || 0) + " on SkillHub · " + (j.hub || "");
    hub.appendChild(cap);
    (j.hits || []).slice(0, 24).forEach((h) => {
      const d = document.createElement("div");
      const t = document.createElement("span");
      const ch = h.channel === "full_zip" ? "FULL" : "tentacle";
      t.textContent = ch + " · " + (h.display || h.slug) + " — " + (h.summary || "").slice(0, 72);
      const b = document.createElement("button");
      b.type = "button";
      b.textContent = h.channel === "full_zip" ? "Install FULL" : "Install";
      b.onclick = async () => {
        b.textContent = "…";
        const action = h.channel === "full_zip" ? "install_full" : "skillhub_install";
        const res = await fetch("/api/skills", {
          method: "POST",
          headers: headers(),
          body: JSON.stringify({ action: action, slug: h.slug, full: h.channel === "full_zip" }),
        });
        const out = await res.json().catch(() => ({}));
        b.textContent = out.ok ? "on" : (out.error || "fail");
        limb.textContent = JSON.stringify(out, null, 2);
        setStatus("skill install " + (out.ok ? "ok: " + h.slug : "failed: " + (out.error || res.status)), !out.ok);
        await refreshSkills();
      };
      d.appendChild(t);
      d.appendChild(b);
      hub.appendChild(d);
    });
    if (!(j.hits || []).length) hub.textContent = j.error || "no SkillHub hits";
  }
  const skSearch = document.getElementById("skills-search");
  if (skSearch) {
    skSearch.onclick = async () => {
      const q = (document.getElementById("skills-q") || {}).value || "";
      await paintHub("hub", q);
    };
  }
  const skHub = document.getElementById("skills-hub-btn");
  if (skHub) skHub.onclick = () => paintHub("hub", (document.getElementById("skills-q") || {}).value || "");
  const skFull = document.getElementById("skills-full-btn");
  if (skFull) skFull.onclick = () => paintHub("full", (document.getElementById("skills-q") || {}).value || "");

  const npList = document.getElementById("np-list");
  const npTitle = document.getElementById("np-title");
  const npBody = document.getElementById("np-body");
  const npStatus = document.getElementById("np-status");
  let npId = "scratch";
  let npDirty = false;
  let npTimer = null;

  function npSetStatus(t) {
    if (npStatus) npStatus.textContent = t;
  }

  async function npRefreshList(selectId) {
    if (!npList) return;
    const r = await fetch("/api/notepad", { headers: headers(), cache: "no-store" });
    const j = await r.json().catch(() => ({}));
    const notes = j.notes || [];
    npList.innerHTML = "";
    notes.forEach((n) => {
      const o = document.createElement("option");
      o.value = n.id;
      o.textContent = (n.title || n.id) + (n.id === "scratch" ? " · scratch" : "");
      npList.appendChild(o);
    });
    const want = selectId || npId;
    if ([].some.call(npList.options, (o) => o.value === want)) npList.value = want;
    npId = npList.value || "scratch";
  }

  async function npLoad(id) {
    const nid = id || npId || "scratch";
    const r = await fetch("/api/notepad?id=" + encodeURIComponent(nid), { headers: headers(), cache: "no-store" });
    const j = await r.json().catch(() => ({}));
    if (!j.ok) {
      npSetStatus("missing");
      return;
    }
    npId = j.id;
    if (npTitle) npTitle.value = j.title || j.id;
    if (npBody) npBody.value = j.text || "";
    if (npList) npList.value = j.id;
    npDirty = false;
    npSetStatus("loaded · " + (j.bytes || 0) + "b");
  }

  async function npSave() {
    const body = {
      action: "save",
      id: npId || "scratch",
      title: npTitle ? npTitle.value : "",
      text: npBody ? npBody.value : "",
    };
    const r = await fetch("/api/notepad", { method: "POST", headers: headers(), body: JSON.stringify(body) });
    const j = await r.json().catch(() => ({}));
    if (!j.ok) {
      npSetStatus("save failed · " + (j.error || r.status));
      return;
    }
    npId = j.id;
    npDirty = false;
    npSetStatus("saved · " + (j.bytes || 0) + "b");
    await npRefreshList(npId);
  }

  function npMarkDirty() {
    npDirty = true;
    npSetStatus("unsaved");
    if (npTimer) clearTimeout(npTimer);
    npTimer = setTimeout(() => { npSave(); }, 900);
  }

  if (npList) {
    npList.onchange = async () => {
      if (npDirty) await npSave();
      await npLoad(npList.value);
    };
  }
  if (npTitle) npTitle.oninput = npMarkDirty;
  if (npBody) npBody.oninput = npMarkDirty;
  const npNew = document.getElementById("np-new");
  if (npNew) {
    npNew.onclick = async () => {
      if (npDirty) await npSave();
      const r = await fetch("/api/notepad", {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({ action: "new", title: "Untitled" }),
      });
      const j = await r.json().catch(() => ({}));
      if (j.ok && j.id) {
        npId = j.id;
        await npRefreshList(j.id);
        await npLoad(j.id);
        if (npTitle) { npTitle.focus(); npTitle.select(); }
      }
    };
  }
  const npSaveBtn = document.getElementById("np-save");
  if (npSaveBtn) npSaveBtn.onclick = npSave;
  const npDel = document.getElementById("np-del");
  if (npDel) {
    npDel.onclick = async () => {
      const id = npId || "scratch";
      if (id !== "scratch" && !confirm("Delete this note?")) return;
      const r = await fetch("/api/notepad", {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({ action: "delete", id }),
      });
      const j = await r.json().catch(() => ({}));
      if (!j.ok) {
        npSetStatus("delete failed");
        return;
      }
      npId = "scratch";
      await npRefreshList("scratch");
      await npLoad("scratch");
      npSetStatus(id === "scratch" ? "scratch cleared" : "deleted");
    };
  }
  const npCap = document.getElementById("np-capture");
  if (npCap) {
    npCap.onclick = () => {
      const sel = (window.getSelection && window.getSelection().toString()) || "";
      if (!sel.trim()) {
        npSetStatus("select text in chat first");
        return;
      }
      if (npBody) {
        npBody.value = (npBody.value ? npBody.value.replace(/\s*$/, "\n\n") : "") + sel.trim();
        npMarkDirty();
        npSave();
      }
    };
  }
  const npAsk = document.getElementById("np-ask");
  if (npAsk) {
    npAsk.onclick = () => {
      const title = (npTitle && npTitle.value) || npId || "scratch";
      msg.value = "Look at my notepad notes. Read note id " + (npId || "scratch") + " titled " + title + " and use it.";
      msg.focus();
    };
  }

  (async function start() {
    await refreshHealth();
    await refreshModels();
    await refreshWorkspace();
    await refreshLimbs();
    try { await refreshSkills(); } catch (_) {}
    await loadContinuity();
    try {
      await npRefreshList();
      await npLoad(npId);
    } catch (_) {}
    const h = await refreshHealth();
    if (h && h.brain !== "ready" && h.brain !== "booting" && h.selected && !bootedOnce) {
      bootedOnce = true;
      await boot(h.selected);
    }
    paintCtx(false);
    if (!stickyStatus) {
      const hh = lastHealth || {};
      setStatus((hh.brain === "ready"
        ? ("ready · engine " + (hh.selected || "?") + " · brain " + brainMode.toUpperCase())
        : ("ready · engine=" + (hh.brain || "?") + " — press Scan drives, pick a model, then Boot LLM")) +
        (restoredFromServer ? " · transcript restored from the engine (" + restoredFromServer + " messages)" : ""));
    }
  })();
  setInterval(refreshHealth, 3000);

  const worldLocal = document.getElementById("world-local");
  const worldUtc = document.getElementById("world-utc");
  const worldCities = document.getElementById("world-cities");
  let worldSnap = null;
  async function refreshWorld() {
    try {
      const r = await fetch("/api/world", { cache: "no-store" });
      worldSnap = await r.json();
    } catch (_) {
      return;
    }
    paintWorld();
  }
  function paintWorld() {
    const now = new Date();
    if (worldLocal) {
      worldLocal.textContent = now.toLocaleString(undefined, { weekday: "short", hour: "2-digit", minute: "2-digit", second: "2-digit" });
    }
    if (worldUtc) {
      worldUtc.textContent = "UTC " + now.toISOString().slice(0, 19).replace("T", " ");
    }
    if (!worldCities || !worldSnap || !worldSnap.cities) return;
    worldCities.innerHTML = "";
    worldSnap.cities.forEach((c) => {
      const d = document.createElement("div");
      d.className = "wcity";
      let clock = c.clock || "";
      try {
        clock = now.toLocaleTimeString(undefined, { timeZone: c.tz, hour: "2-digit", minute: "2-digit" });
      } catch (_) {}
      const wx = c.weather || {};
      const line = (wx.c != null ? Math.round(wx.c) + "° " : "") + (wx.label || "");
      d.innerHTML = '<div class="n"></div><div class="t"></div><div class="w"></div>';
      d.querySelector(".n").textContent = c.name;
      d.querySelector(".t").textContent = clock;
      d.querySelector(".w").textContent = line;
      worldCities.appendChild(d);
    });
  }
  refreshWorld();
  setInterval(paintWorld, 1000);
  setInterval(refreshWorld, 120000);
})();
