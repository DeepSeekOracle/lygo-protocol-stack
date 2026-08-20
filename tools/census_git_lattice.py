#!/usr/bin/env python3
"""Full git-tracked census of lygo-protocol-stack → Overview v2.

Walks `git ls-files`, classifies every path, flags likely orphans, and writes:
  docs/GIT_LATTICE_OVERVIEW.json  (v2 merges prior + census)
  docs/GIT_LATTICE_OVERVIEW.md
  docs/GIT_REPO_CENSUS.json       (full machine census)
  docs/GIT_REPO_CENSUS.md         (human summary)
  Optional: E:\\LYGO_LATTICE_MEMORY\\

Usage:
  python tools/census_git_lattice.py
  python tools/census_git_lattice.py --usb-copy
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
USB = Path("E:/LYGO_LATTICE_MEMORY")
PAGES = "https://deepseekoracle.github.io/lygo-protocol-stack"
REPO = "https://github.com/DeepSeekOracle/lygo-protocol-stack"

# Top-level buckets that define the stack
BUCKET_RULES: list[tuple[str, str]] = [
    (r"^docs/", "docs_pages"),
    (r"^tools/", "tools"),
    (r"^data/", "data_runtime"),
    (r"^clawhub/", "clawhub"),
    (r"^tests/", "tests"),
    (r"^stack/", "stack_core"),
    (r"^protocol[0-9]_/", "protocols"),
    (r"^protocol_bridge/", "protocols"),
    (r"^protocol9_failsafe/", "protocols"),
    (r"^lygo_", "products"),
    (r"^pxpipe_lygo/", "products"),
    (r"^hf_deploy/|^_hf_", "hf_deploy"),
    (r"^\.github/", "ci"),
    (r"^README|^LICENSE|^CHANGELOG|^Dockerfile|^docker-compose", "repo_root"),
]


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_ls_files() -> list[str]:
    out = subprocess.check_output(["git", "ls-files", "-z"], cwd=str(ROOT))
    return [p for p in out.decode("utf-8", errors="replace").split("\0") if p]


def git_meta() -> dict[str, str]:
    def run(*a: str) -> str:
        try:
            return subprocess.check_output(["git", *a], cwd=str(ROOT), text=True).strip()
        except Exception:
            return ""

    return {
        "head": run("rev-parse", "--short", "HEAD"),
        "subject": run("log", "-1", "--format=%s"),
        "committed": run("log", "-1", "--format=%cI"),
        "branch": run("branch", "--show-current"),
        "remote": run("remote", "get-url", "origin") or REPO,
        "commit_count": run("rev-list", "--count", "HEAD"),
    }


def bucket_for(path: str) -> str:
    for pat, name in BUCKET_RULES:
        if re.search(pat, path):
            return name
    top = path.split("/", 1)[0]
    if top.startswith("protocol"):
        return "protocols"
    return "other"


def ext_of(path: str) -> str:
    p = Path(path)
    if p.suffix:
        return p.suffix.lower()
    return "(none)"


def classify_docs(path: str) -> str:
    if path.endswith(".html"):
        return "html_page"
    if path.startswith("docs/data-vault/"):
        return "data_vault"
    if path.startswith("docs/seals/"):
        return "seals_canon"
    if path.startswith("docs/kernel_eggs/"):
        return "kernel_eggs_pages"
    if path.startswith("docs/haven_star_chart/"):
        return "star_chart_data"
    if path.startswith("docs/LYGO_LATTICE_FINDER/"):
        return "lattice_finder"
    if path.startswith("docs/lygo-full-skills/"):
        return "skillhub_packs"
    if path.startswith("docs/clawhub") or "clawhub" in path:
        return "clawhub_docs"
    if path.endswith(".md"):
        return "markdown_doc"
    if path.endswith(".json"):
        return "json_data"
    return "docs_other"


def scan_html_hrefs(files: list[str]) -> dict[str, Any]:
    """Collect internal href targets from docs HTML for orphan-page detection."""
    href_re = re.compile(r"""href=["']([^"'#]+)""", re.I)
    linked: set[str] = set()
    html_files = [f for f in files if f.startswith("docs/") and f.endswith(".html")]
    for rel in html_files:
        try:
            text = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for raw in href_re.findall(text):
            if raw.startswith(("http://", "https://", "mailto:", "javascript:")):
                continue
            # normalize relative to docs/
            base = Path(rel).parent
            try:
                target = (base / raw).resolve()
                try:
                    rel_t = target.relative_to(ROOT.resolve()).as_posix()
                except ValueError:
                    continue
                linked.add(rel_t)
                # also bare filename under docs
                if rel_t.startswith("docs/"):
                    linked.add(rel_t)
            except Exception:
                continue
    # pages linked from README / RESOURCES / overview
    for extra in ("README.md", "docs/RESOURCES.md", "docs/GIT_LATTICE_OVERVIEW.md", "docs/index.html"):
        p = ROOT / extra
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for raw in href_re.findall(text) + re.findall(r"\((docs/[^)\s]+)\)", text):
            if raw.startswith("http"):
                continue
            cand = raw
            if not cand.startswith("docs/") and (DOCS / cand).exists():
                cand = f"docs/{cand}"
            linked.add(cand.replace("\\", "/"))
    return {"linked_targets": sorted(linked), "html_scanned": len(html_files)}


def find_orphan_html(files: list[str], linked: set[str]) -> list[dict[str, str]]:
    orphans = []
    # Always-considered entrypoints (not orphans even if weakly linked)
    entry = {
        "docs/index.html",
        "docs/HavenStarChart.html",
        "docs/HavenStarChartPortal.html",
        "docs/LYGOSKILLHUB.html",
        "docs/LYGO_CLAW.html",
        "docs/LYGO_KNOWLEDGE_HUB.html",
        "docs/SovereignLatticeMesh.html",
        "docs/BiometricEntropyHarness.html",
        "docs/KernelEggRetrieval.html",
        "docs/data-vault/index.html",
        "docs/data-vault/deadman.html",
        "docs/lygo-continuum.html",
    }
    for f in files:
        if not (f.startswith("docs/") and f.endswith(".html")):
            continue
        if f in entry:
            continue
        # skip domain-root mirrors / archive noise for orphan severity
        if any(
            x in f
            for x in (
                "/domain-roots/",
                "/bpmfinder.ca-root/",
                "/archive/",
                "/lygo-full-skills/",
                "/builder/",
            )
        ):
            severity = "low"
        else:
            severity = "medium"
        # linked if any linked target equals or contains basename path
        hit = f in linked or any(f.endswith(Path(t).name) and t.endswith(Path(f).name) for t in linked)
        # also check if basename mentioned
        base = Path(f).name
        if not hit:
            hit = any(base in t for t in linked)
        if not hit:
            orphans.append({"path": f, "severity": severity, "reason": "html_not_found_in_hub_href_scan"})
    return orphans


def clawhub_mirrors() -> list[dict[str, str]]:
    root = ROOT / "clawhub" / "mirrors"
    if not root.is_dir():
        return []
    rows = []
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        skill = d / "SKILL.md"
        rows.append(
            {
                "slug": d.name,
                "has_skill_md": skill.is_file(),
                "path": f"clawhub/mirrors/{d.name}/",
            }
        )
    return rows


def protocol_dirs(files: list[str]) -> list[str]:
    tops = sorted({p.split("/")[0] for p in files if p.startswith("protocol")})
    return tops


def data_subtrees(files: list[str]) -> dict[str, int]:
    c: Counter[str] = Counter()
    for p in files:
        if not p.startswith("data/"):
            continue
        parts = p.split("/")
        key = parts[1] if len(parts) > 1 else "(root)"
        c[key] += 1
    return dict(c.most_common())


def tools_deadman_related(files: list[str]) -> list[str]:
    keys = ("deadman", "haven_star", "continuum", "pure_data", "kernel_egg", "lattice", "overview", "census")
    out = []
    for p in files:
        if not p.startswith("tools/"):
            continue
        low = p.lower()
        if any(k in low for k in keys):
            out.append(p)
    return sorted(out)


def build_census(files: list[str]) -> dict[str, Any]:
    by_bucket: dict[str, list[str]] = defaultdict(list)
    by_ext: Counter[str] = Counter()
    docs_kind: Counter[str] = Counter()
    for p in files:
        by_bucket[bucket_for(p)].append(p)
        by_ext[ext_of(p)] += 1
        if p.startswith("docs/"):
            docs_kind[classify_docs(p)] += 1

    href_scan = scan_html_hrefs(files)
    linked = set(href_scan["linked_targets"])
    orphans = find_orphan_html(files, linked)

    html_pages = sorted(p for p in files if p.startswith("docs/") and p.endswith(".html"))
    # Important public pages presence checklist
    must = [
        "docs/index.html",
        "docs/HavenStarChart.html",
        "docs/data-vault/index.html",
        "docs/data-vault/deadman.html",
        "docs/data-vault/pure-data.html",
        "docs/lygo-continuum.html",
        "docs/LYGOSKILLHUB.html",
        "docs/KernelEggRetrieval.html",
        "docs/LYGO_LATTICE_FINDER/LATTICE_MAP.json",
        "docs/seals/LIGHTFATHER_IRREPLACEABLE_ORIGIN.json",
        "docs/seals/SEAL_277.json",
        "docs/seals/SEAL_278.json",
        "docs/GIT_LATTICE_OVERVIEW.md",
        "data/deadman/DEADMAN_MANIFEST_v2.json",
        "clawhub/mirrors/lygo-continuity-advisor/SKILL.md",
        "tools/seal_deadman_lattice.py",
        "tools/build_haven_star_chart.py",
        "tools/build_git_lattice_overview.py",
    ]
    presence = {m: (m in set(files) or (ROOT / m).is_file()) for m in must}

    # tools referenced in overview/docs vs all tools
    tools_all = [p for p in files if p.startswith("tools/") and p.endswith(".py")]
    # heuristic: unreferenced tools = not mentioned in docs/*.md or README (sample)
    mention_blob = ""
    for rel in ("README.md", "docs/GIT_LATTICE_OVERVIEW.md", "docs/RESOURCES.md", "docs/seals/DEADMAN_OPERATOR_RUNBOOK.md"):
        fp = ROOT / rel
        if fp.is_file():
            mention_blob += fp.read_text(encoding="utf-8", errors="replace")
    unused_tools = []
    for t in tools_all:
        name = Path(t).name
        if name.startswith("_"):
            continue  # private helpers often intentional
        if name not in mention_blob and t not in mention_blob:
            # only flag if also not imported by name in a few key tools — keep light
            unused_tools.append(t)
    # cap noise
    unused_tools_sample = unused_tools[:80]

    census = {
        "signature": "Delta9Phi963-GIT-REPO-CENSUS-v1",
        "generated_utc": utc_iso(),
        "git": git_meta(),
        "totals": {
            "tracked_files": len(files),
            "buckets": {k: len(v) for k, v in sorted(by_bucket.items(), key=lambda kv: -len(kv[1]))},
            "extensions_top": by_ext.most_common(25),
            "docs_kinds": dict(docs_kind),
            "html_pages": len(html_pages),
            "clawhub_mirrors": len(clawhub_mirrors()),
            "protocol_dirs": protocol_dirs(files),
            "tools_py": len(tools_all),
            "tests_files": len(by_bucket.get("tests", [])),
        },
        "data_subtrees": data_subtrees(files),
        "clawhub_mirrors": clawhub_mirrors(),
        "protocol_dirs": protocol_dirs(files),
        "products": sorted(
            {
                p.split("/")[0]
                for p in files
                if p.startswith("lygo_") or p.startswith("pxpipe_lygo")
            }
        ),
        "must_have_presence": presence,
        "must_have_missing": [k for k, v in presence.items() if not v],
        "html_pages": html_pages,
        "href_scan": {"html_scanned": href_scan["html_scanned"], "linked_count": len(linked)},
        "orphan_html": orphans,
        "orphan_html_count": len(orphans),
        "tools_lattice_related": tools_deadman_related(files),
        "tools_unmentioned_in_hub_docs_sample": unused_tools_sample,
        "tools_unmentioned_count": len(unused_tools),
        "bucket_samples": {k: sorted(v)[:30] for k, v in by_bucket.items()},
    }
    return census


def write_census_md(c: dict[str, Any]) -> str:
    g = c["git"]
    t = c["totals"]
    lines = [
        "# GIT Repo Census — full tracked tree",
        "",
        f"**Signature:** `{c['signature']}`  ",
        f"**Generated:** {c['generated_utc']}  ",
        f"**Git:** `{g.get('head')}` — {g.get('subject')}  ",
        f"**Tracked files:** {t['tracked_files']} · **Commits:** {g.get('commit_count')}",
        "",
        "## Bucket counts",
        "",
        "| Bucket | Files |",
        "|--------|------:|",
    ]
    for k, n in t["buckets"].items():
        lines.append(f"| `{k}` | {n} |")
    lines += [
        "",
        f"## Protocols ({len(c['protocol_dirs'])})",
        "",
        ", ".join(f"`{p}`" for p in c["protocol_dirs"]),
        "",
        f"## Products ({len(c['products'])})",
        "",
        ", ".join(f"`{p}`" for p in c["products"]),
        "",
        f"## ClawHub mirrors ({c['totals']['clawhub_mirrors']})",
        "",
    ]
    missing_skill = [m["slug"] for m in c["clawhub_mirrors"] if not m["has_skill_md"]]
    lines.append(f"- With SKILL.md: {c['totals']['clawhub_mirrors'] - len(missing_skill)}")
    if missing_skill:
        lines.append(f"- Missing SKILL.md ({len(missing_skill)}): " + ", ".join(missing_skill[:40]))
    lines += ["", "## Data/ subtrees (file counts)", ""]
    for k, n in list(c["data_subtrees"].items())[:25]:
        lines.append(f"- `{k}`: {n}")
    lines += ["", "## Must-have presence", ""]
    for k, ok in c["must_have_presence"].items():
        lines.append(f"- {'OK' if ok else 'MISSING'}: `{k}`")
    lines += [
        "",
        f"## Orphan HTML pages (href-scan, {c['orphan_html_count']})",
        "",
        "These `docs/**/*.html` files were not clearly linked from scanned hubs/README/RESOURCES/overview.",
        "Severity `low` = domain-root/archive/full-skills noise.",
        "",
    ]
    for o in c["orphan_html"][:60]:
        lines.append(f"- [{o['severity']}] `{o['path']}`")
    if c["orphan_html_count"] > 60:
        lines.append(f"- … +{c['orphan_html_count'] - 60} more (see JSON)")
    lines += [
        "",
        f"## Tools unmentioned in hub docs (sample {len(c['tools_unmentioned_in_hub_docs_sample'])} / {c['tools_unmentioned_count']})",
        "",
        "Heuristic only — many are still used by other scripts. Investigate before deleting.",
        "",
    ]
    for tpath in c["tools_unmentioned_in_hub_docs_sample"][:40]:
        lines.append(f"- `{tpath}`")
    lines += [
        "",
        "## Lattice-related tools",
        "",
    ]
    for tpath in c["tools_lattice_related"]:
        lines.append(f"- `{tpath}`")
    lines += [
        "",
        "## Regenerate",
        "```bash",
        "python tools/census_git_lattice.py --usb-copy",
        "```",
        "",
    ]
    return "\n".join(lines)


def merge_overview_v2(census: dict[str, Any]) -> dict[str, Any]:
    # Prefer regenerating via build_git_lattice_overview pieces + census summary
    prior_path = DOCS / "GIT_LATTICE_OVERVIEW.json"
    prior = {}
    if prior_path.is_file():
        prior = json.loads(prior_path.read_text(encoding="utf-8"))

    overview = {
        "signature": "Delta9Phi963-GIT-LATTICE-OVERVIEW-v2",
        "generated_utc": utc_iso(),
        "git": census["git"],
        "census": {
            "tracked_files": census["totals"]["tracked_files"],
            "buckets": census["totals"]["buckets"],
            "html_pages": census["totals"]["html_pages"],
            "clawhub_mirrors": census["totals"]["clawhub_mirrors"],
            "tools_py": census["totals"]["tools_py"],
            "protocol_dirs": census["protocol_dirs"],
            "products": census["products"],
            "orphan_html_count": census["orphan_html_count"],
            "must_have_missing": census["must_have_missing"],
            "census_json": "docs/GIT_REPO_CENSUS.json",
            "census_md": "docs/GIT_REPO_CENSUS.md",
            "full_scan": True,
            "note": "v2 includes full git ls-files census (not Pages-only).",
        },
        "base": prior.get("base")
        or {
            "repo": REPO,
            "pages": PAGES + "/",
            "hf_dataset": "https://huggingface.co/datasets/DeepSeekOracle/lygo-protocol-stack",
            "clawhub": "https://clawhub.ai/deepseekoracle",
        },
        "systems": prior.get("systems") or [],
        "pages_needing_updates": prior.get("pages_needing_updates") or [],
        "how_tied": prior.get("how_tied") or {},
        "quick_urls": prior.get("quick_urls") or {},
        "file_presence": census["must_have_presence"],
        "orphan_html_medium": [o for o in census["orphan_html"] if o.get("severity") == "medium"][:40],
        "data_subtrees_top": dict(list(census["data_subtrees"].items())[:20]),
        "clawhub_mirror_slugs": [m["slug"] for m in census["clawhub_mirrors"]],
    }
    # Ensure quick urls include census
    overview.setdefault("quick_urls", {})
    overview["quick_urls"]["census_md"] = f"{PAGES}/GIT_REPO_CENSUS.md"
    overview["quick_urls"]["census_json"] = f"{PAGES}/GIT_REPO_CENSUS.json"
    overview["quick_urls"]["overview_md"] = f"{PAGES}/GIT_LATTICE_OVERVIEW.md"
    overview["quick_urls"]["overview_json"] = f"{PAGES}/GIT_LATTICE_OVERVIEW.json"
    return overview


def write_overview_md_v2(o: dict[str, Any]) -> str:
    g = o["git"]
    c = o["census"]
    lines = [
        "# GIT Lattice Overview v2 — full repo census",
        "",
        f"**Signature:** `{o['signature']}`  ",
        f"**Generated:** {o['generated_utc']}  ",
        f"**Git:** `{g.get('head')}` — {g.get('subject')}  ",
        f"**Full scan:** YES — `{c['tracked_files']}` tracked files",
        "",
        "## Scope honesty",
        "v1 mapped Pages hubs (~12 systems). **v2 adds a full `git ls-files` census** of the repository:",
        "protocols, tools, data/, clawhub mirrors, products, tests, CI, docs HTML orphans.",
        "",
        f"- Full census: [{c['census_md']}]({c['census_md']}) · [{c['census_json']}]({c['census_json']})",
        "",
        "## Repo scale",
        "",
        "| Metric | Count |",
        "|--------|------:|",
        f"| Tracked files | {c['tracked_files']} |",
        f"| docs HTML pages | {c['html_pages']} |",
        f"| tools/*.py | {c['tools_py']} |",
        f"| ClawHub mirrors | {c['clawhub_mirrors']} |",
        f"| Protocol dirs | {len(c['protocol_dirs'])} |",
        f"| Orphan HTML (href-scan) | {c['orphan_html_count']} |",
        "",
        "### Buckets",
        "",
    ]
    for k, n in c["buckets"].items():
        lines.append(f"- `{k}`: {n}")
    lines += ["", "### Protocols", "", ", ".join(f"`{p}`" for p in c["protocol_dirs"]), ""]
    lines += ["### Products", "", ", ".join(f"`{p}`" for p in c["products"]), ""]
    if c.get("must_have_missing"):
        lines += ["## Missing must-haves", ""]
        for m in c["must_have_missing"]:
            lines.append(f"- `{m}`")
    else:
        lines += ["## Must-haves", "", "All checklist paths present.", ""]
    lines += ["## Medium-severity orphan HTML (sample)", ""]
    for ohtml in o.get("orphan_html_medium") or []:
        lines.append(f"- `{ohtml['path']}`")
    lines += ["", "## Public systems (from v1 map)", ""]
    for s in o.get("systems") or []:
        lines.append(f"- **{s.get('name')}** (`{s.get('id')}`) — {s.get('url') or s.get('path')}")
    lines += [
        "",
        "## Quick URLs",
        "",
    ]
    for k, v in (o.get("quick_urls") or {}).items():
        lines.append(f"- **{k}:** {v}")
    lines += [
        "",
        "## USB claw",
        "`E:\\LYGO_LATTICE_MEMORY\\` — overview + census copies when built with `--usb-copy`.",
        "",
        "## Regenerate",
        "```bash",
        "python tools/build_git_lattice_overview.py --usb-copy",
        "python tools/census_git_lattice.py --usb-copy",
        "```",
        "",
    ]
    return "\n".join(lines)


def usb_copy(paths: list[Path]) -> list[str]:
    notes = []
    try:
        USB.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return [f"usb_failed: {exc}"]
    for p in paths:
        if p.is_file():
            dst = USB / p.name
            shutil.copy2(p, dst)
            notes.append(str(dst))
    (USB / "README_GIT_OVERVIEW.txt").write_text(
        "LYGO Git Lattice Overview v2 + full repo census\n"
        "==============================================\n"
        f"Updated: {utc_iso()}\n"
        "1. GIT_LATTICE_OVERVIEW.md  (hub map + scale)\n"
        "2. GIT_REPO_CENSUS.md       (full tracked-tree census)\n"
        "3. GIT_REPO_CENSUS.json     (machine)\n"
        "4. PAGES_UPDATE_QUEUE.md    (pages still to refresh)\n"
        f"Live: {PAGES}/GIT_LATTICE_OVERVIEW.md\n",
        encoding="utf-8",
    )
    notes.append(str(USB / "README_GIT_OVERVIEW.txt"))
    return notes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--usb-copy", action="store_true")
    args = ap.parse_args()

    files = git_ls_files()
    census = build_census(files)
    overview = merge_overview_v2(census)

    census_json = DOCS / "GIT_REPO_CENSUS.json"
    census_md = DOCS / "GIT_REPO_CENSUS.md"
    overview_json = DOCS / "GIT_LATTICE_OVERVIEW.json"
    overview_md = DOCS / "GIT_LATTICE_OVERVIEW.md"

    census_json.write_text(json.dumps(census, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    census_md.write_text(write_census_md(census), encoding="utf-8")
    overview_json.write_text(json.dumps(overview, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    overview_md.write_text(write_overview_md_v2(overview), encoding="utf-8")

    # Expand pages update queue with orphan medium items
    queue = DOCS / "PAGES_UPDATE_QUEUE.md"
    q = [
        "# Pages update queue (Overview v2 + census)",
        "",
        f"Generated: {utc_iso()}",
        "",
        "## From hub audit",
        "",
    ]
    for p in overview.get("pages_needing_updates") or []:
        q.append(f"### [{p.get('priority','P?')}] `{p.get('path')}`")
        q.append(f"- Why: {p.get('why')}")
        q.append(f"- Action: {p.get('action')}")
        q.append("")
    q += ["## Medium orphan HTML (from full census href-scan)", ""]
    for ohtml in overview.get("orphan_html_medium") or []:
        q.append(f"- `{ohtml['path']}` — consider linking from index/RESOURCES/Knowledge Hub or archive")
    q.append("")
    queue.write_text("\n".join(q), encoding="utf-8")

    usb_notes = []
    if args.usb_copy:
        usb_notes = usb_copy(
            [overview_md, overview_json, census_md, census_json, queue, DOCS / "LYGO_LATTICE_FINDER" / "LATTICE_MAP.json"]
        )

    report = {
        "ok": True,
        "tracked_files": len(files),
        "html_pages": census["totals"]["html_pages"],
        "orphan_html": census["orphan_html_count"],
        "clawhub_mirrors": census["totals"]["clawhub_mirrors"],
        "tools_py": census["totals"]["tools_py"],
        "must_have_missing": census["must_have_missing"],
        "head": census["git"].get("head"),
        "usb": usb_notes,
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
