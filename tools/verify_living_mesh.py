#!/usr/bin/env python3
"""
Full living mesh verify: A+B local, C public (optional), D badge + peer compare + sim artifact.
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
    ap.add_argument("--skip-public", action="store_true")
    ap.add_argument("--run-sim", action="store_true")
    ap.add_argument("--peer", action="append", default=[])
    args = ap.parse_args()

    report = {
        "signature": "Delta9Phi963-LIVING-MESH-VERIFY-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "layers": {},
        "verdict": "LIVING_ALIGNED",
    }

    # A+B
    ab = subprocess.run(
        [sys.executable, str(TOOLS / "verify_all_kernel_layers.py"), "--json"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    try:
        report["layers"]["AB"] = json.loads(ab.stdout or "{}")
    except json.JSONDecodeError:
        report["layers"]["AB"] = {"verdict": "ERROR", "raw": ab.stdout}
    if report["layers"]["AB"].get("verdict") == "QUARANTINE" or ab.returncode == 3:
        report["verdict"] = "LOCAL_QUARANTINE"

    # C
    if not args.skip_public:
        c_script = (
            ROOT
            / "docs"
            / "skills"
            / "lygo-external-lattice-anchor"
            / "scripts"
            / "verify_public_anchors.py"
        )
        if c_script.is_file():
            c = subprocess.run(
                [sys.executable, str(c_script), "--json", "--stack-root", str(ROOT)],
                capture_output=True,
                text=True,
            )
            try:
                report["layers"]["C"] = json.loads(c.stdout or "{}")
            except json.JSONDecodeError:
                report["layers"]["C"] = {"verdict": "ERROR"}

    # D sentinel
    sent_cmd = [sys.executable, str(TOOLS / "living_mesh_sentinel.py")]
    for p in args.peer or []:
        sent_cmd.extend(["--peer", p])
    if args.run_sim:
        sent_cmd.append("--run-sim")
    s = subprocess.run(sent_cmd, cwd=str(ROOT), capture_output=True, text=True)
    try:
        report["layers"]["D"] = json.loads(s.stdout or "{}")
    except json.JSONDecodeError:
        report["layers"]["D"] = {"verdict": "ERROR", "raw": s.stdout}

    if report["verdict"] != "LOCAL_QUARANTINE":
        dver = (report["layers"].get("D") or {}).get("verdict")
        if dver == "SENTINEL_QUARANTINE":
            report["verdict"] = "LOCAL_QUARANTINE"
        elif dver == "SENTINEL_FORK_VISIBLE":
            report["verdict"] = "LIVING_ALIGNED_FORK_VISIBLE"
        elif (report["layers"].get("C") or {}).get("verdict") == "PUBLIC_DEGRADED":
            report["verdict"] = "LIVING_ALIGNED_PUBLIC_WARN"

    out = ROOT / "tests" / "living_mesh_last_run.json"
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass

    print(json.dumps(report, indent=2) if args.json else f"verdict={report['verdict']}")
    if args.json:
        pass
    else:
        print(json.dumps(report, indent=2))
    return 3 if report["verdict"] == "LOCAL_QUARANTINE" else 0


if __name__ == "__main__":
    raise SystemExit(main())
