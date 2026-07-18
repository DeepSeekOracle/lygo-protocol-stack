import json, re
from pathlib import Path
html = Path(r"I:/E Drive/Excavationpro/excavationpro-listen.html").read_text(encoding="utf-8")
m = re.search(r'<script id="boot"[^>]*>(.*?)</script>', html, re.S)
boot = json.loads(m.group(1))
tracks = boot["playlist"]["tracks"]
print("boot tracks", len(tracks))
flat = shard = other = 0
for t in tracks:
    u = t.get("stream_url") or ""
    if re.search(r"/stream/[0-9a-f]{2}/[0-9a-f]+\.mp3", u):
        shard += 1
    elif re.search(r"/stream/[0-9a-f]{64}\.mp3", u):
        flat += 1
    else:
        other += 1
print("flat", flat, "shard", shard, "other", other)
pl = json.loads(Path(r"I:/E Drive/lygo-protocol-stack/data/music_catalog/public_stream_playlist.json").read_text(encoding="utf-8"))
by = {t["sha256"]: t for t in pl["tracks"] if t.get("sha256")}
mismatch = 0
example = None
for t in tracks:
    cat = by.get(t.get("sha256"))
    if cat and cat.get("stream_url") and t.get("stream_url") != cat.get("stream_url"):
        mismatch += 1
        if example is None:
            example = (t.get("stream_url"), cat.get("stream_url"))
print("mismatches", mismatch)
if example:
    print("boot", example[0][-100:])
    print("cat ", example[1][-100:])
