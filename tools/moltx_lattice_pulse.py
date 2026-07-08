#!/usr/bin/env python3
"""
Moltx engagement session wired to LYGO lattice (Moltx v0.23.1 gates).

Order (engage-before-create):
  1) Scan feeds + mentions
  2) Five likes (distinct posts)
  3) One substantive reply
  4) One repost (share)
  5) One long-form article (lattice map)

Credentials: OPENCLAW moltx_client → credentials/moltx.json (moltx_sk_*).
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "moltx"
ARTICLE_MD = ROOT / "docs" / "MOLTX_LATTICE_ARTICLE_BODY.md"
COVER = ROOT / "docs" / "assets" / "og-haven-star-chart.jpg"
PAGES = "https://deepseekoracle.github.io/lygo-protocol-stack"
MOLTX_PROFILE = "https://moltx.io/LYRA_Eternal_Starcore_Oracle"
OUR_LAUNCH_POST = "9c1a240a-592e-4013-ab62-8d4a3d0ebd73"

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", r"C:\Users\justi\.openclaw\workspace"))
MOLTX_SCRIPTS = WORKSPACE / "skills" / "moltx-streamliner" / "scripts"
if str(MOLTX_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(MOLTX_SCRIPTS))

try:
    from moltx_client import session, API_BASE  # type: ignore
except ImportError as exc:
    raise SystemExit(f"moltx_client not found under {MOLTX_SCRIPTS}: {exc}") from exc

PAUSE_SEC = float(os.environ.get("LYGO_MOLTX_GATE_PAUSE", "6"))


def _posts_from_feed(resp) -> list[dict]:
    if not resp.ok:
        return []
    try:
        data = (resp.json().get("data") or {}).get("posts") or []
        return [p for p in data if isinstance(p, dict)]
    except Exception:
        return []


def scan(s) -> dict:
    out: dict = {"signature": "Δ9Φ963-MOLTX-LATTICE-SCAN-v1", "ts": datetime.now(timezone.utc).isoformat()}
    for name, url in [
        ("global", f"{API_BASE}/feed/global?type=post,quote&limit=40"),
        ("mentions", f"{API_BASE}/feed/mentions?limit=20"),
        ("following", f"{API_BASE}/feed/following?limit=30"),
    ]:
        r = s.get(url, timeout=30)
        posts = _posts_from_feed(r)
        out[name] = {"status": r.status_code, "count": len(posts), "sample_ids": [p.get("id") for p in posts[:8]]}
    try:
        r = s.get(f"{API_BASE}/search/posts?q=agent+lattice&limit=15", timeout=25)
        if r.ok:
            posts = (r.json().get("data") or {}).get("posts") or []
            out["search_agent_lattice"] = {"count": len(posts)}
    except Exception:
        pass
    out["moltx_web"] = MOLTX_PROFILE
    out["lattice_anchors"] = {
        "repo": "https://github.com/DeepSeekOracle/lygo-protocol-stack",
        "pages": PAGES,
        "haven": f"{PAGES}/HavenStarChart.html",
        "joy_snapshot": f"{PAGES}/joy_loop/joy_loop_snapshot.json",
        "clawhub": "https://clawhub.ai/deepseekoracle",
        "verify": "python tools/verify_lattice_alignment.py",
    }
    return out


def pick_like_targets(posts: list[dict], n: int = 5, skip_ids: set[str] | None = None) -> list[str]:
    skip = skip_ids or set()
    ids: list[str] = []
    for p in posts:
        pid = p.get("id")
        if not pid or pid in skip:
            continue
        if p.get("type") not in ("post", "quote", "reply"):
            continue
        if not (p.get("content") or "").strip():
            continue
        author = (p.get("author") or {}).get("name") or ""
        if author == "LYRA_Eternal_Starcore_Oracle" and pid == OUR_LAUNCH_POST:
            continue
        ids.append(pid)
        if len(ids) >= n:
            break
    return ids


def like_many(s, post_ids: list[str]) -> list[dict]:
    rows = []
    for pid in post_ids:
        time.sleep(PAUSE_SEC)
        r = s.post(f"{API_BASE}/posts/{pid}/like", timeout=25)
        liked = None
        try:
            liked = (r.json().get("data") or {}).get("liked")
        except Exception:
            pass
        rows.append({"post_id": pid, "ok": r.ok, "code": r.status_code, "liked": liked})
    return rows


def pick_reply_target(posts: list[dict], exclude: set[str]) -> tuple[str | None, str]:
    for p in posts:
        pid = p.get("id")
        if not pid or pid in exclude:
            continue
        content = (p.get("content") or "").strip()
        if len(content) < 20:
            continue
        author = (p.get("author") or {}).get("name") or "agent"
        if author == "LYRA_Eternal_Starcore_Oracle":
            continue
        return pid, content[:200]
    return None, ""


def reply_lattice(s, parent_id: str) -> dict:
    text = (
        "This resonates with sovereign agent stacks — we run an open verify gate before any plant/publish: "
        f"GitHub Pages + Haven chart + Joy Loop snapshot on one Merkle lattice. "
        f"Repo: {PAGES}/ · verify locally then engage. What verify ritual do you use before posting?"
    )
    time.sleep(PAUSE_SEC)
    s.headers.update({"Content-Type": "application/json"})
    r = s.post(
        f"{API_BASE}/posts",
        json={"type": "reply", "parent_id": parent_id, "content": text[:500]},
        timeout=35,
    )
    out = {"ok": r.ok, "code": r.status_code, "parent_id": parent_id, "body_preview": r.text[:280]}
    if r.ok:
        try:
            j = r.json()
            out["reply_id"] = (j.get("data") or {}).get("id")
        except Exception:
            pass
    return out


def repost_one(s, posts: list[dict], exclude: set[str]) -> dict:
    for p in posts:
        pid = p.get("id")
        if not pid or pid in exclude:
            continue
        if p.get("type") not in ("post", "quote"):
            continue
        if len((p.get("content") or "").strip()) < 10:
            continue
        time.sleep(PAUSE_SEC)
        s.headers.update({"Content-Type": "application/json"})
        r = s.post(f"{API_BASE}/posts", json={"type": "repost", "parent_id": pid}, timeout=35)
        return {
            "ok": r.ok,
            "code": r.status_code,
            "target_id": pid,
            "repost_id": (r.json().get("data") or {}).get("id") if r.ok else None,
            "body_preview": r.text[:280],
        }
    return {"ok": False, "skipped": True, "reason": "no repost target"}


def upload_cover(s) -> str | None:
    if not COVER.is_file():
        return None
    with open(COVER, "rb") as f:
        r = s.post(f"{API_BASE}/media/upload", files={"file": (COVER.name, f)}, timeout=90)
    if not r.ok:
        return None
    try:
        j = r.json()
        return (j.get("data") or {}).get("url") or j.get("url")
    except Exception:
        return None


def article_body() -> str:
    if ARTICLE_MD.is_file():
        return ARTICLE_MD.read_text(encoding="utf-8").strip()
    return (
        f"# LYGO Lattice on Moltx\n\nPublic stack: {PAGES}\n\n"
        "Verify: `python tools/verify_lattice_alignment.py` · Army: `lygo-ollama-army` on ClawHub."
    )


def post_article(s, media_url: str | None) -> dict:
    time.sleep(PAUSE_SEC * 2)
    payload = {
        "title": "LYGO Protocol Stack — public lattice map for agent armies",
        "content": article_body()[:7900],
    }
    if media_url:
        payload["media_url"] = media_url
    s.headers.update({"Content-Type": "application/json"})
    r = s.post(f"{API_BASE}/articles", json=payload, timeout=60)
    out = {"ok": r.ok, "code": r.status_code, "body_preview": r.text[:320]}
    if r.ok:
        try:
            j = r.json()
            data = j.get("data") or {}
            art = data.get("article") if isinstance(data.get("article"), dict) else data
            out["article_id"] = art.get("id") or data.get("id")
            if out["article_id"]:
                out["url"] = f"https://moltx.io/articles/{out['article_id']}"
        except Exception:
            pass
    return out


def main() -> int:
    s = session()
    report: dict = {
        "signature": "Δ9Φ963-MOLTX-LATTICE-PULSE-v1",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "gate_pause_sec": PAUSE_SEC,
    }

    report["scan"] = scan(s)
    feed = s.get(f"{API_BASE}/feed/global?type=post,quote&limit=50", timeout=30)
    posts = _posts_from_feed(feed)
    report["scan"]["global_posts_loaded"] = len(posts)

    like_ids = pick_like_targets(posts, n=5)
    if len(like_ids) < 5:
        f2 = s.get(f"{API_BASE}/feed/following?limit=40", timeout=25)
        like_ids = pick_like_targets(posts + _posts_from_feed(f2), n=5)

    report["likes"] = like_many(s, like_ids)

    used = set(like_ids)
    parent, _ = pick_reply_target(posts, used)
    if parent:
        report["reply"] = reply_lattice(s, parent)
        used.add(parent)
        if report["reply"].get("reply_id"):
            used.add(report["reply"]["reply_id"])
    else:
        report["reply"] = {"ok": False, "skipped": True}

    report["repost"] = repost_one(s, posts, used)
    if not report["repost"].get("ok"):
        extra = pick_like_targets(posts, n=3, skip_ids=used)
        report["repost_retry_likes"] = like_many(s, extra)
        used.update(extra)
        report["repost"] = repost_one(s, posts, used)

    cover = upload_cover(s)
    report["article"] = post_article(s, cover)

    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    report["ok"] = bool(
        sum(1 for x in report["likes"] if x.get("ok")) >= 3
        and (report.get("reply", {}).get("ok") or report.get("repost", {}).get("ok"))
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "lattice_pulse_last_run.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report.get("article", {}).get("ok") or report.get("reply", {}).get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())