#!/usr/bin/env python3
"""Copy canonical .grok lygo-ollama-army into clawhub mirror (sanitized for publish)."""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DST = ROOT / "clawhub" / "mirrors" / "lygo-ollama-army"

SKIP_DIRS = {
    "__pycache__",
    "results",
    "logs",
    "ollama_results",
    "army",
}


def src_root() -> Path:
    return Path(os.environ.get("LYGO_GROK_SKILLS", r"I:\E Drive\.grok\skills")) / "lygo-ollama-army"


def _should_skip(rel: Path) -> bool:
    if any(p in SKIP_DIRS for p in rel.parts):
        return True
    if rel.suffix == ".pyc" or rel.name.endswith(".bak"):
        return True
    if rel.match("ollama_command_center/workspace/*") and rel.suffix == ".json":
        return True
    if rel.match("ollama_command_center/tasks/*.task.json"):
        return True
    if rel.match("ollama_queue/*.task.json"):
        return True
    if rel.match("genesis_console/data/*.json"):
        return True
    return False


def safe_army_config(src: Path) -> dict:
    example = src / "ollama_command_center" / "config" / "army_config.example.json"
    if example.is_file():
        return json.loads(example.read_text(encoding="utf-8"))
    return {
        "name": "LYGO Ollama Army Command Center",
        "signature": "Δ9Φ963-ARMY-CC-v3",
        "lygo_stack_root": "",
        "planting": {"enabled": False, "consent": True},
        "access": {
            "hf_write": False,
            "github_push": False,
            "clawhub_publish": False,
            "workspace_write": True,
        },
        "self_tune": {"enabled": False, "auto_enable_planting": False},
        "sentinel": {"enabled": True, "alert_on_lattice_fail": True},
        "notifications": {
            "webhook_url_env": "LYGO_ARMY_WEBHOOK_URL",
            "webhook_enable_env": "LYGO_ARMY_WEBHOOK_ENABLE",
        },
    }


def main() -> int:
    src = src_root()
    if not src.is_dir():
        print(f"MISSING {src}", file=sys.stderr)
        return 2
    if DST.exists():
        shutil.rmtree(DST)
    DST.mkdir(parents=True)

    for item in src.rglob("*"):
        if not item.is_file():
            continue
        rel = item.relative_to(src)
        if _should_skip(rel):
            continue
        out = DST / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, out)

    for sub in (
        DST / "ollama_command_center" / "tasks",
        DST / "ollama_queue",
        DST / "ollama_command_center" / "workspace",
        DST / "ollama_command_center" / "results",
        DST / "ollama_command_center" / "logs",
    ):
        sub.mkdir(parents=True, exist_ok=True)
        keep = sub / ".gitkeep"
        if not keep.is_file():
            keep.write_text("", encoding="utf-8")

    cfg_path = DST / "ollama_command_center" / "config" / "army_config.json"
    cfg_path.write_text(json.dumps(safe_army_config(src), indent=2) + "\n", encoding="utf-8")

    examples = DST / "examples" / "cron_tasks"
    examples.mkdir(parents=True, exist_ok=True)
    src_tasks = src / "ollama_command_center" / "tasks"
    if src_tasks.is_dir():
        for t in list(src_tasks.glob("cron-*.task.json"))[:3]:
            shutil.copy2(t, examples / t.name)
    (examples / "README.md").write_text(
        "# Example cron tasks (not auto-loaded)\n\n"
        "Copy into `ollama_command_center/tasks/` only after reading "
        "`references/SECURITY.md` and setting `LYGO_STACK_ROOT`.\n",
        encoding="utf-8",
    )

    print(json.dumps({"ok": True, "dst": str(DST), "src": str(src)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())