#!/usr/bin/env python3
"""
LYGO Phase 5 Epidemic Convergence Simulator.
Models stochastic spread of an Alignment Badge across N nodes (ports 8700+N concept).
Version: Δ9Φ963-MESH-SCALE-v1.0
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "tests" / "mesh_scale_last_run.json"


class MeshGossipSimulator:
    """Stochastic epidemic badge push: infected nodes fan out to random peers."""

    def __init__(self, total_nodes: int = 100, fanout: int = 2, seed: int | None = None):
        self.total_nodes = total_nodes
        self.fanout = fanout
        self.nodes = [False] * self.total_nodes
        self.rounds = 0
        if seed is not None:
            random.seed(seed)

    def inject_genesis_badge(self, node_index: int = 0) -> None:
        self.nodes[node_index] = True
        print(f"[MESH INIT] Genesis Badge injected at Node {node_index} (Port {8700 + node_index})")

    def execute_gossip_round(self) -> tuple[int, float]:
        self.rounds += 1
        new_infections: list[int] = []

        for i in range(self.total_nodes):
            if self.nodes[i]:
                for _ in range(self.fanout):
                    target = random.randint(0, self.total_nodes - 1)
                    new_infections.append(target)

        for target in new_infections:
            self.nodes[target] = True

        coverage = sum(self.nodes)
        percent = (coverage / self.total_nodes) * 100
        return coverage, percent

    def simulate_convergence(self, verbose: bool = True, pause: float = 0.1) -> dict:
        if verbose:
            print("==================================================")
            print(f" LYGO MESH SIMULATOR: {self.total_nodes} NODES | FANOUT: {self.fanout}")
            print("==================================================\n")

        self.inject_genesis_badge()

        theoretical_rounds = math.ceil(
            math.log(self.total_nodes) / math.log(self.fanout + 1) + math.log(self.total_nodes)
        )
        if verbose:
            print(f"[THEORY] Expected stochastic convergence: ~{theoretical_rounds} rounds\n")

        history: list[dict] = []
        while not all(self.nodes):
            coverage, percent = self.execute_gossip_round()
            history.append({"round": self.rounds, "coverage": coverage, "percent": round(percent, 4)})
            if verbose:
                bar_length = 40
                filled = int((percent / 100) * bar_length)
                bar = "█" * filled + "-" * (bar_length - filled)
                print(
                    f" ROUND {self.rounds:02d} | [{bar}] {percent:6.2f}% "
                    f"({coverage}/{self.total_nodes} Nodes)"
                )
                if pause > 0:
                    time.sleep(pause)

        result = {
            "signature": "Δ9Φ963-PHASE5-MESH-SCALE",
            "total_nodes": self.total_nodes,
            "fanout": self.fanout,
            "base_port": 8700,
            "convergence_rounds": self.rounds,
            "theoretical_rounds_estimate": theoretical_rounds,
            "under_10_rounds": self.rounds < 10,
            "history": history,
        }

        if verbose:
            print("\n==================================================")
            print(f" [CONVERGENCE ACHIEVED] Network fully saturated in {self.rounds} rounds.")
            print(f" P0 Resonance is globally consistent across all {self.total_nodes} nodes.")
            print("==================================================")

        return result


def main() -> int:
    ap = argparse.ArgumentParser(description="LYGO 100-node epidemic mesh scale simulator")
    ap.add_argument("--nodes", type=int, default=100)
    ap.add_argument("--fanout", type=int, default=2)
    ap.add_argument("--seed", type=int, default=None, help="Optional RNG seed for reproducibility")
    ap.add_argument("--no-pause", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    sim = MeshGossipSimulator(total_nodes=args.nodes, fanout=args.fanout, seed=args.seed)
    report = sim.simulate_convergence(verbose=not args.quiet, pause=0.0 if args.no_pause else 0.1)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\n[LOG] Wrote {args.out}")

    return 0 if report["under_10_rounds"] else 1


if __name__ == "__main__":
    raise SystemExit(main())