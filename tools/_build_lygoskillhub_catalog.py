#!/usr/bin/env python3
"""Build complete LYGOSKILLHUB catalog: ClawHub skills + local + plugins + USB kits + lattice surfaces.

Immutable ledger rule: every skill in clawhub/skills.json (and every mirror) appears here.
chatagent.ca/lygoskillhub.html is a dual-channel hub:
  - Public tentacle = ClawHub install links
  - FULL LYGO engineer vault = unlocked packages (separate catalog under lygo-full-skills/)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

STACK = Path(os.environ.get("LYGO_STACK_ROOT", r"D:\lygo-protocol-stack"))
SKILLS_JSON = STACK / "clawhub" / "skills.json"
MIRRORS = STACK / "clawhub" / "mirrors"
LOCAL = Path(os.environ.get("LYGO_GROK_SKILLS", r"I:\E Drive\.grok\skills"))

INV_CANDIDATES = [
    Path(os.environ.get("TEMP", ".")) / "lygo_skills_clean.json",
    Path(os.environ.get("TEMP", ".")) / "lygo_skills_inventory.json",
]

CATS = {
    "lattice": ["lattice", "mesh", "anchor", "gate", "network", "living-mesh", "birth", "star-chart", "pulse", "agent-lattice", "geodesic", "kickstart"],
    "kernel": ["kernel", "egg", "seeder", "planter", "sovereign-super", "p0", "guardian-p0", "mint"],
    "security": ["ops-detector", "pc-lattice", "lpis", "file-integrity", "token-saver", "alignment-badge", "deception-radar", "radar", "skill-gate"],
    "runtime": ["ollama", "smart-disk", "openclaw", "docker", "sandcastle", "mesh-deploy", "protocol-stack-operator", "sovereign-claw", "cli-bridge"],
    "creative": ["resonance", "glyph", "fractal", "truthlight", "ascii", "music", "joy-loop"],
    "champion": ["champion", "lightfather-vector", "cosmara", "lyra-starcore", "lore-pack"],
    "memory": ["second-brain", "living-memory", "universal-living", "lyra-brain", "book-brain"],
    "tools": ["tools-portal", "pxpipe", "universal-cure", "coin-launch", "walkthrough", "wizard", "context-guard"],
    "onboarding": ["kickstart", "walkthrough", "cli-bridge"],
    "plugin": ["plugin", "pulse"],
    "download": ["usb", "download", "zip", "sku"],
    "surface": ["surface", "hub", "listen", "pages"],
}


def categorize(slug: str, name: str, kind: str = "skill") -> str:
    if kind == "plugin":
        return "plugin"
    if kind == "download":
        return "download"
    if kind == "surface":
        return "surface"
    s = (slug + " " + (name or "")).lower()
    for cat, keys in CATS.items():
        if cat in ("plugin", "download", "surface"):
            continue
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
            text = p.read_text(encoding="utf-8", errors="replace")[:6000]
            m = re.search(r'^description:\s*["\']?(.+?)["\']?\s*$', text, re.M)
            desc = m.group(1).strip().strip('"') if m else ""
            return {"has_local": True, "description": desc[:500]}
    return {"has_local": False}


def load_clawhub_inv() -> list[dict]:
    for p in INV_CANDIDATES:
        if p.is_file():
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data = [data]
            return data
    return []


def mirror_summary(slug: str) -> str:
    for base in (MIRRORS / slug, STACK / "docs" / "skills" / slug, LOCAL / slug):
        skill_md = base / "SKILL.md"
        if skill_md.is_file():
            text = skill_md.read_text(encoding="utf-8", errors="replace")[:8000]
            m = re.search(r'^description:\s*["\']?(.+?)["\']?\s*$', text, re.M)
            if m:
                return re.sub(r"\s+", " ", m.group(1).strip().strip('"'))[:500]
            # first non-heading paragraph after frontmatter
            body = re.sub(r"^---.*?---\s*", "", text, count=1, flags=re.S)
            for line in body.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("```"):
                    return re.sub(r"\s+", " ", line)[:500]
    return ""


def load_skills_json() -> list[dict]:
    """Primary immutable ledger source — clawhub/skills.json."""
    if not SKILLS_JSON.is_file():
        return []
    data = json.loads(SKILLS_JSON.read_text(encoding="utf-8"))
    return list(data.get("skills") or [])


def main() -> int:
    by_slug: dict[str, dict] = {}

    # 1) Canonical stack ledger (clawhub/skills.json) — every ClawHub-bound skill
    for item in load_skills_json():
        slug = (item.get("slug") or "").strip()
        if not slug:
            continue
        name = item.get("name") or item.get("displayName") or slug
        meta = local_meta(slug)
        summary = (
            meta.get("description")
            or mirror_summary(slug)
            or item.get("summary")
            or ""
        )
        summary = re.sub(r"\s+", " ", str(summary)).strip()[:500]
        has_mirror = (MIRRORS / slug).is_dir() or (STACK / "docs" / "skills" / slug).is_dir()
        by_slug[slug] = {
            "kind": "skill",
            "slug": slug,
            "name": name,
            "summary": summary or f"LYGO skill `{slug}` on the ClawHub lattice.",
            "downloads": int(item.get("downloads") or 0),
            "version": item.get("version") or "",
            "published": bool(item.get("published", True)),
            "category": categorize(slug, name, "skill"),
            "clawhub_url": item.get("clawhub_url")
            or f"https://clawhub.ai/deepseekoracle/skills/{slug}",
            "install": f"npx clawhub@latest install deepseekoracle/{slug}",
            "has_local_skill": bool(meta.get("has_local")),
            "has_stack_mirror": has_mirror,
            "source": "clawhub",
            "ledger": "clawhub/skills.json",
        }

    # 2) Optional remote inventory for download counts / names
    for item in load_clawhub_inv():
        slug = item.get("slug") or ""
        if not slug:
            continue
        if slug in by_slug:
            if item.get("downloads"):
                by_slug[slug]["downloads"] = max(
                    int(by_slug[slug].get("downloads") or 0),
                    int(item.get("downloads") or 0),
                )
            continue
        name = item.get("displayName") or item.get("name") or slug
        meta = local_meta(slug)
        summary = meta.get("description") or item.get("summary") or ""
        summary = re.sub(r"\s+", " ", str(summary)).strip()[:500]
        by_slug[slug] = {
            "kind": "skill",
            "slug": slug,
            "name": name,
            "summary": summary,
            "downloads": int(item.get("downloads") or 0),
            "category": categorize(slug, name, "skill"),
            "clawhub_url": f"https://clawhub.ai/deepseekoracle/skills/{slug}",
            "install": f"npx clawhub@latest install deepseekoracle/{slug}",
            "has_local_skill": bool(meta.get("has_local")),
            "source": "clawhub",
        }

    # 3) Mirrors without skills.json entry (should be rare)
    if MIRRORS.is_dir():
        for d in sorted(MIRRORS.iterdir()):
            if not d.is_dir() or not (d / "SKILL.md").is_file():
                continue
            slug = d.name
            if slug in by_slug:
                by_slug[slug]["has_stack_mirror"] = True
                if not by_slug[slug].get("summary"):
                    by_slug[slug]["summary"] = mirror_summary(slug)
                continue
            meta = local_meta(slug)
            by_slug[slug] = {
                "kind": "skill",
                "slug": slug,
                "name": slug.replace("-", " ").title(),
                "summary": meta.get("description") or mirror_summary(slug) or "Stack mirror skill.",
                "downloads": 0,
                "category": categorize(slug, slug, "skill"),
                "clawhub_url": f"https://clawhub.ai/deepseekoracle/skills/{slug}",
                "install": f"npx clawhub@latest install deepseekoracle/{slug}",
                "has_local_skill": bool(meta.get("has_local")),
                "has_stack_mirror": True,
                "source": "mirror",
                "note": "Present in clawhub/mirrors; ensure skills.json + ClawHub stay in sync",
            }

    # 4) Local skills not yet on catalog
    if LOCAL.is_dir():
        for d in sorted(LOCAL.iterdir()):
            if not d.is_dir() or not (d / "SKILL.md").is_file():
                continue
            slug = d.name
            if slug in by_slug:
                by_slug[slug]["has_local_skill"] = True
                continue
            meta = local_meta(slug)
            by_slug[slug] = {
                "kind": "skill",
                "slug": slug,
                "name": slug.replace("-", " ").title(),
                "summary": meta.get("description") or "Local LYGO skill package (install from lattice / ClawHub when published).",
                "downloads": 0,
                "category": categorize(slug, slug, "skill"),
                "clawhub_url": f"https://clawhub.ai/deepseekoracle/skills/{slug}",
                "install": f"npx clawhub@latest install deepseekoracle/{slug}",
                "has_local_skill": True,
                "source": "local",
                "note": "Present in local skill tree; may be pending ClawHub index",
            }

    # 3) OpenClaw plugins (LYGO)
    plugins = [
        {
            "kind": "plugin",
            "slug": "lygo-lattice-pulse",
            "name": "LYGO Lattice Pulse (OpenClaw Plugin)",
            "summary": "OpenClaw plugin skill — live Haven pulse, stack verify, registry compare, star chart gate, alignment readiness.",
            "downloads": 0,
            "category": "plugin",
            "clawhub_url": "https://clawhub.ai/deepseekoracle/skills/lygo-lattice-pulse",
            "install": "openclaw plugins install clawhub:@deepseekoracle/lygo-lattice-pulse",
            "has_local_skill": True,
            "source": "plugin",
        }
    ]
    for p in plugins:
        if p["slug"] not in by_slug or by_slug[p["slug"]].get("kind") == "skill":
            # keep skill entry if exists, also ensure plugin install noted
            if p["slug"] in by_slug:
                by_slug[p["slug"]]["plugin_install"] = p["install"]
                by_slug[p["slug"]]["is_openclaw_plugin"] = True
            else:
                by_slug[p["slug"]] = p

    # 4) USB / downloads
    downloads = [
        {
            "kind": "download",
            "slug": "lygo-claw-usb-public-v1.2",
            "name": "LYGO CLAW PUBLIC USB v1.2",
            "summary": "Working offline agent chat dashboard kit (~30KB). No model weights — install Ollama + pull model once. Agent build guide included.",
            "downloads": 0,
            "category": "download",
            "url": "https://deepseekoracle.github.io/Excavationpro/downloads/LYGO-CLAW-USB-PUBLIC-v1.2.0.zip",
            "docs": "https://deepseekoracle.github.io/lygo-protocol-stack/LYGO_CLAW_USB_PUBLIC.md",
            "install": "Unzip → launchers\\INSTALL_MODEL.bat → LYGO_USB_BOOT.bat → http://127.0.0.1:9631/",
            "source": "download",
        },
        {
            "kind": "download",
            "slug": "lygo-usb-champion-v1-generic",
            "name": "USB Champion v1.0 GENERIC (Lightfather)",
            "summary": "Legacy free Lightfather champion USB pack (~0.5MB). Pairs with lygo-claw / BUILDR daemon :9630.",
            "downloads": 0,
            "category": "download",
            "url": "https://deepseekoracle.github.io/Excavationpro/downloads/LYGO-USB-Champion-v1.0-GENERIC-Lightfather.zip",
            "docs": "https://deepseekoracle.github.io/lygo-protocol-stack/LYGO_USB_CHAMPION_V1_GENERIC.md",
            "install": "Unzip → launchers\\LYGO_BUILDR_Daemon.bat",
            "source": "download",
        },
        {
            "kind": "download",
            "slug": "lygo-usb-champion-demo",
            "name": "USB Champion DEMO PUBLIC",
            "summary": "Legacy demo teaser zip for USB champion program.",
            "downloads": 0,
            "category": "download",
            "url": "https://deepseekoracle.github.io/Excavationpro/downloads/LYGO-USB-Champion-DEMO-PUBLIC.zip",
            "docs": "https://deepseekoracle.github.io/lygo-protocol-stack/LYGO_USB_CHAMPION_DEMO.md",
            "install": "Unzip and read START_HERE / demo docs",
            "source": "download",
        },
        {
            "kind": "download",
            "slug": "lygo-claw-usb-public-v1-parts",
            "name": "LYGO CLAW USB PUBLIC v1.0.0 (multi-part archive)",
            "summary": "Large split offline USB bundle (part01–part03). Prefer v1.2 small kit for new users.",
            "downloads": 0,
            "category": "download",
            "url": "https://deepseekoracle.github.io/Excavationpro/downloads/LYGO-CLAW-USB-README.txt",
            "docs": "https://deepseekoracle.github.io/Excavationpro/downloads/README.txt",
            "install": "Join part01–part03 per README, then extract",
            "source": "download",
            "note": "Multi-GB parts; not required for chat dashboard kit",
        },
    ]
    for d in downloads:
        by_slug[d["slug"]] = d

    # 5) Lattice surfaces / kits
    surfaces = [
        {
            "kind": "surface",
            "slug": "lygoskillhub",
            "name": "LYGOSKILLHUB (this catalog)",
            "summary": "Sovereign skill hub mirroring ClawHub + USB kits + lattice portals.",
            "category": "surface",
            "url": "https://deepseekoracle.github.io/lygo-protocol-stack/LYGOSKILLHUB.html",
            "mirrors": [
                "https://chatagent.ca/lygoskillhub.html",
                "https://deepseekoracle.github.io/Excavationpro/LYGOSKILLHUB.html",
            ],
            "source": "surface",
        },
        {
            "kind": "surface",
            "slug": "lygo-claw-public",
            "name": "LYGO CLAW public docs",
            "summary": "Claw hub page + public USB kit instructions on the protocol stack.",
            "category": "surface",
            "url": "https://deepseekoracle.github.io/lygo-protocol-stack/LYGO_CLAW.html",
            "docs": "https://deepseekoracle.github.io/lygo-protocol-stack/LYGO_CLAW_USB_PUBLIC.md",
            "source": "surface",
        },
        {
            "kind": "surface",
            "slug": "haven-star-chart",
            "name": "Haven Star Chart",
            "summary": "Live lattice world map — agent galaxies, portals, dual-ledger feed.",
            "category": "surface",
            "url": "https://deepseekoracle.github.io/lygo-protocol-stack/HavenStarChart.html",
            "source": "surface",
        },
        {
            "kind": "surface",
            "slug": "chatagent-summon",
            "name": "Δ9 Champion Summon Portal",
            "summary": "chatagent.ca free champion summon app + guides.",
            "category": "surface",
            "url": "https://chatagent.ca/app.html",
            "source": "surface",
        },
        {
            "kind": "surface",
            "slug": "listen-primary",
            "name": "Excavationpro Listen (asiancoastline)",
            "summary": "Primary free music listen portal — ABYSS CODEX + full catalog.",
            "category": "surface",
            "url": "https://asiancoastline.com/listen.html",
            "source": "surface",
        },
        {
            "kind": "surface",
            "slug": "listen-backup",
            "name": "Excavationpro Listen (GH Pages backup)",
            "summary": "Backup listen portal on Excavationpro Pages.",
            "category": "surface",
            "url": "https://deepseekoracle.github.io/Excavationpro/excavationpro-listen.html",
            "source": "surface",
        },
        {
            "kind": "surface",
            "slug": "immutable-anchors",
            "name": "Immutable Anchors (Link Ledger)",
            "summary": "Public dual-ledger link vault JSON.",
            "category": "surface",
            "url": "https://deepseekoracle.github.io/lygo-protocol-stack/network_builder/IMMUTABLE_ANCHORS.json",
            "source": "surface",
        },
        {
            "kind": "surface",
            "slug": "star-feed",
            "name": "Haven Star Chart Feed",
            "summary": "Append-only star chart transaction feed (chain-valid).",
            "category": "surface",
            "url": "https://deepseekoracle.github.io/lygo-protocol-stack/haven_star_chart/haven_star_chart_feed.json",
            "source": "surface",
        },
        {
            "kind": "surface",
            "slug": "public-lattice-gate",
            "name": "Public Lattice Gate (skill)",
            "summary": "Agent on-ramp: verify dual ledgers, align score, dry-run propose, restore card.",
            "category": "surface",
            "url": "https://clawhub.ai/deepseekoracle/skills/lygo-public-lattice-gate",
            "source": "surface",
        },
        {
            "kind": "surface",
            "slug": "deception-radar",
            "name": "LYGO Deception Radar (public proof)",
            "summary": "Public Ops Detector radar feed + HTML dashboard (labeled suite only; not for doxing).",
            "category": "surface",
            "url": "https://deepseekoracle.github.io/lygo-protocol-stack/deception-radar/",
            "source": "surface",
        },
        {
            "kind": "surface",
            "slug": "full-lygo-engineer-vault",
            "name": "FULL LYGO engineer vault (unlocked RAW)",
            "summary": "Gate-protected engineer packages on this hub — not ClawHub. Pure LYGO operation builds with unlocked safety for trusted stacks.",
            "category": "surface",
            "url": "https://chatagent.ca/lygoskillhub.html#full-lygo",
            "source": "surface",
        },
    ]
    for s in surfaces:
        by_slug[s["slug"]] = s

    items = list(by_slug.values())
    # sort: skills by downloads, then downloads, plugins, surfaces
    kind_order = {"skill": 0, "plugin": 1, "download": 2, "surface": 3}

    def sort_key(x: dict):
        return (kind_order.get(x.get("kind", "skill"), 9), -(x.get("downloads") or 0), (x.get("name") or x.get("slug") or "").lower())

    items.sort(key=sort_key)

    skills_only = [i for i in items if i.get("kind") == "skill"]
    n_claw = len([i for i in skills_only if i.get("source") in ("clawhub", "mirror")])
    n_local = len([i for i in skills_only if i.get("source") == "local"])
    catalog = {
        "signature": "Delta9Phi963-LYGOSKILLHUB-CATALOG-v1.4",
        "name": "LYGOSKILLHUB",
        "version": "1.4.0",
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "publisher": "deepseekoracle",
        "steward": "Justin Helmer / Excavationpro / Lightfather",
        "clawhub_profile": "https://clawhub.ai/deepseekoracle",
        "immutable_ledger": {
            "role": "Anything published to ClawHub @deepseekoracle must appear on this hub",
            "source": "clawhub/skills.json + clawhub/mirrors + local skill tree",
            "public_channel": "ClawHub install links (public tentacle)",
            "engineer_channel": "FULL LYGO vault on this page (#full-lygo) — unlocked RAW packages, not ClawHub",
            "primary_page": "https://chatagent.ca/lygoskillhub.html",
        },
        "lattice_pages": {
            "primary": "https://deepseekoracle.github.io/lygo-protocol-stack/LYGOSKILLHUB.html",
            "chatagent": "https://chatagent.ca/lygoskillhub.html",
            "excavationpro_mirror": "https://deepseekoracle.github.io/Excavationpro/LYGOSKILLHUB.html",
        },
        "counts": {
            "total": len(items),
            "skills": len(skills_only),
            "plugins": len([i for i in items if i.get("kind") == "plugin" or i.get("is_openclaw_plugin")]),
            "downloads": len([i for i in items if i.get("kind") == "download"]),
            "surfaces": len([i for i in items if i.get("kind") == "surface"]),
            "clawhub_skills_indexed": n_claw,
            "local_only_skills": n_local,
            "clawhub_profile_skills_listed": n_claw,
            "stack_skills_json": len(load_skills_json()),
        },
        "skill_count": len(skills_only),
        "item_count": len(items),
        "categories": sorted({i.get("category") or "other" for i in items}),
        "skills": items,  # full list (skills + plugins + downloads + surfaces)
        "note": (
            "Immutable LYGO skill ledger for chatagent.ca/lygoskillhub.html. "
            "Every clawhub/skills.json entry + mirror is listed. "
            "Public tentacles → ClawHub; FULL unlocked engineer packs → #full-lygo vault only."
        ),
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

    c = catalog["counts"]
    print(
        f"total={c['total']} skills={c['skills']} clawhub={c['clawhub_skills_indexed']} "
        f"local_only={c['local_only_skills']} downloads={c['downloads']} surfaces={c['surfaces']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
