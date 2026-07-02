from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "stack"))

from merkle_sync import LygoMerkleTree, sync_round
from distributed_mycelium_mesh import DistributedMyceliumMesh
from harmonic_consensus_mesh import HarmonicConsensusEngine, ProposalManager
from sovereign_lattice_mesh import SovereignLatticeMesh


def test_merkle_converge_three_rounds():
    a = {f"n{i}": {"v": i} for i in range(2)}
    b = {**a, "n2": {"v": 2}}
    catalog = dict(a)
    for _ in range(3):
        catalog, _ = sync_round(catalog, b)
    t = LygoMerkleTree()
    tb = LygoMerkleTree()
    assert t.rebuild_tree(catalog) == tb.rebuild_tree(b)


def test_mycelium_store_reconstruct():
    td = Path(tempfile.mkdtemp())
    m = DistributedMyceliumMesh("n1", td)
    for n in ("n1", "n2", "n3"):
        m.register_mesh_node(n)
    payload = "x" * 1200
    m.store("d1", payload)
    m.simulate_node_failure("n2")
    r = m.reconstruct("d1")
    assert r["ok"] is True
    assert r["data"] == payload


def test_harmonic_consensus_five_nodes():
    pm = ProposalManager()
    p = pm.propose("n0", "Enable biometric scaling")
    pid = p["proposal_id"]
    for i, (v, mass) in enumerate([(9, 1.3), (9, 1.1), (6, 0.9), (3, 0.8), (-1, 0.2)]):
        pm.vote(pid, f"node_{i}", v, mass)
    res = pm.finalize(pid)
    assert res["decision"] in (3, 6, 9)
    assert res["participants"] == 5


def test_slm_runtime_converge():
    td = Path(tempfile.mkdtemp())
    slm = SovereignLatticeMesh("local", td)
    slm.register_mesh_node("peer_b")
    remote = {
        "peer_b": {"alignment": "ALIGNED"},
        "peer_c": {"alignment": "ALIGNED"},
    }
    out = slm.converge([remote], max_rounds=3)
    assert out["badge_count"] >= 2