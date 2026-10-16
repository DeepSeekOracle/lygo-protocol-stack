#!/usr/bin/env python3
"""
LYGO SkillSpector BUILDER (FULL SkillHub only).

Extra operator tools for full-stack hosts:
  - HTML multi-skill batch report
  - multi-root gate (CI matrix)
  - JSON CI summary for dashboards

Public ClawHub tentacle = scan/gate/batch/report only.
This module ships unlocked on https://chatagent.ca/lygoskillhub.html#full-lygo

Still: pure stdlib. No network. No subprocess. No auto-install.
Writes under skill state/ only with --i-consent.
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
import skill_spector as core  # noqa: E402

STATE = SKILL_ROOT / "state"
SIG = "Delta9Phi963-SKILL-SPECTOR-BUILDER-v1.0.0"
VERSION = "1.0.0"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def scan_roots(roots: list[Path], max_per: int = 200) -> list[dict]:
    results: list[dict] = []
    for root in roots:
        if not root.is_dir():
            continue
        n = 0
        for child in sorted(root.iterdir()):
            if not child.is_dir() or not (child / "SKILL.md").is_file():
                continue
            if child.name.startswith("."):
                continue
            rep = core.scan_skill(child)
            results.append(
                {
                    "skill": rep.skill_name or child.name,
                    "path": str(child),
                    "root": str(root),
                    "band": rep.risk_band,
                    "score": rep.risk_score,
                    "mismatches": rep.mismatches,
                    "recommendation": rep.recommendation,
                    "files": rep.files_scanned,
                }
            )
            n += 1
            if n >= max_per:
                break
    order = {"critical": 0, "high": 1, "elevated": 2, "low": 3, "clear": 4, "unknown": 5}
    results.sort(key=lambda r: (order.get(r["band"], 9), -r["score"]))
    return results


def html_report(results: list[dict], title: str = "SkillSpector Builder batch") -> str:
    rows = []
    for r in results:
        band = html.escape(r["band"])
        color = {
            "critical": "#8b0000",
            "high": "#c0392b",
            "elevated": "#d68910",
            "low": "#1e8449",
            "clear": "#196f3d",
        }.get(r["band"], "#555")
        mm = "; ".join(r.get("mismatches") or []) or "—"
        rows.append(
            f"<tr><td><strong style='color:{color}'>{band}</strong></td>"
            f"<td>{r['score']}</td>"
            f"<td>{html.escape(r['skill'])}</td>"
            f"<td><code>{html.escape(r['path'])}</code></td>"
            f"<td>{html.escape(mm)}</td>"
            f"<td>{html.escape(r.get('recommendation') or '')}</td></tr>"
        )
    body = "\n".join(rows) if rows else "<tr><td colspan='6'>No skills scanned</td></tr>"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{html.escape(title)}</title>
<style>
body{{font-family:system-ui,sans-serif;margin:1.5rem;background:#0b0f14;color:#e8eef5}}
h1{{font-size:1.25rem}} table{{border-collapse:collapse;width:100%;font-size:.9rem}}
th,td{{border:1px solid #2a3544;padding:.45rem .55rem;text-align:left;vertical-align:top}}
th{{background:#15202b}} code{{font-size:.8rem;word-break:break-all}}
.meta{{color:#8aa0b5;font-size:.85rem;margin-bottom:1rem}}
</style>
</head>
<body>
<h1>🔭 {html.escape(title)}</h1>
<p class="meta">{SIG} · {utc_now()} · {len(results)} skills · local only · no network</p>
<table>
<thead><tr><th>Band</th><th>Score</th><th>Skill</th><th>Path</th><th>Mismatches</th><th>Rec</th></tr></thead>
<tbody>
{body}
</tbody>
</table>
<p class="meta">FULL unlocked builder · SkillHub · Δ9Φ963</p>
</body>
</html>
"""


