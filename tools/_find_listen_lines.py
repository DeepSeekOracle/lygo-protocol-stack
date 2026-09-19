from pathlib import Path
lines = Path(r"I:/E Drive/Excavationpro/excavationpro-listen.html").read_text(encoding="utf-8").splitlines()
keys = ("play-listing-mount", "LYGO_LISTEN_EXPORT", "v2 enhancements", 'id="audio"', "filter-chips", "</style>", "play-listing.js")
for i, l in enumerate(lines, 1):
    if any(k in l for k in keys):
        print(f"{i}: {l[:100]}")
