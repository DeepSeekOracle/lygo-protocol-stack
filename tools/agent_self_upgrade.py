#!/usr/bin/env python3
"""LYGO agent self-upgrade — sync key ClawHub mirrors into .grok/skills + refresh boot memory.

Pure local. No network. No ClawHub publish. No git push.

Usage:
  python tools/agent_self_upgrade.py
  python tools/agent_self_upgrade.py --usb-copy
"""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
MIRRORS = STACK / "clawhub" / "mirrors"
GROK = Path(r"I:\E Drive\.grok\skills")
USB = Path(r"E:\LYGO_LATTICE_MEMORY")

# Core upgrade set — keep agent current
SYNC_SLUGS = [
    "lygo-sovereign-super-skill",
    "lygo-protocol-stack-operator",
    "lygo-continuum",
    "lygo-continuum-integrator",
    "lygo-geodesic-sealer",
    "lygo-quantum-attestor",
    "lygo-mint-verifier",
    "lygo-mint-walkthrough",
    "lygo-pure-data-witness",
    "lygo-automation-workflows",
    "lygo-continuity-advisor",
    "lygo-emotional-ram",
    "lygo-joy-loop",
    "lygo-context-guard",
    "lygo-skill-spector",
    "lygo-sandcastle",
    "lygo-haven-star-chart",
    "lygo-champion-lightfather",
    "lygo-cyborg-kernel",
    "lygo-cyborg-onramp",
]


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sync_one(slug: str) -> dict:
    src = MIRRORS / slug
    dst = GROK / slug
    if not src.is_dir():
        return {"slug": slug, "ok": False, "error": "missing_mirror"}
    GROK.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    ver = None
    cj = src / "claw.json"
    if cj.is_file():
        try:
            ver = json.loads(cj.read_text(encoding="utf-8")).get("version")
        except Exception:
            pass
    return {"slug": slug, "ok": True, "version": ver, "dst": str(dst)}


def write_boot(results: list[dict]) -> Path:
    boot = {
        "signature": "Delta9Phi963-AGENT-BOOT-v1",
        "generated_utc": utc(),
        "stack": str(STACK),
        "purpose": "Continuity map for Grok/OpenClaw agents after self-upgrade",
        "synced": results,
        "read_first": [
            "docs/AGENT_BOOT.md",
            "docs/GIT_LATTICE_OVERVIEW.md",
            "docs/MULTI_SITE_PAGES_CENSUS.md",
            "docs/seals/DEADMAN_OPERATOR_RUNBOOK.md",
        ],
        "clawhub_recent": {
            "lygo-pure-data-witness": "1.3.0",
            "lygo-mint-verifier": "1.1.0",
            "lygo-continuum-integrator": "1.0.1",
            "lygo-automation-workflows": "1.0.0",
            "lygo-continuity-advisor": "1.0.0",
            "lygo-sovereign-super-skill": "1.1.0",
        },
        "rules": [
            "Consent before plant/publish/social",
            "No auto git push / HF upload / ClawHub publish unless user asks",
            "PDW fetch/all require consent flags",
            "Mint verifier is in-process (no subprocess)",
            "Prefer local-first automation (Sandcastle) before SaaS",
        ],
        "quick_cli": [
            "python tools/agent_self_upgrade.py --usb-copy",
            "python tools/seal_deadman_lattice.py status",
            "python tools/build_git_lattice_overview.py --usb-copy",
            "python tools/census_multi_site_pages.py --usb-copy",
        ],
    }
    out_json = STACK / "docs" / "AGENT_BOOT.json"
    out_md = STACK / "docs" / "AGENT_BOOT.md"
    out_json.write_text(json.dumps(boot, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# AGENT BOOT — LYGO / Grok continuity",
        "",
        f"**Generated:** {boot['generated_utc']}",
        "",
        "## Read first",
        "",
    ]
    for r in boot["read_first"]:
        lines.append(f"- `{r}`")
    lines += ["", "## Synced skills", ""]
    for r in results:
        if r.get("ok"):
            lines.append(f"- `{r['slug']}` v{r.get('version')}")
        else:
            lines.append(f"- `{r['slug']}` FAILED: {r.get('error')}")
    lines += [
        "",
        "## Recent ClawHub versions",
        "",
    ]
    for k, v in boot["clawhub_recent"].items():
        lines.append(f"- `{k}` **{v}**")
    lines += [
        "",
        "## Rules",
        "",
    ]
    for rule in boot["rules"]:
        lines.append(f"- {rule}")
    lines += [
        "",
        "## Quick CLI",
        "",
        "```bash",
        *boot["quick_cli"],
        "```",
        "",
        "**Δ9Φ963 — upgrade · verify · remember.**",
        "",
    ]
    out_md.write_text("\n".join(lines), encoding="utf-8")
    return out_md


def usb_copy() -> list[str]:
    notes = []
    try:
        USB.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return [f"usb_failed:{exc}"]
    for name in (
        "AGENT_BOOT.md",
        "AGENT_BOOT.json",
        "GIT_LATTICE_OVERVIEW.md",
        "GIT_LATTICE_OVERVIEW.json",
        "MULTI_SITE_PAGES_CENSUS.md",
        "MULTI_SITE_PAGES_CENSUS.json",
        "PAGES_UPDATE_QUEUE.md",
        "GIT_REPO_CENSUS.md",
    ):
        src = STACK / "docs" / name
        if src.is_file():
            shutil.copy2(src, USB / name)
            notes.append(str(USB / name))
    (USB / "README_AGENT_BOOT.txt").write_text(
        "LYGO Agent Boot Continuity\n"
        "==========================\n"
        f"Updated: {utc()}\n"
        "Start: AGENT_BOOT.md\n"
        "Then: GIT_LATTICE_OVERVIEW.md\n"
        "Pages: MULTI_SITE_PAGES_CENSUS.md + PAGES_UPDATE_QUEUE.md\n"
        "Deadman: docs/seals/DEADMAN_OPERATOR_RUNBOOK.md (in stack)\n",
        encoding="utf-8",
    )
    notes.append(str(USB / "README_AGENT_BOOT.txt"))
    return notes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--usb-copy", action="store_true")
    args = ap.parse_args()

    # de-dupe SYNC_SLUGS
    slugs = []
    for s in SYNC_SLUGS:
        if s and s not in slugs:
            slugs.append(s)

    results = [sync_one(s) for s in slugs]
    boot = write_boot(results)
    usb = usb_copy() if args.usb_copy else []
    report = {
        "ok": all(r.get("ok") for r in results),
        "synced": sum(1 for r in results if r.get("ok")),
        "total": len(results),
        "boot": str(boot),
        "usb": usb,
        "utc": utc(),
    }
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
