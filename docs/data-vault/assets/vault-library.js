(() => {
  "use strict";
  const $ = (s, el = document) => el.querySelector(s);
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const state = { type: "all", cat: "all", q: "", limit: 36 };
  let data = null;

  const catOrder = ["Foundational","Protocol","Seals","Ecosystem","Lore & Books"];
  const catLabel = c => c === "Lore & Books" ? "Lore & Books" : c;

  function formatBody(text) {
    const lines = String(text || "").replace(/\r\n?/g, "\n").split("\n");
    let out = [], para = [], list = [], code = false, codeBuf = [];
    const flushPara = () => {
      if (!para.length) return;
      out.push("<p>" + para.join(" ") + "</p>");
      para = [];
    };
    const flushList = () => {
      if (!list.length) return;
      out.push("<ul>" + list.map(x => "<li>" + x + "</li>").join("") + "</ul>");
      list = [];
    };
    const flush = () => { flushPara(); flushList(); };
    for (const raw of lines) {
      const line = raw.replace(/\t/g, "    ");
      if (/^\s*```/.test(line)) {
        flush();
        if (!code) { code = true; codeBuf = []; } else {
          out.push("<pre>" + esc(codeBuf.join("\n")) + "</pre>");
          code = false; codeBuf = [];
        }
        continue;
      }
      if (code) { codeBuf.push(line); continue; }
      if (!line.trim()) { flush(); continue; }
      const h = line.match(/^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$/);
      if (h) { flush(); out.push("<h3>" + esc(h[2]) + "</h3>"); continue; }
      const li = line.match(/^\s*[-*•]\s+(.+)$/);
      if (li) { flushPara(); list.push(esc(li[1])); continue; }
      flushList();
      para.push(esc(line.trim()));
    }
    flush();
    if (code && codeBuf.length) out.push("<pre>" + esc(codeBuf.join("\n")) + "</pre>");
    return out.join("\n");
  }

  function paperCard(p) {
    return `<article class="card" data-kind="paper" data-slug="${esc(p.slug)}">
      <div class="card-top"><span class="cat">${esc(catLabel(p.category))}</span><span class="kind">FULL TEXT</span></div>
      <h3>${esc(p.title)}</h3>
      <p>${esc(p.excerpt)}</p>
      <div class="meta"><span>${p.words.toLocaleString()} words</span><span>${esc(p.date)}</span><span>${esc(p.sha12)}</span></div>
      <button class="open" aria-label="Read full paper: ${esc(p.title)}"></button>
    </article>`;
  }

  function chatCard(c) {
    const tags = (c.tags || []).slice(0, 3).map(t => `<span class="tag">${esc(t)}</span>`).join("");
    return `<article class="card grok" data-kind="chat" data-chat="${esc(c.id)}">
      <div class="card-top"><span class="cat">Grok excerpt</span><span class="kind">EXCERPT</span></div>
      <h3>${esc(c.title)}</h3>
      <p>${esc(c.excerpt)}</p>
      <div class="tags">${tags}</div>
      <div class="meta"><span>${esc(c.source)}</span></div>
      <button class="open" aria-label="Read Grok excerpt: ${esc(c.title)}"></button>
    </article>`;
  }

  function filtered() {
    if (!data) return [];
    const q = state.q.trim().toLowerCase();
    const hits = (text) => !q || String(text || "").toLowerCase().includes(q);
    let papers = state.type === "chat" ? [] : data.papers.filter(p =>
      (state.cat === "all" || p.category === state.cat) &&
      (hits(p.title) || hits(p.excerpt) || hits(p.category) || hits(p.source))
    );
    let chats = state.type === "paper" ? [] : data.chats.filter(c =>
      (state.cat === "all" || state.cat === "Grok exchanges") &&
      (hits(c.title) || hits(c.excerpt) || hits(c.source) || (c.tags || []).some(hits))
    );
    return [...papers.map(p => ({kind:"paper", v:p})), ...chats.map(c => ({kind:"chat", v:c}))];
  }

  function render() {
    const items = filtered();
    const shown = items.slice(0, state.limit);
    $("#results").innerHTML = shown.length ? shown.map(x => x.kind === "paper" ? paperCard(x.v) : chatCard(x.v)).join("") : `<div class="empty">No entries match that filter.</div>`;
    $("#result-count").textContent = `${items.length.toLocaleString()} ${items.length === 1 ? "entry" : "entries"}`;
    $("#more").style.display = items.length > shown.length ? "flex" : "none";
    $("#results").querySelectorAll(".open").forEach((btn, i) => {
      btn.addEventListener("click", () => {
        const x = shown[i];
        x.kind === "paper" ? openPaper(x.v) : openChat(x.v);
      });
    });
    document.querySelectorAll(".tab").forEach(t => t.classList.toggle("on", t.dataset.type === state.type));
    document.querySelectorAll(".chip").forEach(c => c.classList.toggle("on", c.dataset.cat === state.cat));
  }

  function openPaper(p) {
    const shell = $("#reader");
    shell.classList.add("open");
    document.body.style.overflow = "hidden";
    $("#r-side").innerHTML = `<span class="cat">${esc(catLabel(p.category))}</span>
      <h2>${esc(p.title)}</h2>
      <div class="meta">
        <div><b>Source</b>${esc(p.source)}</div>
        <div><b>Published</b>${esc(p.date)}</div>
        <div><b>Length</b>${p.words.toLocaleString()} words · ${p.chars.toLocaleString()} chars</div>
        <div><b>Fingerprint</b><span style="font-family:var(--mono);font-size:.7rem">${esc(p.sha256)}</span></div>
      </div>
      <div class="notice">Complete document. The full paper is included in this public vault, not an excerpt.</div>
      <div class="reader-tools"><button class="btn" id="copy-link">Copy link</button><button class="btn" id="close-btn">Close</button></div>`;
    $("#r-main").innerHTML = `<h1>${esc(p.title)}</h1>
      <div class="dek">${esc(p.category)} · ${p.words.toLocaleString()} words · source fingerprint ${esc(p.sha12)}</div>
      <div class="paper-body">${formatBody(p.body)}</div>`;
    bindReader(p, "paper");
    history.replaceState(null, "", "#paper=" + encodeURIComponent(p.slug));
  }

  function openChat(c) {
    const shell = $("#reader");
    shell.classList.add("open");
    document.body.style.overflow = "hidden";
    $("#r-side").innerHTML = `<span class="cat">Grok excerpt</span>
      <h2>${esc(c.title)}</h2>
      <div class="meta">
        <div><b>Source</b>${esc(c.source)}</div>
        <div><b>Category</b>${esc(c.category)}</div>
        <div><b>Fingerprint</b>${esc(c.sha12 || "")}</div>
      </div>
      <div class="notice">Excerpt only. The full conversation is not published; private and ordinary chats are excluded from this vault.</div>
      <div class="reader-tools"><button class="btn" id="copy-link">Copy link</button><button class="btn" id="close-btn">Close</button></div>`;
    $("#r-main").innerHTML = `<h1>${esc(c.title)}</h1>
      <div class="dek">Curated Grok-tagged exchange · public excerpt</div>
      <div class="chat-note">This is a public excerpt from the curated Grok archive. It is not a full transcript.</div>
      <div class="paper-body"><p>${esc(c.excerpt)}</p></div>
      <div class="tags" style="margin-top:18px">${(c.tags || []).map(t => `<span class="tag">${esc(t)}</span>`).join("")}</div>`;
    bindReader(c, "chat");
    history.replaceState(null, "", "#chat=" + encodeURIComponent(c.id));
  }

  function bindReader(obj, kind) {
    $("#close-btn").onclick = closeReader;
    $("#copy-link").onclick = async () => {
      try {
        await navigator.clipboard.writeText(location.href);
        $("#copy-link").textContent = "Copied";
        setTimeout(() => { const b = $("#copy-link"); if (b) b.textContent = "Copy link"; }, 1400);
      } catch { prompt("Copy this link:", location.href); }
    };
  }

  function closeReader() {
    $("#reader").classList.remove("open");
    document.body.style.overflow = "";
    history.replaceState(null, "", location.pathname + location.search);
  }

  function openHash() {
    const h = new URLSearchParams(location.hash.replace(/^#/, ""));
    if (h.get("paper")) {
      const p = data.papers.find(x => x.slug === h.get("paper"));
      if (p) openPaper(p);
    } else if (h.get("chat")) {
      const c = data.chats.find(x => x.id === h.get("chat"));
      if (c) openChat(c);
    }
  }

  function init(dataIn) {
    data = dataIn;
    const s = data.stats || {};
    $("#stat-papers").textContent = (s.papers || data.papers.length).toLocaleString();
    $("#stat-words").textContent = (s.paper_words || 0).toLocaleString();
    $("#stat-chats").textContent = (s.chats || data.chats.length).toLocaleString();
    $("#stat-sources").textContent = (s.sources || data.papers.length).toLocaleString();

    const cats = Array.from(new Set(data.papers.map(p => p.category)));
    cats.sort((a, b) => (catOrder.indexOf(a) + 99) - (catOrder.indexOf(b) + 99));
    const chips = [`<button class="chip on" data-cat="all">All papers</button>`, ...cats.map(c => `<button class="chip" data-cat="${esc(c)}">${esc(catLabel(c))}</button>`)];
    $("#cats").innerHTML = chips.join("");
    $("#cats").querySelectorAll(".chip").forEach(ch => ch.onclick = () => { state.cat = ch.dataset.cat; state.limit = 36; render(); });

    document.querySelectorAll(".tab").forEach(t => t.onclick = () => { state.type = t.dataset.type; state.limit = 36; render(); });
    $("#q").addEventListener("input", e => { state.q = e.target.value; state.limit = 36; render(); });
    $("#more-btn").onclick = () => { state.limit += 36; render(); };
    $("#reader-close").addEventListener("click", closeReader);
    $("#reader").addEventListener("click", e => { if (e.target.id === "reader") closeReader(); });
    document.addEventListener("keydown", e => { if (e.key === "Escape" && $("#reader").classList.contains("open")) closeReader(); });
    render();
    openHash();
    window.addEventListener("hashchange", openHash);
  }

  fetch("data/library.json", { cache: "no-store" })
    .then(r => { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
    .then(init)
    .catch(err => { $("#result-count").textContent = "Vault data failed to load: " + err.message; });
})();
