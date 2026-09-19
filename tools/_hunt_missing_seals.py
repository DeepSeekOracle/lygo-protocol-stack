#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(r"I:\E Drive")
vault = json.loads(
    (ROOT / "lygo-protocol-stack/docs/data-vault/data/canonical_seals_public.json").read_text(
        encoding="utf-8"
    )
)
have = set()
for s in vault["seals"]:
    m = re.match(r"^SEAL_(\d+)$", s["id"])
    if m:
        have.add(int(m.group(1)))
missing = [i for i in range(0, 401) if i not in have]
print("missing", len(missing), missing[:60])

# SEAL_286 md
p286 = ROOT / "lygo-protocol-stack/docs/SEAL_286_RECURSIVE_ETHICS.md"
print("SEAL_286 md exists", p286.exists(), "bytes", p286.stat().st_size if p286.exists() else 0)
if p286.exists():
    print(p286.read_text(encoding="utf-8", errors="replace")[:500])

# brain snapshot
p = ROOT / "LYRA_CORE/openclaw_backups/backup_20260608_222729/memory/state/brain_snapshot_20260603_020132.json"
text = p.read_text(encoding="utf-8", errors="replace")
ids = sorted(set(re.findall(r'"SEAL_(\d{3,}[A-Za-z]*)"', text)))
print("brain seal ids", len(ids))
print("brain >=270", [i for i in ids if int(re.match(r"\d+", i).group()) >= 270][:50])

# recursive ethics whitepapers for SEAL_
rec = ROOT / "Recursive Ethics Through Immutable Seal Chains/Recursive Ethics Through Immutable.txt"
if rec.exists():
    t = rec.read_text(encoding="utf-8", errors="replace")
    titles = re.findall(r"^White Paper:\s*(SEAL_[^\n]+)", t, re.M)
    print("whitepaper titles", len(titles))
    print(titles[:30])
    for n in missing[:40]:
        if re.search(rf"SEAL_0*{n}\b", t):
            print("rec has", n)

# Search docs for SEAL_27x definitions
docs = ROOT / "lygo-protocol-stack/docs"
for p in docs.rglob("*"):
    if not p.is_file() or p.suffix.lower() not in {".md", ".txt", ".json"}:
        continue
    if p.stat().st_size > 2_000_000:
        continue
    try:
        t = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    hits = [n for n in missing if re.search(rf"\[SEAL_0*{n}\]|\"SEAL_0*{n}\"|SEAL_0*{n}:", t)]
    if hits:
        print("docs hit", p, hits[:20])
