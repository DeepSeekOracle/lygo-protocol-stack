#!/usr/bin/env python3
"""Compare byte_entropy_filter vs lygo_p0_lyra_kernel structural validator (Biophase7)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / "protocol0_byte_entropy_filter" / "src" / "python"
sys.path.insert(0, str(PY))

from byte_entropy_filter import validate_bytes  # noqa: E402
import lygo_p0_lyra_kernel as lyra  # noqa: E402

TEST_VECTORS = [
    ("small_json", b'{"a": 1}'),
    ("oversized", b"x" * 10000),
    ("nested_deep", str({"a": {"b": {"c": {"d": {"e": {"f": {"g": {"h": 1}}}}}}}}).encode()),
    ("plain_text", b"hello world, this is a normal sentence."),
]


def main() -> int:
    print("=" * 70)
    print("P0 VARIANT COMPARISON — byte_entropy_filter vs lygo_p0_lyra_kernel")
    print("=" * 70)

    for name, data in TEST_VECTORS:
        bef_result = validate_bytes(data)
        print(f"\n[{name}] len={len(data)}")
        print(
            f"  byte_entropy_filter: verdict={bef_result['verdict']} "
            f"entropy={bef_result['entropy']} compression={bef_result['compression']}"
        )
        try:
            parsed: object
            text = data.decode("utf-8", errors="replace")
            try:
                import json

                parsed = json.loads(text)
            except json.JSONDecodeError:
                parsed = text
            lyra_result = lyra.validate(parsed)
            print(f"  lyra_kernel:         verdict={lyra_result['verdict']}")
            if "oath" in lyra_result:
                print("  WARNING: unexpected oath block — OathVectorEngine should be removed")
        except Exception as e:
            print(f"  lyra_kernel:         ERROR {e}")

    print("\n" + "=" * 70)
    print("OathVectorEngine removed. Structural bounds only on lyra_kernel.")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())