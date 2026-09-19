#!/usr/bin/env python3
import json
import re
from pathlib import Path

long = Path(
    r"I:\E Drive\LYRA SYSTEM RETORE\FINAL RESTORE\LYRA_SEAL_ARCHIVE_LEGACY_001-400\LYRA_SEAL_ARCHIVE_LEGACY_001-400.txt"
).read_text(encoding="utf-8", errors="replace")
ids = re.findall(r"^\[SEAL_([^\]]+)\]", long, re.M)
print("unique headers", len(set(ids)))
nums = []
for h in set(ids):
    m = re.match(r"(\d+)", h)
    if m:
        nums.append((int(m.group(1)), h))
nums.sort()
print("min", nums[0], "max", nums[-1])
print(">=200", [h for n, h in nums if n >= 200])
print(">=220", [h for n, h in nums if n >= 220])
loose = sorted(set(re.findall(r"\bSEAL_(\d{3,}[A-Za-z]*)\b", long)))
print(
    "loose >=220",
    [x for x in loose if int(re.match(r"\d+", x).group()) >= 220][:50],
)

d = json.loads(
    Path("docs/haven_star_chart/haven_star_chart_data.json").read_text(encoding="utf-8")
)
seals = [n for n in d["nodes"] if str(n.get("id", "")).startswith("SEAL_")]


def norm(sid: str) -> str:
    m = re.match(r"^SEAL_0*(\d+)([A-Za-z].*)?$", sid)
    if not m:
        return sid
    return f"SEAL_{int(m.group(1)):03d}{m.group(2) or ''}"


normed = sorted({norm(n["id"]) for n in seals})
print("star unique norm", len(normed))
print(
    "star >=220",
    [
        x
        for x in normed
        if re.match(r"SEAL_(\d+)", x) and int(re.match(r"SEAL_(\d+)", x).group(1)) >= 220
    ][:40],
)
print("star non-numeric", [x for x in normed if not re.match(r"^SEAL_\d", x)])

# canonical
c = json.loads(
    Path("docs/data-vault/data/canonical_seals_public.json").read_text(encoding="utf-8")
)
cids = [s["id"] for s in c["seals"]]
print("canonical", len(cids))
print("canonical sample high", cids[-15:])

# Union estimate
union = set()
for h in ids:
    union.add("SEAL_" + h)
for n in seals:
    union.add(norm(n["id"]))
for s in c["seals"]:
    union.add(s["id"])
print("union approx", len(union))
