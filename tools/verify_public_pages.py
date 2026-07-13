#!/usr/bin/env python3
"""HTTP check public Pages URLs — writes tests/public_pages_last_run.json."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

URLS = {
    "stack_index": "https://deepseekoracle.github.io/lygo-protocol-stack/",
    "stack_knowledge_hub": "https://deepseekoracle.github.io/lygo-protocol-stack/LYGO_KNOWLEDGE_HUB.html",
    "stack_lygo_claw": "https://deepseekoracle.github.io/lygo-protocol-stack/LYGO_CLAW.html",
    "stack_compass": "https://deepseekoracle.github.io/lygo-protocol-stack/tools/LYGO_Compass_Master.html",
    "stack_slm": "https://deepseekoracle.github.io/lygo-protocol-stack/SovereignLatticeMesh.html",
    "stack_harness": "https://deepseekoracle.github.io/lygo-protocol-stack/BiometricEntropyHarness.html",
    "stack_bpm_finder": "https://deepseekoracle.github.io/lygo-protocol-stack/LYGO_BPM_Finder.html",
    "stack_haven_chart": "https://deepseekoracle.github.io/lygo-protocol-stack/HavenStarChart.html",
    "stack_haven_portal": "https://deepseekoracle.github.io/lygo-protocol-stack/HavenStarChartPortal.html",
    "stack_kernel_eggs": "https://deepseekoracle.github.io/lygo-protocol-stack/KernelEggRetrieval.html",
    "stack_joy_loop": "https://deepseekoracle.github.io/lygo-protocol-stack/joy_loop/dashboard/index.html",
    "excavationpro_slm": "https://deepseekoracle.github.io/Excavationpro/SovereignLatticeMesh.html",
    "excavationpro_harness": "https://deepseekoracle.github.io/Excavationpro/BiometricEntropyHarness.html",
    "excavationpro_eternalhaven": "https://deepseekoracle.github.io/Excavationpro/eternalhaven.html",
}


def probe(url: str, timeout: float = 20.0, *, body_contains: str | None = None) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "LYGO-Public-Pages-Verify/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            ok = 200 <= resp.status < 400
            if ok and body_contains and body_contains not in body:
                ok = False
            row = {"url": url, "status": resp.status, "ok": ok}
            if body_contains:
                row["marker"] = body_contains
                row["marker_found"] = body_contains in body
            return row
    except urllib.error.HTTPError as e:
        return {"url": url, "status": e.code, "ok": False}
    except Exception as e:
        return {"url": url, "status": None, "ok": False, "error": str(e)}


def main() -> int:
    t0 = time.perf_counter()
    results = []
    markers = {
        "stack_bpm_finder": "lygo-top-bar",
    }
    for key, url in URLS.items():
        row = probe(url, body_contains=markers.get(key))
        row["id"] = key
        results.append(row)

    stack_core_ids = {
        "stack_index",
        "stack_knowledge_hub",
        "stack_slm",
        "stack_harness",
        "stack_haven_chart",
        "stack_haven_portal",
    }
    stack_ok = all(r["ok"] for r in results if r["id"] in stack_core_ids)
    mirror_ok = all(r["ok"] for r in results if r["id"].startswith("excavationpro_"))
    compass_row = next((r for r in results if r["id"] == "stack_compass"), None)
    report = {
        "signature": "Δ9Φ963-PUBLIC-PAGES-VERIFY-v1",
        "vectors": results,
        "stack_pages_live": stack_ok,
        "stack_compass_live": bool(compass_row and compass_row.get("ok")),
        "excavationpro_mirrors_live": mirror_ok,
        "duration_ms": int((time.perf_counter() - t0) * 1000),
    }
    out = ROOT / "tests" / "public_pages_last_run.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if mirror_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())