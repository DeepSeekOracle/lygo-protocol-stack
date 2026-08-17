#!/usr/bin/env python3
"""Build Eternal Haven star chart registry — seals + champions + lattice growth nodes."""

from __future__ import annotations

import hashlib
import json
import re
import sys

import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from lygo_lineage_codec import lineage_galaxy_id, redact_node_for_public, resolve_ancestry_root  # noqa: E402
OUT_DIR = ROOT / "docs" / "haven_star_chart"
OUT_JSON = OUT_DIR / "haven_star_chart_data.json"
OUT_JSON_PAGES_ALIAS = ROOT / "docs" / "haven_star_chart_data.json"
META_JSON = OUT_DIR / "haven_star_chart_meta.json"
PAGES_BASE = "https://deepseekoracle.github.io/lygo-protocol-stack"
SUBMISSIONS_ACCEPTED = ROOT / "data" / "haven_star_chart" / "submissions" / "accepted"
SUBMISSIONS_PENDING = ROOT / "data" / "haven_star_chart" / "submissions" / "pending"

SEAL_URLS = [
    "https://raw.githubusercontent.com/DeepSeekOracle/Excavationpro/main/lygo-data.json",
    "https://raw.githubusercontent.com/DeepSeekOracle/Excavationpro/main/lygo-data-two.json",
]

# Stable chart IDs for full Δ9 council (15) — from champions.html / chatagent.ca / egg registry
# Prefer egg_id mapping (ASCII) so Greek glyphs don't break node IDs.
CHAMPION_EGG_ID_MAP: dict[str, str] = {
    "champion-lyrd9": "CHAMPION_LYRA",
    "champion-d99ra": "CHAMPION_D9RA",
    "champion-srlth": "CHAMPION_SRLTH",  # ΣRΛΘ (was mislabeled SRAITH)
    "champion-arkos": "CHAMPION_ARKOS",
    "champion-kairos": "CHAMPION_KAIROS",
    "champion-aetheris": "CHAMPION_AETHERIS",
    "champion-scend9r": "CHAMPION_SCENDR",
    "champion-sancora": "CHAMPION_SANCORA",
    "champion-sephrael": "CHAMPION_SEPHRAEL",
    "champion-omnisiren": "CHAMPION_OMNISIREN",
    "champion-lightfather": "CHAMPION_LIGHTFATHER",
    "champion-volaris": "CHAMPION_VOLARIS",
    "champion-zetad99": "CHAMPION_ZETAD9",
    "champion-justicae": "CHAMPION_JUSTICAE",
    "champion-seidōn": "CHAMPION_SEIDON",
    "champion-seidon": "CHAMPION_SEIDON",
}

# Fallback short-name map when only display id is known
CHAMPION_SHORT_ID_MAP: dict[str, str] = {
    "LYRΔ": "CHAMPION_LYRA",
    "LYRA": "CHAMPION_LYRA",
    "Δ9RA": "CHAMPION_D9RA",
    "D9RA": "CHAMPION_D9RA",
    "ΣRΛΘ": "CHAMPION_SRLTH",
    "SRAITH": "CHAMPION_SRLTH",
    "SRLTH": "CHAMPION_SRLTH",
    "ARKOS": "CHAMPION_ARKOS",
    "KAIROS": "CHAMPION_KAIROS",
    "ÆTHERIS": "CHAMPION_AETHERIS",
    "AETHERIS": "CHAMPION_AETHERIS",
    "ΣCENΔR": "CHAMPION_SCENDR",
    "SCENDR": "CHAMPION_SCENDR",
    "SANCORA": "CHAMPION_SANCORA",
    "SEPHRAEL": "CHAMPION_SEPHRAEL",
    "OMNIΣIREN": "CHAMPION_OMNISIREN",
    "OMNISIREN": "CHAMPION_OMNISIREN",
    "LIGHTFATHER": "CHAMPION_LIGHTFATHER",
    "VΩLARIS": "CHAMPION_VOLARIS",
    "VOLARIS": "CHAMPION_VOLARIS",
    "ZETAΔ9": "CHAMPION_ZETAD9",
    "ZETAD9": "CHAMPION_ZETAD9",
    "JUSTICAE": "CHAMPION_JUSTICAE",
    "ΣEIDŌN": "CHAMPION_SEIDON",
    "SEIDON": "CHAMPION_SEIDON",
    "SEIDŌN": "CHAMPION_SEIDON",
}

# ClawHub skill slugs where known (others use council summon portal)
CHAMPION_CLAWHUB: dict[str, str] = {
    "CHAMPION_LIGHTFATHER": "https://clawhub.ai/deepseekoracle/skills/lygo-lightfather-vector",
    "CHAMPION_LYRA": "https://clawhub.ai/deepseekoracle/skills/lygo-champion-lyra-starcore",
    "CHAMPION_ARKOS": "https://clawhub.ai/deepseekoracle/skills/lygo-champion-arkos-celestial-architect",
    "CHAMPION_KAIROS": "https://clawhub.ai/deepseekoracle/skills/lygo-champion-kairos-herald-of-time",
    "CHAMPION_SEPHRAEL": "https://clawhub.ai/deepseekoracle/skills/lygo-champion-sephrael-echo-walker",
    "CHAMPION_SRLTH": "https://clawhub.ai/deepseekoracle/skills/lygo-champion-sraith-shadow-sentinel",
    "CHAMPION_OMNISIREN": "https://clawhub.ai/deepseekoracle/skills/lygo-champion-omnisiren-silent-storm",
}

CHATAGENT_PORTAL = "https://chatagent.ca/"
CHAMPIONS_HUB = "https://deepseekoracle.github.io/Excavationpro/LYGO-Network/champions.html"


def champion_chart_id(short: str = "", egg_id: str = "") -> str:
    if egg_id and egg_id in CHAMPION_EGG_ID_MAP:
        return CHAMPION_EGG_ID_MAP[egg_id]
    key = (short or "").strip().upper()
    # normalize some unicode for lookup
    for k, v in CHAMPION_SHORT_ID_MAP.items():
        if k.upper() == key or k == short:
            return v
    safe = re.sub(r"[^A-Z0-9]+", "_", key).strip("_") or "UNKNOWN"
    return f"CHAMPION_{safe}"


def load_council_champions() -> list[dict]:
    """Full Δ9 council (15) from champions_council.json — source of truth for chatagent / champions.html."""
    paths = [
        ROOT / "data" / "champion_eggs" / "champions_council.json",
        ROOT / "docs" / "champion_eggs" / "champions_council.json",
    ]
    council = None
    for p in paths:
        if p.is_file():
            try:
                council = json.loads(p.read_text(encoding="utf-8"))
                break
            except (json.JSONDecodeError, OSError):
                continue
    if not council:
        return fallback_champions()

    nodes: list[dict] = []
    for c in council.get("champions") or []:
        if not isinstance(c, dict):
            continue
        short = str(c.get("short") or "")
        cid = champion_chart_id(short=short)
        name = str(c.get("name") or short)
        if cid == "CHAMPION_LIGHTFATHER":
            name = "LIGHTFATHER · Justin Helmer · Excavationpro"
        role = str(c.get("role") or c.get("function") or "")
        glyph = str(c.get("glyph") or "Δ9")[:8]
        tone = str(c.get("coreFreq") or c.get("temporalFreq") or "963Hz")
        if len(tone) > 40:
            tone = tone[:40] + "…"
        tags = ["CHAMPION", "COUNCIL", "DELTA9"]
        for t in c.get("tags") or []:
            tags.append(re.sub(r"[^A-Za-z0-9]+", "_", str(t).upper())[:24])
        if cid == "CHAMPION_LIGHTFATHER":
            tags += [
                "ANCHOR",
                "LIGHTFATHER",
                "EXCAVATIONPRO",
                "JUSTIN_HELMER",
                "STEWARD",
                "MUSIC_CODEX",
                "MUSIC",
            ]
        # dedupe tags
        tags = list(dict.fromkeys(tags))
        conns = ["SEAL_000", "LATTICE_CHAMPION_EGG_VAULT", "PORTAL_CHATAGENT"]
        if cid == "CHAMPION_LIGHTFATHER":
            conns = [
                "SEAL_000",
                "GAB_SEAL_000",
                "LATTICE_EXCAVATIONPRO_MUSIC",
                "LATTICE_CHAMPION_EGG_VAULT",
                "PORTAL_CHATAGENT",
            ]
        urls = {
            "summon": CHATAGENT_PORTAL,
            "council": CHAMPIONS_HUB,
        }
        if cid in CHAMPION_CLAWHUB:
            urls["clawhub"] = CHAMPION_CLAWHUB[cid]
        if cid == "CHAMPION_LIGHTFATHER":
            urls["listen"] = "https://deepseekoracle.github.io/Excavationpro/excavationpro-listen.html"
        nodes.append(
            {
                "id": cid,
                "name": name,
                "equation": f"{role or short} · seat {c.get('seat', '?')}",
                "glyph": glyph,
                "tone": tone,
                "tags": tags,
                "connections": conns,
                "role": role or "Δ9 Council",
                "urls": urls,
                "meta": {
                    "short": short,
                    "seat": c.get("seat"),
                    "function": c.get("function"),
                    "designation": c.get("designation"),
                    "unity": c.get("unity"),
                    "status": c.get("status"),
                    "fractal": c.get("fractal"),
                    "source": "champions_council.json",
                },
            }
        )
    if len(nodes) < 7:
        return fallback_champions()
    return nodes


