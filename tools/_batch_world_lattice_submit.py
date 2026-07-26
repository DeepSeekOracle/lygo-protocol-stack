#!/usr/bin/env python3
"""Prepare + submit world lattice proposals to Haven Star Chart pending queue."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "protocol0_byte_entropy_filter" / "src" / "python"))
sys.path.insert(0, str(ROOT / "tools"))

from haven_star_chart_gate import (  # noqa: E402
    build_attestation,
    load_registry_ids,
    validate_submission,
)


def sanitize_id(raw: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_]+", "_", raw.upper()).strip("_")
    s = re.sub(r"_+", "_", s)
    if not s.startswith(("LATTICE_", "PORTAL_", "NODE_", "SEAL_", "CHAMPION_")):
        s = "LATTICE_" + s
    if len(s) > 64:
        s = s[:56] + hashlib.sha256(s.encode()).hexdigest()[:8].upper()
    return s


def to_node(p: dict) -> dict:
    kind = "lattice"
    pid = p.get("proposal_id") or p.get("egg_id") or p.get("label") or "X"
    if p.get("kind") == "lattice_surface":
        kind = "portal"
        nid = sanitize_id("PORTAL_" + str(pid).replace("surface-", ""))
    else:
        eid = p.get("egg_id") or pid
        layer = p.get("layer") or ""
        prefix = (
            "EGG_SOV_"
            if "sovereign" in layer or "B_" in layer
            else "EGG_CLS_"
            if "classic" in layer or "A_" in layer
            else "EGG_"
        )
        nid = sanitize_id("LATTICE_" + prefix + str(eid))
        kind = "lattice"

    name = (p.get("label") or p.get("egg_id") or nid)[:120]
    url = p.get("url")
    if not url and p.get("links"):
        links = p["links"]
        url = (
            links.get("retrieval")
            or links.get("snapshot")
            or links.get("doc")
            or next((v for v in links.values() if isinstance(v, str)), None)
        )

    node = {
        "id": nid,
        "kind": kind,
        "name": name,
        "equation": "Truth = ∇·(Light × Lattice) ⊗ Δ9 · 963Hz",
        "glyph": "✦",
        "tone": "963Hz",
        "tags": ["KERNEL", "LATTICE", "WORLD", "VERIFY", "LYGO"],
        "connections": ["SEAL_000", "LATTICE_KERNEL_EGGS", "LATTICE_NETWORK_BUILDER"],
        "layer": 3,
        "urls": {},
        "meta": {
            "source_proposal_id": p.get("proposal_id"),
            "egg_layer": p.get("layer"),
            "egg_id": p.get("egg_id"),
            "content_sha256": p.get("content_sha256"),
            "registry_merkle_root": p.get("registry_merkle_root"),
        },
    }
    if url:
        node["urls"]["primary"] = url
    if p.get("links"):
        node["urls"].update({k: v for k, v in p["links"].items() if isinstance(v, str)})
    return node


def main() -> int:
    consent = "--i-consent" in sys.argv
    dry = "--dry-run" in sys.argv
    if not consent and not dry:
        print(json.dumps({"verdict": "BLOCKED", "reason": "pass --i-consent or --dry-run"}))
        return 2

    proposals = json.loads(
        (ROOT / "docs" / "star_chart_egg_map_proposals.json").read_text(encoding="utf-8")
    )
    reg_ids = load_registry_ids()

    nodes: dict[str, dict] = {}
    for p in proposals.get("proposals") or []:
        n = to_node(p)
        if n["id"] in reg_ids:
            continue
        nodes[n["id"]] = n

    extras = [
        {
            "id": "LATTICE_WORLD_LAYER_C",
            "kind": "lattice",
            "name": "World Lattice Layer C — External Anchor",
            "equation": "World = Mirror(LocalA ⊕ LocalB) ⊗ Δ9 · 963Hz",
            "glyph": "🌐",
            "tone": "963Hz",
            "tags": ["WORLD", "LAYER_C", "EXTERNAL", "VERIFY"],
            "connections": ["SEAL_000", "LATTICE_KERNEL_EGGS", "LATTICE_NETWORK_BUILDER"],
            "urls": {
                "doc": "https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/docs/WORLD_LATTICE_LAYER.md",
                "skill": "https://clawhub.ai/deepseekoracle/skills/lygo-external-lattice-anchor",
                "chart": "https://deepseekoracle.github.io/lygo-protocol-stack/HavenStarChart.html",
            },
            "layer": 3,
        },
        {
            "id": "LATTICE_SOVEREIGN_SEEDS",
            "kind": "lattice",
            "name": "Sovereign Seeds Vault (Layer B)",
            "equation": "Seed = SHA256(payload) → MerkleRoot · 963Hz",
            "glyph": "🌱",
            "tone": "963Hz",
            "tags": ["SOVEREIGN", "SEED", "LAYER_B"],
            "connections": ["SEAL_000", "LATTICE_KERNEL_EGGS", "LATTICE_NETWORK_BUILDER"],
            "urls": {
                "snapshot": "https://raw.githubusercontent.com/DeepSeekOracle/lygo-protocol-stack/main/docs/sovereign_seeds_snapshot/registry.json",
                "skill": "https://clawhub.ai/deepseekoracle/skills/lygo-sovereign-kernel-seeder",
            },
            "layer": 3,
        },
    ]
    for ex in extras:
        if ex["id"] not in reg_ids:
            nodes[ex["id"]] = ex

    for n in nodes.values():
        n["connections"] = [c for c in (n.get("connections") or []) if c in reg_ids or c == "SEAL_000"]
        if not n["connections"]:
            n["connections"] = ["SEAL_000"]

    batch_dir = ROOT / "data" / "haven_star_chart" / "submissions" / "batch_world_lattice"
    batch_dir.mkdir(parents=True, exist_ok=True)

    accept_files: list[Path] = []
    rejected: list[dict] = []
    for nid, node in sorted(nodes.items()):
        att = build_attestation(
            "lygo-external-lattice-anchor",
            "lygo-external-lattice-anchor",
            node,
        )
        sub = {
            "signature": "Δ9Φ963-HAVEN-STAR-SUBMISSION-v1",
            "submitter_type": "aligned_agent",
            "agent_attestation": att,
            "node": node,
            "content_sha256": att["content_sha256"],
        }
        gate = validate_submission(sub)
        path = batch_dir / f"{nid}.json"
        path.write_text(json.dumps({**sub, "gate_result": gate}, indent=2), encoding="utf-8")
        if gate["all_pass"]:
            accept_files.append(path)
        else:
            rejected.append({"id": nid, "errors": gate["errors"]})

    report = {
        "prepared": len(nodes),
        "gate_accept": len(accept_files),
        "gate_reject": len(rejected),
        "rejected_sample": rejected[:10],
        "batch_dir": str(batch_dir),
        "dry_run": dry,
    }

    if dry:
        print(json.dumps(report, indent=2))
        return 0 if not rejected or accept_files else 1

    # submit each accepted file via haven_star_chart_submit
    submit_tool = ROOT / "tools" / "haven_star_chart_submit.py"
    submitted_ok = []
    submit_fail = []
    for path in accept_files:
        cp = subprocess.run(
            [
                sys.executable,
                str(submit_tool),
                str(path),
                "--agent-id",
                "lygo-external-lattice-anchor",
                "--skill-slug",
                "lygo-external-lattice-anchor",
                "--i-consent",
            ],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        if cp.returncode == 0:
            submitted_ok.append(path.name)
        else:
            submit_fail.append({"file": path.name, "out": (cp.stdout or "")[:300], "err": (cp.stderr or "")[:200]})

    report["submitted_ok"] = submitted_ok
    report["submit_fail"] = submit_fail[:10]
    report["submit_ok_count"] = len(submitted_ok)
    print(json.dumps(report, indent=2))
    return 0 if submitted_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
