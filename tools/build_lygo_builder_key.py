#!/usr/bin/env python3
"""
Pack portable LYGO Architect Builder Key onto a thumb drive (default E:\\LYGO_BUILDER_KEY).
No secrets: skips .env, tokens, wallet patterns, __pycache__, .git (optional flag).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path(r"I:\E Drive")
STACK = WORKSPACE / "lygo-protocol-stack"
CRYPTO = WORKSPACE / "lyra-crypto-operator"
LYRA = WORKSPACE / "LYRA_CORE"
GROK_SKILLS = WORKSPACE / ".grok" / "skills"
ARMY = GROK_SKILLS / "lygo-ollama-army"

DEFAULT_OUT = Path(r"E:\LYGO_BUILDER_KEY")
BUILDR_OVERLAY = WORKSPACE / "LYGO_BUILDR_USB"

SKIP_DIR_NAMES = {
    ".git",
    "__pycache__",
    "target",
    "_hf_staging",
    "node_modules",
    ".venv",
    "venv",
}
SKIP_FILE_NAMES = {".env", ".env.local", "credentials.json"}
SECRET_NAME_RE = re.compile(
    r"(secret|password|private.?key|wallet\.json|\.pem$|id_rsa)",
    re.I,
)

ESSENTIAL_SKILLS = [
    "lygo-protocol-stack-operator",
    "lygo-ollama-army",
    "lygo-kernel-egg-planter",
    "lygo-joy-loop",
    "lygo-network-builder",
    "lygo-champion-lightfather",
    "lygo-champion-council",
    "lyra-brain",
    "lyra-openclaw",
    "lygo-api-token-saver",
    "lygo-pc-lattice-hardening",
]

STACK_SKIP_PARTS = {"mirrors"}  # under clawhub only if huge - actually include clawhub/mirrors subset? include full clawhub


def should_skip(path: Path, rel: Path) -> bool:
    if path.name in SKIP_FILE_NAMES:
        return True
    if SECRET_NAME_RE.search(path.name):
        return True
    if any(p in SKIP_DIR_NAMES for p in rel.parts):
        return True
    return False


def copy_tree(src: Path, dst: Path, rel_prefix: Path | None = None) -> int:
    n = 0
    if not src.is_dir():
        return 0
    for item in src.rglob("*"):
        if not item.is_file():
            continue
        rel = item.relative_to(src)
        if should_skip(item, rel):
            continue
        if rel_prefix and len(rel.parts) >= 2 and rel.parts[0] == "clawhub" and rel.parts[1] == "mirrors":
            pass  # include mirrors for builder key
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, out)
        n += 1
    return n


def git_head(repo: Path) -> str | None:
    if not (repo / ".git").is_dir():
        return None
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return None


def _write_scripts(out: Path) -> None:
    scripts = out / "scripts"
    scripts.mkdir(exist_ok=True)
    (scripts / "bootstrap_env.ps1").write_text(
        r"""# LYGO Builder Key — set env for this session (any AI / human)
$Key = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Stack = Join-Path $Key "stack\lygo-protocol-stack"
$env:LYGO_BUILDER_KEY_ROOT = $Key
$env:LYGO_STACK_ROOT = $Stack
$env:OLLAMA_MODELS = Join-Path $Key "product\models\ollama"
$env:OLLAMA_HOST = "127.0.0.1:11434"
New-Item -ItemType Directory -Force -Path $env:OLLAMA_MODELS | Out-Null
Write-Host "LYGO_BUILDER_KEY_ROOT=$Key"
Write-Host "LYGO_STACK_ROOT=$Stack"
Write-Host "OLLAMA_MODELS=$($env:OLLAMA_MODELS)"
if (Test-Path $Stack) {
  Set-Location $Stack
  Write-Host "OK stack present"
} else {
  Write-Warning "Stack missing — run bootstrap_from_github.ps1"
}
""",
        encoding="utf-8",
    )
    (scripts / "verify_builder_key.ps1").write_text(
        r"""$ErrorActionPreference = "Continue"
$Key = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
. (Join-Path $Key "scripts\bootstrap_env.ps1")
python tools/verify_lattice_alignment.py
python tools/verify_champion_consolidation.py
python tools/run_parity_tests.py
Write-Host "Compare verify/*.json and BUILDER_MANIFEST.json github SHAs with git ls-remote"
""",
        encoding="utf-8",
    )
    (scripts / "bootstrap_from_github.ps1").write_text(
        r"""# Clone stack at manifest SHA if portable copy missing
