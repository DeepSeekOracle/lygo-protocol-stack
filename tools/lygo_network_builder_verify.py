#!/usr/bin/env python3
"""LYGO Network Builder — deterministic anchor verification (Biophase7 bulletproof)."""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
ANCHORS_PATH = REPO / "docs" / "network_builder" / "IMMUTABLE_ANCHORS.json"
OUT_PATH = REPO / "tests" / "network_builder_last_run.json"


def _canonical_anchor_digest(data: dict) -> str:
    blob = json.dumps(data.get("immutable_anchors", {}), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _probe(url: str, timeout: float = 22.0) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "LYGO-Network-Builder/1.2"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(65536)
            text = body.decode("utf-8", errors="replace")
            return {
                "url": url,
                "status": resp.status,
                "ok": 200 <= resp.status < 400,
                "bytes": len(body),
                "body_sample": text[:200],
            }
    except urllib.error.HTTPError as e:
        return {"url": url, "status": e.code, "ok": False, "error": str(e)}
    except Exception as e:
        return {"url": url, "status": None, "ok": False, "error": str(e)}


def _collect_anchors(data: dict) -> list[dict]:
    out: list[dict] = []
    imm = data.get("immutable_anchors") or {}
    for group, items in imm.items():
        for item in items:
            row = dict(item)
            row["group"] = group
            out.append(row)
    return out


def main() -> int:
    if not ANCHORS_PATH.is_file():
        print(f"MISSING {ANCHORS_PATH}")
        return 2

    data = json.loads(ANCHORS_PATH.read_text(encoding="utf-8"))
    t0 = time.perf_counter()
    results: list[dict] = []
    required_fail = 0
    soft_fail = 0

    for anchor in _collect_anchors(data):
        mode = anchor.get("verify", "link_only")
        aid = anchor.get("id", "?")
        row: dict[str, Any] = {"id": aid, "group": anchor.get("group"), "mode": mode}

        if mode == "local_repo":
            rel = anchor.get("repo_path", "")
            path = REPO / rel
            row["path"] = str(path)
            row["ok"] = path.is_file()
            if not row["ok"]:
                required_fail += 1
        elif mode == "link_only":
            row["url"] = anchor.get("url")
            row["ok"] = True
            row["note"] = "immutable link; no automated probe (vault TOS)"
        elif mode in ("http_required", "http_soft"):
            url = anchor.get("url", "")
            probe = _probe(url)
            row.update(probe)
            subs = anchor.get("expect_substrings") or []
            if row.get("ok") and subs:
                sample = (probe.get("body_sample") or "").lower()
                if not all(s.lower() in sample for s in subs):
                    row["ok"] = False
                    row["substring_miss"] = subs
            if not row.get("ok"):
                if mode == "http_required":
                    required_fail += 1
                else:
                    soft_fail += 1
        else:
            row["ok"] = False
            row["error"] = f"unknown verify mode {mode}"
            required_fail += 1

        results.append(row)

    all_pass = required_fail == 0
    report = {
        "signature": data.get("signature", "Δ9Φ963-NETWORK-BUILDER-VERIFY"),
        "skill_slug": data.get("skill_slug"),
        "anchors_sha256": _canonical_anchor_digest(data),
        "anchors_version": data.get("version"),
        "vectors": results,
        "required_failures": required_fail,
        "soft_failures": soft_fail,
        "all_pass": all_pass,
        "verdict": "LATTICE ALIGNED" if all_pass else "NEEDS_FIX",
        "duration_ms": int((time.perf_counter() - t0) * 1000),
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())