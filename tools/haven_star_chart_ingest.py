#!/usr/bin/env python3
"""Ingest pending Haven Star Chart submissions — re-gate, accept, rebuild registry."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PENDING = ROOT / "data" / "haven_star_chart" / "submissions" / "pending"
ACCEPTED = ROOT / "data" / "haven_star_chart" / "submissions" / "accepted"
REJECTED = ROOT / "data" / "haven_star_chart" / "submissions" / "rejected"

sys.path.insert(0, str(ROOT / "tools"))
from haven_star_chart_feed import log_ingest_accepted, log_ingest_rejected, publish_feed  # noqa: E402
from haven_star_chart_gate import validate_submission  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--i-consent", action="store_true", help="Steward approves ingest to live chart")
    ap.add_argument("--rebuild", action="store_true", default=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.i_consent:
        print(json.dumps({"verdict": "BLOCKED", "reason": "consent_required"}))
        return 2

    PENDING.mkdir(parents=True, exist_ok=True)
    ACCEPTED.mkdir(parents=True, exist_ok=True)
    REJECTED.mkdir(parents=True, exist_ok=True)

    accepted: list[str] = []
    rejected: list[str] = []

    for f in sorted(PENDING.glob("*.json")):
        try:
            sub = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            rejected.append(f.name)
            if not args.dry_run:
                log_ingest_rejected(None, {"errors": ["invalid_json"]}, f.name)
                shutil.move(str(f), str(REJECTED / f.name))
            continue
        gate = validate_submission(sub)
        if not gate["all_pass"]:
            rejected.append(f.name)
            if not args.dry_run:
                sub["ingest_reject"] = gate
                (REJECTED / f.name).write_text(json.dumps(sub, indent=2), encoding="utf-8")
                f.unlink()
                log_ingest_rejected(sub, gate, f.name)
            continue
        accepted.append(f.name)
        if not args.dry_run:
            shutil.move(str(f), str(ACCEPTED / f.name))
            log_ingest_accepted(sub, f.name)

    report = {"accepted": accepted, "rejected": rejected, "count_accepted": len(accepted)}
    print(json.dumps(report, indent=2))

    if not args.dry_run and (accepted or rejected):
        publish_feed()

    if args.rebuild and accepted and not args.dry_run:
        cp = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "build_haven_star_chart.py")],
            cwd=ROOT,
        )
        return cp.returncode
    return 0 if accepted or not list(PENDING.glob("*.json")) else 1


if __name__ == "__main__":
    raise SystemExit(main())