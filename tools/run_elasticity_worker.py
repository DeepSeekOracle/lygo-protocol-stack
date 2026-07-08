#!/usr/bin/env python3
"""Phase 4 worker — parallel audit drain using federation pool."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "stack"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--interval", type=float, default=5.0)
    args = ap.parse_args()

    from lygo_stack import deploy_stack  # noqa: E402

    stack = deploy_stack("ELASTICITY_WORKER")
    vectors_path = ROOT / "tests" / "test_falsifiable_vectors.json"
    data = json.loads(vectors_path.read_text(encoding="utf-8"))
    items: list[tuple[dict, str]] = []
    for cat, vecs in (data.get("categories") or {}).items():
        for v in vecs[:4]:
            items.append((v, cat))

    def _run(vec: dict, cat: str) -> dict:
        return stack.process_falsifiable_vector(vec, category=cat)

    print(f"LYGO elasticity worker started (workers={args.workers})")
    while True:
        stack.elasticity.drain_queue_to_mycelium()
        if items:
            out = stack.federation.pool.map_vectors(items, _run)
            stack.federation.announce_alignment(
                {"status": "ALIGNED", "processed": len(out), "signature": "Δ9Φ963-PHASE4-WORKER"}
            )
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())