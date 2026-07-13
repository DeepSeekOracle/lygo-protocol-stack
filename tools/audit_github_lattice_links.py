#!/usr/bin/env python3
"""Audit GitHub Pages surfaces vs immutable link archive, sitemap, and hub cross-links."""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ARCHIVE_PATH = DOCS / "LYGO_PUBLIC_LINK_ARCHIVE.json"
SITEMAP_PATH = DOCS / "sitemap.xml"
HUB_PATH = DOCS / "LYGO_KNOWLEDGE_HUB.html"
INDEX_PATH = DOCS / "index.html"
OUT_PATH = ROOT / "tests" / "github_lattice_audit_last_run.json"

STACK_PAGES_BASE = "https://deepseekoracle.github.io/lygo-protocol-stack/"
EXCAVATION_BASE = "https://deepseekoracle.github.io/Excavationpro/"

# Every HTML under docs/ that should be in link archive + reachable
CANONICAL_HTML = [
    "index.html",
    "LYGO_CLAW.html",
    "LYGO_KNOWLEDGE_HUB.html",
    "HavenStarChart.html",
    "HavenStarChartPortal.html",
    "KernelEggRetrieval.html",
    "SovereignLatticeMesh.html",
    "BiometricEntropyHarness.html",
    "LYGO_BPM_Finder.html",
    "tools/LYGO_Compass_Master.html",
    "joy_loop/dashboard/index.html",
    "joy_loop/dashboard/architect.html",
]


def load_archive_paths() -> set[str]:
    data = json.loads(ARCHIVE_PATH.read_text(encoding="utf-8"))
    paths: set[str] = set()
    for entry in data.get("entries", []):
        urls = entry.get("urls") or {}
        for val in urls.values():
            if not isinstance(val, str):
                continue
            if STACK_PAGES_BASE in val:
                rel = val.split("lygo-protocol-stack/", 1)[1].split("#")[0].split("?")[0]
                paths.add(rel.rstrip("/") or "index.html")
            for key in ("repo_canonical", "repo_path", "pages_copy"):
                rp = urls.get(key)
                if isinstance(rp, str) and (rp.endswith(".html") or rp == "docs/index.html"):
                    p = rp.replace("docs/", "", 1) if rp.startswith("docs/") else rp
                    paths.add(p)
    return paths


def load_sitemap_paths() -> set[str]:
    if not SITEMAP_PATH.is_file():
        return set()
    text = SITEMAP_PATH.read_text(encoding="utf-8")
    paths: set[str] = set()
    for m in re.finditer(r"<loc>([^<]+)</loc>", text):
        url = m.group(1)
        if STACK_PAGES_BASE in url:
            rel = url.split("lygo-protocol-stack/", 1)[1].rstrip("/") or "index.html"
            paths.add(rel)
    return paths


def hub_links_to_html() -> set[str]:
    if not HUB_PATH.is_file():
        return set()
    text = HUB_PATH.read_text(encoding="utf-8")
    found: set[str] = set()
    for m in re.finditer(r'href="([^"]+\.html[^"]*)"', text):
        href = m.group(1)
        if href.startswith("http"):
            if STACK_PAGES_BASE in href:
                found.add(href.split("lygo-protocol-stack/", 1)[1].split("#")[0])
        else:
            found.add(href.split("#")[0])
    return found


def probe(url: str, timeout: float = 20.0) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "LYGO-GitHub-Lattice-Audit/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {"url": url, "status": resp.status, "ok": 200 <= resp.status < 400}
    except urllib.error.HTTPError as e:
        return {"url": url, "status": e.code, "ok": False}
    except Exception as e:
        return {"url": url, "status": None, "ok": False, "error": str(e)}


def main() -> int:
    t0 = time.perf_counter()
    archived = load_archive_paths()
    sitemap = load_sitemap_paths()
    hub = hub_links_to_html()

    missing_archive: list[str] = []
    missing_sitemap: list[str] = []
    missing_hub: list[str] = []

    live_checks: list[dict] = []
    for rel in CANONICAL_HTML:
        live_url = STACK_PAGES_BASE + rel
        live_checks.append({**probe(live_url), "id": rel.replace("/", "_")})
        if rel not in archived:
            missing_archive.append(rel)
        if rel not in sitemap and rel != "joy_loop/dashboard/architect.html":
            missing_sitemap.append(rel)
        if rel not in hub and rel not in ("index.html", "joy_loop/dashboard/architect.html"):
            missing_hub.append(rel)

    report = {
        "signature": "Δ9Φ963-GITHUB-LATTICE-AUDIT-v1",
        "audited_utc": datetime.now(timezone.utc).isoformat(),
        "canonical_html_count": len(CANONICAL_HTML),
        "archive_paths_count": len(archived),
        "sitemap_paths_count": len(sitemap),
        "missing_from_link_archive": missing_archive,
        "missing_from_sitemap": missing_sitemap,
        "missing_from_knowledge_hub": missing_hub,
        "live_http": live_checks,
        "all_live": all(r["ok"] for r in live_checks),
        "restore_doc": "I:/E Drive/GITHUB_AGENT_RESTORE.txt",
        "duration_ms": int((time.perf_counter() - t0) * 1000),
    }
    OUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    issues = missing_archive or missing_sitemap or not report["all_live"]
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())