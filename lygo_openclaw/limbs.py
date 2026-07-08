"""Dispatch sovereign limbs — stack tools only; no auto social post."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent


def openclaw_home() -> Path:
    return Path(os.environ.get("OPENCLAW_HOME", os.environ.get("OPENCLAW_WORKSPACE", "")) or Path.home() / ".openclaw")


def cmd_help() -> dict[str, Any]:
    return {
        "limbs": [
            "help",
            "status",
            "lattice",
            "army-sentinel",
            "flow-kit-path",
            "hybrid-skill",
        ],
        "hybrid": "Install lyra-openclaw for browser/discord/moltbook/clawnch (runtime keys, user consent).",
        "cli": "python tools/lygo_openclaw.py run <command>",
    }


def cmd_status() -> dict[str, Any]:
    home = openclaw_home()
    grok_hybrid = WORKSPACE / ".grok" / "skills" / "lyra-openclaw"
    grok_lygo = WORKSPACE / ".grok" / "skills" / "lygo-openclaw"
    return {
        "stack_root": str(ROOT),
        "openclaw_home": str(home),
        "openclaw_home_exists": home.is_dir(),
        "grok_lygo_openclaw": grok_lygo.is_dir(),
        "grok_lyra_openclaw": grok_hybrid.is_dir(),
        "flow_kit_mirror": str(ROOT / "clawhub" / "mirrors" / "openclaw-flow-kit"),
    }


def cmd_lattice() -> dict[str, Any]:
    tool = ROOT / "tools" / "verify_lattice_alignment.py"
    if not tool.is_file():
        return {"ok": False, "error": "missing verify_lattice_alignment.py"}
    r = subprocess.run(
        [sys.executable, str(tool)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    tail = (r.stdout or r.stderr)[-2000:]
    return {"ok": r.returncode == 0, "exit_code": r.returncode, "tail": tail}


def cmd_army_sentinel() -> dict[str, Any]:
    paths = [
        WORKSPACE / ".grok" / "skills" / "lygo-ollama-army" / "ollama_command_center" / "workspace" / "sentinel_status.json",
        ROOT / "clawhub" / "mirrors" / "lygo-ollama-army" / "ollama_command_center" / "workspace" / "sentinel_status.json",
    ]
    for p in paths:
        if p.is_file():
            doc = json.loads(p.read_text(encoding="utf-8"))
            lat = doc.get("lattice") or {}
            return {
                "path": str(p),
                "lattice_ok": lat.get("ok"),
                "summary": lat.get("summary"),
            }
    return {"ok": False, "error": "sentinel_status.json not found"}


def cmd_flow_kit_path() -> dict[str, Any]:
    mirror = ROOT / "clawhub" / "mirrors" / "openclaw-flow-kit"
    return {
        "mirror": str(mirror),
        "envelope": "python scripts/run_envelope.py -- <cmd>",
        "moltx_pipeline": "python scripts/moltx_post_pipeline.py (human approval required)",
    }


def cmd_hybrid_skill() -> dict[str, Any]:
    return {
        "skill": "lyra-openclaw",
        "install": "npx clawhub@latest install deepseekoracle/lyra-openclaw (when published) or .grok/skills/lyra-openclaw",
        "note": "Hybrid ops load credentials at runtime — never commit secrets.",
    }


def dispatch(command: str, args: list[str] | None = None) -> dict[str, Any]:
    args = args or []
    key = command.strip().lower().replace("_", "-")
    if key in ("help", "?"):
        return cmd_help()
    if key == "status":
        return cmd_status()
    if key == "lattice":
        return cmd_lattice()
    if key in ("army-sentinel", "sentinel"):
        return cmd_army_sentinel()
    if key in ("flow-kit-path", "flow-kit"):
        return cmd_flow_kit_path()
    if key in ("hybrid-skill", "hybrid"):
        return cmd_hybrid_skill()
    if key == "passthrough" and args:
        return {
            "mode": "passthrough_stub",
            "command": command,
            "args": args,
            "note": "Use lyra-openclaw OS for browser/discord/moltbook; P0 gate passed.",
        }
    return {
        "mode": "unknown_limb",
        "command": command,
        "args": args,
        "hint": "Try: help | status | lattice | army-sentinel",
    }