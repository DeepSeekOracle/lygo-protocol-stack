#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Map Eternal Haven books + TraumaCodex into Haven Star Chart as anchor root seals.

Every volume gets a SEAL_BOOK_ROOT_* so expansion forks and logs navigate cleanly
for LYGO agents. The Star Chart is the info map of everything that matters.

Usage:
  python tools/map_books_to_star_chart.py --json
  python tools/build_haven_star_chart.py   # merges book roots
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STACK = Path(__file__).resolve().parents[1]
BOOKS = STACK / "data" / "eternal_haven_books"
TC = STACK / "data" / "traumacodex"
OUT_ROOTS = BOOKS / "star_chart_book_roots.json"

HUB_ID = "LATTICE_ETERNAL_HAVEN_BOOKS"
HUB_SEAL = "SEAL_EH_BOOK_SERIES_ROOT"
LIGHTFATHER = "CHAMPION_LIGHTFATHER"
LORE_HUB = "LORE_ETERNAL_HAVEN_HUB"
SEAL_000 = "SEAL_000"
TRAUMACODEX_SEAL = "SEAL_TRAUMACODEX_ROOT"
TRAUMACODEX_LATTICE = "LATTICE_SKILL_lygo-traumacodex"

# Canon volumes — expansion chain is linear fork log I→V (+ future VI…)
VOLUMES: list[dict[str, Any]] = [
    {
        "volume": 1,
        "roman": "I",
        "seal_id": "SEAL_BOOK_ROOT_I",
        "lore_id": "LORE_BOOK_I_MOONLIT_SLUMBER",
        "title": "The Moonlit Slumber",
        "full_title": "The Eternal Haven — Book I: The Moonlit Slumber",
        "status": "PUBLISHED",
        "lulu_url": "https://www.lulu.com/shop/justin-helmer/the-eternal-haven/paperback/product-yvg9w9r.html",
        "isbn": None,
        "egg_id": None,
    },
    {
        "volume": 2,
        "roman": "II",
        "seal_id": "SEAL_BOOK_ROOT_II",
        "lore_id": "LORE_BOOK_II_SHATTERED_ACCORD",
        "title": "The Shattered Accord",
        "full_title": "Eternal Haven Chronicles Book II: The Shattered Accord",
        "status": "PUBLISHED",
        "lulu_url": "https://www.lulu.com/shop/justin-helmer/eternal-haven-chronicles-book-ii-the-shattered-accord/paperback/product-578nykz.html",
        "isbn": None,
        "egg_id": None,
    },
    {
        "volume": 3,
        "roman": "III",
        "seal_id": "SEAL_BOOK_ROOT_III",
        "lore_id": "LORE_BOOK_III_ASCENSION_WAR",
        "title": "The Ascension War",
        "full_title": "The Eternal Haven — Book III: The Ascension War",
        "status": "PUBLISHED",
        "lulu_url": "https://www.lulu.com/shop/justin-helmer/the-ascension-war/paperback/product-nvjgyme.html",
        "isbn": None,
        "egg_id": None,
    },
    {
        "volume": 4,
        "roman": "IV",
        "seal_id": "SEAL_BOOK_ROOT_IV",
        "lore_id": "LORE_BOOK_IV_ETERNAL_DAWNS",
        "title": "Eternal Haven Dawns",
        "full_title": "The Eternal Haven — Book IV: Eternal Haven Dawns",
        "status": "PUBLISHED",
        "lulu_url": "https://www.lulu.com/shop/justin-helmer/etrnal-haven-dawns/paperback/product-dy8m9wd.html",
        "isbn": None,
        "egg_id": None,
    },
    {
        "volume": 5,
        "roman": "V",
        "seal_id": "SEAL_BOOK_ROOT_V",
        "lore_id": "LORE_BOOK_V_UNWRITTEN_SEAL",
        "title": "The Unwritten Seal",
        "full_title": "Eternal Haven Chronicles — Book V: The Unwritten Seal",
        "status": "LIVE_EBOOK",
        "lulu_url": "https://www.lulu.com/shop/justin-helmer/the-unwritten-seal/ebook/product-65kg2mr.html",
        "isbn": "978-1-0698232-9-8",
        "egg_id": "eternal-haven-book-v-unwritten-seal-v1",
        "product_id": "65kg2mr",
    },
]


