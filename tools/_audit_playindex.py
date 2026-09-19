from pathlib import Path
import re
h = Path(r"I:/E Drive/Excavationpro/excavationpro-listen.html").read_text(encoding="utf-8")
# playIndex defs context
for m in re.finditer(r"function playIndex|window\.playIndex\s*=", h):
    i = m.start()
    print("---", m.group(0), "at", i)
    print(h[i:i+200].replace("\n"," ")[:200])
# crossOrigin on audio
for m in re.finditer(r".{0,40}crossOrigin.{0,80}", h):
    print("crossOrigin:", m.group(0).replace("\n"," ")[:120])
# head adsense
head = h.split("</head>")[0]
print("head adsense script", "pagead2.googlesyndication.com" in head)
print("body adsense load?", "ADSENSE_SRC" in h or "loadAdSense" in h)
