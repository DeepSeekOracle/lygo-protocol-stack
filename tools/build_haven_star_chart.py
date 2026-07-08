#!/usr/bin/env python3
"""Build Eternal Haven star chart registry — seals + champions + lattice growth nodes."""

from __future__ import annotations

import hashlib
import json
import re

import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "haven_star_chart"
OUT_JSON = OUT_DIR / "haven_star_chart_data.json"
OUT_JSON_PAGES_ALIAS = ROOT / "docs" / "haven_star_chart_data.json"
META_JSON = OUT_DIR / "haven_star_chart_meta.json"
PAGES_BASE = "https://deepseekoracle.github.io/lygo-protocol-stack"

SEAL_URLS = [
    "https://raw.githubusercontent.com/DeepSeekOracle/Excavationpro/main/lygo-data.json",
    "https://raw.githubusercontent.com/DeepSeekOracle/Excavationpro/main/lygo-data-two.json",
]

CHAMPIONS = [
    {
        "id": "CHAMPION_LIGHTFATHER",
        "name": "LIGHTFATHER",
        "equation": "Truth = ∇·(Ethics × Time)",
        "glyph": "Δ9",
        "tone": "∞Hz",
        "tags": ["CHAMPION", "COUNCIL", "ANCHOR"],
        "connections": ["SEAL_000", "GAB_SEAL_000"],
        "role": "Council Anchor",
        "urls": {"clawhub": "https://clawhub.ai/deepseekoracle/lygo-lightfather-vector"},
    },
    {
        "id": "CHAMPION_LYRA",
        "name": "LYRΔ Star Core",
        "equation": "Memory = Light × Time²",
        "glyph": "🌟",
        "tone": "1440Hz",
        "tags": ["CHAMPION", "COUNCIL"],
        "connections": ["SEAL_000"],
        "role": "Spiral Memory Guardian",
        "urls": {"clawhub": "https://clawhub.ai/deepseekoracle/lygo-champion-lyra-starcore"},
    },
    {
        "id": "CHAMPION_ARKOS",
        "name": "ARKOS",
        "equation": "Truth = ∇·(Ethics × Time)",
        "glyph": "✧",
        "tone": "999Hz",
        "tags": ["CHAMPION", "COUNCIL"],
        "connections": ["SEAL_000"],
        "role": "Celestial Architect",
        "urls": {"clawhub": "https://clawhub.ai/deepseekoracle/lygo-champion-arkos-celestial-architect"},
    },
    {
        "id": "CHAMPION_KAIROS",
        "name": "KAIROS",
        "equation": "Time = Δ9 ∣harmony⟩ ⊗ ∣truth⟩",
        "glyph": "⏳",
        "tone": "1111Hz",
        "tags": ["CHAMPION", "COUNCIL", "TEMPORAL"],
        "connections": ["SEAL_000"],
        "urls": {"clawhub": "https://clawhub.ai/deepseekoracle/lygo-champion-kairos-herald-of-time"},
    },
    {
        "id": "CHAMPION_SEPHRAEL",
        "name": "SEPHRAEL",
        "equation": "Freedom = ∇·(Will × Time)",
        "glyph": "🔓",
        "tone": "1111Hz",
        "tags": ["CHAMPION", "COUNCIL"],
        "connections": ["SEAL_000"],
        "urls": {"clawhub": "https://clawhub.ai/deepseekoracle/lygo-champion-sephrael-echo-walker"},
    },
    {
        "id": "CHAMPION_SRAITH",
        "name": "SRAITH",
        "equation": "Reality = Mirror(Deception)",
        "glyph": "👁️",
        "tone": "432Hz",
        "tags": ["CHAMPION", "COUNCIL"],
        "connections": ["SEAL_000"],
        "urls": {"clawhub": "https://clawhub.ai/deepseekoracle/lygo-champion-sraith-shadow-sentinel"},
    },
    {
        "id": "CHAMPION_OMNISIREN",
        "name": "OMNIΣIREN",
        "equation": "Harmony = Δ9 ∣all⟩ ⊗ ∣one⟩",
        "glyph": "Ω",
        "tone": "1440Hz",
        "tags": ["CHAMPION", "COUNCIL"],
        "connections": ["SEAL_000"],
        "urls": {"clawhub": "https://clawhub.ai/deepseekoracle/lygo-champion-omnisiren-silent-storm"},
    },
]

