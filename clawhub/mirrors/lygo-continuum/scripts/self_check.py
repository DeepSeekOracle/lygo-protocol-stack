#!/usr/bin/env python3
"""Self-check for lygo-continuum — no network, no subprocess spawn of shell."""
from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import continuum as c  # noqa: E402


def main() -> int:
    src = (HERE / "continuum.py").read_text(encoding="utf-8")
    no_subprocess_import = not re.search(r"(?m)^\s*import\s+subprocess\b", src)
    no_urllib = not re.search(r"(?m)^\s*import\s+urllib\b", src)
    no_requests = "import requests" not in src

    demo = c.cmd_demo()

    # Unit: text_sha256 + integrity break
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "f.txt").write_text("hello continuum\n", encoding="utf-8")
        cap = c.seal_capsule(
            claims=[
                {"kind": "file_contains", "path": "f.txt", "needle": "continuum"},
                {"kind": "file_sha256", "path": "f.txt"},
            ],
            task_summary="unit",
            agent="self_check",
            base=root,
        )
        v1 = c.verify_capsule(cap, base=root)
        # Tamper root_hash
        broken = dict(cap)
        broken["root_hash"] = "0" * 64
        v2 = c.verify_capsule(broken, base=root)
        kinds_ok = "file_sha256" in c.CLAIM_KINDS and "json_path_eq" in c.CLAIM_KINDS

    ok = (
        demo.get("ok") is True
        and v1.get("ok") is True
        and v2.get("integrity_ok") is False
        and no_subprocess_import
        and no_urllib
        and no_requests
        and kinds_ok
        and c.SCHEMA == "lygo.continuum.v1"
    )
    print(
        json.dumps(
            {
                "ok": ok,
                "signature": c.SIG,
                "version": c.VERSION,
                "demo_ok": demo.get("ok"),
                "verify_ok": v1.get("ok"),
                "integrity_detects_tamper": v2.get("integrity_ok") is False,
                "no_subprocess_import": no_subprocess_import,
                "no_network_imports": no_urllib and no_requests,
                "claim_kinds": len(c.CLAIM_KINDS),
            },
            indent=2,
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
