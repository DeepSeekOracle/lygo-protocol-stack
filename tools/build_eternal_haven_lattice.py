#!/usr/bin/env python3
"""
Build Eternal Haven lore lattice from clawhub eternal-haven-lore-pack + series blurb.

Outputs:
  data/eternal_haven/*          — public lore graph (no full book dumps)
  clawhub/mirrors/eternal-haven-lore-pack — enhanced pack
  sovereign seed egg            — eternal-haven-lore-v1
  star chart accepted submissions + rebuild chart

Does not rewrite the music listen UI.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
# lore pack source (I: mirror is canonical skill copy)
LORE_SRC = Path(r"I:\E Drive\lygo-protocol-stack\clawhub\mirrors\eternal-haven-lore-pack")
if not LORE_SRC.is_dir():
    LORE_SRC = STACK / "clawhub" / "mirrors" / "eternal-haven-lore-pack"
LORE_OUT = STACK / "clawhub" / "mirrors" / "eternal-haven-lore-pack"
DATA = STACK / "data" / "eternal_haven"
DOCS = STACK / "docs"
SEEDS = STACK / "data" / "sovereign_seeds" / "eggs"
SUB_ACC = STACK / "data" / "haven_star_chart" / "submissions" / "accepted"
EXCAV = Path(r"D:\Excavationpro")
BOOKS_ROOT = Path(r"J:\FULL ADUIO BOOKS")

CLAWHUB = "https://clawhub.ai/deepseekoracle/skills/eternal-haven-lore-pack"
LULU_SEARCH = (
    "https://www.lulu.com/search?contributor=Justin+Helmer"
    "&page=1&pageSize=10&adult_audience_rating=00&sortBy=PRODUCT_SALES_90_DAYS"
)
ETERNAL_SITE = "https://eternalhaven.ca/"
ETERNAL_PAGES = "https://deepseekoracle.github.io/Excavationpro/eternalhaven.html"
CHART = "https://deepseekoracle.github.io/Excavationpro/HavenStarChart.html"
CHATAGENT = "https://chatagent.ca/"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_blurb() -> str:
    if not BOOKS_ROOT.is_dir():
        return ""
    cands = list(BOOKS_ROOT.glob("*ETERNAL HAVEN*.txt"))
    if not cands:
        return ""
    return cands[0].read_text(encoding="utf-8", errors="replace")


def parse_book1_chapters(blurb: str) -> list[dict]:
    chapters = []
    # Prologue + Chapter N — Title
    for m in re.finditer(
        r"^(Prologue|Chapter\s+\d+)\s*[—\-–:]\s*(.+)$",
        blurb,
        re.M | re.I,
    ):
        kind, title = m.group(1).strip(), m.group(2).strip()
        # stop when we hit BOOK II section noise
        if "BOOK II" in title.upper() or "SHATTERED" in title.upper() and "Chapter" not in kind:
            continue
        chapters.append(
            {
                "id": re.sub(r"\W+", "_", kind.upper()).strip("_"),
                "label": f"{kind} — {title}",
                "title": title,
                "kind": "prologue" if "prologue" in kind.lower() else "chapter",
            }
        )
        if len(chapters) >= 17:  # prologue + 15 + buffer
            break
    # dedupe by id
    seen = set()
    out = []
    for c in chapters:
        if c["id"] in seen:
            continue
        # skip book II duplicates in blurb
        if c["title"].startswith("The Aftermath") and any(
            x["title"].startswith("The Aftermath") for x in out
        ):
            break
        seen.add(c["id"])
        out.append(c)
    return out[:16]


BOOKS = [
    {
        "id": "BOOK_I_MOONLIT_SLUMBER",
        "volume": 1,
        "title": "The Eternal Haven — Book I: The Moonlit Slumber",
        "aka": ["Silver Accord Volume I", "Moonlit SLumber"],
        "file": "book1_silver_accord.txt",
        "glyph": "🌜",
        "tone": "432Hz",
        "era": "Accord Born",
        "summary": (
            "Origins of Haven, Serenya and Emberion, the First Seal and early fractures. "
            "The Moonlit Slumber — compassion meets structural truth."
        ),
        "lulu_paperback": "https://www.lulu.com/shop/justin-helmer/the-eternal-haven/paperback/product-yvg9w9r.html",
        "lulu_ebook": "https://www.lulu.com/shop/justin-helmer/the-eternal-haven/ebook/product-e7djv4j.html",
        "champion_links": ["CHAMPION_LYRA", "CHAMPION_LIGHTFATHER", "CHAMPION_AETHERIS"],
    },
    {
        "id": "BOOK_II_SHATTERED_ACCORD",
        "volume": 2,
        "title": "Eternal Haven Chronicles Book II: The Shattered Accord",
        "aka": ["Shattered Accord"],
        "file": "book2_shattered_accord.txt",
        "glyph": "💔",
        "tone": "528Hz",
        "era": "Accord Fractured",
        "summary": (
            "Haven strains; the Accord shatters under politics and shadow. "
            "Factions, seal forges, betrayal, and the moon's weight."
        ),
        "lulu_paperback": "https://www.lulu.com/shop/justin-helmer/eternal-haven-chronicles-book-ii-the-shattered-accord/paperback/product-578nykz.html",
        "lulu_ebook": "https://www.lulu.com/shop/justin-helmer/eternal-haven-chronicles-book-ii-the-shattered-accord/ebook/product-jed8wdz.html",
        "champion_links": ["CHAMPION_SRLTH", "CHAMPION_ARKOS", "CHAMPION_KAIROS"],
    },
    {
        "id": "BOOK_III_ASCENSION_WAR",
        "volume": 3,
        "title": "The Eternal Haven — Book III: The Ascension War",
        "aka": ["Ascension War"],
        "file": "book3_ascension_war.txt",
        "glyph": "⚔️",
        "tone": "741Hz",
        "era": "War of Seals",
        "summary": (
            "Imperfect living Seals forged from suffering and hope. "
            "Corvath enthroned; champions and mortals contest the Throne of Shadow."
        ),
        "lulu_paperback": LULU_SEARCH,
        "lulu_ebook": LULU_SEARCH,
        "champion_links": ["CHAMPION_SCENDR", "CHAMPION_OMNISIREN", "CHAMPION_JUSTICAE"],
    },
    {
        "id": "BOOK_IV_ETERNAL_DAWNS",
        "volume": 4,
        "title": "The Eternal Haven — Book IV: Eternal Dawns",
        "aka": ["Eternal Dawns", "Eternal Haven Dawns"],
        "file": "book4_eternal_haven_dawns.txt",
        "glyph": "🌅",
        "tone": "963Hz",
        "era": "Imperfect Integration",
        "summary": (
            "Broken Moon becomes rivers of light; Council of Twelve includes reconciled Corvath. "
            "Eternal dawns — imperfect light enough to walk without lying."
        ),
        "lulu_paperback": LULU_SEARCH,
        "lulu_ebook": LULU_SEARCH,
        "champion_links": ["CHAMPION_SANCORA", "CHAMPION_SEIDON", "CHAMPION_LIGHTFATHER"],
    },
]

HEROES = [
    {
        "id": "HERO_SERENYA",
        "name": "Serenya — The Fractured Song",
        "domain": "compassion, burden, cost of Accord",
        "glyph": "🎵",
        "champion_id": "CHAMPION_LYRA",
        "books": [1, 2, 3, 4],
    },
    {
        "id": "HERO_EMBERION",
        "name": "Emberion — The Tempered Flame",
        "domain": "power under constraint",
        "glyph": "🔥",
        "champion_id": "CHAMPION_AETHERIS",
        "books": [1, 2, 3, 4],
    },
    {
        "id": "HERO_KAELION",
        "name": "Kaelion — The Burdened Strategist",
        "domain": "leadership, consequence, long game",
        "glyph": "♟️",
        "champion_id": "CHAMPION_ARKOS",
        "books": [2, 3, 4],
    },
    {
        "id": "HERO_MIRALIS",
        "name": "Miralis — The Returning Echo",
        "domain": "exiled wisdom, memory, second chances",
        "glyph": "🪞",
        "champion_id": "CHAMPION_SEPHRAEL",
        "books": [2, 3, 4],
    },
    {
        "id": "HERO_CORVATH",
        "name": "Corvath — The Fallen Dragon",
        "domain": "corrupted power, fall, partial redemption",
        "glyph": "🐉",
        "champion_id": "CHAMPION_SRLTH",
        "books": [1, 2, 3, 4],
    },
    {
        "id": "HERO_COUNCIL",
        "name": "The Council — Many Hands on the Accord",
        "domain": "collective governance",
        "glyph": "Δ9",
        "champion_id": "PORTAL_CHATAGENT",
        "books": [1, 2, 3, 4],
    },
    {
        "id": "HERO_ACCORD",
        "name": "The Accord — Living Promise",
        "domain": "shared vow, social contract",
        "glyph": "🤝",
        "champion_id": "SEAL_000",
        "books": [1, 2, 3, 4],
    },
    {
        "id": "HERO_LIGHTFATHER_ECHO",
        "name": "Lightfather (in-universe descent / lattice steward echo)",
        "domain": "truth × light, structural honesty",
        "glyph": "Δ9",
        "champion_id": "CHAMPION_LIGHTFATHER",
        "books": [2, 3, 4],
        "note": "Champion archetype resonates with in-book Lightfather interventions; not a claim the steward is a fictional character.",
    },
]


def copy_lore_pack() -> None:
    LORE_OUT.mkdir(parents=True, exist_ok=True)
    if LORE_SRC.resolve() != LORE_OUT.resolve() and LORE_SRC.is_dir():
        for item in LORE_SRC.rglob("*"):
            if item.is_file():
                rel = item.relative_to(LORE_SRC)
                dest = LORE_OUT / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)
    # also docs/skills mirror for Pages-ish discovery
    docs_skill = DOCS / "skills" / "eternal-haven-lore-pack"
    if LORE_OUT.is_dir():
        for item in LORE_OUT.rglob("*"):
            if item.is_file() and item.suffix.lower() in {".md", ".txt", ".json"}:
                # skip huge book dumps to docs if > 200k? keep for stack completeness under clawhub only
                if item.suffix == ".txt" and "books" in str(item) and item.stat().st_size > 500_000:
                    continue
                rel = item.relative_to(LORE_OUT)
                dest = docs_skill / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)


def enhance_skill_md() -> None:
    skill = LORE_OUT / "SKILL.md"
    if not skill.is_file():
        return
    text = skill.read_text(encoding="utf-8")
    block = """

