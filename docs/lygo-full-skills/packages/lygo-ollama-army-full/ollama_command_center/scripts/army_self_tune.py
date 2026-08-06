#!/usr/bin/env python3
"""
Army self-tune — LOCAL MUTATING hygiene (not read-only).

When self_tune.enabled is true (default **false**), this script may:
  - rewrite army_config.json (with .bak backup)
  - prune/dedupe queued task files
  - write workspace reports + logs
  - optionally run allowlisted stack tools (e.g. haven chart rebuild)

NEVER enables: github_push, hf_write, clawhub_publish, social publish.
NEVER auto-enables planting (removed SkillSpector high-risk path).
"""

from __future__ import annotations

import sys
from pathlib import Path as _P
_SKILL = _P(__file__).resolve().parents[2]
if str(_SKILL) not in sys.path:
    sys.path.insert(0, str(_SKILL))
from _safe_invoke import run_python, run_daemon_thread, git_status_summary, write_local_alert  # noqa: E402

import json
import os
import shutil
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CC = Path(__file__).resolve().parents[1]
ARMY = CC.parent
CONFIG_PATH = CC / "config" / "army_config.json"
WORKSPACE = CC / "workspace"
STATUS_FILE = WORKSPACE / "sentinel_status.json"
OUT = WORKSPACE / "army_self_tune_last_run.json"
LOG = CC / "logs" / "self_tune.log"

sys.path.insert(0, str(CC / "scripts"))
from army_queue_utils import (  # noqa: E402
    cleanup_stale_locks,
    dedupe_by_role,
    dedupe_cron_by_role,
    probe_http_ok,
    probe_tcp_port,
    queue_dirs,
    unique_task_count,
)


def load_json(path: Path, default: dict | None = None) -> dict:
    if not path.is_file():
        return default or {}
    return json.loads(path.read_text(encoding="utf-8"))


def ollama_up() -> bool:
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=4) as resp:
            data = json.loads(resp.read().decode())
        return bool(data.get("models"))
    except Exception:
        return False


def sync_clawhub_expect(cfg: dict, stack: Path) -> list[str]:
    actions: list[str] = []
    skills = stack / "clawhub" / "skills.json"
    if not skills.is_file():
        return actions
    data = json.loads(skills.read_text(encoding="utf-8"))
    profile = cfg.setdefault("system_profile", {})
    expect = profile.setdefault("clawhub_expect", {})
    pub = data.get("count_published")
    if pub and expect.get("count_published") != pub:
        expect["count_published"] = pub
        actions.append(f"clawhub_expect.count_published={pub}")
    slugs = {s.get("slug") for s in data.get("skills", [])}
    req = list(expect.get("required_slugs") or [])
    for must in ("lygo-network-builder", "lygo-kernel-egg-planter", "lygo-protocol-stack-operator"):
        if must in slugs and must not in req:
            req.append(must)
            actions.append(f"required_slugs+={must}")
    expect["required_slugs"] = req
    return actions


def prune_completed_tasks(max_keep: int) -> list[str]:
    actions: list[str] = []
    result_stems: set[str] = set()
    for d in (CC / "results", ARMY / "ollama_results"):
        if not d.is_dir():
            continue
        for p in d.glob("*.result.json"):
            result_stems.add(p.name.replace(".result.json", ""))
        for p in d.glob("*.json"):
            if p.name.endswith(".result.json"):
                continue
            result_stems.add(p.stem)

    removed = 0
    for qdir in (CC / "tasks", ARMY / "ollama_queue"):
        if not qdir.is_dir():
            continue
        for task in list(qdir.glob("*.task.json")):
            tid = task.stem.replace(".task", "")
            if tid in result_stems:
                task.unlink(missing_ok=True)
                removed += 1

    queued = sum(len(list(d.glob("*.task.json"))) for d in (CC / "tasks", ARMY / "ollama_queue") if d.is_dir())
    if queued > max_keep:
        excess = queued - max_keep
        for qdir in (CC / "tasks", ARMY / "ollama_queue"):
            if not qdir.is_dir() or excess <= 0:
                continue
            for task in sorted(qdir.glob("cron-*.task.json"), key=lambda p: p.stat().st_mtime):
                if excess <= 0:
                    break
                task.unlink(missing_ok=True)
                excess -= 1
                removed += 1
        actions.append(f"pruned_queue_overflow removed={removed} target<={max_keep}")
    elif removed:
        actions.append(f"pruned_completed_tasks removed={removed}")
    return actions


def apply_runtime_tuning(cfg: dict, sentinel: dict) -> list[str]:
    actions: list[str] = []
    healthy = bool(sentinel.get("healthy"))
    lattice_ok = (sentinel.get("lattice") or {}).get("ok", False)
    sent = cfg.setdefault("sentinel", {})
    cap = cfg.setdefault("army_capacity", {})
    tune = cfg.get("self_tune") or {}

    want_interval = 300 if healthy else 180
    if sent.get("interval_seconds") != want_interval:
        sent["interval_seconds"] = want_interval
        cfg["poll_seconds"] = want_interval
        actions.append(f"sentinel.interval_seconds={want_interval}")

    if ollama_up():
        if int(cap.get("hb_light_instances", 1)) < 2:
            cap["hb_light_instances"] = 2
            actions.append("hb_light_instances=2")
    else:
        cap["hb_light_instances"] = 1
        actions.append("hb_light_instances=1 (ollama offline)")

    sent["require_ollama_for_healthy"] = False

    planting = cfg.setdefault("planting", {})
    # SkillSpector HARD RULE: never auto-enable planting from self-tune.
    # Force policy flags false on every run so config cannot drift into auto-plant.
    if tune.get("auto_enable_planting"):
        tune["auto_enable_planting"] = False
        actions.append("forced_auto_enable_planting=false (policy refuse)")
    planting["allow_auto_enable"] = False
    # Only pause (disable) when lattice fails — never enable
    if not lattice_ok and tune.get("pause_planting_on_lattice_fail", True):
        if planting.get("enabled"):
            planting["enabled"] = False
            planting["consent"] = False
            actions.append("planting.enabled=false (lattice fail; pause only)")

    # Never flip social or privileged access on
    social = cfg.setdefault("social_publish", {})
    if social.get("enabled") and not social.get("allow_social_pulse"):
        # leave enabled alone if operator set it; do not auto-on pulse
        pass
    access = cfg.setdefault("access", {})
    for k in ("github_push", "hf_write", "clawhub_publish"):
        if access.get(k):
            access[k] = False
            actions.append(f"forced_access.{k}=false")

    # Do not force public/network probes on — operator must set in config
    return actions


