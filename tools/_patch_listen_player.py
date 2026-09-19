#!/usr/bin/env python3
"""Patch excavationpro-listen.html player: continuous, shuffle bag, radio mode.
Also update the generator template in build_public_music_stream.py.
"""
from __future__ import annotations

from pathlib import Path

LISTEN = Path(r"I:\E Drive\Excavationpro\excavationpro-listen.html")
DOCS = Path(r"I:\E Drive\lygo-protocol-stack\docs\excavationpro-listen.html")
GEN = Path(r"I:\E Drive\lygo-protocol-stack\tools\build_public_music_stream.py")

# ---- shared player logic (plain JS for listen.html) ----
PLAYER_JS_PLAIN = r"""
let order = tracks.map((_, i) => i);
let current = -1;
let shuffle = false;
let repeatOne = false;   // loop current track only
let radio = false;       // infinite random (radio station)
let filteredIdx = order.slice();
let shuffleBag = [];     // no-repeat-until-exhausted bag for shuffle/radio
let advancing = false;   // re-entrancy guard for error/end skip

function playablePool() {
  return filteredIdx.filter(i => tracks[i] && tracks[i].stream_url);
}

function shuffleArray(arr) {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    const t = a[i]; a[i] = a[j]; a[j] = t;
  }
  return a;
}

function refillBag(exclude) {
  let pool = playablePool();
  if (exclude != null && exclude >= 0 && pool.length > 1) {
    pool = pool.filter(i => i !== exclude);
  }
  shuffleBag = shuffleArray(pool);
}

function updateModeUI() {
  const sh = document.getElementById('btn-shuffle');
  const rp = document.getElementById('btn-repeat');
  const rd = document.getElementById('btn-radio');
  if (sh) {
    sh.classList.toggle('on', shuffle && !radio);
    sh.textContent = shuffle && !radio ? 'Shuffle ✓' : 'Shuffle';
  }
  if (rp) {
    rp.classList.toggle('on', repeatOne);
    rp.textContent = repeatOne ? 'Repeat 1 ✓' : 'Repeat 1';
  }
  if (rd) {
    rd.classList.toggle('on', radio);
    rd.textContent = radio ? '📡 Radio ON' : '📡 Radio';
  }
  const pill = document.getElementById('mode-pill');
  if (pill) {
    let label = 'Continuous · auto-next';
    if (radio) label = '📡 RADIO · random forever';
    else if (shuffle) label = 'Shuffle · continuous';
    if (repeatOne) label += ' · loop track';
    pill.textContent = label;
    pill.classList.toggle('on', radio || shuffle || repeatOne);
  }
}

function rebuildFilter() {
  const q = (document.getElementById('q').value || '').toLowerCase().trim();
  const f = document.getElementById('filter').value;
  const sort = document.getElementById('sort').value;
  let idx = tracks.map((_, i) => i);
  if (f === 'isrc') idx = idx.filter(i => (tracks[i].isrcs||[]).length);
  if (f === 'playable') idx = idx.filter(i => tracks[i].stream_url);
  if (q) {
    idx = idx.filter(i => {
      const t = tracks[i];
      return [t.title, t.sha256, ...(t.isrcs||[]), ...(t.aliases||[])].join(' ').toLowerCase().includes(q);
    });
  }
  idx.sort((a,b) => {
    const ta = tracks[a], tb = tracks[b];
    if (sort === 'title-desc') return (tb.title||'').localeCompare(ta.title||'');
    if (sort === 'size') return (tb.size||0) - (ta.size||0);
    if (sort === 'isrc') return ((tb.isrcs||[]).length?1:0) - ((ta.isrcs||[]).length?1:0) || (ta.title||'').localeCompare(tb.title||'');
    return (ta.title||'').localeCompare(tb.title||'');
  });
  filteredIdx = idx;
  if (radio || shuffle) refillBag(current);
  renderList();
}

function renderList() {
  const el = document.getElementById('list');
  el.innerHTML = filteredIdx.map((i, n) => {
    const t = tracks[i];
    const on = i === current ? 'on' : '';
    const can = !!t.stream_url;
    return `<div class="row ${on}" data-i="${i}">
      <div class="n">${n+1}</div>
      <div>
        <div class="title">${esc(t.title)}</div>
        <div class="meta">${(t.isrcs||[]).slice(0,2).map(x=>`<span class="badge">${esc(x)}</span>`).join('')}${t.sha256 ? esc(t.sha256.slice(0,12))+'…' : ''}</div>
      </div>
      <div class="meta sz">${fmtSize(t.size)}</div>
      <button type="button" class="play" ${can?'':'disabled'} data-play="${i}">${i===current && !audio.paused ? 'Pause' : 'Play'}</button>
    </div>`;
  }).join('') || '<p class="sub" style="padding:16px">No matches</p>';
  el.querySelectorAll('[data-play]').forEach(b => b.addEventListener('click', e => {
    e.stopPropagation();
    const i = +b.getAttribute('data-play');
    if (i === current && !audio.paused) { audio.pause(); updatePlayBtn(); renderList(); return; }
    playIndex(i);
  }));
  el.querySelectorAll('.row').forEach(r => r.addEventListener('click', () => playIndex(+r.dataset.i)));
}

function updateNow() {
  const t = current >= 0 ? tracks[current] : null;
  const mode = radio ? ' · 📡 RADIO' : (shuffle ? ' · shuffle' : '');
  document.getElementById('now').innerHTML = t
    ? `<span>▶ ${esc(t.title)}${mode}</span><div class="sub2">${esc((t.isrcs||[])[0]||'')} · ${t.sha256 ? t.sha256.slice(0,16)+'…' : ''}</div>`
    : '<span>Select a track… or hit 📡 Radio</span><div class="sub2"></div>';
}
function updatePlayBtn() {
  document.getElementById('btn-play').textContent = (!audio.paused && current >= 0) ? '⏸ Pause' : '▶ Play';
}

function playIndex(i) {
  const t = tracks[i];
  if (!t || !t.stream_url) return false;
  current = i;
  try { audio.pause(); } catch (e) {}
  audio.src = t.stream_url;
  audio.load();
  const p = audio.play();
  if (p && p.catch) p.catch(() => {});
  updateNow();
  updatePlayBtn();
  renderList();
  try { history.replaceState(null, '', '#' + (t.sha256 || i)); } catch (e) {}
  return true;
}

/** Pick next index. dir: +1 next, -1 prev. Continuous wrap always. */
function pickNext(dir) {
  const pool = playablePool();
  if (!pool.length) return -1;

  // Repeat-one only on natural advance
  if (repeatOne && dir > 0 && current >= 0 && tracks[current] && tracks[current].stream_url) {
    return current;
  }

  // Radio or Shuffle: random from bag (no immediate full-catalog repeats)
  if ((radio || shuffle) && dir > 0) {
    if (!shuffleBag.length) refillBag(current);
    if (!shuffleBag.length) return pool[Math.floor(Math.random() * pool.length)];
    return shuffleBag.pop();
  }

  // Sequential through playable filtered list (wraps forever)
  let pos = pool.indexOf(current);
  if (pos < 0) pos = dir > 0 ? -1 : 0;
  let npos = pos + dir;
  if (npos >= pool.length) npos = 0;
  if (npos < 0) npos = pool.length - 1;
  return pool[npos];
}

function nextTrack(dir) {
  if (advancing) return;
  advancing = true;
  try {
    const pool = playablePool();
    const maxTry = Math.min(25, Math.max(1, pool.length));
    for (let t = 0; t < maxTry; t++) {
      const i = pickNext(dir);
      if (i < 0) break;
      if (playIndex(i)) break;
      shuffleBag = shuffleBag.filter(x => x !== i);
      current = i;
    }
  } finally {
    advancing = false;
  }
}

function setShuffle(on) {
  shuffle = !!on;
  if (shuffle) {
    radio = false;
    refillBag(current);
  } else {
    shuffleBag = [];
  }
  updateModeUI();
  renderList();
}

function toggleShuffle() {
  setShuffle(!shuffle);
}

function toggleRadio() {
  radio = !radio;
  if (radio) {
    shuffle = false;
    repeatOne = false;
    refillBag(-1);
    updateModeUI();
    nextTrack(1); // 1-click: start random forever
  } else {
    shuffleBag = [];
    updateModeUI();
  }
}

function toggleRepeatOne() {
  repeatOne = !repeatOne;
  updateModeUI();
}

document.getElementById('btn-prev').onclick = () => nextTrack(-1);
document.getElementById('btn-next').onclick = () => nextTrack(1);
document.getElementById('btn-play').onclick = () => {
  if (current < 0) { nextTrack(1); return; }
  if (audio.paused) audio.play().catch(()=>{}); else audio.pause();
  updatePlayBtn(); renderList();
};
document.getElementById('btn-shuffle').onclick = toggleShuffle;
const btnRadio = document.getElementById('btn-radio');
if (btnRadio) btnRadio.onclick = toggleRadio;
document.getElementById('btn-repeat').onclick = toggleRepeatOne;
document.getElementById('btn-copy').onclick = async () => {
  const t = current >= 0 ? tracks[current] : null;
  const url = t && t.stream_url ? t.stream_url : location.href;
  try { await navigator.clipboard.writeText(url); document.getElementById('btn-copy').textContent = 'Copied'; setTimeout(() => document.getElementById('btn-copy').textContent = 'Copy link', 1200); }
  catch (e) { prompt('Copy URL', url); }
};

// Continuous listening: always auto-advance on end (Repeat 1 handled in pickNext)
audio.addEventListener('play', () => { updatePlayBtn(); renderList(); });
audio.addEventListener('pause', () => { updatePlayBtn(); renderList(); });
audio.addEventListener('ended', () => { nextTrack(1); });
// Skip dead streams so radio/continuous never stalls
audio.addEventListener('error', () => {
  if (current < 0) return;
  console.warn('stream error, skipping', current);
  setTimeout(() => nextTrack(1), 250);
});

document.getElementById('q').addEventListener('input', rebuildFilter);
document.getElementById('sort').addEventListener('change', rebuildFilter);
document.getElementById('filter').addEventListener('change', rebuildFilter);

document.addEventListener('keydown', e => {
  if (e.target.matches('input,textarea,select')) {
    if (e.key === 'Escape') e.target.blur();
    return;
  }
  if (e.key === ' ') { e.preventDefault(); document.getElementById('btn-play').click(); }
  if (e.key === 'n' || e.key === 'N') nextTrack(1);
  if (e.key === 'p' || e.key === 'P') nextTrack(-1);
  if (e.key === 's' || e.key === 'S') toggleShuffle();
  if (e.key === 'r' || e.key === 'R') toggleRadio();
  if (e.key === '/') { e.preventDefault(); document.getElementById('q').focus(); }
});

(function injectModePill() {
  const dock = document.querySelector('.dock-inner .controls');
  if (dock && !document.getElementById('mode-pill')) {
    const span = document.createElement('span');
    span.id = 'mode-pill';
    span.className = 'mode-pill';
    span.textContent = 'Continuous · auto-next';
    dock.appendChild(span);
  }
  updateModeUI();
})();

// deep link #sha256
rebuildFilter();
(function bootHash() {
  const h = (location.hash || '').replace(/^#/, '');
  if (!h) return;
  const i = tracks.findIndex(t => t.sha256 === h || (t.sha256 && t.sha256.startsWith(h)));
  if (i >= 0) playIndex(i);
  else if (/^\d+$/.test(h)) {
    const n = +h;
    if (n >= 0 && n < tracks.length) playIndex(n);
  }
})();
""".lstrip("\n")