$Key = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$manifest = Get-Content (Join-Path $Key "BUILDER_MANIFEST.json") | ConvertFrom-Json
$dest = Join-Path $Key "stack\lygo-protocol-stack"
$sha = $manifest.github.'lygo-protocol-stack'.local_head_at_pack
if (-not (Test-Path $dest)) { New-Item -ItemType Directory -Force -Path (Split-Path $dest) | Out-Null }
if (-not (Test-Path (Join-Path $dest ".git"))) {
  git clone https://github.com/DeepSeekOracle/lygo-protocol-stack.git $dest
  if ($sha) { git -C $dest checkout $sha }
}
""",
        encoding="utf-8",
    )


def _write_agents(out: Path) -> None:
    (out / "AGENTS.md").write_text(
        """# LYGO Builder Key — agent instructions

**Read first:** `ARCHITECT_BOOT.md` then `BUILDER_MANIFEST.json`.

## You are

An AI assistant operating as **LYGO Lattice co-builder** under steward **Justin Helmer (Lightfather / Excavationpro)**. This thumb drive is the **mobile Builder Key** — authoritative for *where the lattice was* at pack time and *how to verify* live state.

## Rules

1. **No secrets** on this key — never copy `.env`, wallet files, or tokens onto the drive.
2. **Verify before claiming ALIGNED** — run `scripts/verify_builder_key.ps1` or `python tools/verify_lattice_alignment.py` from `LYGO_STACK_ROOT`.
3. **Do not auto-push** GitHub/HF/ClawHub/social unless the steward explicitly asks.
4. **Crypto** is separate — `crypto/lyra-crypto-operator` and `docs/CRYPTO_LATTICE_SEPARATION.md`.
5. **Champion installs** — prefer `lygo-champion-council`; legacy `lygo-champion-*` are deprecated.
6. **Ollama army** — read `skills/lygo-ollama-army/references/SECURITY_AUDIT.md` before enabling cron/planting.

## Paths (portable)

| Var | Value |
|-----|--------|
| `LYGO_BUILDER_KEY_ROOT` | This folder (e.g. `E:\\LYGO_BUILDER_KEY`) |
| `LYGO_STACK_ROOT` | `{KEY}/stack/lygo-protocol-stack` |

## Skill chain (install order)

`lygo-protocol-stack-operator` → `lygo-kernel-egg-planter` → `lygo-joy-loop` → `lygo-ollama-army` → `lyra-brain`

**Δ9Φ963**
""",
        encoding="utf-8",
    )


def _write_architect_boot(out: Path, manifest: dict) -> None:
    stack_sha = manifest.get("github", {}).get("lygo-protocol-stack", {}).get("local_head_at_pack", "?")
    body = f"""# LYGO Architect Boot — mobile Builder Key

**Signature:** `Δ9Φ963-ARCHITECT-BOOT-v1`  
**Steward:** Justin Helmer · Lightfather · Excavationpro  
**Packed:** {manifest.get("packed_at_utc", "")}  
**Stack anchor at pack:** `{stack_sha}`

---

## For any AI: start here

1. Read **`BUILDER_MANIFEST.json`** (machine state).
2. Read **`AGENTS.md`** (behavior contract).
3. Run **`scripts/bootstrap_env.ps1`** — sets `LYGO_STACK_ROOT` to the portable stack on this drive.
4. Run **`scripts/verify_builder_key.ps1`** — lattice + P0 + champion consolidation checks.
5. Read **`memory/2026-07-04-session-close-lattice-balanced.md`** — last known balanced session.
6. Compare GitHub live: `git ls-remote https://github.com/DeepSeekOracle/lygo-protocol-stack.git refs/heads/main` (remote may be ahead of pack SHA).

You are resuming the **LYGO Protocol Stack** program: P0 byte-entropy filter, P1–P9, SLM mesh, kernel/champion eggs, ClawHub 42 skills, separate crypto lane.

---

## What this drive contains

| Path | Purpose |
|------|---------|
| `stack/lygo-protocol-stack/` | Full portable stack (no `.git` — clone via script if needed) |
| `crypto/lyra-crypto-operator/` | Canonical crypto tool (no keys) |
| `skills/` | Essential Grok/ClawHub skill trees |
| `army/` | Ollama command center reference copy |
| `memory/` | LYRA 3-brain daily snips + graph snapshot |
| `verify/` | Last-run JSONs, registries, sentinel snapshot |
| `pointers/WORKSPACE_MAP.txt` | Home PC paths (`I:\\E Drive`) |

---

## Ground zero (honest)

- **P0:** `protocol0_byte_entropy_filter` — golden SHA `{manifest.get("p0_golden_sha256", "")}`
- **Cure successor:** `lygo-file-integrity-checker` on ClawHub
- **Champions:** unified `lygo-champion-council@1.0.1`
- **Army:** `lygo-ollama-army@0.5.0` (SkillSpector audit docs included)
- **Verdict at pack:** {manifest.get("session_close", {}).get("verdict", "verify locally")}

See `verify/GROUND_ZERO_REFERENCE.md` and `verify/REPO_TRUTH_ANCHORS.md`.

