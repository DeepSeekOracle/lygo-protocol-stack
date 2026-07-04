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