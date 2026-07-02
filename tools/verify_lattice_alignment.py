#!/usr/bin/env python3
"""LYGO lattice alignment checks (local files + optional registry inspect)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HF_SPACE = REPO.parent / "Hugging face"
GROK_OPERATOR = REPO.parent / ".grok" / "skills" / "lygo-protocol-stack-operator"

CANONICAL_URLS = {
    "github_pages_stack": "https://deepseekoracle.github.io/lygo-protocol-stack/",
    "github_stack": "https://github.com/DeepSeekOracle/lygo-protocol-stack",
    "hf_dataset": "https://huggingface.co/datasets/DeepSeekOracle/lygo-protocol-stack",
    "hf_space": "https://huggingface.co/spaces/DeepSeekOracle/LYGO-Resonance-Engine",
    "clawhub": "https://clawhub.ai/deepseekoracle",
    "grokipedia": "https://grokipedia.com/page/lygo-protocol-stack",
    "resonance_docs": "https://deepseekoracle.github.io/Excavationpro/LYGORESONANCE.html",
    "biometric_harness_pages": "https://deepseekoracle.github.io/lygo-protocol-stack/BiometricEntropyHarness.html",
    "biometric_harness_excavationpro": "https://deepseekoracle.github.io/Excavationpro/BiometricEntropyHarness.html",
    "slm_pages_stack": "https://deepseekoracle.github.io/lygo-protocol-stack/SovereignLatticeMesh.html",
    "slm_pages_excavationpro": "https://deepseekoracle.github.io/Excavationpro/SovereignLatticeMesh.html",
}


def check(name: str, ok: bool, detail: str = "") -> bool:
    mark = "OK" if ok else "FAIL"
    print(f"  [{mark}] {name}" + (f" — {detail}" if detail else ""))
    return ok


def check_warn(name: str, ok: bool, detail: str = "") -> bool:
    """Non-blocking check (e.g. stack Pages until Settings enabled)."""
    mark = "OK" if ok else "WARN"
    print(f"  [{mark}] {name}" + (f" — {detail}" if detail else ""))
    return True


def in_ci() -> bool:
    return os.environ.get("GITHUB_ACTIONS", "").strip().lower() == "true"


def resolve_hf_paths() -> dict[str, Path]:
    """Prefer local HF Space vault; fall back to in-repo stack (CI / clones)."""
    ext_stack = HF_SPACE / "protocol_stack" / "stack" / "lygo_stack.py"
    if ext_stack.is_file():
        root = HF_SPACE / "protocol_stack"
        return {
            "bundle": root / "stack" / "lygo_stack.py",
            "semantic": root / "stack" / "text_semantic_gate.py",
            "twin": root / "TWIN_GATE_MODE.txt",
            "guardian": HF_SPACE / "lygo_ethical_guardian.py",
            "source": "hf_vault",
        }
    return {
        "bundle": REPO / "stack" / "lygo_stack.py",
        "semantic": REPO / "stack" / "text_semantic_gate.py",
        "twin": REPO / "tests" / "twin_gate_vector_suite_last_run.json",
        "guardian": HF_SPACE / "lygo_ethical_guardian.py",
        "source": "repo_stack",
    }


def main() -> int:
    print("LYGO Lattice alignment verify")
    print("=" * 50)
    all_ok = True

    skills_json = REPO / "clawhub" / "skills.json"
    if skills_json.is_file():
        data = json.loads(skills_json.read_text(encoding="utf-8"))
        n_pub = data.get("count_published", 0)
        n_mir = data.get("count_mirrored", 0)
        slugs = [s["slug"] for s in data.get("skills", [])]
        all_ok &= check("clawhub/skills.json", n_pub == len(slugs), f"published={n_pub} listed={len(slugs)}")
        all_ok &= check("operator in catalog", "lygo-protocol-stack-operator" in slugs)
        all_ok &= check("mirrors count", n_mir >= n_pub - 1, f"mirrored={n_mir}")
    else:
        all_ok &= check("clawhub/skills.json", False, "missing")

    mirror_op = REPO / "clawhub" / "mirrors" / "lygo-protocol-stack-operator" / "SKILL.md"
    all_ok &= check("operator mirror", mirror_op.is_file())

    for key, path in [
        ("STACK_STATUS", REPO / "docs" / "STACK_STATUS.md"),
        ("LYGO_LATTICE", REPO / "docs" / "LYGO_LATTICE.md"),
        ("sovereign test", REPO / "tools" / "run_sovereign_integrity_test.py"),
        ("p0 golden", REPO / "protocol0_nano_kernel" / "fixtures" / "p0_canonical.sha256"),
    ]:
        all_ok &= check(key, path.is_file())

    readme = (REPO / "README.md").read_text(encoding="utf-8")
    for label, url in CANONICAL_URLS.items():
        all_ok &= check(f"README link {label}", url in readme)

    hf = resolve_hf_paths()
    src_note = hf["source"]
    all_ok &= check(
        "HF protocol_stack bundle",
        hf["bundle"].is_file(),
        f"{src_note} · {hf['bundle'].parent}",
    )
    all_ok &= check("HF text_semantic_gate", hf["semantic"].is_file(), src_note)
    all_ok &= check("HF TWIN_GATE_MODE", hf["twin"].is_file(), src_note)
    if hf["guardian"].is_file():
        all_ok &= check("HF ethical guardian module", True)
    elif hf["source"] == "repo_stack":
        check_warn(
            "HF ethical guardian module",
            False,
            "HF Space vault not mounted — stack bundle OK in CI",
        )
    else:
        all_ok &= check("HF ethical guardian module", False)
    all_ok &= check("twin calibration tool", (REPO / "tools" / "run_twin_gate_calibration.py").is_file())
    all_ok &= check("twin vector suite tool", (REPO / "tools" / "run_twin_gate_vector_suite.py").is_file())
    all_ok &= check("grok audit tool", (REPO / "tools" / "run_grok_audit_demo.py").is_file())
    for key, path in [
        ("Dockerfile", REPO / "Dockerfile"),
        ("docker-compose", REPO / "docker-compose.yml"),
        ("setup.sh", REPO / "setup.sh"),
        ("alignment badge tool", REPO / "tools" / "verify_alignment_badge.py"),
        ("phase1 elasticity", REPO / "stack" / "infrastructure_elasticity.py"),
        ("phase3-4 federation", REPO / "stack" / "federation_runtime.py"),
        ("PHASE2 doc", REPO / "docs" / "PHASE2_DEPLOYMENT.md"),
        ("BLUEPRINT", REPO / "docs" / "BLUEPRINT.md"),
        ("lattice gauntlet", REPO / "tools" / "run_lattice_gauntlet.py"),
        ("mesh gossip", REPO / "stack" / "mesh_gossip_http.py"),
        ("mesh scale sim", REPO / "tools" / "run_mesh_scale_sim.py"),
        ("mesh gossip protocol doc", REPO / "docs" / "MESH_GOSSIP_PROTOCOL.md"),
        ("agent memory snapshot", REPO / "docs" / "AGENT_MEMORY_SNAPSHOT.json"),
        ("biometric harness page", REPO / "docs" / "BiometricEntropyHarness.html"),
        ("slm interactive page", REPO / "docs" / "SovereignLatticeMesh.html"),
        ("public link archive", REPO / "docs" / "LYGO_PUBLIC_LINK_ARCHIVE.json"),
        ("log public surface tool", REPO / "tools" / "log_public_surface.py"),
        ("sync excavationpro slm", REPO / "tools" / "sync_excavationpro_slm_page.py"),
        ("phase7 haip ui tool", REPO / "tools" / "haip_ui_entropy.py"),
        ("p6 hardened verify", REPO / "tools" / "verify_attestation_hardened.py"),
        ("p7 ble ingest", REPO / "tools" / "live_ble_telemetry_ingest.py"),
        ("phase7 polish doc", REPO / "docs" / "PHASE7_POLISH.md"),
        ("slm merkle sync", REPO / "stack" / "merkle_sync.py"),
        ("slm mycelium mesh", REPO / "stack" / "distributed_mycelium_mesh.py"),
        ("slm harmonic consensus", REPO / "stack" / "harmonic_consensus_mesh.py"),
        ("slm runtime", REPO / "stack" / "sovereign_lattice_mesh.py"),
        ("slm doc", REPO / "docs" / "SOVEREIGN_LATTICE_MESH.md"),
        ("slm audit tool", REPO / "tools" / "run_slm_audit.py"),
        ("phase9 tls manager", REPO / "tools" / "tls_manager.py"),
        ("phase9 ldq synthesis", REPO / "protocol8_ldq_synthesis" / "harmonic_gravity.py"),
        ("phase9 audit tool", REPO / "tools" / "run_phase9_audit.py"),
        ("phase9 public mesh doc", REPO / "docs" / "PHASE9_PUBLIC_MESH.md"),
    ]:
        all_ok &= check(key, path.is_file())
    slm_run = REPO / "tests" / "slm_audit_last_run.json"
    if slm_run.is_file():
        try:
            sr = json.loads(slm_run.read_text(encoding="utf-8"))
            all_ok &= check("slm audit last run", bool(sr.get("all_pass")), f"ms={sr.get('duration_ms')}")
        except Exception as exc:
            all_ok &= check("slm audit last run", False, str(exc))
    else:
        all_ok &= check("slm audit last run", False, "missing json")
    p9_run = REPO / "tests" / "phase9_audit_last_run.json"
    if p9_run.is_file():
        try:
            p9 = json.loads(p9_run.read_text(encoding="utf-8"))
            all_ok &= check("phase9 audit last run", bool(p9.get("all_pass")), f"ms={p9.get('duration_ms')}")
        except Exception as exc:
            all_ok &= check("phase9 audit last run", False, str(exc))
    else:
        all_ok &= check("phase9 audit last run", False, "missing json")
    mesh_run = REPO / "tests" / "mesh_scale_last_run.json"
    if mesh_run.is_file():
        try:
            mr = json.loads(mesh_run.read_text(encoding="utf-8"))
            ok_mesh = bool(mr.get("under_10_rounds")) and int(mr.get("convergence_rounds", 99)) < 10
            all_ok &= check("mesh scale last run", ok_mesh, f"rounds={mr.get('convergence_rounds')}")
        except Exception as exc:
            all_ok &= check("mesh scale last run", False, str(exc))
    else:
        all_ok &= check("mesh scale last run", False, "missing json")

    compass_canon = REPO / "tools" / "LYGO_Compass_Master.html"
    if compass_canon.is_file():
        all_ok &= check("compass master canonical", True)
    else:
        check_warn(
            "compass master canonical",
            False,
            "tools/LYGO_Compass_Master.html — run tools/sync_compass_pages.py after add",
        )

    op_mirror = REPO / "clawhub" / "mirrors" / "lygo-protocol-stack-operator" / "SKILL.md"
    op_skill = GROK_OPERATOR / "SKILL.md"
    skill_file = op_skill if op_skill.is_file() else op_mirror
    if skill_file.is_file():
        skill_md = skill_file.read_text(encoding="utf-8")
        detail = "mirror" if skill_file == op_mirror else "workspace"
        all_ok &= check(
            "grok operator SKILL.md",
            CANONICAL_URLS["github_stack"] in skill_md,
            detail,
        )
    else:
        all_ok &= check("grok operator", False, "path missing")

    # ClawHub registry version for operator
    try:
        cp = subprocess.run(
            "npx --yes clawhub@latest inspect deepseekoracle/lygo-protocol-stack-operator --json",
            cwd=REPO / "clawhub",
            capture_output=True,
            text=True,
            shell=True,
            timeout=90,
        )
        if cp.returncode == 0:
            reg = json.loads(cp.stdout)
            ver = (reg.get("skill") or {}).get("tags", {}).get("latest", "?")
            all_ok &= check("clawhub operator published", True, f"latest={ver}")
        elif in_ci():
            check_warn("clawhub inspect", False, (cp.stderr or cp.stdout or "")[:120])
        else:
            all_ok &= check("clawhub inspect", False, cp.stderr[:120])
    except Exception as exc:
        if in_ci():
            check_warn("clawhub inspect", False, str(exc))
        else:
            all_ok &= check("clawhub inspect", False, str(exc))

    try:
        subprocess.run(
            [sys.executable, str(REPO / "tools" / "verify_public_pages.py")],
            cwd=REPO,
            timeout=120,
            check=False,
        )
        pp = REPO / "tests" / "public_pages_last_run.json"
        if pp.is_file():
            pr = json.loads(pp.read_text(encoding="utf-8"))
            all_ok &= check(
                "excavationpro public mirrors",
                bool(pr.get("excavationpro_mirrors_live")),
            )
            require_stack = os.environ.get("LYGO_REQUIRE_STACK_PAGES", "").strip() in (
                "1",
                "true",
                "yes",
            )
            stack_live = bool(pr.get("stack_pages_live"))
            if stack_live:
                all_ok &= check("stack github pages", True)
            elif require_stack:
                all_ok &= check(
                    "stack github pages",
                    False,
                    "Settings→Pages→gh-pages / or main+/docs — GITHUB_PAGES_SETUP.md",
                )
            else:
                check_warn(
                    "stack github pages",
                    False,
                    "enable Pages once (gh-pages branch ready) — GITHUB_PAGES_SETUP.md",
                )
        else:
            all_ok &= check("public pages last run", False, "missing json")
    except Exception as exc:
        all_ok &= check("public pages verify", False, str(exc))

    for label, rel in [
        ("anchor lygo_anchor tool", "tools/lygo_anchor.py"),
        ("anchor stack bridge", "stack/lygo_stack_anchor.py"),
        ("anchor deployment doc", "docs/ANCHOR_DEPLOYMENT.md"),
        ("lattice intel index", "docs/LYGO_LATTICE_INTEL_INDEX.json"),
        ("ldq vault reference", "docs/LDQ_VAULT_REFERENCE.md"),
    ]:
        all_ok &= check(label, (REPO / rel).is_file())

    anchor_audit = REPO / "tests" / "anchor_audit_last_run.json"
    if anchor_audit.is_file():
        ar = json.loads(anchor_audit.read_text(encoding="utf-8"))
        all_ok &= check("anchor audit last run", bool(ar.get("all_pass")), f"ms={ar.get('duration_ms')}")
    else:
        check_warn("anchor audit last run", False, "run tools/run_anchor_audit.py")

    print("=" * 50)
    print("LATTICE", "ALIGNED" if all_ok else "NEEDS FIX")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())