def main() -> int:
    cfg = load_json(CONFIG_PATH)
    # Default OFF — operators must set self_tune.enabled true deliberately
    if not cfg.get("self_tune", {}).get("enabled", False):
        print(json.dumps({"skipped": "self_tune.disabled", "note": "set self_tune.enabled=true to allow local config/queue mutation"}))
        return 0

    stack = Path(cfg.get("lygo_stack_root") or os.environ.get("LYGO_STACK_ROOT") or "")
    if not stack:
        stack = Path(r"I:\E Drive\lygo-protocol-stack")
    sentinel = load_json(STATUS_FILE)
    if not sentinel and (CC / "scripts" / "sentinel_heartbeat.py").is_file():
        run_python(CC / "scripts" / "sentinel_heartbeat.py", timeout=240)
        sentinel = load_json(STATUS_FILE)

    actions: list[str] = []
    if (cfg.get("self_tune") or {}).get("sync_clawhub_expect_from_stack", False):
        actions.extend(sync_clawhub_expect(cfg, stack))
    perf = cfg.setdefault("performance", {})
    dirs = queue_dirs(CC, ARMY)
    stale_s = float(perf.get("stale_lock_seconds", 600))
    restored = cleanup_stale_locks(dirs, stale_s)
    if restored:
        actions.append(f"stale_locks_restored={restored}")
    if perf.get("dedupe_cron_by_role", True):
        deduped = dedupe_cron_by_role(dirs)
        if deduped:
            actions.append(f"cron_deduped={deduped}")
    max_per_role = int(perf.get("max_pending_per_role", 1))
    if max_per_role > 0:
        role_deduped = dedupe_by_role(dirs, max_per_role=max_per_role)
        if role_deduped:
            actions.append(f"role_deduped={role_deduped} max_per_role={max_per_role}")

    gw_port = int(perf.get("gateway_port", 18789))
    gw_listen = probe_tcp_port("127.0.0.1", gw_port)
    gw_http = probe_http_ok(f"http://127.0.0.1:{gw_port}/") if gw_listen else False
    perf["gateway_last_probe"] = {
        "port": gw_port,
        "listening": gw_listen,
        "http_ok": gw_http,
    }
    if gw_listen and not gw_http:
        actions.append(f"gateway_port_{gw_port}_listen_no_http")

    max_q = int((cfg.get("self_tune") or {}).get("max_queued_tasks", 30))
    actions.extend(prune_completed_tasks(max_q))
    actions.extend(apply_runtime_tuning(cfg, sentinel))
    perf["queue_unique_tasks"] = unique_task_count(dirs)

    hsc = cfg.get("haven_star_chart") or {}
    # Default rebuild OFF — mutating stack docs only when explicitly enabled
    if hsc.get("rebuild_on_self_tune", False) and (sentinel.get("lattice") or {}).get("ok"):
        builder = stack / "tools" / "build_haven_star_chart.py"
        if builder.is_file():
            cp = run_python(builder, cwd=stack, timeout=120, stack_root=stack)
            if cp.returncode == 0:
                actions.append("haven_star_chart.rebuilt")
            else:
                actions.append("haven_star_chart.rebuild_failed")

    # Final hard clamps before any disk write
    st = cfg.setdefault("self_tune", {})
    st["auto_enable_planting"] = False
    plant = cfg.setdefault("planting", {})
    plant["allow_auto_enable"] = False
    # Never leave planting enabled without consent flag present
    if plant.get("enabled") and not plant.get("consent"):
        plant["enabled"] = False
        actions.append("planting.enabled=false (missing planting.consent)")

    backup = CONFIG_PATH.with_suffix(".json.bak")
    if CONFIG_PATH.is_file():
        shutil.copy2(CONFIG_PATH, backup)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

    report = {
        "signature": "Δ9Φ963-ARMY-SELF-TUNE-v3",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mutating": True,
        "honest_surface": (
            "Mutates army_config.json (+.bak), may prune queue tasks, writes workspace reports/logs. "
            "Never enables planting/social/git/HF/ClawHub. Default self_tune.enabled=false."
        ),
        "actions": actions,
        "healthy": sentinel.get("healthy"),
        "lattice": (sentinel.get("lattice") or {}).get("summary"),
        "queue": sentinel.get("queue"),
        "config_backup": str(backup),
        "verdict": "SELF_TUNED" if actions else "NOOP",
        "policy": {
            "auto_enable_planting": False,
            "planting_allow_auto_enable": False,
            "github_push": False,
            "hf_write": False,
            "clawhub_publish": False,
        },
    }
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{report['timestamp']} | {len(actions)} actions | {actions}\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())