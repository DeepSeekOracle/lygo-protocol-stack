import json
from pathlib import Path

# Reads bundled canon only — no network, no user paths (see references/SECURITY.md).
canon_path = Path(__file__).resolve().parents[1] / "references" / "canon.json"
canon = json.loads(canon_path.read_text(encoding="utf-8"))
print(canon.get("lygo_mint_sha256") or "MISSING_HASH")