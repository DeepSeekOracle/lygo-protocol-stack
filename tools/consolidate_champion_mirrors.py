#!/usr/bin/env python3
"""Mark per-champion ClawHub mirrors deprecated → lygo-champion-council (consolidation complete)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIRRORS = ROOT / "clawhub" / "mirrors"
SUCCESSOR = "lygo-champion-council"
KEEP_OPERATOR = "lygo-champion-lightfather"


def _champion_id(mirror: Path) -> str | None:
    canon = mirror / "references" / "canon.json"
    if canon.is_file():
        return json.loads(canon.read_text(encoding="utf-8")).get("champion")
    return None


def _patch_skill(mirror: Path, slug: str, champion_id: str | None, *, operator_only: bool) -> bool:
    skill = mirror / "SKILL.md"
    if not skill.is_file():
        return False
    text = skill.read_text(encoding="utf-8")
    if SUCCESSOR in text and '"deprecated": true' in text and not operator_only:
        return False
    if operator_only and "operator-only" in text and SUCCESSOR in text:
        return False

    banner = (
        f"> **Consolidated (Δ9 v2):** New installs → `{SUCCESSOR}`. "
        f"This slug is legacy retention only.\n"
        f"> `npx clawhub@latest install deepseekoracle/{SUCCESSOR}`\n\n"
    )
    if operator_only:
        banner = (
            f"> **Council persona:** use `{SUCCESSOR}` (champion_id `Lightfather`).\n"
            f"> **This skill:** full Lightfather **operator** stack map — keep for stack ops only.\n\n"
        )

    meta = {
        "lygo": True,
        "champion": True,
        "version": "1.0.1",
        "successor": SUCCESSOR,
    }
    if champion_id:
        meta["champion_id"] = champion_id
    if operator_only:
        meta["consolidation"] = "operator-only"
    else:
        meta["deprecated"] = True

    desc = f"DEPRECATED slug — use {SUCCESSOR}."
    if champion_id:
        desc += f" Legacy Δ9 champion ({champion_id})."
    if operator_only:
        desc = (
            f"Lightfather operator stack (consent-gated). Persona-only: install {SUCCESSOR} "
            f"with champion_id Lightfather."
        )

    new_fm = (
        f"---\nname: {slug}\n"
        f'description: "{desc}"\n'
        f"metadata: {json.dumps(meta, ensure_ascii=False)}\n---\n\n"
    )
    body = text
    if text.startswith("---"):
        body = re.sub(r"^---\n.*?\n---\n+", "", text, count=1, flags=re.DOTALL)
    if banner.strip() not in body:
        body = banner + body.lstrip()
    skill.write_text(new_fm + body, encoding="utf-8")
    return True


def main() -> int:
    updated = []
    for mirror in sorted(MIRRORS.glob("lygo-champion-*")):
        slug = mirror.name
        if slug == SUCCESSOR:
            continue
        cid = _champion_id(mirror)
        op_only = slug == KEEP_OPERATOR
        if _patch_skill(mirror, slug, cid, operator_only=op_only):
            updated.append(slug)
    # Bump unified council skill note
    council = MIRRORS / SUCCESSOR / "SKILL.md"
    if council.is_file():
        t = council.read_text(encoding="utf-8")
        if '"version": "1.0.1"' not in t:
            t = t.replace('"version": "1.0.0"', '"version": "1.0.1"')
            t = t.replace(
                "Δ9Φ963 — one council skill",
                "Δ9Φ963 — consolidation complete — one council skill",
            )
            council.write_text(t, encoding="utf-8")
            updated.append(SUCCESSOR)
    print(json.dumps({"patched": len(updated), "slugs": updated}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())