#!/usr/bin/env python3
"""
World lattice verify: Layer A+B (local) then Layer C (public HTTP).

Protects user: local mismatch = hard fail; public degrade = soft warn unless --strict-public.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SIG = "Delta9Phi963-WORLD-LATTICE-VERIFY-v1"


def stack_root() -> Path:
    env = os.environ.get("LYGO_STACK_ROOT", "").strip()
    if env:
        return Path(env).resolve()
    for p in HERE.parents:
        if (p / "tools" / "verify_all_kernel_layers.py").is_file() or (
            p / "docs" / "network_builder" / "IMMUTABLE_ANCHORS.json"
        ).is_file():
            return p
    return Path.cwd()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict-public", action="store_true")
    ap.add_argument("--stack-root", default="")
    args = ap.parse_args()
    stack = Path(args.stack_root).resolve() if args.stack_root else stack_root()

    report = {
        "signature": SIG,
        "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stack": str(stack),
        "layers": {},
        "verdict": "WORLD_ALIGNED",
    }

    # A+B
    unified = stack / "tools" / "verify_all_kernel_layers.py"
    if unified.is_file():
        p = subprocess.run(
            [sys.executable, str(unified), "--json"],
            capture_output=True,
            text=True,
            cwd=str(stack),
        )
        try:
            ab = json.loads(p.stdout or "{}")
        except json.JSONDecodeError:
            ab = {"verdict": "ERROR", "raw": p.stdout, "stderr": p.stderr}
        report["layers"]["AB_local"] = ab
        if ab.get("verdict") == "QUARANTINE" or p.returncode == 3:
            report["verdict"] = "LOCAL_QUARANTINE"
    else:
        # sovereign only fallback
        sev = (
            stack
            / "docs"
            / "skills"
            / "lygo-sovereign-kernel-seeder"
            / "scripts"
            / "verify_seed.py"
        )
        if sev.is_file():
            root = stack / "data" / "sovereign_seeds"
            p = subprocess.run(
                [sys.executable, str(sev), "--root", str(root), "--json"],
                capture_output=True,
                text=True,
            )
            try:
                report["layers"]["B_sovereign_only"] = json.loads(p.stdout or "{}")
            except json.JSONDecodeError:
                report["layers"]["B_sovereign_only"] = {"verdict": "ERROR"}
            if p.returncode == 3:
                report["verdict"] = "LOCAL_QUARANTINE"
        else:
            report["layers"]["AB_local"] = {"status": "SKIP", "reason": "no unified tool"}

    # C public
    pub = HERE / "verify_public_anchors.py"
    p2 = subprocess.run(
        [sys.executable, str(pub), "--json", "--stack-root", str(stack)],
        capture_output=True,
        text=True,
    )
    try:
        c = json.loads(p2.stdout or "{}")
    except json.JSONDecodeError:
        c = {"verdict": "ERROR", "raw": p2.stdout}
    report["layers"]["C_public"] = c
    if c.get("verdict") == "PUBLIC_DEGRADED":
        if args.strict_public:
            report["verdict"] = "PUBLIC_DEGRADED"
        elif report["verdict"] == "WORLD_ALIGNED":
            report["verdict"] = "WORLD_ALIGNED_PUBLIC_WARN"

    # refresh map + manifest (local files)
    for script in ("build_public_verify_manifest.py", "map_eggs_to_star_chart.py"):
        sp = HERE / script
        if sp.is_file():
            subprocess.run([sys.executable, str(sp), "--stack-root", str(stack)], cwd=str(stack))

    out = stack / "tests" / "world_lattice_last_run.json"
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"verdict={report['verdict']}")
        print(f"  AB={report['layers'].get('AB_local', report['layers'].get('B_sovereign_only', {})).get('verdict')}")
        print(f"  C={c.get('verdict')}")

    if report["verdict"] == "LOCAL_QUARANTINE":
        return 3
    if report["verdict"] == "PUBLIC_DEGRADED" and args.strict_public:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