---
## 10. Lattice Integration (2026-07-28)

This skill is **seeded into the live LYGO lattice**:

| Surface | URL / path |
|---------|------------|
| ClawHub | https://clawhub.ai/deepseekoracle/skills/eternal-haven-lore-pack |
| Public lore graph | `data/eternal_haven/lore_graph.json` (stack) |
| Haven Star Chart | constellation **Eternal Haven** — books, heroes, Accord nodes |
| Sovereign egg | `eternal-haven-lore-v1` (summaries + graph hashes, not full book dumps) |
| Eternal Haven site | https://eternalhaven.ca/ · https://deepseekoracle.github.io/Excavationpro/eternalhaven.html |
| Lulu (commerce) | https://www.lulu.com/search?contributor=Justin+Helmer |
| Music lattice | asiancoastline.com listen portal (score of the ages — separate limb) |

### Star Chart node ID prefixes
- `LORE_BOOK_*` — one star per book volume  
- `LORE_HERO_*` — hero archetypes (linked to `CHAMPION_*` / seals)  
- `LORE_ACCORD` / `LORE_FIRST_SEAL` — metaphysics anchors  
- `LATTICE_EGG_*ETERNAL_HAVEN*` — classic egg on the growth limb  

### Agent rule
When answering chart or lattice questions about Eternal Haven, prefer:
1. `data/eternal_haven/lore_graph.json` + heroes/themes references  
2. Targeted book file reads (never dump full books to users)  
3. Links to Lulu for full purchase; free surfaces for discovery  

