#!/usr/bin/env python3
"""Restore SAFE waveform visualizer on listen portal (no MediaElementSource)."""
from __future__ import annotations

from pathlib import Path

LISTEN = Path(r"I:\E Drive\Excavationpro\excavationpro-listen.html")
DOCS = Path(r"I:\E Drive\lygo-protocol-stack\docs\excavationpro-listen.html")

CSS = """
/* --- waveform visualizer (SAFE decorative — never uses MediaElementSource) --- */
.wave-shell {
  margin: 0 0 14px; padding: 10px 12px 8px; border-radius: 14px;
  border: 1px solid rgba(0,240,255,.28);
  background: linear-gradient(180deg, rgba(18,18,31,.95), rgba(8,8,16,.98));
  box-shadow: 0 0 28px rgba(0,240,255,.08), inset 0 0 40px rgba(176,107,255,.05);
  position: relative; overflow: hidden;
}
.wave-shell::before {
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background: radial-gradient(600px 80px at 50% 100%, rgba(212,175,55,.08), transparent 70%);
}
#wave-canvas {
  display: block; width: 100%; height: 72px; border-radius: 8px;
  background: rgba(0,0,0,.35);
}
.wave-meta {
  display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; align-items: center;
}
.wave-meta .pill {
  font-size: .68rem; letter-spacing: .04em; text-transform: uppercase;
  padding: 3px 9px; border-radius: 999px;
  border: 1px solid rgba(0,240,255,.25); color: var(--muted);
  background: rgba(0,0,0,.25);
}
.wave-meta .pill.live { border-color: rgba(61,214,140,.5); color: var(--ok); }
.wave-meta .pill.gold { border-color: rgba(212,175,55,.45); color: var(--gold); }
"""

HTML = """
    <div class="wave-shell" id="wave-shell" aria-label="Audio visualizer">
      <canvas id="wave-canvas" width="900" height="72" aria-hidden="true"></canvas>
      <div class="wave-meta">
        <span class="pill gold" id="wave-mode">Visualizer</span>
        <span class="pill" id="wave-cat">All</span>
        <span class="pill" id="wave-count">— tracks</span>
        <span class="pill" id="wave-status">Idle · press play</span>
      </div>
    </div>
"""

