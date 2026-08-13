#!/usr/bin/env python3
"""Single cron tick: optional sentinel + seed safe deterministic army tasks (no LLM).

Defaults match SKILL.md: sentinel/self_tune/public probes OFF.
Planting and social roles seed only when config + consent allow.
"""

from __future__ import annotations

import sys
from pathlib import Path as _P

_SKILL = _P(__file__).resolve().parents[2]
if str(_SKILL) not in sys.path:
    sys.path.insert(0, str(_SKILL))
from _safe_invoke import run_python  # noqa: E402

import json
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

# Always-safe roles only (no plant / no social / no public HTTPS / no self-tune)
SAFE_CRON_ROLES = [
    ("lattice-check", "cron-lattice"),
    ("stack-integrity", "cron-stack"),
    ("clawhub-catalog-audit", "cron-clawhub"),
    ("audit-suite", "cron-audit-suite"),
    ("memory-sync", "cron-memory"),
    ("anchor-health", "cron-anchor"),
    ("mesh-cartographer", "cron-mesh"),
]

# Opt-in only (not in SAFE list)
PUBLIC_PROBE_ROLE = ("public-pages-check", "cron-pages")
SELF_TUNE_ROLE = ("self-tune", "cron-self-tune")

PLANT_CRON_ROLES = [
    ("egg-planter", "cron-egg-plant"),
    ("registry-planter", "cron-registry-plant"),
]

SOCIAL_CRON_ROLES = [
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


def active_roles(cfg: dict) -> list[tuple[str, str]]:
    roles = list(SAFE_CRON_ROLES)
    planting = cfg.get("planting") or {}
    if planting.get("enabled") and planting.get("consent"):
        roles.extend(PLANT_CRON_ROLES)
    social = cfg.get("social_publish") or {}
    if social.get("enabled") and social.get("allow_social_pulse"):
        roles.extend(SOCIAL_CRON_ROLES)
    sent = cfg.get("sentinel") or {}
    # Public HTTPS probes only when explicitly enabled (default false)
    if sent.get("probe_public_pages") is True:
        roles.append(PUBLIC_PROBE_ROLE)
    # self-tune queue seed only when self_tune.enabled (default false)
    if (cfg.get("self_tune") or {}).get("enabled") is True:
        roles.append(SELF_TUNE_ROLE)
    return roles


def main() -> int:
    cfg = load_cfg()
    perf = load_perf()
    dirs = queue_dirs(CC, ARMY)
    stale_s = float(perf.get("stale_lock_seconds", 600))
    cleanup_stale_locks(dirs, stale_s)
    if perf.get("dedupe_cron_by_role", True):
        dedupe_cron_by_role(dirs)
    max_per_role = int(perf.get("max_pending_per_role", 1))
    if max_per_role > 0:
        dedupe_by_role(dirs, max_per_role=max_per_role)

    # self_tune script only if enabled
    if (cfg.get("self_tune") or {}).get("enabled", False):
        run_python(CC / "scripts" / "army_self_tune.py", timeout=120)

    # sentinel only if enabled (default false in example config)
    if (cfg.get("sentinel") or {}).get("enabled", False):
        run_python(CC / "scripts" / "sentinel_heartbeat.py", timeout=240)

    pending = pending_roles(dirs)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    seeded = 0
    skipped = 0
    gated_off = 0

    for role, prefix in active_roles(cfg):
        if role in pending:
            skipped += 1
            continue
        tid = f"{prefix}-{ts}"
        path = TASKS / f"{tid}.task.json"
        path.write_text(json.dumps({"id": tid, "role": role, "payload": {}}), encoding="utf-8")
        pending.add(role)
        seeded += 1

    # Count gated roles for transparency
    if not (cfg.get("self_tune") or {}).get("enabled"):
        gated_off += 1
    if not (cfg.get("sentinel") or {}).get("probe_public_pages"):
        gated_off += 1

    print(
        json.dumps(
            {
                "ok": True,
                "seeded": seeded,
                "skipped": skipped,
                "gated_off_flags": gated_off,
                "roles": [r[0] for r in active_roles(cfg)],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