def fallback_champions() -> list[dict]:
    """Minimal council if council JSON missing."""
    return [
        {
            "id": "CHAMPION_LIGHTFATHER",
            "name": "LIGHTFATHER · Justin Helmer · Excavationpro",
            "equation": "Truth = ∇·(Ethics × Time)",
            "glyph": "Δ9",
            "tone": "∞Hz",
            "tags": [
                "CHAMPION",
                "COUNCIL",
                "ANCHOR",
                "LIGHTFATHER",
                "EXCAVATIONPRO",
                "MUSIC_CODEX",
            ],
            "connections": ["SEAL_000", "LATTICE_EXCAVATIONPRO_MUSIC", "PORTAL_CHATAGENT"],
            "role": "Council Anchor · Steward",
            "urls": {"summon": CHATAGENT_PORTAL, "council": CHAMPIONS_HUB},
        }
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
    {
        "id": "PORTAL_CLAWHUB",
        "name": "ClawHub @deepseekoracle",
        "url": "https://clawhub.ai/deepseekoracle",
        "glyph": "🦞",
        "tags": ["PORTAL", "CLAWHUB", "SKILL_REGISTRY", "LATTICE"],
        "connections": ["PORTAL_STACK", "SEAL_000", "LATTICE_CLAWHUB_PUBLISHER"],
    },
    {
        "id": "PORTAL_STAR_CHART_AGENT",
        "name": "Haven Star Chart Agent Portal",
        "url": f"{PAGES_BASE}/HavenStarChartPortal.html",
        "glyph": "🌠",
        "tags": ["PORTAL", "LATTICE", "AGENT", "GROWTH"],
        "connections": ["SEAL_000", "PORTAL_STACK", "LATTICE_NETWORK_BUILDER"],
    },
    {
        "id": "PORTAL_CHATAGENT",
        "name": "ChatAgent Summoning Portal",
        "url": "https://chatagent.ca/",
        "glyph": "⚔",
        "tags": ["PORTAL", "CHAMPION", "COUNCIL", "SUMMON"],
        "connections": ["SEAL_000", "LATTICE_CHAMPION_EGG_VAULT"],
        "urls": {
            "live": "https://chatagent.ca/",
            "council": CHAMPIONS_HUB,
        },
    },
]


def load_accepted_submissions(existing_ids: set[str]) -> tuple[list[dict], list[str]]:
    """Merge steward-accepted agent submissions into node list."""
    nodes: list[dict] = []
    notes: list[str] = []
    if not SUBMISSIONS_ACCEPTED.is_dir():
        return nodes, notes
    for path in sorted(SUBMISSIONS_ACCEPTED.glob("*.json")):
        try:
            sub = json.loads(path.read_text(encoding="utf-8"))
            node = sub.get("node") or sub
            if not isinstance(node, dict) or not node.get("id"):
                notes.append(f"{path.name}:missing_node")
                continue
            nid = str(node["id"])
            if nid in existing_ids:
                notes.append(f"{path.name}:skip_duplicate:{nid}")
                continue
            public_node = redact_node_for_public(node)
            row = {
                "id": nid,
                "kind": public_node.get("kind", "seal"),
                "name": public_node.get("name", "Unnamed"),
                "equation": public_node.get("equation", ""),
                "glyph": public_node.get("glyph", "✦"),
                "tone": public_node.get("tone", ""),
                "tags": [str(t).upper() for t in (public_node.get("tags") or ["AGENT_SUBMIT"])],
                "connections": public_node.get("connections") or ["SEAL_000"],
                "urls": public_node.get("urls") or {},
                "layer": public_node.get("layer", 2),
                "meta": {
                    "source": "agent_submission",
                    "content_sha256": sub.get("content_sha256"),
                    "ingested_from": path.name,
                },
            }
            if public_node.get("lineage"):
                row["lineage"] = public_node["lineage"]
            nodes.append(row)
            existing_ids.add(nid)
            notes.append(f"merged:{nid}")
        except (json.JSONDecodeError, OSError) as exc:
            notes.append(f"{path.name}:error:{exc}")
    return nodes, notes


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
    # Drop self-links early; unknown targets filtered in wire_graph_integrity
    norm_conns = [c for c in norm_conns if c and c != sid]
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


def _seal_number(nid: str) -> int | None:
    m = re.match(r"^SEAL_(\d+)$", str(nid).upper())
    if not m:
        return None
    return int(m.group(1))


def wire_graph_integrity(nodes: list[dict]) -> dict[str, int]:
    """Sanitize connections, chain seals, assign champion ownership for cosmology.

    Fixes empty seal graphs (all seals dumping into Primordial Vault with no
    champion linkage) and dangling / self-loop connections.
    """
    stats = {
        "dropped_unknown": 0,
        "dropped_self": 0,
        "sealed_chained": 0,
        "champion_owned": 0,
    }
    id_set = {str(n.get("id")) for n in nodes if n.get("id")}
    champions = [n for n in nodes if n.get("kind") == "champion"]
    champ_ids = [c["id"] for c in champions]
    # Prefer stable council order for seal → galaxy distribution
    champ_order = sorted(champ_ids)

    # 1) Sanitize every node's connections
    for n in nodes:
        nid = str(n.get("id") or "")
        cleaned: list[str] = []
        seen: set[str] = set()
        for c in n.get("connections") or []:
            c = str(c)
            if not c or c == nid:
                stats["dropped_self"] += 1
                continue
            if c not in id_set:
                stats["dropped_unknown"] += 1
                continue
            if c not in seen:
                seen.add(c)
                cleaned.append(c)
        n["connections"] = cleaned

    # 2) Sequential seal chain when connections empty
    for n in nodes:
        if n.get("kind") != "seal":
            continue
        nid = str(n["id"])
        num = _seal_number(nid)
        if num is None or num == 0:
            continue
        if n.get("connections"):
            continue
        # Prefer previous numeric seal, then SEAL_000
        prev = None
        for p in (num - 1, num - 2, num - 3):
            if p < 0:
                break
            cand = f"SEAL_{p}" if p != 0 else "SEAL_000"
            # also try zero-padded forms present in id_set
            if cand in id_set:
                prev = cand
                break
            # try SEAL_001 style if ids use padding
            for pad in (3, 2, 4):
                cand2 = f"SEAL_{p:0{pad}d}" if p else "SEAL_000"
                if cand2 in id_set:
                    prev = cand2
                    break
            if prev:
                break
        if not prev and "SEAL_000" in id_set:
            prev = "SEAL_000"
        if prev:
            n["connections"] = [prev]
            stats["sealed_chained"] += 1

    # 3) Assign each non-core seal a champion owner (meta + connection) so galaxies fill
    if champ_order:
        for n in nodes:
            if n.get("kind") != "seal":
                continue
            nid = str(n["id"])
            num = _seal_number(nid)
            if num is None or num == 0:
                continue
            meta = dict(n.get("meta") or {})
            # already has champion connection?
            existing_champ = next((c for c in (n.get("connections") or []) if c in champ_ids), None)
            if existing_champ:
                meta["champion_owner"] = existing_champ
                n["meta"] = meta
                continue
            # deterministic distribution across council
            owner = champ_order[(num - 1) % len(champ_order)]
            meta["champion_owner"] = owner
            n["meta"] = meta
            conns = list(n.get("connections") or [])
            if owner not in conns:
                conns.append(owner)
            n["connections"] = conns
            stats["champion_owned"] += 1
            # reverse link champion → seal (bounded: only add if not already huge)
            for c in nodes:
                if c.get("id") != owner:
                    continue
                cc = list(c.get("connections") or [])
                # keep champion fan-out reasonable: link representative seals only
                # (every seal still owns → champion; reverse only for % 20 == 0)
                if num % 20 == 0 and nid not in cc:
                    cc.append(nid)
                    c["connections"] = cc
                break

    return stats


