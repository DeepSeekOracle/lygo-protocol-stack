#!/usr/bin/env python3
"""LYGO PC + lattice hardening audit (read-only). Writes tests/pc_lattice_hardening_last_run.json"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "pc_lattice_hardening_last_run.json"
SIGNATURE = "Δ9Φ963-PC-LATTICE-HARDENING-AUDIT-v1.1"


def _run(cmd: list[str], cwd: Path | None = None, timeout: int = 120) -> dict:
    try:
        p = subprocess.run(
            cmd,
            cwd=cwd or ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return {"exit": p.returncode, "stdout": (p.stdout or "")[-4000:], "stderr": (p.stderr or "")[-2000:]}
    except Exception as exc:
        return {"exit": -1, "error": str(exc)}


def _git_tracked(path: Path) -> bool:
    try:
        p = subprocess.run(
            ["git", "ls-files", "--error-unmatch", str(path)],
            cwd=ROOT,
            capture_output=True,
            timeout=15,
        )
        return p.returncode == 0
    except Exception:
        return False


def _secret_leaks_in_repo() -> dict:
    """High-signal only: tracked files with material that looks like live secrets."""
    hits: list[str] = []
    skip_dirs = {".git", "_hf_staging", "target", "__pycache__", "node_modules", "references", "books"}
    safe_name_bits = (
        "SECURITY",
        "example",
        "EXAMPLE",
        "moltx_post_utils",
        "load_biophase7_vault",
        "preflight",
        "MOLTX_POST",
        "BIOPHASE7_API",
        "moltx_lattice_pulse",
        "SKILL.md",
    )
    live_prefixes = ("xai-", "nvapi-", "moltx_sk_", "sk-proj-", "sk-")
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        if any(s in p.parts for s in skip_dirs):
            continue
        if p.name == ".env":
            if _git_tracked(p):
                hits.append(".env (tracked by git — CRITICAL)")
            continue
        if p.suffix in {".pyc", ".db", ".pdf", ".txt"} and "books" not in str(p):
            if p.suffix == ".txt" and "vault" not in p.name.lower():
                pass
        if p.suffix in {".pyc", ".db", ".pdf"}:
            continue
        if any(bit in p.name for bit in safe_name_bits):
            continue
        # Intentional fixtures / restore maps — not live key material
        if "leaky_tool_dump" in p.name or "RESTORE_ANCHOR" in p.name:
            continue
        if p.name in {"context_guard.py", "self_check.py"}:
            continue
        rel = str(p.as_posix())
        if "/examples/" in rel:
            continue
        try:
            if p.stat().st_size > 300_000:
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if "REPLACE_ME" in text or "PLACEHOLDER" in text:
            continue
        import re

        for prefix in live_prefixes:
            if prefix in ("xai-", "nvapi-", "moltx_sk_"):
                pat = re.compile(re.escape(prefix) + r"[A-Za-z0-9_-]{24,}")
                if pat.search(text) and _git_tracked(p):
                    hits.append(f"{p.relative_to(ROOT)}:live-{prefix}")
            elif prefix == "sk-proj-" and _git_tracked(p):
                if re.search(r"sk-proj-[A-Za-z0-9_-]{20,}", text):
                    hits.append(f"{p.relative_to(ROOT)}:openai-sk-proj")
    return {"leak_hits": hits[:30], "count": len(hits)}


def main() -> int:
    report: dict = {
        "signature": SIGNATURE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "root": str(ROOT),
        "checks": {},
    }

    report["checks"]["gitignore_env"] = (ROOT / ".gitignore").read_text(encoding="utf-8", errors="ignore")
    report["checks"]["gitignore_has_env"] = ".env" in report["checks"]["gitignore_env"]
    report["checks"]["gitignore_moltx_data"] = "data/moltx" in report["checks"]["gitignore_env"]

    report["checks"]["lattice_alignment"] = _run([sys.executable, "tools/verify_lattice_alignment.py"])
    report["checks"]["alignment_badge"] = _run([sys.executable, "tools/verify_alignment_badge.py"])

    army = Path(r"I:\E Drive\.grok\skills\lygo-ollama-army\ollama_command_center\scripts\army_cron_once.py")
    launcher = Path(r"I:\E Drive\.grok\skills\lygo-ollama-army\ollama_army_launcher.py")
    if army.is_file():
        report["checks"]["army_cron_once"] = _run([sys.executable, str(army)])
    elif launcher.is_file():
        report["checks"]["army_cron_once"] = _run(
            [sys.executable, str(launcher), "--once-check"], cwd=launcher.parent
        )
    else:
        report["checks"]["army_cron_once"] = {"skipped": True, "reason": "path missing"}

    sentinel = Path(
        r"I:\E Drive\.grok\skills\lygo-ollama-army\ollama_command_center\workspace\sentinel_status.json"
    )
    if sentinel.is_file():
        try:
            s = json.loads(sentinel.read_text(encoding="utf-8"))
            report["checks"]["sentinel"] = {
                "lattice_ok": (s.get("lattice") or {}).get("ok"),
                "healthy": s.get("healthy"),
                "summary": (s.get("lattice") or {}).get("summary"),
            }
        except Exception as exc:
            report["checks"]["sentinel"] = {"error": str(exc)}
    else:
        report["checks"]["sentinel"] = {"missing": True}

    home = Path(os.environ.get("OPENCLAW_HOME", r"C:\Users\justi\.openclaw"))
    cred = home / "credentials" / "moltx.json"
    report["checks"]["moltx_cred"] = {
        "path": str(cred),
        "exists": cred.is_file(),
        "note": "presence only; key not read",
    }
    vault_env = ROOT / ".env"
    report["checks"]["repo_dot_env"] = {
        "exists": vault_env.is_file(),
        "gitignored": report["checks"]["gitignore_has_env"],
        "warning": vault_env.is_file() and "never commit",
    }

    biophase = os.environ.get("LYGO_BIOPHASE7_VAULT", "")
    report["checks"]["biophase7_vault_env_set"] = bool(biophase)

    report["checks"]["secret_scan_repo"] = _secret_leaks_in_repo()

    report["checks"]["biophase7_calibrate"] = _run(
        [sys.executable, "tools/calibrate_byte_entropy_filter.py"], timeout=60
    )
    report["checks"]["biophase7_parity"] = _run(
        [sys.executable, "tools/run_parity_tests.py"], timeout=90
    )
    for doc in (
        "docs/LIGHTFATHER_FINAL_ARCHITECT_ADDENDUM.md",
        "docs/P0_HONEST_SPEC.md",
        "docs/CRYPTO_LATTICE_SEPARATION.md",
    ):
        report["checks"][f"doc_{Path(doc).stem}"] = (ROOT / doc).is_file()

    # Verdict: stack lattice + badge + P0 parity + secret hygiene.
    # Local Ollama army is a helper — down Ollama is a recommendation, not a lattice fail.
    lattice_ok = report["checks"].get("sentinel", {}).get("lattice_ok") is True
    la = report["checks"]["lattice_alignment"].get("exit") == 0
    badge = report["checks"]["alignment_badge"].get("exit") == 0
    parity = report["checks"]["biophase7_parity"].get("exit") == 0
    leaks = report["checks"]["secret_scan_repo"].get("count", 0)
    dot_env_ok = not report["checks"]["repo_dot_env"].get("exists") or report["checks"]["repo_dot_env"].get(
        "gitignored"
    )
    report["verdict"] = (
        "HARDENED_OK"
        if (la and badge and parity and leaks == 0 and dot_env_ok)
        else "NEEDS_ATTENTION"
    )
    report["recommendations"] = []
    if leaks:
        report["recommendations"].append("Review secret_scan_repo leak_hits; rotate keys if any real secrets in tracked files.")
    if not report["checks"]["gitignore_moltx_data"]:
        report["recommendations"].append("Ensure data/moltx/*.json is gitignored.")
    if report["checks"]["repo_dot_env"].get("exists"):
        report["recommendations"].append("Keep .env local only; run load_biophase7_vault to .env not git.")
    if not cred.is_file():
        report["recommendations"].append("Moltx: place moltx_sk_* in OPENCLAW_HOME/credentials/moltx.json for gated posts.")
    if not lattice_ok:
        report["recommendations"].append(
            "Start local Ollama (D:\\Ollama\\ollama.exe serve) so the hourly LYGO-Army-Sentinel reports healthy."
        )

    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"verdict={report['verdict']}")
    print(f"report={OUT}")
    return 0 if report["verdict"] == "HARDENED_OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())