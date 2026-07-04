#!/usr/bin/env python3
"""Initialize writable data/ partition (Phase 2; LUKS on Linux — see LUKS_LINUX.md)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

LAYOUT = {
    "signature": "Δ9Φ963-DATA-PARTITION-v1",
    "hermes_audit": "data/hermes_audit/audit_trail.log",
    "memory_mycelium": "data/memory_mycelium/shards",
    "user_data": "data/user_data",
    "models": "data/models",
    "certs": "data/certs",
    "git_sync_queue": "data/.git_sync_queue",
}


def init_data(key_root: Path) -> dict:
    created = []
    for name, rel in LAYOUT.items():
        if name == "signature" or rel.endswith(".log"):
            continue
        p = key_root / rel
        p.mkdir(parents=True, exist_ok=True)
        created.append(rel)
    audit = key_root / LAYOUT["hermes_audit"]
    audit.parent.mkdir(parents=True, exist_ok=True)
    if not audit.is_file():
        audit.write_text("", encoding="utf-8")
    meta = key_root / "data" / "partition_meta.json"
    meta.write_text(
        json.dumps(
            {
                **LAYOUT,
                "initialized_utc": datetime.now(timezone.utc).isoformat(),
                "encrypted": False,
                "note": "Windows Phase 2 uses exFAT data/; enable LUKS on Linux imaging",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    os.environ.setdefault("LYGO_HERMES_AUDIT_LOG", str(audit))
    return {"ok": True, "created": created, "meta": str(meta)}


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--key-root", default=os.environ.get("LYGO_BUILDER_KEY_ROOT", r"E:\LYGO_BUILDER_KEY"))
    args = ap.parse_args()
    print(json.dumps(init_data(Path(args.key_root)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())