JS = r"""
// --- SAFE waveform visualizer (no createMediaElementSource — never mutes HF streams) ---
(function initSafeWaveform() {
  const canvas = document.getElementById('wave-canvas');
  const audioEl = document.getElementById('audio');
  if (!canvas || !audioEl) return;

  const ctx = canvas.getContext('2d');
  let raf = 0;
  const BARS = 64;
  // pseudo spectrum energy (decorative but reacts to play state + progress)
  const energy = new Float32Array(BARS);

  function resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const rect = canvas.getBoundingClientRect();
    const w = Math.max(300, Math.floor(rect.width * dpr));
    const h = Math.floor(72 * dpr);
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
    }
  }

  function updateMeta() {
    const countEl = document.getElementById('wave-count');
    const catEl = document.getElementById('wave-cat');
    const stEl = document.getElementById('wave-status');
    const modeEl = document.getElementById('wave-mode');
    try {
      const n = (typeof filteredIdx !== 'undefined' && filteredIdx && filteredIdx.length)
        ? filteredIdx.length
        : (typeof tracks !== 'undefined' ? tracks.length : 0);
      if (countEl) countEl.textContent = n.toLocaleString() + ' tracks';
      const on = document.querySelector('#filter-chips button.on');
      if (catEl && on) catEl.textContent = (on.textContent || 'All').trim().slice(0, 24);
      const playing = !audioEl.paused && !audioEl.ended && audioEl.currentTime > 0;
      if (stEl) {
        if (playing) {
          const t = (typeof current === 'number' && current >= 0 && tracks[current])
            ? (tracks[current].title || 'Playing').slice(0, 42)
            : 'Playing';
          stEl.textContent = '▶ ' + t;
          stEl.classList.add('live');
        } else {
          stEl.textContent = 'Idle · press play';
          stEl.classList.remove('live');
        }
      }
      if (modeEl) {
        let m = 'Visualizer';
        if (typeof radio !== 'undefined' && radio) m = '📡 Radio wave';
        else if (typeof shuffle !== 'undefined' && shuffle) m = 'Shuffle wave';
        modeEl.textContent = m;
      }
    } catch (e) {}
  }

  function tickEnergy(playing, progress) {
    const t = Date.now() / 1000;
    const drive = playing ? 0.55 + 0.45 * Math.sin(t * 2.1) : 0.12;
    const bass = playing ? 0.35 + 0.25 * Math.sin(t * 3.4 + progress * 12) : 0.08;
    for (let i = 0; i < BARS; i++) {
      const f = i / BARS;
      // falloff like real spectrum + layered motion
      const base =
        Math.sin(t * 4.2 + f * 18) * 0.25 +
        Math.sin(t * 7.1 + f * 31) * 0.15 +
        Math.sin(t * 1.3 + f * 6) * 0.2;
      let e = (0.35 + base) * drive * (1.15 - f * 0.75);
      if (f < 0.18) e += bass * (1 - f / 0.18);
      // progress shimmer
      if (playing) e += 0.08 * Math.sin(progress * Math.PI * 2 + f * 10 + t);
      e = Math.max(0.04, Math.min(1, e));
      // smooth
      energy[i] = energy[i] * 0.72 + e * 0.28;
    }
  }

  function draw() {
    resize();
    const w = canvas.width, h = canvas.height;
    const playing = !audioEl.paused && !audioEl.ended;
    const progress = (audioEl.duration && isFinite(audioEl.duration))
      ? Math.max(0, Math.min(1, audioEl.currentTime / audioEl.duration))
      : 0;

    tickEnergy(playing, progress);

    ctx.clearRect(0, 0, w, h);
    // bg
    const bg = ctx.createLinearGradient(0, 0, 0, h);
    bg.addColorStop(0, 'rgba(6,6,14,.9)');
    bg.addColorStop(1, 'rgba(12,8,24,.95)');
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, w, h);

    // progress glow line
    if (playing && progress > 0) {
      const px = progress * w;
      ctx.fillStyle = 'rgba(212,175,55,.12)';
      ctx.fillRect(0, 0, px, h);
      ctx.strokeStyle = 'rgba(212,175,55,.55)';
      ctx.lineWidth = Math.max(1, w / 900);
      ctx.beginPath();
      ctx.moveTo(px, 0);
      ctx.lineTo(px, h);
      ctx.stroke();
    }

    const gap = 2 * (w / 900);
    const barW = Math.max(2, (w - gap * BARS) / BARS);

    for (let i = 0; i < BARS; i++) {
      const v = energy[i];
      const bh = Math.max(2, v * (h - 6));
      const x = i * (barW + gap);
      const y = h - bh;
      const g = ctx.createLinearGradient(x, y, x, h);
      if (playing) {
        g.addColorStop(0, 'rgba(0,240,255,.95)');
        g.addColorStop(0.45, 'rgba(176,107,255,.75)');
        g.addColorStop(1, 'rgba(212,175,55,.55)');
      } else {
        g.addColorStop(0, 'rgba(0,240,255,.35)');
        g.addColorStop(1, 'rgba(176,107,255,.2)');
      }
      ctx.fillStyle = g;
      // rounded-ish bars
      ctx.fillRect(x, y, barW, bh);
      // mirror glow top
      ctx.fillStyle = playing ? 'rgba(0,240,255,.15)' : 'rgba(0,240,255,.06)';
      ctx.fillRect(x, h / 2 - bh * 0.15, barW, Math.max(1, bh * 0.12));
    }

    // center sine overlay when idle
    if (!playing) {
      ctx.strokeStyle = 'rgba(0,240,255,.4)';
      ctx.lineWidth = 1.5 * (w / 900);
      ctx.beginPath();
      const t = Date.now() / 500;
      for (let x = 0; x < w; x++) {
        const yy = h / 2 + Math.sin(x / 28 + t) * (h * 0.12) + Math.sin(x / 11 + t * 1.3) * (h * 0.05);
        if (x === 0) ctx.moveTo(x, yy); else ctx.lineTo(x, yy);
      }
      ctx.stroke();
    }

    raf = requestAnimationFrame(draw);
  }

  audioEl.addEventListener('play', updateMeta);
  audioEl.addEventListener('pause', updateMeta);
  audioEl.addEventListener('ended', updateMeta);
  setInterval(updateMeta, 2000);
  updateMeta();
  draw();
  console.info('[listen] safe waveform visualizer ready (no MediaElementSource)');
})();
"""


def main() -> int:
    html = LISTEN.read_text(encoding="utf-8")
    if "initSafeWaveform" in html and "wave-canvas" in html:
        print("[ok] waveform already present")
        return 0

    # CSS
    if "wave-shell" not in html:
        if "/* --- v2 enhancements" in html:
            html = html.replace(
                "/* --- v2 enhancements: radio polish / favs / PWA --- */",
                CSS + "\n/* --- v2 enhancements: radio polish / favs / PWA --- */",
                1,
            )
            print("[ok] CSS")
        else:
            html = html.replace("</style>", CSS + "\n</style>", 1)
            print("[ok] CSS via style end")

    # HTML before play-listing mount
    if 'id="wave-shell"' not in html:
        needle = '<div id="play-listing-mount"'
        if needle in html:
            html = html.replace(needle, HTML + "\n    " + needle, 1)
            print("[ok] HTML wave-shell")
        else:
            raise SystemExit("play-listing-mount not found")

    # JS before LYGO_LISTEN export
    if "initSafeWaveform" not in html:
        marker = "// LYGO_LISTEN_EXPORT"
        if marker in html:
            html = html.replace(marker, JS + "\n\n" + marker, 1)
            print("[ok] JS visualizer")
        else:
            html = html.replace(
                '<script src="listen-plugins/play-listing.js',
                "<script>\n" + JS + "\n</script>\n"
                + '<script src="listen-plugins/play-listing.js',
                1,
            )
            print("[ok] JS before plugin")

    # never allow MediaElementSource accidental reintro nearby
    if "createMediaElementSource" in html and "SAFE waveform" not in html:
        print("[warn] MediaElementSource still in page — leaving as-is if unrelated")

    LISTEN.write_text(html, encoding="utf-8")
    if DOCS.parent.is_dir():
        DOCS.write_text(html, encoding="utf-8")
        print("[ok] mirrored docs")
    print("[ok] wrote", LISTEN, "chars", len(html))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
