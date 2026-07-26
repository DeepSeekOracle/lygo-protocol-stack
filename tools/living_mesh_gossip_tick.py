#!/usr/bin/env python3
"""
One epidemic gossip tick: POST local living badge to peers; optional pull /gossip.

Uses HTTP summaries only — never egg payloads.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from collect_living_mesh_badge import collect_living_badge  # noqa: E402

UA = "LYGO-LivingMesh-Gossip/1.0"
SIG = "Delta9Phi963-LIVING-MESH-GOSSIP-v1"


def http_json(method: str, url: str, body: dict | None = None, timeout: int = 12) -> tuple[int, dict | str]:
    data = None
    headers = {"User-Agent": UA}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as e:
        return e.code, str(e)
    except Exception as e:
        return 0, str(e)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--peer", action="append", default=[], help="Peer base URL")
    ap.add_argument("--fanout", type=int, default=2)
    ap.add_argument("--node-id", default="")
    ap.add_argument("--self-base", default="http://127.0.0.1:8787", help="Local node if running")
    args = ap.parse_args()

    badge = collect_living_badge(quick=True, node_id=args.node_id or None)
    peers = list(args.peer or [])
    if not peers and args.self_base:
        peers = [args.self_base]

    random.shuffle(peers)
    targets = peers[: max(1, args.fanout)]
    pushes = []
    for base in targets:
        url = base.rstrip("/") + "/gossip/badge"
        payload = {
            "node_id": badge.get("node_id"),
            "badge": badge,
            "layer": "D",
            "signature": SIG,
        }
        status, resp = http_json("POST", url, payload)
        pushes.append({"peer": base, "http": status, "ok": 200 <= int(status) < 300, "resp": resp if isinstance(resp, dict) else str(resp)[:200]})

    pulls = []
    for base in targets:
        status, resp = http_json("GET", base.rstrip("/") + "/gossip")
        pulls.append({"peer": base, "http": status, "ok": 200 <= int(status) < 300, "gossip": resp if isinstance(resp, dict) else None})

    report = {
        "signature": SIG,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "local_node_id": badge.get("node_id"),
        "roots_digest": (badge.get("living_mesh") or {}).get("roots_digest"),
        "pushes": pushes,
        "pulls": pulls,
        "verdict": "GOSSIP_OK" if any(p.get("ok") for p in pushes) else "GOSSIP_SOFT_FAIL",
    }
    out = ROOT / "tests" / "living_mesh_gossip_last_run.json"
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        # also store latest badge
        (ROOT / "data" / "living_mesh").mkdir(parents=True, exist_ok=True)
        (ROOT / "data" / "living_mesh" / "last_badge.json").write_text(
            json.dumps(badge, indent=2) + "\n", encoding="utf-8"
        )
    except OSError:
        pass
    print(json.dumps(report, indent=2))
    return 0 if report["verdict"] == "GOSSIP_OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
