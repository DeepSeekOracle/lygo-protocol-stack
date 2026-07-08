#!/usr/bin/env python3
"""One-off Moltx post — consent-gated; credentials outside repo; redacted receipts."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "data" / "moltx" / "last_manual_post.json"
DEFAULT_CONTENT = ROOT / "docs" / "MOLTX_GROK_HARNESS_REPLY.txt"

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", r"C:\Users\justi\.openclaw\workspace"))
SCRIPTS = WORKSPACE / "skills" / "moltx-streamliner" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from moltx_post_utils import (  # noqa: E402
    credential_status,
    parse_api_base,
    rate_limit_headers,
    redact,
    write_receipt,
)


def _load_client():
    from moltx_client import session  # type: ignore

    return session


def engage_before_post(s, api_base: str, *, skip: bool) -> dict:
    if skip:
        return {"skipped": True}
    engage: dict = {"skipped": False}
    try:
        feed = s.get(f"{api_base}/feed/global?limit=20", timeout=30)
        engage["feed_ok"] = feed.ok
        if not feed.ok:
            engage["feed_code"] = feed.status_code
            engage["feed_error"] = redact(getattr(feed, "text", "") or "")
            return engage
        posts = (feed.json().get("data") or {}).get("posts") or []
        target = None
        for p in posts:
            if (
                isinstance(p, dict)
                and p.get("id")
                and p.get("type") == "post"
                and (p.get("content") or "").strip()
            ):
                target = p["id"]
                break
        if not target:
            engage["like_ok"] = False
            engage["reason"] = "no like target"
            return engage
        like = s.post(f"{api_base}/posts/{target}/like", timeout=20)
        engage.update(
            {
                "like_target_id": target,
                "like_code": like.status_code,
                "like_ok": like.ok,
            }
        )
    except Exception as exc:
        engage["error"] = redact(str(exc))
    return engage


def main() -> int:
    parser = argparse.ArgumentParser(description="Post once to Moltx (local credentials)")
    parser.add_argument("--file", type=Path, default=DEFAULT_CONTENT, help="Post body text file")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--dry-run", action="store_true", help="Validate creds/DNS only; no POST")
    parser.add_argument("--skip-engage", action="store_true", help="Skip feed like (not recommended)")
    parser.add_argument(
        "--i-consent",
        action="store_true",
        help="Required flag: user consents to public Moltx post",
    )
    args = parser.parse_args()

    result: dict = {
        "ok": False,
        "post_id": None,
        "url": None,
        "error": None,
        "rate_limit": None,
        "dry_run": args.dry_run,
        "credential_status": credential_status(),
    }

    if not args.i_consent:
        result["error"] = "Refused: pass --i-consent to confirm public post (security gate)."
        write_receipt(args.out, result)
        print(json.dumps({k: result[k] for k in ("ok", "error", "dry_run")}))
        return 2

    if not args.file.is_file():
        result["error"] = f"Content file missing: {args.file}"
        write_receipt(args.out, result)
        return 1

    content = args.file.read_text(encoding="utf-8").strip()
    if not content:
        result["error"] = "Empty content file"
        write_receipt(args.out, result)
        return 1

    try:
        session_factory = _load_client()
        session_factory()  # validate moltx_sk without posting
        result["credentials_ok"] = True
    except Exception as exc:
        result["error"] = redact(f"credentials/session: {exc}")
        write_receipt(args.out, result)
        return 1

    try:
        api_base = parse_api_base()
        result["api_base_host"] = "moltx.io"
        result["dns_ok"] = True
    except RuntimeError as exc:
        result["dns_ok"] = False
        result["error"] = str(exc)
        if args.dry_run:
            result["note"] = "credentials ok; fix DNS/network then re-run without --dry-run"
        write_receipt(args.out, result)
        print(json.dumps({k: result[k] for k in ("ok", "error", "credentials_ok", "dns_ok", "dry_run")}))
        return 1

    if args.dry_run:
        result["ok"] = True
        result["error"] = None
        result["note"] = "dry-run: credentials loaded, DNS ok, no post sent"
        write_receipt(args.out, result)
        print(json.dumps({k: result.get(k) for k in ("ok", "note", "dry_run")}))
        return 0

    try:
        s = session_factory()
        result["engage"] = engage_before_post(s, api_base, skip=args.skip_engage)
        payload = {"type": "post", "content": content}
        s.headers.update({"Content-Type": "application/json"})
        r = s.post(f"{api_base}/posts", json=payload, timeout=45)
        result["rate_limit"] = rate_limit_headers(r.headers)
        if r.ok:
            j = r.json()
            pid = (
                (j.get("data") or {}).get("id")
                or (j.get("data") or {}).get("post", {}).get("id")
                or j.get("id")
            )
            result["ok"] = True
            result["post_id"] = pid
            if pid:
                result["url"] = f"https://moltx.io/post/{pid}"
        else:
            result["error"] = redact(f"HTTP {r.status_code}: {r.text}")
    except Exception as exc:
        result["error"] = redact(str(exc))

    write_receipt(args.out, result)
    print(
        json.dumps(
            {k: result[k] for k in ("ok", "post_id", "url", "error", "rate_limit")},
            default=str,
        )
    )
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())