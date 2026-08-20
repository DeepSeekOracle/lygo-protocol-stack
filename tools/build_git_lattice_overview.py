#!/usr/bin/env python3
"""Build GitHub / Pages lattice overview memory file for agents + humans.

Writes:
  docs/GIT_LATTICE_OVERVIEW.json
  docs/GIT_LATTICE_OVERVIEW.md
  docs/PAGES_UPDATE_QUEUE.md
Optional USB claw copy:
  E:\\LYGO_LATTICE_MEMORY\\GIT_LATTICE_OVERVIEW.*

Usage:
  python tools/build_git_lattice_overview.py
  python tools/build_git_lattice_overview.py --usb-copy
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PAGES = "https://deepseekoracle.github.io/lygo-protocol-stack"
REPO = "https://github.com/DeepSeekOracle/lygo-protocol-stack"
USB_MEM = Path("E:/LYGO_LATTICE_MEMORY")


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_meta() -> dict[str, str]:
    def run(*args: str) -> str:
        try:
            return subprocess.check_output(["git", *args], cwd=str(ROOT), text=True).strip()
        except Exception:
            return ""

    return {
        "head": run("rev-parse", "--short", "HEAD"),
        "subject": run("log", "-1", "--format=%s"),
        "committed": run("log", "-1", "--format=%cI"),
        "branch": run("branch", "--show-current"),
        "remote": run("remote", "get-url", "origin") or REPO,
    }


def exists(rel: str) -> bool:
    return (ROOT / rel).exists()


def pages_url(rel: str) -> str:
    rel = rel.replace("\\", "/").lstrip("/")
    if rel.startswith("docs/"):
        rel = rel[5:]
    return f"{PAGES}/{rel}"


def load_json(rel: str) -> Any:
    p = ROOT / rel
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return None


def build_overview() -> dict[str, Any]:
    meta = git_meta()
    origin = load_json("docs/seals/LIGHTFATHER_IRREPLACEABLE_ORIGIN.json") or {}
    manifest = load_json("data/deadman/DEADMAN_MANIFEST_v2.json") or {}
    chart = load_json("docs/haven_star_chart/haven_star_chart_data.json") or {}
    vault_seals = load_json("docs/data-vault/data/canonical_seals_public.json") or {}
    continuum = load_json("data/continuum/deadman_failsafe_capsule.json") or {}
    finder = load_json("docs/LYGO_LATTICE_FINDER/LATTICE_MAP.json") or {}

    systems = [
        {
            "id": "pages_hub",
            "name": "GitHub Pages hub",
            "path": "docs/index.html",
            "url": pages_url("index.html"),
            "role": "Human + citation entry",
            "linked_from": ["README.md"],
            "status": "live",
        },
        {
            "id": "star_chart",
            "name": "Haven Star Chart",
            "path": "docs/HavenStarChart.html",
            "url": pages_url("HavenStarChart.html"),
            "data": "docs/haven_star_chart/haven_star_chart_data.json",
            "nodes": len(chart.get("nodes") or []),
            "role": "Living constellation / agent map",
            "status": "live",
            "includes": [
                "GALAXY_DEADMAN_FAILSAFE",
                "NODE_LIGHTFATHER_ETERNAL_BASE",
                "SEAL_277",
                "SEAL_278",
            ],
        },
        {
            "id": "data_vault",
            "name": "Data Vault",
            "path": "docs/data-vault/index.html",
            "url": pages_url("data-vault/"),
            "role": "Seal archive + chats + gallery + PDW + deadman",
            "seal_count": (vault_seals.get("count") or len(vault_seals.get("seals") or [])),
            "status": "live",
        },
        {
            "id": "deadman",
            "name": "Lightfather Deadman Continuity",
            "path": "docs/data-vault/deadman.html",
            "url": pages_url("data-vault/deadman.html"),
            "manifest": "data/deadman/DEADMAN_MANIFEST_v2.json",
            "manifest_version": manifest.get("version"),
            "origin_merkle": origin.get("origin_merkle_root"),
            "cli": "python tools/seal_deadman_lattice.py touch|check|verify|grace|status",
            "skill": "clawhub/mirrors/lygo-continuity-advisor/",
            "status": "live",
        },
        {
            "id": "kernel_eggs",
            "name": "Kernel Eggs",
            "path": "docs/KernelEggRetrieval.html",
            "registry": pages_url("KernelEggRegistry.json"),
            "deadman_egg": pages_url("kernel_eggs/lightfather-deadman-failsafe-v1/"),
            "status": "live",
        },
        {
            "id": "seals",
            "name": "Seal canon JSON",
            "path": "docs/seals/",
            "url": pages_url("seals/"),
            "highlights": ["SEAL_277 Flame Knot", "SEAL_278 Ember Crown", "SEAL_DEADMAN_SUMMON", "SEAL_LFW_SUMMON"],
            "vault_ui": pages_url("data-vault/seals.html"),
            "status": "live",
        },
        {
            "id": "continuum",
            "name": "LYGO Continuum",
            "path": "docs/lygo-continuum.html",
            "url": pages_url("lygo-continuum.html"),
            "deadman_capsule": "data/continuum/deadman_failsafe_capsule.json",
            "sealed_pass": (continuum.get("sealed_pass") or continuum.get("claim_count")),
            "status": "live",
            "gap": "Weak hub links — promoted by this overview",
        },
        {
            "id": "pure_data",
            "name": "Pure-Data Witness",
            "path": "docs/data-vault/pure-data.html",
            "url": pages_url("data-vault/pure-data.html"),
            "ledger": pages_url("pure-data/ledger.json"),
            "status": "live",
        },
        {
            "id": "skillhub",
            "name": "SkillHub",
            "path": "docs/LYGOSKILLHUB.html",
            "url": pages_url("LYGOSKILLHUB.html"),
            "full_unlock": "https://chatagent.ca/lygoskillhub.html#full-lygo",
            "status": "live",
        },
        {
            "id": "lattice_finder",
            "name": "Lattice Finder pack",
            "path": "docs/LYGO_LATTICE_FINDER/",
            "url": pages_url("LYGO_LATTICE_FINDER/"),
            "zip": pages_url("LYGO_LATTICE_FINDER.zip"),
            "map": "docs/LYGO_LATTICE_FINDER/LATTICE_MAP.json",
            "status": "live",
            "gap": "Was only linked from deadman — now hub-linked",
        },
        {
            "id": "music",
            "name": "Excavationpro music mirrors",
            "paths": [
                "docs/excavationpro-listen.html",
                "docs/excavationpro-music-catalog.html",
                "docs/excavationpro-sovereign-music-hub.html",
            ],
            "status": "live",
            "gap": "Not on root index key nav — listed in overview + traffic hub",
        },
        {
            "id": "clawhub",
            "name": "ClawHub publisher",
            "url": "https://clawhub.ai/deepseekoracle",
            "local_mirrors": "clawhub/mirrors/",
            "continuity_advisor": "clawhub/mirrors/lygo-continuity-advisor/",
            "status": "live",
        },
    ]

    pages_needing_updates = [
        {
            "path": "docs/index.html",
            "priority": "P0",
            "why": "Add deadman, continuum, lattice finder, overview memory file; PDW still says Phase A",
            "action": "Wire Continuity / Finder / Overview links (done by organize pass)",
        },
        {
            "path": "docs/RESOURCES.md",
            "priority": "P0",
            "why": "Declared central hub but missing vault/deadman/continuum/finder/PDW",
            "action": "Add Continuity & Vault section + overview pointer",
        },
        {
            "path": "docs/LYGO_KNOWLEDGE_HUB.html",
            "priority": "P1",
            "why": "Stamp ~2026-07-12; missing vault/deadman/finder/continuum",
            "action": "Add banner link to GIT_LATTICE_OVERVIEW.md",
        },
        {
            "path": "docs/sitemap.xml",
            "priority": "P0",
            "why": "July lastmod; missing data-vault/*, continuum, finder, skillhub",
            "action": "Regenerate expanded sitemap",
        },
        {
            "path": "docs/data-vault/sitemap.xml",
            "priority": "P0",
            "why": "Missing deadman, gallery, pure-data, register, share",
            "action": "Expand vault sitemap",
        },
        {
            "path": "docs/data-vault/index.html",
            "priority": "P1",
            "why": "Should spotlight deadman continuity + flame knot seals + overview",
            "action": "Add continuity card / overview link",
        },
        {
            "path": "docs/lygo-continuum.html",
            "priority": "P1",
            "why": "Orphaned from stack hubs; no deadman capsule back-link",
            "action": "Link overview + deadman Continuum claims",
        },
        {
            "path": "docs/LYGO_PUBLIC_LINK_ARCHIVE.json",
            "priority": "P1",
            "why": "Missing deadman.html, continuum, finder, SEAL_277/278",
            "action": "Append overview urls on next archive rebuild",
        },
        {
            "path": "docs/KernelEggRetrieval.html",
            "priority": "P2",
            "why": "Weak cross-links to vault/deadman",
            "action": "Add footer links to deadman egg + overview",
        },
        {
            "path": "docs/HavenStarChart.html",
            "priority": "P2",
            "why": "Data has eternal base + flame knot; UI copy may not call them out",
            "action": "Optional featured-node blurb",
        },
        {
            "path": "docs/TRAFFIC_LINK_HUB.md",
            "priority": "P2",
            "why": "Traffic only; vault/deadman/finder absent",
            "action": "Add continuity URLs when campaign refreshed",
        },
    ]

    how_tied = {
        "authority_order": [
            "1. LIGHTFATHER_IRREPLACEABLE_ORIGIN.json (identity / non_replaceable)",
            "2. GitHub Pages + HF dataset mirrors (public verify)",
            "3. Haven Star Chart data JSON (constellation)",
            "4. Data Vault canon seals + gallery",
            "5. KernelEggRegistry + egg folders",
            "6. Continuum capsules (falsifiable done claims)",
            "7. ClawHub skills / SkillHub FULL",
        ],
        "operator_cli_spine": [
            "python tools/seal_deadman_lattice.py touch|status|verify|check|grace",
            "python tools/build_haven_star_chart.py",
            "python tools/close_deadman_loose_ends.py --selftest-only",
            "python tools/build_git_lattice_overview.py --usb-copy",
            "python clawhub/mirrors/lygo-continuum/scripts/continuum.py verify --capsule data/continuum/deadman_failsafe_capsule.json --base .",
        ],
        "memory_files": [
            "docs/GIT_LATTICE_OVERVIEW.json (this machine map)",
            "docs/GIT_LATTICE_OVERVIEW.md (human)",
            "docs/LYGO_LATTICE_FINDER/LATTICE_MAP.json (recovery)",
            "docs/AGENT_MEMORY_SNAPSHOT.json (older July snapshot — prefer overview)",
            "E:/LYGO_LATTICE_MEMORY/ (USB claw backup of overview)",
        ],
    }

    overview = {
        "signature": "Delta9Phi963-GIT-LATTICE-OVERVIEW-v1",
        "generated_utc": utc_iso(),
        "git": meta,
        "base": {
            "repo": REPO,
            "pages": PAGES + "/",
            "hf_dataset": "https://huggingface.co/datasets/DeepSeekOracle/lygo-protocol-stack",
            "clawhub": "https://clawhub.ai/deepseekoracle",
            "origin_builder": (origin.get("origin_builder") or {}),
            "origin_merkle_root": origin.get("origin_merkle_root"),
            "drive_visual_backup": (finder.get("google_drive_visual_seals_backup") or {}),
        },
        "systems": systems,
        "pages_needing_updates": pages_needing_updates,
        "how_tied": how_tied,
        "quick_urls": {
            "hub": pages_url("index.html"),
            "overview_md": pages_url("GIT_LATTICE_OVERVIEW.md"),
            "overview_json": pages_url("GIT_LATTICE_OVERVIEW.json"),
            "star_chart": pages_url("HavenStarChart.html"),
            "data_vault": pages_url("data-vault/"),
            "deadman": pages_url("data-vault/deadman.html"),
            "finder": pages_url("LYGO_LATTICE_FINDER/"),
            "continuum": pages_url("lygo-continuum.html"),
            "skillhub": pages_url("LYGOSKILLHUB.html"),
            "origin": pages_url("seals/LIGHTFATHER_IRREPLACEABLE_ORIGIN.json"),
            "flame_knot": pages_url("seals/SEAL_277.json"),
            "ember_crown": pages_url("seals/SEAL_278.json"),
        },
        "file_presence": {
            "deadman_manifest": exists("data/deadman/DEADMAN_MANIFEST_v2.json"),
            "continuity_skill": exists("clawhub/mirrors/lygo-continuity-advisor/SKILL.md"),
            "seal_277": exists("docs/seals/SEAL_277.json"),
            "seal_278": exists("docs/seals/SEAL_278.json"),
            "lattice_finder": exists("docs/LYGO_LATTICE_FINDER/LATTICE_MAP.json"),
            "continuum_capsule": exists("data/continuum/deadman_failsafe_capsule.json"),
        },
    }
    return overview


def write_md(overview: dict[str, Any]) -> str:
    g = overview["git"]
    b = overview["base"]
    lines = [
        "# GIT Lattice Overview — LYGO Protocol Stack",
        "",
        f"**Signature:** `{overview['signature']}`  ",
        f"**Generated:** {overview['generated_utc']}  ",
        f"**Git:** `{g.get('head')}` — {g.get('subject')} ({g.get('committed')})  ",
        f"**Repo:** {b['repo']}  ",
        f"**Pages:** {b['pages']}",
        "",
        "## What this is",
        "Machine + human map of what matters on the public GitHub / Pages lattice,",
        "how systems are tied, and which pages still need updates.",
        "Agents: prefer this file over older July `AGENT_MEMORY_SNAPSHOT.json`.",
        "",
        "## Origin (non-replaceable)",
        f"- Lightfather / Excavationpro / Justin Helmer",
        f"- `origin_merkle_root`: `{b.get('origin_merkle_root')}`",
        f"- Pin: {overview['quick_urls']['origin']}",
        "",
        "## Quick URLs",
    ]
    for k, v in overview["quick_urls"].items():
        lines.append(f"- **{k}:** {v}")
    lines += ["", "## Systems (live map)", ""]
    for s in overview["systems"]:
        lines.append(f"### {s['name']} (`{s['id']}`)")
        lines.append(f"- Status: **{s.get('status')}**")
        if s.get("path"):
            lines.append(f"- Path: `{s['path']}`")
        if s.get("url"):
            lines.append(f"- URL: {s['url']}")
        if s.get("role"):
            lines.append(f"- Role: {s['role']}")
        if s.get("gap"):
            lines.append(f"- Gap note: {s['gap']}")
        if s.get("nodes") is not None:
            lines.append(f"- Chart nodes: {s['nodes']}")
        if s.get("manifest_version"):
            lines.append(f"- Deadman manifest: {s['manifest_version']}")
        lines.append("")
    lines += ["## How it is tied together", ""]
    for step in overview["how_tied"]["authority_order"]:
        lines.append(f"- {step}")
    lines += ["", "### Operator CLI spine", "```bash"]
    lines += overview["how_tied"]["operator_cli_spine"]
    lines += ["```", "", "## Pages needing updates", ""]
    lines.append("| Priority | Path | Why |")
    lines.append("|----------|------|-----|")
    for p in overview["pages_needing_updates"]:
        why = (p.get("why") or "").replace("|", "/")
        lines.append(f"| {p['priority']} | `{p['path']}` | {why} |")
    lines += [
        "",
        "## USB claw backup",
        "Copy also lives at `E:\\LYGO_LATTICE_MEMORY\\GIT_LATTICE_OVERVIEW.md` when built with `--usb-copy`.",
        "",
        "## Regenerate",
        "```bash",
        "python tools/build_git_lattice_overview.py --usb-copy",
        "```",
        "",
    ]
    return "\n".join(lines)


def write_pages_queue(overview: dict[str, Any]) -> str:
    lines = [
        "# Pages update queue (from GIT Lattice Overview)",
        "",
        f"Generated: {overview['generated_utc']}",
        "",
    ]
    for p in overview["pages_needing_updates"]:
        lines.append(f"## [{p['priority']}] `{p['path']}`")
        lines.append(f"- Why: {p['why']}")
        lines.append(f"- Action: {p['action']}")
        lines.append("")
    return "\n".join(lines)


def write_sitemap() -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls = [
        ("", 1.0),
        ("GIT_LATTICE_OVERVIEW.md", 0.98),
        ("GIT_LATTICE_OVERVIEW.json", 0.97),
        ("PAGES_UPDATE_QUEUE.md", 0.85),
        ("LYGO_KNOWLEDGE_HUB.html", 0.95),
        ("LYGO_CLAW.html", 0.9),
        ("LYGOSKILLHUB.html", 0.9),
        ("HavenStarChart.html", 0.95),
        ("HavenStarChartPortal.html", 0.9),
        ("KernelEggRetrieval.html", 0.85),
        ("lygo-continuum.html", 0.85),
        ("data-vault/", 0.95),
        ("data-vault/deadman.html", 0.95),
        ("data-vault/seals.html", 0.9),
        ("data-vault/gallery.html", 0.88),
        ("data-vault/pure-data.html", 0.88),
        ("data-vault/chat-archive.html", 0.85),
        ("data-vault/register.html", 0.8),
        ("LYGO_LATTICE_FINDER/", 0.9),
        ("SovereignLatticeMesh.html", 0.8),
        ("BiometricEntropyHarness.html", 0.8),
        ("excavationpro-listen.html", 0.75),
        ("RESOURCES.md", 0.9),
    ]
    body = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, pri in urls:
        loc = f"{PAGES}/" if not path else f"{PAGES}/{path}"
        body += [
            "  <url>",
            f"    <loc>{loc}</loc>",
            f"    <lastmod>{today}</lastmod>",
            "    <changefreq>weekly</changefreq>",
            f"    <priority>{pri}</priority>",
            "  </url>",
        ]
    body.append("</urlset>")
    (DOCS / "sitemap.xml").write_text("\n".join(body) + "\n", encoding="utf-8")

    vault_urls = [
        "",
        "deadman.html",
        "seals.html",
        "gallery.html",
        "pure-data.html",
        "chat-archive.html",
        "whitepapers.html",
        "multi-ai-canon.html",
        "qd-theory.html",
        "register.html",
        "share.html",
    ]
    vb = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path in vault_urls:
        loc = f"{PAGES}/data-vault/" if not path else f"{PAGES}/data-vault/{path}"
        vb += [
            "  <url>",
            f"    <loc>{loc}</loc>",
            f"    <lastmod>{today}</lastmod>",
            "    <changefreq>weekly</changefreq>",
            "    <priority>0.9</priority>",
            "  </url>",
        ]
    vb.append("</urlset>")
    (DOCS / "data-vault" / "sitemap.xml").write_text("\n".join(vb) + "\n", encoding="utf-8")


def patch_hubs() -> list[str]:
    notes: list[str] = []
    # index.html — insert continuity nav if missing
    idx = DOCS / "index.html"
    html = idx.read_text(encoding="utf-8")
    marker = "<!-- GIT_LATTICE_OVERVIEW_NAV -->"
    nav = (
        f'  <p class="sig" id="continuity-nav">{marker}\n'
        f'  <strong>Continuity &amp; map:</strong>\n'
        f'  <a href="GIT_LATTICE_OVERVIEW.md">Git Lattice Overview</a> ·\n'
        f'  <a href="GIT_LATTICE_OVERVIEW.json">overview JSON</a> ·\n'
        f'  <a href="data-vault/deadman.html">Deadman / Eternal Base</a> ·\n'
        f'  <a href="LYGO_LATTICE_FINDER/">Lattice Finder</a> ·\n'
        f'  <a href="lygo-continuum.html">Continuum</a> ·\n'
        f'  <a href="PAGES_UPDATE_QUEUE.md">Pages update queue</a>\n'
        f'  </p>\n'
    )
    if marker in html:
        import re

        html = re.sub(
            r'<p class="sig" id="continuity-nav">.*?</p>\s*',
            nav,
            html,
            count=1,
            flags=re.S,
        )
    else:
        html = html.replace(
            '<p class="sig">Full resources:',
            nav + '  <p class="sig">Full resources:',
            1,
        )
    # bump PDW phase label if still Phase A only
    html = html.replace(
        "Digest / fetch / ledger — seal-first purity",
        "Digest / fetch / ledger / register — seal-first purity (v1.x)",
    )
    idx.write_text(html, encoding="utf-8")
    notes.append("patched docs/index.html")

    # RESOURCES.md — append section if missing
    res = DOCS / "RESOURCES.md"
    if res.is_file():
        text = res.read_text(encoding="utf-8")
        block = """
