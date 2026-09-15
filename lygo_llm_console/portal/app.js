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
  }
  captureTokenFromUrl();
  function token() { return sessionStorage.getItem(TOKEN_KEY) || ""; }
  function headers() {
    const h = { "Content-Type": "application/json", "X-LYGO-LLM-Token": token() };
    return h;
  }
  const healthEl = document.getElementById("health");
  const log = document.getElementById("log");
  const form = document.getElementById("form");
  const msg = document.getElementById("msg");
  const models = document.getElementById("models");
  const limb = document.getElementById("limb-out");
  const img = document.getElementById("img");
  let pendingImage = null;

  async function refreshHealth() {
    try {
      const r = await fetch("/api/health", { headers: headers() });
      const j = await r.json();
      healthEl.textContent = `brain=${j.brain || "?"} physics=${j.physics} ollama_port=${j.ollama_port_open} ram=${Math.round((j.ram_avail||0)/1e9)}GB`;
    } catch (e) {
      healthEl.textContent = "health failed";
    }
  }
  async function refreshModels() {
    const r = await fetch("/api/models", { headers: headers() });
    if (!r.ok) return;
    const j = await r.json();
    models.innerHTML = "";
    (j.models || []).forEach((m) => {
      const o = document.createElement("option");
      o.value = m.id;
      o.textContent = `${m.id} [${m.kind||"?"} ${m.runnable?"ok":m.status}]`;
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

  document.getElementById("scan").onclick = async () => {
    limb.textContent = "scanning…";
    const r = await fetch("/api/scan", { method: "POST", headers: headers(), body: "{}" });
    const j = await r.json();
    limb.textContent = JSON.stringify({ n: (j.models||[]).length, truncated: j.scan_truncated }, null, 2);
    await refreshModels();
    await refreshHealth();
  };
  document.getElementById("select").onclick = async () => {
    const id = models.value;
    const r = await fetch("/api/select", { method: "POST", headers: headers(), body: JSON.stringify({ id }) });
    const j = await r.json();
    limb.textContent = JSON.stringify(j, null, 2);
    await refreshHealth();
  };
  img.onchange = () => {
    const f = img.files && img.files[0];
    if (!f) { pendingImage = null; return; }
    const reader = new FileReader();
    reader.onload = () => { pendingImage = reader.result; };
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
    const body = {
      messages: [{ role: "user", content }],
      tools: document.getElementById("tools").checked,
      stream: true,
      max_tokens: 512,
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
          } catch (_) {}
        }
      }
    } else {
      const j = await r.json();
      b.textContent = j.text || j.error || JSON.stringify(j);
      if (j.traces) limb.textContent = JSON.stringify(j.traces, null, 2);
    }
    await refreshHealth();
  };
  refreshHealth();
  refreshModels();
  setInterval(refreshHealth, 8000);
})();
