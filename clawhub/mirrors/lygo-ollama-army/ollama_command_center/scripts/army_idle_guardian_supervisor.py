#!/usr/bin/env python3
"""
Advanced idle guardian — safe housekeeping while you are offline/idle.

Requires LYGO_ARMY_IDLE_GUARDIAN=1. No social pulses, no planting unless
idle_guardian.allow_planting is true in army_config.json.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CC = HERE.parent
ARMY = CC.parent
CONFIG = CC / "config" / "army_config.json"
SENTINEL = HERE / "sentinel_heartbeat.py"
IDLE_CRON = HERE / "army_idle_cron_once.py"
DAEMON = ARMY / "ollama_daemon.py"


def load_config() -> dict:
    if CONFIG.is_file():
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    return {}


def idle_cfg(cfg: dict) -> dict:
    return cfg.get("idle_guardian") or {}


def launch_idle_daemons(cfg: dict) -> list[subprocess.Popen]:
    idle = idle_cfg(cfg)
    cap = cfg.get("army_capacity") or {}
    model = cap.get("model", "llama3.2:1b")
    count = max(1, int(idle.get("count_per_role", 1)))
    roles: list[str] = list(
        idle.get("roles")
        or ["idle-housekeep", "lattice-check", "memory-sync", "kernel-verify-only"]
    )
    forbidden = set(idle.get("forbidden_roles") or [])
    roles = [r for r in roles if r not in forbidden]

    env = os.environ.copy()
    stack = (cfg.get("lygo_stack_root") or env.get("LYGO_STACK_ROOT", "")).strip()
    if stack:
        env["LYGO_STACK_ROOT"] = stack

    procs: list[subprocess.Popen] = []
    for role in roles:
        for _ in range(count):
            cmd = [sys.executable, "-B", str(DAEMON), "--role", role, "--model", model, "--poll", "8.0"]
            procs.append(subprocess.Popen(cmd, cwd=str(ARMY), env=env))
            time.sleep(0.3)
    print(f"Idle daemons: {roles} x{count}")
    return procs


def main() -> int:
    if os.environ.get("LYGO_ARMY_IDLE_GUARDIAN", "").strip().lower() not in ("1", "true", "yes"):
        print(
            "Set LYGO_ARMY_IDLE_GUARDIAN=1 to start idle guardian (see IDLE_GUARDIAN.md)",
            file=sys.stderr,
        )
        return 2

    cfg = load_config()
    idle = idle_cfg(cfg)
    stack = (cfg.get("lygo_stack_root") or os.environ.get("LYGO_STACK_ROOT", "")).strip()
    if not stack:
        print("Set lygo_stack_root in army_config.json or LYGO_STACK_ROOT", file=sys.stderr)
        return 2
    os.environ["LYGO_STACK_ROOT"] = stack

    sentinel_iv = int(idle.get("sentinel_interval_seconds", 300))
    cron_iv = int(idle.get("cron_interval_seconds", 1800))

    print("LYGO Army Idle Guardian")
    print(f"  stack: {stack}")
    print(f"  sentinel every {sentinel_iv}s | housekeeping cron every {cron_iv}s")
    print(f"  journal: {CC / 'workspace' / 'idle_guardian_journal.jsonl'}")
    print(f"  upgrades: {CC / 'workspace' / 'idle_upgrade_findings.jsonl'}")
    print("  Close window or Ctrl+C to stop.")

    daemon_procs = launch_idle_daemons(cfg)
    last_cron = 0.0
    try:
        while True:
            subprocess.run([sys.executable, str(SENTINEL)], check=False, timeout=240)
            now = time.time()
            if now - last_cron >= cron_iv:
                subprocess.run([sys.executable, str(IDLE_CRON)], check=False, timeout=1200)
                last_cron = now
            time.sleep(sentinel_iv)
    except KeyboardInterrupt:
        print("Stopping idle guardian...")
        for p in daemon_procs:
            p.terminate()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())