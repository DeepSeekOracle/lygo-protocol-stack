#!/usr/bin/env python3
"""Multi-anchor verify for Lightfather deadman egg / origin (local + public HTTP GET).

Quorum: local files always required; public mirrors optional (Pages + HF).
Does not publish. Read-only HTTPS GET.
"""
from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "deadman" / "multi_anchor_last_verify.json"

LOCAL = {
    "origin": ROOT / "docs" / "seals" / "LIGHTFATHER_IRREPLACEABLE_ORIGIN.json",
    "manifest": ROOT / "data" / "deadman" / "DEADMAN_MANIFEST_v2.json",
    "deadman_seal": ROOT / "docs" / "seals" / "SEAL_DEADMAN_SUMMON.json",
    "lfw_seal": ROOT / "docs" / "seals" / "SEAL_LFW_SUMMON.json",
    "planted": ROOT / "docs" / "seals" / "lattice_failsafe_planted.json",
    "egg_bin": ROOT / "data" / "kernel_eggs" / "build" / "lightfather-deadman-failsafe-v1.bin",
    "pages_egg_origin": ROOT
    / "docs"
    / "kernel_eggs"
    / "lightfather-deadman-failsafe-v1"
    / "LIGHTFATHER_IRREPLACEABLE_ORIGIN.json",
}

REMOTE = {
    "pages_deadman_html": "https://deepseekoracle.github.io/lygo-protocol-stack/data-vault/deadman.html",
    "pages_origin": (
        "https://deepseekoracle.github.io/lygo-protocol-stack/seals/"
        "LIGHTFATHER_IRREPLACEABLE_ORIGIN.json"
    ),
    "pages_egg_origin": (
        "https://deepseekoracle.github.io/lygo-protocol-stack/kernel_eggs/"
        "lightfather-deadman-failsafe-v1/LIGHTFATHER_IRREPLACEABLE_ORIGIN.json"
    ),
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(url: str, timeout: float = 20.0) -> dict:
    try:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "LYGO-DeadmanVerify/2"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            return {
                "ok": 200 <= resp.status < 300,
                "status": resp.status,
                "sha256": sha256_bytes(body),
                "bytes": len(body),
            }
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"ok": False, "error": str(exc)}


def main() -> int:
    local_report = {}
    local_ok = True
    for name, path in LOCAL.items():
        if path.is_file():
            local_report[name] = {"ok": True, "sha256": sha256_bytes(path.read_bytes()), "path": str(path)}
        else:
            local_report[name] = {"ok": False, "missing": True, "path": str(path)}
            # egg_bin optional if only docs mirror present
            if name != "egg_bin":
                local_ok = False

    remote_report = {name: fetch(url) for name, url in REMOTE.items()}
    remote_ok_count = sum(1 for r in remote_report.values() if r.get("ok"))
    quorum = local_ok and remote_ok_count >= 1

    # Origin consistency local vs pages copy if both exist
    consistency = {}
    lo = LOCAL["origin"]
    po = LOCAL["pages_egg_origin"]
    if lo.is_file() and po.is_file():
        a = json.loads(lo.read_text(encoding="utf-8"))
        b = json.loads(po.read_text(encoding="utf-8"))
        consistency["local_pages_egg_merkle_match"] = a.get("origin_merkle_root") == b.get(
            "origin_merkle_root"
        )
        consistency["local_non_replaceable"] = (a.get("origin_builder") or {}).get("non_replaceable")

    report = {
        "signature": "Delta9Phi963-DEADMAN-MULTI-ANCHOR-VERIFY-v1",
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "local_ok": local_ok,
        "remote_ok_count": remote_ok_count,
        "remote_total": len(REMOTE),
        "quorum_ok": quorum,
        "local": local_report,
        "remote": remote_report,
        "consistency": consistency,
        "note": "Local authority; public mirrors corroborate. No auto-publish.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if quorum else 1


if __name__ == "__main__":
    raise SystemExit(main())
