from pathlib import Path
t = Path(r"I:\E Drive\Excavationpro\excavationpro-listen.html").read_text(encoding="utf-8")
print("len", len(t))
print("style open", t.count("<style"))
print("style close", t.count("</style>"))
print("body", t.find("<body"))
print("head end", t.find("</head>"))
print("tools", t.find('class="tools"'))
print("sticky", t.find("sticky-top"))
print("play-trophy", t.find("play-trophy"))
print("copyright", t.find("copyright-notice"))
print("first 300 chars:", t[:300])
# find style locations
idx = 0
while True:
    i = t.find("<style", idx)
    if i < 0:
        break
    print("style at", i, repr(t[i : i + 40]))
    idx = i + 1
idx = 0
while True:
    i = t.find("</style>", idx)
    if i < 0:
        break
    print("end style at", i)
    idx = i + 1
