#!/usr/bin/env python3
"""Seed local-only deterministic tasks (v0.8.0).

Requires LYGO_ARMY_SEED_TASKS=1 after reviewing SECURITY.md.
Never seeds public-pages, social pulses, or planting unless extra env gates are set.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
CC = HERE / "ollama_command_center"
TASKS = CC / "tasks"
LEGACY = HERE / "ollama_queue"
CONFIG = CC / "config" / "army_config.json"


def main() -> int:
    if os.environ.get("LYGO_ARMY_SEED_TASKS", "").strip().lower() not in ("1", "true", "yes"):
        print(
            "SKIP seed_productive_tasks — set LYGO_ARMY_SEED_TASKS=1 after reviewing "
            "references/SECURITY.md"
        )
        return 0

    stack = os.environ.get("LYGO_STACK_ROOT", "").strip()
    cfg = {}
    if CONFIG.is_file():
        cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
        stack = (cfg.get("lygo_stack_root") or stack or "").strip()
    if not stack:
        print("ERROR: set LYGO_STACK_ROOT or lygo_stack_root in army_config.json", file=sys.stderr)
        return 2
    os.environ.setdefault("LYGO_STACK_ROOT", stack)

    # Safe local defaults only
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    seeds = [
        ("lattice-check", f"seed-lattice-{ts}", {}),
        ("clawhub-catalog-audit", f"seed-clawhub-{ts}", {}),
        ("memory-sync", f"seed-memory-{ts}", {}),
        ("kernel-verify-only", f"seed-kernel-verify-{ts}", {}),
        (
            "memory-triage",
            f"seed-triage-{ts}",
            {
                "prompt": (
                    "Review local army queue and lattice status. "
                    'Output compact JSON: {"priority":"low|med|high","summary":"one line","next_action":"one step"}'
                ),
            },
        ),
    ]

    # Optional high-risk seeds — each requires its own env gate
    if os.environ.get("LYGO_ARMY_SEED_SELF_TUNE", "").strip().lower() in ("1", "true", "yes"):
        if (cfg.get("self_tune") or {}).get("enabled"):
            seeds.append(("self-tune", f"seed-self-tune-{ts}", {}))
    if os.environ.get("LYGO_ARMY_SEED_PUBLIC_PAGES", "").strip().lower() in ("1", "true", "yes"):
        if (cfg.get("sentinel") or {}).get("probe_public_pages"):
            seeds.append(("public-pages-check", f"seed-pages-{ts}", {}))
    if os.environ.get("LYGO_ARMY_SEED_PLANTING", "").strip().lower() in ("1", "true", "yes"):
        planting = cfg.get("planting") or {}
        if planting.get("enabled") and planting.get("consent"):
            seeds.append(("egg-planter", f"seed-egg-plant-{ts}", {}))
            seeds.append(("registry-planter", f"seed-registry-plant-{ts}", {}))

    TASKS.mkdir(parents=True, exist_ok=True)
    LEGACY.mkdir(parents=True, exist_ok=True)
    for role, tid, payload in seeds:
        body = {"id": tid, "role": role, "payload": payload}
        text = json.dumps(body, indent=2)
        (TASKS / f"{tid}.task.json").write_text(text, encoding="utf-8")
        (LEGACY / f"{tid}.task.json").write_text(text, encoding="utf-8")

    print(f"Seeded {len(seeds)} local-safe tasks -> {TASKS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
