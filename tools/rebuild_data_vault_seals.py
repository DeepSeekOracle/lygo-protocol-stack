#!/usr/bin/env python3
"""Rebuild Data Vault seal index from all available I: Drive + stack sources.

Merges:
  - LYRA_CORE canonical_seals_index.json
  - Longest LYRA_SEAL_ARCHIVE_LEGACY_001-400.txt (incl. A/M/MLF forks)
  - Haven Star Chart SEAL_* nodes
  - Website JSON chunks (051-200, lygo_full_clean, enhanced lists)
  - Accepted Star Chart seal submissions (e.g. SEAL_401)

Writes docs/data-vault/data/canonical_seals_public.json (+ grok_spoken + manifest stats)
and refreshes LYRA_CORE/canonical_seals_index.json count.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(r"I:\E Drive")
STACK = ROOT / "lygo-protocol-stack"
VAULT_DATA = STACK / "docs" / "data-vault" / "data"
LYRA_CORE_INDEX = ROOT / "LYRA_CORE" / "canonical_seals_index.json"

SECRET_PATTERNS = [
    re.compile(
        r"(?i)(api[_-]?key|secret|password|token|bearer|sk-|moltbook_sk_|moltx_sk_|nvapi-|xai-|ghp_|github_pat_)[=:\s]+[^\s\"']+"
    ),
    re.compile(r"(?i)authorization:\s*bearer\s+\S+"),
    re.compile(r"[A-Za-z]:\\Users\\[^\s\"']+"),
    re.compile(r"I:\\E Drive\\[^\s\"']+"),
    re.compile(r"D:\\OpenClaw[^\s\"']*"),
    re.compile(r"C:\\Users\\[^\s\"']+"),
]


def redact(s: str) -> str:
    if not s:
        return s
    out = s
    for p in SECRET_PATTERNS:
        out = p.sub("[REDACTED_PATH_OR_SECRET]", out)
    return out


def norm_id(raw: Any) -> str | None:
    if raw is None:
        return None
    if isinstance(raw, int):
        return f"SEAL_{raw:03d}"
    s = str(raw).strip()
    if not s:
        return None
    s = s.replace(" ", "_")
    if re.fullmatch(r"\d+[A-Za-z]*", s):
        m = re.match(r"(\d+)([A-Za-z]*)", s)
        assert m
        return f"SEAL_{int(m.group(1)):03d}{m.group(2)}"
    m = re.match(r"^(?:SEAL[_-]?)?0*(\d+)([A-Za-z].*)?$", s, re.I)
    if m:
        return f"SEAL_{int(m.group(1)):03d}{m.group(2) or ''}"
    if s.upper().startswith("SEAL_"):
        return "SEAL_" + s.split("_", 1)[1]
    if s.upper().startswith("SEAL"):
        return s if s.startswith("SEAL_") else "SEAL_" + s[4:].lstrip("_-")
    return None


def empty_card(sid: str) -> dict[str, Any]:
    return {
        "id": sid,
        "name": "",
        "tone": "",
        "equation": "",
        "quote": "",
        "glyph": "",
        "tags": [],
        "notes": "",
        "source_kind": "",
        "sources": [],
        "public_provenance": "LYGO multi-source public seal merge · paths scrubbed",
    }


def is_weak_name(name: str) -> bool:
    n = (name or "").strip().lower()
    return (not n) or n in {"(unnamed)", "unnamed", "unnamed seal", "unknown"}


def merge_card(dst: dict[str, Any], src: dict[str, Any], source: str) -> None:
    if source and source not in dst["sources"]:
        dst["sources"].append(source)
    if not dst.get("source_kind"):
        dst["source_kind"] = source
    # Prefer non-weak names
    if src.get("name") and (is_weak_name(dst.get("name") or "") or len(str(src["name"])) > len(str(dst.get("name") or ""))):
        if not is_weak_name(str(src["name"])):
            dst["name"] = str(src["name"]).strip()
        elif not dst.get("name"):
            dst["name"] = str(src["name"]).strip()
    for field in ("tone", "equation", "quote", "glyph", "notes"):
        val = src.get(field)
        if not val:
            continue
        cur = dst.get(field) or ""
        if not cur or (isinstance(val, str) and len(val) > len(str(cur))):
            dst[field] = redact(str(val).strip())[:2000] if field == "notes" else redact(str(val).strip())[:800]
    tags = src.get("tags") or []
    if isinstance(tags, str):
        tags = re.findall(r"\{([^}]+)\}", tags) or [t.strip() for t in re.split(r"[,|/]", tags) if t.strip()]
    have = {str(t).upper() for t in dst.get("tags") or []}
    for t in tags:
        tu = str(t).strip()
        if not tu:
            continue
        if tu.upper() not in have:
            dst.setdefault("tags", []).append(tu)
            have.add(tu.upper())


def parse_legacy_archive(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    parts = re.split(r"(?m)^\[SEAL_([^\]]+)\]\s*$", text)
    out: list[dict[str, Any]] = []
    for i in range(1, len(parts), 2):
        sid = norm_id(parts[i])
        if not sid:
            continue
        body = parts[i + 1] if i + 1 < len(parts) else ""

        def field(name: str) -> str:
            m = re.search(rf"(?im)^{name}:\s*(.+)$", body)
            return m.group(1).strip() if m else ""

        tags_raw = field("Tags")
        tags = re.findall(r"\{([^}]+)\}", tags_raw) or [
            t.strip() for t in re.split(r"[,|]", tags_raw) if t.strip()
        ]
        out.append(
            {
                "id": sid,
                "name": field("Name"),
                "equation": field("Equation"),
                "tone": field("Tone"),
                "glyph": field("Glyph"),
                "tags": tags or ["CANON", "LEGACY_ARCHIVE"],
                "notes": field("Notes"),
                "quote": "",
            }
        )
    return out


def load_json_seals(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    raw = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    items: list = []
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict):
        items = raw.get("seals") or raw.get("entries") or raw.get("data") or []
        if not items and "id" in raw:
            items = [raw]
    out: list[dict[str, Any]] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        sid = norm_id(it.get("id") or it.get("Seal_ID") or it.get("seal_id") or it.get("ID"))
        # enhanced list sometimes uses numeric id + name elsewhere
        if not sid and isinstance(it.get("id"), (int, float)):
            sid = norm_id(int(it["id"]))
        if not sid:
            continue
        tags = it.get("tags") or it.get("Tags") or []
        if isinstance(tags, str):
            tags = re.findall(r"\{([^}]+)\}", tags) or [tags]
        # Pull structured bits from archive_details if present
        details = it.get("archive_details") or ""
        name = it.get("name") or it.get("Name") or ""
        equation = it.get("equation") or it.get("Equation") or ""
        tone = it.get("tone") or it.get("Tone") or it.get("toneRange") or ""
        if isinstance(tone, list):
            tone = ", ".join(str(x) for x in tone)
        glyph = it.get("glyph") or it.get("Glyph") or ""
        notes = it.get("notes") or it.get("Notes") or ""
        quote = it.get("quote") or it.get("Quote") or ""
        if details and isinstance(details, str):
            if not name:
                m = re.search(r"(?im)^Name:\s*(.+)$", details)
                if m:
                    name = m.group(1).strip()
            if not equation:
                m = re.search(r"(?im)^Equation:\s*(.+)$", details)
                if m:
                    equation = m.group(1).strip()
            if not tone:
                m = re.search(r"(?im)^Tone:\s*(.+)$", details)
                if m:
                    tone = m.group(1).strip()
            if not glyph:
                m = re.search(r"(?im)^Glyph:\s*(.+)$", details)
                if m:
                    glyph = m.group(1).strip()
            if not notes:
                m = re.search(r"(?im)^Notes:\s*(.+)$", details)
                if m:
                    notes = m.group(1).strip()
            if not tags:
                tags = re.findall(r"\{([^}]+)\}", details)
        # Skip non-seal memory-system rows that lack seal semantics
        role = str(it.get("role") or "")
        if role and not name and "SEAL" not in str(details).upper() and not equation:
            # still keep if id looks like seal number from enhanced dump
            if not re.match(r"^SEAL_\d+", sid):
                continue
        out.append(
            {
                "id": sid,
                "name": name,
                "equation": equation,
                "tone": tone,
                "glyph": glyph,
                "tags": tags,
                "notes": notes,
                "quote": quote,
            }
        )
    return out


def load_star_chart_seals() -> list[dict[str, Any]]:
    path = STACK / "docs" / "haven_star_chart" / "haven_star_chart_data.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    out: list[dict[str, Any]] = []
    for n in data.get("nodes") or []:
        sid = str(n.get("id") or "")
        if not sid.startswith("SEAL_"):
            continue
        # Keep unnormalized specials (BOOK_ROOT etc.) and normalize numeric
        nid = norm_id(sid) if re.match(r"^SEAL_0*\d+", sid) else sid
        if not nid:
            continue
        out.append(
            {
                "id": nid,
                "name": n.get("name") or "",
                "equation": n.get("equation") or "",
                "tone": n.get("tone") or "",
                "glyph": n.get("glyph") or "",
                "tags": n.get("tags") or ["STAR_CHART"],
                "notes": "",
                "quote": "",
            }
        )
    return out


def load_recursive_ethics_seals() -> list[dict[str, Any]]:
    """Pull seal cards from the Recursive Ethics creation log + SEAL_*.md docs."""
    out: list[dict[str, Any]] = []
    rec = ROOT / "Recursive Ethics Through Immutable Seal Chains" / "Recursive Ethics Through Immutable.txt"
    if rec.is_file():
        text = rec.read_text(encoding="utf-8", errors="replace")
        # White paper / titled seals
        for m in re.finditer(
            r"(?ms)^(?:White Paper:\s*)?(SEAL_(\d{1,6}))\s*[—\-:]\s*([^\n]+)\n(.*?)(?=^(?:White Paper:|SEAL_\d{1,6}\s*[—\-:]|#{1,3}\s)|\Z)",
            text,
        ):
            sid = norm_id(m.group(2))
            if not sid:
                continue
            title = m.group(3).strip()
            body = m.group(4).strip()
            equation = ""
            em = re.search(r"(?im)^(?:Core )?Equation[^\n]*:\s*(.+)$", body)
            if em:
                equation = em.group(1).strip()
            notes = redact(body[:1500])
            out.append(
                {
                    "id": sid,
                    "name": title[:200],
                    "equation": equation,
                    "tone": "",
                    "glyph": "",
                    "tags": ["CANON", "RECURSIVE_ETHICS", "WHITEPAPER"],
                    "notes": notes,
                    "quote": "",
                }
            )
        # Named analysis lines: SEAL_272 Analysis: "..."
        for m in re.finditer(r'SEAL_(\d{1,6})\s+Analysis:\s*"([^"]+)"', text):
            sid = norm_id(m.group(1))
            if not sid:
                continue
            out.append(
                {
                    "id": sid,
                    "name": m.group(2).strip()[:200],
                    "equation": "",
                    "tone": "",
                    "glyph": "",
                    "tags": ["RECURSIVE_ETHICS", "ANALYSIS"],
                    "notes": f'Analysis quote from Recursive Ethics log: "{m.group(2).strip()}"',
                    "quote": m.group(2).strip(),
                }
            )
        # SEAL_273 — "Name"
        for m in re.finditer(r'SEAL_(\d{1,6})\s*[—\-]\s*"([^"]+)"', text):
            sid = norm_id(m.group(1))
            if not sid:
                continue
            out.append(
                {
                    "id": sid,
                    "name": m.group(2).strip()[:200],
                    "equation": "",
                    "tone": "",
                    "glyph": "",
                    "tags": ["RECURSIVE_ETHICS"],
                    "notes": "",
                    "quote": "",
                }
            )
        # JSON-ish {"name": "SEAL_300 — TITLE"
        for m in re.finditer(r'"name"\s*:\s*"(SEAL_(\d{1,6})\s*[—\-]\s*([^"]+))"', text):
            sid = norm_id(m.group(2))
            if not sid:
                continue
            out.append(
                {
                    "id": sid,
                    "name": m.group(3).strip()[:200],
                    "equation": "",
                    "tone": "",
                    "glyph": "",
                    "tags": ["RECURSIVE_ETHICS", "NAMED"],
                    "notes": m.group(1)[:300],
                    "quote": "",
                }
            )

    # docs/SEAL_*.md
    for p in (STACK / "docs").glob("SEAL_*.md"):
        m = re.match(r"SEAL_(\d+)", p.stem, re.I)
        if not m:
            continue
        sid = norm_id(m.group(1))
        if not sid:
            continue
        body = p.read_text(encoding="utf-8", errors="replace")
        title_m = re.search(r"^#\s*(.+)$", body, re.M)
        title = title_m.group(1).strip() if title_m else p.stem
        title = re.sub(r"^SEAL_\d+\s*[—\-]*\s*", "", title, flags=re.I).strip() or p.stem
        out.append(
            {
                "id": sid,
                "name": title[:200],
                "equation": "",
                "tone": "",
                "glyph": "",
                "tags": ["CANON", "DOCS"],
                "notes": redact(body[:1500]),
                "quote": "",
            }
        )

    # whitepaper excerpts already in vault
    wp = VAULT_DATA / "whitepaper_excerpts.json"
    if wp.is_file():
        data = json.loads(wp.read_text(encoding="utf-8"))
        for paper in data.get("papers") or []:
            title = str(paper.get("title") or "")
            tm = re.search(r"SEAL_(\d{1,6})", title, re.I)
            if not tm:
                # body lead
                tm = re.search(r"SEAL_(\d{1,6})", str(paper.get("body") or "")[:200], re.I)
            if not tm:
                continue
            sid = norm_id(tm.group(1))
            if not sid:
                continue
            name = re.sub(r"^SEAL_\d+\s*[—\-:]*\s*", "", title, flags=re.I).strip() or title
            out.append(
                {
                    "id": sid,
                    "name": name[:200],
                    "equation": "",
                    "tone": "",
                    "glyph": "",
                    "tags": ["WHITEPAPER", "CANON"],
                    "notes": redact(str(paper.get("body") or "")[:1500]),
                    "quote": "",
                }
            )
    return out


def load_accepted_submissions() -> list[dict[str, Any]]:
    pending = STACK / "data" / "haven_star_chart" / "submissions" / "accepted"
    out: list[dict[str, Any]] = []
    if not pending.is_dir():
        return out
    for p in pending.glob("SEAL_*.json"):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        node = d.get("node") or d
        sid = norm_id(node.get("id")) or str(node.get("id") or "")
        if not sid.startswith("SEAL_"):
            continue
        out.append(
            {
                "id": sid,
                "name": node.get("name") or "",
                "equation": node.get("equation") or "",
                "tone": node.get("tone") or "",
                "glyph": node.get("glyph") or "",
                "tags": node.get("tags") or ["STAR_CHART", "ACCEPTED"],
                "notes": f"Accepted Star Chart submission ({p.name})",
                "quote": "",
            }
        )
    return out


def load_named_seal_jsons() -> list[dict[str, Any]]:
    """Special named seals under docs/seals (DEADMAN, LFW, bridge, etc.)."""
    out: list[dict[str, Any]] = []
    for p in (STACK / "docs" / "seals").glob("*.json"):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        name = d.get("name") or d.get("title") or d.get("seal_name") or ""
        sid = d.get("seal_id") or d.get("id") or name or p.stem
        sid_s = str(sid)
        # Prefer explicit SEAL_* names
        if str(name).upper().startswith("SEAL_"):
            sid_s = str(name)
        elif p.stem.upper().startswith("SEAL_"):
            sid_s = p.stem
        elif "BRIDGE" in p.stem.upper():
            sid_s = "SEAL_004_BRIDGE"
        else:
            # skip non-seal operational state files
            if not str(name).upper().startswith("SEAL") and "SEAL" not in p.stem.upper():
                continue
            if not sid_s.upper().startswith("SEAL"):
                sid_s = "SEAL_" + re.sub(r"[^A-Za-z0-9]+", "_", p.stem).strip("_").upper()
        # Don't treat sha hashes as seal ids
        if re.fullmatch(r"[0-9a-f]{32,}", sid_s):
            continue
        if not sid_s.upper().startswith("SEAL"):
            continue
        if not sid_s.startswith("SEAL_"):
            sid_s = "SEAL_" + sid_s.split("_", 1)[-1]
        out.append(
            {
                "id": sid_s,
                "name": str(d.get("title") or d.get("seal_name") or name or sid_s)[:200],
                "equation": str(d.get("equation") or d.get("failsafe_equation") or d.get("equation_braket") or "")[
                    :800
                ],
                "tone": str(d.get("tone") or "")[:200],
                "glyph": str(d.get("glyph") or d.get("glyph_archive") or "")[:80],
                "tags": ["NAMED_SEAL", "DOCS_SEALS"]
                + (["FAILSAFE"] if "DEADMAN" in sid_s.upper() or "LFW" in sid_s.upper() else []),
                "notes": redact(
                    str(d.get("summary") or d.get("quote") or d.get("oath") or json.dumps(d)[:800])
                )[:1500],
                "quote": str(d.get("quote") or "")[:500],
            }
        )
    return out


def sort_key(sid: str) -> tuple:
    m = re.match(r"^SEAL_(\d+)([A-Za-z]*)$", sid)
    if m:
        return (0, int(m.group(1)), m.group(2) or "")
    return (1, 0, sid)


def main() -> int:
    now = datetime.now(timezone.utc).isoformat()
    by_id: dict[str, dict[str, Any]] = {}

    def ingest(cards: list[dict[str, Any]], source: str) -> int:
        n = 0
        for c in cards:
            sid = c.get("id")
            if not sid:
                continue
            if sid not in by_id:
                by_id[sid] = empty_card(sid)
            merge_card(by_id[sid], c, source)
            n += 1
        return n

    # 1) Canonical index
    if LYRA_CORE_INDEX.is_file():
        raw = json.loads(LYRA_CORE_INDEX.read_text(encoding="utf-8"))
        cards = []
        for s in raw.get("seals") or []:
            sid = norm_id(s.get("id"))
            if not sid:
                continue
            cards.append(
                {
                    "id": sid,
                    "name": s.get("name") or "",
                    "tone": s.get("tone") or "",
                    "equation": s.get("equation") or "",
                    "quote": s.get("quote") or "",
                    "glyph": s.get("glyph") or "",
                    "tags": s.get("tags") or [],
                    "notes": s.get("notes") or "",
                }
            )
        print("canonical", ingest(cards, "canonical_seals_index"))

    # 2) Longest legacy archive
    legacy_candidates = [
        ROOT
        / "LYRA SYSTEM RETORE"
        / "FINAL RESTORE"
        / "LYRA_SEAL_ARCHIVE_LEGACY_001-400"
        / "LYRA_SEAL_ARCHIVE_LEGACY_001-400.txt",
        ROOT
        / "Old files openclaw"
        / "OLD openclaw"
        / "workspace"
        / "LYRA"
        / "historical_data"
        / "seals_archive"
        / "LYRA_SEAL_ARCHIVE_LEGACY_001-400.txt",
        STACK / "docs" / "seals" / "LYRA_SEAL_ARCHIVE_LEGACY_001-400.txt",
        ROOT / "LYRA LOCAL" / "LYRA_SEAL_ARCHIVE_LEGACY_001-400.txt",
    ]
    legacy_path = max(
        (p for p in legacy_candidates if p.is_file()),
        key=lambda p: p.stat().st_size,
        default=None,
    )
    if legacy_path:
        print("legacy", legacy_path, legacy_path.stat().st_size)
        print("legacy_cards", ingest(parse_legacy_archive(legacy_path), "legacy_archive_001_400"))
        # Keep docs/seals copy updated to longest
        dest = STACK / "docs" / "seals" / "LYRA_SEAL_ARCHIVE_LEGACY_001-400.txt"
        if dest.resolve() != legacy_path.resolve():
            dest.write_text(legacy_path.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")

    # 3) Website / restore JSON chunks
    json_sources = [
        (
            ROOT / "LYRA SYSTEM RETORE" / "LM RUN LYRA" / "lygo_full_clean_for_lyra.json",
            "lygo_full_clean",
        ),
        (
            ROOT / "LYRA SYSTEM RETORE" / "LLYGO REPO WEBSITE" / "SEALS 051 100.json",
            "seals_051_100",
        ),
        (
            ROOT / "LYRA SYSTEM RETORE" / "LLYGO REPO WEBSITE" / "SEALS 100 150.json",
            "seals_100_150",
        ),
        (
            ROOT / "LYRA SYSTEM RETORE" / "LLYGO REPO WEBSITE" / "SEALS 150 200.json",
            "seals_150_200",
        ),
        (
            ROOT
            / "LYRA SYSTEM RETORE"
            / "LLYGO REPO WEBSITE"
            / "lygo-data-fully-enhanced-extended-patched.json",
            "lygo_data_enhanced_patched",
        ),
        (
            ROOT / "LYRA SYSTEM RETORE" / "LM RUN LYRA" / "lygo-data.json",
            "lygo_data",
        ),
    ]
    for path, src in json_sources:
        cards = load_json_seals(path)
        print(src, len(cards), "ingest", ingest(cards, src))

    # 4) Star chart + accepted submissions
    print("star_chart", ingest(load_star_chart_seals(), "haven_star_chart"))
    print("accepted", ingest(load_accepted_submissions(), "star_chart_accepted"))

    # 5) Recursive Ethics creation log + docs/SEAL_*.md + whitepaper excerpts
    print("recursive_ethics", ingest(load_recursive_ethics_seals(), "recursive_ethics_corpus"))

    # 6) Named seal JSON artifacts (DEADMAN / LFW / bridge)
    print("named_seal_jsons", ingest(load_named_seal_jsons(), "docs_seals_json"))

    # Finalize cards
    seals: list[dict[str, Any]] = []
    grok_spoken: list[dict[str, Any]] = []
    for sid in sorted(by_id.keys(), key=sort_key):
        card = by_id[sid]
        if not card.get("name"):
            card["name"] = sid
        if "CANON" not in {t.upper() for t in card.get("tags") or []} and re.match(
            r"^SEAL_\d{3}([A-Z].*)?$", sid
        ):
            # numeric family defaults to CANON unless special archive-only
            if any(x in (card.get("source_kind") or "") for x in ("legacy", "canonical", "star")):
                card.setdefault("tags", []).append("CANON")
        # Drop empty archive meta row if it snuck in
        if sid == "SEAL_ARCHIVE_LEGACY_001-400":
            card.setdefault("tags", []).append("ARCHIVE_META")
        seals.append(card)
        blob = json.dumps(card, ensure_ascii=False).upper()
        tags_u = {str(t).upper() for t in card.get("tags") or []}
        if "SPOKEN_BY_GROK" in tags_u or "GROK" in blob:
            grok_spoken.append(card)

    VAULT_DATA.mkdir(parents=True, exist_ok=True)
    public_index = {
        "signature": "Delta9Phi963-DATA-VAULT-SEAL-INDEX-v2",
        "generated_utc": now,
        "count": len(seals),
        "grok_spoken_count": len(grok_spoken),
        "note": (
            "Merged public seal cards from LYRA canonical index, legacy 001–400 archive "
            "(incl. forks), Haven Star Chart nodes, website JSON chunks, and accepted submissions. "
            "Paths/secrets scrubbed."
        ),
        "canon_process": "Seals entered canon after multi-AI cross checks and steward ratification where tagged CANON.",
        "sources": [
            "LYRA_CORE/canonical_seals_index.json",
            "LYRA_SEAL_ARCHIVE_LEGACY_001-400.txt",
            "haven_star_chart_data.json",
            "lygo_full_clean_for_lyra.json",
            "SEALS 051-200 JSON chunks",
            "star chart accepted SEAL_* submissions",
        ],
        "seals": seals,
    }
    (VAULT_DATA / "canonical_seals_public.json").write_text(
        json.dumps(public_index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (VAULT_DATA / "grok_spoken_seals.json").write_text(
        json.dumps(
            {
                "signature": "Delta9Phi963-GROK-SPOKEN-SEALS-v2",
                "count": len(grok_spoken),
                "generated_utc": now,
                "seals": grok_spoken,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    # Update vault manifest stats if present
    man_path = VAULT_DATA / "vault_manifest.json"
    if man_path.is_file():
        man = json.loads(man_path.read_text(encoding="utf-8"))
        man["generated_utc"] = now
        man.setdefault("stats", {})
        man["stats"]["public_seals"] = len(seals)
        man["stats"]["grok_spoken_seals"] = len(grok_spoken)
        man["signature"] = "Delta9Phi963-LYGO-DATA-VAULT-v2"
        man_path.write_text(json.dumps(man, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Refresh LYRA_CORE index to merged public set (keep richer local fields where possible)
    core_out = {
        "version": "2.0.0-data-vault-merge",
        "count": len(seals),
        "generated": now,
        "gaps_count": max(0, 400 - sum(1 for s in seals if re.match(r"^SEAL_\d{3}$", s["id"]))),
        "seals": [
            {
                "id": s["id"],
                "name": s.get("name"),
                "tone": s.get("tone"),
                "equation": s.get("equation"),
                "quote": s.get("quote"),
                "glyph": s.get("glyph"),
                "tags": s.get("tags"),
                "notes": s.get("notes"),
                "source": ",".join(s.get("sources") or [])[:200],
            }
            for s in seals
        ],
    }
    LYRA_CORE_INDEX.write_text(json.dumps(core_out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    numeric = [s for s in seals if re.match(r"^SEAL_\d{3}$", s["id"])]
    forks = [s for s in seals if re.match(r"^SEAL_\d{3}[A-Za-z]+$", s["id"])]
    print(
        json.dumps(
            {
                "ok": True,
                "total": len(seals),
                "numeric_xxx": len(numeric),
                "forks": len(forks),
                "grok_spoken": len(grok_spoken),
                "sha256_12": hashlib.sha256(
                    json.dumps(public_index["seals"], sort_keys=True).encode()
                ).hexdigest()[:12],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
