#!/usr/bin/env python3
"""Autonomous anchor worker — drains queue, optional BLE scan, SLM periodic anchor."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(ROOT / "stack"))
sys.path.insert(0, str(TOOLS))

from lygo_stack_anchor import get_orchestrator  # noqa: E402


def pulse(stack_anchor_slm: bool = False) -> dict:
    orch = get_orchestrator()
    drained = orch.drain_queue()
    slm_report = None
    if stack_anchor_slm:
        try:
            from lygo_stack import deploy_stack

            slm_report = deploy_stack(os.environ.get("LYGO_NODE_ID", "ANCHOR_WORKER")).anchor_slm_state()
        except Exception as exc:
            slm_report = {"success": False, "error": str(exc)}
    ble = None
    if os.environ.get("LYGO_ANCHOR_BLE", "1").lower() not in ("0", "false"):
        try:
            from ble_mesh_bouncer import LygoBleMeshBouncer
            import asyncio

            b = LygoBleMeshBouncer()
            ble = asyncio.run(b.run_discovery_and_bounce_loop(3))
        except Exception as exc:
            ble = {"ok": False, "error": str(exc)}
    return {"drained": len(drained), "jobs": drained, "slm": slm_report, "ble_scan": ble}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--interval", type=int, default=300)
    ap.add_argument("--slm-each-pulse", action="store_true")
    args = ap.parse_args()
    if not args.loop:
        print(json.dumps(pulse(args.slm_each_pulse), indent=2))
        return 0
    while True:
        try:
            out = pulse(args.slm_each_pulse)
            print(json.dumps({"ts": time.time(), **out}))
        except KeyboardInterrupt:
            break
        except Exception as exc:
            print(json.dumps({"error": str(exc)}))
        time.sleep(args.interval)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())