def patch_html(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    orig = text

    old_controls = """      <button type="button" id="btn-shuffle" title="Shuffle (S)">Shuffle</button>
      <button type="button" id="btn-repeat" title="Repeat one">Repeat</button>
      <button type="button" id="btn-copy" title="Copy stream URL">Copy link</button>"""
    new_controls = """      <button type="button" id="btn-shuffle" title="Shuffle queue (S)">Shuffle</button>
      <button type="button" id="btn-radio" title="Radio — random forever (R)" class="radio-btn">📡 Radio</button>
      <button type="button" id="btn-repeat" title="Repeat one track">Repeat 1</button>
      <button type="button" id="btn-copy" title="Copy stream URL">Copy link</button>"""
    if old_controls in text:
        text = text.replace(old_controls, new_controls, 1)
    elif "btn-radio" not in text:
        raise SystemExit(f"controls block missing in {path}")

    old_css = """.controls button.on { border-color:var(--gold); color:var(--gold); }
.controls button:hover { border-color:var(--cyan); }"""
    new_css = """.controls button.on { border-color:var(--gold); color:var(--gold); }
.controls button.radio-btn.on { border-color:#ff6b9d; color:#ff6b9d; box-shadow:0 0 12px rgba(255,107,157,.35); }
.controls button:hover { border-color:var(--cyan); }
.mode-pill { font-size:.72rem; color:var(--muted); margin-left:4px; letter-spacing:.03em; }
.mode-pill.on { color:var(--gold); }"""
    if old_css in text:
        text = text.replace(old_css, new_css, 1)

    old_kb = "Keys: <b>Space</b> play/pause · <b>N</b> next · <b>P</b> prev · <b>S</b> shuffle · <b>/</b> focus search"
    new_kb = "Keys: <b>Space</b> play/pause · <b>N</b> next · <b>P</b> prev · <b>S</b> shuffle · <b>R</b> radio · <b>/</b> search · continuous auto-next always on"
    if old_kb in text:
        text = text.replace(old_kb, new_kb, 1)

    # Replace from state vars through end of script (before </script>)
    start = "let order = tracks.map((_, i) => i);"
    # Keep everything BEFORE start; replace from start to just before </script> of main player
    si = text.find(start)
    if si < 0:
        raise SystemExit(f"player state start not found in {path}")
    # Find the script close after si - first </script> after si
    ei = text.find("</script>", si)
    if ei < 0:
        raise SystemExit(f"</script> not found after player in {path}")

    # Keep preamble before `let order` but drop old player — however
    # `let order` is right after audio/const tracks. We need to keep
    # nav/stats/tabs code that sits BETWEEN order and rebuildFilter in OLD file.
    # Old structure:
    #   let order... filteredIdx
    #   // --- nav --- ... lots of non-player code ...
    #   function rebuildFilter ... bootHash
    #
    # New PLAYER_JS includes rebuildFilter through bootHash but NOT nav.
    # So we must only replace from first `function rebuildFilter` OR from
    # `function esc` ... actually best:
    # 1) Replace state vars at top
    # 2) Replace from `function rebuildFilter` through bootHash end

    # Step A: replace state declaration block
    old_state = """let order = tracks.map((_, i) => i);
let current = -1;
let shuffle = false;
let repeat = false;
let filteredIdx = order.slice();"""
    new_state = """let order = tracks.map((_, i) => i);
let current = -1;
let shuffle = false;
let repeatOne = false;   // loop current track only
let radio = false;       // infinite random (radio station)
let filteredIdx = order.slice();
let shuffleBag = [];     // no-repeat-until-exhausted bag for shuffle/radio
let advancing = false;   // re-entrancy guard for error/end skip"""
    if old_state in text:
        text = text.replace(old_state, new_state, 1)
    elif "let radio = false" not in text:
        raise SystemExit(f"state block not found / not patched in {path}")

    # Step B: replace from function rebuildFilter through end of bootHash
    rf = text.find("function rebuildFilter()")
    if rf < 0:
        raise SystemExit(f"rebuildFilter not found in {path}")
    # bootHash ends with })(); before </script>
    boot = text.find("(function bootHash()", rf)
    if boot < 0:
        raise SystemExit(f"bootHash not found in {path}")
    # find closing of bootHash IIFE
    close = text.find("})();", boot)
    if close < 0:
        raise SystemExit(f"bootHash close not found in {path}")
    close_end = close + len("})();")

    # PLAYER_JS_PLAIN starts with state - we need only from playablePool (helpers)
    # through bootHash. Extract portion after state from PLAYER_JS_PLAIN.
    # Our PLAYER_JS_PLAIN includes state + everything - strip state lines.
    body = PLAYER_JS_PLAIN
    # body starts with let order... — strip through advancing line
    marker = "let advancing = false;   // re-entrancy guard for error/end skip\n\n"
    if marker not in body:
        raise SystemExit("marker missing in PLAYER_JS_PLAIN")
    body_from_helpers = body.split(marker, 1)[1]

    text = text[:rf] + body_from_helpers + text[close_end:]

    if text == orig:
        print(f"[skip] no change {path}")
        return
    path.write_text(text, encoding="utf-8")
    print(f"[ok] patched {path} ({len(text):,} chars)")


def patch_generator() -> None:
    """Update f-string template in build_public_music_stream.py (doubled braces)."""
    text = GEN.read_text(encoding="utf-8")
    orig = text

    old_controls = """      <button type="button" id="btn-shuffle" title="Shuffle (S)">Shuffle</button>
      <button type="button" id="btn-repeat" title="Repeat one">Repeat</button>
      <button type="button" id="btn-copy" title="Copy stream URL">Copy link</button>"""
    new_controls = """      <button type="button" id="btn-shuffle" title="Shuffle queue (S)">Shuffle</button>
      <button type="button" id="btn-radio" title="Radio — random forever (R)" class="radio-btn">📡 Radio</button>
      <button type="button" id="btn-repeat" title="Repeat one track">Repeat 1</button>
      <button type="button" id="btn-copy" title="Copy stream URL">Copy link</button>"""
    if old_controls in text:
        text = text.replace(old_controls, new_controls, 1)

    old_css = """.controls button.on {{ border-color:var(--gold); color:var(--gold); }}
.controls button:hover {{ border-color:var(--cyan); }}"""
    new_css = """.controls button.on {{ border-color:var(--gold); color:var(--gold); }}
.controls button.radio-btn.on {{ border-color:#ff6b9d; color:#ff6b9d; box-shadow:0 0 12px rgba(255,107,157,.35); }}
.controls button:hover {{ border-color:var(--cyan); }}
.mode-pill {{ font-size:.72rem; color:var(--muted); margin-left:4px; letter-spacing:.03em; }}
.mode-pill.on {{ color:var(--gold); }}"""
    if old_css in text:
        text = text.replace(old_css, new_css, 1)

    old_kb = "Keys: <b>Space</b> play/pause · <b>N</b> next · <b>P</b> prev · <b>S</b> shuffle · <b>/</b> focus search"
    new_kb = "Keys: <b>Space</b> play/pause · <b>N</b> next · <b>P</b> prev · <b>S</b> shuffle · <b>R</b> radio · <b>/</b> search · continuous auto-next always on"
    if old_kb in text:
        text = text.replace(old_kb, new_kb, 1)

    # Convert plain player JS to f-string safe (double braces for JS objects/format)
    # Generator already uses {{ }} for all JS braces. We'll do surgical replace of
    # the player logic section similar to HTML but with doubled braces.

    old_state = """let order = tracks.map((_, i) => i);
let current = -1;
let shuffle = false;
let repeat = false;
let filteredIdx = order.slice();"""
    new_state = """let order = tracks.map((_, i) => i);
let current = -1;
let shuffle = false;
let repeatOne = false;
let radio = false;
let filteredIdx = order.slice();
let shuffleBag = [];
let advancing = false;"""
    if old_state in text:
        text = text.replace(old_state, new_state, 1)

    # Replace from function rebuildFilter through bootHash in generator template
    # Generator has doubled braces in many places
    rf = text.find("function rebuildFilter()")
    if rf < 0:
        print("[warn] generator rebuildFilter not found — skip JS body")
    else:
        boot = text.find("(function bootHash()", rf)
        if boot < 0:
            print("[warn] generator bootHash not found")
        else:
            close = text.find("}})();", boot)
            # In f-string template bootHash ends with }})();  because of doubled }}
            if close < 0:
                close = text.find("})();", boot)
                close_end = close + len("})();") if close >= 0 else -1
            else:
                close_end = close + len("}})();")
            if close_end < 0:
                print("[warn] generator bootHash close not found")
            else:
                # Convert plain JS to f-string: { -> {{, } -> }}
                plain = PLAYER_JS_PLAIN
                marker = "let advancing = false;   // re-entrancy guard for error/end skip\n\n"
                body = plain.split(marker, 1)[1]
                # Escape for Python f-string: double all braces that are JS
                # Also escape none for $ - not needed
                escaped = body.replace("{", "{{").replace("}", "}}")
                # Fix: already-doubled from replace is fine. But we may have broken
                # nothing else. f-string also has {data_js} elsewhere not in this body.
                text = text[:rf] + escaped + text[close_end:]

    if text == orig:
        print(f"[skip] no change {GEN}")
        return
    GEN.write_text(text, encoding="utf-8")
    print(f"[ok] patched {GEN}")


def main() -> int:
    patch_html(LISTEN)
    if DOCS.exists():
        try:
            patch_html(DOCS)
        except SystemExit as e:
            print(f"[docs] {e}")
    patch_generator()

    # Sanity: listen page must contain radio + continuous handlers
    t = LISTEN.read_text(encoding="utf-8")
    checks = [
        "btn-radio",
        "toggleRadio",
        "shuffleBag",
        "audio.addEventListener('ended'",
        "audio.addEventListener('error'",
        "📡 RADIO",
        "repeatOne",
    ]
    for c in checks:
        ok = c in t
        print(f"  check {'OK' if ok else 'FAIL'}: {c}")
        if not ok:
            return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
