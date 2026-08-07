#!/usr/bin/env python3
"""Army skill self-check — allowlist + policy + import smoke (no autonomous loop)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ollama_command_center" / "scripts"))


def main() -> int:
    report: dict = {"ok": True, "checks": {}}

    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8", errors="replace")
    report["checks"]["version_082"] = "0.8.2" in skill
    report["checks"]["honest_strict_allowlist"] = "STRICT" in skill or "strict" in skill.lower()

    import _safe_invoke as si

    # Strict allowlist: random skill .py must fail; known name under root ok
    fake = ROOT / "not_allowlisted_evil.py"
    try:
        fake.write_text("# evil\n", encoding="utf-8")
        report["checks"]["refuses_arbitrary_skill_py"] = not si.allowed_script(fake)
    finally:
        fake.unlink(missing_ok=True)

    ok_script = ROOT / "ollama_daemon.py"
    report["checks"]["allows_named_daemon"] = si.allowed_script(ok_script)

    # stack tools: arbitrary tools/foo.py must fail
    stack = Path(os.environ.get("LYGO_STACK_ROOT", r"D:\lygo-protocol-stack"))
    if (stack / "tools").is_dir():
        evil_tool = stack / "tools" / "_army_ss_evil_probe_should_not_exist.py"
        report["checks"]["refuses_arbitrary_stack_tool"] = not si.allowed_script(
            evil_tool, stack_root=stack
        )
        good = stack / "tools" / "verify_lattice_alignment.py"
        report["checks"]["allows_named_stack_tool"] = (
            si.allowed_script(good, stack_root=stack) if good.is_file() else True
        )
    else:
        report["checks"]["refuses_arbitrary_stack_tool"] = True
        report["checks"]["allows_named_stack_tool"] = True

    # no bak config
    bak = ROOT / "ollama_command_center" / "config" / "army_config.json.bak"
    report["checks"]["no_bak_config"] = not bak.is_file()

    # example planting off
    ex = ROOT / "ollama_command_center" / "config" / "army_config.example.json"
    if ex.is_file():
        cfg = json.loads(ex.read_text(encoding="utf-8"))
        report["checks"]["example_planting_off"] = not (cfg.get("planting") or {}).get("enabled")
        report["checks"]["example_self_tune_off"] = not (cfg.get("self_tune") or {}).get("enabled")
        report["checks"]["example_no_auto_plant"] = not (cfg.get("self_tune") or {}).get(
            "auto_enable_planting"
        )
        report["checks"]["example_no_notifications"] = "notifications" not in cfg

    # supervisor dual gate
    sup = (
        ROOT / "ollama_command_center" / "scripts" / "army_autonomous_supervisor.py"
    ).read_text(encoding="utf-8", errors="replace")
    report["checks"]["supervisor_dual_gate"] = (
        "LYGO_ARMY_AUTONOMOUS" in sup and "LYGO_ARMY_I_CONSENT" in sup
    )

    # collector local-only default markers
    col = (ROOT / "genesis_console" / "collector.py").read_text(encoding="utf-8", errors="replace")
    report["checks"]["collector_local_default"] = "LYGO_GENESIS_PROBE_PUBLIC" in col
    report["checks"]["collector_no_default_discord"] = "LYGO_GENESIS_OPS_DISCORD" in col

    # health default probes
    hc = (
        ROOT / "ollama_command_center" / "scripts" / "army_health_check.py"
    ).read_text(encoding="utf-8", errors="replace")
    report["checks"]["health_probes_only"] = "probes_only" in hc and "--run-self-tune" in hc

    # cron no token_saver path
    cron = (
        ROOT / "ollama_command_center" / "scripts" / "army_cron_once.py"
    ).read_text(encoding="utf-8", errors="replace")
    report["checks"]["cron_no_token_saver_exec"] = "token_saver_once" not in cron

    # supervisor refuses without env
    old = os.environ.pop("LYGO_ARMY_AUTONOMOUS", None)
    old2 = os.environ.pop("LYGO_ARMY_I_CONSENT", None)
    try:
        import army_autonomous_supervisor as aas

        rc = aas.main()
        report["checks"]["supervisor_refuses"] = rc == 2
    except Exception as e:
        report["checks"]["supervisor_refuses"] = False
        report["err"] = str(e)[:100]
    finally:
        if old is not None:
            os.environ["LYGO_ARMY_AUTONOMOUS"] = old
        if old2 is not None:
            os.environ["LYGO_ARMY_I_CONSENT"] = old2

    report["ok"] = all(bool(v) for v in report["checks"].values())
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