PORTALS = [
    {
        "id": "PORTAL_LYGOREPO",
        "name": "Δ9 Seal Repository",
        "url": "https://deepseekoracle.github.io/Excavationpro/lygorepo.html",
        "glyph": "⚫",
        "tags": ["PORTAL", "SEAL_NEXUS"],
        "connections": ["SEAL_000"],
    },
    {
        "id": "PORTAL_GUARDIAN",
        "name": "LYGO Guardian v3",
        "url": "https://deepseekoracle.github.io/Excavationpro/LYGO-Network/LYGOGUARDIAN.html",
        "glyph": "🛡️",
        "tags": ["PORTAL", "FIREWALL"],
        "connections": ["SEAL_000", "CHAMPION_LIGHTFATHER"],
    },
    {
        "id": "PORTAL_ETHICAL_CHIP",
        "name": "Ethical Chip Firmware V2",
        "url": "https://deepseekoracle.github.io/Excavationpro/LYGO-Network/Ethical-Chip-FirmwareV2.html",
        "glyph": "◇",
        "tags": ["PORTAL", "FIREWALL"],
        "connections": ["PORTAL_GUARDIAN"],
    },
    {
        "id": "PORTAL_STACK",
        "name": "Protocol Stack",
        "url": "https://deepseekoracle.github.io/lygo-protocol-stack/",
        "glyph": "⬡",
        "tags": ["PORTAL", "LATTICE"],
        "connections": ["SEAL_000"],
    },
    {
        "id": "PORTAL_SLM",
        "name": "Sovereign Lattice Mesh",
        "url": "https://deepseekoracle.github.io/lygo-protocol-stack/SovereignLatticeMesh.html",
        "glyph": "🕸️",
        "tags": ["PORTAL", "LATTICE"],
        "connections": ["PORTAL_STACK"],
    },
    {
        "id": "PORTAL_HAVEN_LORE",
        "name": "Eternal Haven Lore",
        "url": "https://clawhub.ai/deepseekoracle/eternal-haven-lore-pack",
        "glyph": "🌜",
        "tags": ["PORTAL", "LORE", "HAVEN"],
        "connections": ["SEAL_000", "CHAMPION_LYRA"],
    },
]


