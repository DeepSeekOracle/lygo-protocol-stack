"""P1 manifest persistence + optional anchor queue (local lattice)."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any

from pxpipe_lygo.config import ANCHOR_MANIFESTS, MANIFEST_DIR, STACK_ROOT, USE_P1, USE_P3


def _p1_store(payload: bytes, memory_id: str) -> dict[str, Any] | None:
    if not USE_P1:
        return None
    try:
        import sys

        p1 = STACK_ROOT / "protocol1_memory_mycelium" / "src" / "python"
        if str(p1) not in sys.path:
            sys.path.insert(0, str(p1))
        from lygo_p1 import MemoryMycelium  # noqa: E402

        mm = MemoryMycelium()
        return mm.store(payload, memory_id=memory_id)
    except Exception as exc:
        return {"stored": False, "error": str(exc)}


def _p3_signature(manifest_json: str) -> dict[str, Any] | None:
    if not USE_P3:
        return None
    try:
        import sys

        p3 = STACK_ROOT / "protocol3_vortex_consensus" / "src" / "python"
        if str(p3) not in sys.path:
            sys.path.insert(0, str(p3))
        from lygo_p3 import VortexConsensusSync  # noqa: E402

        vc = VortexConsensusSync(kernel=None, mycelium=None, sovereign_id="pxpipe-lygo")
        return vc.vortex_signature(manifest_json)
    except Exception as exc:
        return {"error": str(exc)}


def write_manifest(manifest: dict[str, Any]) -> Path:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    mid = manifest["manifest_id"]
    path = MANIFEST_DIR / f"{mid}.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return path


def persist_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(manifest, sort_keys=True).encode("utf-8")
    manifest.setdefault("timestamp", time.time())
    path = write_manifest(manifest)
    result: dict[str, Any] = {"path": str(path.relative_to(STACK_ROOT)).replace("\\", "/")}

    p1 = _p1_store(body, f"pxpipe_{manifest['manifest_id']}")
    if p1:
        result["p1"] = p1

    sig = _p3_signature(body.decode())
    if sig:
        result["p3_vortex"] = sig
        manifest["p3_vortex"] = sig
        write_manifest(manifest)

    if ANCHOR_MANIFESTS:
        anchor_tool = STACK_ROOT / "tools" / "lygo_anchor.py"
        if anchor_tool.is_file():
            proc = subprocess.run(
                [
                    "python",
                    str(anchor_tool),
                    "--type",
                    "file",
                    "--data",
                    str(path),
                ],
                cwd=str(STACK_ROOT),
                capture_output=True,
                text=True,
                timeout=120,
            )
            result["anchor_exit"] = proc.returncode
            if proc.stdout.strip():
                result["anchor_stdout"] = proc.stdout.strip()[:500]

    return result