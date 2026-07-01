#!/usr/bin/env python3
"""Start/stop local LYGO mesh node processes (ports 8700+N). Cross-platform core."""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / "tests" / "mesh_live"
PID_FILE = STATE_DIR / "cluster.json"
SERVER = ROOT / "tools" / "node_api_server.py"


def start_cluster(nodes: int, base_port: int, host: str, stagger_ms: int) -> dict:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    procs: list[dict] = []
    for i in range(nodes):
        port = base_port + i
        node_id = f"mesh-{i:03d}"
        env = os.environ.copy()
        env["LYGO_NODE_ID"] = node_id
        log = STATE_DIR / f"node_{port}.log"
        log_fh = open(log, "a", encoding="utf-8")
        kw: dict = {
            "cwd": str(ROOT),
            "env": env,
            "stdout": log_fh,
            "stderr": subprocess.STDOUT,
            "stdin": subprocess.DEVNULL,
        }
        if sys.platform == "win32":
            create_no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            kw["creationflags"] = create_no_window
        else:
            kw["start_new_session"] = True
        p = subprocess.Popen(
            [sys.executable, str(SERVER), "--host", host, "--port", str(port)],
            **kw,
        )
        log_fh.close()
        procs.append({"node_id": node_id, "port": port, "pid": p.pid, "host": host})
        if stagger_ms > 0:
            time.sleep(stagger_ms / 1000.0)
    meta = {
        "signature": "Δ9Φ963-PHASE5-LIVE-DEPLOYMENT",
        "nodes": nodes,
        "base_port": base_port,
        "host": host,
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "processes": procs,
    }
    PID_FILE.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def stop_cluster() -> int:
    if not PID_FILE.is_file():
        print("No cluster state file")
        return 0
    meta = json.loads(PID_FILE.read_text(encoding="utf-8"))
    stopped = 0
    for proc in meta.get("processes", []):
        pid = proc.get("pid")
        if not pid:
            continue
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=False, capture_output=True)
            else:
                os.kill(pid, signal.SIGTERM)
            stopped += 1
        except Exception:
            pass
    PID_FILE.unlink(missing_ok=True)
    print(f"Stopped {stopped} mesh node processes")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=("start", "stop", "status"))
    ap.add_argument("--nodes", type=int, default=100)
    ap.add_argument("--base-port", type=int, default=8700)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--stagger-ms", type=int, default=50, help="Delay between node starts")
    args = ap.parse_args()
    if args.action == "stop":
        return stop_cluster()
    if args.action == "status":
        if PID_FILE.is_file():
            print(PID_FILE.read_text(encoding="utf-8"))
            return 0
        print("No cluster running")
        return 1
    meta = start_cluster(args.nodes, args.base_port, args.host, args.stagger_ms)
    print(json.dumps({"ok": True, "cluster": meta}, indent=2))
    print(f"Started {args.nodes} nodes on {args.host}:{args.base_port}-{args.base_port + args.nodes - 1}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())