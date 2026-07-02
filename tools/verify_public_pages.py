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
    "stack_slm": "https://deepseekoracle.github.io/lygo-protocol-stack/SovereignLatticeMesh.html",
    "stack_harness": "https://deepseekoracle.github.io/lygo-protocol-stack/BiometricEntropyHarness.html",
    "excavationpro_slm": "https://deepseekoracle.github.io/Excavationpro/SovereignLatticeMesh.html",
    "excavationpro_harness": "https://deepseekoracle.github.io/Excavationpro/BiometricEntropyHarness.html",
}


def probe(url: str, timeout: float = 20.0) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "LYGO-Public-Pages-Verify/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {"url": url, "status": resp.status, "ok": 200 <= resp.status < 400}
    except urllib.error.HTTPError as e:
        return {"url": url, "status": e.code, "ok": False}
    except Exception as e:
        return {"url": url, "status": None, "ok": False, "error": str(e)}


def main() -> int:
    t0 = time.perf_counter()
    results = []
    for key, url in URLS.items():
        row = probe(url)
        row["id"] = key
        results.append(row)

    stack_ok = all(r["ok"] for r in results if r["id"].startswith("stack_"))
    mirror_ok = all(r["ok"] for r in results if r["id"].startswith("excavationpro_"))
    report = {
        "signature": "Δ9Φ963-PUBLIC-PAGES-VERIFY-v1",
        "vectors": results,
        "stack_pages_live": stack_ok,
        "excavationpro_mirrors_live": mirror_ok,
        "duration_ms": int((time.perf_counter() - t0) * 1000),
    }
    out = ROOT / "tests" / "public_pages_last_run.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if mirror_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())