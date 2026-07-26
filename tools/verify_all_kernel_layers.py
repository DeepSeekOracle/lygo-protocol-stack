#!/usr/bin/env python3
"""
Unified kernel layer verify: classic stack eggs + sovereign seeds.

Exit codes:
  0 = all present layers ALIGNED (or EMPTY where allowed)
  1 = tooling error
  3 = QUARANTINE / mismatch on any layer

Signature: Delta9Phi963-KERNEL-LAYERS-VERIFY-v1
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]


def run_classic() -> dict:
    tool = STACK / "tools" / "verify_kernel_eggs.py"
    out_path = STACK / "tests" / "kernel_eggs_last_run.json"
    if not tool.is_file():
        return {
            "layer": "classic_kernel_eggs",
            "status": "SKIP",
            "reason": "tools/verify_kernel_eggs.py not present (sparse checkout or missing tools)",
        }
    rc = subprocess.call([sys.executable, str(tool)], cwd=str(STACK))
    payload: dict = {"layer": "classic_kernel_eggs", "exit_code": rc}
    if out_path.is_file():
        try:
            data = json.loads(out_path.read_text(encoding="utf-8"))
            payload["verdict"] = data.get("verdict")
            payload["all_pass"] = data.get("all_pass")
            payload["artifact"] = str(out_path.relative_to(STACK)).replace("\\", "/")
        except Exception as e:
            payload["verdict"] = "ERROR"
            payload["error"] = str(e)
    else:
        payload["verdict"] = "PASS" if rc == 0 else "FAIL"
    if rc == 3 or str(payload.get("verdict", "")).upper() in ("QUARANTINE", "FAIL"):
        payload["status"] = "QUARANTINE"
    elif rc == 0:
        payload["status"] = "ALIGNED"
    else:
        payload["status"] = "FAIL"
    return payload


def run_sovereign() -> dict:
    seeder = (
        STACK
        / "docs"
        / "skills"
        / "lygo-sovereign-kernel-seeder"
        / "scripts"
        / "verify_seed.py"
    )
    root = STACK / "data" / "sovereign_seeds"
    if not seeder.is_file():
        return {
            "layer": "sovereign_seeds",
            "status": "SKIP",
            "reason": "seeder skill scripts missing under docs/skills/",
        }
    if not (root / "registry.json").is_file():
        return {
            "layer": "sovereign_seeds",
            "status": "EMPTY",
            "root": str(root),
            "verdict": "EMPTY",
        }
    proc = subprocess.run(
        [sys.executable, str(seeder), "--root", str(root), "--json"],
        capture_output=True,
        text=True,
        cwd=str(STACK),
    )
    payload: dict = {
        "layer": "sovereign_seeds",
        "exit_code": proc.returncode,
        "root": str(root),
    }
    try:
        data = json.loads(proc.stdout or "{}")
        payload.update(
            {
                "verdict": data.get("verdict"),
                "errors": data.get("errors"),
                "eggs_checked": data.get("eggs_checked"),
                "registry_merkle_root": data.get("registry_merkle_root"),
                "computed_merkle_root": data.get("computed_merkle_root"),
            }
        )
    except json.JSONDecodeError:
        payload["stdout"] = proc.stdout
        payload["stderr"] = proc.stderr
        payload["verdict"] = "ERROR"
    if proc.returncode == 3 or str(payload.get("verdict", "")).upper() == "QUARANTINE":
        payload["status"] = "QUARANTINE"
    elif proc.returncode == 0 and payload.get("verdict") in ("ALIGNED", "EMPTY"):
        payload["status"] = payload.get("verdict") or "ALIGNED"
    else:
        payload["status"] = "FAIL"
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify classic + sovereign kernel layers")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--require-classic", action="store_true", help="FAIL if classic tools missing")
    ap.add_argument("--require-sovereign", action="store_true", help="FAIL if no sovereign registry")
    args = ap.parse_args()

    layers = [run_classic(), run_sovereign()]
    report = {
        "signature": "Delta9Phi963-KERNEL-LAYERS-VERIFY-v1",
        "stack": str(STACK),
        "layers": layers,
        "verdict": "ALIGNED",
        "doc": "docs/KERNEL_EGG_SYSTEM_UNIFIED.md",
    }

    hard_fail = False
    for layer in layers:
        st = layer.get("status")
        if st == "QUARANTINE" or st == "FAIL":
            hard_fail = True
        if args.require_classic and layer.get("layer") == "classic_kernel_eggs" and st == "SKIP":
            hard_fail = True
            layer["required_missing"] = True
        if args.require_sovereign and layer.get("layer") == "sovereign_seeds" and st in ("SKIP", "EMPTY"):
            hard_fail = True
            layer["required_missing"] = True

    if hard_fail:
        report["verdict"] = "QUARANTINE"

    # dual roots summary
    report["summary"] = {
        "classic": next((x.get("status") for x in layers if x["layer"] == "classic_kernel_eggs"), None),
        "sovereign": next((x.get("status") for x in layers if x["layer"] == "sovereign_seeds"), None),
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"verdict={report['verdict']}")
        for layer in layers:
            print(
                f"  {layer.get('layer')}: status={layer.get('status')} "
                f"verdict={layer.get('verdict')} exit={layer.get('exit_code', '-')}"
            )

    out = STACK / "tests" / "kernel_layers_last_run.json"
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass

    return 3 if hard_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
