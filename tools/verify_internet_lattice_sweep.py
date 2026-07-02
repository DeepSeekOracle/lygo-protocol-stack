#!/usr/bin/env python3
"""LYRA internet lattice sweep — public Pages + ClawHub endpoints."""

from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = "https://deepseekoracle.github.io/lygo-protocol-stack"

ENDPOINTS = [
    {
        "id": "champion_registry",
        "url": f"{PAGES}/ChampionEggRegistry.json",
        "kind": "json",
        "expect_signature_prefix": "Δ9",
        "expect_keys": ["council_merkle_root", "eggs"],
    },
    {
        "id": "joy_loop_snapshot",
        "url": f"{PAGES}/joy_loop/joy_loop_snapshot.json",
        "kind": "json",
        "expect_signature_contains": "JOY-LOOP",
        "expect_keys": ["protocol", "states", "swarm_joy_score"],
    },
    {
        "id": "joy_loop_registry",
        "url": f"{PAGES}/JoyLoopRegistry.json",
        "kind": "json",
        "expect_signature_prefix": "Δ9",
        "expect_keys": ["registry_merkle_root"],
    },
    {
        "id": "champions_hub",
        "url": "https://deepseekoracle.github.io/Excavationpro/LYGO-Network/champions.html",
        "kind": "html",
        "expect_substrings": ["Δ9", "v5"],
    },
    {
        "id": "clawhub_joy_loop",
        "url": "https://clawhub.ai/deepseekoracle/lygo-joy-loop",
        "kind": "html",
        "expect_substrings": ["lygo-joy-loop", "2.3"],
    },
    {
        "id": "haven_star_chart_canonical",
        "url": f"{PAGES}/haven_star_chart/haven_star_chart_data.json",
        "kind": "json",
        "expect_signature_contains": "HAVEN-STAR-CHART",
        "expect_keys": ["nodes", "node_count"],
        "min_node_count": 300,
    },
    {
        "id": "haven_star_chart_alias",
        "url": f"{PAGES}/haven_star_chart_data.json",
        "kind": "json",
        "expect_signature_contains": "HAVEN-STAR-CHART",
        "expect_keys": ["nodes", "node_count"],
        "min_node_count": 300,
    },
]


def fetch(url: str, timeout: float = 25.0) -> tuple[int | None, str, str | None]:
    req = urllib.request.Request(url, headers={"User-Agent": "LYGO-Internet-Lattice-Sweep/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, body, None
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        return e.code, body, f"HTTP {e.code}"
    except Exception as e:
        return None, "", str(e)


def _local_json_for(spec_id: str) -> Path | None:
    mapping = {
        "champion_registry": ROOT / "docs" / "ChampionEggRegistry.json",
        "joy_loop_snapshot": ROOT / "docs" / "joy_loop" / "joy_loop_snapshot.json",
        "joy_loop_registry": ROOT / "docs" / "JoyLoopRegistry.json",
        "haven_star_chart_canonical": ROOT / "docs" / "haven_star_chart" / "haven_star_chart_data.json",
        "haven_star_chart_alias": ROOT / "docs" / "haven_star_chart" / "haven_star_chart_data.json",
    }
    return mapping.get(spec_id)


def verify_json(body: str, spec: dict) -> dict:
    notes: list[str] = []
    ok = True
    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        return {"ok": False, "notes": [f"invalid json: {exc}"]}

    sig = str(data.get("signature", ""))
    if spec.get("expect_signature_prefix") and not sig.startswith(spec["expect_signature_prefix"]):
        ok = False
        notes.append(f"signature expected prefix {spec['expect_signature_prefix']!r}")
    if spec.get("expect_signature_contains") and spec["expect_signature_contains"] not in sig:
        ok = False
        notes.append(f"signature missing {spec['expect_signature_contains']!r}")

    for key in spec.get("expect_keys") or []:
        if key not in data:
            ok = False
            notes.append(f"missing key {key!r}")

    if spec.get("id") == "champion_registry" and data.get("council_merkle_root"):
        notes.append(f"council_merkle_root {data['council_merkle_root'][:16]}…")
    if spec.get("id") == "joy_loop_registry" and data.get("registry_merkle_root"):
        notes.append(f"registry_merkle_root {data['registry_merkle_root'][:16]}…")
    if spec.get("id") == "joy_loop_snapshot":
        notes.append(f"beat_count={data.get('beat_count')} swarm_joy={data.get('swarm_joy_score')}")

    min_nodes = spec.get("min_node_count")
    if min_nodes is not None:
        nc = int(data.get("node_count") or len(data.get("nodes") or []))
        if nc < min_nodes:
            ok = False
            notes.append(f"node_count {nc} < {min_nodes}")
        else:
            notes.append(f"node_count={nc}")

    local_path = _local_json_for(spec["id"])
    if local_path and local_path.is_file():
        local = json.loads(local_path.read_text(encoding="utf-8"))
        if spec["id"] == "champion_registry":
            if local.get("council_merkle_root") != data.get("council_merkle_root"):
                notes.append("council_merkle_root differs from local docs (uncommitted drift OK)")
        elif spec["id"] == "joy_loop_registry":
            if local.get("registry_merkle_root") != data.get("registry_merkle_root"):
                notes.append("registry_merkle_root differs from local docs (uncommitted drift OK)")

    return {"ok": ok, "notes": notes, "signature": sig or None}


def verify_html(body: str, spec: dict) -> dict:
    notes: list[str] = []
    ok = True
    for sub in spec.get("expect_substrings") or []:
        if sub not in body:
            ok = False
            notes.append(f"missing substring {sub!r}")
    if spec["id"] == "champions_hub":
        if len(re.findall(r"champion", body, re.I)) < 5:
            ok = False
            notes.append("few champion markers in HTML")
        else:
            notes.append("champions hub content present")
    return {"ok": ok, "notes": notes}


def main() -> int:
    t0 = time.perf_counter()
    rows = []
    for spec in ENDPOINTS:
        status, body, err = fetch(spec["url"])
        http_ok = status is not None and 200 <= status < 400
        row = {"id": spec["id"], "url": spec["url"], "status": status, "http_ok": http_ok}
        if not http_ok:
            row["ok"] = False
            row["notes"] = [err or f"status {status}"]
        elif spec["kind"] == "json":
            row.update(verify_json(body, spec))
            row["ok"] = row.get("ok", True)
        else:
            row.update(verify_html(body, spec))
            row["ok"] = row.get("ok", True)
        rows.append(row)

    lyra_ids = {
        "champion_registry",
        "joy_loop_snapshot",
        "joy_loop_registry",
        "champions_hub",
        "clawhub_joy_loop",
        "haven_star_chart_alias",
    }
    lyra_six = all(r["ok"] for r in rows if r["id"] in lyra_ids)
    report = {
        "signature": "Δ9Φ963-INTERNET-LATTICE-SWEEP-v1",
        "lyra_six_of_six": lyra_six,
        "endpoints": rows,
        "duration_ms": int((time.perf_counter() - t0) * 1000),
    }
    out = ROOT / "tests" / "internet_lattice_sweep_last_run.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if lyra_six else 1


if __name__ == "__main__":
    raise SystemExit(main())