#!/usr/bin/env python3
"""Army planting tick — kernel eggs + scalable registry (consent + lattice gated)."""

from __future__ import annotations

import sys
from pathlib import Path as _P
_SKILL = _P(__file__).resolve().parents[2]
if str(_SKILL) not in sys.path:
    sys.path.insert(0, str(_SKILL))
from _safe_invoke import run_python, run_daemon_thread, git_status_summary, write_local_alert  # noqa: E402

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

CC = Path(__file__).resolve().parents[1]
CONFIG = CC / "config" / "army_config.json"
WORKSPACE = CC / "workspace"


def _cfg() -> dict:
    if CONFIG.is_file():
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    return {}


def _stack() -> Path:
    sys.path.insert(0, str(CC.parent))
    from lygo_stack_root import resolve_stack_root

    return resolve_stack_root(config_path=CONFIG)


def _run(script: Path, args: list[str] | None = None, cwd: Path | None = None, *, env: dict | None = None, timeout: int = 600, stack_root: Path | None = None):
    """Allowlisted in-process run (v0.6.0 — no subprocess)."""
    extra = {}
    if env and env.get("LYGO_STACK_ROOT"):
        extra["LYGO_STACK_ROOT"] = env["LYGO_STACK_ROOT"]
    return run_python(
        script,
        list(args or []),
        cwd=cwd or script.parent,
        timeout=timeout,
        stack_root=stack_root,
        env_extra=extra or None,
    )


def lattice_aligned(stack: Path) -> bool:
    cp = _run(stack / "tools" / "verify_lattice_alignment.py", cwd=stack, timeout=300, stack_root=stack)
    return cp.returncode == 0 and "ALIGNED" in (cp.stdout or "")


def egg_planter() -> dict:
    cfg = _cfg()
    planting = cfg.get("planting") or {}
    stack = _stack()
    out: dict = {
        "signature": "Δ9Φ963-ARMY-EGG-PLANTER-v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "planted": False,
    }
    if not planting.get("enabled", False):
        out["skipped"] = "planting.disabled"
        return out
    if not lattice_aligned(stack):
        out["skipped"] = "lattice_not_aligned"
        return out

    skill_scripts = stack / "clawhub" / "mirrors" / "lygo-kernel-egg-planter" / "scripts"
    preflight = skill_scripts / "preflight.py"
    smoke = skill_scripts / "smoke_test.py"
    plant = skill_scripts / "plant_with_consent.py"
    env = os.environ.copy()
    env["LYGO_STACK_ROOT"] = str(stack)

    if preflight.is_file():
        # planter scripts under skill mirror — allow if under stack
        cp = run_python(preflight, cwd=skill_scripts, timeout=120, stack_root=stack, env_extra={"LYGO_STACK_ROOT": str(stack)})
        out["preflight"] = cp.returncode == 0
        if cp.returncode == 2 and "not allowlisted" in (cp.stderr or ""):
            out["preflight_note"] = "preflight skipped (not in STACK_TOOL_ALLOW; run planter skill directly)"
    if smoke.is_file():
        cp = run_python(smoke, cwd=skill_scripts, timeout=180, stack_root=stack, env_extra={"LYGO_STACK_ROOT": str(stack)})
        out["smoke_test"] = cp.returncode == 0

    consent = bool(planting.get("consent")) or env.get("LYGO_EGG_PLANT_CONSENT", "").lower() in ("yes", "1", "true")
    if consent and plant.is_file():
        env["LYGO_EGG_PLANT_CONSENT"] = "yes"
        surfaces = ",".join(planting.get("egg_surfaces") or ["local", "registry", "stubs"])
        args = ["--i-consent", "--stack-root", str(stack), "--surfaces", surfaces]
        if planting.get("local_only_anchor", True):
            args.append("--local-only")
        cp = run_python(plant, args, cwd=skill_scripts, timeout=900, stack_root=stack, env_extra={"LYGO_STACK_ROOT": str(stack)})
        out["plant_exit"] = cp.returncode
        out["planted"] = cp.returncode == 0
        if cp.stdout:
            out["plant_tail"] = cp.stdout[-2000:]
        if cp.returncode == 2:
            out["plant_note"] = "use lygo-kernel-egg-planter skill for plant_with_consent (allowlisted path)"
    else:
        out["skipped_plant"] = "consent_false"

    verify = stack / "tools" / "verify_kernel_eggs.py"
    if verify.is_file():
        cp = _run(verify, cwd=stack, timeout=120, stack_root=stack)
        out["kernel_eggs_verify"] = cp.returncode == 0
    return out


