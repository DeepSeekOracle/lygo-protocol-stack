from pathlib import Path
import re
p = Path(r"I:/E Drive/Excavationpro/excavationpro-listen.html")
h = p.read_text(encoding="utf-8")
# cache bust plugin
h2 = h.replace("play-listing.js?v=2", "play-listing.js?v=3")
h2 = h2.replace("play-listing.js?v=1", "play-listing.js?v=3")
# SW registration
h2 = re.sub(r"sw-listen\.js\?v=\d+", "sw-listen.js?v=5", h2)
if "sw-listen.js" in h2 and "sw-listen.js?v=" not in h2:
    h2 = h2.replace("sw-listen.js", "sw-listen.js?v=5")
# CACHE_BUST comment
h2 = re.sub(r"CACHE_BUST_v\d+", "CACHE_BUST_v5", h2)
if h2 != h:
    p.write_text(h2, encoding="utf-8")
    print("listen.html updated")
else:
    print("no string changes needed; checking contents")
print("plugin v3", "play-listing.js?v=3" in h2)
print("sw v5", "sw-listen.js?v=5" in h2)
