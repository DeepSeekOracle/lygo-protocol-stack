#!/usr/bin/env python3
"""
Autonomous army supervisor: heartbeats (5m) + cron tick (1h).
Launches role set from army_config.json (slim or full capacity).
"""

from __future__ import annotations

import sys
from pathlib import Path as _P
_SKILL = _P(__file__).resolve().parents[2]
if str(_SKILL) not in sys.path:
    sys.path.insert(0, str(_SKILL))
from _safe_invoke import run_python, run_daemon_thread, git_status_summary, write_local_alert  # noqa: E402

import json
import os
import re
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
        ps = type('R', (), {'returncode': 0, 'stdout': '', 'stderr': ''})()
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



def launch_daemons_from_config(cfg: dict):
    """In-process army threads (v0.6.0 — no Popen)."""
    import ollama_daemon as od
    roles = (cfg.get("roles") or cfg.get("daemon_roles") or ["hb-light", "draft-simple"])
    model = cfg.get("model") or os.environ.get("LYGO_OLLAMA_MODEL", "llama3.2:1b")
    threads = []
    for role in roles:
        def worker(r=role, m=model):
            old = sys.argv[:]
            try:
                sys.argv = ["ollama_daemon.py", "--role", r, "--model", m, "--poll", "5.0"]
                if hasattr(od, "main"):
                    od.main()
            finally:
                sys.argv = old
        threads.append(run_daemon_thread(worker, name=f"army-{role}"))
        print(f"[LAUNCHED] army-{role} thread")
    return threads


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
            run_python(SENTINEL, timeout=240)
            now = time.time()
            if now - last_cron >= INTERVAL_CRON:
                run_python(HERE / "army_self_tune.py", timeout=120)
                run_python(CRON, timeout=600)
                last_cron = now
            time.sleep(INTERVAL_SENTINEL)
    except KeyboardInterrupt:
        print("Stopping supervisor...")
        for p in daemon_procs:
            p.terminate()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())