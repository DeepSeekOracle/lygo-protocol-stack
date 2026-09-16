(function () {
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
  let pendingImage = null;
  let bootedOnce = false;
  let chatHistory = [];
  const HIST_KEY = "lygo_llm_chatHistory";

  function setHealth(j) {
    const err = j.error ? " err=" + j.error : "";
    healthEl.textContent =
      `build=${j.build || "?"} brain=${j.brain || "?"} selected=${j.selected || "—"} models=${j.scan_n || 0} limbs=${(j.tools||[]).length} engine=${j.engine_present} ram=${Math.round((j.ram_avail || 0) / 1e9)}GB${err}`;
  }

  async function refreshHealth() {
    try {
      const r = await fetch("/api/health", { headers: headers() });
      const j = await r.json();
      setHealth(j);
      document.body.dataset.brain = j.brain || "";
      if (typeof j.scan_n === "number" && j.scan_n !== lastScan) {
        lastScan = j.scan_n;
        try { await refreshModels(); } catch (_) {}
      }
      return j;
    } catch (e) {
      healthEl.textContent = "health failed";
      return null;
    }
  }
  async function refreshModels() {
    const r = await fetch("/api/models", { headers: headers(), cache: "no-store" });
    if (!r.ok) {
      limb.textContent = "models " + r.status + " — retry Scan drives (header bar)";
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
    log.scrollTop = log.scrollHeight;
    return d;
  }

  async function boot(id) {
    limb.textContent = "booting " + (id || "selected") + " … first load can take a minute";
    const r = await fetch("/api/boot", {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({ id: id || models.value }),
    });
    const j = await r.json();
    limb.textContent = JSON.stringify(j, null, 2);
    await refreshHealth();
  }

  document.getElementById("scan").onclick = async () => {
    limb.textContent = "scanning…";
    const r = await fetch("/api/scan", { method: "POST", headers: headers(), body: "{}" });
    const j = await r.json();
    limb.textContent = JSON.stringify(
      { n: (j.models || j.registry && j.registry.models || []).length, truncated: j.scan_truncated, roots: j.roots, selected: (j.registry || {}).selected },
      null,
      2
    );
    await refreshModels();
    await refreshHealth();
  };
  document.getElementById("select").onclick = async () => {
    await boot(models.value);
  };
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
  form.onsubmit = async (ev) => {
    ev.preventDefault();
    const text = msg.value.trim();
    if (!text && !pendingImage) return;
    msg.value = "";
    bubble("user", text || "[image]");
    const content = pendingImage
      ? [
          { type: "text", text },
          { type: "image_url", image_url: { url: pendingImage } },
        ]
      : text;
    pendingImage = null;
    img.value = "";
    const h = await refreshHealth();
    if (h && h.brain !== "ready" && h.brain !== "booting") {
      await boot(models.value);
    }
    chatHistory.push({ role: "user", content });
    if (chatHistory.length > 24) chatHistory = chatHistory.slice(-24);
    const body = {
      messages: chatHistory,
      model: models.value || undefined,
      tools: document.getElementById("tools").checked,
      stream: true,
      max_tokens: 768,
    };
    const r = await fetch("/api/chat", { method: "POST", headers: headers(), body: JSON.stringify(body) });
    const b = bubble("assistant", "");
    if ((r.headers.get("content-type") || "").includes("event-stream")) {
      const reader = r.body.getReader();
      const dec = new TextDecoder();
      let buf = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });
        const parts = buf.split("\n\n");
        buf = parts.pop();
        for (const p of parts) {
          const line = p.replace(/^data:\s*/, "").trim();
          if (!line) continue;
          try {
            const evn = JSON.parse(line);
            if (evn.delta) b.textContent += evn.delta;
            if (evn.traces) limb.textContent = JSON.stringify(evn.traces, null, 2);
            if (evn.type === "done" && b.textContent) chatHistory.push({ role: "assistant", content: b.textContent });
          } catch (_) {}
        }
      }
    } else {
      const j = await r.json();
      b.textContent = j.text || j.error || JSON.stringify(j);
      if (j.traces) limb.textContent = JSON.stringify(j.traces, null, 2);
      if (j.text) chatHistory.push({ role: "assistant", content: j.text });
    }
    await refreshHealth();
    await persistHistory();
  };

  async function refreshWorkspace() {
    const ul = document.getElementById("ws");
    if (!ul) return;
    const r = await fetch("/api/workspace", { headers: headers(), cache: "no-store" });
    const j = await r.json().catch(() => ({}));
    ul.innerHTML = "";
    (j.entries || []).forEach((e) => {
      const li = document.createElement("li");
      li.textContent = (e.dir ? "📁 " : "📄 ") + e.name;
      li.onclick = () => {
        msg.value = e.dir ? "list_dir " + e.name : "Read workspace file " + e.name + " and summarize.";
        msg.focus();
      };
      ul.appendChild(li);
    });
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
        else if (n === "now" || n === "whoami" || n === "kernel_status" || n === "todo_list" || n === "notepad_list" || n === "skill_list") args = {};
        else {
          msg.value = "Use tool " + n + " as needed: ";
          msg.focus();
          return;
        }
        const res = await fetch("/api/limb", { method: "POST", headers: headers(), body: JSON.stringify({ name: n, arguments: args }) });
        limb.textContent = JSON.stringify(await res.json(), null, 2);
      };
      box.appendChild(b);
    });
  }
  async function persistHistory() {
    try {
      sessionStorage.setItem(HIST_KEY, JSON.stringify(chatHistory.slice(-40)));
    } catch (_) {}
    try {
      await fetch("/api/session", { method: "POST", headers: headers(), body: JSON.stringify({ messages: chatHistory }) });
    } catch (_) {}
  }
  async function loadContinuity() {
    try {
      const s = await fetch("/api/session", { headers: headers() });
      const j = await s.json();
      if (j.messages && j.messages.length) {
        chatHistory = j.messages;
        log.innerHTML = "";
        chatHistory.forEach((m) => bubble(m.role === "user" ? "user" : "assistant", typeof m.content === "string" ? m.content : JSON.stringify(m.content)));
      } else {
        const raw = sessionStorage.getItem(HIST_KEY);
        if (raw) chatHistory = JSON.parse(raw);
      }
    } catch (_) {}
    try {
      const soul = await (await fetch("/api/soul", { headers: headers() })).json();
      const mem = await (await fetch("/api/memory", { headers: headers() })).json();
      const pre = document.getElementById("soul-preview");
      if (pre) pre.textContent = ((soul.text || "").slice(0, 400) + "\n---\n" + (mem.memory_md || "").slice(-400)).trim();
    } catch (_) {}
  }
  const ns = document.getElementById("new-session");
  if (ns) {
    ns.onclick = async () => {
      chatHistory = [];
      log.innerHTML = "";
      sessionStorage.removeItem(HIST_KEY);
      await fetch("/api/session", { method: "POST", headers: headers(), body: JSON.stringify({ new: true }) });
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
  const skSearch = document.getElementById("skills-search");
  if (skSearch) {
    skSearch.onclick = async () => {
      const q = (document.getElementById("skills-q") || {}).value || "";
      const hub = document.getElementById("skills-hub");
      if (hub) hub.textContent = "searching ClawHub…";
      const r = await fetch("/api/skills?q=" + encodeURIComponent(q || "lygo"), { headers: headers(), cache: "no-store" });
      const j = await r.json().catch(() => ({}));
      if (!hub) return;
      hub.innerHTML = "";
      (j.hits || []).forEach((h) => {
        const d = document.createElement("div");
        const t = document.createElement("span");
        t.textContent = (h.display || h.slug) + " — " + (h.summary || "").slice(0, 80);
        const b = document.createElement("button");
        b.type = "button";
        b.textContent = "Install";
        b.onclick = async () => {
          b.textContent = "…";
          const res = await fetch("/api/skills", {
            method: "POST",
            headers: headers(),
            body: JSON.stringify({ action: "install", slug: h.slug }),
          });
          const out = await res.json().catch(() => ({}));
          b.textContent = out.ok ? "on" : "fail";
          limb.textContent = JSON.stringify(out, null, 2);
          await refreshSkills();
        };
        d.appendChild(t);
        d.appendChild(b);
        hub.appendChild(d);
      });
      if (!(j.hits || []).length) hub.textContent = j.error || "no hits";
    };
  }

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
    if (h && h.brain !== "ready" && h.selected && !bootedOnce) {
      bootedOnce = true;
      await boot(h.selected);
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
