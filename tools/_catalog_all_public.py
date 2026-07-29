#!/usr/bin/env python3
"""Mark every skill as ClawHub-public; map protected *-openclaw slugs; rebuild counts."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

CAT_PATHS = [
    Path(r"D:\lygo-protocol-stack\docs\lygoskillhub_catalog.json"),
    Path(r"D:\lygo-protocol-stack\docs\data\lygoskillhub_catalog.json"),
    Path(r"D:\Excavationpro\data\lygoskillhub_catalog.json"),
    Path(r"D:\chatagent\data\lygoskillhub_catalog.json"),
]

PUBLIC_MAP = {
    "lygo-openclaw": {
        "public_slug": "lygo-open-claw",
        "install": "npx clawhub@latest install deepseekoracle/lygo-open-claw",
        "clawhub_url": "https://clawhub.ai/deepseekoracle/skills/lygo-open-claw",
        "note": "ClawHub protects *-openclaw slugs. Public install: lygo-open-claw (also lygo-sovereign-claw).",
        "also_install": "npx clawhub@latest install deepseekoracle/lygo-sovereign-claw",
    },
    "lyra-openclaw": {
        "public_slug": "lyra-open-claw",
        "install": "npx clawhub@latest install deepseekoracle/lyra-open-claw",
        "clawhub_url": "https://clawhub.ai/deepseekoracle/skills/lyra-open-claw",
        "note": "ClawHub protects *-openclaw slugs. Public install: lyra-open-claw.",
    },
    "lygo-lattice-pulse": {
        "public_slug": "lygo-lattice-pulse",
        "install": "npx clawhub@latest install deepseekoracle/lygo-lattice-pulse",
        "clawhub_url": "https://clawhub.ai/deepseekoracle/skills/lygo-lattice-pulse",
        "plugin_install": "openclaw plugins install clawhub:@deepseekoracle/lygo-lattice-pulse",
        "is_openclaw_plugin": True,
    },
    "lygo-pc-lattice-hardening": {
        "public_slug": "lygo-pc-lattice-hardening",
        "install": "npx clawhub@latest install deepseekoracle/lygo-pc-lattice-hardening",
        "clawhub_url": "https://clawhub.ai/deepseekoracle/skills/lygo-pc-lattice-hardening",
    },
}

ALIASES = [
    {
        "kind": "skill",
        "slug": "lygo-open-claw",
        "name": "LYGO OpenClaw (Sovereign Router)",
        "summary": "Public ClawHub slug for LYGO-OpenClaw sovereign router (pairs with lygo-sovereign-claw). P0–P5 gates, consent-gated planter. ClawHub blocks *-openclaw names.",
        "downloads": 0,
        "category": "runtime",
        "clawhub_url": "https://clawhub.ai/deepseekoracle/skills/lygo-open-claw",
        "install": "npx clawhub@latest install deepseekoracle/lygo-open-claw",
        "has_local_skill": True,
        "source": "clawhub",
        "alias_of": "lygo-sovereign-claw",
        "internal_name": "lygo-openclaw",
    },
    {
        "kind": "skill",
        "slug": "lyra-open-claw",
        "name": "LYRA OpenClaw Hybrid",
        "summary": "Public hybrid LYRA + OpenClaw super-system map — browser, Discord, Moltbook/MoltX, Clawnch, memory, Ollama. Runtime secrets never ship. Consent-gated. ClawHub blocks *-openclaw names.",
        "downloads": 0,
        "category": "runtime",
        "clawhub_url": "https://clawhub.ai/deepseekoracle/skills/lyra-open-claw",
        "install": "npx clawhub@latest install deepseekoracle/lyra-open-claw",
        "has_local_skill": True,
        "source": "clawhub",
        "internal_name": "lyra-openclaw",
    },
]


def main() -> int:
    cat = json.loads(CAT_PATHS[0].read_text(encoding="utf-8"))
    by = {s["slug"]: s for s in cat.get("skills", [])}

    for s in cat["skills"]:
        if (s.get("kind") or "skill") != "skill":
            continue
        slug = s.get("slug") or ""
        # All skills are public now
        if s.get("source") == "local":
            s["source"] = "clawhub"
        if "note" in s and "pending ClawHub" in str(s.get("note", "")):
            s.pop("note", None)
        s.setdefault("source", "clawhub")
        if slug in PUBLIC_MAP:
            m = PUBLIC_MAP[slug]
            s["source"] = "clawhub"
            s["has_local_skill"] = True
            s["install"] = m["install"]
            s["clawhub_url"] = m["clawhub_url"]
            s["public_slug"] = m["public_slug"]
            if m.get("note"):
                s["note"] = m["note"]
            if m.get("also_install"):
                s["also_install"] = m["also_install"]
            if m.get("plugin_install"):
                s["plugin_install"] = m["plugin_install"]
            if m.get("is_openclaw_plugin"):
                s["is_openclaw_plugin"] = True

    for a in ALIASES:
        if a["slug"] not in by:
            cat["skills"].append(a)
            by[a["slug"]] = a
            print("added", a["slug"])
        else:
            by[a["slug"]].update({k: v for k, v in a.items()})
            print("updated", a["slug"])

    skills = cat["skills"]
    n_skill = sum(1 for s in skills if (s.get("kind") or "skill") == "skill")
    n_local = sum(
        1
        for s in skills
        if (s.get("kind") or "skill") == "skill" and s.get("source") == "local"
    )
    n_claw = sum(
        1
        for s in skills
        if (s.get("kind") or "skill") == "skill" and s.get("source") == "clawhub"
    )
    n_dl = sum(1 for s in skills if s.get("kind") == "download")
    n_surf = sum(1 for s in skills if s.get("kind") == "surface")
    n_plug = sum(1 for s in skills if s.get("kind") == "plugin" or s.get("is_openclaw_plugin"))

    cat["counts"] = {
        "total": len(skills),
        "skills": n_skill,
        "plugins": max(n_plug, 1),
        "downloads": n_dl,
        "surfaces": n_surf,
        "clawhub_skills_indexed": n_claw,
        "local_only_skills": n_local,
        "clawhub_profile_skills_listed": 63,
        "all_skills_public": n_local == 0,
    }
    cat["skill_count"] = n_skill
    cat["item_count"] = len(skills)
    cat["version"] = "1.3.0"
    cat["signature"] = "Delta9Phi963-LYGOSKILLHUB-CATALOG-v1.3"
    cat["updated_utc"] = datetime.now(timezone.utc).isoformat()
    cat["note"] = (
        "Balanced public lattice: every skill has a ClawHub install. "
        "Protected *-openclaw namespace maps to lygo-open-claw + lyra-open-claw. "
        "Zero local_only. Dual ledgers + LYGOAGENT on hub page."
    )
    cat["categories"] = sorted({s.get("category") for s in skills if s.get("category")})
    tmp = {k: v for k, v in cat.items() if k != "catalog_sha256"}
    raw = json.dumps(tmp, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    cat["catalog_sha256"] = hashlib.sha256(raw.encode()).hexdigest()

    for p in CAT_PATHS:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("wrote", p)

    print("skills", n_skill, "local_only", n_local, "clawhub", n_claw, "total", len(skills))
    if n_local != 0:
        locals_ = [
            s["slug"]
            for s in skills
            if (s.get("kind") or "skill") == "skill" and s.get("source") == "local"
        ]
        raise SystemExit(f"still local: {locals_}")
    print("OK all skills public")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
