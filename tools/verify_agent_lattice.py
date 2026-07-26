#!/usr/bin/env python3
"""
Full agent lattice verify: living mesh (optional) + identity + announce/gossip + sentinel.
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--skip-mesh", action="store_true")
    ap.add_argument("--peer", action="append", default=[])
    ap.add_argument("--run-gossip", action="store_true")
    args = ap.parse_args()

    report = {
        "signature": "Delta9Phi963-AGENT-LATTICE-VERIFY-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "layers": {},
        "verdict": "AGENT_LATTICE_ALIGNED",
    }

    if not args.skip_mesh:
        mesh = TOOLS / "verify_living_mesh.py"
        if mesh.is_file():
            cmd = [sys.executable, str(mesh), "--json", "--skip-public"]
            p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
            try:
                report["layers"]["D_living_mesh"] = json.loads(p.stdout or "{}")
            except json.JSONDecodeError:
                report["layers"]["D_living_mesh"] = {"verdict": "ERROR"}
            if report["layers"]["D_living_mesh"].get("verdict") == "LOCAL_QUARANTINE":
                report["verdict"] = "LOCAL_QUARANTINE"

    # identity
    id_cmd = [sys.executable, str(TOOLS / "agent_lattice_identity.py"), "--json"]
    pi = subprocess.run(id_cmd, cwd=str(ROOT), capture_output=True, text=True)
    try:
        report["layers"]["identity"] = json.loads(pi.stdout or "{}")
    except json.JSONDecodeError:
        report["layers"]["identity"] = {"error": pi.stdout}

    # gossip or announce
    if args.run_gossip or args.peer:
        gcmd = [sys.executable, str(TOOLS / "agent_lattice_gossip_tick.py")]
        for peer in args.peer or []:
            gcmd.extend(["--peer", peer])
        pg = subprocess.run(gcmd, cwd=str(ROOT), capture_output=True, text=True)
        try:
            report["layers"]["gossip"] = json.loads(pg.stdout or "{}")
        except json.JSONDecodeError:
            report["layers"]["gossip"] = {"verdict": "ERROR", "raw": (pg.stdout or "")[:400]}
    else:
        acmd = [sys.executable, str(TOOLS / "agent_lattice_announce.py")]
        pa = subprocess.run(acmd, cwd=str(ROOT), capture_output=True, text=True)
        try:
            report["layers"]["announce"] = json.loads(pa.stdout or "{}")
        except json.JSONDecodeError:
            report["layers"]["announce"] = {"verdict": "ERROR"}

    scmd = [sys.executable, str(TOOLS / "agent_lattice_sentinel.py"), "--json"]
    for peer in args.peer or []:
        scmd.extend(["--peer", peer])
    ps = subprocess.run(scmd, cwd=str(ROOT), capture_output=True, text=True)
    try:
        report["layers"]["sentinel"] = json.loads(ps.stdout or "{}")
    except json.JSONDecodeError:
        report["layers"]["sentinel"] = {"verdict": "ERROR"}

    if report["verdict"] != "LOCAL_QUARANTINE":
        sver = (report["layers"].get("sentinel") or {}).get("verdict")
        if sver == "SENTINEL_QUARANTINE":
            report["verdict"] = "LOCAL_QUARANTINE"
        elif sver == "SENTINEL_BLOCKED":
            report["verdict"] = "AGENT_LATTICE_BLOCKED"
        elif sver == "SENTINEL_PEERS_DOWN":
            report["verdict"] = "AGENT_LATTICE_ALIGNED_PEERS_WARN"

    out = ROOT / "tests" / "agent_lattice_last_run.json"
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass

    print(json.dumps(report, indent=2) if args.json else f"verdict={report['verdict']}")
    if not args.json:
        print(json.dumps(report, indent=2))
    return 3 if report["verdict"] == "LOCAL_QUARANTINE" else 0


if __name__ == "__main__":
    raise SystemExit(main())
