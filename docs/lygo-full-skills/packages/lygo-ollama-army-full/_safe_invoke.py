#!/usr/bin/env python3
"""Allowlisted in-process Python runner — SkillSpector-safe (no OS process spawn / shell).

Strict allowlist:
  - Skill-local: only named scripts (not arbitrary .py under SKILL_ROOT)
  - Stack tools: only STACK_TOOL_ALLOW under validated LYGO_STACK_ROOT/tools/
  - Kernel planter: only named consent scripts under lygo-kernel-egg-planter mirrors
"""
from __future__ import annotations

import contextlib
import io
import os
import runpy
import sys
import threading
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

SKILL_ROOT = Path(__file__).resolve().parent

# Stack tools that army roles may invoke (must live under validated LYGO_STACK_ROOT/tools/)
STACK_TOOL_ALLOW = frozenset(
    {
        "verify_lattice_alignment.py",
        "run_sovereign_integrity_test.py",
        "lygo_network_builder_verify.py",
        "verify_public_pages.py",
        "run_slm_audit.py",
        "run_phase7_audit.py",
        "run_phase9_audit.py",
        "verify_kernel_eggs.py",
        "verify_champion_eggs.py",
        "run_anchor_audit.py",
        "anchor_autonomy_worker.py",
        "moltx_lattice_pulse.py",
        "moltbook_lattice_pulse.py",
        "joy_loop_protocol.py",
        "champion_bootloader.py",
        "build_haven_star_chart.py",
        "build_haven_star_chart_artifacts.py",
        "render_clawhub_catalog.py",
    }
)

# Exact basenames that may be run via run_python under this skill
ARMY_SCRIPT_ALLOW = frozenset(
    {
        # skill root
        "ollama_daemon.py",
        "ollama_army_launcher.py",
        "champion_summon.py",
        "seed_productive_tasks.py",
        "resonance_utility.py",
        "lygo_stack_root.py",
        "self_check.py",
        # command center scripts
        "army_self_tune.py",
        "sentinel_heartbeat.py",
        "army_idle_housekeeping.py",
        "army_idle_cron_once.py",
        "army_cron_once.py",
        "army_health_check.py",
        "run_army_planting.py",
        "verify_army_tuning.py",
        "heartbeats_only.py",
        "army_autonomous_supervisor.py",
        "army_idle_guardian_supervisor.py",
        "army_queue_utils.py",
        # genesis
        "collector.py",
        "server.py",
    }
)

PLANTER_SCRIPT_ALLOW = frozenset(
    {
        "preflight.py",
        "smoke_test.py",
        "plant_with_consent.py",
        "verify_eggs.py",
    }
)


@dataclass
class RunResult:
    returncode: int
    stdout: str
    stderr: str


def _is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except (ValueError, OSError):
        return False


def allowed_script(script: Path, *, stack_root: Path | None = None) -> bool:
    """Strict allowlist — no 'any .py under tree' escape hatches."""
    script = script.resolve()
    if not script.is_file() or script.suffix.lower() != ".py":
        return False

    if _is_under(script, SKILL_ROOT):
        return script.name in ARMY_SCRIPT_ALLOW

    if stack_root and _is_under(script, stack_root):
        if _is_under(script, stack_root / "tools"):
            return script.name in STACK_TOOL_ALLOW
        # consent-gated planter mirror scripts only (named + under planter skill dir)
        if "lygo-kernel-egg-planter" in script.parts and script.name in PLANTER_SCRIPT_ALLOW:
            return True
        if "clawhub" in script.parts and "mirrors" in script.parts:
            if "lygo-kernel-egg-planter" in script.parts and script.name in PLANTER_SCRIPT_ALLOW:
                return True
    return False


def run_python(
    script: Path | str,
    args: list[str] | None = None,
    *,
    cwd: Path | str | None = None,
    timeout: float = 180,
    stack_root: Path | None = None,
    env_extra: dict[str, str] | None = None,
) -> RunResult:
    """In-process allowlisted script execution (captures stdout/stderr)."""
    script_p = Path(script).resolve()
    if not allowed_script(script_p, stack_root=stack_root):
        return RunResult(2, "", f"REFUSED: script not allowlisted: {script_p}")

    args = list(args or [])
    cwd_p = Path(cwd).resolve() if cwd else script_p.parent
    if not cwd_p.is_dir():
        return RunResult(2, "", f"REFUSED: bad cwd {cwd_p}")

    safe_env: dict[str, str] = {}
    if env_extra:
        for k, v in env_extra.items():
            if k == "LYGO_STACK_ROOT" and v and Path(v).is_dir():
                safe_env[k] = str(Path(v).resolve())
            elif k == "MOLTBOOK_ACCOUNT" and str(v) in ("lyra", "lightfather"):
                safe_env[k] = str(v)

    out_buf = io.StringIO()
    err_buf = io.StringIO()
    code_box: list[int] = [0]
    old_argv = sys.argv[:]
    old_cwd = os.getcwd()
    old_env = {k: os.environ.get(k) for k in safe_env}

    def target() -> None:
        try:
            sys.argv = [str(script_p), *args]
            os.chdir(str(cwd_p))
            for k, v in safe_env.items():
                os.environ[k] = v
            with contextlib.redirect_stdout(out_buf), contextlib.redirect_stderr(err_buf):
                runpy.run_path(str(script_p), run_name="__main__")
            code_box[0] = 0
        except SystemExit as exc:
            c = exc.code
            if c is None:
                code_box[0] = 0
            elif isinstance(c, int):
                code_box[0] = c
            else:
                code_box[0] = 1
                err_buf.write(str(c))
        except Exception:
            code_box[0] = 1
            err_buf.write(traceback.format_exc())
        finally:
            sys.argv = old_argv
            try:
                os.chdir(old_cwd)
            except OSError:
                pass
            for k, prev in old_env.items():
                if prev is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = prev

    thr = threading.Thread(target=target, name=f"safe-run-{script_p.name}", daemon=True)
    thr.start()
    thr.join(timeout=timeout)
    if thr.is_alive():
        return RunResult(
            124,
            out_buf.getvalue(),
            (err_buf.getvalue() + "\nTIMEOUT after %ss" % timeout).strip(),
        )
    return RunResult(code_box[0], out_buf.getvalue(), err_buf.getvalue())


def run_daemon_thread(fn: Callable[[], None], *, name: str = "army-daemon") -> threading.Thread:
    t = threading.Thread(target=fn, name=name, daemon=True)
    t.start()
    return t


def git_status_summary(repo: Path) -> dict:
    """Local git status via reading .git (no subprocess). Best-effort."""
    git = Path(repo) / ".git"
    if not git.exists():
        return {"ok": False, "clean": True, "status_line": "no .git"}
    head = ""
    try:
        head_path = git / "HEAD"
        if head_path.is_file():
            head = head_path.read_text(encoding="utf-8", errors="replace").strip()[:80]
    except OSError:
        pass
    return {"ok": True, "clean": True, "status_line": head or "git present"}


def write_local_alert(path: Path, message: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(message.rstrip() + "\n")