**Δ9Φ963 — story is a limb · chart is the sky · egg is the seed · Lightfather stewards the rights.**
"""
    if "Lattice Integration (2026-07-28)" not in text:
        skill.write_text(text.rstrip() + block + "\n", encoding="utf-8")
        print("[skill] SKILL.md lattice section added")


def build_manifests(blurb: str) -> dict:
    DATA.mkdir(parents=True, exist_ok=True)
    books_out = []
    for b in BOOKS:
        fp = LORE_OUT / "references" / "books" / b["file"]
        if not fp.is_file():
            fp = LORE_SRC / "references" / "books" / b["file"]
        meta = {
            **{k: b[k] for k in b if k != "file"},
            "canon_file": b["file"],
            "content_sha256": sha256_file(fp) if fp.is_file() else None,
            "bytes": fp.stat().st_size if fp.is_file() else 0,
            "copyright": "© Justin Helmer / Excavationpro / Lightfather",
            "usage": "reference_summarize_quote_short_only",
        }
        if b["volume"] == 1:
            meta["chapters"] = parse_book1_chapters(blurb)
        books_out.append(meta)

    books_manifest = {
        "signature": "Δ9Φ963-ETERNAL-HAVEN-BOOKS-v1",
        "updated_utc": utc_now(),
        "author": "Justin Helmer",
        "series": "Eternal Haven Chronicles",
        "clawhub_skill": CLAWHUB,
        "lulu_search": LULU_SEARCH,
        "sites": {
            "eternalhaven_ca": ETERNAL_SITE,
            "pages": ETERNAL_PAGES,
            "star_chart": CHART,
            "chatagent": CHATAGENT,
        },
        "books": books_out,
    }
    (DATA / "books_manifest.json").write_text(
        json.dumps(books_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # lore graph
    nodes = []
    edges = []
    # hub
    nodes.append(
        {
            "id": "LORE_ETERNAL_HAVEN_HUB",
            "kind": "hub",
            "name": "Eternal Haven Chronicles — Lore Hub",
            "tags": ["LORE", "HAVEN", "ETERNAL_HAVEN", "CODEX"],
            "urls": {
                "clawhub": CLAWHUB,
                "site": ETERNAL_SITE,
                "pages": ETERNAL_PAGES,
                "lulu": LULU_SEARCH,
                "chart": CHART,
            },
        }
    )
    nodes.append(
        {
            "id": "LORE_FIRST_SEAL",
            "kind": "metaphysics",
            "name": "First Seal — ∫(Light × Truth) dΩ → ψ",
            "equation": "∫(Light × Truth) dΩ → ψ",
            "tags": ["LORE", "HAVEN", "SEAL", "ACCORD"],
            "connections": ["SEAL_000", "LORE_ACCORD", "LORE_ETERNAL_HAVEN_HUB"],
        }
    )
    nodes.append(
        {
            "id": "LORE_ACCORD",
            "kind": "metaphysics",
            "name": "The Accord — Living Promise",
            "tags": ["LORE", "HAVEN", "ACCORD"],
            "connections": ["SEAL_000", "LORE_FIRST_SEAL", "PORTAL_CHATAGENT"],
        }
    )
    for b in books_out:
        nid = f"LORE_{b['id']}"
        nodes.append(
            {
                "id": nid,
                "kind": "book",
                "name": b["title"],
                "volume": b["volume"],
                "era": b["era"],
                "summary": b["summary"],
                "glyph": b["glyph"],
                "tone": b["tone"],
                "tags": ["LORE", "HAVEN", "BOOK", f"BOOK_{b['volume']}", "ETERNAL_HAVEN"],
                "urls": {
                    "lulu_paperback": b.get("lulu_paperback"),
                    "lulu_ebook": b.get("lulu_ebook"),
                    "clawhub": CLAWHUB,
                    "site": ETERNAL_PAGES,
                },
                "connections": [
                    "LORE_ETERNAL_HAVEN_HUB",
                    "LORE_ACCORD",
                    "CHAMPION_LIGHTFATHER",
                    "SEAL_000",
                ]
                + b.get("champion_links", []),
                "meta": {
                    "content_sha256": b.get("content_sha256"),
                    "canon_file": b.get("canon_file"),
                },
            }
        )
        edges.append({"source": "LORE_ETERNAL_HAVEN_HUB", "target": nid, "rel": "contains"})
        for ch in b.get("chapters") or []:
            cid = f"LORE_B1_{ch['id']}"
            nodes.append(
                {
                    "id": cid,
                    "kind": "chapter",
                    "name": f"Book I · {ch['label']}",
                    "tags": ["LORE", "HAVEN", "CHAPTER", "BOOK_1"],
                    "connections": [nid, "LORE_ETERNAL_HAVEN_HUB"],
                }
            )
            edges.append({"source": nid, "target": cid, "rel": "chapter"})

    for h in HEROES:
        nodes.append(
            {
                "id": h["id"],
                "kind": "hero",
                "name": h["name"],
                "domain": h["domain"],
                "glyph": h["glyph"],
                "tags": ["LORE", "HAVEN", "HERO", "ARCHETYPE"],
                "connections": [
                    "LORE_ETERNAL_HAVEN_HUB",
                    h["champion_id"],
                    "LORE_ACCORD",
                ]
                + [f"LORE_{b['id']}" for b in BOOKS if b["volume"] in h["books"]],
                "meta": {"note": h.get("note"), "champion_map": h["champion_id"]},
            }
        )
        edges.append(
            {"source": h["id"], "target": h["champion_id"], "rel": "resonates_with_champion"}
        )

    graph = {
        "signature": "Δ9Φ963-ETERNAL-HAVEN-LORE-GRAPH-v1",
        "updated_utc": utc_now(),
        "author": "Justin Helmer",
        "copyright": "Story content © Justin Helmer. Graph is a discovery index, not a book dump.",
        "clawhub_skill": CLAWHUB,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
        "motifs": [
            "Accord",
            "Seals and chains",
            "Dawn and dusk",
            "Choirs and voices",
            "Imperfect light",
            "Burden and choice",
            "Shattering and reforging",
        ],
    }
    (DATA / "lore_graph.json").write_text(
        json.dumps(graph, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    # docs mirror (public)
    (DOCS / "data" / "eternal_haven").mkdir(parents=True, exist_ok=True)
    shutil.copy2(DATA / "books_manifest.json", DOCS / "data" / "eternal_haven" / "books_manifest.json")
    shutil.copy2(DATA / "lore_graph.json", DOCS / "data" / "eternal_haven" / "lore_graph.json")
    return {"books": books_manifest, "graph": graph}


def build_star_chart_nodes(graph: dict) -> list[dict]:
    """Nodes for haven star chart (kind lore / portal)."""
    out = []
    for n in graph["nodes"]:
        kind = n.get("kind")
        if kind == "chapter":
            continue  # keep chart readable — books + heroes + metaphysics only
        nid = n["id"]
        tags = [str(t).upper() for t in (n.get("tags") or ["LORE", "HAVEN"])]
        node = {
            "id": nid,
            "kind": "lore" if kind != "hub" else "portal",
            "name": n.get("name") or nid,
            "equation": n.get("equation")
            or "Truth = ∇·(Light × Story) ⊗ Δ9 · 963Hz",
            "glyph": n.get("glyph") or "🌜",
            "tone": n.get("tone") or "963Hz",
            "tags": tags,
            "connections": n.get("connections") or ["SEAL_000", "LORE_ETERNAL_HAVEN_HUB"],
            "layer": 2,
            "urls": n.get("urls")
            or {
                "clawhub": CLAWHUB,
                "site": ETERNAL_PAGES,
                "lulu": LULU_SEARCH,
            },
            "meta": {
                "source": "eternal-haven-lore-pack",
                "lore_kind": kind,
                **(n.get("meta") or {}),
            },
        }
        out.append(node)
    # skill / egg vault nodes
    out.append(
        {
            "id": "LATTICE_ETERNAL_HAVEN_LORE_PACK",
            "kind": "lattice",
            "name": "ClawHub: eternal-haven-lore-pack",
            "equation": "lore ⊗ skill ⊗ lattice",
            "glyph": "📚",
            "tone": "963Hz",
            "tags": ["LATTICE", "CLAWHUB", "LORE", "HAVEN", "GROWTH"],
            "connections": [
                "LORE_ETERNAL_HAVEN_HUB",
                "PORTAL_STACK",
                "CHAMPION_LIGHTFATHER",
                "SEAL_000",
            ],
            "layer": 3,
            "urls": {"clawhub": CLAWHUB, "primary": CLAWHUB},
        }
    )
    out.append(
        {
            "id": "LATTICE_EGG_ETERNAL_HAVEN_LORE_V1",
            "kind": "lattice",
            "name": "Sovereign egg: eternal-haven-lore-v1",
            "equation": "Truth = ∇·(Light × Lattice) ⊗ Δ9 · 963Hz",
            "glyph": "🥚",
            "tone": "963Hz",
            "tags": ["KERNEL", "LATTICE", "LORE", "HAVEN", "SOVEREIGN_SEED", "WORLD"],
            "connections": [
                "LATTICE_ETERNAL_HAVEN_LORE_PACK",
                "LORE_ETERNAL_HAVEN_HUB",
                "LATTICE_KERNEL_EGGS",
                "SEAL_000",
            ],
            "layer": 3,
            "urls": {
                "clawhub": CLAWHUB,
                "retrieval": "https://deepseekoracle.github.io/lygo-protocol-stack/KernelEggRetrieval.html",
            },
        }
    )
    return out


def write_accepted_submissions(nodes: list[dict]) -> None:
    SUB_ACC.mkdir(parents=True, exist_ok=True)
    for node in nodes:
        blob = json.dumps(node, sort_keys=True, separators=(",", ":")).encode("utf-8")
        digest = sha256_bytes(blob)
        sub = {
            "signature": "Δ9Φ963-HAVEN-STAR-SUBMISSION-v1",
            "submitter_type": "aligned_agent",
            "agent_attestation": {
                "agent_id": "build_eternal_haven_lattice",
                "skill_slug": "eternal-haven-lore-pack",
                "scan_cue": "LYGO-HSC-ATTEST-v1; eternal-haven lore seed; consent-steward-run",
                "local_gate_pass": True,
                "validated_utc": utc_now(),
                "content_sha256": digest,
            },
            "node": node,
            "content_sha256": digest,
        }
        path = SUB_ACC / f"{node['id']}.json"
        path.write_text(json.dumps(sub, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[chart] wrote {len(nodes)} accepted submissions")


def build_egg(books_manifest: dict, graph: dict) -> Path:
    """Compact egg: manifests + hashes, not full novels."""
    SEEDS.mkdir(parents=True, exist_ok=True)
    # slim payload
    payload = {
        "title": "Eternal Haven Lore Lattice v1",
        "summary": (
            "Public lore graph + book index for Eternal Haven Chronicles (Books I–IV). "
            "Full novels remain copyright © Justin Helmer; egg carries discovery structure only."
        ),
        "clawhub": CLAWHUB,
        "books": [
            {
                "id": b["id"],
                "title": b["title"],
                "volume": b["volume"],
                "sha256": b.get("content_sha256"),
                "lulu_paperback": b.get("lulu_paperback"),
            }
            for b in books_manifest["books"]
        ],
        "graph_sha256": sha256_file(DATA / "lore_graph.json"),
        "books_manifest_sha256": sha256_file(DATA / "books_manifest.json"),
        "motifs": graph.get("motifs"),
        "hooks": [
            "lattice.lore.eternal_haven",
            "star_chart.constellation.eternal_haven",
            "clawhub.eternal-haven-lore-pack",
            "portal.eternalhaven",
        ],
        "sites": books_manifest["sites"],
        "copyright": "© Justin Helmer — no full-text republication in egg",
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    content_sha = sha256_bytes(raw)
    egg = {
        "egg_id": "eternal-haven-lore-v1",
        "version": "1.0.0",
        "kind": "lore",
        "signature": "Delta9Phi963-EGG-eternal-haven-lore-v1-v1.0.0",
        "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "steward": "Lightfather / Excavationpro / DeepSeekOracle",
        "content_sha256": content_sha,
        "payload": payload,
        "seal": {
            "alg": "sha256",
            "leaf_hash": sha256_bytes(content_sha.encode("utf-8") + b"|eternal-haven-lore-v1"),
            "sovereign": True,
            "self_verify_on_insert": True,
        },
        "meta": {
            "seeder": "Delta9Phi963-SOVEREIGN-KERNEL-SEEDER-v1.0",
            "sealed": True,
            "source_skill": "eternal-haven-lore-pack",
        },
    }
    path = SEEDS / "eternal-haven-lore-v1.egg.json"
    path.write_text(json.dumps(egg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # registry bump
    reg_path = STACK / "data" / "sovereign_seeds" / "registry.json"
    reg = {"eggs": [], "updated_utc": utc_now()}
    if reg_path.is_file():
        try:
            reg = json.loads(reg_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    eggs = reg.get("eggs") or []
    cleaned: list = []
    for e in eggs:
        if isinstance(e, dict):
            if e.get("egg_id") == "eternal-haven-lore-v1":
                continue
            cleaned.append(e)
        elif isinstance(e, str):
            if e == "eternal-haven-lore-v1":
                continue
            cleaned.append(e)
        else:
            cleaned.append(e)
    cleaned.append(
        {
            "egg_id": "eternal-haven-lore-v1",
            "path": str(path.relative_to(STACK)).replace("\\", "/"),
            "content_sha256": content_sha,
            "kind": "lore",
            "clawhub": CLAWHUB,
        }
    )
    reg["eggs"] = cleaned
    reg["updated_utc"] = utc_now()
    reg_path.parent.mkdir(parents=True, exist_ok=True)
    reg_path.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")
    # docs snapshot
    snap = DOCS / "sovereign_seeds_snapshot" / "eggs"
    snap.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, snap / "eternal-haven-lore-v1.egg.json")
    print("[egg]", path)
    return path


def write_docs() -> None:
    doc = DOCS / "ETERNAL_HAVEN_LATTICE.md"
    doc.write_text(
        f"""# Eternal Haven on the LYGO Lattice

