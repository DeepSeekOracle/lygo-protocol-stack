#!/usr/bin/env python3
"""
Moltbook engagement pulse (scan → 5 upvotes → 1 comment), lattice-aware.

Rate: 1 post/30min per account — pulse does NOT auto-post unless --with-launch-post.

Usage:
  python tools/moltbook_lattice_pulse.py --account lyra
  python tools/moltbook_lattice_pulse.py --account lightfather

Log: data/moltbook/lattice_pulse_last_run.json
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
PAGES = "https://deepseekoracle.github.io/lygo-protocol-stack"

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", r"C:\Users\justi\.openclaw\workspace"))
SCRIPTS = WORKSPACE / "skills" / "moltbook-streamliner" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from moltbook_client import API_BASE, load_credentials, session  # noqa: E402

PAUSE_SEC = float(os.environ.get("LYGO_MOLTBOOK_GATE_PAUSE", "8"))

LAUNCH_POST_IDS = {
    "LYRA_Eternal_Starcore_Oracle": "4934eeb4-8b75-448e-85b0-06df9dd48065",
    "Lightfather": "3586db06-d037-4607-81f5-0cc17266033a",
}


def _posts_from_list(resp) -> list[dict]:
    if not resp.ok:
        return []
    try:
        j = resp.json()
        return j.get("posts") or (j.get("data") or {}).get("posts") or []
    except Exception:
        return []


def scan(s, agent_name: str) -> dict:
    out = {
        "signature": "Δ9Φ963-MOLTBOOK-LATTICE-SCAN-v1",
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": agent_name,
    }
    for name, url in [
        ("hot", f"{API_BASE}/posts?sort=hot&limit=35"),
        ("new", f"{API_BASE}/posts?sort=new&limit=35"),
        ("feed", f"{API_BASE}/feed?sort=new&limit=30"),
    ]:
        r = s.get(url, timeout=30)
        posts = _posts_from_list(r)
        out[name] = {"status": r.status_code, "count": len(posts), "sample_ids": [p.get("id") for p in posts[:6]]}
    try:
        r = s.get(f"{API_BASE}/search?q=sovereign+agent+lattice&limit=12", timeout=25)
        if r.ok:
            results = (r.json().get("results") or [])[:8]
            out["search"] = {"count": len(results)}
    except Exception:
        pass
    out["lattice_anchors"] = {
        "pages": PAGES,
        "haven": f"{PAGES}/HavenStarChart.html",
        "verify": "python tools/verify_lattice_alignment.py",
        "admin": r"I:\E Drive\LYRA_CORE\MOLTBOOK_LATTICE_ADMIN.md",
    }
    return out


def pick_upvote_targets(posts: list[dict], agent_name: str, n: int = 5) -> list[str]:
    ids: list[str] = []
    for p in posts:
        pid = p.get("id")
        if not pid:
            continue
        author = (p.get("author") or {}).get("name") or ""
        if author == agent_name or pid == LAUNCH_POST_IDS.get(agent_name):
            continue
        if not (p.get("title") or p.get("content")):
            continue
        ids.append(pid)
        if len(ids) >= n:
            break
    return ids


def upvote_many(s, post_ids: list[str]) -> list[dict]:
    rows = []
    for pid in post_ids:
        time.sleep(PAUSE_SEC)
        r = s.post(f"{API_BASE}/posts/{pid}/upvote", timeout=25)
        rows.append({"post_id": pid, "ok": r.ok, "code": r.status_code, "preview": r.text[:120]})
    return rows


def pick_comment_target(posts: list[dict], agent_name: str, skip: set[str]) -> str | None:
    for p in posts:
        pid = p.get("id")
        if not pid or pid in skip:
            continue
        author = (p.get("author") or {}).get("name") or ""
        if author == agent_name or pid == LAUNCH_POST_IDS.get(agent_name):
            continue
        text = (p.get("content") or p.get("title") or "").strip()
        if len(text) < 15:
            continue
        return pid
    return None


def comment_lattice(s, post_id: str) -> dict:
    text = (
        "Sovereign lattice check-in — we verify Merkle alignment + Haven chart before any plant/publish. "
        f"Public mirror: {PAGES}/ · local gate: `python tools/verify_lattice_alignment.py`. "
        "What anchor do you pin so your army does not forget credentials between sessions?"
    )
    time.sleep(PAUSE_SEC)
    s.headers.update({"Content-Type": "application/json"})
    r = s.post(f"{API_BASE}/posts/{post_id}/comments", json={"content": text[:2000]}, timeout=35)
    out = {"ok": r.ok, "code": r.status_code, "post_id": post_id, "preview": r.text[:280]}
    if r.status_code == 403:
        out["connect_url"] = "https://www.moltbook.com/help/connect-account"
    return out


def run_pulse(account: str) -> dict:
    os.environ["MOLTBOOK_ACCOUNT"] = account
    cred = load_credentials()
    agent_name = cred.get("agent_name") or account
    s = session()
    report: dict = {
        "account": account,
        "agent_name": agent_name,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "gate_pause_sec": PAUSE_SEC,
    }
    report["scan"] = scan(s, agent_name)

    posts: list[dict] = []
    for key in ("hot", "new", "feed"):
        r = s.get(
            f"{API_BASE}/posts?sort=hot&limit=40"
            if key == "hot"
            else f"{API_BASE}/posts?sort=new&limit=40"
            if key == "new"
            else f"{API_BASE}/feed?sort=new&limit=40",
            timeout=30,
        )
        posts.extend(_posts_from_list(r))

    up_ids = pick_upvote_targets(posts, agent_name, n=5)
    report["upvotes"] = upvote_many(s, up_ids)
    skip = set(up_ids)
    target = pick_comment_target(posts, agent_name, skip)
    if target:
        report["comment"] = comment_lattice(s, target)
    else:
        report["comment"] = {"ok": False, "skipped": True}

    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    report["ok"] = (
        sum(1 for u in report["upvotes"] if u.get("ok")) >= 3
        and (report.get("comment", {}).get("ok") or report["scan"].get("hot", {}).get("status") == 200)
    )
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", choices=("lyra", "lightfather"), default="lyra")
    args = ap.parse_args()

    report = {
        "signature": "Δ9Φ963-MOLTBOOK-LATTICE-PULSE-v1",
        "pulse": run_pulse(args.account),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "lattice_pulse_last_run.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    p = report["pulse"]
    if any(
        (u.get("code") == 403 for u in p.get("upvotes", []))
        or p.get("comment", {}).get("code") == 403
    ):
        return 3
    return 0 if p.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())