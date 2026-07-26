#!/usr/bin/env python3
"""
HTTP-check public verify components (Layer C). Network required.
Compares optional local merkle roots to public mirrors when JSON available.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SIG = "Delta9Phi963-EXTERNAL-LATTICE-ANCHOR-v1.0"
UA = "LYGO-ExternalLatticeAnchor/1.0 (+https://eternalhaven.ca)"


def fetch(url: str, timeout: int = 25) -> tuple[int, bytes | None, str | None]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read(), None
    except urllib.error.HTTPError as e:
        return e.code, None, str(e)
    except Exception as e:
        return 0, None, str(e)


def stack_root() -> Path:
    env = os.environ.get("LYGO_STACK_ROOT", "").strip()
    if env:
        return Path(env).resolve()
    here = Path(__file__).resolve()
    for p in here.parents:
        if (p / "docs" / "network_builder" / "IMMUTABLE_ANCHORS.json").is_file():
            return p
    return Path.cwd()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--stack-root", default="")
    args = ap.parse_args()
    stack = Path(args.stack_root).resolve() if args.stack_root else stack_root()

    man_path = Path(args.manifest) if args.manifest else stack / "docs" / "public_verify_manifest.json"
    if not man_path.is_file():
        # build first
        builder = Path(__file__).resolve().parent / "build_public_verify_manifest.py"
        if builder.is_file():
            os.system(f'"{sys.executable}" "{builder}" --stack-root "{stack}"')
    endpoints = []
    if man_path.is_file():
        man = json.loads(man_path.read_text(encoding="utf-8"))
        endpoints = man.get("public_endpoints") or []
    else:
        endpoints = [
            {
                "id": "anchors",
                "url": "https://raw.githubusercontent.com/DeepSeekOracle/lygo-protocol-stack/main/docs/network_builder/IMMUTABLE_ANCHORS.json",
            },
            {
                "id": "star",
                "url": "https://deepseekoracle.github.io/lygo-protocol-stack/HavenStarChart.html",
            },
        ]

    results = []
    hard_fail = False
    for ep in endpoints:
        url = ep.get("url")
        if not url:
            continue
        status, body, err = fetch(url)
        ok = 200 <= status < 400
        item = {
            "id": ep.get("id"),
            "url": url,
            "http_status": status,
            "ok": ok,
            "role": ep.get("role"),
            "error": err,
            "bytes": len(body) if body else 0,
        }
        if body and url.endswith(".json") and ok:
            try:
                data = json.loads(body.decode("utf-8", errors="replace"))
                if isinstance(data, dict):
                    if "registry_merkle_root" in data:
                        item["registry_merkle_root"] = data.get("registry_merkle_root")
                    if "version" in data and "immutable_anchors" in data:
                        item["anchors_version"] = data.get("version")
            except Exception:
                item["json_parse"] = False
        if ep.get("verify") == "http_required" and not ok:
            hard_fail = True
        results.append(item)

    # local vs public sovereign root if both present
    local_sov = stack / "data" / "sovereign_seeds" / "registry.json"
    if local_sov.is_file():
        try:
            lr = json.loads(local_sov.read_text(encoding="utf-8")).get("registry_merkle_root")
            pub = next((r for r in results if r.get("id") == "sovereign_seeds_snapshot"), None)
            if pub and pub.get("registry_merkle_root") and lr:
                item = {
                    "id": "sovereign_root_sync",
                    "local": lr,
                    "public": pub.get("registry_merkle_root"),
                    "match": lr == pub.get("registry_merkle_root"),
                }
                results.append(item)
                if not item["match"]:
                    # not quarantine — mirror lag is OK; warn only
                    item["note"] = "mirror lag or unpublished snapshot — re-run local snapshot + git push"
        except Exception:
            pass

    report = {
        "signature": SIG,
        "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "verdict": "PUBLIC_OK" if not hard_fail else "PUBLIC_DEGRADED",
        "checked": len(results),
        "results": results,
        "user_protection": {
            "do_not_trust_public_over_local": True,
            "if_mismatch_prefer_local_verify": True,
        },
    }

    out = stack / "tests" / "public_anchors_last_run.json"
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"verdict={report['verdict']} checked={report['checked']}")
        for r in results:
            if "http_status" in r:
                print(f"  {r.get('id')}: {r.get('http_status')} ok={r.get('ok')} {r.get('url','')[:70]}")
            else:
                print(f"  {r.get('id')}: {r}")

    return 0 if not hard_fail else 1


if __name__ == "__main__":
    raise SystemExit(main())
