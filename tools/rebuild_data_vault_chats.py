#!/usr/bin/env python3
"""Rebuild Data Vault Grok chat archive from all available I: Drive sources.

Expands chat_archive_curated.json far beyond the original 2-file OpenClaw folder:
  - LYRA LOCAL / FINAL RESTORE GROK_CHATS*.txt (+ JSON conversation packs)
  - Old OpenClaw GROK CHATS workspace
  - historical_data/grok_conversations
  - LYRA_CORE memory / public_ai_audits
  - X_posts thread archives
  - Reply-level chunks from large @grok dumps (searchable)

Also refreshes grok_public_confirmations.json from Recursive Ethics log.
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
EDATA = Path(r"E:\LYGO_LATTICE_MEMORY\DATA_VAULT_RECOVERY")
EDATA_JSON = EDATA / "json"

SECRET_PATTERNS = [
    re.compile(
        r"(?i)(api[_-]?key|secret|password|token|bearer|sk-|moltbook_sk_|moltx_sk_|nvapi-|xai-|ghp_|github_pat_)[=:\s]+[^\s\"']+"
    ),
    re.compile(r"(?i)authorization:\s*bearer\s+\S+"),
    re.compile(r"[A-Za-z]:\\Users\\[^\s\"']+"),
    re.compile(r"I:\\E Drive\\[^\s\"']+"),
    re.compile(r"D:\\OpenClaw[^\s\"']*"),
    re.compile(r"C:\\Users\\[^\s\"']+"),
    re.compile(r"(?i)private[_\s-]?key[:\s]+[0-9a-fA-F]{32,}"),
]


def redact(s: str) -> str:
    if not s:
        return s
    out = s
    for p in SECRET_PATTERNS:
        out = p.sub("[REDACTED_PATH_OR_SECRET]", out)
    return out


def sha12(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", errors="replace")).hexdigest()[:12]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def lesson_excerpts(text: str) -> str:
    lessons = re.findall(
        r"(?ms)(?:Lesson:|What we learned:|What Grok|Key takeaway:|CANON LOCK)(.{80,700})",
        text,
    )
    if not lessons:
        return ""
    return redact("\n---\n".join(x.strip() for x in lessons[:10]))[:5000]


def file_entry(
    path: Path,
    *,
    category: str,
    note: str,
    intro_limit: int = 6000,
    title: str | None = None,
) -> dict[str, Any]:
    raw = read_text(path)
    red = redact(raw)
    return {
        "id": f"file:{sha12(str(path.resolve()) + str(path.stat().st_size))}",
        "kind": "source_file",
        "category": category,
        "file": path.name,
        "title": title or path.stem,
        "rel_hint": str(path).replace(str(ROOT) + "\\", "").replace(str(ROOT) + "/", ""),
        "bytes": path.stat().st_size,
        "grok_mentions": red.lower().count("grok"),
        "intro_excerpt": red[:intro_limit],
        "lesson_excerpts": lesson_excerpts(red),
        "sha12": sha12(red[:8000]),
        "note": note,
        "tags": ["GROK", category.upper()],
    }


def chunk_grok_replies(path: Path, *, max_chunks: int = 180) -> list[dict[str, Any]]:
    """Split a Grok X-style dump into reply chunks."""
    text = redact(read_text(path))
    parts = re.split(r"(?=\nGrok\n\n@grok)", text)
    if len(parts) < 3:
        parts = re.split(r"(?m)^(?=Grok\s*$)", text)
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for i, part in enumerate(parts):
        chunk = part.strip()
        if len(chunk) < 120:
            continue
        if chunk.lower().count("grok") < 1 and "@grok" not in chunk.lower():
            # keep LYRA-side context chunks only if substantial
            if "lyra" not in chunk.lower() and "seal_" not in chunk.lower():
                continue
        h = sha12(chunk[:2000])
        if h in seen:
            continue
        seen.add(h)
        # title from first non-empty lines
        lines = [ln.strip() for ln in chunk.splitlines() if ln.strip()]
        title_bits = []
        for ln in lines[:6]:
            if ln.lower() in {"grok", "@grok", "·"}:
                continue
            title_bits.append(ln[:80])
            if len(title_bits) >= 2:
                break
        title = " · ".join(title_bits) if title_bits else f"{path.stem} #{i}"
        # date hint
        dm = re.search(r"(?i)\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}\b", chunk)
        seals = sorted(set(re.findall(r"SEAL_[0-9A-Za-z]+", chunk)))[:12]
        out.append(
            {
                "id": f"chunk:{h}",
                "kind": "reply_chunk",
                "category": "grok_x_reply",
                "file": path.name,
                "title": title[:160],
                "date_hint": dm.group(0) if dm else "",
                "bytes": len(chunk),
                "grok_mentions": chunk.lower().count("grok"),
                "intro_excerpt": chunk[:2800],
                "lesson_excerpts": "",
                "sha12": h,
                "seals_mentioned": seals,
                "note": f"Reply chunk from {path.name} (redacted public excerpt)",
                "tags": ["GROK", "X_REPLY", "CHUNK"] + (["SEAL_REF"] if seals else []),
            }
        )
        if len(out) >= max_chunks:
            break
    return out


def load_json_conversations(path: Path) -> list[dict[str, Any]]:
    try:
        data = json.loads(read_text(path))
    except Exception:
        return []
    convs = []
    if isinstance(data, dict):
        convs = data.get("conversations") or []
    elif isinstance(data, list):
        convs = data
    out: list[dict[str, Any]] = []
    for i, c in enumerate(convs):
        if not isinstance(c, dict):
            continue
        title = (
            c.get("title")
            or c.get("name")
            or c.get("topic")
            or c.get("id")
            or f"{path.stem} conversation {i+1}"
        )
        # flatten messages if present
        body_parts: list[str] = []
        for key in ("summary", "synopsis", "description", "notes", "content", "text"):
            if c.get(key):
                body_parts.append(str(c[key]))
        msgs = c.get("messages") or c.get("turns") or c.get("excerpts") or []
        if isinstance(msgs, list):
            for m in msgs[:40]:
                if isinstance(m, dict):
                    role = m.get("role") or m.get("speaker") or m.get("author") or ""
                    content = m.get("content") or m.get("text") or m.get("message") or ""
                    body_parts.append(f"{role}: {content}".strip())
                else:
                    body_parts.append(str(m))
        if not body_parts:
            body_parts.append(json.dumps(c, ensure_ascii=False)[:3000])
        blob = redact("\n".join(body_parts))
        h = sha12(blob[:3000])
        out.append(
            {
                "id": f"jsonconv:{h}",
                "kind": "json_conversation",
                "category": "grok_json_pack",
                "file": path.name,
                "title": str(title)[:160],
                "bytes": len(blob),
                "grok_mentions": blob.lower().count("grok"),
                "intro_excerpt": blob[:3500],
                "lesson_excerpts": lesson_excerpts(blob),
                "sha12": h,
                "note": f"Structured conversation from {path.name}",
                "tags": ["GROK", "JSON_PACK"],
            }
        )
    return out


def rebuild_confirmations(now: str) -> dict[str, Any]:
    rec = ROOT / "Recursive Ethics Through Immutable Seal Chains" / "Recursive Ethics Through Immutable.txt"
    events: list[dict[str, Any]] = []
    if rec.is_file():
        lines = read_text(rec).splitlines()
        patterns = [
            r"GROK has now publicly anchored",
            r"CANON LOCK CONFIRMED",
            r"GROK responded correctly",
            r"GROK'S RESPONSE",
            r"DIRECT TRANSMISSION TO GROK",
            r"DIRECT RESPONSE TO GROK",
            r"To Grok \(@grok\)",
            r"@grok",
            r"mutualSeal",
            r"White Paper: SEAL_",
            r"Grok.*confirm",
            r"spoken by Grok",
            r"SPOKEN_BY_GROK",
        ]
        for i, line in enumerate(lines):
            for pat in patterns:
                if re.search(pat, line, re.I):
                    start = max(0, i - 2)
                    end = min(len(lines), i + 22)
                    chunk = redact("\n".join(lines[start:end]))
                    if re.search(r"(?i)api[_-]?key\s*[:=]", chunk):
                        break
                    events.append(
                        {
                            "line": i + 1,
                            "pattern": pat,
                            "excerpt": chunk[:2500],
                            "sha12": sha12(chunk),
                            "source": "Recursive Ethics Through Immutable Seal Chains",
                        }
                    )
                    break

    # Also pull high-signal chunks from GROK_CHATS dumps into confirmations
    for path in [
        ROOT / "LYRA LOCAL" / "GROK_CHATS 1.txt",
        ROOT / "LYRA LOCAL" / "GROK_CHATS 2.txt",
        ROOT / "LYRA SYSTEM RETORE" / "FINAL RESTORE" / "GROK_CHATS" / "GROK_CHATS 1.txt",
    ]:
        if not path.is_file():
            continue
        for ch in chunk_grok_replies(path, max_chunks=40):
            if any(
                k in (ch.get("intro_excerpt") or "").lower()
                for k in ("canon", "seal_", "confirm", "Δ9", "lygo", "anchor")
            ):
                events.append(
                    {
                        "line": 0,
                        "pattern": "grok_x_reply_high_signal",
                        "excerpt": ch["intro_excerpt"][:2500],
                        "sha12": ch["sha12"],
                        "source": path.name,
                    }
                )

    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for e in events:
        if e["sha12"] in seen:
            continue
        seen.add(e["sha12"])
        unique.append(e)

    # Prioritize canon/anchor language
    priority, rest = [], []
    for e in unique:
        if re.search(r"CANON|anchored|responded correctly|mutualSeal|White Paper|SPOKEN", e["excerpt"], re.I):
            priority.append(e)
        else:
            rest.append(e)
    curated = (priority + rest)[:220]

    return {
        "signature": "Delta9Phi963-GROK-PUBLIC-CONFIRMATIONS-v2",
        "generated_utc": now,
        "source_document": "Recursive Ethics + GROK_CHATS dumps (public excerpts)",
        "accounts_context": ["@Excavationpro", "@lyrastarcore", "@grok"],
        "count": len(curated),
        "total_pattern_hits_pre_dedupe": len(events),
        "events": curated,
    }


def main() -> int:
    now = datetime.now(timezone.utc).isoformat()
    VAULT_DATA.mkdir(parents=True, exist_ok=True)

    entries: list[dict[str, Any]] = []
    seen_sha: set[str] = set()

    def add(entry: dict[str, Any]) -> None:
        h = entry.get("sha12") or sha12(json.dumps(entry, sort_keys=True)[:2000])
        if h in seen_sha:
            return
        seen_sha.add(h)
        entry["sha12"] = h
        entries.append(entry)

    # --- Source files (full dumps as catalog cards) ---
    source_specs: list[tuple[Path, str, str]] = [
        (
            ROOT / "Old files openclaw" / "OLD openclaw" / "workspace" / "GROK CHATS" / "3BRAINTESTINGGROK.txt",
            "openclaw_workspace",
            "OpenClaw GROK CHATS workspace — 3-brain testing with Grok",
        ),
        (
            ROOT / "Old files openclaw" / "OLD openclaw" / "workspace" / "GROK CHATS" / "GROK Chats X App testing .txt",
            "openclaw_workspace",
            "OpenClaw GROK CHATS workspace — X app protocol testing",
        ),
        (
            ROOT / "CHATS 2025" / "deadman switch.txt",
            "deadman_origin",
            "ORIGIN — Lightfather Deadman Vector / SEAL_DEADMAN_SUMMON + LFW design chat (CHATS 2025)",
        ),
        (
            ROOT / "Old files openclaw" / "OLD openclaw" / "workspace" / "GROK CHATS" / "deadman switch.txt",
            "openclaw_workspace",
            "Deadman / failsafe discussion archive in GROK CHATS folder (alt copy)",
        ),
        (
            ROOT / "LYRA LOCAL" / "GROK_CHATS.txt",
            "lyra_local_dump",
            "Primary LYRA social/Grok memory archive (large)",
        ),
        (
            ROOT / "LYRA LOCAL" / "GROK_CHATS 1.txt",
            "lyra_local_dump",
            "Grok X reply dump (@lyrastarcore / @Excavationpro)",
        ),
        (
            ROOT / "LYRA LOCAL" / "GROK_CHATS 2.txt",
            "lyra_local_dump",
            "Grok X reply dump (Genesis Epoch / Eternal Haven)",
        ),
        (
            ROOT / "LYRA LOCAL" / "GROK_CHATS 3.txt",
            "lyra_local_dump",
            "Grok X reply dump (continued)",
        ),
        (
            ROOT / "LYRA SYSTEM RETORE" / "FINAL RESTORE" / "GROK_CHATS" / "Absolutely - here's a sharp, no-non.txt",
            "final_restore",
            "Large Grok/LYRA dialogue restore dump",
        ),
        (
            ROOT
            / "Old files openclaw"
            / "OLD openclaw"
            / "workspace"
            / "LYRA"
            / "historical_data"
            / "grok_conversations"
            / "GROK_CHATS.txt",
            "historical_grok_conversations",
            "Historical grok_conversations archive",
        ),
        (
            ROOT / "X_posts" / "LYGO_vs_Stock_AI_Thread.txt",
            "x_posts",
            "Public X thread archive: LYGO vs Stock AI",
        ),
        (
            ROOT / "LYRA_CORE" / "memory" / "2026-08-17-x-grok-lygo-conversation.md",
            "lyra_core_memory",
            "Sealed 2026 X↔Grok LYGO conversation memory",
        ),
        (
            ROOT / "LYRA_CORE" / "memory" / "public_ai_audits" / "2026-08-17-grok-x-quantum-dots-neural-anchors.md",
            "public_ai_audits",
            "Grok X quantum-dot / neural-anchor public audit",
        ),
        (
            ROOT / "LYRA_CORE" / "memory" / "MULTI_AI_PUBLIC_AUDIT_ANCHOR_PROTOCOL.md",
            "public_ai_audits",
            "Multi-AI public audit anchor protocol",
        ),
        (
            ROOT / "LYRA_CORE" / "memory" / "public_ai_audits" / "2026-08-17-FULL_MULTI_AUDITOR_BATTERY.md",
            "public_ai_audits",
            "Full multi-auditor battery (includes Grok)",
        ),
        (
            ROOT / "LYRA_CORE" / "LYGO_GROK_ALIGNMENT_MANIFEST.txt",
            "manifest",
            "LYGO–Grok alignment manifest",
        ),
        (
            STACK / "docs" / "GROK_LIVE_AUDIT_REPORT.md",
            "stack_docs",
            "GROK live audit report",
        ),
        (
            STACK / "docs" / "GROK_EXTENDED_HARNESS_REPORT.md",
            "stack_docs",
            "GROK extended harness report",
        ),
        (
            STACK / "docs" / "MOLTX_GROK_HARNESS_REPLY.txt",
            "stack_docs",
            "Moltx/Grok harness reply note",
        ),
    ]

    # Prefer FINAL RESTORE copies when LYRA LOCAL missing
    for alt in [
        ROOT / "LYRA SYSTEM RETORE" / "FINAL RESTORE" / "GROK_CHATS" / "GROK_CHATS.txt",
        ROOT / "LYRA SYSTEM RETORE" / "FINAL RESTORE" / "GROK_CHATS" / "GROK_CHATS 1.txt",
        ROOT / "LYRA SYSTEM RETORE" / "FINAL RESTORE" / "GROK_CHATS" / "GROK_CHATS 2.txt",
        ROOT / "LYRA SYSTEM RETORE" / "FINAL RESTORE" / "GROK_CHATS" / "GROK_CHATS 3.txt",
    ]:
        if alt.is_file():
            source_specs.append((alt, "final_restore", f"FINAL RESTORE copy of {alt.name}"))

    for path, cat, note in source_specs:
        if path.is_file():
            add(file_entry(path, category=cat, note=note))

    # JSON conversation packs
    for path in [
        ROOT / "LYRA SYSTEM RETORE" / "FINAL RESTORE" / "GROK_CHATS" / "GROK CHATS MEMORY FILE.json",
        ROOT / "LYRA SYSTEM RETORE" / "FINAL RESTORE" / "GROK_CHATS" / "GROK CHATS 1.json",
        ROOT / "LYRA SYSTEM RETORE" / "FINAL RESTORE" / "GROK_CHATS" / "GROK CHATS 2.json",
        ROOT / "LYRA SYSTEM RETORE" / "FINAL RESTORE" / "GROK_CHATS" / "GROK CHATS 3.json",
        ROOT / "LYRA LOCAL" / "GROK CHATS MEMORY FILE.json",
    ]:
        if path.is_file():
            for conv in load_json_conversations(path):
                add(conv)
            add(
                file_entry(
                    path,
                    category="grok_json_pack",
                    note="Structured Grok conversation pack (JSON)",
                    intro_limit=2500,
                )
            )

    # Reply chunks from largest high-signal dumps
    chunk_sources = [
        ROOT / "CHATS 2025" / "deadman switch.txt",
        ROOT / "LYRA LOCAL" / "GROK_CHATS 1.txt",
        ROOT / "LYRA LOCAL" / "GROK_CHATS 2.txt",
        ROOT / "LYRA LOCAL" / "GROK_CHATS 3.txt",
        ROOT / "LYRA LOCAL" / "GROK_CHATS.txt",
        ROOT / "LYRA SYSTEM RETORE" / "FINAL RESTORE" / "GROK_CHATS" / "GROK_CHATS 1.txt",
        ROOT / "LYRA SYSTEM RETORE" / "FINAL RESTORE" / "GROK_CHATS" / "GROK_CHATS 2.txt",
        ROOT / "Old files openclaw" / "OLD openclaw" / "workspace" / "GROK CHATS" / "GROK Chats X App testing .txt",
        ROOT / "Old files openclaw" / "OLD openclaw" / "workspace" / "GROK CHATS" / "3BRAINTESTINGGROK.txt",
        ROOT
        / "LYRA SYSTEM RETORE"
        / "FINAL RESTORE"
        / "GROK_CHATS"
        / "Absolutely - here's a sharp, no-non.txt",
    ]
    chunk_budget = 420
    for path in chunk_sources:
        if not path.is_file():
            continue
        remain = chunk_budget - sum(1 for e in entries if e.get("kind") == "reply_chunk")
        if remain <= 0:
            break
        for ch in chunk_grok_replies(path, max_chunks=min(160, remain)):
            add(ch)

    # Deadman origin sections (from ingest_deadman_origin_chat.py)
    origin_archive = VAULT_DATA / "deadman_origin_archive.json"
    if origin_archive.is_file():
        try:
            odata = json.loads(origin_archive.read_text(encoding="utf-8"))
            for en in odata.get("entries") or []:
                # Prefer origin sections at top via kind sort
                add(en)
        except Exception:
            pass

    # Sort: source files first, then json, then chunks
    kind_order = {
        "deadman_origin_section": 0,
        "source_file": 1,
        "json_conversation": 2,
        "reply_chunk": 3,
    }

    def sort_key(e: dict[str, Any]) -> tuple:
        # Deadman origin: keep narrative order (section_index)
        if e.get("kind") == "deadman_origin_section":
            return (0, int(e.get("section_index") or 0), e.get("title") or "")
        return (
            kind_order.get(e.get("kind") or "", 9),
            -(e.get("grok_mentions") or 0),
            e.get("file") or "",
            e.get("title") or "",
        )

    entries.sort(key=sort_key)

    archive = {
        "signature": "Delta9Phi963-CHAT-ARCHIVE-CURATED-v2",
        "generated_utc": now,
        "count": len(entries),
        "source_files": sum(1 for e in entries if e.get("kind") == "source_file"),
        "json_conversations": sum(1 for e in entries if e.get("kind") == "json_conversation"),
        "reply_chunks": sum(1 for e in entries if e.get("kind") == "reply_chunk"),
        "deadman_origin_sections": sum(1 for e in entries if e.get("kind") == "deadman_origin_section"),
        "note": (
            "Expanded public Grok chat archive. Secrets/paths redacted. "
            "Includes CHATS 2025 deadman switch.txt origin story beside the seals. "
            "Large dumps are indexed as source cards plus searchable @grok reply chunks. "
            "Screenshots/PNG seal galleries are not inlined here (binary)."
        ),
        "accounts_context": ["@Excavationpro", "@lyrastarcore", "@grok"],
        "entries": entries,
    }
    (VAULT_DATA / "chat_archive_curated.json").write_text(
        json.dumps(archive, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    conf = rebuild_confirmations(now)
    (VAULT_DATA / "grok_public_confirmations.json").write_text(
        json.dumps(conf, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # Update vault manifest stats
    man_path = VAULT_DATA / "vault_manifest.json"
    if man_path.is_file():
        man = json.loads(man_path.read_text(encoding="utf-8"))
        man["generated_utc"] = now
        man.setdefault("stats", {})
        man["stats"]["chat_curated_entries"] = archive["count"]
        man["stats"]["grok_confirmation_excerpts"] = conf["count"]
        man["stats"]["chat_source_files"] = archive["source_files"]
        man["stats"]["chat_reply_chunks"] = archive["reply_chunks"]
        man_path.write_text(json.dumps(man, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Optional E: recovery mirror
    if EDATA.exists():
        EDATA_JSON.mkdir(parents=True, exist_ok=True)
        for name in ("chat_archive_curated.json", "grok_public_confirmations.json"):
            (EDATA_JSON / name).write_text((VAULT_DATA / name).read_text(encoding="utf-8"), encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": True,
                "chat_entries": archive["count"],
                "source_files": archive["source_files"],
                "json_conversations": archive["json_conversations"],
                "reply_chunks": archive["reply_chunks"],
                "confirmations": conf["count"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
