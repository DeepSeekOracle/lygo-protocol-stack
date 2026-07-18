#!/usr/bin/env python3
"""Repair listen page JS — remove syntax errors and force working playIndex."""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

LISTEN = Path(r"I:\E Drive\Excavationpro\excavationpro-listen.html")
DOCS = Path(r"I:\E Drive\lygo-protocol-stack\docs\excavationpro-listen.html")

FINAL = r"""
// === PLAYINDEX_FINAL — last definition wins; restores reliable HF playback ===
function playIndex(i) {
  var t = tracks[i];
  if (!t || !t.stream_url) {
    console.warn("[listen] no stream", i);
    return false;
  }
  current = i;
  try { audio.pause(); } catch (e0) {}
  try { audio.removeAttribute("crossorigin"); } catch (e1) {}
  audio.src = t.stream_url;
  var p = audio.play();
  if (p && p.catch) {
    p.catch(function (err) {
      console.error("[listen] play failed", err);
      setTimeout(function () {
        audio.src = t.stream_url;
        audio.play().catch(function (e2) { console.error("[listen] retry failed", e2); });
      }, 200);
    });
  }
  try { updateNow(); } catch (e3) {}
  try { updatePlayBtn(); } catch (e4) {}
  try {
    if (typeof renderList === "function") renderList();
  } catch (e5) {}
  try { history.replaceState(null, "", "#" + (t.sha256 || i)); } catch (e6) {}
  return true;
}
window.playIndex = playIndex;

// Re-bind list play clicks (in case older handlers closed over broken playIndex)
(function rebindPlayClicks() {
  var list = document.getElementById("list");
  if (!list || list._lygoPlayBound) return;
  list._lygoPlayBound = true;
  list.addEventListener("click", function (ev) {
    var btn = ev.target && ev.target.closest && ev.target.closest("[data-play]");
    var row = ev.target && ev.target.closest && ev.target.closest(".row[data-i]");
    if (btn) {
      ev.preventDefault();
      ev.stopPropagation();
      var i = +btn.getAttribute("data-play");
      if (i === current && audio && !audio.paused) {
        audio.pause();
        try { updatePlayBtn(); } catch (e) {}
        return;
      }
      playIndex(i);
      return;
    }
    if (row && !ev.target.closest("button")) {
      playIndex(+row.getAttribute("data-i"));
    }
  }, true);
})();

var _btnPlay = document.getElementById("btn-play");
if (_btnPlay) {
  _btnPlay.onclick = function () {
    if (current < 0) {
      if (typeof filteredIdx !== "undefined" && filteredIdx.length) playIndex(filteredIdx[0]);
      else if (tracks && tracks.length) playIndex(0);
      return;
    }
    if (audio.paused) {
      audio.play().catch(function () { playIndex(current); });
    } else {
      audio.pause();
    }
    try { updatePlayBtn(); } catch (e) {}
  };
}
console.info("[listen] PLAYINDEX_FINAL ready, tracks=", (tracks && tracks.length) || 0);
"""


def main() -> int:
    html = LISTEN.read_text(encoding="utf-8")
    before = len(html)

    # --- Remove broken mangled lines (THE current syntax error) ---
    bad = "try { if (!audio.crossOrigin) audio./* no crossOrigin */ } catch (e) {}"
    count = html.count(bad)
    html = html.replace(bad, "/* fixed crossOrigin line */")
    print("removed exact bad lines:", count)

    # broader cleanup
    html = re.sub(
        r"try\s*\{\s*if\s*\(\s*!audio\.crossOrigin\s*\)\s*audio\./\*[\s\S]*?\*/\s*\}\s*catch\s*\(\s*e\s*\)\s*\{\s*\}",
        "/* fixed */",
        html,
    )
    html = re.sub(r"audio\./\*[^*]*\*/", "/*fixed*/", html)
    html = html.replace("/* no crossOrigin */", "/*fixed*/")

    # Clean single audio element
    html = re.sub(
        r"<audio\b[^>]*>\s*(?:</audio>\s*)*",
        '<audio id="audio" controls preload="none" playsinline></audio>\n',
        html,
        count=1,
    )

    # Kill MediaElementSource hard
    html = html.replace(
        "createMediaElementSource(audio)",
        "null /* no MediaElementSource */",
    )

    # Force maybeCrossfade off
    html = re.sub(
        r"function maybeCrossfade\(\)\s*\{",
        "function maybeCrossfade(){ return;",
        html,
        count=1,
    )

    # Remove previous FINAL blocks
    html = re.sub(
        r"// === PLAYINDEX_FINAL[\s\S]*?PLAYINDEX_FINAL ready[\s\S]*?\n",
        "",
        html,
    )

    idx = html.rfind("</script>")
    if idx < 0:
        raise SystemExit("no script end")
    html = html[:idx] + "\n" + FINAL + "\n" + html[idx:]

    if len(html) < before * 0.8:
        raise SystemExit(f"shrink {before}->{len(html)}")

    LISTEN.write_text(html, encoding="utf-8")
    shutil.copy2(LISTEN, DOCS)

    # syntax check main script
    scripts = re.findall(
        r"<script(?![^>]*application/json)[^>]*>([\s\S]*?)</script>", html
    )
    main_js = max(scripts, key=len)
    tmp = Path(__file__).resolve().parent.parent / "_tmp_listen_main.js"
    tmp.write_text(main_js, encoding="utf-8")
    r = subprocess.run(["node", "--check", str(tmp)], capture_output=True, text=True)
    print("node exit", r.returncode)
    if r.returncode != 0:
        print(r.stderr[:2000])
        # show bad line context
        m = re.search(r":(\d+)\n", r.stderr or "")
        if m:
            ln = int(m.group(1))
            lines = main_js.splitlines()
            for n in range(max(0, ln - 4), min(len(lines), ln + 4)):
                mark = ">>" if n + 1 == ln else "  "
                print(f"{mark}{n+1}: {lines[n][:180]}")
        return 1

    print("OK syntax")
    print("len", len(html))
    print("bad leftover", "audio./*" in html)
    print("PLAYINDEX_FINAL", "PLAYINDEX_FINAL" in html)
    print("audio tag", re.search(r"<audio[^>]*>", html).group(0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
