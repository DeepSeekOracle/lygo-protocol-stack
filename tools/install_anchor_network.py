#!/usr/bin/env python3
"""Install LYGO Anchor across local network surfaces (army, lattice, profiles)."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from lygo_anchor_config import save_default_profile  # noqa: E402

ARMY_CC = ROOT.parent / ".grok" / "skills" / "lygo-ollama-army" / "ollama_command_center"
LYRA_CORE = ROOT.parent / "LYRA_CORE"


def main() -> int:
    log: list[str] = []
    profile_path = save_default_profile()
    log.append(f"profile: {profile_path}")

    for sub in ("data/anchors", "data/anchor_queue", "data/kernel_eggs/build", "tools/lygo_control_center/workspace"):
        (ROOT / sub).mkdir(parents=True, exist_ok=True)
        log.append(f"mkdir {sub}")

    import subprocess

    for cmd in (
        [sys.executable, str(TOOLS / "build_kernel_eggs.py")],
        [sys.executable, str(TOOLS / "anchor_kernel_eggs.py"), "--local-only"],
    ):
        try:
            subprocess.run(cmd, cwd=ROOT, check=False, timeout=120)
            log.append("ran " + " ".join(cmd[-1:]))
        except Exception as exc:
            log.append(f"kernel_egg step skipped: {exc}")

    if ARMY_CC.is_dir():
        ws = ARMY_CC / "workspace"
        ws.mkdir(parents=True, exist_ok=True)
        manifest = {
            "signature": "Δ9Φ963-ANCHOR-NETWORK-v1",
            "stack_root": str(ROOT),
            "cron_roles": ["anchor-health"],
            "worker": "python tools/anchor_autonomy_worker.py --loop --interval 300 --slm-each-pulse",
            "mode_env": "LYGO_ANCHOR_MODE=multi",
        }
        (ws / "LYGO_ANCHOR_NETWORK.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        log.append(f"army manifest: {ws / 'LYGO_ANCHOR_NETWORK.json'}")

        cfg = ARMY_CC / "config" / "army_config.json"
        if cfg.is_file():
            data = json.loads(cfg.read_text(encoding="utf-8"))
            roles = data.get("army_capacity", {}).get("roles", [])
            if "anchor-health" not in roles:
                roles.append("anchor-health")
                data["army_capacity"]["roles"] = roles
                cfg.write_text(json.dumps(data, indent=2), encoding="utf-8")
                log.append("army_config: added anchor-health role")

    mem_day = LYRA_CORE / "memory"
    if mem_day.is_dir():
        stamp = mem_day / "ANCHOR_NETWORK_INSTALLED.md"
        stamp.write_text(
            "\n".join(
                [
                    "# LYGO Anchor network install",
                    f"- Stack: `{ROOT}`",
                    "- Run: `python tools/anchor_autonomy_worker.py --loop`",
                    "- Audit: `python tools/run_anchor_audit.py`",
                    "",
                    *log,
                ]
            ),
            encoding="utf-8",
        )
        log.append(f"lyra stamp: {stamp}")

    archive = ROOT / "docs" / "LYGO_PUBLIC_LINK_ARCHIVE.json"
    if archive.is_file():
        data = json.loads(archive.read_text(encoding="utf-8"))
        if not any(e.get("id") == "lygo-anchor-system" for e in data.get("entries", [])):
            data.setdefault("entries", []).append(
                {
                    "id": "lygo-anchor-system",
                    "title": "LYGO Immutable Anchor (local + permaweb)",
                    "role": "anchor-infra",
                    "urls": {
                        "docs": "docs/ANCHOR_DEPLOYMENT.md",
                        "audit_tool": "tools/run_anchor_audit.py",
                    },
                    "since": "2026-07-02",
                }
            )
            archive.write_text(json.dumps(data, indent=2), encoding="utf-8")
            log.append("link archive: lygo-anchor-system entry")

    print(json.dumps({"ok": True, "log": log}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())