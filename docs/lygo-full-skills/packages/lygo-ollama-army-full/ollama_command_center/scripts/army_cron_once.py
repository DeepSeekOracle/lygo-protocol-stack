#!/usr/bin/env python3
"""Single cron tick: sentinel + seed safe deterministic army tasks (no LLM).

Planting and social/molt* roles are NOT seeded unless config + consent allow.
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

# Always-safe roles (no plant / no social outbound)
SAFE_CRON_ROLES = [
    ("lattice-check", "cron-lattice"),
    ("stack-integrity", "cron-stack"),
    ("clawhub-catalog-audit", "cron-clawhub"),
    ("public-pages-check", "cron-pages"),
    ("audit-suite", "cron-audit-suite"),
    ("memory-sync", "cron-memory"),
    ("anchor-health", "cron-anchor"),
    ("mesh-cartographer", "cron-mesh"),
    ("self-tune", "cron-self-tune"),
]

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
    # social / public probe roles require explicit social_publish allow
    social = cfg.get("social_publish") or {}
    if social.get("enabled") and social.get("allow_social_pulse"):
        roles.extend(SOCIAL_CRON_ROLES)
    # public-pages-check is safe GET; if operator disabled probes, drop it
    sent = cfg.get("sentinel") or {}
    if sent.get("probe_public_pages") is False:
        roles = [r for r in roles if r[0] != "public-pages-check"]
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

    # self_tune only if enabled (default false) — run_python still no-ops when disabled
    if (cfg.get("self_tune") or {}).get("enabled", False):
        run_python(CC / "scripts" / "army_self_tune.py", timeout=120)
    run_python(CC / "scripts" / "sentinel_heartbeat.py", timeout=240)

    ts_hub = Path.home() / ".grok" / "skills" / "lygo-api-token-saver" / "scripts" / "token_saver_once.py"
    if not ts_hub.is_file():
        ts_hub = Path(r"I:\E Drive\.grok\skills\lygo-api-token-saver\scripts\token_saver_once.py")
    if ts_hub.is_file() and (cfg.get("token_saver") or {}).get("enabled", False):
        # token_saver may be outside army allowlist — only if path is under skill trees
        try:
            run_python(ts_hub, timeout=60)
        except Exception:
            pass

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

    # Count gated roles not active for report honesty
    for role, _ in PLANT_CRON_ROLES + SOCIAL_CRON_ROLES:
        if role not in {r[0] for r in active_roles(cfg)}:
            gated_off += 1

    legacy = ARMY / "ollama_queue"
    if perf.get("mirror_legacy_queue", False):
        legacy.mkdir(parents=True, exist_ok=True)
        for p in TASKS.glob("cron-*.task.json"):
            dest = legacy / p.name
            if not dest.exists():
                dest.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")

    print(
        f"Cron tick OK — seeded={seeded} skipped={skipped} gated_off={gated_off} "
        f"plant={bool((cfg.get('planting') or {}).get('enabled'))} tasks={TASKS}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