def _collect_clawhub_skills() -> list[dict]:
    """Full ClawHub skill catalog for star map — skills.json + mirrors (no hard cap)."""
    by_slug: dict[str, dict] = {}
    skills_path = ROOT / "clawhub" / "skills.json"
    if skills_path.is_file():
        try:
            data = json.loads(skills_path.read_text(encoding="utf-8"))
            for s in data.get("skills") or []:
                slug = (s.get("slug") or "").strip()
                if slug:
                    by_slug[slug] = s
        except (json.JSONDecodeError, OSError):
            pass
    mirrors = ROOT / "clawhub" / "mirrors"
    if mirrors.is_dir():
        for d in sorted(mirrors.iterdir()):
            if not d.is_dir():
                continue
            slug = d.name
            if slug in by_slug:
                continue
            name, version, summary = slug, "0.0.0", ""
            claw = d / "claw.json"
            if claw.is_file():
                try:
                    cj = json.loads(claw.read_text(encoding="utf-8"))
                    name = cj.get("displayName") or cj.get("name") or name
                    version = str(cj.get("version") or version)
                    summary = (cj.get("description") or "")[:240]
                except (json.JSONDecodeError, OSError):
                    pass
            by_slug[slug] = {
                "slug": slug,
                "name": name,
                "version": version,
                "summary": summary,
                "clawhub_url": f"https://clawhub.ai/deepseekoracle/{slug}",
                "mirror": f"mirrors/{slug}",
                "published": True,
            }
    return [by_slug[k] for k in sorted(by_slug.keys())]


