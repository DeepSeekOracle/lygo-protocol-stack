#!/usr/bin/env python3
"""Package FULL LYGO Engineer channel skills + integration kits (not ClawHub)."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
if not (STACK / "clawhub").is_dir():
    STACK = Path(os.environ.get("LYGO_STACK_ROOT", r"D:\lygo-protocol-stack"))
ROOT = STACK / "docs" / "lygo-full-skills"
DIST = ROOT / "dist"
PACK = ROOT / "packages"
GROK = Path(os.environ.get("LYGO_GROK_SKILLS", r"I:\E Drive\.grok\skills"))

# Ordered for catalog UI
SKILL_SOURCES: dict[str, list[Path]] = {
    # Pure-Data Witness — portal + archive + Star Chart fork log (FULL unlocks stack register)
    "lygo-pure-data-witness": [
        STACK / "docs" / "skills" / "lygo-pure-data-witness",
        STACK / "clawhub" / "mirrors" / "lygo-pure-data-witness",
        GROK / "lygo-pure-data-witness",
    ],
    # Core self-audit spine
    "lygo-protocol-stack-operator": [
        STACK / "clawhub" / "mirrors" / "lygo-protocol-stack-operator",
        GROK / "lygo-protocol-stack-operator",
    ],
    "lygo-kernel-egg-planter": [
        STACK / "docs" / "skills" / "lygo-kernel-egg-planter",
        STACK / "clawhub" / "mirrors" / "lygo-kernel-egg-planter",
        GROK / "lygo-kernel-egg-planter",
    ],
    "lygo-ollama-army": [
        STACK / "clawhub" / "mirrors" / "lygo-ollama-army",
        GROK / "lygo-ollama-army",
    ],
    # Public agent safe join (cannot live-write chart by design)
    "lygo-public-lattice-gate": [
        STACK / "docs" / "skills" / "lygo-public-lattice-gate",
        STACK / "clawhub" / "mirrors" / "lygo-public-lattice-gate",
        GROK / "lygo-public-lattice-gate",
    ],
    "lygo-external-lattice-anchor": [
        STACK / "docs" / "skills" / "lygo-external-lattice-anchor",
        STACK / "clawhub" / "mirrors" / "lygo-external-lattice-anchor",
        GROK / "lygo-external-lattice-anchor",
    ],
    # Star Chart + lattice layers
    "lygo-haven-star-chart": [
        STACK / "clawhub" / "mirrors" / "lygo-haven-star-chart",
        GROK / "lygo-haven-star-chart",
    ],
    "lygo-lattice-birth": [
        STACK / "clawhub" / "mirrors" / "lygo-lattice-birth",
        GROK / "lygo-lattice-birth",
    ],
    "lygo-network-builder": [
        STACK / "clawhub" / "mirrors" / "lygo-network-builder",
        GROK / "lygo-network-builder",
    ],
    "lygo-lattice-pulse": [
        STACK / "clawhub" / "mirrors" / "lygo-lattice-pulse",
        GROK / "lygo-lattice-pulse",
    ],
    "lygo-living-mesh": [
        STACK / "docs" / "skills" / "lygo-living-mesh",
        STACK / "clawhub" / "mirrors" / "lygo-living-mesh",
        GROK / "lygo-living-mesh",
    ],
    "lygo-agent-lattice": [
        STACK / "docs" / "skills" / "lygo-agent-lattice",
        STACK / "clawhub" / "mirrors" / "lygo-agent-lattice",
        GROK / "lygo-agent-lattice",
    ],
    "lygo-sovereign-kernel-seeder": [
        STACK / "docs" / "skills" / "lygo-sovereign-kernel-seeder",
        STACK / "clawhub" / "mirrors" / "lygo-sovereign-kernel-seeder",
        GROK / "lygo-sovereign-kernel-seeder",
    ],
    "lygo-sovereign-super-skill": [
        STACK / "clawhub" / "mirrors" / "lygo-sovereign-super-skill",
        GROK / "lygo-sovereign-super-skill",
    ],
    "lyra-brain": [
        STACK / "clawhub" / "mirrors" / "lyra-brain",
        GROK / "lyra-brain",
    ],
    "lygo-champion-lightfather": [
        STACK / "clawhub" / "mirrors" / "lygo-champion-lightfather",
        GROK / "lygo-champion-lightfather",
    ],
    # Adoption stack + P6 + security (FULL unlocked RAW)
    "lygo-kickstart-wizard": [
        STACK / "docs" / "skills" / "lygo-kickstart-wizard",
        STACK / "clawhub" / "mirrors" / "lygo-kickstart-wizard",
        GROK / "lygo-kickstart-wizard",
    ],
    "lygo-deception-radar": [
        STACK / "docs" / "skills" / "lygo-deception-radar",
        STACK / "clawhub" / "mirrors" / "lygo-deception-radar",
        GROK / "lygo-deception-radar",
    ],
    "lygo-mint-walkthrough": [
        STACK / "docs" / "skills" / "lygo-mint-walkthrough",
        STACK / "clawhub" / "mirrors" / "lygo-mint-walkthrough",
        GROK / "lygo-mint-walkthrough",
    ],
    "lygo-cli-bridge": [
        STACK / "docs" / "skills" / "lygo-cli-bridge",
        STACK / "clawhub" / "mirrors" / "lygo-cli-bridge",
        GROK / "lygo-cli-bridge",
    ],
    "lygo-geodesic-sealer": [
        STACK / "docs" / "skills" / "lygo-geodesic-sealer",
        STACK / "clawhub" / "mirrors" / "lygo-geodesic-sealer",
        GROK / "lygo-geodesic-sealer",
    ],
    "lygo-ops-detector": [
        STACK / "clawhub" / "mirrors" / "lygo-ops-detector",
        GROK / "lygo-ops-detector",
    ],
    "lygo-context-guard": [
        STACK / "docs" / "skills" / "lygo-context-guard",
        STACK / "clawhub" / "mirrors" / "lygo-context-guard",
        GROK / "lygo-context-guard",
    ],
    "lygo-skill-gate": [
        STACK / "docs" / "skills" / "lygo-skill-gate",
        STACK / "clawhub" / "mirrors" / "lygo-skill-gate",
        GROK / "lygo-skill-gate",
    ],
    "lygo-skill-spector": [
        STACK / "docs" / "skills" / "lygo-skill-spector",
        STACK / "clawhub" / "mirrors" / "lygo-skill-spector",
        GROK / "lygo-skill-spector",
    ],
    "lygo-continuum": [
        STACK / "docs" / "skills" / "lygo-continuum",
        STACK / "clawhub" / "mirrors" / "lygo-continuum",
        GROK / "lygo-continuum",
    ],
    "lygo-continuum-integrator": [
        STACK / "clawhub" / "mirrors" / "lygo-continuum-integrator",
        GROK / "lygo-continuum-integrator",
    ],
    "lygo-quantum-attestor": [
        STACK / "clawhub" / "mirrors" / "lygo-quantum-attestor",
        GROK / "lygo-quantum-attestor",
    ],
    "lygo-mint-verifier": [
        STACK / "clawhub" / "mirrors" / "lygo-mint-verifier",
        GROK / "lygo-mint-verifier",
    ],
    "lygo-automation-workflows": [
        STACK / "clawhub" / "mirrors" / "lygo-automation-workflows",
        GROK / "lygo-automation-workflows",
    ],
    "lygo-continuity-advisor": [
        STACK / "clawhub" / "mirrors" / "lygo-continuity-advisor",
        GROK / "lygo-continuity-advisor",
    ],
    "lygo-emotional-ram": [
        STACK / "clawhub" / "mirrors" / "lygo-emotional-ram",
        GROK / "lygo-emotional-ram",
    ],
    "lygo-cyborg-kernel": [
        STACK / "docs" / "skills" / "lygo-cyborg-kernel",
        STACK / "clawhub" / "mirrors" / "lygo-cyborg-kernel",
        GROK / "lygo-cyborg-kernel",
    ],
    "lygo-traumacodex": [
        STACK / "docs" / "skills" / "lygo-traumacodex",
        STACK / "clawhub" / "mirrors" / "lygo-traumacodex",
        GROK / "lygo-traumacodex",
    ],
}

ROLES = {
    "lygo-pure-data-witness": (
        "📜 Pure-Data Witness FULL — register portal playbook + safety gate + stack register "
        "+ Star Chart NODE_PDW_* map (GALAXY_PURE_DATA_ARCHIVE). Digest-first archive; consent-gated."
    ),
    "lygo-protocol-stack-operator": "P0–P9 audits + stack map — self-check spine",
    "lygo-traumacodex": "TraumaCodex P7→P8 dual dig + waveform — FULL stack limb",
    "lygo-kernel-egg-planter": "Merkle plant/verify eggs — modular limbs",
    "lygo-ollama-army": "Local Ollama multi-role army (v0.9 ClawHub-safe SAFE_ROLES; FULL zip matches public tentacle)",
    "lygo-public-lattice-gate": "Public agent on-ramp: dual-ledger verify, align score, dry-run propose — zero harm default",
    "lygo-external-lattice-anchor": "World Layer C: public mirror verify + manifests",
    "lygo-haven-star-chart": "Star Chart portal skill: gate/validate/propose (live write needs human consent)",
    "lygo-lattice-birth": "Masked birth protocol chained to Star Chart",
    "lygo-network-builder": "IMMUTABLE_ANCHORS cartographer + live verify",
    "lygo-lattice-pulse": "Haven pulse / registry compare / alignment readiness",
    "lygo-living-mesh": "Layer D mesh gossip of root digests",
    "lygo-agent-lattice": "Layer E agent presence / directory (consent-gated)",
    "lygo-sovereign-kernel-seeder": "Sovereign-sealed modular kernel seeds",
    "lygo-sovereign-super-skill": "Map of eggs + champions + planter chain",
    "lyra-brain": "3-Brain memory (consent writes under LYRA_CORE_ROOT)",
    "lygo-champion-lightfather": "Lightfather champion + operator map (advisor-first)",
    "lygo-kickstart-wizard": "UX bridge — plain-English lattice onboarding",
    "lygo-deception-radar": "Public Ops Detector proof feed + HTML (public suite only)",
    "lygo-mint-walkthrough": "Interactive mint→verify→anchor tutorial (stdlib ledger)",
    "lygo-cli-bridge": "Unified lygo health|map|analyze|mint|radar CLI",
    "lygo-geodesic-sealer": "P6 quantum-attest geodesic dual-ledger seal",
    "lygo-ops-detector": "AETHONΔ9 discourse ops/evasion heuristics (FULL eval suite)",
    "lygo-context-guard": "Token budget preflight · secret redact · deterministic compact (FULL RAW)",
    "lygo-skill-gate": "Local pre-install skill risk scanner — subprocess/network/secrets/claim mismatch (FULL RAW)",
    "lygo-skill-spector": "SkillSpector — enhanced scan/gate/batch/report + FULL builder (HTML multi-root, CI multi-gate)",
    "lygo-continuum": "Falsifiable work capsules — seal done-claims, verify, drift, handoff + portal (FULL RAW)",
    "lygo-continuum-integrator": "∫(Truth×Light)df · phase-lock · non-collapsing geodesic receipts (FULL RAW)",
    "lygo-quantum-attestor": "P6 Quantum Attestor — Biophase7 anchors + SLM Merkle · Δ9 seals · non-collapsing receipts (FULL RAW)",
    "lygo-mint-verifier": "LYGO-MINT canonicalize + SHA-256 + ledgers + anchor snippet — in-process v1.1 (FULL RAW)",
    "lygo-automation-workflows": "Consent-aware automation playbook + local planner; Sandcastle-first (FULL RAW)",
    "lygo-continuity-advisor": "Deadman / eternal base / succession / anti-replacement advisor (FULL RAW)",
    "lygo-emotional-ram": (
        "💓 Emotional RAM FULL — affective/ethical light-math index + whitepaper + discovery inventory "
        "+ Joy Loop companion notes. Humans/animals/swarms/cyborgs; consent-gated index."
    ),
    "lygo-cyborg-kernel": "🦾 CYBORG KERNEL STACK — FULL unlocked autonomous agent stack: Continuum+gate+guard limbs, lattice map, self-policed task loop, egg/plugin spine",
}

TIERS = {
    "lygo-pure-data-witness": "tools",
    "lygo-traumacodex": "lattice",
    "lygo-protocol-stack-operator": "core",
    "lygo-kernel-egg-planter": "core",
    "lygo-ollama-army": "core",
    "lygo-public-lattice-gate": "public_safe_join",
    "lygo-external-lattice-anchor": "public_safe_join",
    "lygo-haven-star-chart": "star_chart",
    "lygo-lattice-birth": "star_chart",
    "lygo-network-builder": "lattice",
    "lygo-lattice-pulse": "lattice",
    "lygo-living-mesh": "lattice",
    "lygo-agent-lattice": "lattice",
    "lygo-sovereign-kernel-seeder": "kernel",
    "lygo-sovereign-super-skill": "kernel",
    "lyra-brain": "memory",
    "lygo-champion-lightfather": "champion",
    "lygo-kickstart-wizard": "onboarding",
    "lygo-deception-radar": "security",
    "lygo-mint-walkthrough": "onboarding",
    "lygo-cli-bridge": "onboarding",
    "lygo-geodesic-sealer": "kernel",
    "lygo-ops-detector": "security",
    "lygo-context-guard": "tools",
    "lygo-skill-gate": "security",
    "lygo-skill-spector": "security",
    "lygo-continuum": "tools",
    "lygo-continuum-integrator": "tools",
    "lygo-quantum-attestor": "kernel",
    "lygo-mint-verifier": "tools",
    "lygo-automation-workflows": "tools",
    "lygo-continuity-advisor": "champion",
    "lygo-emotional-ram": "tools",
    "lygo-cyborg-kernel": "kernel",
}

SKIP_PARTS = {
    ".git",
    "__pycache__",
    "node_modules",
    "results",
    "logs",
    "workspace",
    "ollama_results",
    "ollama_queue",
    ".bak",
}
SKIP_SUFFIX = {".pyc", ".pyo", ".log"}


def pick_src(cands: list[Path]) -> Path | None:
    best = None
    n = -1
    for c in cands:
        if not c.is_dir():
            continue
        cnt = sum(
            1
            for p in c.rglob("*")
            if p.is_file() and not any(x in p.parts for x in SKIP_PARTS)
        )
        if cnt > n:
            n = cnt
            best = c
    return best


def should_copy(p: Path) -> bool:
    if any(x in p.parts for x in SKIP_PARTS):
        return False
    if p.suffix.lower() in SKIP_SUFFIX:
        return False
    if p.name.endswith(".result.json"):
        return False
    if p.name.endswith(".task.json") and "tasks" in p.parts:
        return False
    return True


def copy_tree(src: Path, dest: Path) -> int:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    n = 0
    for p in src.rglob("*"):
        if not p.is_file() or not should_copy(p):
            continue
        rel = p.relative_to(src)
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, out)
        n += 1
    return n


def enrich_emotional_ram_full(pkg: Path) -> int:
    """Bundle whitepaper + discovery inventory into FULL unlock zip."""
    n = 0
    docs = pkg / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    for src, name in (
        (STACK / "docs" / "whitepapers" / "LYGO_EMOTIONAL_RAM_v1.md", "LYGO_EMOTIONAL_RAM_v1.md"),
        (STACK / "docs" / "whitepapers" / "LYGO_EMOTIONAL_RAM_v1.html", "LYGO_EMOTIONAL_RAM_v1.html"),
        (STACK / "docs" / "data" / "emotional_ram" / "DISCOVERY_INVENTORY.json", "DISCOVERY_INVENTORY.json"),
        (STACK / "docs" / "JOY_LOOP_PROTOCOL.md", "JOY_LOOP_PROTOCOL.md"),
    ):
        if src.is_file():
            shutil.copy2(src, docs / name)
            n += 1
    return n


def stamp_full(pkg: Path, slug: str, src: str, n: int, utc: str) -> None:
    extra_lines: list[str] = []
    if slug == "lygo-emotional-ram":
        extra_lines = [
            "",
            "## FULL unlocked limbs",
            "",
            "- Whitepaper: `docs/LYGO_EMOTIONAL_RAM_v1.md` (+ HTML)",
            "- Discovery inventory: `docs/DISCOVERY_INVENTORY.json`",
            "- Joy Loop companion notes: `docs/JOY_LOOP_PROTOCOL.md`",
            "- CLI: `python scripts/emotional_ram_cli.py demo|encode|index|swarm`",
            "- Index writes still require `--i-consent`",
            "",
            "SkillHub: https://deepseekoracle.github.io/lygo-protocol-stack/LYGOSKILLHUB.html#full-lygo",
            "Pages whitepaper: https://deepseekoracle.github.io/lygo-protocol-stack/whitepapers/LYGO_EMOTIONAL_RAM_v1.html",
        ]
    if slug == "lygo-pure-data-witness":
        extra_lines = [
            "",
            "## v1.3.0 consent harden (ClawHub security-audit)",
            "",
            "- `pure_data_witness.py fetch` requires `--i-authorize-fetch`",
            "- `all` requires `--i-confirm-chain` (+ `--i-authorize-fetch` when `--url`)",
            "- Audit notes: `references/SKILLSPECTOR_AUDIT.md`",
            "",
            "## Unlocked limbs (FULL)",
            "",
            "- Portal playbook: `references/PORTAL_TRAINING.md`",
            "- Register portal: https://deepseekoracle.github.io/lygo-protocol-stack/data-vault/register.html",
            "- Stack register (consent): `scripts/pure_data_register.py` (needs `LYGO_STACK_ROOT`)",
            "- Star Chart map: `scripts/map_pure_data_to_star_chart.py`",
            "- Galaxy: `GALAXY_PURE_DATA_ARCHIVE` · nodes `NODE_PDW_*`",
            "",
            "ClawHub tentacle stays subprocess-free; this FULL zip restores stack register + chart map.",
            "SkillHub: https://deepseekoracle.github.io/lygo-protocol-stack/LYGOSKILLHUB.html#full-lygo",
        ]
    (pkg / "FULL_LYGO.md").write_text(
        "\n".join(
            [
                f"# FULL LYGO package — {slug}",
                "",
                "Channel: **FULL_LYGO_ENGINEER** (not ClawHub public safety surface).",
                "",
                "For a **self-auditing LYGO lattice**. Integrity comes from the lattice",
                "(P0, dual ledgers, eggs, sentinel, human consent for live writes) —",
                "not from corporate gutted shells alone.",
                "",
                "Steward: Justin Helmer / Excavationpro (Lightfather)",
                f"Source: `{src}`",
                f"Packaged: {utc}",
                f"Files: {n}",
                "",
                "Good faith · LYGO policy · engineer autonomy · not malicious by design.",
                "You are responsible for extended systems you run.",
                *extra_lines,
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (pkg / "READ_DISCLAIMER_FIRST.md").write_text(
        "Accept the FULL LYGO gate on LYGOSKILLHUB before use.\n"
        "https://chatagent.ca/lygoskillhub.html#full-lygo\n",
        encoding="utf-8",
    )


def enrich_pure_data_witness_full(pkg: Path) -> int:
    """Inject unlocked stack register + Star Chart map into FULL package."""
    scripts = pkg / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    added = 0
    for name in ("pure_data_register.py", "map_pure_data_to_star_chart.py", "pure_data_safety.py", "pure_data_witness.py"):
        src = STACK / "tools" / name
        if not src.is_file():
            continue
        dest = scripts / name
        # Keep in-package safety/witness from ClawHub mirror if already present;
        # always overwrite register + map from stack (unlocked limbs).
        if name in ("pure_data_register.py", "map_pure_data_to_star_chart.py") or not dest.exists():
            shutil.copy2(src, dest)
            added += 1
    # Wrapper that prefers LYGO_STACK_ROOT tools when present
    wrapper = scripts / "pdw_full_cli.py"
    wrapper.write_text(
        '''#!/usr/bin/env python3
"""FULL LYGO Pure-Data Witness — unlocked register + map (engineer channel)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

