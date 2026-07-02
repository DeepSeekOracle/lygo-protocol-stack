#!/usr/bin/env python3
"""
Autonomous army supervisor: heartbeats (5m) + cron tick (1h).
Launches full role set from army_config.json (v2 public-pages + audit suite).
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
CONFIG_PATH = CC / "config" / "army_config.json"
SENTINEL = HERE / "sentinel_heartbeat.py"
CRON = HERE / "army_cron_once.py"
DAEMON = ARMY / "ollama_daemon.py"
INTERVAL_SENTINEL = 300
INTERVAL_CRON = 3600


def load_config() -> dict:
    if CONFIG_PATH.is_file():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def launch_daemons_from_config(cfg: dict) -> list[subprocess.Popen]:
    cap = cfg.get("army_capacity") or {}
    model = cap.get("model", "llama3.2:1b")
    champion = cap.get("champion_default")
    count = int(cap.get("count_per_role", 1))
    roles: list[str] = list(cap.get("roles") or ["hb-light", "lattice-check"])
    hb_n = int(cap.get("hb_light_instances", 1))
    procs: list[subprocess.Popen] = []
    env = os.environ.copy()
    stack = cfg.get("lygo_stack_root")
    if stack:
        env["LYGO_STACK_ROOT"] = stack

    launched_roles: list[str] = []
    for role in roles:
        n = hb_n if role == "hb-light" else count
        for _ in range(max(1, n)):
            cmd = [sys.executable, "-B", str(DAEMON), "--role", role, "--model", model, "--poll", "6.0"]
            if champion and role in ("hb-light", "memory-triage", "draft-simple"):
                cmd += ["--champion", champion]
            procs.append(subprocess.Popen(cmd, cwd=str(ARMY), env=env))
            launched_roles.append(role)
            time.sleep(0.35)

    print(f"Launched {len(procs)} daemons: {launched_roles}")
    return procs


def main() -> int:
    cfg = load_config()
    os.environ.setdefault("LYGO_STACK_ROOT", cfg.get("lygo_stack_root", r"I:\E Drive\lygo-protocol-stack"))
    print("LYGO Army Autonomous Supervisor (v3)")
    print("  - sentinel every 5 min (+ network-builder probe)")
    print("  - cron (lattice/stack/pages/mesh/audit/memory/planting) every 60 min")
    print("  - daemons from army_config.army_capacity")

    daemon_procs = launch_daemons_from_config(cfg)

    last_cron = 0.0
    try:
        while True:
            subprocess.run([sys.executable, str(SENTINEL)], check=False, timeout=240)
            now = time.time()
            if now - last_cron >= INTERVAL_CRON:
                subprocess.run([sys.executable, str(CRON)], check=False, timeout=600)
                last_cron = now
            time.sleep(INTERVAL_SENTINEL)
    except KeyboardInterrupt:
        print("Stopping supervisor...")
        for p in daemon_procs:
            p.terminate()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())