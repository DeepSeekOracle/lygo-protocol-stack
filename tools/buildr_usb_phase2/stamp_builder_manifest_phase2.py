#!/usr/bin/env python3
"""Stamp BUILDER_MANIFEST.json with Phase 2 fields after core image exists."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def stamp(key_root: Path) -> dict:
    manifest_path = key_root / "BUILDER_MANIFEST.json"
    if not manifest_path.is_file():
        return {"ok": False, "error": "missing BUILDER_MANIFEST.json"}
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    core = key_root / "images" / "lygo_core.tar.gz"
    phase = 2 if core.is_file() else int(data.get("phase", 1))
    data.update(
        {
            "edition": data.get("edition", "GROK_BUILDR"),
            "phase": phase,
            "phase2_core": "images/lygo_core.tar.gz",
            "supervisor_port": 9630,
            "phase2_stamped_utc": datetime.now(timezone.utc).isoformat(),
            "boot_entry_grok": data.get("boot_entry_grok", "GROK_BUILDR_BOOT.md"),
            "blueprint": data.get("blueprint", "README_BUILDR_USB_BLUEPRINT.md"),
        }
    )
    manifest_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return {"ok": True, "phase": phase, "path": str(manifest_path)}


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--key-root", default=None)
    args = ap.parse_args()
    key = Path(args.key_root) if args.key_root else Path(__file__).resolve().parents[1]
    print(json.dumps(stamp(key), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())