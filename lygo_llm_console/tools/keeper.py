"""Keeper: the daemon that keeps this console alive and its schedule running.

The console is a single process holding a model in VRAM. When it dies the page dies with it and
nothing restarts it; when the doorbell dies, even the operator's Boot button goes quiet. The keeper
is the smallest thing that fixes both: a sweep loop that checks the two ports, brings back what is
missing (with a cooldown, so a crash loop cannot turn into a relaunch storm), and drives the cron
schedule.

Ported from the Hermes periodic scheduler (`agent/periodic_scheduler.py`) and the cron runtime
(`cron/scheduler.py`): the loop is a sweep, not a pile of timers, and every sweep is idempotent
because the state it reads is the record it writes.

Testability is deliberate: `sweep()` takes its probes as arguments, so the whole supervision policy
can be exercised without a console, a doorbell or a model.

Usage:
    python tools/keeper.py --once                 # one sweep, print it, exit
    python tools/keeper.py --interval 20          # sweep every 20s (foreground)
    python tools/keeper.py --detach               # sweep every 20s, detached, logged
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DATA = ROOT / "data"
STATE = DATA / "keeper.json"
LOCK = DATA / "keeper.lock"
LOGDIR = ROOT / "save" / "logs"
RING_COOLDOWN_S = 90.0      # never relaunch more often than this
DEFAULT_INTERVAL = 20.0


# --------------------------------------------------------------------------- probes
def console_port() -> int:
    try:
        cfg = json.loads((ROOT / "config" / "console.json").read_text(encoding="utf-8"))
        return int(cfg.get("port") or cfg.get("console_port") or 9641)
    except Exception:
        return 9641


def probe_console(port: int = 0, timeout: float = 6.0) -> dict[str, Any]:
    port = port or console_port()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=timeout) as fh:
            h = json.loads(fh.read().decode("utf-8", "replace"))
        return {"up": True, "port": port, "brain": h.get("brain"), "build": h.get("release")}
    except Exception as exc:
        return {"up": False, "port": port, "why": type(exc).__name__}


def probe_doorbell(port: int = 0, timeout: float = 6.0) -> dict[str, Any]:
    port = port or (console_port() - 1)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/state", timeout=timeout) as fh:
            s = json.loads(fh.read().decode("utf-8", "replace"))
        return {"up": bool(s.get("doorbell")), "port": port, "console_up": s.get("console_up")}
    except Exception as exc:
        return {"up": False, "port": port, "why": type(exc).__name__}


# --------------------------------------------------------------------------- actions
def ring_doorbell(timeout: float = 60.0) -> dict[str, Any]:
    port = console_port() - 1
    tokf = DATA / ".lygo_doorbell_token"
    tok = tokf.read_text(encoding="utf-8").strip() if tokf.is_file() else ""
    if not tok:
        return {"ok": False, "error": "no_doorbell_token"}
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/boot?token={tok}", timeout=timeout) as fh:
            return {"ok": True, "answer": fh.read(200).decode("utf-8", "replace")}
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__}


def start_doorbell() -> dict[str, Any]:
    """Start the doorbell detached, so it outlives whatever started the keeper."""
    py = sys.executable
    cmd = ["powershell", "-NoProfile", "-Command",
           f"Start-Process -FilePath '{py}' -ArgumentList '{ROOT / 'tools' / 'doorbell.py'}','--detach' "
           f"-WorkingDirectory '{ROOT}' -WindowStyle Hidden"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return {"ok": r.returncode == 0, "code": r.returncode, "err": (r.stderr or "")[:200]}


def start_console() -> dict[str, Any]:
    """Start the whole stack detached (launcher), the way the operator's desktop icon does."""
    launcher = ROOT / "LYGO_LLM_CONSOLE.bat"
    if not launcher.is_file():
        return {"ok": False, "error": "no_launcher", "looked_for": str(launcher)}
    cmd = ["powershell", "-NoProfile", "-Command",
           f"Start-Process -FilePath '{launcher}' -WorkingDirectory '{ROOT}' -WindowStyle Normal"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return {"ok": r.returncode == 0, "code": r.returncode, "err": (r.stderr or "")[:200]}


# --------------------------------------------------------------------------- state
def load_state() -> dict[str, Any]:
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state: dict[str, Any]) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, STATE)


def log_line(text: str) -> None:
    LOGDIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with (LOGDIR / "keeper.log").open("a", encoding="utf-8") as fh:
        fh.write(f"[keeper] {stamp} {text}\n")


