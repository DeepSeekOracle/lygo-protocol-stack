"""Execute workflow — optional sandcastle-ai; default local sovereign dry-run."""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Any

SANDCASTLE_AVAILABLE = False
try:
    import sandcastle  # type: ignore  # noqa: F401

    SANDCASTLE_AVAILABLE = True
except ImportError:
    pass


def execute_workflow(workflow: dict[str, Any]) -> dict[str, Any]:
    name = workflow.get("name") or "unnamed"
    agent = workflow.get("agent") or workflow.get("provider") or "local"
    sandbox = workflow.get("sandbox") or "none"
    prompt = workflow.get("prompt") or workflow.get("task") or ""
    residency = workflow.get("data_residency") or workflow.get("lygo", {}).get("residency") or "local"

    if SANDCASTLE_AVAILABLE and os.environ.get("LYGO_SANDCASTLE_USE_UPSTREAM", "").lower() in (
        "1",
        "yes",
        "true",
    ):
        return _run_sandcastle_subprocess(workflow)

    return {
        "mode": "lygo_local_dry_run",
        "workflow_name": name,
        "agent": agent,
        "sandbox": sandbox,
        "data_residency": residency,
        "prompt_preview": (prompt[:240] + "…") if len(prompt) > 240 else prompt,
        "stdout": f"[LYGO] Sovereign dry-run for '{name}' — set LYGO_SANDCASTLE_USE_UPSTREAM=yes and install sandcastle-ai to delegate.",
        "exit_code": 0,
    }


def _run_sandcastle_subprocess(workflow: dict[str, Any]) -> dict[str, Any]:
    """Best-effort CLI if sandcastle package exposes a module entry."""
    return {
        "mode": "sandcastle_stub",
        "workflow_name": workflow.get("name"),
        "note": "sandcastle-ai import OK; wire your fork CLI here",
        "exit_code": 0,
    }


def run_ollama_step(prompt: str, model: str = "llama3.2:1b") -> dict[str, Any]:
    """Optional local inference step for simple workflows."""
    try:
        r = subprocess.run(
            ["ollama", "run", model, prompt[:4000]],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return {"ok": r.returncode == 0, "stdout": r.stdout[:8000], "stderr": r.stderr[:2000]}
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return {"ok": False, "error": str(e)}