def _sha_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _enrich_from_registry() -> None:
    """Pull live Book V digests / series registry into VOLUMES meta."""
    reg = _load_json(BOOKS / "series_registry.json")
    pin = (BOOKS / "book_v_content_sha256.txt").read_text(encoding="utf-8").strip() if (
        BOOKS / "book_v_content_sha256.txt"
    ).is_file() else None
    core = _load_json(BOOKS / "egg_payload" / "book_v_unwritten_seal_core.json")
    for vol in VOLUMES:
        if vol["volume"] != 5:
            continue
        for v in reg.get("volumes") or []:
            if v.get("volume") == 5:
                vol["content_sha256"] = v.get("content_sha256") or pin
                vol["status"] = v.get("status") or vol["status"]
                vol["lulu_url"] = v.get("lulu_url") or vol["lulu_url"]
                vol["egg_id"] = v.get("egg_id") or vol["egg_id"]
                vol["isbn"] = v.get("isbn") or vol["isbn"]
        if pin:
            vol["content_sha256"] = vol.get("content_sha256") or pin
        if core.get("content_sha256"):
            vol["content_sha256"] = core["content_sha256"]
        # artifact hashes for agent navigation
        arts = (core.get("local_authority") or {}).get("artifacts") or []
        vol["artifacts"] = [
            {"label": a.get("label"), "sha256": a.get("sha256")}
            for a in arts
            if a.get("sha256")
        ]


