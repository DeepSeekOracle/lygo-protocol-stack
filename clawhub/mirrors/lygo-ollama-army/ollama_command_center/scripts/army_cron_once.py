#!/usr/bin/env python3
"""Single cron tick: local sentinel + seed deterministic LOCAL roles only (v0.7.0).

No cross-skill execution, no social pulse roles, no token-saver external path.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

CC = Path(__file__).resolve().parents[1]
ARMY = CC.parent
_SKILL = ARMY
if str(_SKILL) not in sys.path:
    sys.path.insert(0, str(_SKILL))
from _safe_invoke import run_python  # noqa: E402

CONFIG = CC / "config" / "army_config.json"
TASKS = CC / "tasks"
TASKS.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(CC / "scripts"))
from army_queue_utils import cleanup_stale_locks, dedupe_by_role, pending_roles, queue_dirs  # noqa: E402

# Local-only deterministic roles (no social / moltbook / planter by default)
CRON_ROLES = [
    ("lattice-check", "cron-lattice"),
    ("clawhub-catalog-audit", "cron-clawhub"),
    ("memory-sync", "cron-memory"),
    ("kernel-verify-only", "cron-kernel-verify"),
    ("self-tune", "cron-self-tune"),
]


def load_cfg() -> dict:
    if not CONFIG.is_file():
        return {}
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def main() -> int:
    cfg = load_cfg()
    planting = cfg.get("planting") or {}
    access = cfg.get("access") or {}
    if access.get("social_publish"):
        print("[refuse] social_publish must stay false in public army")
        return 2

    dirs = queue_dirs(CC, ARMY)
    cleanup_stale_locks(dirs, 600)
    dedupe_by_role(dirs, max_per_role=1)

    # self-tune only if explicitly enabled
    if (cfg.get("self_tune") or {}).get("enabled"):
        run_python(CC / "scripts" / "army_self_tune.py", timeout=120)
    run_python(CC / "scripts" / "sentinel_heartbeat.py", timeout=240)

    roles = list(CRON_ROLES)
    # planter only if both enabled AND consent (still local queue seed only)
    if planting.get("enabled") and planting.get("consent"):
        roles.append(("egg-planter", "cron-egg-plant"))

    pending = pending_roles(dirs)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    seeded = 0
    for role, prefix in roles:
        if role in pending:
            continue
        tid = f"{prefix}-{ts}"
        path = TASKS / f"{tid}.task.json"
        path.write_text(json.dumps({"id": tid, "role": role, "payload": {}}), encoding="utf-8")
        pending.add(role)
        seeded += 1

    print(f"Cron tick OK — seeded={seeded} tasks={TASKS} (local roles only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
