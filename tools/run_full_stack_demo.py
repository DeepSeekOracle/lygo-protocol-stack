#!/usr/bin/env python3
"""CLI entrypoint — full LYGO Protocol Stack demonstration."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "stack"))

from lygo_stack import deploy_stack  # noqa: E402


def main() -> int:
    print("⚡ LYGO Protocol Stack — Full Demonstration (P0–P5)")
    print("=" * 72)
    stack = deploy_stack()
    report = stack.demo_cycle()
    print(json.dumps(report, indent=2, default=str))
    ok = (
        report.get("p5", {}).get("success") is True
        and report.get("p3", {}).get("consensus_found") is True
    )
    print("\n✅ Demo complete — all protocols exercised." if ok else "\n⚠️ Demo finished with warnings.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())