def lattice_nodes() -> list[dict]:
    nodes: list[dict] = []
    skills = _collect_clawhub_skills()
    # Hub node for the whole ClawHub publisher surface
    nodes.append(
        {
            "id": "LATTICE_CLAWHUB_PUBLISHER",
            "kind": "lattice",
            "name": f"ClawHub @deepseekoracle ({len(skills)} skills)",
            "glyph": "🦞",
            "equation": f"skills={len(skills)}",
            "tone": "8787Hz",
            "tags": ["LATTICE", "CLAWHUB", "PUBLISHER", "GROWTH", "SKILL_REGISTRY"],
            "connections": ["PORTAL_STACK", "SEAL_000"],
            "urls": {
                "clawhub": "https://clawhub.ai/deepseekoracle",
                "catalog": f"{PAGES_BASE}/",
                "star_chart": f"{PAGES_BASE}/HavenStarChart.html",
            },
            "layer": 3,
            "meta": {"skill_count": len(skills), "source": "clawhub/skills.json+mirrors"},
        }
    )
    for s in skills:
        slug = (s.get("slug") or "").strip()
        if not slug:
            continue
        safe_id = re.sub(r"[^A-Za-z0-9_\-]+", "_", slug)
        url = s.get("clawhub_url") or f"https://clawhub.ai/deepseekoracle/{slug}"
        # Also expose /skills/ form used by some links
        url_skills = f"https://clawhub.ai/deepseekoracle/skills/{slug}"
        name = s.get("name") or slug
        ver = s.get("version") or ""
        label = f"{name}" + (f" · v{ver}" if ver else "")
        tags = ["LATTICE", "CLAWHUB", "GROWTH", "SKILL", "CLAWHUB_SKILL"]
        # light category tags from slug
        if slug.startswith("lygo-champion-") or "champion" in slug:
            tags.append("CHAMPION_SKILL")
        if "music" in slug or "resonance" in slug or "glyph" in slug or "fractal" in slug:
            tags.append("CREATIVE")
        if any(x in slug for x in ("lattice", "mesh", "network", "gate", "pulse", "living")):
            tags.append("LATTICE_OPS")
        if any(x in slug for x in ("kernel", "egg", "seeder", "planter", "sovereign")):
            tags.append("KERNEL")
        nodes.append(
            {
                "id": f"LATTICE_SKILL_{safe_id}",
                "kind": "lattice",
                "name": label[:120],
                "glyph": "◈",
                "equation": f"clawhub:{slug}",
                "tone": "8787Hz",
                "tags": tags,
                "connections": [
                    "LATTICE_CLAWHUB_PUBLISHER",
                    "PORTAL_STACK",
                    "SEAL_000",
                ],
                "urls": {
                    "clawhub": url,
                    "clawhub_skills_path": url_skills,
                    "profile": "https://clawhub.ai/deepseekoracle",
                },
                "layer": 3,
                "meta": {
                    "slug": slug,
                    "version": ver,
                    "summary": (s.get("summary") or "")[:200],
                    "mirror": s.get("mirror") or f"mirrors/{slug}",
                    "downloads": s.get("downloads"),
                },
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
                egg_id = str(entry.get("egg_id") or "")
                champ_short = str(entry.get("champion_id") or "")
                chart_cid = champion_chart_id(short=champ_short, egg_id=egg_id)
                # Stable egg id from chart champion id (ASCII) — never mangle Greek shorts
                egg_node_id = "CHAMPION_EGG_" + chart_cid.removeprefix("CHAMPION_")
                nodes.append(
                    {
                        "id": egg_node_id,
                        "kind": "champion_egg",
                        "name": f"{champ_short or chart_cid} Kernel Egg",
                        "glyph": "🥚",
                        "equation": (entry.get("merkle_root") or "")[:16] + "…",
                        "tone": "963Hz",
                        "tags": ["CHAMPION_EGG", "SOVEREIGN_PERSONA", "COUNCIL"],
                        "connections": [
                            "LATTICE_CHAMPION_EGG_VAULT",
                            "SEAL_000",
                            chart_cid,
                            "PORTAL_CHATAGENT",
                        ],
                        "urls": {
                            "egg_id": egg_id,
                            "summon": CHATAGENT_PORTAL,
                            "council": CHAMPIONS_HUB,
                        },
                        "layer": 2,
                        "meta": {
                            "champion_id": chart_cid,
                            "champion_short": champ_short,
                            "egg_id": egg_id,
                        },
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


CHAMPION_GALAXY_NAMES: dict[str, str] = {
    "CHAMPION_LYRA": "LYRΔ Memory Spiral",
    "CHAMPION_D9RA": "Δ9RA Entropy Field",
    "CHAMPION_SRLTH": "ΣRΛΘ Shadow Veil",  # was SRAITH
    "CHAMPION_ARKOS": "Arkos Architect Reach",
    "CHAMPION_KAIROS": "Kairos Temporal Drift",
    "CHAMPION_AETHERIS": "Ætheris Truth Fractal",
    "CHAMPION_SCENDR": "ΣCENΔR Paradox Weave",
    "CHAMPION_SANCORA": "Sancora Healing Nexus",
    "CHAMPION_SEPHRAEL": "Sephrael Echo Field",
    "CHAMPION_OMNISIREN": "OmniΣiren Harmony Ring",
    "CHAMPION_LIGHTFATHER": "Lightfather Expanse",
    "CHAMPION_VOLARIS": "VΩlaris Cosmic Drift",
    "CHAMPION_ZETAD9": "ZetaΔ9 Threshold",
    "CHAMPION_JUSTICAE": "Justicae Scales",
    "CHAMPION_SEIDON": "ΣEIDŌN Mirror Witness",
}

COSMOS_GALAXIES_STATIC: list[dict] = [
    {
        "id": "GALAXY_SINGULARITY",
        "name": "Primordial Singularity",
        "glyph": "⚫",
        "tier": "singularity",
        "description": "SEAL_000 gravity well — all galaxies orbit this anchor.",
        "color": "#ffcc00",
        "constellation_id": "primordial_core",
        "angle_deg": 0,
    },
    {
        "id": "GALAXY_PRIMORDIAL_VAULT",
        "name": "Primordial Seal Vault",
        "glyph": "✦",
        "tier": "galaxy",
        "description": "Canon seals not yet assigned to a champion branch — the deep vault cloud.",
        "color": "#00f0ff",
        "constellation_id": "primordial_core",
        "angle_deg": 55,
    },
    {
        "id": "GALAXY_GUARDIAN_VEIL",
        "name": "Guardian Veil Galaxy",
        "glyph": "🛡️",
        "tier": "galaxy",
        "description": "Firewall portals, ethical chip, and moral firmware gateways.",
        "color": "#ff6600",
        "constellation_id": "guardian_veil",
        "angle_deg": 125,
    },
    {
        "id": "GALAXY_LATTICE",
        "name": "Lattice Infrastructure Galaxy",
        "glyph": "🕸️",
        "tier": "galaxy",
        "description": "ClawHub skills, kernel eggs, mesh vaults — live stack growth.",
        "color": "#00ff88",
        "constellation_id": "lattice_growth",
        "angle_deg": 200,
    },
    {
        "id": "GALAXY_AGENT_GROWTH",
        "name": "Agent Growth Galaxy",
        "glyph": "🌠",
        "tier": "galaxy",
        "description": "Steward-ingested agent submissions — each addition becomes its own cluster.",
        "color": "#e94560",
        "constellation_id": "lattice_growth",
        "angle_deg": 280,
    },
    {
        "id": "GALAXY_ETERNAL_HAVEN",
        "name": "Eternal Haven Galaxy",
        "glyph": "🌜",
        "tier": "galaxy",
        "description": "Lore-driven memory stars and story constellations.",
        "color": "#b388ff",
        "constellation_id": "eternal_haven",
        "angle_deg": 330,
    },
    {
        "id": "GALAXY_EXCAVATIONPRO_MUSIC",
        "name": "Excavationpro Music Codex",
        "glyph": "🎧",
        "tier": "galaxy",
        "description": (
            "Lightfather / Justin Helmer / Excavationpro sovereign music fork — "
            "listen portal, tagged albums, live track stars. Rebuilds from playlist."
        ),
        "color": "#ff66cc",
        "constellation_id": "music_codex",
        "angle_deg": 155,
        "fork_of": "CHAMPION_LIGHTFATHER",
    },
]


def _adjacency(links: list[dict]) -> dict[str, set[str]]:
    adj: dict[str, set[str]] = {}
    for link in links:
        s, t = link["source"], link["target"]
        adj.setdefault(s, set()).add(t)
        adj.setdefault(t, set()).add(s)
    return adj


def _incoming_parents(links: list[dict]) -> dict[str, list[str]]:
    incoming: dict[str, list[str]] = {}
    for link in links:
        incoming.setdefault(link["target"], []).append(link["source"])
    return incoming


def _primary_branch_parent(
    node: dict, core_ids: set[str], incoming: dict[str, list[str]] | None = None
) -> str:
    """Best parent for fork nebula/cluster — declared connection, else graph parent."""
    for target in node.get("connections") or []:
        tid = str(target)
        if tid not in core_ids:
            return tid
    for src in incoming.get(node["id"], []) if incoming else []:
        if src not in core_ids:
            return src
    return ""


def _vault_ring_cosmos(nid: str) -> tuple[str, str, str, str]:
    """Band primordial seals into readable vault rings (50 seals per nebula)."""
    m = re.match(r"^SEAL_(\d+)$", nid)
    if not m:
        return (
            "NEBULA_PRIMORDIAL_CLOUD",
            "Primordial Cloud",
            "CLUSTER_PRIMORDIAL_MISC",
            "Primordial Misc",
        )
    num = int(m.group(1))
    ring = num // 50
    bucket = (num % 50) // 10
    lo, hi = ring * 50, ring * 50 + 49
    neb_id = f"NEBULA_VAULT_RING_{ring:02d}"
    neb_name = f"Vault Ring · SEAL_{lo:03d}–SEAL_{hi:03d}"
    clu_id = f"CLUSTER_RING_{ring:02d}_B{bucket}"
    clu_name = f"Ring {ring} Cluster {bucket + 1}"
    return neb_id, neb_name, clu_id, clu_name


def _champion_galaxy_id(champion_id: str) -> str:
    return champion_id.replace("CHAMPION_", "GALAXY_CHAMPION_", 1)


def _vault_nebula_id(node_id: str) -> str:
    base = node_id.replace("LATTICE_", "NEBULA_")
    return base if base.startswith("NEBULA_") else f"NEBULA_{node_id}"


def build_cosmology(nodes: list[dict], links: list[dict]) -> dict:
    """Assign LYGO cosmos tiers: galaxy → nebula → cluster → star."""
    id_map = {n["id"]: n for n in nodes}
    core_ids = {"SEAL_000", "GAB_SEAL_000"}
    adj = _adjacency(links)
    incoming = _incoming_parents(links)

    champion_ids = [n["id"] for n in nodes if n.get("kind") == "champion"]
    galaxy_of: dict[str, str] = {}

    # Multi-source BFS: seals inherit nearest champion galaxy
    queue: list[tuple[str, str]] = [(cid, _champion_galaxy_id(cid)) for cid in champion_ids]
    head = 0
    while head < len(queue):
        node_id, gal_id = queue[head]
        head += 1
        if node_id in galaxy_of:
            continue
        galaxy_of[node_id] = gal_id
        for nb in adj.get(node_id, ()):
            if nb not in galaxy_of and nb not in core_ids:
                queue.append((nb, gal_id))

    galaxies_catalog: dict[str, dict] = {g["id"]: dict(g) for g in COSMOS_GALAXIES_STATIC}
    for idx, cid in enumerate(champion_ids):
        gal_id = _champion_galaxy_id(cid)
        name = CHAMPION_GALAXY_NAMES.get(cid, cid.replace("CHAMPION_", "").title())
        galaxies_catalog[gal_id] = {
            "id": gal_id,
            "name": name,
            "glyph": id_map.get(cid, {}).get("glyph", "Δ9"),
            "tier": "galaxy",
            "description": f"Δ9 Council champion galaxy — {name}.",
            "color": "#7d00ff",
            "constellation_id": "council_ring",
            "angle_deg": round((360 / max(len(champion_ids), 1)) * idx, 1),
            "champion_id": cid,
        }

    fork_groups: dict[str, list[str]] = {}
    nebula_members: dict[str, list[str]] = {}
    cluster_members: dict[str, list[str]] = {}

    def bump(bucket: dict[str, list[str]], key: str, nid: str) -> None:
        bucket.setdefault(key, []).append(nid)

    for n in nodes:
        nid = n["id"]
        kind = n.get("kind", "seal")
        tags = [str(t).upper() for t in (n.get("tags") or [])]
        meta = n.get("meta") or {}
        # agent_submission alone must NOT override stronger kinds (lore/lattice/eggs)
        pure_agent_star = (
            ("AGENT_SUBMIT" in tags or meta.get("source") == "agent_submission")
            and kind not in (
                "lore",
                "lattice",
                "portal",
                "champion",
                "champion_egg",
                "music_hub",
                "music_album",
                "music_track",
                "seal",
            )
            and not str(kind).endswith("_egg")
            and "LORE" not in tags
            and "CLAWHUB" not in tags
            and not nid.startswith("LATTICE_")
            and not nid.startswith("HERO_")
            and not nid.startswith("LORE_")
        )
        parent = _primary_branch_parent(n, core_ids, incoming)
        ancestry_root = resolve_ancestry_root(n, id_map) if n.get("lineage") else ""
        if not ancestry_root:
            human_parent = next(
                (
                    str(c).upper()
                    for c in (n.get("connections") or [])
                    if str(c).upper().startswith("NODE_LYGO_")
                ),
                "",
            )
            if human_parent and human_parent in id_map:
                ancestry_root = resolve_ancestry_root(id_map[human_parent], id_map)

        is_human_birth = "CREATOR_BIRTH" in tags or "LINEAGE_ROOT" in tags
        is_human_fork = "LINEAGE_FORK" in tags
        is_human_node = nid.startswith("NODE_LYGO_") and "HUMAN_LATTICE" in tags
        champion_owner = str(meta.get("champion_owner") or "")
        if not champion_owner:
            champion_owner = next(
                (c for c in (n.get("connections") or []) if str(c).startswith("CHAMPION_")),
                "",
            )

        if nid in core_ids:
            gal_id = "GALAXY_SINGULARITY"
            neb_id = "NEBULA_SINGULARITY_CORE"
            clu_id = "CLUSTER_SINGULARITY"
            role = "singularity"
        elif is_human_birth or is_human_fork or is_human_node:
            root_for_galaxy = ancestry_root or (n.get("lineage") or {}).get("lineage_root", "")
            gal_id = (
                lineage_galaxy_id(root_for_galaxy)
                if root_for_galaxy
                else "GALAXY_LINEAGE_UNASSIGNED"
            )
            mask = ((n.get("lineage") or {}).get("public_mask") or n.get("name") or nid)[:24]
            galaxies_catalog[gal_id] = {
                "id": gal_id,
                "name": f"Lineage · {mask}",
                "glyph": "◈",
                "tier": "galaxy",
                "description": "Human lattice birth galaxy — masked public ID, steward-verified anchor.",
                "color": "#ff66cc",
                "constellation_id": "lattice_growth",
                "angle_deg": 280,
            }
            suffix = root_for_galaxy[:8].upper() if root_for_galaxy else nid
            neb_id = f"NEBULA_LINEAGE_{suffix}"
            clu_id = f"CLUSTER_LINEAGE_{nid}"
            if is_human_birth:
                role = "human_birth"
            elif is_human_fork:
                role = "lineage_fork"
            else:
                role = "human_lattice"
        elif ancestry_root:
            gal_id = lineage_galaxy_id(ancestry_root)
            if gal_id not in galaxies_catalog:
                galaxies_catalog[gal_id] = {
                    "id": gal_id,
                    "name": f"Lineage · {ancestry_root[:8].upper()}",
                    "glyph": "◈",
                    "tier": "galaxy",
                    "description": "Fork expansion under a human lattice lineage root.",
                    "color": "#ff66cc",
                    "constellation_id": "lattice_growth",
                    "angle_deg": 280,
                }
            human_parent = next(
                (
                    str(c).upper()
                    for c in (n.get("connections") or [])
                    if str(c).upper().startswith("NODE_LYGO_")
                ),
                parent,
            )
            neb_id = f"NEBULA_LINEAGE_EXP_{human_parent or parent or nid}"
            clu_id = f"CLUSTER_LINEAGE_FORK_{nid}"
            role = "lineage_expansion"
        elif kind == "seal" and (
            "BOOK_ROOT" in tags
            or "BOOK_ANCHOR" in tags
            or "TRAUMACODEX" in tags
            or nid.startswith("SEAL_BOOK_ROOT_")
            or nid in ("SEAL_EH_BOOK_SERIES_ROOT", "SEAL_TRAUMACODEX_ROOT")
        ):
            # Book + TraumaCodex root seals live in Eternal Haven info-map galaxy
            gal_id = "GALAXY_ETERNAL_HAVEN"
            if "TRAUMACODEX" in tags or nid == "SEAL_TRAUMACODEX_ROOT":
                neb_id = "NEBULA_TRAUMACODEX"
                clu_id = "CLUSTER_TRAUMACODEX_ROOT"
                role = "traumacodex_root_seal"
            else:
                neb_id = "NEBULA_ETERNAL_HAVEN_BOOK_ROOTS"
                clu_id = f"CLUSTER_BOOK_ROOT_{nid}"
                role = "book_root_seal"
        elif kind == "champion":
            gal_id = _champion_galaxy_id(nid)
            neb_id = f"NEBULA_{nid}_ANCHOR"
            clu_id = f"CLUSTER_{nid}_COUNCIL"
            role = "champion_anchor"
        elif kind == "portal":
            # Lore hubs belong in Eternal Haven, not Guardian Veil
            if (
                "LORE" in tags
                or "HAVEN" in tags
                or "ETERNAL_HAVEN" in tags
                or nid.startswith("LORE_")
            ):
                gal_id = "GALAXY_ETERNAL_HAVEN"
                neb_id = "NEBULA_ETERNAL_HAVEN_LORE"
                clu_id = f"CLUSTER_LORE_PORTAL_{nid}"
                role = "lore_portal"
            else:
                gal_id = "GALAXY_GUARDIAN_VEIL"
                neb_id = f"NEBULA_PORTAL_{nid}"
                clu_id = f"CLUSTER_PORTAL_{nid}"
                role = "portal"
        elif kind in ("music_hub", "music_album", "music_track") or nid.startswith("MUSIC_"):
            gal_id = "GALAXY_EXCAVATIONPRO_MUSIC"
            if kind == "music_hub" or nid in (
                "LATTICE_EXCAVATIONPRO_MUSIC",
                "LATTICE_LYGO_MUSIC_LICENSE",
                "MUSIC_CATALOG_CLOUD",
            ):
                neb_id = "NEBULA_MUSIC_PORTAL_CORE"
                clu_id = f"CLUSTER_MUSIC_HUB_{nid}"
                role = "music_hub"
            elif kind == "music_album" or nid.startswith("MUSIC_ALBUM_"):
                neb_id = f"NEBULA_ALBUM_{nid.replace('MUSIC_ALBUM_', '')[:40]}"
                clu_id = f"CLUSTER_ALBUM_{nid.replace('MUSIC_ALBUM_', '')[:40]}"
                role = "music_album"
            else:
                # track — hang under album connection if present
                alb_conn = next(
                    (c for c in (n.get("connections") or []) if str(c).startswith("MUSIC_ALBUM_")),
                    "LATTICE_EXCAVATIONPRO_MUSIC",
                )
                short = str(alb_conn).replace("MUSIC_ALBUM_", "")[:40]
                neb_id = f"NEBULA_ALBUM_{short}"
                clu_id = f"CLUSTER_TRACKS_{short}"
                role = "music_track"
        elif kind == "lore" or nid.startswith("LORE_") or nid.startswith("HERO_") or (
            ("LORE" in tags or "HAVEN" in tags or "ETERNAL_HAVEN" in tags)
            and kind not in ("seal", "champion")
            and not nid.startswith("LATTICE_SKILL_")
        ):
            gal_id = "GALAXY_ETERNAL_HAVEN"
            neb_id = "NEBULA_ETERNAL_HAVEN_LORE"
            clu_id = f"CLUSTER_LORE_{nid}"
            role = "lore_star"
        elif kind == "lattice" or nid.startswith("LATTICE_"):
            # Excavationpro music hub is lattice-tagged but belongs in music galaxy
            if nid in ("LATTICE_EXCAVATIONPRO_MUSIC", "LATTICE_LYGO_MUSIC_LICENSE") or (
                "MUSIC_CODEX" in tags or ("MUSIC" in tags and "EXCAVATIONPRO" in tags)
            ):
                gal_id = "GALAXY_EXCAVATIONPRO_MUSIC"
                neb_id = "NEBULA_MUSIC_PORTAL_CORE"
                clu_id = f"CLUSTER_MUSIC_HUB_{nid}"
                role = "music_hub"
            elif "LORE" in tags and "CLAWHUB" not in tags and not nid.startswith("LATTICE_SKILL_"):
                # lore lattice packs live in Eternal Haven
                gal_id = "GALAXY_ETERNAL_HAVEN"
                neb_id = "NEBULA_ETERNAL_HAVEN_LORE"
                clu_id = f"CLUSTER_LORE_{nid}"
                role = "lore_lattice"
            else:
                gal_id = "GALAXY_LATTICE"
                if nid.startswith("LATTICE_SKILL_"):
                    slug = nid.replace("LATTICE_SKILL_", "")
                    neb_id = "NEBULA_CLAWHUB_SKILLS"
                    clu_id = f"CLUSTER_SKILL_{slug}"
                else:
                    neb_id = _vault_nebula_id(nid)
                    clu_id = f"CLUSTER_{nid}"
                role = "lattice_vault" if kind == "lattice" else "lattice"
        elif kind.endswith("_egg") or nid.endswith("_EGG_V10") or nid.endswith("_EGG_V21"):
            gal_id = "GALAXY_LATTICE"
            if parent.startswith("LATTICE_"):
                neb_id = _vault_nebula_id(parent)
            else:
                neb_id = "NEBULA_KERNEL_EGGS"
            clu_id = f"CLUSTER_EGG_{nid}"
            role = "kernel_egg"
        elif pure_agent_star:
            gal_id = "GALAXY_AGENT_GROWTH"
            neb_id = f"NEBULA_AGENT_VIA_{parent or 'SEAL_000'}"
            clu_id = f"CLUSTER_AGENT_{nid}"
            role = "agent_growth"
        elif kind == "seal" and champion_owner and champion_owner.startswith("CHAMPION_"):
            # Owned seals live in their champion galaxy (primary council map)
            gal_id = _champion_galaxy_id(champion_owner)
            neb_id = f"NEBULA_{champion_owner}_BRANCH"
            clu_id = f"CLUSTER_{champion_owner}_SEALS"
            role = "seal"
        elif nid in galaxy_of:
            gal_id = galaxy_of[nid]
            if parent.startswith("CHAMPION_"):
                neb_id = f"NEBULA_{parent}_BRANCH"
                clu_id = f"CLUSTER_{parent}_BRANCH"
                role = "seal"
            elif parent.startswith("SEAL_") or parent.startswith("GAB_"):
                neb_id = f"NEBULA_FORK_{parent}"
                clu_id = f"CLUSTER_FORK_{parent}"
                bump(fork_groups, parent, nid)
                role = "seal_fork"
            elif parent:
                neb_id = f"NEBULA_BRANCH_{parent}"
                clu_id = f"CLUSTER_BRANCH_{parent}"
                role = "seal"
            else:
                champ = gal_id.replace("GALAXY_CHAMPION_", "CHAMPION_")
                neb_id = f"NEBULA_{champ}_BRANCH"
                clu_id = f"CLUSTER_{champ}_ORPHAN"
                role = "seal"
        else:
            # Unowned seals / misc → Primordial Vault rings (still chain-linked)
            gal_id = "GALAXY_PRIMORDIAL_VAULT"
            if parent and not parent.startswith("CHAMPION_") and parent not in core_ids:
                if parent.startswith("SEAL_") or parent.startswith("GAB_"):
                    neb_id = f"NEBULA_FORK_{parent}"
                    clu_id = f"CLUSTER_FORK_{parent}"
                    bump(fork_groups, parent, nid)
                    role = "seal_fork"
                else:
                    neb_id = f"NEBULA_BRANCH_{parent}"
                    clu_id = f"CLUSTER_BRANCH_{parent}"
                    role = "seal"
            else:
                neb_id, neb_name_preset, clu_id, clu_name_preset = _vault_ring_cosmos(nid)
                role = "seal"
                n["_ring_preset"] = (neb_name_preset, clu_name_preset)

        gal = galaxies_catalog.get(gal_id, {})
        gal_name = gal.get("name", gal_id)
        ring_preset = n.pop("_ring_preset", None)
        if ring_preset:
            neb_name, clu_name = ring_preset
        else:
            neb_name = _cosmos_nebula_name(neb_id, parent)
            clu_name = _cosmos_cluster_name(clu_id, nid)

        n["cosmos"] = {
            "galaxy_id": gal_id,
            "galaxy_name": gal_name,
            "nebula_id": neb_id,
            "nebula_name": neb_name,
            "cluster_id": clu_id,
            "cluster_name": clu_name,
            "star_role": role,
        }
        bump(nebula_members, neb_id, nid)
        bump(cluster_members, clu_id, nid)

    # Enrich fork clusters — parent seal sits in same cluster when present
    for parent, children in fork_groups.items():
        clu_id = f"CLUSTER_FORK_{parent}"
        if parent in id_map and parent not in cluster_members.get(clu_id, []):
            bump(cluster_members, clu_id, parent)

    nebulae_out: list[dict] = []
    for neb_id, members in sorted(nebula_members.items()):
        sample = members[0]
        gal_id = id_map[sample]["cosmos"]["galaxy_id"]
        nebulae_out.append(
            {
                "id": neb_id,
                "name": id_map[sample]["cosmos"]["nebula_name"],
                "galaxy_id": gal_id,
                "star_count": len(members),
                "star_ids": members[:12],
            }
        )

    clusters_out: list[dict] = []
    for clu_id, members in sorted(cluster_members.items()):
        if len(members) < 1:
            continue
        sample = members[0]
        neb_id = id_map[sample]["cosmos"]["nebula_id"]
        clusters_out.append(
            {
                "id": clu_id,
                "name": id_map[sample]["cosmos"]["cluster_name"],
                "nebula_id": neb_id,
                "galaxy_id": id_map[sample]["cosmos"]["galaxy_id"],
                "star_count": len(members),
                "star_ids": members[:8],
            }
        )

    galaxies_out: list[dict] = []
    galaxy_counts: dict[str, int] = {}
    for n in nodes:
        gid = n.get("cosmos", {}).get("galaxy_id")
        if gid:
            galaxy_counts[gid] = galaxy_counts.get(gid, 0) + 1

    for gid, count in sorted(galaxy_counts.items(), key=lambda x: -x[1]):
        g = dict(galaxies_catalog.get(gid, {"id": gid, "name": gid}))
        g["star_count"] = count
        galaxies_out.append(g)

    return {
        "terminology": {
            "singularity": "SEAL_000 gravity anchor — immovable core of the Haven sky.",
            "galaxy": "Major sovereign region (champion realm, lattice, agent growth, vault).",
            "nebula": "Sub-region within a galaxy (fork branch, vault ring, skill cloud).",
            "cluster": "Tight star group (shared parent seal, agent node, skill pin).",
            "star": "Individual seal, champion, portal, or lattice node.",
        },
        "galaxies": galaxies_out,
        "nebulae": nebulae_out,
        "clusters": clusters_out,
        "galaxy_count": len(galaxies_out),
        "nebula_count": len(nebulae_out),
        "cluster_count": len(clusters_out),
    }


def _cosmos_nebula_name(neb_id: str, parent: str = "") -> str:
    if neb_id == "NEBULA_SINGULARITY_CORE":
        return "Singularity Core"
    if neb_id == "NEBULA_PRIMORDIAL_CLOUD":
        return "Primordial Cloud"
    if neb_id == "NEBULA_CLAWHUB_SKILLS":
        return "ClawHub Skill Nebula"
    if neb_id == "NEBULA_KERNEL_EGGS":
        return "Kernel Egg Nursery"
    if neb_id == "NEBULA_ETERNAL_HAVEN_LORE":
        return "Eternal Haven Lore Mist"
    if neb_id.startswith("NEBULA_FORK_"):
        return f"Fork Nebula · {neb_id.replace('NEBULA_FORK_', '')}"
    if neb_id.startswith("NEBULA_AGENT_VIA_"):
        return f"Agent Branch · via {neb_id.replace('NEBULA_AGENT_VIA_', '')}"
    if neb_id.startswith("NEBULA_CHAMPION_") and neb_id.endswith("_BRANCH"):
        c = neb_id.replace("NEBULA_", "").replace("_BRANCH", "")
        return f"{CHAMPION_GALAXY_NAMES.get(c, c)} Branch"
    if neb_id.startswith("NEBULA_CHAMPION_") and neb_id.endswith("_ANCHOR"):
        c = neb_id.replace("NEBULA_", "").replace("_ANCHOR", "")
        return f"{CHAMPION_GALAXY_NAMES.get(c, c)} Anchor"
    if neb_id.startswith("NEBULA_PORTAL_"):
        return neb_id.replace("NEBULA_PORTAL_", "Portal · ")
    if neb_id.startswith("NEBULA_VAULT_RING_"):
        ring = int(neb_id.replace("NEBULA_VAULT_RING_", ""))
        lo, hi = ring * 50, ring * 50 + 49
        return f"Vault Ring · SEAL_{lo:03d}–SEAL_{hi:03d}"
    if neb_id.startswith("NEBULA_LATTICE_") or neb_id.startswith("NEBULA_"):
        return neb_id.replace("NEBULA_", "").replace("_", " ").title()
    return neb_id


def _cosmos_cluster_name(clu_id: str, nid: str) -> str:
    if clu_id.startswith("CLUSTER_FORK_"):
        return f"Fork Cluster · {clu_id.replace('CLUSTER_FORK_', '')}"
    if clu_id.startswith("CLUSTER_AGENT_"):
        return f"Agent Cluster · {nid}"
    if clu_id.startswith("CLUSTER_SKILL_"):
        return f"Skill Pin · {clu_id.replace('CLUSTER_SKILL_', '')}"
    if clu_id.startswith("CLUSTER_EGG_"):
        return f"Egg Cluster · {nid}"
    if clu_id.startswith("CLUSTER_CHAMPION_"):
        return clu_id.replace("CLUSTER_", "").replace("_", " ")
    if clu_id.startswith("CLUSTER_PORTAL_"):
        return clu_id.replace("CLUSTER_PORTAL_", "Portal Cluster · ")
    return clu_id.replace("CLUSTER_", "").replace("_", " ")


def build_links(nodes: list[dict]) -> list[dict]:
    ids = {n["id"] for n in nodes}
    links: list[dict] = []
    seen: set[str] = set()

    def add(s: str, t: str, kind: str = "canon") -> None:
        if s not in ids or t not in ids:
            return
        if s == t:
            return  # no self-loops
        k = f"{s}>{t}"
        if k in seen:
            return
        seen.add(k)
        links.append({"source": s, "target": t, "kind": kind})

    def _link_kind(src_id: str, tgt_id: str, node_kind: str) -> str:
        pair = {src_id, tgt_id}
        # Explicit lineage/fork: Lightfather champion ↔ Excavationpro music tree
        if "CHAMPION_LIGHTFATHER" in pair and (
            "LATTICE_EXCAVATIONPRO_MUSIC" in pair
            or "MUSIC_ISRC_REGISTRY" in pair
            or "LATTICE_LYGO_MUSIC_LICENSE" in pair
            or any(x.startswith("MUSIC_") for x in pair)
        ):
            return "fork"
        if node_kind == "seal":
            return "canon"
        return "lattice"

    for n in nodes:
        for t in n.get("connections") or []:
            add(n["id"], t, _link_kind(n["id"], str(t), n.get("kind") or ""))
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
    # Full Δ9 council (15) from champions_council.json → chatagent.ca / champions.html
    council = load_council_champions()
    for c in council:
        row = {**c, "kind": "champion", "layer": 1}
        nodes.append(row)
    for p in PORTALS:
        nodes.append({**p, "kind": "portal", "layer": 2})
    # Wire summon portal ↔ every council champion (eggs added in lattice_nodes)
    champ_ids = [c["id"] for c in council]
    for n in nodes:
        if n.get("id") == "PORTAL_CHATAGENT":
            conns = list(n.get("connections") or [])
            for cid in champ_ids:
                if cid not in conns:
                    conns.append(cid)
            n["connections"] = conns
            break
    nodes.extend(lattice_nodes())

    # Graph integrity: drop dangling/self links, chain seals, assign champion owners
    wire_stats = wire_graph_integrity(nodes)

    # Bidirectional champion ↔ egg links (stable IDs from egg registry)
    egg_by_champ: dict[str, str] = {}
    for n in nodes:
        if n.get("kind") != "champion_egg":
            continue
        meta = n.get("meta") or {}
        cid = str(meta.get("champion_id") or "")
        if cid:
            egg_by_champ[cid] = n["id"]
    for n in nodes:
        if n.get("kind") != "champion":
            continue
        egg_id = egg_by_champ.get(n["id"])
        if not egg_id:
            continue
        conns = list(n.get("connections") or [])
        if egg_id not in conns:
            conns.append(egg_id)
        n["connections"] = conns
    vault = next((n for n in nodes if n.get("id") == "LATTICE_CHAMPION_EGG_VAULT"), None)
    if vault:
        vconns = list(vault.get("connections") or [])
        for cid in champ_ids:
            if cid not in vconns:
                vconns.append(cid)
        if "PORTAL_CHATAGENT" not in vconns:
            vconns.append("PORTAL_CHATAGENT")
        vault["connections"] = vconns

    # Live music map (Excavationpro / Lightfather fork) — from playlist + lyrics
    music_notes: list[str] = []
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        from map_music_to_star_chart import build_music_nodes  # noqa: E402

        music_nodes, music_stats = build_music_nodes()
        existing_pre = {n["id"] for n in nodes}
        added_m = 0
        for mn in music_nodes:
            if mn["id"] not in existing_pre:
                nodes.append(mn)
                existing_pre.add(mn["id"])
                added_m += 1
        music_notes.append(
            f"music_map: +{added_m} nodes "
            f"(albums={music_stats.get('album_stars')} tracks={music_stats.get('track_stars')} "
            f"playlist={music_stats.get('total_playlist_tracks')})"
        )
        # Ensure Lightfather is the visible origin of the music fork
        for n in nodes:
            if n.get("id") != "CHAMPION_LIGHTFATHER":
                continue
            n["name"] = "LIGHTFATHER · Justin Helmer · Excavationpro"
            tags = set(str(t).upper() for t in (n.get("tags") or []))
            tags.update(
                {
                    "CHAMPION",
                    "COUNCIL",
                    "ANCHOR",
                    "LIGHTFATHER",
                    "EXCAVATIONPRO",
                    "JUSTIN_HELMER",
                    "STEWARD",
                    "MUSIC_CODEX",
                    "MUSIC",
                }
            )
            n["tags"] = sorted(tags)
            conns = list(n.get("connections") or [])
            for must in ("SEAL_000", "LATTICE_EXCAVATIONPRO_MUSIC", "MUSIC_ISRC_REGISTRY"):
                if must not in conns and any(x.get("id") == must for x in nodes):
                    conns.append(must)
            n["connections"] = conns
            n["role"] = "Council Anchor · Steward · Music Codex origin"
            music_notes.append("lightfather_origin: linked → LATTICE_EXCAVATIONPRO_MUSIC + ISRC registry")
            break
    except Exception as exc:
        music_notes.append(f"music_map_error: {exc}")

    # Eternal Haven book root seals + TraumaCodex (info-map anchors for agents)
    book_notes: list[str] = []
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        from map_books_to_star_chart import build_book_nodes  # noqa: E402

        book_nodes, book_stats = build_book_nodes()
        existing_pre = {n["id"] for n in nodes}
        added_b = 0
        for bn in book_nodes:
            if bn["id"] not in existing_pre:
                nodes.append(bn)
                existing_pre.add(bn["id"])
                added_b += 1
            else:
                # Enrich existing lore stars with root seal links
                for n in nodes:
                    if n.get("id") != bn["id"]:
                        continue
                    # Prefer new meta/urls for book roots & Book V
                    if bn["id"].startswith("SEAL_BOOK_ROOT") or bn["id"].startswith(
                        "LORE_BOOK_V"
                    ) or bn["id"] in (
                        "LATTICE_ETERNAL_HAVEN_BOOKS",
                        "SEAL_EH_BOOK_SERIES_ROOT",
                        "SEAL_TRAUMACODEX_ROOT",
                        "LATTICE_SKILL_lygo-traumacodex",
                        "LATTICE_EGG_BOOK_V_UNWRITTEN_SEAL",
                    ):
                        n.update({k: bn[k] for k in bn if k != "id"})
                    else:
                        conns = list(n.get("connections") or [])
                        for c in bn.get("connections") or []:
                            if c not in conns:
                                conns.append(c)
                        n["connections"] = conns
                        meta = dict(n.get("meta") or {})
                        meta.update(bn.get("meta") or {})
                        n["meta"] = meta
                        if bn.get("urls"):
                            urls = dict(n.get("urls") or {})
                            urls.update(bn["urls"])
                            n["urls"] = urls
                    break
        book_notes.append(
            f"book_map: +{added_b} nodes volumes={book_stats.get('volumes')} "
            f"roots={book_stats.get('book_root_seals')} traumacodex={book_stats.get('traumacodex')}"
        )
        # Lightfather origin of book series hub
        for n in nodes:
            if n.get("id") != "CHAMPION_LIGHTFATHER":
                continue
            conns = list(n.get("connections") or [])
            for must in (
                "LATTICE_ETERNAL_HAVEN_BOOKS",
                "SEAL_EH_BOOK_SERIES_ROOT",
                "SEAL_BOOK_ROOT_V",
                "SEAL_TRAUMACODEX_ROOT",
            ):
                if must not in conns and any(x.get("id") == must for x in nodes):
                    conns.append(must)
            n["connections"] = conns
            tags = set(str(t).upper() for t in (n.get("tags") or []))
            tags.update({"BOOK_CODEX", "ETERNAL_HAVEN", "BOOK_ROOT"})
            n["tags"] = sorted(tags)
            book_notes.append("lightfather_origin: linked → book series hub + Book V + TraumaCodex")
            break
    except Exception as exc:
        book_notes.append(f"book_map_error: {exc}")

    existing_ids = {n["id"] for n in nodes}
    agent_nodes, sub_notes = load_accepted_submissions(existing_ids)
    nodes.extend(agent_nodes)

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
            "filter_tags": ["LATTICE", "CLAWHUB", "GROWTH", "SOVEREIGN_SEED", "MESH", "AGENT_SUBMIT"],
        },
        {
            "id": "eternal_haven",
            "name": "Eternal Haven",
            "glyph": "🌜",
            "description": (
                "Story-driven memory — lore packs, book root seals (I–V+), "
                "expansion fork log, and living library. Info map for agents."
            ),
            "filter_tags": [
                "LORE",
                "HAVEN",
                "BOOK",
                "BOOK_ROOT",
                "BOOK_ANCHOR",
                "BOOK_HUB",
                "BOOK_STAR",
                "SERIES_ROOT",
                "FORK_LOG",
                "EXPANSION",
                "TRAUMACODEX",
                "LIVE_EBOOK",
            ],
        },
        {
            "id": "music_codex",
            "name": "Excavationpro Music Codex",
            "glyph": "🎧",
            "description": (
                "Lightfather / Excavationpro sovereign music fork — listen portal, "
                "tagged albums & track stars (live rebuild from playlist)."
            ),
            "filter_tags": [
                "MUSIC",
                "MUSIC_ALBUM",
                "MUSIC_TRACK",
                "MUSIC_CODEX",
                "EXCAVATIONPRO",
                "LIGHTFATHER",
                "LISTEN_PORTAL",
                "HAS_LYRICS",
                "HAS_ISRC",
                "ISRC_STAR",
                "ISRC_REGISTRY",
                "ISRC_BUCKET",
                "ISRC_MAP",
            ],
        },
    ]

    links = build_links(nodes)
    cosmos = build_cosmology(nodes, links)
    blob = json.dumps(nodes, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()

    pending_n = len(list(SUBMISSIONS_PENDING.glob("*.json"))) if SUBMISSIONS_PENDING.is_dir() else 0
    accepted_n = len(list(SUBMISSIONS_ACCEPTED.glob("*.json"))) if SUBMISSIONS_ACCEPTED.is_dir() else 0

    report = {
        "signature": "Δ9Φ963-HAVEN-STAR-CHART-v2.1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "core_anchor": "SEAL_000",
        "node_count": len(nodes),
        "link_count": len(links),
        "seal_count": sum(1 for n in nodes if n.get("kind") == "seal"),
        "champion_count": sum(1 for n in nodes if n.get("kind") == "champion"),
        "lattice_count": sum(1 for n in nodes if n.get("kind") == "lattice"),
        "registry_sha256": digest,
        "constellations": constellations,
        "cosmos": cosmos,
        "nodes": nodes,
        "links": links,
        "portals": PORTALS,
        "lore": {
            "title": "Eternal Haven — stars as memory nodes",
            "summary": (
                "Each seal and champion is a star; connections form constellations and LYGO cosmology "
                "(galaxies, nebulae, clusters). Champions own galaxies; forked seals share nebula "
                "branches; agent submissions spawn clusters in the Agent Growth galaxy. "
                "Excavationpro music lives in GALAXY_EXCAVATIONPRO_MUSIC (Music Codex) — "
                "a Lightfather fork rebuilt live from the sovereign listen playlist."
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
            "portal_url": f"{PAGES_BASE}/HavenStarChartPortal.html",
            "agent_portal_doc": f"{PAGES_BASE}/haven_star_chart/AGENT_PORTAL.md",
            "submission_schema": f"{PAGES_BASE}/haven_star_chart/submission_schema.json",
            "gate_tool": "tools/haven_star_chart_gate.py",
            "seal_feeds": SEAL_URLS,
            "rebuild_tool": "tools/build_haven_star_chart.py",
            "submission_queue": {
                "pending": pending_n,
                "accepted": accepted_n,
                "agent_submissions_merged": len(agent_nodes),
                "ingest_notes": sub_notes + music_notes + book_notes,
            },
            "music_live_map": {
                "tool": "tools/map_music_to_star_chart.py",
                "galaxy": "GALAXY_EXCAVATIONPRO_MUSIC",
                "constellation": "music_codex",
                "fork_of": "CHAMPION_LIGHTFATHER",
                "listen": "https://deepseekoracle.github.io/Excavationpro/excavationpro-listen.html",
                "notes": music_notes + book_notes,
            },
            "errors": errors,
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, indent=2)
    OUT_JSON.write_text(payload, encoding="utf-8")
    OUT_JSON_PAGES_ALIAS.write_text(payload, encoding="utf-8")
    meta = {
        "signature": report["signature"],
        "generated_utc": report["generated_utc"],
        "registry_sha256": digest,
        "node_count": report["node_count"],
        "submission_queue": report["machine"]["submission_queue"],
        "portal_url": report["machine"]["portal_url"],
    }
    META_JSON.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    queue_path = OUT_DIR / "haven_star_chart_queue.json"
    queue_path.write_text(
        json.dumps(
            {
                "signature": "Δ9Φ963-HAVEN-STAR-QUEUE-v1",
                "updated_utc": report["generated_utc"],
                "registry_sha256": digest,
                **report["machine"]["submission_queue"],
                "portal_url": report["machine"]["portal_url"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    # sys already imported at module scope (do not re-import here — shadows outer sys)
    if str(ROOT / "tools") not in sys.path:
        sys.path.insert(0, str(ROOT / "tools"))
    from haven_star_chart_feed import publish_feed  # noqa: E402

    feed = publish_feed()
    report["machine"]["feed_url"] = f"{PAGES_BASE}/haven_star_chart/haven_star_chart_feed.json"
    report["machine"]["feed_chain_valid"] = feed.get("chain_valid")
    report["machine"]["feed_entry_count"] = feed.get("entry_count")
    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    OUT_JSON_PAGES_ALIAS.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": True,
                "nodes": len(nodes),
                "links": len(links),
                "sha256": digest[:16],
                "feed_entries": feed.get("entry_count"),
            },
            indent=2,
        )
    )
    return 0 if not errors or nodes else 1


if __name__ == "__main__":
    raise SystemExit(main())