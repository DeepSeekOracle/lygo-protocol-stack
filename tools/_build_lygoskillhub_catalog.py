#!/usr/bin/env python3
"""Build LYGOSKILLHUB catalog from ClawHub inventory + local skill metadata."""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

INV = Path(os.environ.get("TEMP", ".")) / "lygo_skills_inventory.json"
LOCAL = Path(r"I:\E Drive\.grok\skills")

CATS = {
    "lattice": ["lattice", "mesh", "anchor", "gate", "network", "living-mesh", "birth", "star-chart", "pulse"],
    "kernel": ["kernel", "egg", "seeder", "planter", "sovereign-super", "p0", "guardian-p0"],
    "security": ["ops-detector", "pc-lattice", "lpis", "file-integrity", "token-saver", "alignment-badge"],
    "runtime": ["ollama", "smart-disk", "openclaw", "docker", "sandcastle", "mesh-deploy", "protocol-stack-operator", "sovereign-claw"],
    "creative": ["resonance", "glyph", "fractal", "truthlight", "ascii", "music", "joy-loop"],
    "champion": ["champion", "lightfather-vector", "cosmara", "lyra-starcore"],
    "memory": ["second-brain", "living-memory", "universal-living"],
    "tools": ["tools-portal", "pxpipe", "universal-cure", "lore-pack"],
}


def categorize(slug: str, name: str) -> str:
    s = (slug + " " + (name or "")).lower()
    for cat, keys in CATS.items():
        if any(k in s for k in keys):
            return cat
    return "other"


def local_meta(slug: str) -> dict:
    variants = [
        slug,
        slug.replace("lygo-ascii-art-studio", "lygo-ascii-art"),
        slug.replace("lygo-sovereign-claw", "lygo-openclaw"),
    ]
    for name in variants:
        p = LOCAL / name / "SKILL.md"
        if p.is_file():
            text = p.read_text(encoding="utf-8", errors="replace")[:5000]
            m = re.search(r'^description:\s*["\']?(.+?)["\']?\s*$', text, re.M)
            desc = m.group(1).strip().strip('"') if m else ""
            return {"has_local": True, "description": desc[:500]}
    return {"has_local": False}


def main() -> int:
    inv = json.loads(INV.read_text(encoding="utf-8"))
    if isinstance(inv, dict):
        inv = [inv]

    skills = []
    for item in inv:
        slug = item.get("slug") or ""
        name = item.get("displayName") or slug
        meta = local_meta(slug)
        summary = meta.get("description") or item.get("summary") or ""
        if isinstance(summary, str):
            summary = re.sub(r"\s+", " ", summary).strip()[:500]
        skills.append(
            {
                "slug": slug,
                "name": name,
                "summary": summary,
                "downloads": int(item.get("downloads") or 0),
                "category": categorize(slug, name),
                "clawhub_url": f"https://clawhub.ai/deepseekoracle/skills/{slug}",
                "install": f"npx clawhub@latest install deepseekoracle/{slug}",
                "has_local_skill": bool(meta.get("has_local")),
            }
        )

    skills.sort(key=lambda x: (-x["downloads"], x["name"].lower()))
    catalog = {
        "signature": "Delta9Phi963-LYGOSKILLHUB-CATALOG-v1",
        "name": "LYGOSKILLHUB",
        "version": "1.0.0",
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "publisher": "deepseekoracle",
        "steward": "Justin Helmer / Excavationpro / Lightfather",
        "clawhub_profile": "https://clawhub.ai/deepseekoracle",
        "lattice_pages": {
            "primary": "https://deepseekoracle.github.io/lygo-protocol-stack/LYGOSKILLHUB.html",
            "chatagent": "https://chatagent.ca/lygoskillhub.html",
            "excavationpro_mirror": "https://deepseekoracle.github.io/Excavationpro/LYGOSKILLHUB.html",
        },
        "skill_count": len(skills),
        "categories": sorted({s["category"] for s in skills}),
        "skills": skills,
    }
    raw = json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"
    catalog["catalog_sha256"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    raw = json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"

    outs = [
        Path(r"D:\lygo-protocol-stack\docs\data\lygoskillhub_catalog.json"),
        Path(r"D:\lygo-protocol-stack\docs\lygoskillhub_catalog.json"),
        Path(r"D:\Excavationpro\data\lygoskillhub_catalog.json"),
        Path(r"D:\chatagent\data\lygoskillhub_catalog.json"),
    ]
    for o in outs:
        o.parent.mkdir(parents=True, exist_ok=True)
        o.write_text(raw, encoding="utf-8")
        print("wrote", o)

    print("skills", len(skills), "sha", catalog["catalog_sha256"][:16])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
