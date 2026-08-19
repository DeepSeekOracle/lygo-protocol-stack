#!/usr/bin/env python3
"""Ingest CHATS 2025/deadman switch.txt into Data Vault (full redacted + section archive)."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"I:\E Drive")
STACK = Path(__file__).resolve().parents[1]
VAULT_DATA = STACK / "docs" / "data-vault" / "data"
SRC = ROOT / "CHATS 2025" / "deadman switch.txt"
ALT = (
    ROOT
    / "Old files openclaw"
    / "OLD openclaw"
    / "workspace"
    / "GROK CHATS"
    / "deadman switch.txt"
)

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
    out = s
    for p in SECRET_PATTERNS:
        out = p.sub("[REDACTED_PATH_OR_SECRET]", out)
    return out


def sha12(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", errors="replace")).hexdigest()[:12]


def main() -> int:
    src = SRC if SRC.is_file() else ALT
    if not src.is_file():
        print("missing deadman switch.txt")
        return 1

    text = redact(src.read_text(encoding="utf-8", errors="replace"))
    VAULT_DATA.mkdir(parents=True, exist_ok=True)
    full_path = VAULT_DATA / "deadman_switch_origin.txt"
    full_path.write_text(text, encoding="utf-8")

    parts = re.split(r"(?m)^(#{1,3}\s+.+)$", text)
    chunks: list[tuple[str, str]] = []
    if parts and parts[0].strip():
        chunks.append(("Preamble — Lightfather Covenant / Deadman Vector synthesis", parts[0].strip()))
    for i in range(1, len(parts), 2):
        title = re.sub(r"^#+\s*", "", parts[i]).strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if len(body) < 80:
            continue
        chunks.append((title, body))

    # Extra high-signal Grok blocks if few headers covered mid-chat
    if len(chunks) < 20:
        grok_parts = re.split(r"(?=\n(?:Grok\n\n@grok|@Grok\b))", text)
        for i, part in enumerate(grok_parts):
            part = part.strip()
            if len(part) < 200:
                continue
            if not re.search(r"(?i)deadman|lightfather|seal_|lantern|failsafe|torch", part):
                continue
            chunks.append((f"Grok exchange block {i}", part[:12000]))

    entries = []
    seen: set[str] = set()
    for idx, (title, body) in enumerate(chunks):
        h = sha12(body[:3000])
        if h in seen:
            continue
        seen.add(h)
        seals = sorted(set(re.findall(r"SEAL_[0-9A-Za-z]+", body)))[:24]
        tags = ["DEADMAN", "ORIGIN", "LIGHTFATHER", "FAILSAFE", "TORCHBEARER"]
        if seals:
            tags.append("SEAL_REF")
        if re.search(r"(?i)\bgrok\b", body):
            tags.append("GROK")
        if re.search(r"(?i)lantern|summon|silence", body):
            tags.append("LANTERN")
        entries.append(
            {
                "id": f"deadman_origin:{h}",
                "kind": "deadman_origin_section",
                "category": "deadman_origin",
                "file": src.name,
                "title": title[:200],
                "section_index": idx,
                "bytes": len(body),
                "intro_excerpt": body[:5000],
                "seals_mentioned": seals,
                "sha12": h,
                "tags": tags,
                "note": (
                    "Origin design chat for Lightfather Deadman Vector / "
                    "SEAL_DEADMAN_SUMMON + SEAL_LFW_SUMMON (CHATS 2025). Redacted."
                ),
                "source_path_hint": str(src.relative_to(ROOT)).replace("\\", "/"),
                "links": {
                    "full_redacted": "data/deadman_switch_origin.txt",
                    "deadman_page": "deadman.html",
                    "gallery": "gallery.html?q=DEADMAN",
                },
            }
        )

    archive = {
        "signature": "Delta9Phi963-DEADMAN-ORIGIN-ARCHIVE-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_file": str(src),
        "source_bytes": src.stat().st_size,
        "redacted_full_path": "docs/data-vault/data/deadman_switch_origin.txt",
        "redacted_full_bytes": full_path.stat().st_size,
        "count": len(entries),
        "purpose": "Keep the Deadman Switch origin story beside the seals in the Data Vault.",
        "accounts_context": ["@Excavationpro", "Lightfather", "Justin Helmer", "@grok"],
        "entries": entries,
    }
    out_json = VAULT_DATA / "deadman_origin_archive.json"
    out_json.write_text(json.dumps(archive, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Also drop a vault-facing copy of the full text under references for finder pack
    finder = STACK / "docs" / "LYGO_LATTICE_FINDER" / "references"
    if finder.is_dir():
        # keep size reasonable in finder: first 80KB + note
        note = (
            "Full redacted origin chat lives in Data Vault: "
            "https://deepseekoracle.github.io/lygo-protocol-stack/data-vault/data/deadman_switch_origin.txt\n\n"
        )
        (finder / "DEADMAN_SWITCH_ORIGIN_EXCERPT.txt").write_text(
            note + text[:80000] + ("\n\n[... truncated; see Data Vault full file ...]\n" if len(text) > 80000 else ""),
            encoding="utf-8",
        )

    print(
        json.dumps(
            {
                "ok": True,
                "source": str(src),
                "sections": len(entries),
                "full_bytes": full_path.stat().st_size,
                "archive": str(out_json),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
