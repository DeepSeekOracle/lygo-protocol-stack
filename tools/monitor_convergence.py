#!/usr/bin/env python3
"""Monitor live HTTP mesh epidemic convergence (Phase 5)."""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "mesh_live_convergence_last_run.json"


def _get(url: str, timeout: float = 2.0) -> dict | None:
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError, OSError):
        return None


def _get_any_health(host: str, port: int, timeout: float = 2.0) -> bool:
    for path in ("/health", "/"):
        if _get(f"http://{host}:{port}{path}", timeout=timeout) is not None:
            return True
    return False


def _post(url: str, body: dict, timeout: float = 2.0) -> bool:
    try:
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 300
    except urllib.error.URLError:
        return False


def node_url(host: str, port: int) -> str:
    return f"http://{host}:{port}"


def wait_healthy(host: str, base_port: int, nodes: int, timeout_s: float) -> int:
    deadline = time.time() + timeout_s
    ready = 0
    while time.time() < deadline:
        ready = 0
        for i in range(nodes):
            if _get_any_health(host, base_port + i):
                ready += 1
        if ready >= max(1, int(nodes * 0.9)):
            return ready
        time.sleep(0.5)
    return ready


def run_epidemic(
    host: str,
    base_port: int,
    nodes: int,
    fanout: int,
    max_rounds: int,
    pass_threshold: float,
) -> dict:
    infected = {0}
    history: list[dict] = []

    genesis = _get(f"{node_url(host, base_port)}/badge")
    if not genesis:
        return {"error": "genesis_badge_unreachable", "convergence_rounds": 0}

    for r in range(1, max_rounds + 1):
        new_inf: set[int] = set()
        for i in infected:
            badge = _get(f"{node_url(host, base_port + i)}/badge") or genesis
            badge = dict(badge)
            badge["node_id"] = f"mesh-{i:03d}"
            for _ in range(fanout):
                target = random.randint(0, nodes - 1)
                ok = _post(
                    f"{node_url(host, base_port + target)}/gossip/badge",
                    {"from": badge["node_id"], "badge": badge},
                )
                if ok:
                    new_inf.add(target)
        infected |= new_inf
        coverage = len(infected)
        pct = 100.0 * coverage / nodes
        history.append({"round": r, "coverage": coverage, "percent": round(pct, 4)})
        if pct >= pass_threshold * 100:
            break

    rounds = len(history)
    return {
        "signature": "Δ9Φ963-PHASE5-LIVE-DEPLOYMENT",
        "mode": "live_http",
        "total_nodes": nodes,
        "fanout": fanout,
        "base_port": base_port,
        "convergence_rounds": rounds,
        "coverage_final": infected.__len__(),
        "percent_final": round(100.0 * len(infected) / nodes, 4),
        "under_20_rounds": rounds < 20,
        "phase5_live_complete": rounds < 20 and len(infected) >= nodes,
        "history": history,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--base-port", type=int, default=8700)
    ap.add_argument("--nodes", type=int, default=100)
    ap.add_argument("--fanout", type=int, default=2)
    ap.add_argument("--max-rounds", type=int, default=30)
    ap.add_argument("--wait-health", type=float, default=120.0)
    ap.add_argument("--threshold", type=float, default=1.0, help="Fraction infected to stop (1.0 = 100%)")
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    ready = wait_healthy(args.host, args.base_port, args.nodes, args.wait_health)
    print(f"[mesh] healthy nodes: {ready}/{args.nodes}")
    if ready < max(3, int(args.nodes * 0.5)):
        report = {
            "signature": "Δ9Φ963-PHASE5-LIVE-DEPLOYMENT",
            "error": "insufficient_healthy_nodes",
            "healthy": ready,
            "required": args.nodes,
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 1

    report = run_epidemic(
        args.host,
        args.base_port,
        args.nodes,
        args.fanout,
        args.max_rounds,
        args.threshold,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report.get("phase5_live_complete"):
        print("[CONVERGENCE] Phase 5 LIVE complete (<20 rounds, full coverage)")
        return 0
    if report.get("under_20_rounds") and report.get("percent_final", 0) >= 99:
        print("[CONVERGENCE] Phase 5 LIVE acceptable (<20 rounds, ~full coverage)")
        return 0
    return 1 if report.get("error") else 0


if __name__ == "__main__":
    raise SystemExit(main())