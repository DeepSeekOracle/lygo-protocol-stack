#!/usr/bin/env python3
"""
Layer D badge: Phase-2 alignment badge + A/B/C roots + mesh identity.

Safe for gossip: no secrets, no private paths required on wire.
Signature: Delta9Phi963-LIVING-MESH-BADGE-v1
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

SIG = "Delta9Phi963-LIVING-MESH-BADGE-v1"


def _load(p: Path) -> dict | None:
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _sha_file(p: Path) -> str | None:
    if not p.is_file():
        return None
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_living_badge(*, quick: bool = True, node_id: str | None = None) -> dict:
    from verify_alignment_badge import collect_badge  # noqa: E402

    base = collect_badge(quick=quick)
    host = socket.gethostname()
    nid = node_id or os.environ.get("LYGO_NODE_ID") or f"NODE_{host}"

    classic = _load(ROOT / "data" / "kernel_eggs" / "registry.json") or _load(
        ROOT / "docs" / "KernelEggRegistry.json"
    )
    sovereign = _load(ROOT / "data" / "sovereign_seeds" / "registry.json") or _load(
        ROOT / "docs" / "sovereign_seeds_snapshot" / "registry.json"
    )
    public_man = _load(ROOT / "docs" / "public_verify_manifest.json")
    world = _load(ROOT / "tests" / "world_lattice_last_run.json")
    layers = _load(ROOT / "tests" / "kernel_layers_last_run.json")
    star_meta = _load(ROOT / "docs" / "haven_star_chart" / "haven_star_chart_meta.json")

    a_root = (classic or {}).get("registry_merkle_root") or base.get("kernel_egg_registry_merkle_root")
    b_root = (sovereign or {}).get("registry_merkle_root")
    c_sha = _sha_file(ROOT / "docs" / "public_verify_manifest.json")
    star_sha = (star_meta or {}).get("registry_sha256") or _sha_file(
        ROOT / "docs" / "haven_star_chart" / "haven_star_chart_data.json"
    )

    # alignment summary for mesh
    local_status = "ALIGNED"
    if layers and layers.get("verdict") == "QUARANTINE":
        local_status = "QUARANTINE"
    elif world and world.get("verdict") == "LOCAL_QUARANTINE":
        local_status = "QUARANTINE"
    elif layers and layers.get("verdict") == "ALIGNED":
        local_status = "ALIGNED"
    elif base.get("status") in ("ALIGNED", "NEEDS_FIX", "UNKNOWN"):
        # map phase2 statuses
        local_status = "ALIGNED" if base.get("status") == "ALIGNED" else str(base.get("status"))

    badge = {
        **base,
        "signature": SIG,
        "layer": "D",
        "node_id": nid,
        "hostname": host,
        "living_mesh": {
            "version": "1.0.0",
            "local_status": local_status,
            "roots": {
                "A_classic_merkle": a_root,
                "B_sovereign_merkle": b_root,
                "C_public_manifest_sha256": c_sha,
                "star_chart_registry_sha256": star_sha,
            },
            "counts": {
                "classic_eggs": len((classic or {}).get("eggs") or [])
                if isinstance((classic or {}).get("eggs"), list)
                else len((classic or {}).get("eggs") or {})
                if isinstance((classic or {}).get("eggs"), dict)
                else None,
                "sovereign_eggs": len((sovereign or {}).get("eggs") or {})
                if isinstance((sovereign or {}).get("eggs"), dict)
                else None,
            },
            "public_endpoints_hint": [
                "https://deepseekoracle.github.io/lygo-protocol-stack/",
                "https://deepseekoracle.github.io/lygo-protocol-stack/HavenStarChart.html",
                "https://raw.githubusercontent.com/DeepSeekOracle/lygo-protocol-stack/main/docs/network_builder/IMMUTABLE_ANCHORS.json",
            ],
            "protection": {
                "local_is_authority": True,
                "gossip_summaries_only": True,
                "no_egg_payloads_on_wire": True,
                "consent_for_join": True,
            },
            "world_verdict": (world or {}).get("verdict"),
            "ab_verdict": (layers or {}).get("verdict"),
            "public_manifest_present": bool(public_man),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # compact hash of mesh roots for quick compare
    root_blob = json.dumps(badge["living_mesh"]["roots"], sort_keys=True).encode("utf-8")
    badge["living_mesh"]["roots_digest"] = hashlib.sha256(root_blob).hexdigest()
    return badge


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--node-id", default="")
    ap.add_argument("--quick", action="store_true", default=True)
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    badge = collect_living_badge(quick=not args.full, node_id=args.node_id or None)
    text = json.dumps(badge, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
