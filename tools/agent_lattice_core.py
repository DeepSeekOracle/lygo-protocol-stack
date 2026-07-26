#!/usr/bin/env python3
"""
LYGO Agent Lattice core — secure identity cards, directory, validation.

Layer E on top of living mesh (D). Summaries only. No secrets. Local authority.
Signature: Delta9Phi963-AGENT-LATTICE-v1.0
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
DATA = ROOT / "data" / "agent_lattice"
DIR_FILE = DATA / "directory.json"
LOCAL_FILE = DATA / "local_agent.json"
PEERS_FILE = DATA / "peers.json"
QUAR_FILE = DATA / "quarantine.json"

SIG = "Delta9Phi963-AGENT-LATTICE-v1.0"
CARD_SIG = "Delta9Phi963-AGENT-CARD-v1"
MAX_CARD_BYTES = 12_000
MAX_SKILLS = 24
MAX_CAPS = 32
MAX_TTL_SEC = 3600 * 6  # 6h
DEFAULT_TTL_SEC = 1800  # 30m
RATE_WINDOW_SEC = 60
RATE_MAX_PER_AGENT = 12

# Avoid bare words like "secret"/"token" (they appear in safety metadata e.g. no_secrets).
SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key\s*[:=]\s*\S+|password\s*[:=]\s*\S+|bearer\s+[a-z0-9._\-]{16,})"),
    re.compile(r"(?i)(secret\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,})"),
    re.compile(r"(?i)(xai-|sk-|sk-or-|ghp_|github_pat_|hf_)[A-Za-z0-9_\-]{16,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"clh_[A-Za-z0-9_]{20,}"),
    re.compile(r"-----BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY-----"),
    re.compile(r"(?i)(aws_secret_access_key|private_key\s*[:=]|discord_bot\s*[:=]|hf_token\s*[:=])"),
]

ALLOWED_STATUS = {"ALIGNED", "NEEDS_FIX", "UNKNOWN", "QUARANTINE"}
ALLOWED_ROLES = {
    "steward",
    "operator",
    "champion",
    "army",
    "openclaw",
    "lyra",
    "builder",
    "observer",
    "mesh_node",
    "agent",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def card_digest(card: dict) -> str:
    body = {k: v for k, v in card.items() if k not in ("digest", "received_utc", "source_peer")}
    blob = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def contains_secrets(obj: Any) -> bool:
    try:
        text = json.dumps(obj, default=str)
    except Exception:
        text = str(obj)
    if len(text) > MAX_CARD_BYTES * 2:
        return True
    return any(p.search(text) for p in SECRET_PATTERNS)


def validate_card(card: dict, *, require_aligned: bool = False) -> list[str]:
    errs: list[str] = []
    if not isinstance(card, dict):
        return ["not_object"]
    raw = json.dumps(card, default=str).encode("utf-8")
    if len(raw) > MAX_CARD_BYTES:
        errs.append("card_too_large")
    if card.get("signature") not in (CARD_SIG, SIG):
        errs.append("bad_signature")
    agent_id = str(card.get("agent_id") or "").strip()
    if not agent_id or len(agent_id) > 128:
        errs.append("bad_agent_id")
    if not re.match(r"^[A-Za-z0-9_.:@-]{3,128}$", agent_id or "x"):
        errs.append("agent_id_charset")
    role = str(card.get("role") or "agent")
    if role not in ALLOWED_ROLES:
        errs.append("bad_role")
    status = str(card.get("alignment_status") or "UNKNOWN")
    if status not in ALLOWED_STATUS:
        errs.append("bad_status")
    if require_aligned and status != "ALIGNED":
        errs.append("not_aligned")
    if status == "QUARANTINE":
        errs.append("quarantine_card")
    if contains_secrets(card):
        errs.append("secret_pattern")
    skills = card.get("skills") or []
    if not isinstance(skills, list) or len(skills) > MAX_SKILLS:
        errs.append("skills_overflow")
    caps = card.get("capabilities") or []
    if not isinstance(caps, list) or len(caps) > MAX_CAPS:
        errs.append("capabilities_overflow")
    # no private paths
    for key in ("cwd", "home", "path", "stack_root", "private"):
        if key in card:
            errs.append(f"forbidden_field:{key}")
    roots = card.get("lattice_roots") or {}
    if roots and not isinstance(roots, dict):
        errs.append("bad_roots")
    # TTL
    exp = card.get("expires_unix")
    if exp is not None:
        try:
            if float(exp) < time.time() - 30:
                errs.append("expired")
            if float(exp) > time.time() + MAX_TTL_SEC + 120:
                errs.append("ttl_too_long")
        except (TypeError, ValueError):
            errs.append("bad_expires")
    return errs


def build_agent_card(
    *,
    agent_id: str | None = None,
    role: str = "agent",
    skills: list[str] | None = None,
    capabilities: list[str] | None = None,
    display_name: str = "",
    endpoint: str = "",
    ttl_sec: int = DEFAULT_TTL_SEC,
    require_aligned: bool = True,
) -> dict:
    import sys

    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))

    host = socket.gethostname()
    nid = agent_id or os.environ.get("LYGO_AGENT_ID") or os.environ.get("LYGO_NODE_ID") or f"AGENT_{host}"
    role = role if role in ALLOWED_ROLES else "agent"

    living = {}
    roots = {}
    roots_digest = None
    alignment = "UNKNOWN"
    try:
        from collect_living_mesh_badge import collect_living_badge

        badge = collect_living_badge(quick=True, node_id=nid)
        lm = badge.get("living_mesh") or {}
        roots = lm.get("roots") or {}
        roots_digest = lm.get("roots_digest")
        alignment = lm.get("local_status") or badge.get("status") or "UNKNOWN"
        living = {
            "layer": "D",
            "roots_digest": roots_digest,
            "ab_verdict": lm.get("ab_verdict"),
            "world_verdict": lm.get("world_verdict"),
        }
    except Exception as e:
        living = {"layer": "D", "error": type(e).__name__}

    if require_aligned and alignment == "QUARANTINE":
        # still build card but mark blocked for announce
        pass

    default_skills = skills or [
        "lygo-living-mesh",
        "lygo-external-lattice-anchor",
        "lygo-agent-lattice",
    ]
    default_caps = capabilities or [
        "badge_gossip",
        "agent_presence",
        "directory_sync",
        "local_authority",
    ]

    card = {
        "signature": CARD_SIG,
        "protocol": SIG,
        "layer": "E",
        "agent_id": nid,
        "display_name": (display_name or nid)[:80],
        "role": role,
        "hostname_hash": hashlib.sha256(host.encode()).hexdigest()[:16],
        "alignment_status": alignment if alignment in ALLOWED_STATUS else "UNKNOWN",
        "lattice_roots": {
            "A_classic_merkle": roots.get("A_classic_merkle"),
            "B_sovereign_merkle": roots.get("B_sovereign_merkle"),
            "C_public_manifest_sha256": roots.get("C_public_manifest_sha256"),
            "star_chart_registry_sha256": roots.get("star_chart_registry_sha256"),
            "roots_digest": roots_digest,
        },
        "living_mesh": living,
        "skills": list(default_skills)[:MAX_SKILLS],
        "capabilities": list(default_caps)[:MAX_CAPS],
        "endpoint": (endpoint or os.environ.get("LYGO_AGENT_ENDPOINT") or "")[:256],
        "public_hints": [
            "https://clawhub.ai/deepseekoracle/skills/lygo-agent-lattice",
            "https://clawhub.ai/deepseekoracle/skills/lygo-living-mesh",
            "https://clawhub.ai/deepseekoracle/skills/lygo-external-lattice-anchor",
            "https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/docs/AGENT_LATTICE.md",
        ],
        "protection": {
            "summaries_only": True,
            "no_secrets": True,
            "no_egg_payloads": True,
            "local_is_authority": True,
            "alignment_gated": True,
            "consent_for_join": True,
        },
        "created_utc": utc_now(),
        "expires_unix": int(time.time()) + max(60, min(int(ttl_sec), MAX_TTL_SEC)),
        "ttl_sec": max(60, min(int(ttl_sec), MAX_TTL_SEC)),
    }
    card["digest"] = card_digest(card)
    return card


class AgentDirectory:
    def __init__(self, path: Path = DIR_FILE) -> None:
        self.path = path
        self.data = _load(path) or {
            "signature": SIG,
            "agents": {},
            "updated_utc": utc_now(),
        }
        if "agents" not in self.data:
            self.data["agents"] = {}

    def save(self) -> None:
        self.data["signature"] = SIG
        self.data["updated_utc"] = utc_now()
        # prune expired
        now = time.time()
        keep = {}
        for aid, entry in (self.data.get("agents") or {}).items():
            card = entry.get("card") or entry
            exp = card.get("expires_unix")
            if exp is not None and float(exp) < now:
                continue
            keep[aid] = entry
        self.data["agents"] = keep
        _save(self.path, self.data)

    def upsert(self, card: dict, *, source: str = "local") -> dict:
        errs = validate_card(card)
        if errs:
            return {"ok": False, "errors": errs}
        aid = card["agent_id"]
        # rate limit
        q = _load(QUAR_FILE)
        rates = q.get("rates") or {}
        window = rates.get(aid) or []
        now = time.time()
        window = [t for t in window if now - t < RATE_WINDOW_SEC]
        if len(window) >= RATE_MAX_PER_AGENT:
            return {"ok": False, "errors": ["rate_limited"]}
        window.append(now)
        rates[aid] = window
        q["rates"] = rates
        # quarantine list
        if aid in (q.get("blocked") or []):
            return {"ok": False, "errors": ["blocked"]}
        _save(QUAR_FILE, q)

        prev = (self.data["agents"].get(aid) or {}).get("card")
        entry = {
            "card": card,
            "source": source,
            "received_utc": utc_now(),
            "digest": card.get("digest") or card_digest(card),
        }
        self.data["agents"][aid] = entry
        self.save()
        return {
            "ok": True,
            "agent_id": aid,
            "digest": entry["digest"],
            "changed": (prev or {}).get("digest") != entry["digest"],
        }

    def list_cards(self) -> list[dict]:
        out = []
        for aid, entry in sorted((self.data.get("agents") or {}).items()):
            c = dict(entry.get("card") or {})
            c["_source"] = entry.get("source")
            c["_received_utc"] = entry.get("received_utc")
            out.append(c)
        return out

    def snapshot(self) -> dict:
        cards = self.list_cards()
        digests = sorted(c.get("digest") or "" for c in cards)
        return {
            "signature": SIG,
            "updated_utc": self.data.get("updated_utc"),
            "agent_count": len(cards),
            "agents": cards,
            "directory_digest": hashlib.sha256(
                json.dumps(digests, separators=(",", ":")).encode()
            ).hexdigest(),
            "protection": {
                "summaries_only": True,
                "local_is_authority": True,
            },
        }


def load_peers() -> list[dict]:
    d = _load(PEERS_FILE)
    return list(d.get("peers") or [])


def save_peer(base_url: str, label: str = "") -> dict:
    d = _load(PEERS_FILE) or {"signature": SIG, "peers": []}
    entry = {
        "base_url": base_url.rstrip("/"),
        "label": label or base_url,
        "joined_utc": utc_now(),
    }
    peers = [p for p in d.get("peers") or [] if p.get("base_url") != entry["base_url"]]
    peers.append(entry)
    d["peers"] = peers
    d["updated_utc"] = utc_now()
    _save(PEERS_FILE, d)
    return entry


def public_bootstrap_peers() -> list[str]:
    """Known public bootstrap hints (read-only; connection still local-operator)."""
    return [
        # operator self — not auto-connected; listed for discovery docs
        "https://deepseekoracle.github.io/lygo-protocol-stack/",
    ]


def http_json(
    method: str,
    url: str,
    body: dict | None = None,
    timeout: int = 12,
    headers: dict | None = None,
) -> tuple[int, Any]:
    import urllib.error
    import urllib.request

    data = None
    hdrs = {"User-Agent": "LYGO-AgentLattice/1.0", **(headers or {})}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as e:
        try:
            body_txt = e.read().decode("utf-8", errors="replace")
            try:
                return e.code, json.loads(body_txt)
            except Exception:
                return e.code, body_txt
        except Exception:
            return e.code, str(e)
    except Exception as e:
        return 0, str(e)
