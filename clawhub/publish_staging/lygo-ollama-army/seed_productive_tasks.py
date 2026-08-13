#!/usr/bin/env python3
"""Seed productive deterministic + optional LLM tasks for the Ollama army.

Requires LYGO_ARMY_SEED_TASKS=1.
Default seeds are safe local roles only.
- public-pages-check: only if sentinel.probe_public_pages=true
- self-tune / plant roles: only if LYGO_ARMY_SEED_PLANTING=1 AND config gates
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
    cfg: dict = {}
    stack = os.environ.get("LYGO_STACK_ROOT", "").strip()
    if CONFIG.is_file():
        cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
        stack = cfg.get("lygo_stack_root", stack) or stack
    if not stack:
        print("ERROR: set LYGO_STACK_ROOT or lygo_stack_root in army_config.json", file=sys.stderr)
        return 2
    os.environ.setdefault("LYGO_STACK_ROOT", stack)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    seeds = [
        ("lattice-check", f"seed-lattice-{ts}", {}),
        ("stack-integrity", f"seed-stack-{ts}", {}),
        ("clawhub-catalog-audit", f"seed-clawhub-{ts}", {}),
        ("audit-suite", f"seed-audit-{ts}", {}),
        ("memory-sync", f"seed-memory-{ts}", {}),
        ("mesh-cartographer", f"seed-mesh-{ts}", {}),
        (
            "memory-triage",
            f"seed-triage-{ts}",
            {
                "prompt": (
                    "Review LYGO lattice health. "
                    'Output compact JSON: {"priority":"low|med|high","summary":"one line","next_action":"one step"}'
                ),
            },
        ),
    ]

    # Optional public probes only when config enables them
    if (cfg.get("sentinel") or {}).get("probe_public_pages") is True:
        seeds.append(("public-pages-check", f"seed-pages-{ts}", {}))

    # Privileged roles never in default list — require explicit env + config
    planting_ok = os.environ.get("LYGO_ARMY_SEED_PLANTING", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    planting = cfg.get("planting") or {}
    access = cfg.get("access") or {}
    if (
        planting_ok
        and planting.get("enabled")
        and planting.get("consent")
        and access.get("allow_privileged_roles")
    ):
        seeds.extend(
            [
                ("egg-planter", f"seed-egg-plant-{ts}", {}),
                ("registry-planter", f"seed-registry-plant-{ts}", {}),
            ]
        )
    if planting_ok and (cfg.get("self_tune") or {}).get("enabled") is True:
        seeds.append(("self-tune", f"seed-self-tune-{ts}", {}))

    TASKS.mkdir(parents=True, exist_ok=True)
    LEGACY.mkdir(parents=True, exist_ok=True)
    for role, tid, payload in seeds:
        body = {"id": tid, "role": role, "payload": payload}
        text = json.dumps(body, indent=2)
        (TASKS / f"{tid}.task.json").write_text(text, encoding="utf-8")
        (LEGACY / f"{tid}.task.json").write_text(text, encoding="utf-8")

    print(f"Seeded {len(seeds)} tasks -> {TASKS} and {LEGACY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
