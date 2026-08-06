#!/usr/bin/env python3
"""LYGO Army + USB daemon health suite (read-only probes + optional queue smoke)."""

from __future__ import annotations

import sys
from pathlib import Path as _P
_SKILL = _P(__file__).resolve().parents[2]
if str(_SKILL) not in sys.path:
    sys.path.insert(0, str(_SKILL))
from _safe_invoke import run_python, run_daemon_thread, git_status_summary, write_local_alert  # noqa: E402

import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
CC = HERE.parent
ARMY = CC.parent
CONFIG = CC / "config" / "army_config.json"
OUT = CC / "workspace" / "army_health_last_run.json"

sys.path.insert(0, str(HERE))
from army_queue_utils import (  # noqa: E402
    dedupe_by_role,
    dedupe_cron_by_role,
    probe_http_ok,
    probe_tcp_port,
    queue_dirs,
    unique_task_count,
)


def load_config() -> dict:
    if CONFIG.is_file():
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    return {}


def probe_ollama() -> dict:
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5) as resp:
            data = json.loads(resp.read().decode())
        models = [m.get("name") for m in data.get("models", [])]
        return {"ok": bool(models), "models": models[:12]}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def probe_gateway(port: int) -> dict:
    listening = probe_tcp_port("127.0.0.1", port)
    http_ok = probe_http_ok(f"http://127.0.0.1:{port}/") if listening else False
    return {"port": port, "listening": listening, "http_ok": http_ok}


def list_daemon_processes() -> dict:
    roles: list[str] = []
    count = 0
    try:
        ps = type('R', (), {'returncode': 0, 'stdout': '', 'stderr': ''})()
        for line in (ps.stdout or "").splitlines():
            if "ollama_daemon.py" not in line and "lyra_ollama_daemon.py" not in line:
                continue
            count += 1
            m = re.search(r"--role\s+(\S+)", line)
            if m:
                roles.append(m.group(1))
    except Exception as exc:
        return {"count": count, "roles": roles, "error": str(exc)}
    return {"count": count, "roles": roles, "unique_roles": sorted(set(roles))}


def run_self_tune() -> dict:
    script = HERE / "army_self_tune.py"
    cp = run_python(script, timeout=180)
    try:
        report = json.loads(cp.stdout or "{}")
    except json.JSONDecodeError:
        report = {"raw": (cp.stdout or "")[-1500:]}
    return {"exit_code": cp.returncode, "verdict": report.get("verdict"), "actions": len(report.get("actions", []))}


def run_sentinel() -> dict:
    script = HERE / "sentinel_heartbeat.py"
    cp = run_python(script, timeout=240)
    status_path = CC / "workspace" / "sentinel_status.json"
    status = {}
    if status_path.is_file():
        status = json.loads(status_path.read_text(encoding="utf-8"))
    return {
        "exit_code": cp.returncode,
        "healthy": status.get("healthy"),
        "lattice": (status.get("lattice") or {}).get("summary"),
    }


def smoke_lattice_task(timeout: float = 120.0) -> dict:
    """Enqueue one lattice-check, wait for result (stack-worker or lattice-check daemon)."""
    tasks = CC / "tasks"
    results = CC / "results"
    tasks.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)
    tid = f"health-lattice-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    task_path = tasks / f"{tid}.task.json"
    task_path.write_text(json.dumps({"id": tid, "role": "lattice-check", "payload": {}}), encoding="utf-8")

    deadline = time.time() + timeout
    result_path = results / f"{tid}.result.json"
    while time.time() < deadline:
        if result_path.is_file():
            blob = json.loads(result_path.read_text(encoding="utf-8"))
            aligned = (blob.get("result") or {}).get("aligned")
            return {"ok": aligned is True, "task_id": tid, "aligned": aligned}
        time.sleep(2.0)
    return {"ok": False, "task_id": tid, "error": "timeout waiting for result"}


def main() -> int:
    cfg = load_config()
    perf = cfg.get("performance") or {}
    dirs = queue_dirs(CC, ARMY)

    before = unique_task_count(dirs)
    pruned = dedupe_cron_by_role(dirs)
    max_per_role = int(perf.get("max_pending_per_role", 1))
    if max_per_role > 0:
        pruned += dedupe_by_role(dirs, max_per_role=max_per_role)
    after = unique_task_count(dirs)

    report = {
        "signature": "Δ9Φ963-ARMY-HEALTH-v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ollama": probe_ollama(),
        "gateway": probe_gateway(int(perf.get("gateway_port", 18789))),
        "queue": {
            "unique_tasks_before": before,
            "unique_tasks_after": after,
            "cron_deduped": pruned,
        },
        "daemons": list_daemon_processes(),
        "self_tune": run_self_tune(),
        "sentinel": run_sentinel(),
    }

    if "--smoke" in sys.argv:
        report["lattice_smoke"] = smoke_lattice_task()

    checks = [
        report["ollama"]["ok"],
        report["sentinel"].get("healthy") is not False,
        report["self_tune"]["exit_code"] == 0,
    ]
    if "--smoke" in sys.argv:
        checks.append(report.get("lattice_smoke", {}).get("ok") is True)

    report["all_pass"] = all(checks)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())