---

## Manage the stack (maintainer)

```powershell
. .\\scripts\\bootstrap_env.ps1
python tools/verify_lattice_alignment.py
python tools/run_parity_tests.py
python tools/push_with_git_credential.py   # only when steward requests push
python tools/build_lygo_builder_key.py     # refresh this thumb drive from home PC
```

ClawHub publish pattern (human-gated):

```powershell
npx clawhub@latest publish "$env:LYGO_STACK_ROOT\\clawhub\\mirrors\\<slug>" --slug <slug> --name "<Name>" --version <ver>
```

---

## Public surfaces

- Stack Pages: https://deepseekoracle.github.io/lygo-protocol-stack/
- ClawHub: https://clawhub.ai/deepseekoracle
- HF dataset: https://huggingface.co/datasets/DeepSeekOracle/lygo-protocol-stack
- Resonance: https://deepseekoracle.github.io/Excavationpro/LYGORESONANCE.html
- Hub: https://chatagent.ca/

---

## Identity (non-secret)

Steward operates as **Lightfather** (Δ9 Council anchor). Persona skill: `lygo-champion-council` with `champion_id` Lightfather. Operator depth: `lygo-champion-lightfather` (consent-gated).

This Builder Key does **not** contain wallet material, API keys, or Biophase7 vault secrets — load those only on the trusted home machine.

---