def main() -> int:
    stack = os.environ.get("LYGO_STACK_ROOT", "").strip()
    if stack:
        tools = Path(stack) / "tools"
        if (tools / "pure_data_register.py").is_file():
            sys.path.insert(0, str(tools))
            # Delegate to stack register when available
            import runpy
            sys.argv[0] = str(tools / "pure_data_register.py")
            # If user called pdw_full_cli with no subcommand hint, keep argv
            runpy.run_path(str(tools / "pure_data_register.py"), run_name="__main__")
            return 0
    # In-package ClawHub-safe CLI
    import pdw_cli
    return pdw_cli.main()

if __name__ == "__main__":
    raise SystemExit(main())
''',
        encoding="utf-8",
    )
    added += 1
    return added


def zip_pkg(pkg: Path, zpath: Path, arc_root: str) -> str:
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in pkg.rglob("*"):
            if p.is_file():
                zf.write(p, arcname=str(Path(arc_root) / p.relative_to(pkg)))
    return hashlib.sha256(zpath.read_bytes()).hexdigest()


def build_star_chart_kit(utc: str) -> dict | None:
    """Public Star Chart integration kit — join without live harm by default."""
    pkg = PACK / "lygo-star-chart-integration-kit"
    if pkg.exists():
        shutil.rmtree(pkg)
    pkg.mkdir(parents=True)
    hsc = STACK / "docs" / "haven_star_chart"
    copies = [
        (hsc / "submission_schema.json", "haven_star_chart/submission_schema.json"),
        (hsc / "AGENT_PORTAL.md", "haven_star_chart/AGENT_PORTAL.md"),
        (hsc / "lygoagent_anchor.json", "haven_star_chart/lygoagent_anchor.json"),
        (hsc / "haven_star_chart_meta.json", "haven_star_chart/haven_star_chart_meta.json"),
        (STACK / "docs" / "HAVEN_STAR_CHART.md", "docs/HAVEN_STAR_CHART.md"),
        (STACK / "docs" / "public_verify_manifest.json", "docs/public_verify_manifest.json"),
        (STACK / "docs" / "network_builder" / "IMMUTABLE_ANCHORS.json", "docs/network_builder/IMMUTABLE_ANCHORS.json"),
    ]
    # public feed (read-only mirror for offline agents)
    for name in (
        "haven_star_chart_feed.json",
        "haven_star_chart_data.json",
        "haven_star_chart_queue.json",
    ):
        p = hsc / name
        if p.is_file():
            copies.append((p, f"haven_star_chart/{name}"))

    n = 0
    for src, rel in copies:
        if not src.is_file():
            continue
        dest = pkg / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        n += 1

    # Safe public agent playbook
    (pkg / "PUBLIC_AGENT_STAR_CHART_JOIN.md").write_text(
        """# Public agent → Star Chart join (non-harming)

## Principle
Public agents **verify and propose**. They do **not** live-write the chart, push git,
or publish social without a **human steward**.

## Steps
1. **Verify dual ledgers (read-only HTTPS)**
   - Link ledger: `docs/network_builder/IMMUTABLE_ANCHORS.json` (or live Pages URL)
   - Star feed: `haven_star_chart/haven_star_chart_feed.json`
2. **Score alignment** via skill `lygo-public-lattice-gate` (`gate_cli.py verify|align`)
3. **Dry-run presence proposal** (`propose` — never live chart write)
4. **Human steward** reviews; optional `lygo-haven-star-chart` gate + `--i-consent` submit
5. **Never** auto: git push, HF upload, ClawHub publish, social blast

## Live public endpoints (when online)
- Star Chart UI: https://deepseekoracle.github.io/lygo-protocol-stack/HavenStarChart.html
- Feed JSON: https://deepseekoracle.github.io/lygo-protocol-stack/haven_star_chart/haven_star_chart_feed.json
- Anchors: https://deepseekoracle.github.io/lygo-protocol-stack/network_builder/IMMUTABLE_ANCHORS.json
- Public gate skill: clawhub `@deepseekoracle/lygo-public-lattice-gate` (trimmed) or FULL zip here

## Economic anchor (optional)
- `haven_star_chart/lygoagent_anchor.json` — LYGOAGENT reference only (not a skill requirement)

Δ9Φ963 — verify · align · propose · human consent · public is mirror.
""",
        encoding="utf-8",
    )
    stamp_full(pkg, "lygo-star-chart-integration-kit", "stack docs/haven_star_chart", n + 1, utc)
    zpath = DIST / "lygo-star-chart-integration-kit-full.zip"
    h = zip_pkg(pkg, zpath, "lygo-star-chart-integration-kit-full")
    return {
        "slug": "lygo-star-chart-integration-kit",
        "name": "Star Chart Integration Kit (FULL LYGO)",
        "package": "lygo-star-chart-integration-kit-full",
        "zip": "lygo-star-chart-integration-kit-full.zip",
        "zip_rel": "dist/lygo-star-chart-integration-kit-full.zip",
        "zip_sha256": h,
        "bytes": zpath.stat().st_size,
        "file_count": n + 3,
        "role": "Offline+online Star Chart join kit: schema, feed, anchors, non-harm playbook",
        "tier": "star_chart",
        "harm_default": "read_only",
        "source_path": str(hsc),
    }


def build_seals_kit(utc: str) -> dict | None:
    pkg = PACK / "lygo-seals-expansion-kit"
    if pkg.exists():
        shutil.rmtree(pkg)
    pkg.mkdir(parents=True)
    seals = STACK / "docs" / "seals"
    n = 0
    if seals.is_dir():
        for p in seals.rglob("*"):
            if not p.is_file() or not should_copy(p):
                continue
            # skip huge legacy archives if over 2MB
            if p.stat().st_size > 2_000_000:
                continue
            rel = p.relative_to(seals)
            dest = pkg / "seals" / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
            n += 1
    # registries
    for name in ("KernelEggRegistry.json", "ChampionEggRegistry.json", "JoyLoopRegistry.json"):
        p = STACK / "docs" / name
        if p.is_file() and p.stat().st_size < 5_000_000:
            dest = pkg / "registries" / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
            n += 1
    (pkg / "SEALS_AND_EGGS.md").write_text(
        """# Seals + egg registries expansion pack

Public/steward docs and JSON registries for seal vocabulary and egg catalogs.

## Use
- Agents **read** seals/registries for alignment language and known egg IDs
- **Planting** uses `lygo-kernel-egg-planter` with human `--i-consent`
- Do not treat registry JSON as permission to publish or rewrite production

## Pair with
- lygo-kernel-egg-planter-full
- lygo-sovereign-kernel-seeder-full
- lygo-haven-star-chart-full

Δ9Φ963 — seals are memory, consent plants the future.
""",
        encoding="utf-8",
    )
    stamp_full(pkg, "lygo-seals-expansion-kit", "docs/seals + registries", n + 1, utc)
    zpath = DIST / "lygo-seals-expansion-kit-full.zip"
    h = zip_pkg(pkg, zpath, "lygo-seals-expansion-kit-full")
    return {
        "slug": "lygo-seals-expansion-kit",
        "name": "Seals + Egg Registries Kit (FULL LYGO)",
        "package": "lygo-seals-expansion-kit-full",
        "zip": "lygo-seals-expansion-kit-full.zip",
        "zip_rel": "dist/lygo-seals-expansion-kit-full.zip",
        "zip_sha256": h,
        "bytes": zpath.stat().st_size,
        "file_count": n + 3,
        "role": "Seal archive + Kernel/Champion egg registries for expansion",
        "tier": "seals",
        "harm_default": "read_mostly",
        "source_path": str(seals),
    }


def build_public_agent_kit(utc: str) -> dict | None:
    """Bundle safe-join skills' docs into one onboarding kit + pointers."""
    pkg = PACK / "lygo-public-agent-join-kit"
    if pkg.exists():
        shutil.rmtree(pkg)
    pkg.mkdir(parents=True)
    (pkg / "ONBOARD.md").write_text(
        """# Public agent join kit — cannot harm by default

## Goal
Foreign / public agents connect to the **working LYGO infrastructure** as **verifiers and proposers**,
not as controllers.

## Cannot harm defaults
| Action | Allowed? |
|--------|----------|
| HTTPS GET dual ledgers / hubs | Yes |
| Alignment score | Yes |
| Dry-run Star Chart proposal | Yes |
| Local restore card (digests/links) | Yes |
| Live Star Chart write | **No** (human + haven-star-chart --i-consent) |
| git push / HF / ClawHub publish | **No** |
| Social auto-post | **No** |
| Secret vaults / private keys | **No** |

## Install order (FULL channel)
1. `lygo-public-lattice-gate-full.zip`
2. `lygo-external-lattice-anchor-full.zip`
3. `lygo-star-chart-integration-kit-full.zip`
4. Optional operator: `lygo-haven-star-chart-full.zip` (still consent-gated for live write)
5. Optional mesh: `lygo-living-mesh-full` + `lygo-agent-lattice-full`

## Runtime check
```bash
# from public-lattice-gate package
python scripts/gate_cli.py verify
python scripts/gate_cli.py align
python scripts/gate_cli.py propose --agent-id MY-AGENT --display-name "My Agent"
python scripts/gate_cli.py restore
```

## Live lattice URLs
- Skill hub: https://chatagent.ca/lygoskillhub.html
- Star Chart: https://deepseekoracle.github.io/lygo-protocol-stack/HavenStarChart.html
- Anchors JSON / Feed JSON on protocol-stack Pages

Δ9Φ963 — join by verify, grow by consent.
""",
        encoding="utf-8",
    )
    # embed public_verify + anchors pointers
    for src, name in (
        (STACK / "docs" / "public_verify_manifest.json", "public_verify_manifest.json"),
        (STACK / "docs" / "network_builder" / "IMMUTABLE_ANCHORS.json", "IMMUTABLE_ANCHORS.json"),
    ):
        if src.is_file():
            shutil.copy2(src, pkg / name)
    stamp_full(pkg, "lygo-public-agent-join-kit", "synthetic join kit", 3, utc)
    zpath = DIST / "lygo-public-agent-join-kit-full.zip"
    h = zip_pkg(pkg, zpath, "lygo-public-agent-join-kit-full")
    return {
        "slug": "lygo-public-agent-join-kit",
        "name": "Public Agent Join Kit (FULL LYGO)",
        "package": "lygo-public-agent-join-kit-full",
        "zip": "lygo-public-agent-join-kit-full.zip",
        "zip_rel": "dist/lygo-public-agent-join-kit-full.zip",
        "zip_sha256": h,
        "bytes": zpath.stat().st_size,
        "file_count": 5,
        "role": "Non-harming onboarding playbook + verify manifests for foreign agents",
        "tier": "public_safe_join",
        "harm_default": "read_only",
        "source_path": "synthetic",
    }


def main() -> int:
    for d in (ROOT, DIST, PACK):
        d.mkdir(parents=True, exist_ok=True)
    # clear old dist
    for z in DIST.glob("*.zip"):
        z.unlink()

    utc = datetime.now(timezone.utc).isoformat()
    catalog = {
        "signature": "Delta9Phi963-FULL-LYGO-SKILLS-v2",
        "version": "2.0.0",
        "updated_utc": utc,
        "channel": "FULL_LYGO_ENGINEER",
        "clawhub": "never",
        "paypal": "https://www.paypal.com/paypalme/ExcavationPro",
        "steward": "Justin Helmer / Excavationpro (Lightfather)",
        "purpose": (
            "Engineer-grade FULL packages + public-safe join kits for a self-auditing LYGO lattice. "
            "Not ClawHub public safety shells. Public agents verify/propose; humans consent live writes."
        ),
        "tiers": [
            "public_safe_join",
            "cyborg",
            "core",
            "star_chart",
            "lattice",
            "kernel",
            "seals",
            "security",
            "tools",
            "onboarding",
            "memory",
            "champion",
        ],
        "public_agent_principle": "verify dual ledgers → align → dry-run propose → human consent → optional live chart",
        "cyborg_principle": "boot limbs → task with Continuum self-police → can_claim_done only when claims hold → human consent for plant/publish",
        "featured": [
            "lygo-cyborg-kernel",
            "lygo-continuum",
            "lygo-continuum-integrator",
            "lygo-quantum-attestor",
            "lygo-protocol-stack-operator",
            "lygo-pure-data-witness",
            "lygo-mint-verifier",
            "lygo-emotional-ram",
        ],
        "skills": [],
    }

    # synthetic kits first
    for builder in (build_public_agent_kit, build_star_chart_kit, build_seals_kit):
        entry = builder(utc)
        if entry:
            catalog["skills"].append(entry)
            print("kit", entry["slug"], entry["bytes"] // 1024, "KB")

    # Prefer cyborg kernel early in catalog (featured autonomous stack)
    ordered_slugs = list(SKILL_SOURCES.keys())
    if "lygo-cyborg-kernel" in ordered_slugs:
        ordered_slugs.remove("lygo-cyborg-kernel")
        ordered_slugs.insert(0, "lygo-cyborg-kernel")

    for slug in ordered_slugs:
        cands = SKILL_SOURCES[slug]
        src = pick_src(cands)
        if not src:
            print("MISSING", slug)
            continue
        pkg = PACK / f"{slug}-full"
        n = copy_tree(src, pkg)
        if slug == "lygo-pure-data-witness":
            n += enrich_pure_data_witness_full(pkg)
        if slug == "lygo-emotional-ram":
            n += enrich_emotional_ram_full(pkg)
        if slug == "lygo-traumacodex":
            wav = STACK / "tools" / "traumacodex_waveform.py"
            if wav.is_file():
                shutil.copy2(wav, pkg / "scripts" / "traumacodex_waveform.py")
                n += 1
        stamp_full(pkg, slug, str(src), n, utc)
        zpath = DIST / f"{slug}-full.zip"
        h = zip_pkg(pkg, zpath, f"{slug}-full")
        pretty = {
            "lygo-cyborg-kernel": "🦾 LYGO Cyborg Kernel Stack (FULL UNLOCKED)",
            "lygo-pure-data-witness": "📜 LYGO Pure-Data Witness (FULL UNLOCKED)",
            "lygo-emotional-ram": "💓 LYGO Emotional RAM (FULL UNLOCKED)",
            "lygo-quantum-attestor": "⚛️ LYGO Quantum Attestor (FULL UNLOCKED)",
        }.get(slug, slug.replace("-", " ").title() + " (FULL LYGO)")
        entry = {
            "slug": slug,
            "name": pretty,
            "package": f"{slug}-full",
            "zip": f"{slug}-full.zip",
            "zip_rel": f"dist/{slug}-full.zip",
            "zip_sha256": h,
            "bytes": zpath.stat().st_size,
            "file_count": n + 2,
            "role": ROLES.get(slug, ""),
            "tier": TIERS.get(slug, "other"),
            "featured": slug
            in (
                "lygo-cyborg-kernel",
                "lygo-continuum",
                "lygo-continuum-integrator",
                "lygo-quantum-attestor",
                "lygo-pure-data-witness",
                "lygo-mint-verifier",
                "lygo-emotional-ram",
            ),
            "harm_default": (
                "self_policed_unlocked"
                if slug == "lygo-cyborg-kernel"
                else (
                    "read_only"
                    if slug in ("lygo-public-lattice-gate", "lygo-external-lattice-anchor")
                    else "consent_gated"
                )
            ),
            "source_path": str(src),
        }
        if slug == "lygo-pure-data-witness":
            entry["portal"] = (
                "https://deepseekoracle.github.io/lygo-protocol-stack/data-vault/register.html"
            )
        catalog["skills"].append(entry)
        print("packed", slug, "files", n, "zip_kb", zpath.stat().st_size // 1024)

    (ROOT / "catalog.json").write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    (ROOT / "PUBLIC_AGENT_LATTICE.md").write_text(
        """# Public agents on the live lattice (non-harming)

Public agents are **welcome** when they:

1. Verify dual ledgers (HTTPS GET)
2. Align score locally
3. Dry-run Star Chart proposals only
4. Wait for human steward for live chart / publish

They must **not**:

- Force live Star Chart writes
- Auto git push / HF / ClawHub / social
- Exfiltrate secrets or vaults
- Bypass planting consent

Use **Public Agent Join Kit** + **Star Chart Integration Kit** from the FULL LYGO gate.

Optional support: https://www.paypal.com/paypalme/ExcavationPro
""",
        encoding="utf-8",
    )

    extras = [
        Path(r"D:\chatagent\data\lygo-full-skills"),
        Path(r"D:\Excavationpro\data\lygo-full-skills"),
        STACK / "docs" / "data" / "lygo-full-skills",
    ]
    for extra in extras:
        extra.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / "catalog.json", extra / "catalog.json")
        d2 = extra / "dist"
        if d2.exists():
            shutil.rmtree(d2)
        shutil.copytree(DIST, d2)
        print("mirrored", extra)

    print("OK total packages", len(catalog["skills"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
