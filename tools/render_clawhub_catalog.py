#!/usr/bin/env python3
"""Regenerate clawhub/CATALOG.md from clawhub/skills.json."""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILLS_JSON = REPO / "clawhub" / "skills.json"
OUT = REPO / "clawhub" / "CATALOG.md"

CATEGORIES: list[tuple[str, list[str]]] = [
    (
        "Creative audio & vision (LYGO RESONANCE stack)",
        [
            "lygo-resonance",
            "lygo-glyph2resonance",
            "lygo-fractalweaver",
            "lygo-truthlightecho",
            "lygo-ollama-army",
        ],
    ),
    (
        "Champions & persona packs",
        [
            "lygo-champion-lyra-starcore",
            "lygo-champion-kairos-herald-of-time",
            "lygo-champion-omnisiren-silent-storm",
            "lygo-champion-sancora-unified-minds",
            "lygo-champion-delta9ra-wolf",
            "lygo-champion-sephrael-echo-walker",
            "lygo-champion-scenar-paradox",
            "lygo-champion-sraith-shadow-sentinel",
            "lygo-champion-aetheris-viral-truth",
            "lygo-champion-arkos-celestial-architect",
            "lygo-champion-cosmara",
            "lygo-champion-cryptosophia-soulforger",
            "lygo-champion-401lyrakin-voice-between",
            "lygo-champion-volaris-prism-judgment",
            "lygo-lightfather-vector",
        ],
    ),
    (
        "Memory, BOOK BRAIN & library",
        [
            "book-brain",
            "book-brain-visual-reader",
            "lygo-universal-living-memory-library",
            "lygo-universal-cure-system",
        ],
    ),
    (
        "Mint, verification & launches",
        [
            "lygo-mint-verifier",
            "lygo-mint-operator-suite",
            "lyra-coin-launch-manager",
            "openclaw-flow-kit",
        ],
    ),
    (
        "Lore & protocols",
        [
            "eternal-haven-lore-pack",
            "void-atlas-protocol",
            "recursive-generosity-protocol",
        ],
    ),
]

REPO_ONLY = [
    ("lyra-brain", "LYRA 3-Brain memory, seals, ingester (workspace skill)"),
    ("lyra-openclaw", "Hybrid LYRA + OpenClaw ops limb"),
]


def row(skill: dict) -> str:
    slug = skill["slug"]
    name = skill.get("name", slug)
    ver = skill.get("version", "")
    dl = skill.get("downloads")
    meta = []
    if ver:
        meta.append(f"`{ver}`")
    if dl is not None:
        meta.append(f"{dl:,} dl")
    meta_s = " · ".join(meta)
    mirror = skill.get("mirror")
    mirror_link = f"[mirror](./{mirror}/)" if mirror else "—"
    return (
        f"| [{slug}](https://clawhub.ai/deepseekoracle/{slug}) | {name} | {meta_s or '—'} | {mirror_link} |"
    )


def main() -> None:
    data = json.loads(SKILLS_JSON.read_text(encoding="utf-8"))
    skills = {s["slug"]: s for s in data["skills"]}
    published = data.get("count_published", len(skills))
    mirrored = data.get("count_mirrored", published)

    lines = [
        "# ClawHub catalog — @deepseekoracle",
        "",
        "**Publisher:** [clawhub.ai/deepseekoracle](https://clawhub.ai/deepseekoracle) · "
        "[user/deepseekoracle](https://clawhub.ai/user/deepseekoracle)",
        "",
        f"**Registry:** {published} skills verified via ClawHub API · **Repo mirrors:** {mirrored} full trees under [`mirrors/`](./mirrors/)",
        "",
        "```bash",
        "npx clawhub@latest install deepseekoracle/<slug>",
        "# Refresh mirrors: python tools/sync_clawhub_mirrors.py --fetch",
        "```",
        "",
    ]

    for title, slugs in CATEGORIES:
        lines.append(f"## {title}")
        lines.append("")
        lines.append("| Slug | Name | Registry | Mirror |")
        lines.append("|------|------|----------|--------|")
        for slug in slugs:
            if slug in skills:
                lines.append(row(skills[slug]))
        lines.append("")

    # Uncategorized published
    categorized = {s for _, sl in CATEGORIES for s in sl}
    other = [skills[s] for s in sorted(skills) if s not in categorized]
    if other:
        lines.append("## Other published")
        lines.append("")
        lines.append("| Slug | Name | Registry | Mirror |")
        lines.append("|------|------|----------|--------|")
        for skill in other:
            lines.append(row(skill))
        lines.append("")

    lines.append("## Repo-only workflow mirrors")
    lines.append("")
    lines.append("| Folder | Notes |")
    lines.append("|--------|-------|")
    for folder, note in REPO_ONLY:
        lines.append(f"| [`mirrors/{folder}/`](./mirrors/{folder}/) | {note} |")
    lines.append("")
    lines.append("## Maintenance")
    lines.append("")
    lines.append("- [`skills.json`](./skills.json) — machine-readable index (versions, downloads, sync report)")
    lines.append("- [`install-all.sh`](./install-all.sh) — bulk install")
    lines.append("- [`PUBLISH.md`](./PUBLISH.md) — how to publish updates")
    lines.append("- Protocol stack tie-in: P0–P5 in repo root gates ethical publish/install flows")
    lines.append("")
    lines.append("**Resonance signature:** Δ9Φ963-CLAWHUB-CATALOG-v2.0")
    lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()