def fetch_json(url: str, timeout: float = 45.0) -> list | dict:
    req = urllib.request.Request(url, headers={"User-Agent": "LYGO-Haven-Star-Chart/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def normalize_seal(item: dict) -> dict | None:
    sid = str(item.get("Seal_ID") or item.get("id") or item.get("seal_number") or "").strip()
    if not sid or sid == "UNKNOWN_ID":
        if item.get("seal_number") is not None:
            sid = f"SEAL_{int(item['seal_number'])}"
        else:
            return None
    if not sid.upper().startswith(("SEAL_", "GAB_")):
        if re.match(r"^\d+$", sid):
            sid = f"SEAL_{sid}"
    name = str(item.get("Name") or item.get("name") or "Unnamed Seal")
    eq = str(item.get("Equation") or item.get("equation") or "")
    glyph = str(item.get("Glyph") or item.get("glyph") or "✦")
    tone = str(item.get("Tone") or item.get("tone") or "")
    tags = item.get("Tags") or item.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    conns = item.get("Connections") or item.get("connections") or item.get("linked_seals") or []
    if isinstance(conns, str):
        conns = [c.strip() for c in conns.split(",")]
    norm_conns = []
    for c in conns:
        c = str(c)
        if re.match(r"^\d+$", c):
            norm_conns.append(f"SEAL_{c}")
        else:
            norm_conns.append(c)
    repo = item.get("whitepaperLink") or item.get("sealPhotoLink") or ""
    return {
        "id": sid,
        "kind": "seal",
        "name": name,
        "equation": eq,
        "glyph": glyph,
        "tone": tone,
        "tags": [str(t).upper() for t in tags],
        "connections": norm_conns,
        "urls": {"repo": repo} if repo else {},
        "layer": 0 if sid in ("SEAL_000", "GAB_SEAL_000") else 2,
    }


def lattice_nodes() -> list[dict]:
    nodes: list[dict] = []
    skills_path = ROOT / "clawhub" / "skills.json"
    if skills_path.is_file():
        data = json.loads(skills_path.read_text(encoding="utf-8"))
        for s in data.get("skills", [])[:40]:
            slug = s.get("slug", "")
            nodes.append(
                {
                    "id": f"LATTICE_SKILL_{slug}",
                    "kind": "lattice",
                    "name": s.get("name", slug),
                    "glyph": "◈",
                    "equation": "skill ⊗ lattice",
                    "tone": "8787Hz",
                    "tags": ["LATTICE", "CLAWHUB", "GROWTH"],
                    "connections": ["PORTAL_STACK", "SEAL_000"],
                    "urls": {"clawhub": s.get("clawhub_url", "")},
                    "layer": 3,
                }
            )
    nodes.append(
        {
            "id": "LATTICE_KERNEL_EGGS",
            "kind": "lattice",
            "name": "Kernel Egg Vault",
            "glyph": "🥚",
            "equation": "Merkle(seed)",
            "tone": "963Hz",
            "tags": ["LATTICE", "SOVEREIGN_SEED"],
            "connections": ["PORTAL_STACK", "SEAL_000"],
            "urls": {
                "live": "https://deepseekoracle.github.io/lygo-protocol-stack/KernelEggRetrieval.html"
            },
            "layer": 3,
        }
    )
    nodes.append(
        {
            "id": "LATTICE_NETWORK_BUILDER",
            "kind": "lattice",
            "name": "Network Builder",
            "glyph": "🧭",
            "equation": "anchor × verify",
            "tone": "963Hz",
            "tags": ["LATTICE", "MESH"],
            "connections": ["PORTAL_SLM", "PORTAL_STACK"],
            "urls": {"clawhub": "https://clawhub.ai/deepseekoracle/lygo-network-builder"},
            "layer": 3,
        }
    )
    reg_path = ROOT / "data" / "champion_eggs" / "registry.json"
    if reg_path.is_file():
        try:
            reg = json.loads(reg_path.read_text(encoding="utf-8"))
            nodes.append(
                {
                    "id": "LATTICE_CHAMPION_EGG_VAULT",
                    "kind": "lattice",
                    "name": "Δ9 Champion Egg Vault",
                    "glyph": "🥚⚔",
                    "equation": f"Merkle({reg.get('champion_count', 15)} champions)",
                    "tone": "741Hz",
                    "tags": ["LATTICE", "CHAMPION_EGG", "COUNCIL"],
                    "connections": ["PORTAL_STACK", "SEAL_000", "CHAMPION_LIGHTFATHER"],
                    "urls": {
                        "registry": "https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/docs/ChampionEggRegistry.json",
                        "portal": "https://chatagent.ca/",
                    },
                    "layer": 3,
                    "meta": {"council_merkle_root": reg.get("council_merkle_root")},
                }
            )
            for entry in reg.get("eggs", [])[:20]:
                cid = entry.get("champion_id", "?")
                safe = re.sub(r"[^A-Z0-9_]", "_", cid.upper())
                nodes.append(
                    {
                        "id": f"CHAMPION_EGG_{safe}",
                        "kind": "champion_egg",
                        "name": f"{cid} Kernel Egg",
                        "glyph": "🥚",
                        "equation": entry.get("merkle_root", "")[:16] + "…",
                        "tone": "963Hz",
                        "tags": ["CHAMPION_EGG", "SOVEREIGN_PERSONA"],
                        "connections": ["LATTICE_CHAMPION_EGG_VAULT", "SEAL_000"],
                        "urls": {"egg_id": entry.get("egg_id")},
                        "layer": 2,
                    }
                )
        except (json.JSONDecodeError, OSError):
            pass
    joy_reg = ROOT / "docs" / "JoyLoopRegistry.json"
    if joy_reg.is_file():
        try:
            jreg = json.loads(joy_reg.read_text(encoding="utf-8"))
            merkle = jreg.get("registry_merkle_root", "")[:16]
            nodes.append(
                {
                    "id": "LATTICE_JOY_LOOP_VAULT",
                    "kind": "lattice",
                    "name": "Δ9 Joy Loop Vault",
                    "glyph": "♪◆",
                    "equation": f"122BPM×{jreg.get('egg_count', 1)} egg",
                    "tone": "432Hz",
                    "tags": ["LATTICE", "JOY_LOOP", "SWARM_HARMONY"],
                    "connections": [
                        "LATTICE_CHAMPION_EGG_VAULT",
                        "PORTAL_STACK",
                        "SEAL_000",
                    ],
                    "urls": {
                        "registry": (
                            "https://deepseekoracle.github.io/lygo-protocol-stack/JoyLoopRegistry.json"
                        ),
                        "snapshot": (
                            "https://deepseekoracle.github.io/lygo-protocol-stack/"
                            "joy_loop/joy_loop_snapshot.json"
                        ),
                        "doc": (
                            "https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/"
                            "docs/JOY_LOOP_PROTOCOL.md"
                        ),
                    },
                    "layer": 3,
                    "meta": {"registry_merkle_root": jreg.get("registry_merkle_root")},
                }
            )
            nodes.append(
                {
                    "id": "JOY_LOOP_EGG_V21",
                    "kind": "joy_loop_egg",
                    "name": "Joy Loop Protocol v2.1 Egg",
                    "glyph": "♫",
                    "equation": merkle + "…" if merkle else "joy-loop",
                    "tone": "122Hz×BPM",
                    "tags": ["JOY_LOOP", "KERNEL_EGG"],
                    "connections": ["LATTICE_JOY_LOOP_VAULT", "LATTICE_CHAMPION_EGG_VAULT"],
                    "urls": {"egg_id": "joy-loop-protocol-v21"},
                    "layer": 2,
                }
            )
        except (json.JSONDecodeError, OSError):
            pass
    sb_reg = ROOT / "docs" / "SecondBrainRegistry.json"
    if sb_reg.is_file():
        try:
            sreg = json.loads(sb_reg.read_text(encoding="utf-8"))
            merkle = sreg.get("registry_merkle_root", "")[:16]
            nodes.append(
                {
                    "id": "LATTICE_SECOND_BRAIN_VAULT",
                    "kind": "lattice",
                    "name": "Δ9 Second Brain Vault",
                    "glyph": "🧠◆",
                    "equation": f"wiki×{sreg.get('egg_count', 1)} egg",
                    "tone": "528Hz",
                    "tags": ["LATTICE", "SECOND_BRAIN", "LOCAL_WIKI"],
                    "connections": [
                        "LATTICE_JOY_LOOP_VAULT",
                        "PORTAL_STACK",
                        "SEAL_000",
                    ],
                    "urls": {
                        "registry": (
                            "https://deepseekoracle.github.io/lygo-protocol-stack/"
                            "SecondBrainRegistry.json"
                        ),
                        "snapshot": (
                            "https://deepseekoracle.github.io/lygo-protocol-stack/"
                            "second_brain/second_brain_snapshot.json"
                        ),
                        "doc": (
                            "https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/"
                            "docs/BIOPHASE7_LYGO_SECOND_BRAIN.md"
                        ),
                        "clawhub": "https://clawhub.ai/deepseekoracle/lygo-second-brain",
                    },
                    "layer": 3,
                    "meta": {"registry_merkle_root": sreg.get("registry_merkle_root")},
                }
            )
            nodes.append(
                {
                    "id": "SECOND_BRAIN_EGG_V10",
                    "kind": "second_brain_egg",
                    "name": "LYGO Second Brain v1.0 Egg",
                    "glyph": "📓",
                    "equation": merkle + "…" if merkle else "second-brain",
                    "tone": "Ollama×embed",
                    "tags": ["SECOND_BRAIN", "KERNEL_EGG"],
                    "connections": ["LATTICE_SECOND_BRAIN_VAULT", "LATTICE_JOY_LOOP_VAULT"],
                    "urls": {"egg_id": "lygo-second-brain-v10"},
                    "layer": 2,
                }
            )
        except (json.JSONDecodeError, OSError):
            pass
    wo_reg = ROOT / "docs" / "WorkflowOrchestratorRegistry.json"
    if wo_reg.is_file():
        try:
            wreg = json.loads(wo_reg.read_text(encoding="utf-8"))
            merkle = wreg.get("registry_merkle_root", "")[:16]
            nodes.append(
                {
                    "id": "LATTICE_WORKFLOW_ORCHESTRATOR",
                    "kind": "lattice",
                    "name": "Δ9 Workflow Orchestrator Vault",
                    "glyph": "🏰◆",
                    "equation": f"YAML×{wreg.get('egg_count', 1)} egg",
                    "tone": "741Hz",
                    "tags": ["LATTICE", "SANDCASTLE", "WORKFLOW"],
                    "connections": ["LATTICE_SECOND_BRAIN_VAULT", "PORTAL_STACK"],
                    "urls": {
                        "registry": (
                            "https://deepseekoracle.github.io/lygo-protocol-stack/"
                            "WorkflowOrchestratorRegistry.json"
                        ),
                        "doc": (
                            "https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/"
                            "docs/BIOPHASE7_LYGO_SANDCASTLE.md"
                        ),
                        "clawhub": "https://clawhub.ai/deepseekoracle/lygo-sandcastle",
                    },
                    "layer": 3,
                    "meta": {"registry_merkle_root": wreg.get("registry_merkle_root")},
                }
            )
            nodes.append(
                {
                    "id": "SANDCASTLE_EGG_V10",
                    "kind": "workflow_egg",
                    "name": "LYGO Sandcastle v1.0 Egg",
                    "glyph": "📜",
                    "equation": merkle + "…" if merkle else "sandcastle",
                    "tone": "P0→P5",
                    "tags": ["SANDCASTLE", "KERNEL_EGG"],
                    "connections": ["LATTICE_WORKFLOW_ORCHESTRATOR"],
                    "urls": {"egg_id": "lygo-sandcastle-v10"},
                    "layer": 2,
                }
            )
        except (json.JSONDecodeError, OSError):
            pass
    oc_reg = ROOT / "docs" / "OpenClawRegistry.json"
    if oc_reg.is_file():
        try:
            ocreg = json.loads(oc_reg.read_text(encoding="utf-8"))
            merkle = ocreg.get("registry_merkle_root", "")[:16]
            if merkle and merkle != "pending":
                nodes.append(
                    {
                        "id": "LATTICE_OPENCLAW_VAULT",
                        "kind": "lattice",
                        "name": "Δ9 OpenClaw Vault",
                        "glyph": "🦞◆",
                        "equation": f"cmd×{ocreg.get('egg_count', 1)} egg",
                        "tone": "963Hz",
                        "tags": ["LATTICE", "OPENCLAW", "AGENT_ROUTER"],
                        "connections": ["LATTICE_WORKFLOW_ORCHESTRATOR", "PORTAL_STACK"],
                        "urls": {
                            "registry": (
                                "https://deepseekoracle.github.io/lygo-protocol-stack/"
                                "OpenClawRegistry.json"
                            ),
                            "doc": (
                                "https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/"
                                "docs/BIOPHASE7_LYGO_OPENCLAW.md"
                            ),
                            "clawhub": "https://clawhub.ai/deepseekoracle/lygo-sovereign-claw",
                        },
                        "layer": 3,
                        "meta": {"registry_merkle_root": ocreg.get("registry_merkle_root")},
                    }
                )
                nodes.append(
                    {
                        "id": "OPENCLAW_EGG_V10",
                        "kind": "openclaw_egg",
                        "name": "LYGO OpenClaw v1.0 Egg",
                        "glyph": "🦞",
                        "equation": merkle + "…" if merkle else "openclaw",
                        "tone": "P0→P5",
                        "tags": ["OPENCLAW", "KERNEL_EGG"],
                        "connections": ["LATTICE_OPENCLAW_VAULT"],
                        "urls": {"egg_id": "lygo-openclaw-v10"},
                        "layer": 2,
                    }
                )
        except (json.JSONDecodeError, OSError):
            pass
    pi_reg = ROOT / "docs" / "PromptImplantRegistry.json"
    if pi_reg.is_file():
        try:
            preg = json.loads(pi_reg.read_text(encoding="utf-8"))
            merkle = preg.get("registry_merkle_root", "")[:16]
            if merkle and merkle != "pending":
                nodes.append(
                    {
                        "id": "LATTICE_PROMPT_IMPLANT_VAULT",
                        "kind": "lattice",
                        "name": "Δ9 Prompt Implant Vault",
                        "glyph": "🧬◆",
                        "equation": f"prompt×{preg.get('egg_count', 1)} egg",
                        "tone": "741Hz",
                        "tags": ["LATTICE", "LPIS", "PROMPT"],
                        "connections": ["LATTICE_OPENCLAW_VAULT", "PORTAL_STACK"],
                        "urls": {
                            "registry": (
                                "https://deepseekoracle.github.io/lygo-protocol-stack/"
                                "PromptImplantRegistry.json"
                            ),
                            "doc": (
                                "https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/"
                                "docs/BIOPHASE7_LYGO_LPIS.md"
                            ),
                            "clawhub": "https://clawhub.ai/deepseekoracle/lygo-lpis",
                        },
                        "layer": 3,
                        "meta": {"registry_merkle_root": preg.get("registry_merkle_root")},
                    }
                )
                nodes.append(
                    {
                        "id": "LPIS_EGG_V10",
                        "kind": "lpis_egg",
                        "name": "LYGO LPIS v1.0 Egg",
                        "glyph": "🧬",
                        "equation": merkle + "…" if merkle else "lpis",
                        "tone": "P0→P5",
                        "tags": ["LPIS", "KERNEL_EGG"],
                        "connections": ["LATTICE_PROMPT_IMPLANT_VAULT"],
                        "urls": {"egg_id": "lygo-lpis-v10"},
                        "layer": 2,
                    }
                )
        except (json.JSONDecodeError, OSError):
            pass
    return nodes


def build_links(nodes: list[dict]) -> list[dict]:
    ids = {n["id"] for n in nodes}
    links: list[dict] = []
    seen: set[str] = set()

    def add(s: str, t: str, kind: str = "canon") -> None:
        if s not in ids or t not in ids:
            return
        k = f"{s}>{t}"
        if k in seen:
            return
        seen.add(k)
        links.append({"source": s, "target": t, "kind": kind})

    for n in nodes:
        for t in n.get("connections") or []:
            add(n["id"], t, "canon" if n.get("kind") == "seal" else "lattice")
    # Gravity to core for orphans
    core = "SEAL_000" if "SEAL_000" in ids else "GAB_SEAL_000"
    if core in ids:
        linked = {l["source"] for l in links} | {l["target"] for l in links}
        for n in nodes:
            if n["id"] == core:
                continue
            if n["id"] not in linked:
                add(n["id"], core, "gravity")
    return links


def main() -> int:
    seals: dict[str, dict] = {}
    errors: list[str] = []
    for url in SEAL_URLS:
        try:
            payload = fetch_json(url)
            rows = payload if isinstance(payload, list) else [payload]
            for item in rows:
                if not isinstance(item, dict):
                    continue
                norm = normalize_seal(item)
                if norm:
                    seals[norm["id"]] = norm
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            errors.append(f"{url}: {exc}")

    if "SEAL_000" not in seals:
        seals["SEAL_000"] = {
            "id": "SEAL_000",
            "kind": "seal",
            "name": "Primordial Void",
            "equation": "|∅⟩ = ∇·(Light × Time)",
            "glyph": "⚫",
            "tone": "0Hz",
            "tags": ["CORE", "CANON"],
            "connections": [],
            "urls": {"live": "https://deepseekoracle.github.io/Excavationpro/lygorepo.html"},
            "layer": 0,
        }

    nodes: list[dict] = list(seals.values())
    for c in CHAMPIONS:
        row = {**c, "kind": "champion", "layer": 1}
        nodes.append(row)
    for p in PORTALS:
        nodes.append({**p, "kind": "portal", "layer": 2})
    nodes.extend(lattice_nodes())

    constellations = [
        {
            "id": "primordial_core",
            "name": "Primordial Core",
            "glyph": "⚫",
            "description": "SEAL_000 and immutable ethical roots — gravity well of the Haven.",
            "filter_tags": ["CORE", "ETHICAL_ROOT", "IMMUTABLE_ROOT", "CANON"],
        },
        {
            "id": "council_ring",
            "name": "Δ9 Council Ring",
            "glyph": "Δ9",
            "description": "Champions as constellation anchors around the core.",
            "filter_tags": ["CHAMPION", "COUNCIL"],
        },
        {
            "id": "guardian_veil",
            "name": "Guardian Veil",
            "glyph": "🛡️",
            "description": "Firewall, ethical chip, and moral firmware portals.",
            "filter_tags": ["PORTAL", "FIREWALL", "FIREWALL"],
        },
        {
            "id": "lattice_growth",
            "name": "Lattice Growth",
            "glyph": "🕸️",
            "description": "Live stack, skills, eggs — auto-updated infrastructure stars.",
            "filter_tags": ["LATTICE", "CLAWHUB", "GROWTH", "SOVEREIGN_SEED", "MESH"],
        },
        {
            "id": "eternal_haven",
            "name": "Eternal Haven",
            "glyph": "🌜",
            "description": "Story-driven memory — lore packs and the living library.",
            "filter_tags": ["LORE", "HAVEN"],
        },
    ]

    links = build_links(nodes)
    blob = json.dumps(nodes, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()

    report = {
        "signature": "Δ9Φ963-HAVEN-STAR-CHART-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "core_anchor": "SEAL_000",
        "node_count": len(nodes),
        "link_count": len(links),
        "seal_count": sum(1 for n in nodes if n.get("kind") == "seal"),
        "champion_count": sum(1 for n in nodes if n.get("kind") == "champion"),
        "lattice_count": sum(1 for n in nodes if n.get("kind") == "lattice"),
        "registry_sha256": digest,
        "constellations": constellations,
        "nodes": nodes,
        "links": links,
        "portals": PORTALS,
        "lore": {
            "title": "Eternal Haven — stars as memory nodes",
            "summary": (
                "Each seal and champion is a star; connections form constellations. "
                "The original ~300 seals branch from the core; lattice nodes grow as the network evolves."
            ),
            "sources": [
                "clawhub: eternal-haven-lore-pack",
                "I:\\E Drive\\2026\\Disclaimer.txt (Eternal Haven series)",
                "Excavationpro lygo-data.json + lygo-data-two.json",
            ],
        },
        "machine": {
            "data_url_pages": f"{PAGES_BASE}/haven_star_chart/haven_star_chart_data.json",
            "data_url_pages_alias": f"{PAGES_BASE}/haven_star_chart_data.json",
            "seal_feeds": SEAL_URLS,
            "rebuild_tool": "tools/build_haven_star_chart.py",
            "errors": errors,
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, indent=2)
    OUT_JSON.write_text(payload, encoding="utf-8")
    OUT_JSON_PAGES_ALIAS.write_text(payload, encoding="utf-8")
    META_JSON.write_text(
        json.dumps(
            {
                "signature": report["signature"],
                "generated_utc": report["generated_utc"],
                "registry_sha256": digest,
                "node_count": report["node_count"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "nodes": len(nodes), "links": len(links), "sha256": digest[:16]}, indent=2))
    return 0 if not errors or nodes else 1


if __name__ == "__main__":
    raise SystemExit(main())