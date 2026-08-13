#!/usr/bin/env python3
"""
Advanced idle guardian — safe housekeeping while you are offline/idle.

Requires LYGO_ARMY_IDLE_GUARDIAN=1. No social pulses, no planting unless
idle_guardian.allow_planting is true in army_config.json.
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



# Narrow passive/housekeeping roles only — never plant/social/self-tune via idle
_IDLE_ROLE_ALLOW = frozenset({
    "hb-light",
    "draft-simple",
    "idle-housekeep",
    "lattice-check",
    "memory-sync",
    "kernel-verify-only",
    "memory-triage",
})


def launch_idle_daemons(cfg: dict):
    """In-process army threads for idle_guardian.roles only (narrow allowlist)."""
    import ollama_daemon as od

    idle = cfg.get("idle_guardian") or {}
    forbidden = set(idle.get("forbidden_roles") or [])
    raw_roles = list(idle.get("roles") or ["idle-housekeep", "lattice-check", "kernel-verify-only"])
    # Prefer idle_guardian.roles; never fall back to army_capacity general roles
    roles = []
    for r in raw_roles:
        if r in forbidden:
            print(f"[SKIP] idle role forbidden: {r}")
            continue
        if r not in _IDLE_ROLE_ALLOW:
            print(f"[SKIP] idle role not on allowlist: {r}")
            continue
        # Social / plant never from idle even if mislisted
        if r in ("egg-planter", "registry-planter", "self-tune") or "molt" in r or "discord" in r:
            print(f"[SKIP] idle blocks privileged/social role: {r}")
            continue
        roles.append(r)
    if not roles:
        roles = ["idle-housekeep"]
    model = (cfg.get("army_capacity") or {}).get("model") or os.environ.get(
        "LYGO_OLLAMA_MODEL", "llama3.2:1b"
    )
    threads = []
    for role in roles:
        def worker(r=role, m=model):
            old = sys.argv[:]
            try:
                sys.argv = ["ollama_daemon.py", "--role", r, "--model", m, "--poll", "5.0"]
                if hasattr(od, "main"):
                    od.main()
                else:
                    od.run_daemon(r, m, 5.0, None)
            finally:
                sys.argv = old

        threads.append(run_daemon_thread(worker, name=f"army-{role}"))
        print(f"[LAUNCHED] army-{role} thread (idle allowlist)")
    return threads


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
            run_python(SENTINEL, timeout=240)
            now = time.time()
            if now - last_cron >= cron_iv:
                run_python(IDLE_CRON, timeout=1200)
                last_cron = now
            time.sleep(sentinel_iv)
    except KeyboardInterrupt:
        print("Stopping idle guardian...")
        for p in daemon_procs:
            p.terminate()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())