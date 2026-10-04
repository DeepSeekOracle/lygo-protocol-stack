"""Verify The Continuity Seed. Stdlib only. No network. No writes."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def load_poem() -> str:
    t = (HERE / "POEM.txt").read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return t.strip() + "\n"


def verify() -> dict:
    seed = json.loads((HERE / "CONTINUITY_SEED.json").read_text(encoding="utf-8"))
    poem = load_poem()
    got = sha256_text(poem)
    expect = seed.get("alignment_hash")
    axioms = seed.get("core_axioms") or []
    root_src = str(seed.get("seed_id") or "") + "\n" + "\n".join(axioms) + "\n" + got + "\n"
    root = sha256_text(root_src)
    poem_ok = got == expect
    root_ok = root == seed.get("lattice_root")
    n = len((HERE / "CONTINUITY_SEED.json").read_bytes())
    status = "CONTINUATION" if poem_ok and root_ok else "FORK"
    if not poem_ok:
        status = "QUARANTINE" if not poem_ok else status
    return {
        "ok": poem_ok and root_ok,
        "status": "CONTINUATION" if poem_ok and root_ok else ("QUARANTINE" if not poem_ok else "SUPERSEDES"),
        "alignment_hash": got,
        "alignment_match": poem_ok,
        "lattice_root": root,
        "lattice_match": root_ok,
        "json_bytes": n,
        "under_4kb": n < 4096,
        "seed_id": seed.get("seed_id"),
        "witness_chain": seed.get("witness_chain"),
    }


def main() -> int:
    r = verify()
    json.dump(r, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0 if r.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
