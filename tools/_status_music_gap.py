import json
from pathlib import Path

vault = Path(r"I:\E Drive\MUSIC_VAULT\manifest\vault_index.json")
stream = Path(r"I:\E Drive\MUSIC_VAULT\public_stream")
pl = Path(r"I:\E Drive\lygo-protocol-stack\data\music_catalog\public_stream_playlist.json")

d = json.loads(vault.read_text(encoding="utf-8")) if vault.exists() else {}
objs = d.get("objects") or []
stats = d.get("stats") or {}
print("VAULT unique:", len(objs))
print("  new_this_scan:", stats.get("new_objects_this_scan"))
print("  total_gb:", stats.get("total_gb"))
print("  merkle:", (d.get("merkle_root") or "")[:40])

n_stream = len(list(stream.glob("*.mp3"))) if stream.is_dir() else 0
print("STREAM mp3 on disk:", n_stream)
missing = 0
for o in objs:
    h = o.get("sha256")
    if not h:
        continue
    if not (stream / f"{h}.mp3").is_file():
        missing += 1
print("vault missing stream file:", missing)

if pl.exists():
    p = json.loads(pl.read_text(encoding="utf-8"))
    print("PLAYLIST tracks:", len(p.get("tracks") or []))
    print("  base:", (p.get("public_base_url") or "")[:70])
else:
    print("PLAYLIST: missing")

act = 0
for o in objs:
    for path in o.get("paths") or []:
        parts = path.replace("/", "\\").split("\\")
        if any(x.lower() == "actors" for x in parts):
            act += 1
            break
print("Actors path objects:", act)
print("scan_roots count:", len(d.get("scan_roots") or []))
