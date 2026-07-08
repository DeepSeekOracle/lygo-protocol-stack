#!/usr/bin/env python3
"""
Moltbook stack + army launch (dual account), wired to LYGO lattice.

Usage:
  python tools/moltbook_lattice_army_launch.py --account lyra
  python tools/moltbook_lattice_army_launch.py --account lightfather
  python tools/moltbook_lattice_army_launch.py --account both
  python tools/moltbook_lattice_army_launch.py --dry-run --account both

Env: MOLTBOOK_ACCOUNT set per account. Credentials: OPENCLAW credentials/moltbook_*.json
Log: data/moltbook/lattice_launch_last_run.json
Admin: I:\\E Drive\\LYRA_CORE\\MOLTBOOK_LATTICE_ADMIN.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "moltbook"
LYRA_BODY = ROOT / "docs" / "MOLTBOOK_LAUNCH_LYRA_BODY.md"
LF_BODY = ROOT / "docs" / "MOLTBOOK_LAUNCH_LIGHTFATHER_BODY.md"
PAGES = "https://deepseekoracle.github.io/lygo-protocol-stack"

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", r"C:\Users\justi\.openclaw\workspace"))
SCRIPTS = WORKSPACE / "skills" / "moltbook-streamliner" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from moltbook_client import API_BASE, load_credentials, request_with_backoff, session  # noqa: E402

from moltbook_verification_solver import submit_verification  # noqa: E402

PAUSE_BETWEEN_ACCOUNTS = float(os.environ.get("LYGO_MOLTBOOK_ACCOUNT_PAUSE", "5"))


def launch_payload(account: str) -> dict:
    if account == "lightfather":
        body_path = LF_BODY
        submolt = os.environ.get("MOLTBOOK_LF_SUBMOLT", "general")
        title = "LYGO stack + Ollama army — Lightfather lattice revival (2026)"
    else:
        body_path = LYRA_BODY
        submolt = os.environ.get("MOLTBOOK_LYRA_SUBMOLT", "lyra-haven")
        title = "LYGO Protocol Stack + Ollama army — public lattice revival (2026)"
    content = body_path.read_text(encoding="utf-8").strip() if body_path.is_file() else (
        f"LYGO public lattice: {PAGES}/ — verify with tools/verify_lattice_alignment.py"
    )
    return {"submolt_name": submolt, "title": title[:300], "content": content[:39000]}


def post_launch(account: str, dry_run: bool) -> dict:
    os.environ["MOLTBOOK_ACCOUNT"] = account
    cred = load_credentials()
    payload = launch_payload(account)
    row = {
        "account": account,
        "agent_name": cred.get("agent_name"),
        "submolt": payload["submolt_name"],
        "title": payload["title"],
        "dry_run": dry_run,
        "lattice": {
            "repo": "https://github.com/DeepSeekOracle/lygo-protocol-stack",
            "pages": PAGES,
            "admin_doc": r"I:\E Drive\LYRA_CORE\MOLTBOOK_LATTICE_ADMIN.md",
            "moltx_launch_ref": "docs/MOLTX_STACK_ARMY_LAUNCH_2026-07-02.md",
        },
    }
    if dry_run:
        row["ok"] = True
        row["payload_preview"] = payload["content"][:400]
        return row

    s = session()
    s.headers.update({"Content-Type": "application/json"})
    r, tries = request_with_backoff(
        "POST", f"{API_BASE}/posts", session_obj=s, json=payload, max_tries=3, timeout=90
    )
    row["ok"] = r.ok
    row["code"] = r.status_code
    row["tries"] = tries
    row["body_preview"] = r.text[:500]
    if r.status_code == 403:
        row["blocked"] = True
        row["connect_url"] = "https://www.moltbook.com/help/connect-account"
    if r.ok:
        try:
            j = r.json()
            pid = (j.get("data") or {}).get("id") or (j.get("post") or {}).get("id")
            row["post_id"] = pid
            if pid:
                row["url"] = f"https://www.moltbook.com/post/{pid}"
            v = submit_verification(s, API_BASE, j)
            row["verification"] = v
            if v.get("success") or v.get("skipped"):
                row["published"] = True
            elif (j.get("post") or {}).get("verification_status") == "pending":
                row["published"] = False
                row["note"] = (
                    "Post API-created but hidden until math verify succeeds "
                    "(see Moltbook skill § AI Verification)."
                )
        except Exception:
            pass
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", choices=("lyra", "lightfather", "both"), default="both")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    accounts = ["lyra", "lightfather"] if args.account == "both" else [args.account]
    report = {
        "signature": "Δ9Φ963-MOLTBOOK-LATTICE-LAUNCH-v1",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "launches": [],
    }
    for i, acct in enumerate(accounts):
        if i > 0:
            time.sleep(PAUSE_BETWEEN_ACCOUNTS)
        report["launches"].append(post_launch(acct, args.dry_run))

    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    report["ok"] = all(x.get("ok") for x in report["launches"]) and not any(
        x.get("blocked") for x in report["launches"]
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "lattice_launch_last_run.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if any(x.get("blocked") for x in report["launches"]):
        return 3
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())