def write_under_state(name: str, content: str) -> Path:
    STATE.mkdir(parents=True, exist_ok=True)
    out = STATE / Path(name).name
    out.write_text(content, encoding="utf-8")
    return out.resolve()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="skill-spector-builder", description="FULL SkillSpector builder tools")
    sub = ap.add_subparsers(dest="cmd")

    p_html = sub.add_parser("html-batch", help="HTML report for one or more skill roots")
    p_html.add_argument("roots", nargs="+", help="Directories containing skill packages")
    p_html.add_argument("--max", type=int, default=200)
    p_html.add_argument("--write", default="batch_report.html")
    p_html.add_argument("--i-consent", action="store_true")

    p_multi = sub.add_parser("multi-gate", help="Gate many roots; fail if any skill worse than max-band")
    p_multi.add_argument("roots", nargs="+")
    p_multi.add_argument("--max-band", default="elevated", choices=core.BAND_ORDER)
    p_multi.add_argument("--max", type=int, default=200)
    p_multi.add_argument("--json", action="store_true")

    p_ci = sub.add_parser("ci-summary", help="Compact JSON summary for CI dashboards")
    p_ci.add_argument("roots", nargs="+")
    p_ci.add_argument("--max", type=int, default=200)
    p_ci.add_argument("--write", default="")
    p_ci.add_argument("--i-consent", action="store_true")

    sub.add_parser("version")

    args = ap.parse_args(argv)
    cmd = args.cmd or "version"

    if cmd == "version":
        print(json.dumps({"ok": True, "signature": SIG, "version": VERSION, "channel": "FULL_BUILDER"}, indent=2))
        return 0

    if cmd == "html-batch":
        roots = [Path(r).expanduser().resolve() for r in args.roots]
        results = scan_roots(roots, max_per=args.max)
        doc = html_report(results)
        print(doc if not args.i_consent else f"<!-- {len(results)} skills -->")
        if args.write:
            if not args.i_consent:
                print(json.dumps({"written": False, "hint": "pass --i-consent"}))
                return 2
            path = write_under_state(args.write, doc)
            print(json.dumps({"written": True, "path": str(path), "scanned": len(results)}))
        worst = results[0]["band"] if results else "clear"
        return 10 if worst in ("critical", "high") else (5 if worst == "elevated" else 0)

    if cmd == "multi-gate":
        roots = [Path(r).expanduser().resolve() for r in args.roots]
        results = scan_roots(roots, max_per=args.max)
        max_i = core.BAND_ORDER.index(args.max_band)
        fails = []
        for r in results:
            bi = core.BAND_ORDER.index(r["band"]) if r["band"] in core.BAND_ORDER else 4
            if bi > max_i or r.get("mismatches"):
                fails.append(r)
        out = {
            "ok": len(fails) == 0,
            "signature": SIG,
            "scanned": len(results),
            "max_band": args.max_band,
            "failures": fails[:50],
        }
        print(json.dumps(out, indent=2))
        if fails:
            worst = fails[0]["band"]
            return 10 if worst in ("critical", "high") else 5
        return 0

    if cmd == "ci-summary":
        roots = [Path(r).expanduser().resolve() for r in args.roots]
        results = scan_roots(roots, max_per=args.max)
        counts: dict[str, int] = {}
        for r in results:
            counts[r["band"]] = counts.get(r["band"], 0) + 1
        summary = {
            "ok": True,
            "signature": SIG,
            "scanned_utc": utc_now(),
            "scanned": len(results),
            "band_counts": counts,
            "worst": results[0]["band"] if results else "clear",
            "top": results[:15],
        }
        print(json.dumps(summary, indent=2))
        if args.write:
            if not args.i_consent:
                print(json.dumps({"written": False, "hint": "pass --i-consent"}))
            else:
                path = write_under_state(args.write, json.dumps(summary, indent=2) + "\n")
                print(json.dumps({"written": True, "path": str(path)}))
        worst = summary["worst"]
        return 10 if worst in ("critical", "high") else (5 if worst == "elevated" else 0)

    print(json.dumps({"ok": False, "error": "need html-batch|multi-gate|ci-summary|version"}))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
