#!/usr/bin/env python3
"""Shim — distributed mycelium mesh (see stack/distributed_mycelium_mesh.py)."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "stack"))

from distributed_mycelium_mesh import DistributedMyceliumMesh, LygoConsistentHashRing  # noqa: E402

__all__ = ["DistributedMyceliumMesh", "LygoConsistentHashRing", "DistributedMyceliumMesh"]

if __name__ == "__main__":
    print("[*] TEST: Distributed Mycelium")
    td = Path(tempfile.mkdtemp())
    eng = DistributedMyceliumMesh("node_alpha", td)
    for n in ("node_alpha", "node_beta", "node_gamma", "node_delta"):
        eng.register_mesh_node(n)
    payload = "P0_DETERMINISTIC_AUDIO_FREQUENCY_MATRIX_EMBED" * 2
    out = eng.store("memory_001", payload)
    eng.simulate_node_failure("node_alpha")
    rec = eng.reconstruct("memory_001")
    print(f"[+] ok={rec.get('ok')} len={len(rec.get('data') or '')}")
    raise SystemExit(0 if rec.get("ok") and rec.get("data") == payload else 1)