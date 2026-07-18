#!/usr/bin/env python3
"""Fix listen portal playback breakage after v2/v3 enhancements."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

LISTEN = Path(r"I:\E Drive\Excavationpro\excavationpro-listen.html")
DOCS = Path(r"I:\E Drive\lygo-protocol-stack\docs\excavationpro-listen.html")


def main() -> int:
    html = LISTEN.read_text(encoding="utf-8")
    before = len(html)

    # --- audio tag: CORS + mobile ---
    html2, n = re.subn(
        r"<audio\s+id=\"audio\"[^>]*>",
        '<audio id="audio" controls preload="metadata" crossorigin="anonymous" playsinline></audio>',
        html,
        count=1,
    )
    if n:
        html = html2
        print("[ok] audio tag")
    else:
        print("[warn] audio tag not replaced")

    # --- declare waveFailed ---
    if "let waveFailed" not in html and "let waveReady = false" in html:
        html = html.replace(
            "let waveReady = false;",
            "let waveReady = false;\n  let waveFailed = false;",
            1,
        )
        print("[ok] waveFailed flag")

    # --- kill MediaElementSource (root cause of mute with HF streams) ---
    # Replace ensureAnalyser function body(ies)
    def repl_ensure(m: re.Match) -> str:
        return (
            "function ensureAnalyser() {\n"
            "    // SAFE: do not use createMediaElementSource — it can MUTE\n"
            "    // cross-origin Hugging Face streams in Chrome/Edge.\n"
            "    // Waveform stays decorative (time-based) without hijacking <audio>.\n"
            "    waveFailed = true;\n"
            "    waveReady = false;\n"
            "  }"
        )

    html2, n = re.subn(
        r"function ensureAnalyser\(\)\s*\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}",
        repl_ensure,
        html,
        count=3,
    )
    if n:
        html = html2
        print(f"[ok] ensureAnalyser disabled x{n}")
    else:
        # fallback simple replace of createMediaElementSource line
        if "createMediaElementSource" in html:
            html = html.replace(
                "sourceNode = audioCtx.createMediaElementSource(audio);",
                "// sourceNode DISABLED for playback safety\n      throw new Error('MediaElementSource disabled');",
            )
            print("[ok] neutered createMediaElementSource")
        else:
            print("[warn] ensureAnalyser not found")

    # --- disable crossfade swap (can break src/currentTime) ---
    if "CROSSFADE_DISABLED_FOR_PLAYBACK" not in html and "function maybeCrossfade()" in html:
        html = html.replace(
            "function maybeCrossfade() {",
            "function maybeCrossfade() {\n"
            "    // CROSSFADE_DISABLED_FOR_PLAYBACK — dual-element swap stalled HF streams\n"
            "    return;",
            1,
        )
        print("[ok] crossfade disabled")

    # --- playback safety after audio const ---
    safety = """
// PLAYBACK_SAFETY: HF stream playback must stay native
(function playbackSafety(){
  try {
    if (audio) {
      audio.crossOrigin = 'anonymous';
      audio.setAttribute('playsinline', '');
      audio.setAttribute('preload', 'metadata');
    }
  } catch (e) {}
})();
"""
    if "PLAYBACK_SAFETY" not in html:
        needle = "const audio = document.getElementById('audio');"
        if needle in html:
            html = html.replace(needle, needle + "\n" + safety, 1)
            print("[ok] playback safety")
        else:
            print("[warn] audio const not found")

    # --- playIndex: remove audio.load() race ---
    old = """  try { audio.pause(); } catch (e) {}
  audio.src = t.stream_url;
  audio.load();
  const p = audio.play();
  if (p && p.catch) p.catch(() => {});"""
    new = """  try { audio.pause(); } catch (e) {}
  try { if (!audio.crossOrigin) audio.crossOrigin = 'anonymous'; } catch (e) {}
  // Avoid audio.load() — it can cancel an in-flight play() on some browsers
  audio.src = t.stream_url;
  const p = audio.play();
  if (p && p.catch) {
    p.catch(function(err) {
      console.error('[listen] play failed', err);
      setTimeout(function() {
        audio.play().catch(function(e2){ console.error('[listen] retry failed', e2); });
      }, 250);
    });
  }"""
    if old in html:
        html = html.replace(old, new, 1)
        print("[ok] playIndex load/play")
    else:
        # try without try/pause line variations
        old2 = """  audio.src = t.stream_url;
  audio.load();
  const p = audio.play();
  if (p && p.catch) p.catch(() => {});"""
        if old2 in html:
            html = html.replace(old2, new.replace("  try { audio.pause(); } catch (e) {}\n", ""), 1)
            print("[ok] playIndex alt")
        else:
            print("[warn] playIndex pattern not found")

    # --- mini-player dock must not block clicks permanently ---
    # body.has-mini .dock { pointer-events: none } breaks controls
    if "body.has-mini .dock" in html:
        html = html.replace(
            "body.has-mini .dock { opacity: .35; pointer-events: none; transition: opacity .2s; }",
            "body.has-mini .dock { opacity: .92; pointer-events: auto; transition: opacity .2s; }",
        )
        html = html.replace(
            "body.has-mini .dock { opacity: .35; pointer-events: none; transition: opacity .2s; }",
            "body.has-mini .dock { opacity: .92; pointer-events: auto; transition: opacity .2s; }",
        )
        # also minified variants
        html = re.sub(
            r"body\.has-mini \.dock \{[^}]*pointer-events:\s*none[^}]*\}",
            "body.has-mini .dock { opacity: .95; pointer-events: auto; transition: opacity .2s; }",
            html,
        )
        print("[ok] dock pointer-events restored")

    if len(html) < before * 0.85:
        raise SystemExit(f"abort shrink {before} -> {len(html)}")

    LISTEN.write_text(html, encoding="utf-8")
    shutil.copy2(LISTEN, DOCS)
    print(f"wrote {len(html)} (was {before})")

    checks = [
        "PLAYBACK_SAFETY",
        "crossorigin",
        "MediaElementSource disabled",
        "CROSSFADE_DISABLED_FOR_PLAYBACK",
        "play failed",
        "stream_url",
    ]
    # MediaElementSource disabled text may vary
    t = html
    print("createMediaElementSource still active?", "createMediaElementSource(audio)" in t and "DISABLED" not in t and "disabled" not in t.lower())
    for c in checks:
        print(("OK" if c in t else "MISS"), c)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
