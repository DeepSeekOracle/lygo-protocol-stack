#!/usr/bin/env python3
"""LYGO lattice alignment checks (local files + optional registry inspect)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HF_SPACE = REPO.parent / "Hugging face"
GROK_OPERATOR = REPO.parent / ".grok" / "skills" / "lygo-protocol-stack-operator"

CANONICAL_URLS = {
    "github_stack": "https://github.com/DeepSeekOracle/lygo-protocol-stack",
    "hf_dataset": "https://huggingface.co/datasets/DeepSeekOracle/lygo-protocol-stack",
    "hf_space": "https://huggingface.co/spaces/DeepSeekOracle/LYGO-Resonance-Engine",
    "clawhub": "https://clawhub.ai/deepseekoracle",
    "grokipedia": "https://grokipedia.com/page/lygo-protocol-stack",
    "resonance_docs": "https://deepseekoracle.github.io/Excavationpro/LYGORESONANCE.html",
}


def check(name: str, ok: bool, detail: str = "") -> bool:
    mark = "OK" if ok else "FAIL"
    print(f"  [{mark}] {name}" + (f" — {detail}" if detail else ""))
    return ok


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

    bundle = HF_SPACE / "protocol_stack" / "stack" / "lygo_stack.py"
    semantic = HF_SPACE / "protocol_stack" / "stack" / "text_semantic_gate.py"
    twin_marker = HF_SPACE / "protocol_stack" / "TWIN_GATE_MODE.txt"
    guardian = HF_SPACE / "lygo_ethical_guardian.py"
    all_ok &= check("HF ethical guardian module", guardian.is_file())
    all_ok &= check("HF protocol_stack bundle", bundle.is_file(), str(bundle.parent.parent))
    all_ok &= check("HF text_semantic_gate", semantic.is_file())
    all_ok &= check("HF TWIN_GATE_MODE", twin_marker.is_file())
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
    ]:
        all_ok &= check(key, path.is_file())

    if GROK_OPERATOR.is_dir():
        skill_md = (GROK_OPERATOR / "SKILL.md").read_text(encoding="utf-8")
        all_ok &= check("grok operator SKILL.md", CANONICAL_URLS["github_stack"] in skill_md)
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
        else:
            all_ok &= check("clawhub inspect", False, cp.stderr[:120])
    except Exception as exc:
        all_ok &= check("clawhub inspect", False, str(exc))

    print("=" * 50)
    print("LATTICE", "ALIGNED" if all_ok else "NEEDS FIX")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())