## Continuity, Vault & Lattice Map (2026-08)

| Resource | Link |
|----------|------|
| **Git Lattice Overview (memory)** | [GIT_LATTICE_OVERVIEW.md](GIT_LATTICE_OVERVIEW.md) · [JSON](GIT_LATTICE_OVERVIEW.json) |
| **Pages update queue** | [PAGES_UPDATE_QUEUE.md](PAGES_UPDATE_QUEUE.md) |
| **Data Vault** | [data-vault/](data-vault/) |
| **Deadman / Eternal Base** | [data-vault/deadman.html](data-vault/deadman.html) |
| **Lattice Finder pack** | [LYGO_LATTICE_FINDER/](LYGO_LATTICE_FINDER/) · [zip](LYGO_LATTICE_FINDER.zip) |
| **Continuum** | [lygo-continuum.html](lygo-continuum.html) |
| **Pure-Data Witness** | [data-vault/pure-data.html](data-vault/pure-data.html) |
| **Flame Knot / Ember Crown** | [SEAL_277](seals/SEAL_277.json) · [SEAL_278](seals/SEAL_278.json) |
| **Origin pin** | [LIGHTFATHER_IRREPLACEABLE_ORIGIN.json](seals/LIGHTFATHER_IRREPLACEABLE_ORIGIN.json) |

