#!/usr/bin/env python3
"""Safe idle housekeeping — catalog memory, 3-brain index, verify eggs, scout upgrades.

No git push, ClawHub publish, social posts, or kernel planting unless explicitly enabled
in army_config idle_guardian.allow_planting (default false).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CC = Path(__file__).resolve().parents[1]
ARMY = CC.parent
CONFIG = CC / "config" / "army_config.json"
WORKSPACE = CC / "workspace"
JOURNAL = WORKSPACE / "idle_guardian_journal.jsonl"
FINDINGS = WORKSPACE / "idle_upgrade_findings.jsonl"
STATE = WORKSPACE / "idle_upgrade_state.json"

DEFAULT_OPS = [
    "memory_sync",
    "three_brain_index",
    "kernel_verify",
    "self_grow_check",
    "living_memory_audit",
    "clawhub_catalog_render",
    "haven_chart_refresh",
    "upgrade_scout",
    "lattice_light",
]


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _cfg() -> dict:
    if CONFIG.is_file():
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    return {}


def _idle_cfg() -> dict:
    return (_cfg().get("idle_guardian") or {})


def _stack() -> Path:
    sys.path.insert(0, str(ARMY))
    from lygo_stack_root import resolve_stack_root

    return resolve_stack_root(config_path=CONFIG)


def _lyra_core() -> Path | None:
    for key in ("LYRA_CORE_ROOT", "LYRA_CORE"):
        raw = os.environ.get(key, "").strip()
        if raw:
            p = Path(raw)
            if (p / "memory").is_dir() or (p / "modules" / "lyra_brain.py").is_file():
                return p
    for candidate in (
        Path(r"I:\E Drive\LYRA_CORE"),
        _stack().parent / "LYRA_CORE",
        Path.home() / "LYRA_CORE",
    ):
        if (candidate / "memory").is_dir():
            return candidate
    return None


def _append(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _log(op: str, ok: bool, detail: dict) -> None:
    _append(JOURNAL, {"ts": _utc(), "op": op, "ok": ok, "detail": detail})


def _run_tool(stack: Path, rel: str, timeout: int = 300) -> dict:
    script = stack / "tools" / rel
    if not script.is_file():
        return {"ok": False, "error": f"missing {rel}"}
    cp = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(stack),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    out: dict = {"exit_code": cp.returncode, "ok": cp.returncode == 0}
    if cp.stdout:
        try:
            out["json"] = json.loads(cp.stdout)
        except json.JSONDecodeError:
            out["stdout_tail"] = cp.stdout[-2500:]
    if cp.stderr:
        out["stderr_tail"] = cp.stderr[-1200:]
    return out


def op_memory_sync(stack: Path) -> dict:
    snap = stack / "docs" / "AGENT_MEMORY_SNAPSHOT.json"
    dest = WORKSPACE / "LYGO_MEMORY_SYNC.json"
    if not snap.is_file():
        return {"ok": False, "error": "missing AGENT_MEMORY_SNAPSHOT.json"}
    raw = snap.read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = json.loads(re.sub(r",(\s*[}\]])", r"\1", raw))
    sync = {
        "signature": "Δ9Φ963-ARMY-IDLE-MEMORY-SYNC-v1",
        "synced_from": str(snap),
        "timestamp": _utc(),
        "stack_git_head": (data.get("stack") or {}).get("github_main"),
        "lattice_ok": (data.get("stack") or {}).get("lattice") == "ALIGNED",
        "public_pages": data.get("public_pages", {}),
    }
    dest.write_text(json.dumps(sync, indent=2), encoding="utf-8")
    return {"ok": True, "path": str(dest)}


def op_three_brain_index(_stack: Path) -> dict:
    core = _lyra_core()
    if not core:
        return {"ok": False, "error": "LYRA_CORE not found (set LYRA_CORE_ROOT)"}
    mem = core / "memory"
    if not mem.is_dir():
        return {"ok": False, "error": "missing memory/"}
    snips = sorted(mem.glob("*.md"))
    daily_files = [p for p in snips if re.match(r"^\d{4}-\d{2}-\d{2}\.md$", p.name)]
    topic_snips = [p for p in snips if p not in daily_files and not p.name.startswith("_")]
    catalog = {
        "signature": "Δ9Φ963-IDLE-3BRAIN-CATALOG-v1",
        "ts": _utc(),
        "lyra_core": str(core),
        "snip_count": len(topic_snips),
        "daily_count": len(daily_files),
        "snips": [{"name": p.name, "bytes": p.stat().st_size} for p in topic_snips[:200]],
    }
    out_path = WORKSPACE / "three_brain_catalog.json"
    out_path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    # Append missing snips to today's daily index (additive only)
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    daily = mem / f"{day}.md"
    if not daily.exists():
        daily.write_text(f"# LYRA daily — {day}\n\n", encoding="utf-8")
    existing = daily.read_text(encoding="utf-8")
    appended = 0
    for p in topic_snips:
        if p.name.startswith(f"{day}-") and f"`{p.name}`" not in existing:
            with daily.open("a", encoding="utf-8") as f:
                f.write(f"- snip: `{p.name}` — (idle index)\n")
            appended += 1
    return {"ok": True, "catalog": str(out_path), "daily_appended": appended}


def op_kernel_verify(stack: Path) -> dict:
    r1 = _run_tool(stack, "verify_kernel_eggs.py", 120)
    r2 = _run_tool(stack, "verify_champion_eggs.py", 120)
    ok = r1.get("ok") and r2.get("ok")
    return {"ok": ok, "kernel": r1, "champion": r2}


def op_self_grow_check(_stack: Path) -> dict:
    core = _lyra_core()
    if not core:
        return {"ok": True, "skipped": "no LYRA_CORE"}
    mod = core / "modules" / "lyra_brain.py"
    if not mod.is_file():
        return {"ok": True, "skipped": "no lyra_brain module"}
    mem = core / "memory"
    ref = mem / "reference"
    return {
        "ok": True,
        "memory_md": len(list(mem.glob("*.md"))) if mem.is_dir() else 0,
        "reference_stubs": len(list(ref.glob("*.ref.txt"))) if ref.is_dir() else 0,
        "note": "counts only; no grow() on idle tick",
    }


def op_living_memory_audit(stack: Path) -> dict:
    script = (
        stack
        / "clawhub"
        / "mirrors"
        / "lygo-universal-living-memory-library"
        / "scripts"
        / "audit_library.py"
    )
    if not script.is_file():
        return {"ok": True, "skipped": "audit_library.py not in mirror"}
    authority = os.environ.get("LYGO_AUTHORITY_ROOT", "").strip() or str(stack.parent)
    cp = subprocess.run(
        [sys.executable, str(script), "--base", authority],
        capture_output=True,
        text=True,
        timeout=180,
    )
    return {"ok": cp.returncode == 0, "exit_code": cp.returncode, "stdout_tail": (cp.stdout or "")[-2000:]}


def op_clawhub_catalog_render(stack: Path) -> dict:
    return _run_tool(stack, "render_clawhub_catalog.py", 60)


def op_haven_chart_refresh(stack: Path) -> dict:
    return _run_tool(stack, "build_haven_star_chart.py", 120)


def op_lattice_light(stack: Path) -> dict:
    cp = subprocess.run(
        [sys.executable, str(stack / "tools" / "verify_kernel_eggs.py")],
        cwd=str(stack),
        capture_output=True,
        text=True,
        timeout=90,
    )
    skills = stack / "clawhub" / "skills.json"
    pub = listed = None
    if skills.is_file():
        data = json.loads(skills.read_text(encoding="utf-8"))
        pub = data.get("count_published")
        listed = len(data.get("skills", []))
    return {
        "ok": cp.returncode == 0,
        "eggs_verdict": (cp.stdout or "")[:500],
        "clawhub_published": pub,
        "clawhub_listed": listed,
        "catalog_balanced": pub == listed if pub is not None and listed is not None else None,
    }


def op_upgrade_scout(stack: Path) -> dict:
    prev = {}
    if STATE.is_file():
        try:
            prev = json.loads(STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            prev = {}
    head = ""
    dirty = 0
    try:
        cp = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(stack),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if cp.returncode == 0:
            head = cp.stdout.strip()
        cp2 = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(stack),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if cp2.returncode == 0:
            dirty = len([ln for ln in cp2.stdout.splitlines() if ln.strip()])
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    skills_path = stack / "clawhub" / "skills.json"
    versions: dict[str, str] = {}
    if skills_path.is_file():
        for s in json.loads(skills_path.read_text(encoding="utf-8")).get("skills", []):
            slug = s.get("slug")
            if slug:
                versions[slug] = str(s.get("version", ""))

    reg = stack / "data" / "kernel_eggs" / "registry.json"
    merkle = git_head = None
    if reg.is_file():
        blob = json.loads(reg.read_text(encoding="utf-8"))
        merkle = (blob.get("registry_merkle_root") or "")[:16]
        git_head = blob.get("git_head")

    findings: list[str] = []
    if prev.get("stack_head") and head and prev["stack_head"] != head:
        findings.append(f"stack HEAD changed {prev['stack_head']} -> {head}")
    if dirty > 0:
        findings.append(f"working tree has {dirty} changed paths (review when online)")
    if prev.get("kernel_merkle") and merkle and prev["kernel_merkle"] != merkle:
        findings.append(f"kernel registry merkle changed")
    for slug, ver in versions.items():
        old = (prev.get("skill_versions") or {}).get(slug)
        if old and old != ver:
            findings.append(f"ClawHub mirror version bump: {slug} {old} -> {ver}")

    state = {
        "ts": _utc(),
        "stack_head": head,
        "dirty_count": dirty,
        "kernel_merkle": merkle,
        "kernel_git_head": git_head,
        "skill_versions": versions,
    }
    STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    for msg in findings:
        _append(FINDINGS, {"ts": _utc(), "kind": "upgrade_hint", "message": msg, "state": state})
    return {"ok": True, "findings": findings, "dirty_count": dirty, "stack_head": head}


OPS = {
    "memory_sync": op_memory_sync,
    "three_brain_index": op_three_brain_index,
    "kernel_verify": op_kernel_verify,
    "self_grow_check": op_self_grow_check,
    "living_memory_audit": op_living_memory_audit,
    "clawhub_catalog_render": op_clawhub_catalog_render,
    "haven_chart_refresh": op_haven_chart_refresh,
    "upgrade_scout": op_upgrade_scout,
    "lattice_light": op_lattice_light,
}


def run_ops(ops: list[str]) -> dict:
    stack = _stack()
    summary: dict = {"ts": _utc(), "ops": {}, "all_ok": True}
    for name in ops:
        fn = OPS.get(name)
        if not fn:
            detail = {"ok": False, "error": "unknown op"}
        else:
            try:
                detail = fn(stack)
            except Exception as exc:  # noqa: BLE001 — idle tick must not crash supervisor
                detail = {"ok": False, "error": str(exc)}
        if not detail.get("ok", False) and "skipped" not in detail:
            summary["all_ok"] = False
        summary["ops"][name] = detail
        _log(name, bool(detail.get("ok")), detail)
    tick = WORKSPACE / "idle_guardian_last_tick.json"
    tick.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="LYGO Army idle housekeeping")
    ap.add_argument("--tick", action="store_true", help="Run configured safe ops once")
    ap.add_argument("--op", action="append", help="Single op (repeatable)")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()
    if args.list:
        print("\n".join(sorted(OPS.keys())))
        return 0
    if args.op:
        ops = args.op
    elif args.tick:
        idle = _idle_cfg()
        ops = list(idle.get("housekeep_ops") or DEFAULT_OPS)
    else:
        ap.print_help()
        return 2
    summary = run_ops(ops)
    print(json.dumps({"all_ok": summary["all_ok"], "ops": list(summary["ops"].keys())}))
    return 0 if summary["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())