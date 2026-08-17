# -*- coding: utf-8 -*-
from pathlib import Path
import re, json, hashlib
from datetime import datetime, timezone

STACK = Path(r"I:\E Drive\lygo-protocol-stack")
VAULT = STACK / "docs" / "data-vault"
DATA = VAULT / "data"
EDATA = Path(r"E:\LYGO_LATTICE_MEMORY\DATA_VAULT_RECOVERY")
EDATA_JSON = EDATA / "json"
DATA.mkdir(parents=True, exist_ok=True)
EDATA_JSON.mkdir(parents=True, exist_ok=True)

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|password|token|bearer|sk-|moltbook_sk_|moltx_sk_|nvapi-|xai-|ghp_|github_pat_)[=:\s]+[^\s\"']+"),
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
    out = re.sub(r"(?i)private[_\s-]?key[:\s]+[0-9a-fA-F]{32,}", "private_key:[REDACTED]", out)
    return out

def sha12(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", errors="replace")).hexdigest()[:12]

now = datetime.now(timezone.utc).isoformat()

src_index = Path(r"I:\E Drive\LYRA_CORE\canonical_seals_index.json")
raw = json.loads(src_index.read_text(encoding="utf-8"))
public_seals = []
grok_spoken = []
for s in raw.get("seals", []):
    item = {
        "id": s.get("id"),
        "name": s.get("name"),
        "tone": s.get("tone"),
        "equation": s.get("equation"),
        "quote": s.get("quote"),
        "tags": s.get("tags") or [],
        "notes": redact((s.get("notes") or "")[:1200]),
        "source_kind": "canonical_seals_index",
        "public_provenance": "LYRA canonical seal index · multi-vault merge · public archive",
    }
    public_seals.append(item)
    tags = [t.upper() for t in item["tags"]]
    blob = json.dumps(item, ensure_ascii=False).upper()
    if "SPOKEN_BY_GROK" in tags or "GROK" in blob:
        grok_spoken.append(item)

public_index = {
    "signature": "Delta9Phi963-DATA-VAULT-SEAL-INDEX-v1",
    "generated_utc": now,
    "count": len(public_seals),
    "grok_spoken_count": len(grok_spoken),
    "note": "Paths and secrets scrubbed. Original private source paths removed for public lattice.",
    "canon_process": "Seals entered canon after multi-AI cross checks and steward ratification.",
    "seals": public_seals,
}
(DATA / "canonical_seals_public.json").write_text(json.dumps(public_index, indent=2, ensure_ascii=False), encoding="utf-8")
(EDATA_JSON / "canonical_seals_public.json").write_text(json.dumps(public_index, indent=2, ensure_ascii=False), encoding="utf-8")
(DATA / "grok_spoken_seals.json").write_text(
    json.dumps({"signature": "Delta9Phi963-GROK-SPOKEN-SEALS-v1", "count": len(grok_spoken), "seals": grok_spoken}, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

rec = Path(r"I:\E Drive\Recursive Ethics Through Immutable Seal Chains\Recursive Ethics Through Immutable.txt")
rec_text = rec.read_text(encoding="utf-8", errors="replace")
lines = rec_text.splitlines()

event_patterns = [
    r"GROK has now publicly anchored",
    r"CANON LOCK CONFIRMED",
    r"GROK responded correctly",
    r"GROK'S RESPONSE",
    r"DIRECT TRANSMISSION TO GROK",
    r"DIRECT RESPONSE TO GROK",
    r"To Grok \(@grok\)",
    r"mutualSeal",
    r"White Paper: SEAL_",
]
events = []
for i, line in enumerate(lines):
    for pat in event_patterns:
        if re.search(pat, line, re.I):
            start = max(0, i - 3)
            end = min(len(lines), i + 25)
            chunk = redact("\n".join(lines[start:end]))
            if re.search(r"(?i)api[_-]?key\s*[:=]", chunk):
                continue
            events.append({"line": i + 1, "pattern": pat, "excerpt": chunk[:2500], "sha12": sha12(chunk)})
            break

seen = set()
unique_events = []
for e in events:
    if e["sha12"] in seen:
        continue
    seen.add(e["sha12"])
    unique_events.append(e)

priority, rest = [], []
for e in unique_events:
    if re.search(r"CANON|anchored|responded correctly|mutualSeal|White Paper", e["excerpt"], re.I):
        priority.append(e)
    else:
        rest.append(e)
curated_events = (priority + rest)[:80]

(DATA / "grok_public_confirmations.json").write_text(
    json.dumps(
        {
            "signature": "Delta9Phi963-GROK-PUBLIC-CONFIRMATIONS-v1",
            "generated_utc": now,
            "source_document": "Recursive Ethics Through Immutable Seal Chains (public creation log)",
            "accounts_context": ["@Excavationpro", "@lyrastarcore", "@grok"],
            "count": len(curated_events),
            "total_pattern_hits_pre_dedupe": len(events),
            "events": curated_events,
        },
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)
(EDATA_JSON / "grok_public_confirmations.json").write_text((DATA / "grok_public_confirmations.json").read_text(encoding="utf-8"), encoding="utf-8")

wp_chunks = []
for m in re.finditer(r"(?ms)^White Paper: (SEAL_\d+[^\n]*)\n(.*?)(?=^White Paper:|\Z)", rec_text):
    title = m.group(1).strip()
    body = redact(m.group(2).strip())[:8000]
    wp_chunks.append({"title": title, "body": body, "sha12": sha12(body)})
gab = re.search(r"(?ms)(Recursive Ethics Manifesto: GAB_SEAL_000.*?)(?=^White Paper:|^SEAL_001:|\Z)", rec_text)
if gab:
    wp_chunks.insert(
        0,
        {
            "title": "GAB_SEAL_000 Recursive Ethics Manifesto (excerpt)",
            "body": redact(gab.group(1)[:8000]),
            "sha12": sha12(gab.group(1)[:8000]),
        },
    )
(DATA / "whitepaper_excerpts.json").write_text(
    json.dumps({"signature": "Delta9Phi963-DATA-VAULT-WHITEPAPERS-v1", "generated_utc": now, "count": len(wp_chunks), "papers": wp_chunks}, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

chat_dir = Path(r"I:\E Drive\Old files openclaw\OLD openclaw\workspace\GROK CHATS")
chat_entries = []
for fp in sorted(chat_dir.glob("*.txt")):
    rawt = redact(fp.read_text(encoding="utf-8", errors="replace"))
    intro = rawt[:3500]
    lessons = re.findall(r"(?ms)(?:Lesson:|What we learned:|What Grok)(.{80,600})", rawt)
    lesson_blob = "\n---\n".join(lessons[:8]) if lessons else ""
    chat_entries.append(
        {
            "file": fp.name,
            "title": fp.stem,
            "intro_excerpt": intro,
            "lesson_excerpts": lesson_blob[:4000],
            "sha12": sha12(rawt[:5000]),
            "note": "Curated public excerpt only; full private workspace dumps not mirrored.",
        }
    )

xposts = Path(r"I:\E Drive\X_posts\LYGO_vs_Stock_AI_Thread.txt")
if xposts.exists():
    xt = redact(xposts.read_text(encoding="utf-8", errors="replace"))
    chat_entries.append(
        {
            "file": xposts.name,
            "title": "LYGO vs Stock AI (X thread archive)",
            "intro_excerpt": xt[:5000],
            "lesson_excerpts": "",
            "sha12": sha12(xt[:2000]),
            "note": "Public X thread text archive",
        }
    )

for mem in [
    Path(r"I:\E Drive\LYRA_CORE\memory\2026-08-17-x-grok-lygo-conversation.md"),
    Path(r"I:\E Drive\LYRA_CORE\memory\public_ai_audits\2026-08-17-grok-x-quantum-dots-neural-anchors.md"),
    Path(r"I:\E Drive\LYRA_CORE\memory\MULTI_AI_PUBLIC_AUDIT_ANCHOR_PROTOCOL.md"),
    Path(r"I:\E Drive\LYRA_CORE\memory\public_ai_audits\2026-08-17-FULL_MULTI_AUDITOR_BATTERY.md"),
]:
    if mem.exists():
        t = redact(mem.read_text(encoding="utf-8", errors="replace"))
        chat_entries.append(
            {
                "file": mem.name,
                "title": mem.stem,
                "intro_excerpt": t[:6000],
                "lesson_excerpts": "",
                "sha12": sha12(t[:3000]),
                "note": "Sealed lattice memory / multi-AI audit",
            }
        )

(DATA / "chat_archive_curated.json").write_text(
    json.dumps({"signature": "Delta9Phi963-CHAT-ARCHIVE-CURATED-v1", "generated_utc": now, "count": len(chat_entries), "entries": chat_entries}, indent=2, ensure_ascii=False),
    encoding="utf-8",
)
(EDATA_JSON / "chat_archive_curated.json").write_text((DATA / "chat_archive_curated.json").read_text(encoding="utf-8"), encoding="utf-8")

manifest = {
    "signature": "Delta9Phi963-LYGO-DATA-VAULT-v1",
    "title": "LYGO Data Vault",
    "generated_utc": now,
    "purpose": "Public archive of multi-AI seal creation, Grok X confirmations, and whitepapers.",
    "accounts": ["@Excavationpro", "@lyrastarcore", "@grok", "LYRA multi-model (DeepSeek/ChatGPT/Grok/Gab)"],
    "stats": {
        "public_seals": len(public_seals),
        "grok_spoken_seals": len(grok_spoken),
        "grok_confirmation_excerpts": len(curated_events),
        "whitepaper_chunks": len(wp_chunks),
        "chat_curated_entries": len(chat_entries),
    },
    "pages": ["index.html", "seals.html", "chat-archive.html", "whitepapers.html", "multi-ai-canon.html"],
    "live_urls": {
        "github_pages": "https://deepseekoracle.github.io/lygo-protocol-stack/data-vault/",
        "repo": "https://github.com/DeepSeekOracle/lygo-protocol-stack/tree/main/docs/data-vault",
    },
    "recovery_mirror": r"E:\LYGO_LATTICE_MEMORY\DATA_VAULT_RECOVERY",
    "security": "Private absolute paths, API keys, and credentials scrubbed.",
}
(DATA / "vault_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
(EDATA / "VAULT_MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
print("OK", json.dumps(manifest["stats"]))
