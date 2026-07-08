#!/usr/bin/env python3
"""Re-sign scalable registry manifests after P0 golden hash changes."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.scalable_registry.manifest_builder import manifest_content_sha256  # noqa: E402
from tools.scalable_registry.provenance import sign_merkle_root  # noqa: E402

MANIFESTS = ROOT / "data" / "scalable_registry" / "manifests"


def main() -> int:
    count = 0
    for path in MANIFESTS.glob("*.json"):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        root = str(manifest.get("merkle_root") or "")
        if not root:
            continue
        node = (manifest.get("provenance") or {}).get("generator_node_id") or "LYGO_REGISTRY_NODE"
        manifest["provenance"] = sign_merkle_root(root, node_id=node)
        manifest["content_sha256"] = manifest_content_sha256(manifest)
        path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        count += 1
    print(f"resigned={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())