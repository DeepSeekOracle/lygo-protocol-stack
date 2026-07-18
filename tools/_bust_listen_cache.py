#!/usr/bin/env python3
from pathlib import Path
import re

paths = [
    Path(r"I:\E Drive\Excavationpro\excavationpro-listen.html"),
    Path(r"I:\E Drive\lygo-protocol-stack\docs\excavationpro-listen.html"),
]

nuke = r"""
// CACHE_BUST_v4: drop stale PWA shells that pinned broken play-count builds
(function(){
  if (window.caches && caches.keys) {
    caches.keys().then(function(keys){
      keys.forEach(function(k){
        if (/excavationpro-listen-shell-v[123]/.test(k) || k === 'excavationpro-listen-shell-v2') {
          caches.delete(k);
          console.info('[listen] deleted old cache', k);
        }
      });
    });
  }
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.getRegistrations().then(function(regs){
      regs.forEach(function(reg){
        // re-register will pick up ?v=4
        console.info('[listen] SW scope', reg.scope);
      });
    });
  }
})();
"""

for p in paths:
    t = p.read_text(encoding="utf-8")
    if "listen-build:" not in t:
        t = t.replace("<head>", "<head>\n<!-- listen-build: eab3f05-playback-restore-v4 -->\n", 1)
    t = re.sub(
        r"navigator\.serviceWorker\.register\(\s*['\"]\./sw-listen\.js(?:\?[^'\"]*)?['\"]",
        "navigator.serviceWorker.register('./sw-listen.js?v=4'",
        t,
    )
    if "CACHE_BUST_v4" not in t:
        idx = t.rfind("</script>")
        if idx > 0:
            t = t[:idx] + "\n" + nuke + "\n" + t[idx:]
    p.write_text(t, encoding="utf-8")
    print(p.name, len(t), "v4", "sw-listen.js?v=4" in t, "bust", "CACHE_BUST_v4" in t)

# also copy SW to docs if needed
sw = Path(r"I:\E Drive\Excavationpro\sw-listen.js")
docs_sw = Path(r"I:\E Drive\lygo-protocol-stack\docs\sw-listen.js")
if sw.exists():
    docs_sw.write_text(sw.read_text(encoding="utf-8"), encoding="utf-8")
    print("synced sw-listen.js")
