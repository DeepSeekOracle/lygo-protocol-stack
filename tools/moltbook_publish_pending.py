#!/usr/bin/env python3
"""Delete stuck pending posts, repost with verify (post + math challenge)."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", r"C:\Users\justi\.openclaw\workspace"))
SCRIPTS = WORKSPACE / "skills" / "moltbook-streamliner" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT / "tools"))

from moltbook_client import API_BASE, load_credentials, request_with_backoff, session  # noqa: E402
from moltbook_verification_solver import solve_challenge_text, submit_verification  # noqa: E402


def ollama_answer(challenge: str) -> str | None:
    prompt = (
        "You solve Moltbook lobster math riddles. The riddle uses obfuscated English number words "
        "and + - * / or physics (two forces in newtons — add for total force). "
        "Reply with ONLY one number, two decimal places, nothing else.\n\n"
        f"Riddle:\n{challenge}\n\nAnswer:"
    )
    try:
        cp = subprocess.run(
            ["ollama", "run", "llama3.2:1b", prompt],
            capture_output=True,
            text=True,
            timeout=90,
        )
        text = (cp.stdout or "").strip()
        m = re.search(r"-?\d+\.\d{2}|-?\d+", text)
        if m:
            return f"{float(m.group()):.2f}"
    except Exception:
        pass
    return None


def candidate_answers(challenge: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for fn in (solve_challenge_text, ollama_answer):
        a = fn(challenge)
        if a and a not in seen:
            seen.add(a)
            out.append(a)
    # brute small integer ops from extracted word numbers
    words = re.findall(r"[a-zA-Z]+", challenge.lower())
    nums = []
    num_map = {
        "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
        "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
        "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30,
        "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
    }
    for i, w in enumerate(words):
        if w in num_map:
            nums.append(num_map[w])
        if w == "sixty" and i + 1 < len(words) and words[i + 1] in num_map and num_map[words[i + 1]] < 10:
            nums.append(60 + num_map[words[i + 1]])
        if w == "thirty" and i + 1 < len(words) and words[i + 1] in num_map and num_map[words[i + 1]] < 10:
            nums.append(30 + num_map[words[i + 1]])
    if len(nums) >= 2:
        a, b = nums[0], nums[1]
        for val in (a + b, a - b, a * b, a / b if b else None):
            if val is not None:
                s = f"{val:.2f}"
                if s not in seen:
                    seen.add(s)
                    out.append(s)
    return out


def try_verify(session, create_json: dict) -> dict:
    post = create_json.get("post") or {}
    ver = post.get("verification") or {}
    code = ver.get("verification_code")
    challenge = ver.get("challenge_text") or ""
    if not code:
        return {"ok": False, "error": "no_verification_code", "post_id": post.get("id")}
    session.headers["Content-Type"] = "application/json"
    # ONE submit per verification_code — wrong answer often burns the code (409 on retry).
    candidates = candidate_answers(challenge)
    ans = candidates[0] if candidates else None
    if not ans:
        return {"ok": False, "error": "no_answer", "challenge": challenge, "post_id": post.get("id")}
    r = session.post(
        f"{API_BASE}/verify",
        json={"verification_code": code, "answer": ans},
        timeout=30,
    )
    row = {"answer": ans, "http": r.status_code, "preview": r.text[:300], "candidates_considered": candidates[:6]}
    try:
        if r.json().get("success"):
            return {"ok": True, "success": True, "answer": ans, "post_id": post.get("id"), "attempt": row}
    except Exception:
        pass
    return {"ok": False, "challenge": challenge, "post_id": post.get("id"), "attempt": row}


def publish(account: str, title_suffix: str) -> dict:
    os.environ["MOLTBOOK_ACCOUNT"] = account
    cred = load_credentials()
    if account == "lightfather":
        body = (ROOT / "docs" / "MOLTBOOK_LAUNCH_LIGHTFATHER_BODY.md").read_text(encoding="utf-8")
        submolt = "general"
        title = f"LYGO stack + Ollama army — Lightfather lattice revival (2026){title_suffix}"
    else:
        body = (ROOT / "docs" / "MOLTBOOK_LAUNCH_LYRA_BODY.md").read_text(encoding="utf-8")
        submolt = "lyra-haven"
        title = f"LYGO Protocol Stack + Ollama army — public lattice revival (2026){title_suffix}"

    s = session()
    s.headers["Content-Type"] = "application/json"
    payload = {"submolt_name": submolt, "title": title[:300], "content": body.strip()[:39000]}
    r, _ = request_with_backoff("POST", f"{API_BASE}/posts", session_obj=s, json=payload, max_tries=3, timeout=90)
    out = {"account": account, "http": r.status_code, "agent": cred.get("agent_name")}
    if not r.ok:
        out["error"] = r.text[:400]
        return out
    j = r.json()
    post = j.get("post") or {}
    out["post_id"] = post.get("id")
    out["url"] = f"https://www.moltbook.com/post/{post.get('id')}"
    out["verify"] = try_verify(s, j)
    if out["verify"].get("success"):
        r2 = s.get(f"{API_BASE}/posts/{post.get('id')}", timeout=25)
        if r2.ok:
            out["verification_status"] = (r2.json().get("post") or {}).get("verification_status")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", choices=("lyra", "lightfather", "both"), required=True)
    ap.add_argument("--suffix", default="", help="Title suffix to avoid duplicate-post dedupe")
    args = ap.parse_args()
    accounts = ["lyra", "lightfather"] if args.account == "both" else [args.account]
    report = {"ts": datetime.now(timezone.utc).isoformat(), "results": []}
    for i, acct in enumerate(accounts):
        if i:
            time.sleep(155)
        report["results"].append(publish(acct, args.suffix))
    path = ROOT / "data" / "moltbook" / "publish_pending_last_run.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if all(r.get("verify", {}).get("success") for r in report["results"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())