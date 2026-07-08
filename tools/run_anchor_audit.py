#!/usr/bin/env python3
"""Anchor subsystem audit — local CA, receipts, mesh DB, optional turbo ping."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from lygo_anchor import MultiAnchor  # noqa: E402
from lygo_anchor_config import AnchorProfile, save_default_profile  # noqa: E402
from lygo_mesh_router import LygoMeshRouter  # noqa: E402


def main() -> int:
    t0 = time.perf_counter()
    checks: list[dict] = []
    profile = AnchorProfile.load()
    paths = profile.resolve_paths(ROOT)

    def record(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})

    save_default_profile()
    record("anchor_profile", (ROOT / "tools" / "lygo_control_center" / "anchor_profile.json").is_file())

    for key in ("workspace", "queue", "receipts"):
        p = paths[key]
        p.mkdir(parents=True, exist_ok=True)
        record(f"path_{key}", p.is_dir(), str(p))

    anchor = MultiAnchor(profile, ROOT)
    test = anchor.anchor_payload("audit_probe", {"probe": True, "ts": time.time()}, "AUDIT")
    record("anchor_roundtrip", test.success, test.service)

    router = LygoMeshRouter()
    router.record("deadbeef", "audit", hop=0)
    record("mesh_router", len(router.list_recent(1)) >= 1)

    required = [
        ROOT / "tools" / "lygo_anchor.py",
        ROOT / "tools" / "lygo_immutable_anchor.py",
        ROOT / "stack" / "lygo_stack_anchor.py",
        ROOT / "docs" / "ANCHOR_DEPLOYMENT.md",
    ]
    for p in required:
        record(p.name, p.is_file(), str(p.relative_to(ROOT)))

    all_pass = all(c["ok"] for c in checks)
    out = {
        "signature": "Δ9Φ963-ANCHOR-AUDIT-v1",
        "all_pass": all_pass,
        "duration_ms": int((time.perf_counter() - t0) * 1000),
        "checks": checks,
        "sample_anchor_url": test.url,
    }
    (ROOT / "tests" / "anchor_audit_last_run.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())