#!/usr/bin/env python3
"""Aggregate LYGO lattice data for Genesis Console (GitHub, HF, local checks, army)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
STATUS_PATH = DATA_DIR / "status.json"
ARMY = ROOT.parent
STACK = Path(os.environ.get("LYGO_STACK_ROOT", r"I:\E Drive\lygo-protocol-stack"))
CC = ARMY / "ollama_command_center"
LYRA_CORE = Path(os.environ.get("LYRA_CORE_ROOT", r"I:\E Drive\LYRA_CORE"))
JOY_API_PORT = int(os.environ.get("LYGO_JOY_API_PORT", "9965"))
GENESIS_PORT = int(os.environ.get("LYGO_GENESIS_PORT", "9963"))
PAGES = "https://deepseekoracle.github.io/lygo-protocol-stack"

LINKS = {
    "github_stack": "https://github.com/DeepSeekOracle/lygo-protocol-stack",
    "github_pages": "https://deepseekoracle.github.io/lygo-protocol-stack/",
    "hf_dataset": "https://huggingface.co/datasets/DeepSeekOracle/lygo-protocol-stack",
    "hf_space": "https://huggingface.co/spaces/DeepSeekOracle/LYGO-Resonance-Engine",
    "clawhub": "https://clawhub.ai/deepseekoracle",
    "clawhub_operator": "https://clawhub.ai/deepseekoracle/lygo-protocol-stack-operator",
    "clawhub_mesh": "https://clawhub.ai/deepseekoracle/lygo-mesh-deploy",
    "grokipedia": "https://grokipedia.com/page/lygo-protocol-stack",
    "resonance_docs": "https://deepseekoracle.github.io/Excavationpro/LYGORESONANCE.html",
    "biometric_harness_pages": "https://deepseekoracle.github.io/lygo-protocol-stack/BiometricEntropyHarness.html",
    "biometric_harness_excavationpro": "https://deepseekoracle.github.io/Excavationpro/BiometricEntropyHarness.html",
    "excavationpro": "https://github.com/DeepSeekOracle/Excavationpro",
    "discord_dev": "https://discord.com/developers/applications",
    "clawnch": "https://clawnch.ai",
    "moltx": "https://moltx.io",
    "haven_star_chart": f"{PAGES}/HavenStarChart.html",
    "champions_hub": "https://deepseekoracle.github.io/Excavationpro/LYGO-Network/champions.html",
    "joy_snapshot_pages": f"{PAGES}/joy_loop/joy_loop_snapshot.json",
    "clawhub_joy_loop": "https://clawhub.ai/deepseekoracle/lygo-joy-loop",
    "compass": f"{PAGES}/tools/LYGO_Compass_Master.html",
    "genesis_local": f"http://127.0.0.1:{GENESIS_PORT}/",
    "joy_architect_local": f"http://127.0.0.1:{JOY_API_PORT}/architect",
    "army_dashboard_local": f"http://127.0.0.1:{GENESIS_PORT}/#army",
    "lygo_claw_github": "https://github.com/DeepSeekOracle/lygo-claw",
    "lygo_claw_pages": "https://deepseekoracle.github.io/lygo-protocol-stack/LYGO_CLAW.html",
    "buildr_daemon_health": "http://127.0.0.1:9630/health",
    "buildr_usb_standalone_doc": "https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/docs/BUILDR_USB_STANDALONE.md",
}


def _get_json(url: str, timeout: int = 20) -> dict | list | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "LYGO-Genesis-Console/1.0", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def github_repo() -> dict:
    data = _get_json("https://api.github.com/repos/DeepSeekOracle/lygo-protocol-stack")
    if not data:
        return {"ok": False}
    return {
        "ok": True,
        "name": data.get("full_name"),
        "default_branch": data.get("default_branch"),
        "updated_at": data.get("updated_at"),
        "pushed_at": data.get("pushed_at"),
        "stars": data.get("stargazers_count"),
        "open_issues": data.get("open_issues_count"),
        "html_url": data.get("html_url"),
    }


def github_last_commit() -> dict:
    data = _get_json(
        "https://api.github.com/repos/DeepSeekOracle/lygo-protocol-stack/commits?per_page=1"
    )
    if not data or not isinstance(data, list) or not data:
        return {"ok": False}
    c = data[0]
    return {
        "ok": True,
        "sha": (c.get("sha") or "")[:7],
        "message": (c.get("commit", {}).get("message") or "")[:120],
        "date": c.get("commit", {}).get("author", {}).get("date"),
    }


def hf_space() -> dict:
    data = _get_json("https://huggingface.co/api/spaces/DeepSeekOracle/LYGO-Resonance-Engine")
    if not data:
        return {"ok": False}
    runtime = data.get("runtime") or {}
    stage = runtime.get("stage") or data.get("stage") or "unknown"
    stage_ok = stage in (
        "RUNNING",
        "BUILDING",
        "STARTING",
        "PAUSED",
        "APP_STARTING",
        "RUNNING_APP_STARTING",
    )
    return {
        "ok": stage_ok,
        "id": data.get("id"),
        "stage": stage,
        "sdk": data.get("sdk"),
        "last_modified": data.get("lastModified") or data.get("last_modified"),
    }


def hf_dataset() -> dict:
    data = _get_json("https://huggingface.co/api/datasets/DeepSeekOracle/lygo-protocol-stack")
    if not data:
        return {"ok": False}
    siblings = data.get("siblings") or []
    total = sum(int(s.get("size") or 0) for s in siblings if isinstance(s, dict))
    return {
        "ok": True,
        "id": data.get("id"),
        "last_modified": data.get("lastModified") or data.get("last_modified"),
        "files": len(siblings),
        "size_bytes": total,
    }


def run_lattice() -> dict:
    script = STACK / "tools" / "verify_lattice_alignment.py"
    if not script.is_file():
        return {"ok": False, "detail": "missing verify script"}
    cp = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(STACK),
        capture_output=True,
        text=True,
        timeout=180,
    )
    aligned = cp.returncode == 0 and "ALIGNED" in (cp.stdout or "")
    return {"ok": aligned, "summary": "ALIGNED" if aligned else "NEEDS_FIX", "exit_code": cp.returncode}


def local_git() -> dict:
    if not (STACK / ".git").is_dir():
        return {"ok": True, "detail": "no git"}
    cp = subprocess.run(["git", "log", "-1", "--oneline"], cwd=str(STACK), capture_output=True, text=True, timeout=30)
    st = subprocess.run(["git", "status", "-sb"], cwd=str(STACK), capture_output=True, text=True, timeout=30)
    lines = [ln for ln in (st.stdout or "").splitlines() if ln.strip()]
    dirty = len(lines) > 1 or any(
        ln.startswith("??") or ln.startswith(" M") or ln.startswith("M ") for ln in lines[1:]
    )
    return {"ok": True, "head": (cp.stdout or "").strip(), "dirty": dirty, "branch_line": lines[0] if lines else ""}


def clawhub_index() -> dict:
    p = STACK / "clawhub" / "skills.json"
    if not p.is_file():
        return {"ok": False}
    d = json.loads(p.read_text(encoding="utf-8"))
    watch = {
        "lygo-protocol-stack-operator",
        "lygo-mesh-deploy",
        "lygo-docker-deploy",
        "lygo-alignment-badge",
        "lygo-joy-loop",
        "lygo-ollama-army",
        "lygo-kernel-egg-planter",
        "lygo-network-builder",
    }
    versions = {}
    for s in d.get("skills", []):
        if s.get("slug") in watch:
            versions[s["slug"]] = s.get("version")
    return {
        "ok": True,
        "published": d.get("count_published"),
        "mirrored": d.get("count_mirrored"),
        "operator": any(s.get("slug") == "lygo-protocol-stack-operator" for s in d.get("skills", [])),
        "versions": versions,
    }


def phase5_metrics() -> dict:
    sim = STACK / "tests" / "mesh_scale_last_run.json"
    live = STACK / "tests" / "mesh_live_convergence_last_run.json"
    out = {"sim_rounds": None, "live_rounds": None, "phase5_live": False}
    if sim.is_file():
        try:
            s = json.loads(sim.read_text(encoding="utf-8"))
            out["sim_rounds"] = s.get("convergence_rounds")
            out["sim_ok"] = s.get("under_10_rounds")
        except Exception:
            pass
    if live.is_file():
        try:
            l = json.loads(live.read_text(encoding="utf-8"))
            out["live_rounds"] = l.get("convergence_rounds")
            out["phase5_live"] = bool(l.get("phase5_live_complete"))
        except Exception:
            pass
    return out


def twin_gate() -> dict:
    p = STACK / "tests" / "twin_gate_vector_suite_last_run.json"
    if not p.is_file():
        return {"ok": False}
    d = json.loads(p.read_text(encoding="utf-8"))
    return {
        "ok": d.get("verdict_match_count") == d.get("total"),
        "match": f"{d.get('verdict_match_count')}/{d.get('total')}",
        "delta_phi": d.get("mean_abs_delta_phi"),
    }


def army_state() -> dict:
    queues = [
        ARMY / "ollama_queue",
        CC / "tasks",
    ]
    results = [
        ARMY / "ollama_results",
        CC / "results",
    ]
    q = sum(len(list(p.glob("*.task.json"))) for p in queues if p.is_dir())
    r = sum(len(list(p.glob("*.json"))) for p in results if p.is_dir())
    sentinel = CC / "workspace" / "sentinel_status.json"
    last = None
    if sentinel.is_file():
        try:
            last = json.loads(sentinel.read_text(encoding="utf-8")).get("timestamp")
        except Exception:
            pass
    ollama_ok = False
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=3) as resp:
            ollama_ok = bool(json.loads(resp.read()).get("models"))
    except Exception:
        pass
    return {"queued": q, "results": r, "last_sentinel": last, "ollama_online": ollama_ok}


def ops_discord_crypto() -> dict:
    script = LYRA_CORE / "lygo_ops_status.py"
    if not script.is_file():
        return {"ok": False, "detail": "missing lygo_ops_status.py"}
    if str(LYRA_CORE) not in sys.path:
        sys.path.insert(0, str(LYRA_CORE))
    try:
        import lygo_ops_status  # noqa: WPS433

        payload = lygo_ops_status.collect_ops_status()
        d = payload.get("discord") or {}
        c = payload.get("crypto") or {}
        healthy = bool(d.get("online") or d.get("api_me", {}).get("ok"))
        return {"ok": True, "healthy": healthy, "discord": d, "crypto": c, "integrations": payload.get("integrations")}
    except Exception as exc:
        return {"ok": False, "detail": str(exc)[:200]}


def p0_golden() -> dict:
    p = STACK / "protocol0_byte_entropy_filter" / "fixtures" / "p0_canonical.sha256"
    if not p.is_file():
        return {"ok": False}
    return {"ok": True, "sha256": p.read_text(encoding="utf-8").strip()[:16] + "…"}


def _http_probe(url: str, timeout: float = 18.0) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "LYGO-Genesis-Console/3.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {"url": url, "status": resp.status, "ok": 200 <= resp.status < 400}
    except urllib.error.HTTPError as e:
        return {"url": url, "status": e.code, "ok": False}
    except Exception as exc:
        return {"url": url, "status": None, "ok": False, "error": str(exc)[:80]}


def internet_lattice() -> dict:
    """LYRA six public checks (+ canonical Haven); HTTP only."""
    specs = [
        ("champion_registry", f"{PAGES}/ChampionEggRegistry.json"),
        ("joy_loop_snapshot", f"{PAGES}/joy_loop/joy_loop_snapshot.json"),
        ("joy_loop_registry", f"{PAGES}/JoyLoopRegistry.json"),
        ("champions_hub", LINKS["champions_hub"]),
        ("clawhub_joy_loop", LINKS["clawhub_joy_loop"]),
        ("haven_alias", f"{PAGES}/haven_star_chart_data.json"),
    ]
    rows = [_http_probe(u) for _, u in specs]
    for row, (sid, _) in zip(rows, specs):
        row["id"] = sid
    lyra_six = all(r["ok"] for r in rows)
    return {"ok": lyra_six, "lyra_six_of_six": lyra_six, "endpoints": rows}


def joy_loop() -> dict:
    snap_path = STACK / "docs" / "joy_loop" / "joy_loop_snapshot.json"
    out: dict = {
        "snapshot_ok": False,
        "live_ok": False,
        "architect_url": LINKS["joy_architect_local"],
        "port": JOY_API_PORT,
    }
    if snap_path.is_file():
        try:
            snap = json.loads(snap_path.read_text(encoding="utf-8"))
            out.update(
                {
                    "snapshot_ok": True,
                    "signature": snap.get("signature"),
                    "protocol": snap.get("protocol"),
                    "beat_count": snap.get("beat_count"),
                    "swarm_joy_score": snap.get("swarm_joy_score"),
                    "champion_count": snap.get("champion_count"),
                }
            )
        except (json.JSONDecodeError, OSError):
            pass
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{JOY_API_PORT}/api/joy",
            headers={"User-Agent": "LYGO-Genesis-Console/3.0"},
        )
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            live = json.loads(resp.read().decode())
            out["live_ok"] = True
            out["live_swarm_joy"] = live.get("swarm_joy_score")
            out["live_beat_count"] = live.get("beat_count")
            out["live_champion_count"] = live.get("champion_count")
    except Exception:
        out["live_ok"] = False
    return out


def ensure_sentinel_fresh(max_age_sec: int = 420) -> None:
    script = CC / "scripts" / "sentinel_heartbeat.py"
    sentinel = CC / "workspace" / "sentinel_status.json"
    if not script.is_file():
        return
    stale = True
    if sentinel.is_file():
        try:
            ts = json.loads(sentinel.read_text(encoding="utf-8")).get("timestamp", "")
            if ts:
                from datetime import datetime

                then = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                age = (datetime.now(timezone.utc) - then).total_seconds()
                stale = age > max_age_sec
        except Exception:
            pass
    if stale:
        subprocess.run(
            [sys.executable, str(script)],
            cwd=str(CC),
            capture_output=True,
            text=True,
            timeout=200,
            check=False,
        )


def resolve_buildr_key_root() -> Path | None:
    env = os.environ.get("LYGO_BUILDER_KEY_ROOT")
    if env and (Path(env) / "verify_bootstrap.py").is_file():
        return Path(env)
    for letter in "DEFGHIJKLMNOPQRSTUVWXYZ":
        for sub in ("LYGO_BUILDER_KEY", ""):
            p = Path(f"{letter}:\\") / sub if sub else Path(f"{letter}:\\")
            if (p / "verify_bootstrap.py").is_file() and (p / "phase2" / "buildr_usb_daemon.py").is_file():
                return p
    overlay = Path(r"I:\E Drive\LYGO_BUILDR_USB")
    if (overlay / "verify_bootstrap.py").is_file():
        return overlay
    return None


def buildr_usb_status() -> dict:
    root = resolve_buildr_key_root()
    if not root:
        return {"ok": False, "detail": "USB key root not found"}
    bench = root / "verify" / "buildr_benchmark_last_run.json"
    standalone = root / "scripts" / "verify_standalone_usb.py"
    daemon_ok = False
    try:
        with urllib.request.urlopen("http://127.0.0.1:9630/health", timeout=2) as resp:
            d = json.loads(resp.read().decode())
            daemon_ok = bool(d.get("ok"))
    except Exception:
        pass
    bench_summary = None
    if bench.is_file():
        try:
            b = json.loads(bench.read_text(encoding="utf-8"))
            bench_summary = b.get("summary")
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "ok": True,
        "key_root": str(root),
        "daemon_health_ok": daemon_ok,
        "benchmark_summary": bench_summary,
        "has_standalone_verify": standalone.is_file(),
    }


def quick_commands() -> list[dict]:
    """Copy-paste commands for Genesis dashboard (BUILDR USB, Claw, army, retail)."""
    key = resolve_buildr_key_root()
    key_s = str(key) if key else r"E:\LYGO_BUILDER_KEY"
    overlay = r"I:\E Drive\LYGO_BUILDR_USB"
    claw = r"I:\E Drive\lygo-claw"
    stack = str(STACK)
    cc = str(CC / "scripts")
    exports = r"I:\E Drive\LYGO_BUILDR_EXPORTS"
    return [
        {"group": "Genesis / Army", "label": "Army hourly cron (once)", "cmd": f'cd "{cc}" && python army_cron_once.py'},
        {"group": "Genesis / Army", "label": "Genesis collector refresh", "cmd": f'cd "{ROOT}" && python collector.py'},
        {"group": "Genesis / Army", "label": "Genesis UI server", "cmd": f'cd "{ROOT}" && python server.py'},
        {"group": "BUILDR USB — Tray & daemon", "label": "Daemon tray (double-click)", "cmd": f'"{key_s}\\launchers\\LYGO_Daemon_Tray.bat"'},
        {"group": "BUILDR USB — Tray & daemon", "label": "Install logon autostart (+ Ollama)", "cmd": f'powershell -ExecutionPolicy Bypass -File "{key_s}\\launchers\\install_buildr_autostart.ps1" -WithOllama'},
        {"group": "BUILDR USB — Tray & daemon", "label": "Remove autostart task", "cmd": f'powershell -ExecutionPolicy Bypass -File "{key_s}\\launchers\\install_buildr_autostart.ps1" -Remove'},
        {"group": "BUILDR USB — Tray & daemon", "label": "Console daemon + Ollama", "cmd": f'"{key_s}\\launchers\\LYGO_BUILDR_Daemon.bat"'},
        {"group": "BUILDR USB — Tray & daemon", "label": "Daemon health (browser/curl)", "cmd": "http://127.0.0.1:9630/health"},
        {"group": "BUILDR USB — AI & verify", "label": "One-Boot offline chat", "cmd": f'"{key_s}\\launchers\\LYGO_One_Boot_AI.bat"'},
        {"group": "BUILDR USB — AI & verify", "label": "System check", "cmd": f'"{key_s}\\launchers\\CHECK_SYSTEM.bat"'},
        {"group": "BUILDR USB — AI & verify", "label": "Standalone verify", "cmd": f'cd /d "{key_s}" && python scripts\\verify_standalone_usb.py'},
        {"group": "BUILDR USB — AI & verify", "label": "Phase 2 bootstrap verify", "cmd": f'cd /d "{key_s}" && python verify_bootstrap.py --edition GROK_BUILDR --phase2'},
        {"group": "BUILDR USB — AI & verify", "label": "Full stick benchmark", "cmd": f'cd /d "{key_s}" && python scripts\\benchmark_buildr_stick.py --network --lygo-claw-root "{claw}"'},
        {"group": "BUILDR USB — AI & verify", "label": "Benchmark launcher", "cmd": f'"{key_s}\\launchers\\LYGO_Run_Benchmark.bat"'},
        {"group": "BUILDR USB — Sync & retail", "label": "Sync overlay to stick", "cmd": f'powershell -ExecutionPolicy Bypass -File "{overlay}\\scripts\\sync_overlay_to_builder_key.ps1"'},
        {"group": "BUILDR USB — Sync & retail", "label": "Export all PUBLIC SKUs", "cmd": f'powershell -ExecutionPolicy Bypass -File "{key_s}\\scripts\\build_phase3_all_skus.ps1"'},
        {"group": "BUILDR USB — Sync & retail", "label": "Zip SKUs for Gumroad", "cmd": f'powershell -ExecutionPolicy Bypass -File "{overlay}\\scripts\\package_public_sku_zips.ps1"'},
        {"group": "LYGO-Claw", "label": "Install + self-check", "cmd": f'"{claw}\\launchers\\INSTALL_AND_CHECK.bat"'},
        {"group": "LYGO-Claw", "label": "USB supervisor health", "cmd": f'cd /d "{claw}" && set PYTHONPATH={claw}\\src && python -m lygo_claw.cli usb-health'},
        {"group": "LYGO-Claw", "label": "Gateway test", "cmd": f'cd /d "{claw}" && set PYTHONPATH={claw}\\src && python -m lygo_claw.cli gateway "hello"'},
        {"group": "LYGO-Claw", "label": "Queue stick task", "cmd": f'cd /d "{claw}" && set PYTHONPATH={claw}\\src && python -m lygo_claw.cli buildr-task verify_standalone --wait'},
        {"group": "LYGO-Claw", "label": "Sovereign loop (desktop+USB+lattice)", "cmd": f'"{claw}\\launchers\\RUN_SOVEREIGN_LOOP.bat"'},
        {"group": "LYGO-Claw", "label": "God-Mode brain init", "cmd": f'cd /d "{claw}" && set PYTHONPATH={claw}\\src && set LYGO_BUILDER_KEY_ROOT={key_s} && python -m lygo_claw.cli brain-init'},
        {"group": "BUILDR USB — Tray & daemon", "label": "Nightly brain loop (USB)", "cmd": f'"{key_s}\\launchers\\LYGO_Nightly_Brain_Loop.bat"'},
        {"group": "Stack", "label": "Lattice verify", "cmd": f'cd /d "{stack}" && python tools\\verify_lattice_alignment.py'},
        {"group": "Stack", "label": "Push with credential helper", "cmd": f'python "{stack}\\tools\\push_with_git_credential.py"'},
    ]


def sentinel_status() -> dict:
    p = CC / "workspace" / "sentinel_status.json"
    if not p.is_file():
        return {"ok": False, "detail": "no sentinel_status.json"}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return {
            "ok": bool(d.get("healthy")),
            "timestamp": d.get("timestamp"),
            "lattice": d.get("lattice"),
            "ollama": d.get("ollama"),
            "hf_space": d.get("hf_space"),
            "public_pages": d.get("public_pages"),
            "network_builder": d.get("network_builder"),
            "queue": d.get("queue"),
            "git": d.get("git"),
            "raw": d,
        }
    except (json.JSONDecodeError, OSError) as exc:
        return {"ok": False, "detail": str(exc)[:120]}


def collect() -> dict:
    ts = datetime.now(timezone.utc).isoformat()
    ensure_sentinel_fresh()
    lattice = run_lattice()
    gh = github_repo()
    commit = github_last_commit()
    space = hf_space()
    dataset = hf_dataset()
    ops = ops_discord_crypto()
    phase5 = phase5_metrics()
    twin = twin_gate()
    sentinel = sentinel_status()
    joy = joy_loop()
    public = internet_lattice()
    healthy = bool(
        lattice.get("ok")
        and gh.get("ok")
        and space.get("ok")
        and (sentinel.get("ok") or lattice.get("ok"))
    )
    return {
        "signature": "Δ9Φ963-GENESIS-CONSOLE-v3",
        "title": "LYGO Lightfather Genesis Console — Full Lattice Monitor",
        "updated_at": ts,
        "healthy": healthy,
        "links": LINKS,
        "services": {
            "genesis_port": GENESIS_PORT,
            "joy_api_port": JOY_API_PORT,
            "stack_root": str(STACK),
        },
        "lattice": lattice,
        "internet_lattice": public,
        "sentinel": sentinel,
        "joy_loop": joy,
        "github": {"repo": gh, "last_commit": commit, "local": local_git()},
        "huggingface": {"space": space, "dataset": dataset},
        "clawhub": clawhub_index(),
        "p0": p0_golden(),
        "army": army_state(),
        "ops": ops,
        "phase5": phase5,
        "twin_gate": twin,
        "buildr_usb": buildr_usb_status(),
        "commands": quick_commands(),
    }


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = collect()
    STATUS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {STATUS_PATH} healthy={payload.get('healthy')}")
    return 0 if payload.get("healthy") else 1


if __name__ == "__main__":
    raise SystemExit(main())