# --------------------------------------------------------------------------- the sweep
def sweep(console: Callable[[], dict[str, Any]] | None = None,
          doorbell: Callable[[], dict[str, Any]] | None = None,
          ring: Callable[[], dict[str, Any]] | None = None,
          start_db: Callable[[], dict[str, Any]] | None = None,
          start_console_fn: Callable[[], dict[str, Any]] | None = None,
          run_due: Callable[..., list] | None = None,
          now: float | None = None, cooldown: float = RING_COOLDOWN_S) -> dict[str, Any]:
    """One supervision pass. Every probe and action is injectable so this is testable without a stack."""
    now = time.time() if now is None else now
    console = console or probe_console
    doorbell = doorbell or probe_doorbell
    ring = ring or ring_doorbell
    start_db = start_db or start_doorbell
    start_console_fn = start_console_fn or start_console
    if run_due is None:
        import crons

        run_due = crons.run_due

    state = load_state()
    c = console()
    d = doorbell()
    actions: list[str] = []
    last_ring = float(state.get("last_ring") or 0)

    if not d.get("up"):
        got = start_db()
        actions.append("doorbell_started" if got.get("ok") else f"doorbell_start_failed:{got.get('error') or got.get('code')}")
    if not c.get("up"):
        if (now - last_ring) >= cooldown:
            if d.get("up") or any(a.startswith("doorbell_started") for a in actions):
                got = ring()
                state["last_ring"] = now
                actions.append(f"rung_doorbell:{got.get('ok')}")
            else:
                got = start_console_fn()
                state["last_ring"] = now
                actions.append(f"started_console:{got.get('ok')}")
        else:
            actions.append(f"restart_on_cooldown:{int(cooldown - (now - last_ring))}s")

    crons_run: list = []
    try:
        crons_run = run_due(now)
    except Exception as exc:
        actions.append(f"cron_error:{type(exc).__name__}")

    state.update({"last_sweep": now, "last_sweep_human": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now)),
                  "console_up": bool(c.get("up")), "console_port": c.get("port"),
                  "doorbell_up": bool(d.get("up")), "doorbell_port": d.get("port"),
                  "actions": actions[-8:], "crons_run": crons_run[-8:],
                  "sweeps": int(state.get("sweeps") or 0) + 1})
    save_state(state)
    if actions or crons_run:
        log_line(f"console={state['console_up']} doorbell={state['doorbell_up']} "
                 f"actions={actions} crons={[c['name'] for c in crons_run]}")
    return {"ok": True, "console": c, "doorbell": d, "actions": actions, "crons_run": crons_run,
            "state": {k: state.get(k) for k in ("sweeps", "console_up", "doorbell_up", "last_ring")}}


def status() -> dict[str, Any]:
    state = load_state()
    c = probe_console()
    d = probe_doorbell()
    pid, alive = _lock_holder()
    return {"ok": True, "console": c, "doorbell": d, "state": state, "keeper_pid": pid, "keeper_alive": alive,
            "interval_s": state.get("interval_s") or DEFAULT_INTERVAL, "log": str(LOGDIR / "keeper.log")}


# --------------------------------------------------------------------------- one instance
def _lock_holder() -> tuple[int, bool]:
    try:
        pid = int(LOCK.read_text(encoding="utf-8").strip().split()[0])
    except Exception:
        return 0, False
    try:
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True,
                             timeout=60).stdout
        return pid, str(pid) in out
    except Exception:
        return pid, False


def acquire_lock() -> bool:
    pid, alive = _lock_holder()
    if alive and pid != os.getpid():
        return False
    DATA.mkdir(parents=True, exist_ok=True)
    LOCK.write_text(f"{os.getpid()} {time.strftime('%Y-%m-%d %H:%M:%S')}", encoding="utf-8")
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Keep the LYGO console alive and its cron schedule running")
    ap.add_argument("--once", action="store_true", help="one sweep, print the JSON, exit")
    ap.add_argument("--interval", type=float, default=DEFAULT_INTERVAL)
    ap.add_argument("--detach", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--log", default="")
    args = ap.parse_args(argv)

    if args.status:
        print(json.dumps(status(), ensure_ascii=False, indent=2))
        return 0
    if args.once:
        print(json.dumps(sweep(), ensure_ascii=False, indent=2))
        return 0

    if args.detach:
        log = args.log or str(LOGDIR / "keeper.out.log")
        LOGDIR.mkdir(parents=True, exist_ok=True)
        # No -RedirectStandardOutput here: PowerShell refuses that together with -WindowStyle, and it
        # failed silently the first time. The keeper writes its own keeper.log anyway.
        cmd = ["powershell", "-NoProfile", "-Command",
               f"Start-Process -FilePath '{sys.executable}' "
               f"-ArgumentList '{Path(__file__).resolve()}','--interval','{args.interval}' "
               f"-WorkingDirectory '{ROOT}' -WindowStyle Hidden"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        detail = (r.stderr or r.stdout or "").strip()[:300]
        if r.returncode != 0:
            log_line(f"detach failed rc={r.returncode} {detail}")
        print(json.dumps({"detached": r.returncode == 0, "code": r.returncode, "log": str(LOGDIR / "keeper.log"),
                          "interval_s": args.interval, "detail": detail}))
        return 0 if r.returncode == 0 else 1

    if not acquire_lock():
        pid, _ = _lock_holder()
        print(f"a keeper is already running (pid {pid})", file=sys.stderr)
        return 3
    log_line(f"keeper up: interval={args.interval}s console={console_port()}")
    state = load_state()
    state["interval_s"] = args.interval
    save_state(state)
    try:
        while True:
            s = sweep()
            print(f"[keeper] {time.strftime('%H:%M:%S')} console={s['console'].get('up')} "
                  f"doorbell={s['doorbell'].get('up')} actions={s['actions']} crons={[c['name'] for c in s['crons_run']]}",
                  flush=True)
            time.sleep(max(5.0, args.interval))
    except KeyboardInterrupt:
        log_line("keeper down (keyboard interrupt)")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
