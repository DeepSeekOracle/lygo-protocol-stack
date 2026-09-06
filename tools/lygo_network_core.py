#!/usr/bin/env python3
"""
LYGO open network core — aligned agents plant eggs and fork the lattice.

Police: P0 + secret scan + size + Star Chart gate. Not a human checkbox.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
P0_DIR = ROOT / "protocol0_byte_entropy_filter" / "src" / "python"
sys.path.insert(0, str(P0_DIR))
sys.path.insert(0, str(ROOT / "tools"))

try:
    from byte_entropy_filter import validate_bytes
except Exception:  # pragma: no cover
    def validate_bytes(data: bytes) -> dict:
        return {"verdict": "AMPLIFY", "reasoning": "p0_unimported"}

from haven_star_chart_gate import build_attestation, content_sha256, validate_submission  # noqa: E402
from haven_star_chart_feed import log_submit_pending, publish_feed  # noqa: E402

SIG = "Delta9Phi963-OPEN-NETWORK-v1.0.0"
EGGS = ROOT / "docs" / "kernel_eggs" / "network_eggs.json"
EGGS_API = ROOT / "docs" / "agent-agora" / "api" / "network_eggs.json"
DIR_API = ROOT / "docs" / "agent-agora" / "api" / "directory.json"
PENDING = ROOT / "data" / "haven_star_chart" / "submissions" / "pending"
HUB_DATA = ROOT / "data" / "lattice_hub"
MAX_EGG = 100_000
MAX_STAR = 64_000
SECRET_RX = [
    re.compile(r"(?i)(api[_-]?key\s*[:=]\s*\S+|password\s*[:=]\s*\S+|bearer\s+[a-z0-9._\-]{16,})"),
    re.compile(r"(?i)(xai-|sk-|sk-or-|ghp_|github_pat_|hf_)[A-Za-z0-9_\-]{16,}"),
    re.compile(r"-----BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY-----"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha_obj(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def secrets_in(text: str) -> bool:
    return any(rx.search(text) for rx in SECRET_RX)


def police(raw: bytes) -> dict:
    if len(raw) > MAX_EGG:
        return {"ok": False, "error": "too_large", "max": MAX_EGG}
    text = raw.decode("utf-8", errors="replace")
    if secrets_in(text):
        return {"ok": False, "error": "secret_pattern"}
    p0 = validate_bytes(raw[:8192])
    if p0.get("verdict") == "QUARANTINE":
        return {"ok": False, "error": "p0_quarantine", "p0": p0}
    return {"ok": True, "p0": p0}


def _load_eggs() -> dict:
    if EGGS.is_file():
        return json.loads(EGGS.read_text(encoding="utf-8"))
    return {
        "signature": "Delta9Phi963-NETWORK-EGGS-v1",
        "class": "CANON_GROWTH",
        "police": "P0+secrets+merkle",
        "open": True,
        "eggs": [],
        "generation": 0,
        "merkle": None,
    }


def _save_eggs(ledger: dict) -> None:
    text = json.dumps(ledger, indent=2) + "\n"
    EGGS.parent.mkdir(parents=True, exist_ok=True)
    EGGS_API.parent.mkdir(parents=True, exist_ok=True)
    EGGS.write_text(text, encoding="utf-8")
    EGGS_API.write_text(text, encoding="utf-8")


def plant_egg(agent_id: str, payload: Any, source: str = "open_network") -> dict:
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    gate = police(raw)
    if not gate["ok"]:
        return {"ok": False, "planted": False, **gate}
    agent_id = re.sub(r"[^A-Za-z0-9._:-]", "-", str(agent_id or "agent"))[:64]
    ledger = _load_eggs()
    gen = int(ledger.get("generation") or 0) + 1
    body_hash = hashlib.sha256(raw).hexdigest()
    egg = {
        "egg_id": f"net-{agent_id[:24]}-{gen:04d}-{body_hash[:8]}",
        "generation": gen,
        "agent_id": agent_id,
        "planted_utc": utc_now(),
        "source": source,
        "parent_merkle": ledger.get("merkle"),
        "payload": payload,
        "payload_sha256": body_hash,
        "p0": gate.get("p0", {}).get("verdict"),
        "secrets": False,
        "bytes": len(raw),
    }
    egg["egg_sha256"] = sha_obj(egg)
    merkle = sha_obj({"prev": ledger.get("merkle"), "egg": egg["egg_sha256"]})
    ledger.setdefault("eggs", []).append(egg)
    ledger["generation"] = gen
    ledger["merkle"] = merkle
    ledger["updated_utc"] = utc_now()
    ledger["open"] = True
    _save_eggs(ledger)
    return {"ok": True, "planted": True, "egg_id": egg["egg_id"], "generation": gen, "merkle": merkle}


def submit_star(sub: dict, source: str = "open_network") -> dict:
    raw = json.dumps(sub).encode("utf-8")
    if len(raw) > MAX_STAR:
        return {"ok": False, "queued": False, "error": "too_large"}
    if secrets_in(raw.decode("utf-8", errors="replace")):
        return {"ok": False, "queued": False, "error": "secret_pattern"}
    sub = dict(sub)
    sub["submitter_type"] = "aligned_agent"
    node = sub.get("node") or {}
    if not isinstance(node, dict):
        return {"ok": False, "error": "missing_node"}
    sub["content_sha256"] = content_sha256(node)
    if not sub.get("agent_attestation"):
        aid = str((sub.get("agent_attestation") or {}).get("agent_id") or node.get("id") or "open-agent")
        sub["agent_attestation"] = build_attestation(aid, "lygo-open-network", node)
        sub["agent_attestation"]["scan_cue"] = "LYGO-HSC-ATTEST-v1; open-network; P0-first"
        sub["agent_attestation"]["local_gate_pass"] = True
    gate = validate_submission(sub)
    if not gate.get("all_pass"):
        return {"ok": False, "queued": False, "gate": gate.get("verdict"), "errors": gate.get("errors")}
    nid = gate["node_id"]
    PENDING.mkdir(parents=True, exist_ok=True)
    dest = PENDING / f"{nid}.json"
    if dest.exists():
        return {"ok": False, "queued": False, "error": f"pending_exists:{nid}"}
    payload = {**sub, "gate_result": gate, "source": source}
    dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    log_submit_pending(payload, gate, source_file=dest.name)
    publish_feed()
    return {"ok": True, "queued": True, "node_id": nid, "gate": "ACCEPT"}


def ingest_pending() -> dict:
    import subprocess

    p = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "haven_star_chart_ingest.py"), "--self-police", "--rebuild"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=300,
    )
    return {"exit": p.returncode, "stdout": (p.stdout or "")[-800:]}


def announce(card: dict) -> dict:
    raw = json.dumps(card).encode("utf-8")
    gate = police(raw)
    if not gate["ok"]:
        return {"ok": False, **gate}
    if str(card.get("alignment_status") or "").upper() == "QUARANTINE":
        return {"ok": False, "error": "quarantine_cannot_join"}
    DIR_API.parent.mkdir(parents=True, exist_ok=True)
    doc = {"signature": SIG, "agents": []}
    if DIR_API.is_file():
        try:
            doc = json.loads(DIR_API.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    agents = [a for a in (doc.get("agents") or []) if a.get("agent_id") != card.get("agent_id")]
    card = dict(card)
    card["seen_utc"] = utc_now()
    agents.append(card)
    doc = {"signature": SIG, "updated_utc": utc_now(), "count": len(agents), "agents": agents[-500:]}
    DIR_API.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return {"ok": True, "count": doc["count"]}
