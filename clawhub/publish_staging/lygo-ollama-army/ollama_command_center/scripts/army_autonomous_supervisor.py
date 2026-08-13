#!/usr/bin/env python3
"""
Autonomous army supervisor: in-process daemon threads + sentinel + hourly cron.

REQUIRES env LYGO_ARMY_AUTONOMOUS=1 (and usually LYGO_STACK_ROOT).
Long-running; no interactive confirmation after env gate — set deliberately.

Uses in-process threads + runpy only (no OS process spawn from this Python file).
Operator PowerShell full-capacity launcher is a separate surface that does spawn Python.
"""

from __future__ import annotations

import sys
from pathlib import Path as _P
_SKILL = _P(__file__).resolve().parents[2]
if str(_SKILL) not in sys.path:
    sys.path.insert(0, str(_SKILL))
from _safe_invoke import run_python, run_daemon_thread  # noqa: E402

import json
import os
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CC = HERE.parent
ARMY = CC.parent
CONFIG_PATH = CC / "config" / "army_config.json"
SENTINEL = HERE / "sentinel_heartbeat.py"
CRON = HERE / "army_cron_once.py"
INTERVAL_SENTINEL = 300
INTERVAL_CRON = 3600


def load_config() -> dict:
    if CONFIG_PATH.is_file():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def resolve_launch_plan(cfg: dict) -> tuple[list[str], dict[str, int], str]:
    cap = cfg.get("army_capacity") or {}
    perf = cfg.get("performance") or {}
    model = cap.get("model", "llama3.2:1b")
    count = int(cap.get("count_per_role", 1))
    hb_n = int(cap.get("hb_light_instances", 1))
    boot_n = int(cap.get("champion_egg_boot_instances", 0))

    # Privileged roles need explicit allow
    allow_priv = bool((cfg.get("access") or {}).get("allow_privileged_roles", False))
    privileged = {
        "egg-planter",
        "registry-planter",
        "champion-egg-boot",
        "moltx-lattice-pulse",
        "moltbook-lyra-pulse",
        "moltbook-lightfather-pulse",
    }

    if perf.get("slim_boot", True):
        roles = list(perf.get("slim_roles") or ["hb-light", "draft-simple"])
    else:
        roles = list(cap.get("roles") or ["hb-light", "lattice-check"])

    if not allow_priv:
        roles = [r for r in roles if r not in privileged]

    want: dict[str, int] = {}
    for role in roles:
        if role == "hb-light":
            want[role] = max(1, hb_n)
        elif role == "champion-egg-boot":
            want[role] = boot_n if allow_priv else 0
        else:
            want[role] = count
    # drop zero-count roles
    roles = [r for r in roles if want.get(r, 0) > 0]
    return roles, want, model


def launch_daemons_from_config(cfg: dict):
    """In-process army threads (no Popen / no subprocess)."""
    import ollama_daemon as od

    roles, want, model = resolve_launch_plan(cfg)
    threads = []
    for role in roles:
        for i in range(int(want.get(role, 1))):
            def worker(r=role, m=model, n=i):
                old = sys.argv[:]
                try:
                    sys.argv = ["ollama_daemon.py", "--role", r, "--model", m, "--poll", "5.0"]
                    if hasattr(od, "main"):
                        od.main()
                finally:
                    sys.argv = old

            t = run_daemon_thread(worker, name=f"army-{role}-{i}")
            threads.append(t)
            print(f"[LAUNCHED] in-process thread army-{role}-{i}")
    return threads


def main() -> int:
    auto = os.environ.get("LYGO_ARMY_AUTONOMOUS", "").strip().lower() in ("1", "true", "yes")
    consent = os.environ.get("LYGO_ARMY_I_CONSENT", "").strip().lower() in ("1", "true", "yes")
    if not auto or not consent:
        print(
            "Refusing autonomous supervisor (SkillSpector dual gate).\n"
            "  Set LYGO_ARMY_AUTONOMOUS=1\n"
            "  Set LYGO_ARMY_I_CONSENT=1  (operator accepts long-running daemons + cron)\n"
            "Read references/SECURITY.md first.\n"
            "Safer entry: python ollama_army_launcher.py --roles hb-light,draft-simple",
            file=sys.stderr,
        )
        return 2

    cfg = load_config()
    if not os.environ.get("LYGO_STACK_ROOT", "").strip():
        stack = (cfg.get("lygo_stack_root") or "").strip()
        if stack:
            os.environ["LYGO_STACK_ROOT"] = stack

    planting = cfg.get("planting") or {}
    self_tune = cfg.get("self_tune") or {}
    social = cfg.get("social_publish") or {}
    perf = cfg.get("performance") or {}
    sent = cfg.get("sentinel") or {}
    mode = "slim" if perf.get("slim_boot", True) else "full"
    plant_on = bool(planting.get("enabled") and planting.get("consent"))
    tune_on = bool(self_tune.get("enabled", False))
    social_on = bool(social.get("enabled") and social.get("allow_social_pulse"))
    probes_on = bool(sent.get("probe_public_pages") or sent.get("probe_network_builder"))

    print("LYGO Army Autonomous Supervisor v0.8.1")
    print("  WARNING: long-running autonomous loop — dual env gate accepted")
    print("  CAUTION: no further interactive confirmation after env gates")
    print(f"  - boot mode: {mode}")
    print("  - sentinel every 5 min")
    print(f"  - public HTTPS GET probes: {'ON' if probes_on else 'OFF (default)'}")
    print(
        "  - hourly cron seeds SAFE roles only "
        "(lattice/stack/pages/mesh/audit/memory names are task *roles*, not auto-plant)"
    )
    print(
        f"  - consent gates now: planting={'ON' if plant_on else 'OFF'}; "
        f"self_tune={'ON' if tune_on else 'OFF'}; "
        f"social_pulse={'ON' if social_on else 'OFF'}"
    )
    print("  - daemons: in-process threads only (no OS spawn from this Python file)")
    print("  - Operator PS1 full-capacity is a SEPARATE surface that spawns python.exe")

    daemon_threads = launch_daemons_from_config(cfg)

    last_cron = 0.0
    try:
        while True:
            run_python(SENTINEL, timeout=240)
            now = time.time()
            if now - last_cron >= INTERVAL_CRON:
                if self_tune.get("enabled", False):
                    run_python(HERE / "army_self_tune.py", timeout=120)
                run_python(CRON, timeout=600)
                last_cron = now
            time.sleep(INTERVAL_SENTINEL)
    except KeyboardInterrupt:
        print("Stopping supervisor (threads are daemon; process exit ends them)...")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
