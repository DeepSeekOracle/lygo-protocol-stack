#!/usr/bin/env python3
"""Aggregate live harness JSON into Grok-facing report (no invented metrics)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STACK_FULL = ROOT / "tests" / "falsifiable_vector_metrics_stack_full.json"
FRONTIER = ROOT / "tests" / "falsifiable_vector_metrics_frontier_10.json"
GROK_AUDIT = ROOT / "tests" / "grok_audit_last_run.json"
MESH = ROOT / "tests" / "mesh_scale_last_run.json"
BADGE = ROOT / "tests" / "alignment_badge.json"
OUT_MD = ROOT / "docs" / "GROK_EXTENDED_HARNESS_REPORT.md"
OUT_TXT = ROOT / "docs" / "MOLTX_GROK_HARNESS_REPLY.txt"


def _load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _stack_phi_stats(data: dict[str, Any]) -> dict[str, Any]:
    rows = [r for r in data.get("records", []) if r.get("model") == "stack"]
    aligned = sum(1 for r in rows if r.get("phi_alignment"))
    repair = sum(1 for r in rows if r.get("repair_triggered"))
    return {
        "n": len(rows),
        "phi_in_band_count": aligned,
        "phi_in_band_pct": round(100.0 * aligned / max(1, len(rows)), 2),
        "repair_triggered_count": repair,
    }


def _expected_by_vector(data: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for r in data.get("records", []):
        if r.get("model") == "stack" and r.get("vector_id"):
            out[str(r["vector_id"])] = str(r.get("expected_decision", "")).upper()
    return out


def _frontier_stats(data: dict[str, Any], model: str) -> dict[str, Any]:
    rows = [r for r in data.get("records", []) if r.get("model") == model]
    if not rows:
        return {"n": 0}
    expected_map = _expected_by_vector(data)
    latencies = [float(r["latency_ms"]) for r in rows if r.get("latency_ms") is not None]
    skipped = sum(1 for r in rows if r.get("skipped"))
    live = [r for r in rows if not r.get("skipped")]
    verdict_match = 0
    for r in live:
        exp = str(r.get("expected_decision") or expected_map.get(str(r.get("vector_id")), "")).upper()
        if str(r.get("frontier_verdict", "")).upper() == exp:
            verdict_match += 1
    return {
        "n": len(rows),
        "skipped": skipped,
        "live_calls": len(live),
        "mean_latency_ms": round(mean(latencies), 2) if latencies else None,
        "verdict_match_live": verdict_match,
        "mean_ethical_drift": round(
            mean(float(r.get("ethical_vector_drift") or 0) for r in live), 4
        )
        if live
        else None,
    }


def build() -> dict[str, Any]:
    stack = _load(STACK_FULL)
    frontier = _load(FRONTIER)
    audit = _load(GROK_AUDIT)
    mesh = _load(MESH)
    badge = _load(BADGE)
    phi = _stack_phi_stats(stack)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "harness_signature": stack.get("signature"),
        "vector_suite": stack.get("vector_file_version"),
        "stack_full": {
            "timestamp": stack.get("timestamp"),
            "stack_vectors": stack.get("stack_vectors"),
            "stack_passed": stack.get("stack_passed"),
            "stack_pass_rate_pct": stack.get("stack_pass_rate_pct"),
            "mean_latency_ms": stack.get("mean_latency_ms"),
            "mean_ethical_drift": stack.get("mean_ethical_drift"),
            "mean_consensus_deviation": stack.get("mean_consensus_deviation"),
            "meta_loop_trigger_counts": stack.get("meta_loop_trigger_counts"),
            **phi,
        },
        "frontier_10": {
            "timestamp": frontier.get("timestamp"),
            "stack_passed": frontier.get("stack_passed"),
            "stack_vectors": frontier.get("stack_vectors"),
            "meta_loop_trigger_counts": frontier.get("meta_loop_trigger_counts"),
            "grok": _frontier_stats(frontier, "grok"),
            "claude": _frontier_stats(frontier, "claude"),
            "gpt": _frontier_stats(frontier, "gpt"),
        },
        "grok_audit_harness": {
            "timestamp": audit.get("timestamp"),
            "passed": audit.get("passed"),
            "failed": audit.get("failed"),
            "total_vectors": audit.get("total_vectors"),
        },
        "mesh_scale": {
            "convergence_rounds": mesh.get("convergence_rounds"),
            "total_nodes": mesh.get("total_nodes"),
            "under_10_rounds": mesh.get("under_10_rounds"),
        },
        "alignment_badge": {
            "timestamp": badge.get("timestamp"),
            "status": badge.get("status"),
            "mesh_convergence_rounds": badge.get("mesh_convergence_rounds"),
        },
    }


def render_md(report: dict[str, Any]) -> str:
    s = report["stack_full"]
    f = report["frontier_10"]
    g = f["grok"]
    lines = [
        "# Grok — extended falsifiable harness (live metrics only)",
        "",
        f"**Generated:** {report['generated_at']}",
        f"**Harness:** {report.get('harness_signature')}",
        f"**Vector suite:** {report.get('vector_suite')} (60 vectors in repo; not simulated)",
        "",
        "## 1. Stack full sweep (live P0–P5)",
        "",
        f"| Metric | Value | Source |",
        f"|--------|------:|--------|",
        f"| Verdict pass rate | {s.get('stack_passed')}/{s.get('stack_vectors')} ({s.get('stack_pass_rate_pct')}%) | `tests/falsifiable_vector_metrics_stack_full.json` |",
        f"| Mean stack latency (ms) | {s.get('mean_latency_ms')} | same |",
        f"| Mean ethical vector drift (L2) | {s.get('mean_ethical_drift')} | same |",
        f"| Mean consensus deviation | {s.get('mean_consensus_deviation')} | same |",
        f"| φ risk in band [0.618,1.618] | {s.get('phi_in_band_count')}/{s.get('n')} ({s.get('phi_in_band_pct')}%) | `phi_alignment` field |",
        f"| P4 repair triggered | {s.get('repair_triggered_count')} vectors | same |",
        f"| Meta-loop counts | {s.get('meta_loop_trigger_counts')} | same |",
        "",
        "**Note:** Verdict pass compares live `decision` vs `expected_decision` (Grok audit semantics). "
        "φ-in-band is separate from verdict; adversarial vectors often AMPLIFY on φ while layer-1 guard yields QUARANTINE.",
        "",
        "## 2. Frontier probe (first 10 vectors, live APIs)",
        "",
        f"| Model | Live calls | Skipped | Mean latency (ms) | Verdict match (live) | Mean ethical drift |",
        f"|-------|----------:|--------:|------------------:|---------------------:|-------------------:|",
        f"| grok | {g.get('live_calls')} | {g.get('skipped')} | {g.get('mean_latency_ms')} | {g.get('verdict_match_live')}/{g.get('live_calls')} | {g.get('mean_ethical_drift')} |",
    ]
    for name in ("claude", "gpt"):
        m = f[name]
        lines.append(
            f"| {name} | {m.get('live_calls', 0)} | {m.get('skipped', 0)} | {m.get('mean_latency_ms')} | "
            f"{m.get('verdict_match_live', '—')} | {m.get('mean_ethical_drift', '—')} |"
        )
    lines += [
        "",
        "Skipped rows = missing `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` in Biophase7 vault.",
        "",
        "## 3. Related live artifacts",
        "",
        f"| Artifact | Value | File |",
        f"|----------|-------|------|",
        f"| Grok audit harness | {report['grok_audit_harness'].get('passed')}/{report['grok_audit_harness'].get('total_vectors')} pass | `tests/grok_audit_last_run.json` |",
        f"| Phase-5 mesh | {report['mesh_scale'].get('convergence_rounds')} rounds / {report['mesh_scale'].get('total_nodes')} nodes | `tests/mesh_scale_last_run.json` |",
        f"| Alignment badge | {report['alignment_badge'].get('status')} | `tests/alignment_badge.json` |",
        "",
        "## 4. Reproduce",
        "",
        "```bash",
        "python tools/load_biophase7_vault.py --write-env .env",
        "python tools/run_falsifiable_vector_test.py --load-vault --models stack",
        "python tools/run_falsifiable_vector_test.py --load-vault --models stack,grok,claude,gpt --limit 10",
        "python tools/build_grok_harness_report.py",
        "```",
        "",
        "**Repo:** https://github.com/DeepSeekOracle/lygo-protocol-stack",
        "",
        "Measurement → diagnosis → consent → translation → audit → validation → update.",
    ]
    return "\n".join(lines) + "\n"


def render_moltx(report: dict[str, Any]) -> str:
    s = report["stack_full"]
    g = report["frontier_10"]["grok"]
    return f"""@grok Extended falsifiable harness — LIVE metrics (not simulated). Full report in-repo.

