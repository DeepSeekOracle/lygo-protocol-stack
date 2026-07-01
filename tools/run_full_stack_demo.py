#!/usr/bin/env python3
"""Run integrated P0–P5 LYGO stack demo."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "stack"))

from lygo_stack import deploy_stack  # noqa: E402


def main() -> int:
    stack = deploy_stack()
    result = stack.demo_cycle()
    print(json.dumps(result, indent=2, default=str)[:12000])
    ok = result.get("harmony_node", {}).get("success", False)
    print("\n✅ Full stack demo complete." if ok else "\n⚠️ Stack demo finished with warnings.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())