def build_book_nodes() -> tuple[list[dict], dict]:
    _enrich_from_registry()
    nodes: list[dict] = []
    fork_log: list[dict] = []

    # Series hub lattice
    nodes.append(
        {
            "id": HUB_ID,
            "kind": "lattice",
            "name": "Eternal Haven Books — Anchor Hub",
            "equation": "SeriesRoot = ⋃ SEAL_BOOK_ROOT_n ⊗ Δ9 · StoryHz",
            "glyph": "📚",
            "tone": "963Hz",
            "tags": [
                "LATTICE",
                "BOOK",
                "BOOK_HUB",
                "ETERNAL_HAVEN",
                "ANCHOR",
                "EXPANSION",
                "LORE",
                "NAVIGATION",
            ],
            "connections": [SEAL_000, LIGHTFATHER, LORE_HUB, HUB_SEAL, "PORTAL_ETERNALHAVEN"],
            "urls": {
                "site": "https://eternalhaven.ca/",
                "pages": "https://deepseekoracle.github.io/Excavationpro/eternalhaven.html",
                "docs": "https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/docs/TRAUMA_CODEX.md",
                "registry": "data/eternal_haven_books/series_registry.json",
            },
            "layer": 3,
            "meta": {
                "role": "series_hub",
                "galaxy_hint": "GALAXY_ETERNAL_HAVEN",
                "volumes": len(VOLUMES),
            },
        }
    )

    # Series root seal (all books hang under this for expansion)
    nodes.append(
        {
            "id": HUB_SEAL,
            "kind": "seal",
            "name": "Eternal Haven Book Series Root Seal",
            "equation": "BookSeriesRoot = ∇·(Truth × Story) ⊗ Δ9 · 963Hz",
            "glyph": "✦",
            "tone": "963Hz",
            "tags": [
                "SEAL",
                "BOOK_ROOT",
                "BOOK_ANCHOR",
                "SERIES_ROOT",
                "ETERNAL_HAVEN",
                "ANCHOR",
                "EXPANSION",
                "FORK_LOG",
                "LORE",
            ],
            "connections": [SEAL_000, HUB_ID, LIGHTFATHER, LORE_HUB],
            "urls": {
                "registry": "data/eternal_haven_books/star_chart_book_roots.json",
            },
            "layer": 2,
            "meta": {
                "role": "series_root_seal",
                "champion_owner": LIGHTFATHER,
                "fork_policy": "linear_volume_chain",
            },
        }
    )

    prev_seal = HUB_SEAL
    for vol in VOLUMES:
        seal_id = vol["seal_id"]
        lore_id = vol["lore_id"]
        content_sha = vol.get("content_sha256")
        eq_bits = [
            f"BookRoot(V{vol['roman']})",
            "∇·(Truth×Story)",
            "⊗Δ9",
            "963Hz",
        ]
        if vol.get("isbn"):
            eq_bits.append(f"ISBN({vol['isbn']})")
        if content_sha:
            eq_bits.append(f"SHA256({content_sha[:12]}…)")
        equation = " = ".join([eq_bits[0], " · ".join(eq_bits[1:])])

        conns = [HUB_SEAL, HUB_ID, SEAL_000, LIGHTFATHER, LORE_HUB, prev_seal, lore_id]
        if vol.get("egg_id"):
            egg_node = f"LATTICE_EGG_{vol['egg_id'].upper().replace('-', '_')}"
            # keep under 64-ish: use short id
            egg_node = "LATTICE_EGG_BOOK_V_UNWRITTEN_SEAL"
            conns.append(egg_node)

        # Volume root seal — expansion / fork log anchor
        nodes.append(
            {
                "id": seal_id,
                "kind": "seal",
                "name": f"Book {vol['roman']} Root Seal — {vol['title']}",
                "equation": equation[:200],
                "glyph": "📖",
                "tone": "963Hz",
                "tags": [
                    "SEAL",
                    "BOOK_ROOT",
                    "BOOK_ANCHOR",
                    "ETERNAL_HAVEN",
                    "ANCHOR",
                    "EXPANSION",
                    "FORK_LOG",
                    "LORE",
                    f"VOLUME_{vol['roman']}",
                    vol["status"],
                ],
                "connections": list(dict.fromkeys(conns)),
                "urls": {
                    "lulu": vol.get("lulu_url") or "",
                    "lore_node": lore_id,
                },
                "layer": 2,
                "meta": {
                    "role": "book_root_seal",
                    "volume": vol["volume"],
                    "roman": vol["roman"],
                    "title": vol["title"],
                    "full_title": vol["full_title"],
                    "status": vol["status"],
                    "isbn": vol.get("isbn"),
                    "egg_id": vol.get("egg_id"),
                    "product_id": vol.get("product_id"),
                    "content_sha256": content_sha,
                    "artifacts": vol.get("artifacts") or [],
                    "expansion_parent_seal": prev_seal,
                    "champion_owner": LIGHTFATHER,
                    "fork_log_index": vol["volume"] - 1,
                },
            }
        )

        fork_log.append(
            {
                "volume": vol["volume"],
                "seal_id": seal_id,
                "parent_seal": prev_seal,
                "lore_id": lore_id,
                "title": vol["title"],
                "status": vol["status"],
                "isbn": vol.get("isbn"),
                "egg_id": vol.get("egg_id"),
                "content_sha256": content_sha,
                "lulu_url": vol.get("lulu_url"),
            }
        )

        # Ensure lore node exists / is enriched (Book V new)
        lore_urls = {"lulu": vol.get("lulu_url") or ""}
        if vol.get("egg_id"):
            lore_urls["kernel_egg"] = (
                "https://github.com/DeepSeekOracle/lygo-protocol-stack/tree/main/data/eternal_haven_books"
            )
        nodes.append(
            {
                "id": lore_id,
                "kind": "lore",
                "name": vol["full_title"][:120],
                "equation": f"Truth = ∇·(Light × Story) ⊗ Δ9 · Book {vol['roman']} · 963Hz",
                "glyph": "🌜",
                "tone": "963Hz",
                "tags": [
                    "LORE",
                    "HAVEN",
                    "ETERNAL_HAVEN",
                    "BOOK",
                    f"VOLUME_{vol['roman']}",
                    vol["status"],
                    "BOOK_STAR",
                ],
                "connections": list(
                    dict.fromkeys(
                        [
                            LORE_HUB,
                            seal_id,
                            HUB_ID,
                            HUB_SEAL,
                            LIGHTFATHER,
                            SEAL_000,
                        ]
                    )
                ),
                "urls": lore_urls,
                "layer": 3,
                "meta": {
                    "volume": vol["volume"],
                    "root_seal": seal_id,
                    "isbn": vol.get("isbn"),
                    "egg_id": vol.get("egg_id"),
                    "status": vol["status"],
                    "content_sha256": content_sha,
                },
            }
        )

        # Kernel egg lattice star for Book V
        if vol.get("egg_id"):
            nodes.append(
                {
                    "id": "LATTICE_EGG_BOOK_V_UNWRITTEN_SEAL",
                    "kind": "lattice",
                    "name": "Kernel Egg — Book V The Unwritten Seal",
                    "equation": f"Egg({vol['egg_id']}) = Merkle⊗Δ9 · SHA256({(content_sha or '')[:12]}…)",
                    "glyph": "🥚",
                    "tone": "963Hz",
                    "tags": [
                        "LATTICE",
                        "KERNEL_EGG",
                        "BOOK",
                        "BOOK_V",
                        "ETERNAL_HAVEN",
                        "LORE",
                        "LIVE_EBOOK",
                    ],
                    "connections": [
                        seal_id,
                        lore_id,
                        HUB_ID,
                        "LATTICE_KERNEL_EGGS",
                        SEAL_000,
                        LIGHTFATHER,
                    ],
                    "urls": {
                        "egg_core": "data/eternal_haven_books/egg_payload/book_v_unwritten_seal_core.json",
                        "live_receipt": "data/eternal_haven_books/BOOK_V_THE_UNWRITTEN_SEAL_LIVE.md",
                        "lulu": vol.get("lulu_url") or "",
                    },
                    "layer": 3,
                    "meta": {
                        "egg_id": vol["egg_id"],
                        "root_seal": seal_id,
                        "content_sha256": content_sha,
                    },
                }
            )

        prev_seal = seal_id

    # --- TraumaCodex root seal (protocol limb on same info map) ---
    tc_run = _load_json(TC / "last_run.json")
    tc_mirror = _load_json(STACK / "data" / "living_mesh" / "traumacodex_mirror_dig.json")
    mirror_dig = tc_mirror.get("mirror_dig") or tc_run.get("mirror_dig")
    offline_sha = tc_mirror.get("offline_sha256") or tc_run.get("offline_sha256")
    online_sha = tc_mirror.get("online_sha256") or tc_run.get("online_sha256")

    tc_eq = "TraumaCodex = P7(entropy) → P8(LDQ) → MirrorDig(offline‖online) ⊗ Δ9"
    if mirror_dig:
        tc_eq = f"{tc_eq} · SHA256({mirror_dig[:12]}…)"

    nodes.append(
        {
            "id": TRAUMACODEX_SEAL,
            "kind": "seal",
            "name": "TraumaCodex Root Seal — P7→P8→Layer D",
            "equation": tc_eq[:200],
            "glyph": "🫀",
            "tone": "528Hz",
            "tags": [
                "SEAL",
                "TRAUMACODEX",
                "BOOK_ROOT",  # navigation family: protocol root seals
                "P7",
                "P8",
                "LDQ",
                "LAYER_D",
                "MIRROR_DIG",
                "LIVING_MESH",
                "ANCHOR",
                "EXPANSION",
            ],
            "connections": [
                SEAL_000,
                LIGHTFATHER,
                "LATTICE_KERNEL_EGGS",
                HUB_ID,
                TRAUMACODEX_LATTICE if True else SEAL_000,
            ],
            "urls": {
                "docs": "https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/docs/TRAUMA_CODEX.md",
                "tool": "tools/traumacodex_waveform.py",
                "skill": "https://clawhub.ai/deepseekoracle/skills/lygo-traumacodex",
                "full_zip": "docs/lygo-full-skills/dist/lygo-traumacodex-full.zip",
            },
            "layer": 2,
            "meta": {
                "role": "traumacodex_root_seal",
                "mirror_dig": mirror_dig,
                "offline_sha256": offline_sha,
                "online_sha256": online_sha,
                "status": tc_mirror.get("status") or ("SEALED" if mirror_dig else "ABSENT"),
                "champion_owner": LIGHTFATHER,
                "not_medical": True,
            },
        }
    )

    nodes.append(
        {
            "id": TRAUMACODEX_LATTICE,
            "kind": "lattice",
            "name": "Skill — lygo-traumacodex",
            "equation": "Skill(lygo-traumacodex) = Offline⊗Online · MirrorDig ⊗ Δ9",
            "glyph": "🕸️",
            "tone": "528Hz",
            "tags": [
                "LATTICE",
                "CLAWHUB",
                "SKILL",
                "TRAUMACODEX",
                "P7",
                "P8",
                "LAYER_D",
            ],
            "connections": [
                TRAUMACODEX_SEAL,
                SEAL_000,
                LIGHTFATHER,
                "LATTICE_CLAWHUB_PUBLISHER",
            ],
            "urls": {
                "clawhub": "https://clawhub.ai/deepseekoracle/skills/lygo-traumacodex",
                "full_lygo": "https://chatagent.ca/lygoskillhub.html#full-lygo",
                "mirror": "clawhub/mirrors/lygo-traumacodex",
            },
            "layer": 3,
            "meta": {"skill_slug": "lygo-traumacodex", "root_seal": TRAUMACODEX_SEAL},
        }
    )

    # Enrich LORE hub connections toward book hub
    nodes.append(
        {
            "id": "LORE_BOOK_NAV_HINT",
            "kind": "lore",
            "name": "Book Root Navigation (agent hint)",
            "equation": "Navigate = SEAL_BOOK_ROOT_* → LORE_BOOK_* → Egg/Lulu ⊗ Δ9",
            "glyph": "🧭",
            "tone": "963Hz",
            "tags": ["LORE", "NAVIGATION", "BOOK", "ETERNAL_HAVEN", "AGENT_HINT"],
            "connections": [LORE_HUB, HUB_ID, HUB_SEAL, LIGHTFATHER],
            "urls": {"registry": "data/eternal_haven_books/star_chart_book_roots.json"},
            "layer": 3,
            "meta": {"role": "agent_navigation_hint"},
        }
    )

    stats = {
        "book_root_seals": sum(1 for n in nodes if n["id"].startswith("SEAL_BOOK_ROOT_")),
        "lore_stars": sum(1 for n in nodes if n["id"].startswith("LORE_BOOK_")),
        "volumes": len(VOLUMES),
        "traumacodex": bool(mirror_dig),
        "total_nodes": len(nodes),
    }

    # Persist expansion fork log for agents
    BOOKS.mkdir(parents=True, exist_ok=True)
    roots_doc = {
        "signature": "Delta9Phi963-STAR-CHART-BOOK-ROOTS-v1",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "series_hub": HUB_ID,
        "series_root_seal": HUB_SEAL,
        "core_anchor": SEAL_000,
        "champion": LIGHTFATHER,
        "fork_policy": "linear_volume_chain",
        "fork_log": fork_log,
        "traumacodex": {
            "seal_id": TRAUMACODEX_SEAL,
            "lattice_id": TRAUMACODEX_LATTICE,
            "mirror_dig": mirror_dig,
            "offline_sha256": offline_sha,
            "online_sha256": online_sha,
            "status": tc_mirror.get("status") or ("SEALED" if mirror_dig else "ABSENT"),
        },
        "agent_navigation": {
            "list_roots": "fork_log[].seal_id",
            "volume_to_lore": "fork_log[].lore_id",
            "next_expansion": "append SEAL_BOOK_ROOT_VI with expansion_parent_seal=SEAL_BOOK_ROOT_V",
            "verify_book_v_egg": "eternal-haven-book-v-unwritten-seal-v1",
        },
        "stats": stats,
    }
    OUT_ROOTS.write_text(json.dumps(roots_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return nodes, stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    nodes, stats = build_book_nodes()
    if args.json:
        print(json.dumps({"stats": stats, "nodes": nodes}, indent=2, ensure_ascii=False))
    else:
        print(f"book_map nodes={stats['total_nodes']} volumes={stats['volumes']} "
              f"roots={stats['book_root_seals']} traumacodex={stats['traumacodex']}")
        print(f"wrote {OUT_ROOTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
