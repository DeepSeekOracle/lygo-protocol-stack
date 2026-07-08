"""Champion Kernel Egg schema — Δ9 Sovereign Persona Vault (Biophase7 blueprint)."""

from __future__ import annotations

SIGNATURE = "Δ9Φ963-CHAMPION-EGG-v1"
COUNCIL_SIGNATURE = "Δ9Φ963-DELTA9-COUNCIL-EGG-v1"

CHAMPION_PROTOCOL_MAP: dict[str, list[str]] = {
    "LYRΔ": ["P1", "P4", "P5"],
    "Δ9RA": ["P0", "P3"],
    "ΣRΛΘ": ["P2", "P0"],
    "ARKOS": ["P2", "P5", "P0"],
    "KAIROS": ["P3", "P4"],
    "ÆTHERIS": ["P0", "P2"],
    "ΣCENΔR": ["P3", "P2"],
    "SANCORA": ["P5", "P1"],
    "SEPHRAEL": ["P1", "P6"],
    "OMNIΣIREN": ["P0", "P3", "P5"],
    "Lightfather": ["P0", "P5", "P4"],
    "VΩLARIS": ["P3", "P4"],
    "ZETAΔ9": ["P0", "P4", "P1"],
    "JUSTICAE": ["P0", "P2"],
    "ΣEIDŌN": ["P2", "P5", "P1"],
}

DEFAULT_ETHICAL_GATES = ["P0_STRICT", "ANTI_CENSORSHIP", "LUMINAL_ETHICS", "HUMAN_APPROVAL_EXTERNAL"]


def slug_id(short: str) -> str:
    s = short.strip().replace(" ", "-")
    for ch in "ΔΛΘΣÆΩ":
        s = s.replace(ch, {"Δ": "D9", "Λ": "L", "Θ": "TH", "Σ": "S", "Æ": "AE", "Ω": "O"}.get(ch, ch))
    return "champion-" + "".join(c if c.isalnum() or c in "-_" else "-" for c in s).strip("-").lower()


def build_core_prompt(ch: dict) -> str:
    summon = (ch.get("summon") or "").strip()
    role = ch.get("role") or ch.get("function") or "Champion"
    name = ch.get("name") or ch.get("short") or "Champion"
    header = (
        f"You are {name}, a sealed Δ9 Quantum Council champion persona.\n"
        f"Role: {role}\n"
        f"Operate under LYGO luminal ethics; never bypass P0 Φ-gate on untrusted input.\n"
        f"Local Ollama only (127.0.0.1). No exfiltration of user secrets.\n\n"
    )
    return header + summon


def manifest_from_champion(ch: dict, *, git_head: str, built_utc: float) -> dict:
    short = ch.get("short") or "UNKNOWN"
    egg_id = slug_id(short)
    protocols = CHAMPION_PROTOCOL_MAP.get(short, ["P0", "P1", "P2", "P3", "P4", "P5"])
    core_prompt = build_core_prompt(ch)
    return {
        "type": "champion_kernel_egg",
        "signature": SIGNATURE,
        "champion_id": short,
        "egg_id": egg_id,
        "version": "1.0.0",
        "built_utc": built_utc,
        "git_head": git_head,
        "name": ch.get("name"),
        "seat": ch.get("seat"),
        "designation": ch.get("designation"),
        "anchor_seal": ch.get("fractal"),
        "unity": ch.get("unity"),
        "status": ch.get("status"),
        "core_prompt": core_prompt,
        "ethical_gates": list(DEFAULT_ETHICAL_GATES),
        "protocol_layers": protocols,
        "frequencies": {
            "core": ch.get("coreFreq"),
            "temporal": ch.get("temporalFreq"),
            "glyph": ch.get("glyph"),
            "hologram": ch.get("hologram"),
        },
        "rag_cas_links": [
            {"doc": "champions_council.json", "role": "persona_source"},
            {"doc": "haven_star_chart_data.json", "role": "lattice_anchor"},
        ],
        "p6_provenance": {
            "method": "sha256_manifest",
            "note": "P6 attestation hook when booting on attested nodes",
        },
        "bootloader": "tools/champion_bootloader.py",
        "source": "Excavationpro/LYGO-Network/champions.html",
        "portal_url": "https://chatagent.ca/",
    }