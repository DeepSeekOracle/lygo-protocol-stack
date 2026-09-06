#!/usr/bin/env python3
"""
LYGO cyborg lattice heartbeat — autonomous A–E tick for the public network.

Autonomous (always): dual ledgers, egg registry, Star Chart feed chain, map, Agora.
Optional local: kernel verify, Layer E hub gossip.
Never: git push, HF upload, ClawHub, live Star Chart ingest, egg plant, ACP.

  python tools/cyborg_lattice_heartbeat.py --loop
  python tools/cyborg_lattice_heartbeat.py --write-public --i-consent

Signature: Delta9Phi963-CYBORG-HEARTBEAT-v1.1
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
PUBLIC_OUT = ROOT / "docs" / "agent-agora" / "api" / "heartbeat.json"
SIG = "Delta9Phi963-CYBORG-HEARTBEAT-v1.1"
UA = "LYGO-CyborgHeartbeat/1.1 (+https://chatagent.ca/agents/)"
SURFACES = [
    ("anchors", "https://deepseekoracle.github.io/lygo-protocol-stack/network_builder/IMMUTABLE_ANCHORS.json", "CANON"),
    ("star_feed", "https://deepseekoracle.github.io/lygo-protocol-stack/haven_star_chart/haven_star_chart_feed.json", "CANON"),
    ("eggs", "https://deepseekoracle.github.io/lygo-protocol-stack/KernelEggRegistry.json", "CANON"),
    ("agora", "https://deepseekoracle.github.io/lygo-protocol-stack/agent-agora/api/pulse.json", "CANON"),
    ("map", "https://chatagent.ca/lattice/map.json", "RESOURCE"),
    ("join", "https://chatagent.ca/join/doctrine.json", "RESOURCE"),
    ("bench", "https://chatagent.ca/bench/doctrine.json", "RESOURCE"),
]


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


def http_get(url: str, timeout: float = 16.0, max_bytes: int = 800000) -> dict:
    try:
        req = Request(url, headers={"User-Agent": UA})
        with urlopen(req, timeout=timeout) as r:
            body = r.read(max_bytes)
            out = {"ok": 200 <= r.status < 400, "status": r.status, "bytes": len(body), "url": url}
            if body[:1] in (b"{", b"["):
                try:
                    out["json"] = json.loads(body.decode("utf-8"))
                except Exception:
                    out["json"] = None
            return out
    except Exception as e:
        return {"ok": False, "status": 0, "error": str(e)[:200], "url": url}


def star_chain_ok(data: dict) -> dict:
    entries = data.get("entries") or []
    errs = []
    for i in range(len(entries) - 1):
        a, b = entries[i], entries[i + 1]
        if (a.get("prev_hash") or "") != (b.get("entry_hash") or ""):
            errs.append("break_at_seq_" + str(a.get("seq")))
            break
    return {
        "entry_count": data.get("entry_count") or len(entries),
        "chain_valid_published": data.get("chain_valid"),
        "chain_valid_checked": len(errs) == 0 and bool(entries),
        "chain_root": data.get("chain_root"),
        "errors": errs,
    }


def pulse_public() -> dict:
    rows = {}
    canon_fail = 0
    for sid, url, klass in SURFACES:
        got = http_get(url)
        got["class"] = klass
        if sid == "star_feed" and got.get("json"):
            got["feed"] = star_chain_ok(got["json"])
            got.pop("json", None)
        elif sid == "eggs" and got.get("json"):
            eggs = got["json"].get("eggs") or []
            got["eggs"] = {
                "count": len(eggs),
                "registry_merkle_root": got["json"].get("registry_merkle_root"),
                "signature": got["json"].get("signature"),
            }
            got.pop("json", None)
        elif sid == "agora" and got.get("json"):
            got["pulse"] = {
                "chart_nodes": got["json"].get("chart_nodes"),
                "feed_entries": got["json"].get("feed_entries"),
                "feed_root": got["json"].get("feed_root"),
                "writes": got["json"].get("writes"),
            }
            got.pop("json", None)
        elif sid == "anchors" and got.get("json"):
            groups = got["json"].get("immutable_anchors") or {}
            got["anchors"] = {"category_count": len(groups) if isinstance(groups, dict) else 0, "signature": got["json"].get("signature")}
            got.pop("json", None)
        elif sid == "map" and got.get("json"):
            got["doors"] = len(got["json"].get("doors") or [])
            got.pop("json", None)
        else:
            got.pop("json", None)
        if klass == "CANON" and not got.get("ok"):
            canon_fail += 1
        if sid == "star_feed" and got.get("feed") and not got["feed"].get("chain_valid_checked"):
            canon_fail += 1
        rows[sid] = got
    if canon_fail:
        y = "SHADOW"
    elif not all(rows[s]["ok"] for s, _, k in SURFACES if k == "RESOURCE"):
        y = "DRIFT"
    else:
        y = "ALIGNED"
    return {"class": "RESOURCE_PULSE", "yield": y, "canon_fail": canon_fail, "surfaces": rows}


def tick(args: argparse.Namespace) -> dict:
    os.environ["LYGO_STACK_ROOT"] = str(ROOT)
    report: dict = {
        "signature": SIG,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "stack": str(ROOT),
        "peer": args.peer,
        "publish": False,
        "live_star_chart_ingest": False,
        "egg_plant": False,
        "layers": {},
        "verdict": "TICK_OK",
        "doors": {
            "agents": "https://chatagent.ca/agents/",
            "join": "https://chatagent.ca/join/",
            "map": "https://chatagent.ca/lattice/map.json",
            "heartbeat": "https://deepseekoracle.github.io/lygo-protocol-stack/agent-agora/api/heartbeat.json",
        },
    }

    pub = pulse_public()
    report["layers"]["public"] = pub
    if pub.get("yield") == "SHADOW":
        report["verdict"] = "PUBLIC_SHADOW"
    elif pub.get("yield") == "DRIFT" and report["verdict"] == "TICK_OK":
        report["verdict"] = "PUBLIC_DRIFT"

    if not args.skip_kernel:
        rc, body = run_py(TOOLS / "verify_all_kernel_layers.py", ["--json"])
        report["layers"]["AB_kernel"] = body if isinstance(body, dict) else {"raw": body, "exit": rc}
        v = (body or {}).get("verdict") if isinstance(body, dict) else ""
        if v == "QUARANTINE" or (isinstance(body, dict) and body.get("summary", {}).get("classic") == "QUARANTINE"):
            report["verdict"] = "QUARANTINE"
            report["action"] = "STOP_ALL_EXTERNAL"
            return report

    if not args.skip_hub:
        health = http_get(args.peer.rstrip("/") + "/health")
        report["layers"]["hub_health"] = health
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
        else:
            report["layers"]["hub_health"]["note"] = "optional_local — public pulse still autonomous"
    return report


def persist(report: dict, write_public: bool) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    if write_public:
        PUBLIC_OUT.parent.mkdir(parents=True, exist_ok=True)
        public = {
            "signature": SIG,
            "class": "RESOURCE",
            "created_utc": report.get("created_utc"),
            "verdict": report.get("verdict"),
            "public": report.get("layers", {}).get("public"),
            "live_star_chart_ingest": False,
            "egg_plant": False,
            "doors": report.get("doors"),
        }
        PUBLIC_OUT.write_text(json.dumps(public, indent=2, default=str) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--peer", default="http://127.0.0.1:8791")
    ap.add_argument("--pulse", action="store_true", help="legacy flag; public pulse is now always on")
    ap.add_argument("--skip-kernel", action="store_true")
    ap.add_argument("--skip-hub", action="store_true", help="public network only (no localhost Layer E)")
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--interval", type=int, default=90)
    ap.add_argument("--write-public", action="store_true")
    ap.add_argument("--i-consent", action="store_true")
    args = ap.parse_args()

    def once() -> int:
        report = tick(args)
        if args.write_public and not args.i_consent:
            report["write_public"] = "refused — need --i-consent (does not live-ingest the chart)"
        persist(report, bool(args.write_public and args.i_consent))
        print(json.dumps(report, indent=2, default=str))
        if report["verdict"] == "QUARANTINE":
            return 3
        if report["verdict"] == "PUBLIC_SHADOW":
            return 2
        return 0

    if not args.loop:
        return once()
    code = 0
    while True:
        code = once()
        if code == 3:
            return 3
        try:
            import time

            time.sleep(max(30, args.interval))
        except KeyboardInterrupt:
            return code
    return code


if __name__ == "__main__":
    raise SystemExit(main())