def registry_planter() -> dict:
    cfg = _cfg()
    planting = cfg.get("planting") or {}
    stack = _stack()
    out: dict = {
        "signature": "Δ9Φ963-ARMY-REGISTRY-PLANTER-v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "registered": False,
    }
    if not planting.get("enabled", False):
        out["skipped"] = "planting.disabled"
        return out
    if not lattice_aligned(stack):
        out["skipped"] = "lattice_not_aligned"
        return out

    cli = stack / "tools" / "cas_registry_cli.py"
    verify = stack / "tools" / "verify_registry.py"
    if verify.is_file():
        # verify_registry may not be in STACK_TOOL_ALLOW — soft-fail
        cp = run_python(verify, cwd=stack, timeout=180, stack_root=stack)
        out["registry_verify"] = cp.returncode == 0
        if cp.returncode == 2:
            out["registry_note"] = "verify_registry not allowlisted; install stack tool path or run manually"

    rel = planting.get("registry_smoke_file") or "docs/STACK_STATUS.md"
    target = stack / rel
    if not target.is_file():
        target = stack / "docs" / "AGENT_MEMORY_SNAPSHOT.json"
    if cli.is_file() and target.is_file():
        meta = json.dumps({"name": "army-lattice-plant", "source": rel, "army": True})
        cp = run_python(
            cli,
            ["build", "--file", str(target), "--metadata", meta, "--no-p6", "--verify"],
            cwd=stack,
            timeout=600,
            stack_root=stack,
        )
        out["register_exit"] = cp.returncode
        out["registered"] = cp.returncode == 0
        out["file"] = str(target)
        if cp.returncode == 2:
            out["register_note"] = "cas_registry_cli not in STACK_TOOL_ALLOW — run from stack tools manually"
    else:
        out["skipped_register"] = "missing_cli_or_file"
    return out


def main() -> int:
    mode = (sys.argv[1] if len(sys.argv) > 1 else "all").lower()
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    report: dict = {"timestamp": datetime.now(timezone.utc).isoformat()}

    if mode in ("egg", "all"):
        report["egg"] = egg_planter()
        (WORKSPACE / "egg_plant_last_run.json").write_text(json.dumps(report["egg"], indent=2), encoding="utf-8")
    if mode in ("registry", "all"):
        report["registry"] = registry_planter()
        (WORKSPACE / "registry_plant_last_run.json").write_text(
            json.dumps(report["registry"], indent=2), encoding="utf-8"
        )

    print(json.dumps(report, indent=2))
    ok = True
    for k in ("egg", "registry"):
        if k in report:
            block = report[k]
            if block.get("skipped"):
                continue
            if k == "egg" and planting_failed(block):
                ok = False
            if k == "registry" and block.get("register_exit", 0) not in (0, None) and not block.get("skipped_register"):
                if block.get("register_exit", 1) != 0:
                    ok = False
    return 0 if ok else 1


def planting_failed(block: dict) -> bool:
    if block.get("planted") is False and not block.get("skipped_plant") and not block.get("skipped"):
        return True
    if block.get("kernel_eggs_verify") is False:
        return True
    return False


if __name__ == "__main__":
    raise SystemExit(main())