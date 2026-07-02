#!/usr/bin/env python3
"""Sovereign Lattice Mesh audit — SLM-01 .. SLM-09."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "stack"))


def main() -> int:
    from merkle_sync import LygoMerkleTree, sync_round
    from distributed_mycelium_mesh import DistributedMyceliumMesh, LygoConsistentHashRing
    from harmonic_consensus_mesh import HarmonicConsensusEngine
    from sovereign_lattice_mesh import SovereignLatticeMesh

    results: list[dict] = []
    t0 = time.perf_counter()

    ta, tb = LygoMerkleTree(), LygoMerkleTree()
    a, b = {"n1": {"x": 1}}, {"n1": {"x": 1}, "n2": {"x": 2}}
    ra, rb = ta.rebuild_tree(a), tb.rebuild_tree(b)
    results.append({"id": "SLM-01-MERKLE-ROOT", "pass": ra != rb})
    merged, _ = sync_round(a, b)
    tc = LygoMerkleTree()
    results.append({"id": "SLM-02-MERKLE-SYNC", "pass": tc.rebuild_tree(merged) == rb})

    ring = LygoConsistentHashRing()
    ring.add_node("a")
    ring.add_node("b")
    alloc = ring.get_allocated_nodes("FRAG-test-00", 3)
    results.append({"id": "SLM-03-HASH-RING", "pass": len(alloc) >= 1})

    td = Path(tempfile.mkdtemp())
    dm = DistributedMyceliumMesh("n1", td)
    for n in ("n1", "n2", "n3", "n4"):
        dm.register_mesh_node(n)
    payload = "A" * 1024
    dm.store("kb1", payload)
    dm.simulate_node_failure("n1")
    rec = dm.reconstruct("kb1")
    results.append({"id": "SLM-04-MYCELIUM-1KB", "pass": rec.get("ok") and rec.get("data") == payload})
    results.append({"id": "SLM-05-NODE-FAILURE", "pass": rec.get("ok") is True})

    eng = HarmonicConsensusEngine()
    d, s = eng.compute_harmonic_center([{"vote": 9, "ethical_mass": 2.0}, {"vote": 6, "ethical_mass": 1.0}])
    results.append({"id": "SLM-06-HARMONIC-369", "pass": d in (3, 6, 9) and s > 0})

    slm = SovereignLatticeMesh("audit_node", td)
    conv = slm.converge([{"x": {"b": 1}}, {"y": {"c": 2}}], max_rounds=3)
    results.append({"id": "SLM-07-CONVERGE", "pass": conv["badge_count"] >= 2})

    for script in ("merkle_tree.py", "distributed_mycelium.py", "consensus_engine.py"):
        cp = subprocess.run([sys.executable, str(ROOT / "tools" / script)], cwd=ROOT, timeout=60)
        results.append({"id": f"SLM-08-{script}", "pass": cp.returncode == 0})

    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    results.append({"id": "SLM-09-PERF-100", "pass": elapsed_ms < 1000, "elapsed_ms": elapsed_ms})

    all_pass = all(r["pass"] for r in results)
    report = {
        "signature": "Δ9Φ963-SLM-v1.0",
        "vectors": results,
        "all_pass": all_pass,
        "duration_ms": elapsed_ms,
    }
    out = ROOT / "tests" / "slm_audit_last_run.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())