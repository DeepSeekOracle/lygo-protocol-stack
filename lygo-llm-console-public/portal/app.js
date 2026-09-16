(function () {
  const TOKEN_KEY = "lygo_llm_token";
  function captureTokenFromUrl() {
    const u = new URL(location.href);
    const t = u.searchParams.get("t") || u.searchParams.get("token");
    if (t) {
      sessionStorage.setItem(TOKEN_KEY, t);
      u.searchParams.delete("t");
      u.searchParams.delete("token");
      history.replaceState({}, "", u.pathname + u.search);
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
    return { "Content-Type": "application/json", "X-LYGO-LLM-Token": token() };
  }
  const healthEl = document.getElementById("health");
  const log = document.getElementById("log");
  const form = document.getElementById("form");
  const msg = document.getElementById("msg");
  const models = document.getElementById("models");
  const limb = document.getElementById("limb-out");
  const img = document.getElementById("img");
  let pendingImage = null;
  let bootedOnce = false;
  let history = [];

  function setHealth(j) {
    const err = j.error ? " err=" + j.error : "";
    healthEl.textContent =
      `brain=${j.brain || "?"} selected=${j.selected || "—"} models=${j.scan_n || 0} engine=${j.engine_present} ram=${Math.round((j.ram_avail || 0) / 1e9)}GB${err}`;
  }

  async function refreshHealth() {
    try {
      const r = await fetch("/api/health", { headers: headers() });
      const j = await r.json();
      setHealth(j);
      return j;
    } catch (e) {
      healthEl.textContent = "health failed";
      return null;
    }
  }
  async function refreshModels() {
    const r = await fetch("/api/models", { headers: headers() });
    if (!r.ok) {
      limb.textContent = "models " + r.status + " — retry Scan";
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
    history.push({ role: "user", content });
    if (history.length > 24) history = history.slice(-24);
    const body = {
      messages: history,
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
            if (evn.type === "done" && b.textContent) history.push({ role: "assistant", content: b.textContent });
          } catch (_) {}
        }
      }
    } else {
      const j = await r.json();
      b.textContent = j.text || j.error || JSON.stringify(j);
      if (j.traces) limb.textContent = JSON.stringify(j.traces, null, 2);
      if (j.text) history.push({ role: "assistant", content: j.text });
    }
    await refreshHealth();
  };

  async function refreshWorkspace() {
    const ul = document.getElementById("ws");
    if (!ul) return;
    const r = await fetch("/api/workspace", { headers: headers() });
    const j = await r.json();
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
    const r = await fetch("/api/tools", { headers: headers() });
    const j = await r.json();
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
        else if (n === "now" || n === "whoami" || n === "kernel_status" || n === "todo_list") args = {};
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
  const wsr = document.getElementById("ws-refresh");
  if (wsr) wsr.onclick = refreshWorkspace;

  (async function start() {
    await refreshHealth();
    await refreshModels();
    await refreshWorkspace();
    await refreshLimbs();
    const h = await refreshHealth();
    if (h && h.brain !== "ready" && h.selected && !bootedOnce) {
      bootedOnce = true;
      await boot(h.selected);
    }
  })();
  setInterval(refreshHealth, 3000);
})();
