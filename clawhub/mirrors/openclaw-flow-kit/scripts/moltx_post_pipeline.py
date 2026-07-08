#!/usr/bin/env python3
"""MoltX post pipeline wrapper.

Pipeline:
1) Engage-gate preflight (read feeds + like/repost)
2) Attempt post (delegates to moltx-streamliner post.py)
3) If blocked (429 engage gate), re-engage, backoff, retry
4) Write a receipt JSON file (tmp/receipts/moltx/...) with artifacts

Usage:
  python scripts/moltx_post_pipeline.py --text-file <path> [--random-seal] [--max-attempts 3]

Exit codes:
  0 = posted
  2 = could not post
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from ws_paths import find_workspace_root

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def run_json(cmd: list[str], timeout: int = 180) -> dict:
    cp = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    # Prefer stdout JSON; fall back to stderr.
    txt = (cp.stdout or "").strip() or (cp.stderr or "").strip()
    try:
        obj = json.loads(txt)
    except Exception:
        obj = {"raw": txt, "exit_code": cp.returncode}
    obj.setdefault("exit_code", cp.returncode)
    return obj


def write_receipt(ws: Path, payload: dict) -> Path:
    out_dir = ws / "tmp" / "receipts" / "moltx"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    path = out_dir / f"moltx_post_{stamp}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--text-file", required=True)
    ap.add_argument("--random-seal", action="store_true")
    ap.add_argument("--max-attempts", type=int, default=3)
    ap.add_argument("--base-backoff", type=float, default=2.0)
    ap.add_argument("--no-engage", action="store_true", help="Skip engage-gate step (not recommended)")
    args = ap.parse_args()

    ws = find_workspace_root(__file__)

    engage_script = ws / "skills" / "public" / "openclaw-flow-kit" / "scripts" / "moltx_engage_gate.py"
    post_script = ws / "skills" / "moltx-streamliner" / "scripts" / "post.py"

    if not post_script.exists():
        out = {"ok": False, "error": "moltx-streamliner not installed", "expected": str(post_script)}
        receipt = write_receipt(ws, out)
        print(json.dumps({**out, "receipt": str(receipt)}, ensure_ascii=False, indent=2))
        return 2

    attempts = []
    for i in range(1, args.max_attempts + 1):
        step = {"attempt": i}

        if not args.no_engage:
            step["engage"] = run_json([sys.executable, str(engage_script), "--mode", "minimal"]) 

        post_cmd = [sys.executable, str(post_script), "--no-engage", "--text-file", str(Path(args.text_file).resolve())]
        if args.random_seal:
            post_cmd.append("--random-seal")

        post_res = run_json(post_cmd)
        step["post"] = post_res
        attempts.append(step)

        post_ok = bool(post_res.get("post_ok") is True)
        if post_ok:
            out = {
                "ok": True,
                "post_id": post_res.get("post_id"),
                "media_url": post_res.get("media_url"),
                "seal_path": post_res.get("seal_path"),
                "attempts": attempts,
            }
            receipt = write_receipt(ws, out)
            out["receipt"] = str(receipt)
            print(json.dumps(out, ensure_ascii=False, indent=2))
            return 0

        # Retry classification
        code = post_res.get("post_code")
        body = (post_res.get("post_body_preview") or "")
        retryable = (code == 429) and ("Engage before posting" in body or "rate" in body.lower())
        step["retryable"] = retryable

        if not retryable or i == args.max_attempts:
            break

        # backoff
        sleep_s = min(30.0, args.base_backoff * (2 ** (i - 1)))
        step["backoffSeconds"] = sleep_s
        time.sleep(sleep_s)

    out = {"ok": False, "error": "post_failed", "attempts": attempts}
    receipt = write_receipt(ws, out)
    out["receipt"] = str(receipt)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
