"""Curated kernel / protocol artifacts for permaweb eggs (free tier ≤100 KiB each)."""

from __future__ import annotations

import hashlib
from pathlib import Path

SIGNATURE = "Δ9Φ963-KERNEL-EGG-CATALOG-v1"
REPO = Path(__file__).resolve().parents[1]
E_DRIVE = REPO.parent

# egg_id -> list of (label, path relative to repo or absolute)
EGG_SPECS: dict[str, list[tuple[str, Path]]] = {
    "p0-nano-kernel": [
        ("p0_core", REPO / "protocol0_byte_entropy_filter/src/python/lygo_p0.py"),
        ("kernel_bridge", REPO / "stack/kernel_bridge.py"),
        ("p0_golden_sha", REPO / "protocol0_byte_entropy_filter/fixtures/p0_canonical.sha256"),
        ("p0_lyra_kernel", REPO / "protocol0_byte_entropy_filter/src/python/lygo_p0_lyra_kernel.py"),
    ],
    "stack-anchor-hook": [
        ("stack_anchor", REPO / "stack/lygo_stack_anchor.py"),
        ("stack_status", REPO / "docs/STACK_STATUS.md"),
    ],
    "stack-orchestrator-slim": [
        ("lygo_stack_head", REPO / "stack/lygo_stack.py"),
    ],
    "lattice-soa-index": [
        ("lattice_intel", REPO / "docs/LYGO_LATTICE_INTEL_INDEX.json"),
        ("lattice_map", REPO / "docs/LYGO_LATTICE.md"),
        ("link_archive_sources", REPO / "docs/LYGO_PUBLIC_LINK_ARCHIVE.json"),
    ],
    # Excavationpro full song/ISRC restore ledger (DistroKid recovery) — growable
    "excavationpro-music-catalog-v1": [
        ("music_egg_core", REPO / "data/music_catalog/egg_payload/music_egg_core.json"),
        ("music_egg_readme", REPO / "data/music_catalog/egg_payload/README.md"),
        ("restore_gap_summary", REPO / "data/music_catalog/RESTORE_GAP_SUMMARY.md"),
        ("isrcs_unique", REPO / "data/music_catalog/excavationpro_isrcs_unique.txt"),
        ("ledger_sha_note", REPO / "data/music_catalog/music_vault_merkle_root.txt"),
    ],
    # Sovereign CAS vault Merkle + public stream lattice map (slim, plantable)
    "excavationpro-music-vault-v1": [
        ("music_vault_egg_core", REPO / "data/music_catalog/egg_payload/music_vault_egg_core.json"),
        ("vault_merkle_root", REPO / "data/music_catalog/music_vault_merkle_root.txt"),
        ("listen_hub_lattice", REPO / "data/music_catalog/listen_hub_lattice.json"),
        ("music_portal_map", REPO / "clawhub/mirrors/lygo-excavationpro-music-lattice/references/MUSIC_PORTAL.json"),
    ],
    # ClawHub music-lattice skill pin (metadata only — no audio)
    "excavationpro-music-lattice-skill-v1": [
        ("skill_md", REPO / "clawhub/mirrors/lygo-excavationpro-music-lattice/SKILL.md"),
        ("music_portal_json", REPO / "clawhub/mirrors/lygo-excavationpro-music-lattice/references/MUSIC_PORTAL.json"),
        ("lattice_map", REPO / "clawhub/mirrors/lygo-excavationpro-music-lattice/references/LATTICE_MAP.md"),
        ("agent_contract", REPO / "clawhub/mirrors/lygo-excavationpro-music-lattice/references/AGENT_CONTRACT.md"),
    ],
    "firmware-p04-drivers": [
        ("p0_nano_gate", E_DRIVE / "2026/lygo_p0_nano_gate.py"),
        ("updatefeed", E_DRIVE / "2026/updatefeed.json"),
        ("p0_firmware_kernel", E_DRIVE / "2026/LYGO P0 FIRMWARE KERNEL v0.3.py"),
    ],
    "protocol-drivers-p2-p5": [
        ("p2_cognitive", REPO / "protocol2_cognitive_bridge/src/python/lygo_p2.py"),
        ("p3_vortex", REPO / "protocol3_vortex_consensus/src/python/lygo_p3.py"),
        ("p5_harmony", REPO / "protocol5_harmony_node/src/python/lygo_p5.py"),
    ],
    "joy-loop-protocol-v21": [
        ("joy_loop_protocol", REPO / "tools" / "joy_loop_protocol.py"),
        ("joy_loop_doc", REPO / "docs" / "JOY_LOOP_PROTOCOL.md"),
        ("joy_loop_manifest", REPO / "data" / "joy_loop" / "joy_loop_egg_manifest.json"),
    ],
    "lygo-second-brain-v10": [
        ("second_brain_cli", REPO / "tools" / "lygo_second_brain.py"),
        ("second_brain_spec", REPO / "docs" / "BIOPHASE7_LYGO_SECOND_BRAIN.md"),
        ("vault_readme", REPO / "lygo_second_brain" / "README.md"),
        ("ingest_script", REPO / "lygo_second_brain" / "scripts" / "ingest.py"),
        ("embed_index", REPO / "lygo_second_brain" / "scripts" / "embed_index.py"),
        ("second_brain_manifest", REPO / "data" / "second_brain" / "second_brain_egg_manifest.json"),
    ],
    "lygo-sandcastle-v10": [
        ("sandcastle_cli", REPO / "tools" / "lygo_sandcastle.py"),
        ("sandcastle_spec", REPO / "docs" / "BIOPHASE7_LYGO_SANDCASTLE.md"),
        ("sandcastle_readme", REPO / "lygo_sandcastle" / "README.md"),
        ("example_workflow", REPO / "lygo_sandcastle" / "workflows" / "example_sovereign.yaml"),
        ("orchestrator", REPO / "lygo_sandcastle" / "orchestrator.py"),
        ("workflow_egg_manifest", REPO / "data" / "sandcastle" / "workflow_egg_manifest.json"),
    ],
    "lygo-openclaw-v10": [
        ("openclaw_cli", REPO / "tools" / "lygo_openclaw.py"),
        ("openclaw_spec", REPO / "docs" / "BIOPHASE7_LYGO_OPENCLAW.md"),
        ("openclaw_readme", REPO / "lygo_openclaw" / "README.md"),
        ("framework", REPO / "lygo_openclaw" / "framework.py"),
        ("limbs", REPO / "lygo_openclaw" / "limbs.py"),
        ("openclaw_egg_manifest", REPO / "data" / "openclaw" / "openclaw_egg_manifest.json"),
    ],
    "lygo-lpis-v10": [
        ("lpis_cli", REPO / "tools" / "lygo_lpis.py"),
        ("lpis_spec", REPO / "docs" / "BIOPHASE7_LYGO_LPIS.md"),
        ("lpis_readme", REPO / "lygo_lpis" / "README.md"),
        ("framework", REPO / "lygo_lpis" / "framework.py"),
        ("vault", REPO / "lygo_lpis" / "vault.py"),
        ("lpis_egg_manifest", REPO / "data" / "prompt_vault" / "lpis_egg_manifest.json"),
    ],
    "lygo-ops-detector-v1": [
        ("ops_detector_skill", REPO / "clawhub" / "mirrors" / "lygo-ops-detector" / "SKILL.md"),
        ("detector_core", REPO / "clawhub" / "mirrors" / "lygo-ops-detector" / "scripts" / "lygo_ops_detector.py"),
        ("aethon_blueprint", REPO / "clawhub" / "mirrors" / "lygo-ops-detector" / "references" / "AETHON_D9_BLUEPRINT.md"),
        ("security_doc", REPO / "clawhub" / "mirrors" / "lygo-ops-detector" / "references" / "SECURITY.md"),
    ],
    # Universal agent utilities (ClawHub + FULL SkillHub vault)
    "lygo-context-guard-v1": [
        ("context_guard_skill", REPO / "clawhub" / "mirrors" / "lygo-context-guard" / "SKILL.md"),
        ("context_guard_core", REPO / "clawhub" / "mirrors" / "lygo-context-guard" / "scripts" / "context_guard.py"),
        ("security_doc", REPO / "clawhub" / "mirrors" / "lygo-context-guard" / "references" / "SECURITY.md"),
        ("quickstart", REPO / "clawhub" / "mirrors" / "lygo-context-guard" / "examples" / "quickstart.md"),
    ],
    "lygo-skill-gate-v1": [
        ("skill_gate_skill", REPO / "clawhub" / "mirrors" / "lygo-skill-gate" / "SKILL.md"),
        ("skill_gate_core", REPO / "clawhub" / "mirrors" / "lygo-skill-gate" / "scripts" / "skill_gate.py"),
        ("security_doc", REPO / "clawhub" / "mirrors" / "lygo-skill-gate" / "references" / "SECURITY.md"),
        ("quickstart", REPO / "clawhub" / "mirrors" / "lygo-skill-gate" / "examples" / "quickstart.md"),
    ],
}

RETRIEVAL_SOA = {
    "github_repo": "https://github.com/DeepSeekOracle/lygo-protocol-stack",
    "hf_dataset": "https://huggingface.co/datasets/DeepSeekOracle/lygo-protocol-stack",
    "hf_space": "https://huggingface.co/spaces/DeepSeekOracle/LYGO-Resonance-Engine",
    "pages_index": "https://deepseekoracle.github.io/lygo-protocol-stack/",
    "authority_root": str(E_DRIVE),
}


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def merkle_root(hex_hashes: list[str]) -> str:
    if not hex_hashes:
        return hashlib.sha256(b"").hexdigest()
    layer = list(hex_hashes)
    while len(layer) > 1:
        nxt = []
        for i in range(0, len(layer), 2):
            pair = layer[i] + (layer[i + 1] if i + 1 < len(layer) else layer[i])
            nxt.append(hashlib.sha256(pair.encode()).hexdigest())
        layer = nxt
    return layer[0]