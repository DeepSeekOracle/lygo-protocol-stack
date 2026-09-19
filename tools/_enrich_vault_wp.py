from pathlib import Path
import re, json, hashlib
from datetime import datetime, timezone

def redact(s):
    s = re.sub(r"(?i)(api[_-]?key|secret|password|token|bearer|moltbook_sk_|moltx_sk_|nvapi-|ghp_)[=:\s]+\S+", "[REDACTED]", s)
    s = re.sub(r"[A-Za-z]:\\[^\s\"']+", "[REDACTED_PATH]", s)
    return s

rec = Path(r"I:\E Drive\Recursive Ethics Through Immutable Seal Chains\Recursive Ethics Through Immutable.txt").read_text(encoding="utf-8", errors="replace")
parts = re.split(r"(?m)^(?=(?:White Paper:\s*)?SEAL_\d+)", rec)
papers = []
for p in parts:
    p = p.strip()
    if len(p) < 200:
        continue
    first = p.splitlines()[0][:120]
    if not re.search(r"SEAL_\d+", first):
        continue
    body = redact(p[:6000])
    papers.append({"title": first.strip(), "body": body, "sha12": hashlib.sha256(body.encode()).hexdigest()[:12]})
seen = set()
out = []
for x in papers:
    if x["title"] in seen:
        continue
    seen.add(x["title"])
    out.append(x)
out = out[:80]
obj = {
    "signature": "Delta9Phi963-DATA-VAULT-WHITEPAPERS-v2",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "count": len(out),
    "papers": out,
}
path = Path(r"I:\E Drive\lygo-protocol-stack\docs\data-vault\data\whitepaper_excerpts.json")
path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
Path(r"E:\LYGO_LATTICE_MEMORY\DATA_VAULT_RECOVERY\json\whitepaper_excerpts.json").write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
print("whitepapers", len(out))
