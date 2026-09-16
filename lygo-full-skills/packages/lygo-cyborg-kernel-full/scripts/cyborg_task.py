#!/usr/bin/env python3
"""
LYGO Cyborg Task Runner — autonomous task loop with Continuum self-police.

FULL unlocked channel: runs local task specs end-to-end (plan → work hooks → seal).
Does not network or spawn shell by default. Optional --allow-shell is OFF forever here
(self-police: no shell in cyborg_task; use stack tools with human for shell).

Signature: Delta9Phi963-CYBORG-KERNEL-v1.0.0
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cyborg_kernel as ck  # noqa: E402

SIG = ck.SIG
STATE = ck.STATE


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_task(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    for k in ("goal", "claims"):
        if k not in raw:
            raise ValueError(f"task missing {k}")
    return raw


def run_task(task: dict[str, Any], base: Path, write_state: bool, consent: bool) -> dict[str, Any]:
    """
    Autonomous cycle:
    1. boot limbs
    2. optional context pack of notes
    3. continuum preflight against claims (world must already match or fail)
    4. emit handoff + status
    """
    boot = ck.boot_report(task.get("stack_root"))
    if not boot.get("ready"):
        return {"ok": False, "phase": "boot", "boot": boot, "signature": SIG}

    notes = task.get("notes") or task.get("brief") or ""
    packed = None
    if notes:
        packed = ck.pack_context(str(notes), budget=int(task.get("token_budget", 4000)))

    claims = task["claims"]
    pf = ck.preflight_done(
        claims=claims,
        task=str(task["goal"]),
        base=str(base),
        agent=str(task.get("agent", "lygo-cyborg")),
    )

    # handoff markdown via continuum
    sys.path.insert(0, str(ck.KERNEL))
    import continuum as cont  # noqa: E402

    capsule = pf.get("capsule") or {}
    verify = pf.get("verify") or {}
    handoff = cont.handoff_markdown(capsule, verify)

    out = {
        "ok": bool(pf.get("can_claim_done")),
        "phase": "complete" if pf.get("can_claim_done") else "blocked_self_police",
        "goal": task["goal"],
        "can_claim_done": pf.get("can_claim_done"),
        "boot": {"ready": boot.get("ready"), "limbs": boot.get("limbs")},
        "context_pack": {
            "over_budget": packed.get("over_budget") if packed else None,
            "tokens": (packed or {}).get("estimate"),
        },
        "preflight": {
            "can_claim_done": pf.get("can_claim_done"),
            "sealed_pass": capsule.get("sealed_pass"),
            "sealed_fail": capsule.get("sealed_fail"),
            "root_hash": capsule.get("root_hash"),
            "capsule_id": capsule.get("id"),
        },
        "handoff_markdown": handoff,
        "next": (
            ["Task holds under Continuum — safe to report done to human"]
            if pf.get("can_claim_done")
            else [
                "Self-police blocked done claim",
                "Fix files on disk or adjust claims",
                "Re-run cyborg_task.py run",
            ]
        ),
        "signature": SIG,
        "finished_utc": utc_now(),
    }

    if write_state:
        if not consent:
            out["state_write"] = "skipped_need_i_consent"
        else:
            STATE.mkdir(parents=True, exist_ok=True)
            cid = str(capsule.get("id") or "task")
            sp = STATE / f"{cid}.json"
            sp.write_text(json.dumps(out, indent=2, default=str) + "\n", encoding="utf-8")
            # also write capsule alone
            (STATE / f"{cid}.capsule.json").write_text(
                json.dumps(capsule, indent=2, default=str) + "\n", encoding="utf-8"
            )
            out["state_write"] = str(sp)

    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="LYGO Cyborg autonomous task runner")
    sub = ap.add_subparsers(dest="cmd")
    r = sub.add_parser("run", help="Run a task JSON through self-policed loop")
    r.add_argument("--task", required=True, help="Path to task JSON")
    r.add_argument("--base", default=None, help="Filesystem base for claims")
    r.add_argument("--write-state", action="store_true")
    r.add_argument("--i-consent", action="store_true")
    sub.add_parser("example", help="Print example task JSON")
    args = ap.parse_args()

    if args.cmd == "example" or args.cmd is None:
        ex = {
            "goal": "Prove README and continuum limb exist for cyborg kernel",
            "agent": "lygo-cyborg",
            "token_budget": 2000,
            "notes": "Cyborg task example — world must already satisfy claims.",
            "claims": [
                {"id": "c1", "kind": "file_exists", "path": "SKILL.md"},
                {"id": "c2", "kind": "file_contains", "path": "SKILL.md", "needle": "Cyborg"},
                {"id": "c3", "kind": "file_exists", "path": "kernel/continuum.py"},
                {"id": "c4", "kind": "glob_count_gte", "pattern": "scripts/*.py", "n": 2},
            ],
        }
        print(json.dumps(ex, indent=2))
        return 0

    if args.cmd == "run":
        task = load_task(Path(args.task))
        base = Path(args.base).resolve() if args.base else Path.cwd()
        out = run_task(task, base, write_state=args.write_state, consent=args.i_consent)
        print(json.dumps(out, indent=2, default=str))
        return 0 if out.get("ok") else 10

    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
