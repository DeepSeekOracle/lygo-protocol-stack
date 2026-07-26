#!/usr/bin/env python3
"""Compare local Layer D badge roots against peer badges (summaries only)."""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from collect_living_mesh_badge import collect_living_badge  # noqa: E402

UA = "LYGO-LivingMesh/1.0"


def fetch_json(url: str, timeout: int = 15) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def compare(local: dict, remote: dict) -> dict:
    lr = (local.get("living_mesh") or {}).get("roots") or {}
    rr = (remote.get("living_mesh") or remote.get("badge", {}).get("living_mesh") or {}).get("roots")
    if rr is None and "kernel_egg_registry_merkle_root" in remote:
        rr = {
            "A_classic_merkle": remote.get("kernel_egg_registry_merkle_root"),
            "B_sovereign_merkle": None,
            "C_public_manifest_sha256": None,
            "star_chart_registry_sha256": None,
        }
    rr = rr or {}
    fields = [
        "A_classic_merkle",
        "B_sovereign_merkle",
        "C_public_manifest_sha256",
        "star_chart_registry_sha256",
    ]
    diffs = {}
    matches = {}
    for f in fields:
        lv, rv = lr.get(f), rr.get(f)
        if lv and rv:
            matches[f] = lv == rv
            if lv != rv:
                diffs[f] = {"local": lv, "remote": rv}
        elif lv or rv:
            matches[f] = None  # incomplete
    local_q = (local.get("living_mesh") or {}).get("local_status") == "QUARANTINE"
    remote_q = (remote.get("living_mesh") or {}).get("local_status") == "QUARANTINE"
    if local_q or remote_q:
        status = "QUARANTINE_SIGNAL"
    elif diffs:
        status = "FORK_VISIBLE"
    elif any(v is True for v in matches.values()):
        status = "HARMONIC"
    else:
        status = "INCOMPLETE"
    return {
        "status": status,
        "matches": matches,
        "diffs": diffs,
        "local_status": (local.get("living_mesh") or {}).get("local_status"),
        "remote_status": (remote.get("living_mesh") or {}).get("local_status"),
        "remote_node_id": remote.get("node_id") or remote.get("badge", {}).get("node_id"),
        "protection": "do_not_merge_eggs_on_fork; local remains authority",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--peer", action="append", default=[], help="Peer base URL e.g. http://127.0.0.1:8787")
    ap.add_argument("--badge-url", action="append", default=[], help="Full badge JSON URL")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    local = collect_living_badge(quick=True)
    reports = []
    for base in args.peer:
        url = base.rstrip("/") + "/badge"
        try:
            remote = fetch_json(url)
            reports.append({"peer": base, "ok": True, **compare(local, remote)})
        except Exception as e:
            reports.append({"peer": base, "ok": False, "error": str(e), "status": "UNREACHABLE"})
    for url in args.badge_url:
        try:
            remote = fetch_json(url)
            reports.append({"peer": url, "ok": True, **compare(local, remote)})
        except Exception as e:
            reports.append({"peer": url, "ok": False, "error": str(e), "status": "UNREACHABLE"})

    out = {
        "signature": "Delta9Phi963-LIVING-MESH-COMPARE-v1",
        "local_node_id": local.get("node_id"),
        "local_roots_digest": (local.get("living_mesh") or {}).get("roots_digest"),
        "peers": reports,
        "verdict": "HARMONIC"
        if reports and all(r.get("status") == "HARMONIC" for r in reports if r.get("ok"))
        else "MIXED"
        if reports
        else "NO_PEERS",
    }
    # save
    art = ROOT / "tests" / "living_mesh_compare_last_run.json"
    try:
        art.parent.mkdir(parents=True, exist_ok=True)
        art.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass
    print(json.dumps(out, indent=2))
    if any(r.get("status") == "QUARANTINE_SIGNAL" for r in reports):
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