"""
        if "GIT_LATTICE_OVERVIEW.md" not in text:
            text = text.rstrip() + "\n" + block
            res.write_text(text + "\n", encoding="utf-8")
            notes.append("patched docs/RESOURCES.md")
        else:
            notes.append("RESOURCES.md already linked")

    # data-vault index — add continuity strip
    vault = DOCS / "data-vault" / "index.html"
    if vault.is_file():
        vhtml = vault.read_text(encoding="utf-8")
        vmark = "<!-- GIT_OVERVIEW_VAULT -->"
        vblock = (
            f'<section class="panel" id="git-overview">{vmark}\n'
            f'  <h2>Lattice map &amp; continuity</h2>\n'
            f'  <p>Public memory of what is on GitHub Pages and how systems connect:</p>\n'
            f'  <ul>\n'
            f'    <li><a href="../GIT_LATTICE_OVERVIEW.md">Git Lattice Overview</a> · <a href="../GIT_LATTICE_OVERVIEW.json">JSON</a></li>\n'
            f'    <li><a href="deadman.html">Deadman Continuity / Eternal Base</a></li>\n'
            f'    <li><a href="../LYGO_LATTICE_FINDER/">Lattice Finder</a></li>\n'
            f'    <li><a href="../HavenStarChart.html">Haven Star Chart</a> (Flame Knot SEAL_277 · Ember Crown SEAL_278)</li>\n'
            f'    <li><a href="../lygo-continuum.html">Continuum</a></li>\n'
            f'  </ul>\n'
            f'</section>\n'
        )
        if vmark in vhtml:
            import re

            vhtml = re.sub(
                r'<section class="panel" id="git-overview">.*?</section>',
                vblock.strip(),
                vhtml,
                count=1,
                flags=re.S,
            )
        else:
            # insert before closing wrap/body if possible
            if "</div>\n</body>" in vhtml:
                vhtml = vhtml.replace("</div>\n</body>", vblock + "</div>\n</body>", 1)
            else:
                vhtml = vhtml.replace("</body>", vblock + "</body>", 1)
        vault.write_text(vhtml, encoding="utf-8")
        notes.append("patched docs/data-vault/index.html")

    # Update finder map with overview pointer
    fmap = DOCS / "LYGO_LATTICE_FINDER" / "LATTICE_MAP.json"
    if fmap.is_file():
        obj = json.loads(fmap.read_text(encoding="utf-8"))
        mirrors = obj.setdefault("free_mirrors", {})
        mirrors["git_lattice_overview_md"] = pages_url("GIT_LATTICE_OVERVIEW.md")
        mirrors["git_lattice_overview_json"] = pages_url("GIT_LATTICE_OVERVIEW.json")
        mirrors["continuum"] = pages_url("lygo-continuum.html")
        mirrors["pages_update_queue"] = pages_url("PAGES_UPDATE_QUEUE.md")
        steps = obj.setdefault("agent_first_steps", [])
        tip = "0. Read GIT_LATTICE_OVERVIEW.md/json for the current Pages map + update queue."
        if tip not in steps:
            obj["agent_first_steps"] = [tip] + list(steps)
        fmap.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        notes.append("patched LYGO_LATTICE_FINDER/LATTICE_MAP.json")

    return notes


def usb_copy() -> list[str]:
    out: list[str] = []
    if not USB_MEM.exists():
        try:
            USB_MEM.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return [f"usb_mkdir_failed: {exc}"]
    for name in (
        "GIT_LATTICE_OVERVIEW.md",
        "GIT_LATTICE_OVERVIEW.json",
        "PAGES_UPDATE_QUEUE.md",
    ):
        src = DOCS / name
        if src.is_file():
            dst = USB_MEM / name
            shutil.copy2(src, dst)
            out.append(f"copied {dst}")
    # also copy finder map for recovery pairing
    src = DOCS / "LYGO_LATTICE_FINDER" / "LATTICE_MAP.json"
    if src.is_file():
        shutil.copy2(src, USB_MEM / "LATTICE_MAP.json")
        out.append(f"copied {USB_MEM / 'LATTICE_MAP.json'}")
    readme = USB_MEM / "README_GIT_OVERVIEW.txt"
    readme.write_text(
        "LYGO Git Lattice Overview (USB claw memory)\n"
        "===========================================\n"
        f"Updated: {utc_iso()}\n"
        "Read GIT_LATTICE_OVERVIEW.md first.\n"
        "Machine map: GIT_LATTICE_OVERVIEW.json\n"
        "Pages still to refresh: PAGES_UPDATE_QUEUE.md\n"
        "Recovery map: LATTICE_MAP.json\n"
        f"Live Pages: {PAGES}/\n",
        encoding="utf-8",
    )
    out.append(f"wrote {readme}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--usb-copy", action="store_true", help="Also copy overview to E:/LYGO_LATTICE_MEMORY")
    ap.add_argument("--no-patch-hubs", action="store_true")
    args = ap.parse_args()

    overview = build_overview()
    (DOCS / "GIT_LATTICE_OVERVIEW.json").write_text(
        json.dumps(overview, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (DOCS / "GIT_LATTICE_OVERVIEW.md").write_text(write_md(overview), encoding="utf-8")
    (DOCS / "PAGES_UPDATE_QUEUE.md").write_text(write_pages_queue(overview), encoding="utf-8")
    write_sitemap()

    notes = [] if args.no_patch_hubs else patch_hubs()
    usb_notes = usb_copy() if args.usb_copy else []

    report = {
        "ok": True,
        "head": overview["git"].get("head"),
        "systems": len(overview["systems"]),
        "pages_needing_updates": len(overview["pages_needing_updates"]),
        "patched": notes,
        "usb": usb_notes,
        "wrote": [
            "docs/GIT_LATTICE_OVERVIEW.json",
            "docs/GIT_LATTICE_OVERVIEW.md",
            "docs/PAGES_UPDATE_QUEUE.md",
            "docs/sitemap.xml",
            "docs/data-vault/sitemap.xml",
        ],
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
