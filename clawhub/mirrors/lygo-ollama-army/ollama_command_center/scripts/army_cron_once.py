#!/usr/bin/env python3
"""Single cron tick: sentinel pulse + seed deterministic army tasks (no LLM)."""

from __future__ import annotations

import sys
from pathlib import Path as _P
_SKILL = _P(__file__).resolve().parents[2]
if str(_SKILL) not in sys.path:
    sys.path.insert(0, str(_SKILL))
from _safe_invoke import run_python, run_daemon_thread, git_status_summary, write_local_alert  # noqa: E402

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

CC = Path(__file__).resolve().parents[1]
ARMY = CC.parent
CONFIG = CC / "config" / "army_config.json"
TASKS = CC / "tasks"
TASKS.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(CC / "scripts"))
from army_queue_utils import (  # noqa: E402
    cleanup_stale_locks,
    dedupe_by_role,
    dedupe_cron_by_role,
    pending_roles,
    queue_dirs,
)

CRON_ROLES = [
    ("lattice-check", "cron-lattice"),
    ("stack-integrity", "cron-stack"),
    ("clawhub-catalog-audit", "cron-clawhub"),
    ("public-pages-check", "cron-pages"),
    ("audit-suite", "cron-audit-suite"),
    ("memory-sync", "cron-memory"),
    ("anchor-health", "cron-anchor"),
    ("mesh-cartographer", "cron-mesh"),
    ("self-tune", "cron-self-tune"),
    ("egg-planter", "cron-egg-plant"),
    ("registry-planter", "cron-registry-plant"),
    ("moltx-lattice-pulse", "cron-moltx"),
    ("moltbook-lyra-pulse", "cron-moltbook-lyra"),
    ("moltbook-lightfather-pulse", "cron-moltbook-lf"),
]


def load_cfg() -> dict:
    if not CONFIG.is_file():
        return {}
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def load_perf() -> dict:
    return load_cfg().get("performance") or {}


def main() -> int:
    perf = load_perf()
    dirs = queue_dirs(CC, ARMY)
    stale_s = float(perf.get("stale_lock_seconds", 600))
    cleanup_stale_locks(dirs, stale_s)
    if perf.get("dedupe_cron_by_role", True):
        dedupe_cron_by_role(dirs)
    max_per_role = int(perf.get("max_pending_per_role", 1))
    if max_per_role > 0:
        dedupe_by_role(dirs, max_per_role=max_per_role)

    run_python(CC / "scripts" / "army_self_tune.py", timeout=120)
    run_python(CC / "scripts" / "sentinel_heartbeat.py", timeout=240)
    ts_hub = Path.home() / ".grok" / "skills" / "lygo-api-token-saver" / "scripts" / "token_saver_once.py"
    if not ts_hub.is_file():
        ts_hub = Path(r"I:\E Drive\.grok\skills\lygo-api-token-saver\scripts\token_saver_once.py")
    if ts_hub.is_file() and load_cfg().get("token_saver", {}).get("enabled", True):
        run_python(ts_hub, timeout=60)

    pending = pending_roles(dirs)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    seeded = 0
    skipped = 0

    for role, prefix in CRON_ROLES:
        if role in pending:
            skipped += 1
            continue
        tid = f"{prefix}-{ts}"
        path = TASKS / f"{tid}.task.json"
        path.write_text(json.dumps({"id": tid, "role": role, "payload": {}}), encoding="utf-8")
        pending.add(role)
        seeded += 1

    legacy = ARMY / "ollama_queue"
    if perf.get("mirror_legacy_queue", False):
        legacy.mkdir(parents=True, exist_ok=True)
        for p in TASKS.glob("cron-*.task.json"):
            dest = legacy / p.name
            if not dest.exists():
                dest.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")

    print(f"Cron tick OK — seeded={seeded} skipped={skipped} tasks={TASKS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())