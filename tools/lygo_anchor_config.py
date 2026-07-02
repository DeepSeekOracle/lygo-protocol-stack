#!/usr/bin/env python3
"""LYGO Anchor configuration — env + JSON profile (dev / prod / airgap)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE_PATH = ROOT / "tools" / "lygo_control_center" / "anchor_profile.json"
SIGNATURE = "Δ9Φ963-ANCHOR-CONFIG-v1"


@dataclass
class AnchorProfile:
    mode: str = "multi"  # local | turbo | multi | airgap
    workspace_dir: str = "data/anchors"
    receipt_dir: str = "tools/lygo_control_center/workspace"
    queue_dir: str = "data/anchor_queue"
    mesh_db: str = "data/anchor_mesh.sqlite"
    turbo_upload_url: str = "https://up.arweave.net/tx"
    turbo_data_url: str = "https://up.arweave.net/data"
    arweave_gateway: str = "https://arweave.net/"
    free_max_bytes: int = 102400
    ble_company_id: int = 0x9639
    ble_enabled: bool = True
    auto_append_link_archive: bool = True
    tags: list[dict[str, str]] = field(default_factory=list)

    @classmethod
    def from_env(cls) -> "AnchorProfile":
        mode = os.environ.get("LYGO_ANCHOR_MODE", "multi").lower()
        p = cls(mode=mode)
        p.workspace_dir = os.environ.get("LYGO_ANCHOR_WORKSPACE", p.workspace_dir)
        p.receipt_dir = os.environ.get("LYGO_ANCHOR_RECEIPTS", p.receipt_dir)
        if os.environ.get("LYGO_ANCHOR_BLE", "1").lower() in ("0", "false", "no"):
            p.ble_enabled = False
        if not p.tags:
            p.tags = [
                {"name": "App-Name", "value": "LYGO-Anchor"},
                {"name": "Content-Type", "value": "application/json"},
                {"name": "LYGO-Version", "value": "Δ9Φ963-ULTIMATE-v1"},
            ]
        return p

    @classmethod
    def load(cls, path: Path | None = None) -> "AnchorProfile":
        path = path or DEFAULT_PROFILE_PATH
        base = cls.from_env()
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            for k, v in data.items():
                if hasattr(base, k):
                    setattr(base, k, v)
        return base

    def resolve_paths(self, repo_root: Path | None = None) -> dict[str, Path]:
        root = repo_root or ROOT
        return {
            "workspace": root / self.workspace_dir,
            "receipts": root / self.receipt_dir,
            "queue": root / self.queue_dir,
            "mesh_db": root / self.mesh_db,
        }


def save_default_profile(path: Path | None = None) -> Path:
    path = path or DEFAULT_PROFILE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    profile = AnchorProfile.from_env()
    payload: dict[str, Any] = {
        "signature": SIGNATURE,
        "mode": profile.mode,
        "workspace_dir": profile.workspace_dir,
        "receipt_dir": profile.receipt_dir,
        "queue_dir": profile.queue_dir,
        "mesh_db": profile.mesh_db,
        "ble_enabled": profile.ble_enabled,
        "auto_append_link_archive": profile.auto_append_link_archive,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


if __name__ == "__main__":
    p = save_default_profile()
    print(f"Wrote {p}")