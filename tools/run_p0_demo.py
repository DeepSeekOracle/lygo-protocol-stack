#!/usr/bin/env python3
"""CLI demo: input, phi_risk, verdict, reasoning for every P0 vector."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P0 = ROOT / "protocol0_byte_entropy_filter" / "src" / "python" / "lygo_p0.py"
BUILD = ROOT / "tools" / "build_p0_vectors.py"
PARITY = ROOT / "tools" / "p0_crosslang_parity.py"


def main() -> int:
    parser = argparse.ArgumentParser(description="LYGO P0 Nano Kernel demo CLI")
    parser.add_argument("--rebuild-vectors", action="store_true", help="Regenerate fixture JSON")
    parser.add_argument("--parity", action="store_true", help="Run C/Rust SHA parity after demo")
    parser.add_argument("--quiet", action="store_true", help="Hide reasoning text")
    parser.add_argument("--id", help="Run a single vector id only")
    args = parser.parse_args()

    if args.rebuild_vectors:
        subprocess.run([sys.executable, str(BUILD)], check=True)

    sys.path.insert(0, str(P0.parent))
    import lygo_p0  # noqa: E402

    if not lygo_p0.fixtures_path().is_file():
        subprocess.run([sys.executable, str(BUILD)], check=True)

    vectors = lygo_p0.load_vectors()
    if args.id:
        vectors = [v for v in vectors if v["id"] == args.id]
        if not vectors:
            print(f"Unknown vector id: {args.id}", file=sys.stderr)
            return 1

    print("LYGO P0.4 — Φ-gate demo")
    print("=" * 72)
    for entry in vectors:
        data = bytes.fromhex(entry["hex"])
        res = lygo_p0.validate_bytes(data)
        preview = lygo_p0._preview_bytes(data)
        print(f"\n[{entry['id']}] ({entry.get('category', '')}) {entry.get('description', '')}")
        print(f"  input: {preview}")
        print(f"  len: {len(data)}  hash16: {res['hash']}")
        print(f"  phi_risk: {res['phi_risk']:.4f}")
        print(f"  decision: {res['verdict']}")
        if not args.quiet:
            print(f"  reasoning: {res['reasoning']}")

    body = lygo_p0.run_vector_suite()
    import hashlib

    digest = hashlib.sha256(body.encode()).hexdigest()
    print("\n" + "=" * 72)
    print(f"vectors run: {len(vectors)} (suite total: {len(lygo_p0.load_vectors())})")
    print(f"SHA-256(canonical): {digest}")

    if args.parity:
        return subprocess.call([sys.executable, str(PARITY)])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())