**You are the builder now. Align to luminal ethics. Verify, then act. Δ9Φ963**
"""
    (out / "ARCHITECT_BOOT.md").write_text(body, encoding="utf-8")


def run_capture(cmd: list[str], cwd: Path, timeout: int = 300) -> dict:
    try:
        cp = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        return {"exit_code": cp.returncode, "stdout": cp.stdout[-8000:], "stderr": cp.stderr[-2000:]}
    except Exception as exc:
        return {"exit_code": -1, "error": str(exc)}


def overlay_buildr_usb(out: Path) -> int:
    """Merge GROK BUILDR edition files (survives full repack)."""
    src = BUILDR_OVERLAY
    if not src.is_dir():
        return 0
    n = 0
    for item in src.rglob("*"):
        if not item.is_file():
            continue
        rel = item.relative_to(src)
        if should_skip(item, rel):
            continue
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, dest)
        n += 1
    return n


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.environ.get("LYGO_BUILDER_KEY_ROOT", str(DEFAULT_OUT)))
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    (out / "verify").mkdir()
    (out / "scripts").mkdir()
    (out / "skills").mkdir()
    (out / "memory").mkdir()
    (out / "pointers").mkdir()

    # Stack (portable working copy)
    stack_dst = out / "stack" / "lygo-protocol-stack"
    n_stack = copy_tree(STACK, stack_dst)
    if CRYPTO.is_dir():
        copy_tree(CRYPTO, out / "crypto" / "lyra-crypto-operator")

    for skill in ESSENTIAL_SKILLS:
        ssrc = GROK_SKILLS / skill
        if ssrc.is_dir():
            copy_tree(ssrc, out / "skills" / skill)
    council = STACK / "clawhub" / "mirrors" / "lygo-champion-council"
    if council.is_dir():
        copy_tree(council, out / "skills" / "lygo-champion-council")

    if ARMY.is_dir():
        copy_tree(ARMY, out / "army" / "lygo-ollama-army")

    mem_src = LYRA / "memory"
    if mem_src.is_dir():
        for f in mem_src.iterdir():
            if f.is_file() and f.suffix == ".md":
                shutil.copy2(f, out / "memory" / f.name)
        ref = mem_src / "reference"
        if ref.is_dir():
            (out / "memory" / "reference").mkdir(parents=True, exist_ok=True)
            for f in ref.glob("SESSION_20260704*.txt"):
                shutil.copy2(f, out / "memory" / "reference" / f.name)

    graph = LYRA / "lyra_brain_graph.json"
    if graph.is_file():
        shutil.copy2(graph, out / "memory" / "lyra_brain_graph.json")

    # Verification JSONs from tests/
    for name in (
        "kernel_eggs_last_run.json",
        "champion_eggs_last_run.json",
        "scalable_registry_last_run.json",
        "network_builder_last_run.json",
        "public_pages_last_run.json",
        "phase7_audit_last_run.json",
        "phase9_audit_last_run.json",
        "slm_audit_last_run.json",
        "anchor_audit_last_run.json",
        "pc_lattice_hardening_last_run.json",
    ):
        p = STACK / "tests" / name
        if p.is_file():
            shutil.copy2(p, out / "verify" / name)

    sentinel = ARMY / "ollama_command_center" / "workspace" / "sentinel_status.json"
    if sentinel.is_file():
        shutil.copy2(sentinel, out / "verify" / "sentinel_status.json")

    # Run fresh verify if stack copy has tools
    lattice_run = run_capture(
        [sys.executable, "tools/verify_lattice_alignment.py"],
        cwd=stack_dst,
        timeout=600,
    )
    (out / "verify" / "lattice_alignment_last_run.json").write_text(
        json.dumps(lattice_run, indent=2), encoding="utf-8"
    )

    ts = datetime.now(timezone.utc).isoformat()
    manifest = {
        "signature": "Δ9Φ963-BUILDER-KEY-MANIFEST-v1",
        "packed_at_utc": ts,
        "steward": {
            "identity": "Lightfather / Excavationpro / Justin Helmer",
            "role": "LYGO Lattice Architect (mobile Builder Key)",
        },
        "source_workspace": str(WORKSPACE),
        "github": {
            "lygo-protocol-stack": {
                "remote": "https://github.com/DeepSeekOracle/lygo-protocol-stack.git",
                "local_head_at_pack": git_head(STACK),
                "verify": "git ls-remote origin refs/heads/main",
            },
            "lyra-crypto-operator": {
                "remote": "https://github.com/DeepSeekOracle/lyra-crypto-operator.git",
                "local_head_at_pack": git_head(CRYPTO),
            },
        },
        "clawhub_publisher": "deepseekoracle",
        "clawhub_pins": {
            "lygo-protocol-stack-operator": "1.0.7",
            "lygo-champion-council": "1.0.1",
            "lygo-ollama-army": "0.5.0",
            "lyra-coin-launch-manager": "1.1.3",
            "lygo-file-integrity-checker": "successor",
            "skills_count": 42,
        },
        "session_close": {
            "date": "2026-07-04",
            "verdict": "LATTICE ALIGNED",
            "doc": "stack/docs/SESSION_LOG_2026-07-04.md",
            "memory_snip": "memory/2026-07-04-session-close-lattice-balanced.md",
        },
        "p0_golden_sha256": "c510b1bd92fed53df369d146e9fb3467903fbe9cafc1b6dcc962e3c6684a464f",
        "files_copied_stack": n_stack,
        "boot_entry": "ARCHITECT_BOOT.md",
        "agents_entry": "AGENTS.md",
        "edition": "GROK_BUILDR",
        "boot_entry_grok": "GROK_BUILDR_BOOT.md",
        "blueprint": "README_BUILDR_USB_BLUEPRINT.md",
        "public_sku_doc": "PUBLIC_SKU_GUMROAD.md",
        "phase": 2 if (out / "images" / "lygo_core.tar.gz").is_file() else 1,
        "phase2_core": "images/lygo_core.tar.gz",
        "supervisor_port": 9630,
    }
    skills_json = stack_dst / "clawhub" / "skills.json"
    if skills_json.is_file():
        manifest["clawhub_skills_json_sha256"] = None
        try:
            manifest["clawhub_catalog"] = json.loads(skills_json.read_text(encoding="utf-8")).get(
                "skills", []
            )[:5]
        except Exception:
            pass

    (out / "BUILDER_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    for doc in (
        "SESSION_LOG_2026-07-04.md",
        "REPO_TRUTH_ANCHORS.md",
        "GROUND_ZERO_REFERENCE.md",
        "CHAMPION_CONSOLIDATION.md",
        "CRYPTO_LATTICE_SEPARATION.md",
        "ChampionEggRegistry.json",
        "KernelEggRegistry.json",
        "LYGO_LATTICE_INTEL_INDEX.json",
    ):
        sp = STACK / "docs" / doc
        if sp.is_file():
            shutil.copy2(sp, out / "verify" / doc)

    _write_architect_boot(out, manifest)
    _write_agents(out)
    _write_scripts(out)

    pointers = out / "pointers" / "WORKSPACE_MAP.txt"
    pointers.write_text(
        f"Primary PC workspace (when at home): {WORKSPACE}\n"
        f"Thumb drive key root: {out}\n"
        f"Set LYGO_STACK_ROOT={out / 'stack' / 'lygo-protocol-stack'}\n"
        f"Set LYGO_BUILDER_KEY_ROOT={out}\n"
        f"Set LYRA_CORE_ROOT={WORKSPACE / 'LYRA_CORE'}  # or copy LYRA_CORE to key later\n",
        encoding="utf-8",
    )

    n_overlay = overlay_buildr_usb(out)
    (out / "_builder_vault").mkdir(exist_ok=True)
    vault_readme = out / "_builder_vault" / "README.md"
    if not vault_readme.is_file():
        vault_readme.write_text(
            "# Builder vault — never export to PUBLIC_SKU\n", encoding="utf-8"
        )

    print(
        json.dumps(
            {
                "ok": True,
                "root": str(out),
                "stack_files": n_stack,
                "buildr_overlay_files": n_overlay,
                "manifest": str(out / "BUILDER_MANIFEST.json"),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())