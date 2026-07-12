#!/usr/bin/env python3
"""Immutable append-only feed ledger for Haven Star Chart agent submissions."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "haven_star_chart" / "feed_ledger.jsonl"
OUT_FEED = ROOT / "docs" / "haven_star_chart" / "haven_star_chart_feed.json"
SIGNATURE = "Δ9Φ963-HAVEN-STAR-FEED-v1"
GENESIS_PREV = "0" * 64


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_entry_body(entry: dict[str, Any]) -> bytes:
    body = {k: v for k, v in entry.items() if k not in ("entry_hash", "prev_hash")}
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")


def entry_hash(entry: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_entry_body(entry)).hexdigest()


def read_ledger() -> list[dict[str, Any]]:
    if not LEDGER.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def verify_chain(rows: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    prev = GENESIS_PREV
    for i, row in enumerate(rows):
        if row.get("prev_hash") != prev:
            errors.append(f"chain_break:seq={row.get('seq', i + 1)}")
        expected = entry_hash(row)
        if row.get("entry_hash") != expected:
            errors.append(f"hash_mismatch:seq={row.get('seq', i + 1)}")
        prev = row.get("entry_hash") or prev
    return len(errors) == 0, errors


def append_event(
    event_type: str,
    status: str,
    *,
    agent_id: str = "",
    skill_slug: str = "",
    node_id: str = "",
    node_name: str = "",
    kind: str = "",
    verdict: str = "",
    errors: list[str] | None = None,
    content_sha256: str = "",
    source_file: str = "",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append one immutable ledger line. Returns the new entry."""
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    rows = read_ledger()
    seq = len(rows) + 1
    prev = rows[-1]["entry_hash"] if rows else GENESIS_PREV
    entry: dict[str, Any] = {
        "signature": SIGNATURE,
        "seq": seq,
        "event_utc": utc_now(),
        "event_type": event_type,
        "status": status,
        "agent_id": agent_id,
        "skill_slug": skill_slug,
        "node_id": node_id,
        "node_name": node_name,
        "kind": kind,
        "verdict": verdict,
        "errors": errors or [],
        "content_sha256": content_sha256,
        "source_file": source_file,
        "prev_hash": prev,
    }
    if extra:
        entry["extra"] = extra
    entry["entry_hash"] = entry_hash(entry)
    with LEDGER.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, separators=(",", ":")) + "\n")
    return entry


def _submission_fields(sub: dict[str, Any]) -> dict[str, str]:
    node = sub.get("node") or sub
    att = sub.get("agent_attestation") or {}
    return {
        "agent_id": str(att.get("agent_id") or ""),
        "skill_slug": str(att.get("skill_slug") or ""),
        "node_id": str(node.get("id") or ""),
        "node_name": str(node.get("name") or ""),
        "kind": str(node.get("kind") or ""),
        "content_sha256": str(sub.get("content_sha256") or att.get("content_sha256") or ""),
    }


def log_gate_reject(sub: dict[str, Any] | None, gate: dict[str, Any], source_file: str = "") -> dict[str, Any]:
    fields = _submission_fields(sub or {})
    return append_event(
        "gate_reject",
        "REJECTED",
        verdict="REJECT",
        errors=gate.get("errors") or [],
        source_file=source_file,
        **fields,
    )


def log_submit_pending(sub: dict[str, Any], gate: dict[str, Any], source_file: str) -> dict[str, Any]:
    fields = _submission_fields(sub)
    return append_event(
        "submit_pending",
        "PENDING",
        verdict="ACCEPT",
        source_file=source_file,
        extra={"math_score": (gate.get("math_resonance") or {}).get("score")},
        **fields,
    )


def log_ingest_accepted(sub: dict[str, Any], source_file: str) -> dict[str, Any]:
    fields = _submission_fields(sub)
    return append_event(
        "ingest_accepted",
        "ACCEPTED",
        verdict="ACCEPT",
        source_file=source_file,
        **fields,
    )


def log_ingest_rejected(sub: dict[str, Any] | None, gate: dict[str, Any], source_file: str) -> dict[str, Any]:
    fields = _submission_fields(sub or {})
    return append_event(
        "ingest_rejected",
        "REJECTED",
        verdict="REJECT",
        errors=gate.get("errors") or ["invalid_json"],
        source_file=source_file,
        **fields,
    )


def backfill_from_submissions() -> int:
    """One-time backfill when ledger is empty — from on-disk submission folders."""
    if read_ledger():
        return 0
    count = 0
    base = ROOT / "data" / "haven_star_chart" / "submissions"
    for folder, event_type, status in (
        ("accepted", "ingest_accepted", "ACCEPTED"),
        ("rejected", "ingest_rejected", "REJECTED"),
        ("pending", "submit_pending", "PENDING"),
    ):
        d = base / folder
        if not d.is_dir():
            continue
        for path in sorted(d.glob("*.json")):
            try:
                sub = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            gate = sub.get("gate_result") or sub.get("ingest_reject") or {}
            fields = _submission_fields(sub)
            append_event(
                event_type,
                status,
                verdict=gate.get("verdict") or ("ACCEPT" if status == "ACCEPTED" else status),
                errors=gate.get("errors") or [],
                source_file=path.name,
                **fields,
            )
            count += 1
    return count


def publish_feed() -> dict[str, Any]:
    """Verify ledger chain and write public feed JSON for Pages."""
    backfill_from_submissions()
    rows = read_ledger()
    ok, chain_errors = verify_chain(rows)
    chain_root = rows[-1]["entry_hash"] if rows else GENESIS_PREV
    ledger_sha = hashlib.sha256(LEDGER.read_bytes()).hexdigest() if LEDGER.is_file() else GENESIS_PREV
    feed = {
        "signature": SIGNATURE,
        "updated_utc": utc_now(),
        "ledger_path": "data/haven_star_chart/feed_ledger.jsonl",
        "ledger_sha256": ledger_sha,
        "chain_root": chain_root,
        "chain_valid": ok,
        "chain_errors": chain_errors,
        "entry_count": len(rows),
        "entries": list(reversed(rows)),
    }
    OUT_FEED.parent.mkdir(parents=True, exist_ok=True)
    OUT_FEED.write_text(json.dumps(feed, indent=2), encoding="utf-8")
    return feed


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Haven Star Chart immutable feed")
    ap.add_argument("--publish", action="store_true", help="Publish feed JSON from ledger")
    ap.add_argument("--verify", action="store_true", help="Verify ledger chain only")
    ap.add_argument("--backfill", action="store_true", help="Backfill ledger from submission folders")
    args = ap.parse_args()

    if args.backfill:
        n = backfill_from_submissions()
        print(json.dumps({"backfilled": n}))
    if args.verify:
        rows = read_ledger()
        ok, errs = verify_chain(rows)
        print(json.dumps({"chain_valid": ok, "entries": len(rows), "errors": errs}, indent=2))
        return 0 if ok else 1
    if args.publish or not any((args.backfill, args.verify)):
        feed = publish_feed()
        print(
            json.dumps(
                {
                    "ok": True,
                    "entries": feed["entry_count"],
                    "chain_valid": feed["chain_valid"],
                    "out": str(OUT_FEED),
                },
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())