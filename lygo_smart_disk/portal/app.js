/* LYGO SMART DISK AGENT portal — no login */
const log = document.getElementById("log");
const form = document.getElementById("form");
const msg = document.getElementById("msg");
const healthEl = document.getElementById("health");
const limbOut = document.getElementById("limb-out");

function addBubble(text, cls) {
  const d = document.createElement("div");
  d.className = "bubble " + cls;
  d.textContent = text;
  log.appendChild(d);
  log.scrollTop = log.scrollHeight;
}

async function refreshHealth() {
  try {
    const r = await fetch("/api/health", { cache: "no-store" });
    const j = await r.json();
    const brain = j.brain || "missing";
    healthEl.className = "health " + brain;
    healthEl.textContent =
      "brain:" + brain +
      (j.model ? " · " + j.model : "") +
      " · :9631 open · no password · free " +
      Math.round((j.disk_free_bytes || 0) / 1024) + " KB";
  } catch (e) {
    healthEl.className = "health missing";
    healthEl.textContent = "agent offline — run LYGO_SMART_DISK_BOOT.bat";
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = msg.value.trim();
  if (!text) return;
  addBubble(text, "user");
  msg.value = "";
  try {
    const r = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    const j = await r.json();
    const reply = j.reply || j.error || JSON.stringify(j);
    addBubble((j.model ? "[" + j.model + "] " : "") + reply, j.ok === false ? "sys" : "bot");
  } catch (err) {
    addBubble("Chat failed — is the agent running?", "sys");
  }
  refreshHealth();
});

document.querySelectorAll("[data-limb]").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const limb = btn.getAttribute("data-limb");
    try {
      const r = await fetch("/api/limb", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ limb, args: [] }),
      });
      const j = await r.json();
      limbOut.textContent = JSON.stringify(j, null, 2);
    } catch (e) {
      limbOut.textContent = String(e);
    }
  });
});

addBubble("Smart Disk portal ready. No password. Local kernel + Ollama brain.", "sys");
refreshHealth();
setInterval(refreshHealth, 15000);
