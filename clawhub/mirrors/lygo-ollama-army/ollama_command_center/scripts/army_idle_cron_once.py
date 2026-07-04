#!/usr/bin/env python3
"""Idle cron: sentinel + safe task seeds only (no social, no planting by default)."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CC = Path(__file__).resolve().parents[1]
TASKS = CC / "tasks"
CONFIG = CC / "config" / "army_config.json"


def _idle_cfg() -> dict:
    if CONFIG.is_file():
        return (json.loads(CONFIG.read_text(encoding="utf-8")).get("idle_guardian") or {})
    return {}


def main() -> int:
    subprocess.run([sys.executable, str(CC / "scripts" / "sentinel_heartbeat.py")], check=False, timeout=240)

    idle = _idle_cfg()
    forbidden = set(idle.get("forbidden_roles") or [])
    allow_plant = bool(idle.get("allow_planting", False))

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    seeds = [
        ("lattice-check", f"idle-lattice-{ts}"),
        ("memory-sync", f"idle-memory-{ts}"),
        ("kernel-verify-only", f"idle-kernel-verify-{ts}"),
        ("idle-housekeep", f"idle-housekeep-{ts}"),
        ("clawhub-catalog-audit", f"idle-clawhub-{ts}"),
        ("public-pages-check", f"idle-pages-{ts}"),
    ]
    if allow_plant:
        seeds.extend(
            [
                ("egg-planter", f"idle-egg-plant-{ts}"),
                ("registry-planter", f"idle-registry-plant-{ts}"),
            ]
        )

    TASKS.mkdir(parents=True, exist_ok=True)
    for role, tid in seeds:
        if role in forbidden:
            continue
        path = TASKS / f"{tid}.task.json"
        if path.exists():
            continue
        payload: dict = {}
        if role == "idle-housekeep":
            payload = {"ops": idle.get("housekeep_ops") or ["memory_sync", "three_brain_index", "upgrade_scout"]}
        path.write_text(json.dumps({"id": tid, "role": role, "payload": payload}), encoding="utf-8")

    subprocess.run(
        [sys.executable, str(CC / "scripts" / "army_idle_housekeeping.py"), "--tick"],
        check=False,
        timeout=900,
    )
    print(f"Idle cron OK — tasks in {TASKS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())