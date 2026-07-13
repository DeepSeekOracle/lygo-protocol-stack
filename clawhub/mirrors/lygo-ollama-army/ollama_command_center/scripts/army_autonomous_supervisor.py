#!/usr/bin/env python3
"""
Autonomous army supervisor: heartbeats (5m) + cron tick (1h).
Launches role set from army_config.json (slim or full capacity).
"""

from __future__ import annotations

import json
import os
import re
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


def existing_daemon_counts() -> dict[str, int]:
    counts: dict[str, int] = {}
    try:
        ps = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_Process -Filter \"name='python.exe'\" "
                "| Select-Object -Expand CommandLine",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        for line in (ps.stdout or "").splitlines():
            if "ollama_daemon.py" not in line:
                continue
            m = re.search(r"--role\s+(\S+)", line)
            if not m:
                continue
            role = m.group(1)
            counts[role] = counts.get(role, 0) + 1
    except Exception:
        pass
    return counts


def resolve_launch_plan(cfg: dict) -> tuple[list[str], dict[str, int], str, str | None]:
    cap = cfg.get("army_capacity") or {}
    perf = cfg.get("performance") or {}
    model = cap.get("model", "llama3.2:1b")
    champion = cap.get("champion_default")
    count = int(cap.get("count_per_role", 1))
    hb_n = int(cap.get("hb_light_instances", 1))
    boot_n = int(cap.get("champion_egg_boot_instances", 1))

    if perf.get("slim_boot", True):
        roles = list(perf.get("slim_roles") or ["hb-light", "stack-worker", "champion-egg-boot"])
        want: dict[str, int] = {}
        for role in roles:
            if role == "hb-light":
                want[role] = hb_n
            elif role == "champion-egg-boot":
                want[role] = boot_n
            else:
                want[role] = count
        return roles, want, model, champion

    roles = list(cap.get("roles") or ["hb-light", "lattice-check"])
    want = {}
    for role in roles:
        if role == "hb-light":
            want[role] = hb_n
        elif role == "champion-egg-boot":
            want[role] = boot_n
        else:
            want[role] = count
    return roles, want, model, champion


def launch_daemons_from_config(cfg: dict) -> list[subprocess.Popen]:
    perf = cfg.get("performance") or {}
    poll = str(perf.get("poll_idle_seconds", 6.0))
    roles, want, model, champion = resolve_launch_plan(cfg)
    existing = existing_daemon_counts()
    env = os.environ.copy()
    stack = cfg.get("lygo_stack_root")
    if stack:
        env["LYGO_STACK_ROOT"] = stack

    procs: list[subprocess.Popen] = []
    launched_roles: list[str] = []
    for role in roles:
        need = want.get(role, 1)
        have = existing.get(role, 0)
        to_launch = max(0, need - have)
        for _ in range(to_launch):
            cmd = [sys.executable, "-B", str(DAEMON), "--role", role, "--model", model, "--poll", poll]
            if champion and role in ("hb-light", "memory-triage", "draft-simple"):
                cmd += ["--champion", champion]
            procs.append(subprocess.Popen(cmd, cwd=str(ARMY), env=env))
            launched_roles.append(role)
            time.sleep(0.25)

    skipped = {r: existing.get(r, 0) for r in roles if existing.get(r, 0) >= want.get(r, 1)}
    print(f"Launched {len(procs)} daemons: {launched_roles}")
    if skipped:
        print(f"Skipped (already running): {skipped}")
    return procs


def main() -> int:
    cfg = load_config()
    if not os.environ.get("LYGO_STACK_ROOT", "").strip():
        stack = (cfg.get("lygo_stack_root") or "").strip()
        if stack:
            os.environ["LYGO_STACK_ROOT"] = stack
        else:
            print(
                "Set LYGO_STACK_ROOT or lygo_stack_root in army_config.json",
                file=sys.stderr,
            )
            return 2
    perf = cfg.get("performance") or {}
    mode = "slim" if perf.get("slim_boot", True) else "full"
    print("LYGO Army Autonomous Supervisor (v3.1)")
    print(f"  - boot mode: {mode}")
    print("  - sentinel every 5 min (+ network-builder probe)")
    print("  - cron (lattice/stack/pages/mesh/audit/memory/planting) every 60 min")
    print("  - daemons: dedupe existing processes before launch")

    daemon_procs = launch_daemons_from_config(cfg)

    last_cron = 0.0
    try:
        while True:
            subprocess.run([sys.executable, str(SENTINEL)], check=False, timeout=240)
            now = time.time()
            if now - last_cron >= INTERVAL_CRON:
                subprocess.run([sys.executable, str(HERE / "army_self_tune.py")], check=False, timeout=120)
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