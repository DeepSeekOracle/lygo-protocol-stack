#!/usr/bin/env python3
"""Army skill self-check — allowlist + policy + 0.8.3 gate smoke (no autonomous loop)."""
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
    report["checks"]["version_083"] = "0.8.3" in skill
    report["checks"]["honest_strict_allowlist"] = "STRICT" in skill or "strict" in skill.lower()

    import _safe_invoke as si

    fake = ROOT / "not_allowlisted_evil.py"
    try:
        fake.write_text("# evil\n", encoding="utf-8")
        report["checks"]["refuses_arbitrary_skill_py"] = not si.allowed_script(fake)
    finally:
        fake.unlink(missing_ok=True)

    ok_script = ROOT / "ollama_daemon.py"
    report["checks"]["allows_named_daemon"] = si.allowed_script(ok_script)

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

    bak = ROOT / "ollama_command_center" / "config" / "army_config.json.bak"
    report["checks"]["no_bak_config"] = not bak.is_file()

    ex = ROOT / "ollama_command_center" / "config" / "army_config.example.json"
    if ex.is_file():
        cfg = json.loads(ex.read_text(encoding="utf-8"))
        report["checks"]["example_planting_off"] = not (cfg.get("planting") or {}).get("enabled")
        report["checks"]["example_self_tune_off"] = not (cfg.get("self_tune") or {}).get("enabled")
        report["checks"]["example_sentinel_off"] = not (cfg.get("sentinel") or {}).get("enabled")
        report["checks"]["example_idle_off"] = not (cfg.get("idle_guardian") or {}).get("enabled")
        report["checks"]["example_probe_public_off"] = not (cfg.get("sentinel") or {}).get(
            "probe_public_pages"
        )
        report["checks"]["example_no_auto_plant"] = not (cfg.get("self_tune") or {}).get(
            "auto_enable_planting"
        )
        report["checks"]["example_no_notifications"] = "notifications" not in cfg

    sup = (
        ROOT / "ollama_command_center" / "scripts" / "army_autonomous_supervisor.py"
    ).read_text(encoding="utf-8", errors="replace")
    report["checks"]["supervisor_dual_gate"] = (
        "LYGO_ARMY_AUTONOMOUS" in sup and "LYGO_ARMY_I_CONSENT" in sup
    )

    col = (ROOT / "genesis_console" / "collector.py").read_text(encoding="utf-8", errors="replace")
    report["checks"]["collector_local_default"] = "LYGO_GENESIS_PROBE_PUBLIC" in col
    report["checks"]["collector_no_default_discord"] = "LYGO_GENESIS_OPS_DISCORD" in col

    hc = (
        ROOT / "ollama_command_center" / "scripts" / "army_health_check.py"
    ).read_text(encoding="utf-8", errors="replace")
    report["checks"]["health_probes_only"] = "probes_only" in hc and "--run-self-tune" in hc

    cron = (
        ROOT / "ollama_command_center" / "scripts" / "army_cron_once.py"
    ).read_text(encoding="utf-8", errors="replace")
    report["checks"]["cron_no_token_saver_exec"] = "token_saver_once" not in cron
    # SAFE_CRON_ROLES block must not list self-tune (opt-in is SELF_TUNE_ROLE)
    import re as _re

    m = _re.search(r"SAFE_CRON_ROLES\s*=\s*\[(.*?)\]", cron, _re.S)
    safe_block = m.group(1) if m else ""
    report["checks"]["cron_self_tune_not_safe_list"] = "self-tune" not in safe_block
    report["checks"]["cron_self_tune_opt_in"] = "SELF_TUNE_ROLE" in cron
    report["checks"]["cron_public_pages_not_safe"] = "public-pages-check" not in safe_block

    hb = (
        ROOT / "ollama_command_center" / "scripts" / "heartbeats_only.py"
    ).read_text(encoding="utf-8", errors="replace")
    report["checks"]["heartbeats_collector_opt_in"] = "LYGO_GENESIS_COLLECT" in hb

    desk = (ROOT / "install_desktop_launchers.ps1").read_text(encoding="utf-8", errors="replace")
    report["checks"]["desktop_install_gate"] = "LYGO_ARMY_INSTALL_DESKTOP" in desk
    # Must not auto-assign consent env in generated .bat body
    report["checks"]["desktop_no_inject_consent"] = (
        "set LYGO_ARMY_AUTONOMOUS=1\n" not in desk.replace("\r\n", "\n")
        and "set LYGO_ARMY_I_CONSENT=1\n" not in desk.replace("\r\n", "\n")
        and "set LYGO_ARMY_AUTONOMOUS=1\r" not in desk
    )

    gen = (ROOT / "install_genesis_desktop.ps1").read_text(encoding="utf-8", errors="replace")
    report["checks"]["genesis_install_gate"] = "LYGO_ARMY_INSTALL_DESKTOP" in gen

    # daemon gates
    daemon = (ROOT / "ollama_daemon.py").read_text(encoding="utf-8", errors="replace")
    report["checks"]["daemon_gate_helper"] = "def _gated" in daemon
    report["checks"]["daemon_plant_gate"] = "planting.enabled" in daemon or "allow_privileged_roles" in daemon

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

    # process_task gate smoke (ignore live steward config — force safe gates)
    try:
        import ollama_daemon as od

        od.load_army_cfg = lambda: {
            "sentinel": {"probe_public_pages": False, "enabled": False},
            "self_tune": {"enabled": False},
            "planting": {"enabled": False, "consent": False},
            "access": {"allow_privileged_roles": False},
            "social_publish": {"enabled": False, "allow_social_pulse": False},
        }
        r = od.process_task({"id": "t", "role": "public-pages-check", "payload": {}}, "llama3.2:1b")
        report["checks"]["daemon_public_pages_gated"] = bool((r.get("result") or {}).get("gated"))
        r2 = od.process_task({"id": "t2", "role": "self-tune", "payload": {}}, "llama3.2:1b")
        report["checks"]["daemon_self_tune_gated"] = bool((r2.get("result") or {}).get("gated"))
        r3 = od.process_task({"id": "t3", "role": "egg-planter", "payload": {}}, "llama3.2:1b")
        report["checks"]["daemon_egg_gated"] = bool((r3.get("result") or {}).get("gated"))
    except Exception as e:
        report["checks"]["daemon_public_pages_gated"] = False
        report["checks"]["daemon_self_tune_gated"] = False
        report["checks"]["daemon_egg_gated"] = False
        report["daemon_err"] = str(e)[:120]

    report["ok"] = all(bool(v) for v in report["checks"].values())
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
