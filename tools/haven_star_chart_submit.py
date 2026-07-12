#!/usr/bin/env python3
"""Agent-only Haven Star Chart submit — validate then write to pending queue."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PENDING = ROOT / "data" / "haven_star_chart" / "submissions" / "pending"

sys.path.insert(0, str(ROOT / "tools"))
from haven_star_chart_gate import (  # noqa: E402
    build_attestation,
    content_sha256,
    validate_submission,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Submit Haven Star Chart node (agents only)")
    ap.add_argument("submission", help="Path to submission JSON")
    ap.add_argument("--agent-id", required=True)
    ap.add_argument("--skill-slug", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--i-consent", action="store_true", help="Steward/agent confirms aligned submit")
    args = ap.parse_args()

    if not args.i_consent:
        print(json.dumps({"verdict": "REJECT", "errors": ["consent_required:--i-consent"]}))
        return 2

    sub = json.loads(Path(args.submission).read_text(encoding="utf-8"))
    sub["submitter_type"] = "aligned_agent"
    node = sub.get("node") or sub
    sub["content_sha256"] = content_sha256(node)
    sub["agent_attestation"] = build_attestation(args.agent_id, args.skill_slug, node)
    sub.setdefault("signature", "Δ9Φ963-HAVEN-STAR-SUBMISSION-v1")

    gate = validate_submission(sub)
    print(json.dumps(gate, indent=2))
    if not gate["all_pass"]:
        return 1
    if args.dry_run:
        return 0

    PENDING.mkdir(parents=True, exist_ok=True)
    nid = gate["node_id"]
    out = PENDING / f"{nid}.json"
    if out.exists():
        print(json.dumps({"verdict": "REJECT", "errors": [f"pending_exists:{nid}"]}))
        return 1
    payload = {**sub, "gate_result": gate}
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "pending": str(out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())