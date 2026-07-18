from pathlib import Path
t = Path(r"I:\E Drive\Excavationpro\excavationpro-listen.html").read_text(encoding="utf-8")
checks = [
    'id="play-trophy"',
    "trophy-total",
    "hits.dwyl.com",
    "lygo_listen_play_ledger_v1",
    "MIN_SECONDS",
    "BPMFINDER.CA",
    "sticky-top",
    "copyright-notice",
    "LISTEN PORTAL v3",
    "mini-player",
    "smart-filters",
]
for c in checks:
    print(("OK" if c in t else "MISS"), c)
print("len", len(t))
