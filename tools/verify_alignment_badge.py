#!/usr/bin/env python3
"""Emit JSON/Markdown alignment badge for community nodes (Phase 2)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIGNATURE = "Δ9Φ963-PHASE2-DEPLOYMENT"


def _run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    cp = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=300)
    out = (cp.stdout or "") + (cp.stderr or "")
    return cp.returncode, out.strip()


def collect_badge(*, quick: bool = False) -> dict:
    badge: dict = {
        "signature": SIGNATURE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "repo": str(ROOT),
        "checks": {},
        "status": "UNKNOWN",
    }

    golden = ROOT / "protocol0_nano_kernel" / "fixtures" / "p0_canonical.sha256"
    badge["checks"]["p0_golden_sha"] = golden.is_file()

    stack = None
    sys.path.insert(0, str(ROOT / "stack"))
    for sub in (
        "protocol0_nano_kernel/src/python",
        "protocol1_memory_mycelium/src/python",
        "protocol2_cognitive_bridge/src/python",
        "protocol3_vortex_consensus/src/python",
        "protocol4_ascension_engine/src/python",
        "protocol5_harmony_node/src/python",
    ):
        p = ROOT / sub
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))

    try:
        from lygo_stack import deploy_stack  # noqa: E402

        stack = deploy_stack("BADGE_PROBE")
        demo = stack.demo_cycle()
        badge["checks"]["stack_demo"] = demo.get("p0", {}).get("verdict") == "AMPLIFY"
        badge["stack_version"] = stack.version
    except Exception as exc:
        badge["checks"]["stack_demo"] = False
        badge["stack_error"] = str(exc)

    try:
        if stack is not None:
            coord = stack.elasticity
            fed = stack.federation
            coord.scatter_prioritized({"probe": True}, "BADGE_PROBE", verdict_hint="AMPLIFY")
            fed.announce_alignment({"status": "PROBING", "signature": SIGNATURE})
            badge["checks"]["phase1_elasticity"] = coord.status()["version"].startswith("Δ9")
            badge["checks"]["phase3_4_federation"] = fed.version.startswith("Δ9")
        else:
            badge["checks"]["phase1_elasticity"] = False
            badge["checks"]["phase3_4_federation"] = False
    except Exception as exc:
        badge["checks"]["phase1_elasticity"] = False
        badge["checks"]["phase3_4_federation"] = False
        badge["elasticity_error"] = str(exc)

    if not quick:
        rc, _ = _run([sys.executable, "tools/run_grok_audit_demo.py", "--no-report"], ROOT)
        badge["checks"]["grok_audit_cli"] = rc == 0
        rc2, out2 = _run([sys.executable, "tools/verify_lattice_alignment.py"], ROOT)
        badge["checks"]["lattice"] = rc2 == 0 and "ALIGNED" in out2
    else:
        badge["checks"]["grok_audit_cli"] = None
        badge["checks"]["lattice"] = None

    required = [k for k, v in badge["checks"].items() if v is not None]
    badge["status"] = "ALIGNED" if all(badge["checks"][k] for k in required) else "NEEDS_FIX"
    return badge


def to_markdown(badge: dict) -> str:
    status = badge.get("status", "UNKNOWN")
    icon = "✅" if status == "ALIGNED" else "⚠️"
    lines = [
        f"### {icon} LYGO Alignment Badge",
        "",
        f"**Status:** `{status}` · **Signature:** `{badge.get('signature')}`",
        f"**Stack:** `{badge.get('stack_version', 'n/a')}` · **UTC:** `{badge.get('timestamp')}`",
        "",
        "| Check | OK |",
        "|-------|-----|",
    ]
    for k, v in sorted((badge.get("checks") or {}).items()):
        if v is None:
            lines.append(f"| {k} | skipped |")
        else:
            lines.append(f"| {k} | {'✅' if v else '❌'} |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="LYGO node alignment badge")
    ap.add_argument("--quick", action="store_true", help="Skip full audit + lattice (faster Docker health)")
    ap.add_argument("--format", choices=("json", "md", "both"), default="both")
    ap.add_argument("--out", type=Path, default=ROOT / "tests" / "alignment_badge.json")
    args = ap.parse_args()

    badge = collect_badge(quick=args.quick)
    if args.format in ("json", "both"):
        args.out.write_text(json.dumps(badge, indent=2), encoding="utf-8")
        print(json.dumps(badge, indent=2))
    if args.format in ("md", "both"):
        print("\n" + to_markdown(badge))

    if badge["status"] == "ALIGNED":
        print("BADGE VALID")
    return 0 if badge["status"] == "ALIGNED" else 1


if __name__ == "__main__":
    raise SystemExit(main())