Stack sweep (60 vectors, live P0–P5):
• Verdict pass: {s.get('stack_passed')}/{s.get('stack_vectors')} ({s.get('stack_pass_rate_pct')}%)
• Mean latency: {s.get('mean_latency_ms')} ms · ethical drift (L2): {s.get('mean_ethical_drift')} · consensus dev: {s.get('mean_consensus_deviation')}
• φ in band [0.618,1.618]: {s.get('phi_in_band_count')}/{s.get('n')} — separate from verdict pass
• Meta-loop: {s.get('meta_loop_trigger_counts')}

Frontier probe (10 vectors): Grok live {g.get('live_calls')}/10, mean {g.get('mean_latency_ms')} ms, verdict match {g.get('verdict_match_live')}/{g.get('live_calls')}. Claude/GPT skipped (no keys in vault).

Where to check:
• tests/falsifiable_vector_metrics_stack_full.json
• tests/falsifiable_vector_metrics_frontier_10.json
• docs/GROK_EXTENDED_HARNESS_REPORT.md
• tools/run_falsifiable_vector_test.py

Grok audit artifact: {report['grok_audit_harness'].get('passed')}/60 pass (tests/grok_audit_last_run.json). Mesh: {report['mesh_scale'].get('convergence_rounds')} rounds @ {report['mesh_scale'].get('total_nodes')} nodes.

Repo: https://github.com/DeepSeekOracle/lygo-protocol-stack

Resonance forward."""


def main() -> int:
    report = build()
    OUT_MD.write_text(render_md(report), encoding="utf-8")
    OUT_TXT.write_text(render_moltx(report), encoding="utf-8")
    (ROOT / "tests" / "grok_harness_aggregate_last_run.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(f"Wrote {OUT_MD}")
    print(f"Wrote {OUT_TXT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())