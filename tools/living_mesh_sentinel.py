#!/usr/bin/env python3
"""
Living mesh sentinel: local badge + optional peer compares + scale sim health.
Army / OpenClaw friendly single command.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--peer", action="append", default=[])
    ap.add_argument("--run-sim", action="store_true", help="Run 100-node gossip scale sim")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    from collect_living_mesh_badge import collect_living_badge

    badge = collect_living_badge(quick=True)
    peers_file = ROOT / "data" / "living_mesh" / "peers.json"
    peers = []
    if peers_file.is_file():
        peers = [p.get("base_url") for p in json.loads(peers_file.read_text(encoding="utf-8")).get("peers") or []]
    peers = list({*(args.peer or []), *peers})

    compare = None
    if peers:
        cmd = [sys.executable, str(TOOLS / "living_mesh_compare.py"), "--json"]
        for p in peers:
            cmd.extend(["--peer", p])
        cp = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
        try:
            compare = json.loads(cp.stdout or "{}")
        except json.JSONDecodeError:
            compare = {"error": cp.stderr or cp.stdout}

    sim = None
    if args.run_sim:
        sim_tool = TOOLS / "run_mesh_scale_sim.py"
        if sim_tool.is_file():
            cp = subprocess.run(
                [sys.executable, str(sim_tool), "--nodes", "100", "--fanout", "2", "--no-pause"],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=120,
            )
            art = ROOT / "tests" / "mesh_scale_last_run.json"
            if art.is_file():
                sim = json.loads(art.read_text(encoding="utf-8"))
            else:
                sim = {"stdout": (cp.stdout or "")[-500:], "returncode": cp.returncode}

    report = {
        "signature": "Delta9Phi963-LIVING-MESH-SENTINEL-v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "node_id": badge.get("node_id"),
        "local_status": (badge.get("living_mesh") or {}).get("local_status"),
        "roots_digest": (badge.get("living_mesh") or {}).get("roots_digest"),
        "roots": (badge.get("living_mesh") or {}).get("roots"),
        "peer_compare": compare,
        "mesh_scale_sim": sim,
        "verdict": "SENTINEL_OK",
    }
    if (badge.get("living_mesh") or {}).get("local_status") == "QUARANTINE":
        report["verdict"] = "SENTINEL_QUARANTINE"
    elif compare and compare.get("verdict") == "MIXED":
        # forks visible is not fatal
        report["verdict"] = "SENTINEL_FORK_VISIBLE"

    out = ROOT / "tests" / "living_mesh_sentinel_last_run.json"
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass

    if args.json or True:
        print(json.dumps(report, indent=2))
    return 3 if report["verdict"] == "SENTINEL_QUARANTINE" else 0


if __name__ == "__main__":
    raise SystemExit(main())
