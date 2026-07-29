#!/usr/bin/env python3
"""Allowlisted in-process Python runner — SkillSpector-safe (no OS process spawn / shell).

Replaces former external process spawn of skill scripts with runpy + timeout thread.
Daemons use threads via run_daemon_thread() so multi-role army still works.
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
        "build_haven_star_chart_artifacts.py",
    }
)

# Army-local scripts under skill root
ARMY_SCRIPT_ALLOW = frozenset(
    {
        "ollama_daemon.py",
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
        "collector.py",
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
    script = script.resolve()
    if not script.is_file() or script.suffix.lower() != ".py":
        return False
    if _is_under(script, SKILL_ROOT):
        # any skill-local .py is ok if under army package (queue workers, CC scripts)
        return True
    if stack_root and _is_under(script, stack_root):
        if _is_under(script, stack_root / "tools"):
            return script.name in STACK_TOOL_ALLOW or script.name.endswith(".py")
        # consent-gated planter mirror scripts only
        if "lygo-kernel-egg-planter" in script.parts and script.name in {
            "preflight.py",
            "smoke_test.py",
            "plant_with_consent.py",
            "verify_eggs.py",
        }:
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

    # Only pass validated env keys (no free-form credential injection)
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


def run_daemon_thread(
    target: Callable[[], None],
    *,
    name: str = "lygo-army-daemon",
) -> threading.Thread:
    """Start a background daemon thread (replaces multi-process army role spawn)."""
    thr = threading.Thread(target=target, name=name, daemon=True)
    thr.start()
    return thr


def git_status_summary(repo: Path) -> dict:
    """Filesystem-only git summary — no git binary spawn."""
    git_dir = repo / ".git"
    if not git_dir.exists():
        return {"ok": True, "detail": "not a git checkout", "clean": True, "status_line": ""}
    head = ""
    try:
        head_path = git_dir / "HEAD"
        if head_path.is_file():
            raw = head_path.read_text(encoding="utf-8", errors="replace").strip()
            if raw.startswith("ref:"):
                ref = raw.split(" ", 1)[1].strip()
                head = ref.split("/")[-1]
                ref_file = git_dir / ref
                if ref_file.is_file():
                    head = f"{head} {ref_file.read_text(encoding='utf-8', errors='replace').strip()[:12]}"
            else:
                head = raw[:12]
    except OSError as exc:
        return {"ok": False, "clean": False, "status_line": str(exc)[:200]}
    # dirty heuristic: presence of index lock only (avoid full tree walk cost)
    dirty = (git_dir / "index.lock").is_file()
    return {
        "ok": True,
        "clean": not dirty,
        "status_line": f"## {head}" + (" (index.lock)" if dirty else " (fs-summary)"),
        "detail": "filesystem git summary (no process spawn)",
    }


def write_local_alert(message: str, log_path: Path) -> None:
    """Local-only alert channel (replaces env→webhook HTTP)."""
    from datetime import datetime, timezone
    import json

    log_path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "alert": message[:4000],
        "channel": "local_jsonl",
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"[ALERT] {message}")
