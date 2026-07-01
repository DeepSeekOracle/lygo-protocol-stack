#!/usr/bin/env python3
"""Lattice Gauntlet — Phase 3 acceptance checklist (BLUEPRINT.md)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIGNATURE = "Δ9Φ963-PHASE3-SCALE-INIT"
LYRA = Path(r"I:\E Drive\LYRA_CORE")


def _run(cmd: list[str], cwd: Path, timeout: int = 600) -> tuple[int, str]:
    cp = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    return cp.returncode, (cp.stdout or "") + (cp.stderr or "")


def check_lattice() -> tuple[bool, str]:
    rc, out = _run([sys.executable, "tools/verify_lattice_alignment.py"], ROOT)
    ok = rc == 0 and "ALIGNED" in out
    return ok, "LATTICE ALIGNED" if ok else out[-400:]


def check_badge() -> tuple[bool, str]:
    rc, out = _run([sys.executable, "tools/verify_alignment_badge.py", "--format=json"], ROOT, timeout=900)
    ok = rc == 0 and ("BADGE VALID" in out or '"status": "ALIGNED"' in out)
    return ok, "BADGE VALID (ALIGNED)" if ok else out[-400:]


def check_grok() -> tuple[bool, str]:
    rc, out = _run([sys.executable, "tools/run_grok_audit_demo.py"], ROOT, timeout=900)
    ok = rc == 0 and "Failed: 0" in out
    return ok, "60/60 GROK AUDIT" if ok else out[-400:]


def check_hf() -> tuple[bool, str]:
    try:
        req = urllib.request.Request(
            "https://huggingface.co/api/spaces/DeepSeekOracle/LYGO-Resonance-Engine",
            headers={"User-Agent": "LYGO-Gauntlet/1.0"},
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode())
        stage = (data.get("runtime") or {}).get("stage", "?")
        ok = stage == "RUNNING"
        return ok, f"HF {stage}"
    except Exception as exc:
        return False, str(exc)[:200]


def check_discord() -> tuple[bool, str]:
    if not LYRA.is_dir():
        return False, "LYRA_CORE missing"
    sys.path.insert(0, str(LYRA))
    try:
        from lygo_ops_status import collect_ops_status  # noqa: E402

        d = (collect_ops_status().get("discord") or {})
        ok = bool(
            d.get("online")
            or d.get("process_running")
            or (d.get("api_me") or {}).get("ok")
        )
        detail = f"online={d.get('online')} process={d.get('process_running')} api_me={(d.get('api_me') or {}).get('ok')}"
        return ok, detail
    except Exception as exc:
        return False, str(exc)[:200]


def check_twin() -> tuple[bool, str]:
    rc, out = _run([sys.executable, "tools/run_twin_gate_vector_suite.py"], ROOT, timeout=600)
    ok = rc == 0 and "100.0%" in out
    return ok, "TWIN GATE 100% verdict match" if ok else out[-500:]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="Fail if Discord offline")
    args = ap.parse_args()

    checks = [
        ("lattice", check_lattice),
        ("badge", check_badge),
        ("grok_60", check_grok),
        ("hf_running", check_hf),
        ("discord_ops", check_discord),
        ("twin_gate", check_twin),
    ]
    print("=" * 60)
    print(" LYGO LATTICE GAUNTLET")
    print(f" {SIGNATURE}")
    print("=" * 60)
    all_ok = True
    for name, fn in checks:
        if name == "discord_ops" and not args.strict:
            ok, detail = fn()
            mark = "OK" if ok else "WARN"
            print(f"  [{mark}] {name}: {detail}")
            continue
        ok, detail = fn()
        mark = "OK" if ok else "FAIL"
        print(f"  [{mark}] {name}: {detail}")
        all_ok &= ok

    print("=" * 60)
    print("GAUNTLET", "PASS" if all_ok else "NEEDS WORK")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())