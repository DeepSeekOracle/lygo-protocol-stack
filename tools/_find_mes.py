from pathlib import Path
h = Path(r"I:/E Drive/Excavationpro/excavationpro-listen.html").read_text(encoding="utf-8")
idx = 0
while True:
    i = h.find("createMediaElementSource", idx)
    if i < 0: break
    print("--- at", i)
    print(h[max(0,i-200):i+200])
    idx = i + 1
