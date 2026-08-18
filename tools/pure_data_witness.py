#!/usr/bin/env python3
"""LYGO Pure-Data Witness (Phase A) — digest / fetch / ledger.

Seal-first purity: prove bytes at time T without replacing Wayback.
No secrets. Size-capped fetch. Stdlib only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SIG = "Delta9Phi963-PURE-DATA-WITNESS-v1"
MAX_FETCH = 256 * 1024  # 256 KiB public snapshot cap
UA = "LYGO-PureDataWitness/1.0 (+https://deepseekoracle.github.io/lygo-protocol-stack/)"

SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|secret|password|token|bearer|moltbook_sk_|moltx_sk_|nvapi-|ghp_|github_pat_)[=:\s]+\S+"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def redact_text(s: str) -> str:
    return SECRET_RE.sub("[REDACTED]", s)


def witness_id(content_sha: str, captured: str) -> str:
    raw = f"{content_sha}:{captured}".encode()
    return "PDW-" + hashlib.sha256(raw).hexdigest()[:12].upper()


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def digest_file(path: Path, out_dir: Path, source_url: str | None = None) -> dict:
    data = path.read_bytes()
    captured = utc_now()
    digest = sha256_bytes(data)
    wid = witness_id(digest, captured)
    card = {
        "signature": SIG,
        "witness_id": wid,
        "captured_utc": captured,
        "source_url": source_url,
        "source_path_hint": path.name,
        "content_sha256": digest,
        "bytes": len(data),
        "content_type": "application/octet-stream",
        "method": "local_file",
        "fetch_status": None,
        "snapshot_saved": False,
        "mirrors": [],
        "notes": "Phase A digest witness — pure bytes, no fabrication.",
    }
    # optional text snapshot if small-ish utf8
    snap_path = out_dir / f"{wid}.bin"
    if len(data) <= MAX_FETCH:
        snap_path.write_bytes(data)
        card["snapshot_saved"] = True
        card["snapshot_file"] = snap_path.name
        try:
            text = data.decode("utf-8")
            card["content_type"] = "text/plain; charset=utf-8"
            (out_dir / f"{wid}.txt").write_text(redact_text(text), encoding="utf-8")
            card["snapshot_txt"] = f"{wid}.txt"
        except UnicodeDecodeError:
            pass
    write_json(out_dir / f"{wid}.json", card)
    return card


def fetch_url(url: str, out_dir: Path) -> dict:
    if not url.startswith("https://"):
        raise SystemExit("Only https:// URLs allowed in Phase A")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    captured = utc_now()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            status = resp.status
            ctype = resp.headers.get("Content-Type", "application/octet-stream")
            data = resp.read(MAX_FETCH + 1)
    except urllib.error.HTTPError as e:
        status = e.code
        ctype = "text/plain"
        data = (e.read(MAX_FETCH) if hasattr(e, "read") else str(e).encode())[:MAX_FETCH]
    except Exception as e:
        raise SystemExit(f"fetch failed: {e}") from e

    truncated = len(data) > MAX_FETCH
    if truncated:
        data = data[:MAX_FETCH]

    digest = sha256_bytes(data)
    wid = witness_id(digest, captured)
    card = {
        "signature": SIG,
        "witness_id": wid,
        "captured_utc": captured,
        "source_url": url,
        "content_sha256": digest,
        "bytes": len(data),
        "content_type": ctype,
        "method": "https_get",
        "fetch_status": status,
        "truncated": truncated,
        "max_fetch_bytes": MAX_FETCH,
        "snapshot_saved": True,
        "snapshot_file": f"{wid}.bin",
        "mirrors": [],
        "notes": "Phase A URL witness — digest is authority; snapshot may be truncated.",
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{wid}.bin").write_bytes(data)
    try:
        text = data.decode("utf-8", errors="replace")
        (out_dir / f"{wid}.txt").write_text(redact_text(text), encoding="utf-8")
        card["snapshot_txt"] = f"{wid}.txt"
    except Exception:
        pass
    write_json(out_dir / f"{wid}.json", card)
    return card


def rebuild_ledger(witness_dir: Path, ledger_path: Path) -> dict:
    rows = []
    for p in sorted(witness_dir.glob("PDW-*.json")):
        try:
            rows.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            continue
    # Merkle-ish root over sorted witness digests
    joined = "\n".join(sorted(r.get("content_sha256", "") for r in rows)).encode()
    root = sha256_bytes(joined) if rows else sha256_bytes(b"")
    ledger = {
        "signature": SIG + "-LEDGER",
        "updated_utc": utc_now(),
        "count": len(rows),
        "merkle_style_root": root,
        "note": "Public digest ledger. Snapshots may live beside cards; digests are enough to refuse rewrites.",
        "witnesses": [
            {
                "witness_id": r.get("witness_id"),
                "captured_utc": r.get("captured_utc"),
                "source_url": r.get("source_url"),
                "content_sha256": r.get("content_sha256"),
                "bytes": r.get("bytes"),
                "fetch_status": r.get("fetch_status"),
                "truncated": r.get("truncated"),
            }
            for r in rows
        ],
    }
    write_json(ledger_path, ledger)
    return ledger


def verify_card(card_path: Path) -> dict:
    card = json.loads(card_path.read_text(encoding="utf-8"))
    snap = card_path.parent / card.get("snapshot_file", "")
    out = {"witness_id": card.get("witness_id"), "ok": False}
    if not snap.is_file():
        out["error"] = "snapshot missing — digest-only verify needs bytes"
        return out
    data = snap.read_bytes()
    got = sha256_bytes(data)
    out["expected"] = card.get("content_sha256")
    out["observed"] = got
    out["ok"] = got == card.get("content_sha256")
    out["bytes"] = len(data)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="LYGO Pure-Data Witness Phase A")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("digest", help="Digest a local file")
    p1.add_argument("--file", required=True)
    p1.add_argument("--url", help="Optional source URL label")
    p1.add_argument("--out", default="data/pure_data")

    p2 = sub.add_parser("fetch", help="HTTPS GET + digest (size-capped)")
    p2.add_argument("--url", required=True)
    p2.add_argument("--out", default="data/pure_data")

    p3 = sub.add_parser("ledger", help="Rebuild public ledger JSON")
    p3.add_argument("--dir", default="data/pure_data")
    p3.add_argument("--ledger", default="docs/pure-data/ledger.json")

    p4 = sub.add_parser("verify", help="Re-hash snapshot vs card")
    p4.add_argument("--card", required=True)

    args = ap.parse_args()
    if args.cmd == "digest":
        card = digest_file(Path(args.file), Path(args.out), args.url)
        print(json.dumps(card, indent=2))
        return 0
    if args.cmd == "fetch":
        card = fetch_url(args.url, Path(args.out))
        print(json.dumps(card, indent=2))
        return 0
    if args.cmd == "ledger":
        led = rebuild_ledger(Path(args.dir), Path(args.ledger))
        print(json.dumps({"ok": True, "count": led["count"], "root": led["merkle_style_root"]}, indent=2))
        return 0
    if args.cmd == "verify":
        res = verify_card(Path(args.card))
        print(json.dumps(res, indent=2))
        return 0 if res.get("ok") else 10
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