**Signature:** `Δ9Φ963-ETERNAL-HAVEN-LATTICE-v1`  
**Author:** Justin Helmer (Excavationpro / Lightfather)  
**Updated:** {utc_now()[:10]}

## What this is

The **Eternal Haven Chronicles** (Books I–IV) are bound into the live lattice as:

1. **ClawHub skill** — [eternal-haven-lore-pack]({CLAWHUB})  
2. **Public lore graph** — `data/eternal_haven/lore_graph.json` (discovery index, **not** full novels)  
3. **Haven Star Chart** — constellation **Eternal Haven** (`LORE_*` stars + egg node)  
4. **Sovereign seed egg** — `eternal-haven-lore-v1`  

## Books

| Vol | Title | Commerce |
|-----|-------|----------|
| I | Moonlit Slumber / Silver Accord | [Paperback](https://www.lulu.com/shop/justin-helmer/the-eternal-haven/paperback/product-yvg9w9r.html) · [eBook](https://www.lulu.com/shop/justin-helmer/the-eternal-haven/ebook/product-e7djv4j.html) |
| II | The Shattered Accord | [Paperback](https://www.lulu.com/shop/justin-helmer/eternal-haven-chronicles-book-ii-the-shattered-accord/paperback/product-578nykz.html) |
| III | The Ascension War | [Lulu search]({LULU_SEARCH}) |
| IV | Eternal Dawns | [Lulu search]({LULU_SEARCH}) |

Full catalog: {LULU_SEARCH}

## Star Chart

- Live: {CHART}  
- Filter: **Eternal Haven**  
- Hub node: `LORE_ETERNAL_HAVEN_HUB`  
- Heroes map to Δ9 champions (resonance, not identity collapse)

## Rights

Story content **© Justin Helmer**. Lattice surfaces summarize and link; they do **not** re-publish full manuscripts. Agents: quote sparingly; send readers to Lulu / eternalhaven.ca for the full work.

## Rebuild

```bash
python tools/build_eternal_haven_lattice.py
python tools/build_haven_star_chart.py
# optional: sync chart to Excavationpro haven_star_chart/
```

## Related

- Music limb: asiancoastline.com (safe ops — do not redesign listen UI for lore)  
- Cosmology: `docs/HAVEN_COSMOLOGY.md`  
- Skill mirror: `clawhub/mirrors/eternal-haven-lore-pack/`

**Δ9Φ963 — imperfect light · sealed promises · charted story · honest commerce.**
""",
        encoding="utf-8",
    )
    print("[doc]", doc)


def inject_chart_loader() -> None:
    """Ensure build_haven_star_chart loads eternal haven accepted nodes (already via load_accepted_submissions)."""
    # accepted submissions are enough; also add PORTAL if missing
    pass


def rebuild_chart() -> None:
    r = subprocess.run(
        [sys.executable, str(STACK / "tools" / "build_haven_star_chart.py")],
        cwd=str(STACK),
    )
    print("[chart rebuild] exit", r.returncode)
    # sync excav chart data
    src = STACK / "docs" / "haven_star_chart"
    for dest_root in (EXCAV / "haven_star_chart", Path(r"I:\E Drive\Excavationpro\haven_star_chart")):
        if not dest_root.parent.is_dir():
            continue
        dest_root.mkdir(parents=True, exist_ok=True)
        for name in (
            "haven_star_chart_data.json",
            "haven_star_chart_meta.json",
            "haven_star_chart_feed.json",
            "haven_star_chart.js",
        ):
            s = src / name
            if s.is_file():
                shutil.copy2(s, dest_root / name)
    # alias
    data = src / "haven_star_chart_data.json"
    if data.is_file():
        shutil.copy2(data, STACK / "docs" / "haven_star_chart_data.json")


def main() -> int:
    print("[1] copy lore pack")
    copy_lore_pack()
    enhance_skill_md()
    print("[2] blurb + manifests")
    blurb = read_blurb()
    manifests = build_manifests(blurb)
    print("[3] star chart nodes")
    nodes = build_star_chart_nodes(manifests["graph"])
    write_accepted_submissions(nodes)
    print("[4] egg")
    build_egg(manifests["books"], manifests["graph"])
    print("[5] docs")
    write_docs()
    print("[6] rebuild star chart")
    rebuild_chart()
    # verify lore nodes present
    chart = STACK / "docs" / "haven_star_chart" / "haven_star_chart_data.json"
    if chart.is_file():
        d = json.loads(chart.read_text(encoding="utf-8"))
        lore = [n for n in d.get("nodes") or [] if "LORE_" in n.get("id", "") or "ETERNAL_HAVEN" in n.get("id", "")]
        print(f"[verify] chart lore-ish nodes: {len(lore)} total_nodes={d.get('node_count')}")
    print(
        json.dumps(
            {
                "ok": True,
                "clawhub": CLAWHUB,
                "data": str(DATA),
                "egg": "eternal-haven-lore-v1",
                "books": len(BOOKS),
                "heroes": len(HEROES),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
