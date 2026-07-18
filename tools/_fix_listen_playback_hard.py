#!/usr/bin/env python3
"""Hard fix listen portal playback — broken audio tag + crossOrigin mute."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

LISTEN = Path(r"I:\E Drive\Excavationpro\excavationpro-listen.html")
DOCS = Path(r"I:\E Drive\lygo-protocol-stack\docs\excavationpro-listen.html")


def main() -> int:
    html = LISTEN.read_text(encoding="utf-8")
    before = len(html)

    # 1) Fix broken / over-attributed audio element (critical)
    # Seen: <audio ...></audio></audio>
    html2, n = re.subn(
        r"<audio\b[^>]*>\s*(?:</audio>\s*)*",
        '<audio id="audio" controls preload="none" playsinline></audio>\n',
        html,
        count=1,
    )
    if n:
        html = html2
        print(f"[ok] audio tag cleaned x{n}")
    else:
        print("[warn] audio tag regex miss")

    # Remove any remaining stray </audio>
    # (only if more closing than opening)
    opens = len(re.findall(r"<audio\b", html, flags=re.I))
    closes = html.count("</audio>")
    print(f"audio open={opens} close={closes}")
    if closes > opens:
        # remove extras from the end carefully — replace first dock audio section only
        html = html.replace("</audio></audio>", "</audio>")
        html = html.replace("</audio>\n</audio>", "</audio>")
        print("[ok] removed duplicate </audio>")

    # 2) Strip crossOrigin on HTMLMediaElement (HF playback often fails with it)
    html = html.replace("crossorigin=\"anonymous\"", "")
    html = html.replace("crossOrigin = 'anonymous';", "/* no crossOrigin */")
    html = html.replace('crossOrigin = "anonymous";', "/* no crossOrigin */")
    html = re.sub(
        r"if\s*\(\s*!audio\.crossOrigin\s*\)\s*audio\.crossOrigin\s*=\s*['\"]anonymous['\"]\s*;?",
        "/* no crossOrigin */",
        html,
    )
    html = re.sub(
        r"try\s*\{\s*if\s*\(\s*!audio\.crossOrigin\s*\)\s*audio\.crossOrigin\s*=\s*['\"]anonymous['\"]\s*;\s*\}\s*catch\s*\([^)]*\)\s*\{\s*\}",
        "/* no crossOrigin */",
        html,
    )
    print("[ok] stripped crossOrigin for media")

    # 3) PLAYBACK_SAFETY block — rewrite to NOT set crossOrigin
    safety_new = """
// PLAYBACK_SAFETY: native HF stream playback (no CORS media mode)
(function playbackSafety(){
  try {
    if (audio) {
      audio.removeAttribute('crossorigin');
      audio.setAttribute('playsinline', '');
      audio.preload = 'none';
    }
  } catch (e) {}
})();
"""
    html = re.sub(
        r"// PLAYBACK_SAFETY:[\s\S]*?\}\)\(\);\s*",
        safety_new + "\n",
        html,
        count=1,
    )
    print("[ok] playback safety rewritten")

    # 4) ensureAnalyser must stay disabled
    if "createMediaElementSource(audio)" in html:
        html = html.replace(
            "createMediaElementSource(audio)",
            "/*createMediaElementSource DISABLED*/ null",
        )
        print("[ok] neutered remaining MediaElementSource")

    # 5) Replace playIndex with bulletproof version
    play_fn = r"""
function playIndex(i) {
  const t = tracks[i];
  if (!t || !t.stream_url) {
    console.warn('[listen] no stream', i, t && t.title);
    return false;
  }
  current = i;
  try { audio.pause(); } catch (e) {}
  try { audio.removeAttribute('crossorigin'); } catch (e) {}
  // Direct native play — Hugging Face MP3 URLs
  audio.src = t.stream_url;
  var p = audio.play();
  if (p && p.catch) {
    p.catch(function (err) {
      console.error('[listen] play failed', err);
      // Retry without cache-bust first, then with
      setTimeout(function () {
        try {
          audio.src = t.stream_url + (t.stream_url.indexOf('?') >= 0 ? '&' : '?') + 't=' + Date.now();
          audio.play().catch(function (e2) {
            console.error('[listen] retry failed', e2);
            try {
              if (typeof toast === 'function') toast('Play blocked — click Play again');
            } catch (e3) {}
          });
        } catch (e4) {}
      }, 200);
    });
  }
  try { updateNow(); } catch (e) {}
  try { updatePlayBtn(); } catch (e) {}
  try { if (typeof renderList === 'function') renderList(); } catch (e) {}
  try { history.replaceState(null, '', '#' + (t.sha256 || i)); } catch (e) {}
  return true;
}
"""
    # Match existing function playIndex ... until next function
    html2, n = re.subn(
        r"function playIndex\s*\(\s*i\s*\)\s*\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}",
        play_fn.strip(),
        html,
        count=1,
    )
    if n:
        html = html2
        print("[ok] playIndex replaced")
    else:
        print("[warn] playIndex replace failed — inserting override")
        # Append override before last </script>
        override = (
            "\n// PLAYINDEX_OVERRIDE\n"
            + play_fn
            + "\nwindow.playIndex = playIndex;\n"
        )
        idx = html.rfind("</script>")
        html = html[:idx] + override + html[idx:]

    # 6) Force-disable crossfade again
    if "function maybeCrossfade()" in html and "CROSSFADE_HARD_OFF" not in html:
        html = html.replace(
            "function maybeCrossfade() {",
            "function maybeCrossfade() { /* CROSSFADE_HARD_OFF */ return;",
            1,
        )
        print("[ok] crossfade hard off")

    # 7) btn-play handler must call playIndex not only audio.play()
    # leave as-is if already correct

    if len(html) < before * 0.85:
        raise SystemExit(f"abort shrink {before}->{len(html)}")

    LISTEN.write_text(html, encoding="utf-8")
    shutil.copy2(LISTEN, DOCS)
    print(f"wrote {LISTEN} len={len(html)}")

    # Verify
    t = LISTEN.read_text(encoding="utf-8")
    # audio tags
    opens = len(re.findall(r"<audio\b", t, flags=re.I))
    closes = t.count("</audio>")
    print("audio open/close", opens, closes)
    m = re.search(r"<audio\b[^>]*>", t)
    print("audio tag:", m.group(0) if m else "NONE")
    print("crossorigin left on audio?", "crossorigin" in (m.group(0) if m else ""))
    print("createMediaElementSource(audio)", "createMediaElementSource(audio)" in t)
    print("playIndex override present", "no stream" in t or "PLAYINDEX" in t)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
