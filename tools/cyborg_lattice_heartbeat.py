#!/usr/bin/env python3
"""
LYGO cyborg lattice heartbeat — local A–E tick.

Does: kernel verify, HTTPS pulse (optional), Layer E gossip, agent-lattice verify, write receipt.
Does NOT: git push, HF upload, ClawHub publish, live Star Chart write, ACP.

  set LYGO_STACK_ROOT=I:\\E Drive\\lygo-protocol-stack
  python tools/cyborg_lattice_heartbeat.py
  python tools/cyborg_lattice_heartbeat.py --pulse --peer http://127.0.0.1:8791

Signature: Delta9Phi963-CYBORG-HEARTBEAT-v1
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(os.environ.get("LYGO_STACK_ROOT", "")).resolve() if os.environ.get("LYGO_STACK_ROOT") else Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
OUT = ROOT / "tests" / "cyborg_heartbeat_last_run.json"
SIG = "Delta9Phi963-CYBORG-HEARTBEAT-v1"


def run_py(script: Path, extra: list[str]) -> tuple[int, dict | str]:
    if not script.is_file():
        return 2, {"error": "missing", "script": str(script)}
    p = subprocess.run(
        [sys.executable, str(script), *extra],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    text = (p.stdout or "").strip()
    dec = json.JSONDecoder()
    found = []
    idx = 0
    while True:
        j = text.find("{", idx)
        if j < 0:
            break
        try:
            obj, end = dec.raw_decode(text[j:])
            if isinstance(obj, dict):
                found.append(obj)
            idx = j + max(end, 1)
        except json.JSONDecodeError:
            idx = j + 1
    if found:
        for obj in reversed(found):
            if obj.get("signature") or obj.get("verdict"):
                return p.returncode, obj
        return p.returncode, found[-1]
    return p.returncode, (text or p.stderr or "")[-800:]


def http_get(url: str, timeout: float = 8.0) -> dict:
    try:
        req = Request(url, headers={"User-Agent": "LYGO-CyborgHeartbeat/1"})
        with urlopen(req, timeout=timeout) as r:
            body = r.read(200000)
            return {"ok": True, "status": r.status, "bytes": len(body)}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--peer", default="http://127.0.0.1:8791")
    ap.add_argument("--pulse", action="store_true", help="HTTPS GET public lattice pulse (RESOURCE)")
    ap.add_argument("--skip-kernel", action="store_true")
    args = ap.parse_args()

    os.environ["LYGO_STACK_ROOT"] = str(ROOT)
    report: dict = {
        "signature": SIG,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "stack": str(ROOT),
        "peer": args.peer,
        "publish": False,
        "layers": {},
        "verdict": "TICK_OK",
    }

    if not args.skip_kernel:
        rc, body = run_py(TOOLS / "verify_all_kernel_layers.py", ["--json"])
        report["layers"]["AB_kernel"] = body if isinstance(body, dict) else {"raw": body, "exit": rc}
        v = (body or {}).get("verdict") if isinstance(body, dict) else ""
        if v == "QUARANTINE" or (isinstance(body, dict) and body.get("summary", {}).get("classic") == "QUARANTINE"):
            report["verdict"] = "QUARANTINE"
            report["action"] = "STOP_ALL_EXTERNAL"
            OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(report, indent=2))
            return 3

    health = http_get(args.peer.rstrip("/") + "/health")
    report["layers"]["hub_health"] = health
    if not health.get("ok"):
        report["verdict"] = "HUB_DOWN"
        report["action"] = "start tools/launch_cyborg_lattice.ps1"

    if health.get("ok"):
        gcmd = ["--peer", args.peer, "--role", "steward"]
        if os.environ.get("LYGO_AGENT_ID"):
            gcmd.extend(["--agent-id", os.environ["LYGO_AGENT_ID"]])
        rc, body = run_py(TOOLS / "agent_lattice_gossip_tick.py", gcmd)
        report["layers"]["gossip"] = body if isinstance(body, dict) else {"raw": body, "exit": rc}
        rc2, body2 = run_py(
            TOOLS / "verify_agent_lattice.py",
            ["--json", "--skip-mesh", "--run-gossip", "--peer", args.peer],
        )
        report["layers"]["E_verify"] = body2 if isinstance(body2, dict) else {"raw": body2, "exit": rc2}
        ev = body2.get("verdict") if isinstance(body2, dict) else ""
        if ev == "LOCAL_QUARANTINE":
            report["verdict"] = "QUARANTINE"

    if args.pulse:
        report["layers"]["public_pulse"] = {
            "pages": http_get("https://deepseekoracle.github.io/lygo-protocol-stack/"),
            "agora": http_get("https://deepseekoracle.github.io/lygo-protocol-stack/agent-agora/api/pulse.json"),
            "class": "RESOURCE",
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, default=str))
    if report["verdict"] == "QUARANTINE":
        return 3
    if report["verdict"] == "HUB_DOWN":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
