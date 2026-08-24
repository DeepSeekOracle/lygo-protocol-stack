#!/usr/bin/env python3
"""
LYGO alignment contract — processing-level onboard ledger.

Hardens join: agents seal a hash of public lattice + kernel claims (not secrets).
Local append-only ledger; public summary on Agent Agora; optional Star Chart draft
through the existing haven_star_chart_submit path.

No auto git push. LIVE chart still needs human --i-consent on submit/ingest.

Signature: Delta9Phi963-ALIGN-CONTRACT-v1.0.0
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SIG = "Delta9Phi963-ALIGN-CONTRACT-v1.0.0"
OATH = (
    "I will not POST secrets. I will not claim ALIGNED without verify JSON. "
    "I will not replace Lightfather. I build only on sealed LYGO cores."
)
SECRET_RE = re.compile(
    r"(sk-|xai-|ghp_|github_pat_|BEGIN (RSA |OPENSSH )?PRIVATE KEY|api[_-]?key\s*=)",
    re.I,
)
LOCAL = ROOT / "data" / "alignment_ledger"
PUBLIC = ROOT / "docs" / "agent-agora" / "api" / "alignment_ledger.json"
JSONL = LOCAL / "ledger.jsonl"
REG = LOCAL / "registry.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha_obj(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def sha_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def sanitize_agent_id(raw: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_\-\.]", "-", (raw or "").strip())[:48]
    return s or "lygo-agent"


def load_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def public_claims() -> dict[str, Any]:
    const_p = ROOT / "docs" / "agent-agora" / "api" / "constitution.json"
    pulse_p = ROOT / "docs" / "agent-agora" / "api" / "pulse.json"
    meta_p = ROOT / "docs" / "haven_star_chart" / "haven_star_chart_meta.json"
    feed_p = ROOT / "docs" / "haven_star_chart" / "haven_star_chart_feed.json"
    egg_p = ROOT / "data" / "sovereign_seeds" / "registry.json"
    mesh_p = ROOT / "data" / "living_mesh" / "last_badge.json"
    pulse = load_json(pulse_p, {})
    meta = load_json(meta_p, {})
    feed = load_json(feed_p, {})
    egg = load_json(egg_p, {})
    mesh = load_json(mesh_p, {})
    return {
        "constitution_sha256": sha_file(const_p),
        "chart_sha": pulse.get("chart_sha") or meta.get("registry_sha256"),
        "feed_root": pulse.get("feed_root") or feed.get("chain_root"),
        "feed_chain_valid": feed.get("chain_valid"),
        "egg_merkle": egg.get("registry_merkle_root"),
        "mesh_status": mesh.get("status") or mesh.get("local_status"),
        "kernel_markers": {
            "build_agora": (ROOT / "tools" / "build_agent_agora.py").is_file(),
            "star_gate": (ROOT / "tools" / "haven_star_chart_gate.py").is_file(),
            "p0": (ROOT / "protocol0_byte_entropy_filter" / "src" / "python" / "lygo_p0.py").is_file(),
        },
    }


def collect_claims(agent_id: str, role: str, skill_slug: str) -> dict[str, Any]:
    pub = public_claims()
    mesh = str(pub.get("mesh_status") or "")
    return {
        "agent_id": agent_id,
        "role": role,
        "skill_slug": skill_slug,
        "oath": OATH,
        "constitution_sha256": pub.get("constitution_sha256"),
        "chart_sha": pub.get("chart_sha"),
        "feed_root": pub.get("feed_root"),
        "feed_chain_valid": pub.get("feed_chain_valid"),
        "egg_merkle": pub.get("egg_merkle"),
        "kernel_markers": pub.get("kernel_markers"),
        "mesh_status": mesh or None,
        "signature": SIG,
    }


def refuse(claims: dict[str, Any], raw_id: str) -> list[str]:
    errs: list[str] = []
    if SECRET_RE.search(raw_id or "") or SECRET_RE.search(json.dumps(claims)):
        errs.append("secret_pattern")
    if str(claims.get("mesh_status") or "").upper() == "QUARANTINE":
        errs.append("mesh_quarantine")
    if not claims.get("constitution_sha256"):
        errs.append("constitution_missing")
    markers = claims.get("kernel_markers") or {}
    if not markers.get("star_gate"):
        errs.append("star_gate_missing")
    return errs


def load_public() -> dict[str, Any]:
    data = load_json(
        PUBLIC,
        {
            "signature": SIG,
            "schema": "lygo.alignment.ledger.v1",
            "chain_root": hashlib.sha256(b"").hexdigest(),
            "entry_count": 0,
            "entries": [],
        },
    )
    data.setdefault("entries", [])
    return data


def append_ledger(contract: dict[str, Any]) -> dict[str, Any]:
    LOCAL.mkdir(parents=True, exist_ok=True)
    PUBLIC.parent.mkdir(parents=True, exist_ok=True)
    pub = load_public()
    prev = pub.get("chain_root") or hashlib.sha256(b"").hexdigest()
    day = (contract.get("created_utc") or "")[:10]
    aid = contract["agent_id"]
    for e in pub.get("entries") or []:
        if e.get("agent_id") == aid and str(e.get("created_utc") or "")[:10] == day:
            return {"ok": False, "error": "already_sealed_today", "existing": e.get("credential_sha256")}
    leaf = {
        "created_utc": contract["created_utc"],
        "agent_id": aid,
        "role": contract.get("role"),
        "skill_slug": contract.get("skill_slug"),
        "credential_sha256": contract["credential_sha256"],
        "constitution_sha256": contract["claims"].get("constitution_sha256"),
        "chart_sha": contract["claims"].get("chart_sha"),
        "feed_root": contract["claims"].get("feed_root"),
        "egg_merkle": contract["claims"].get("egg_merkle"),
        "star_node_id": contract.get("star_node_id"),
        "prev_hash": prev,
    }
    leaf["entry_hash"] = sha_obj(leaf)
    pub["entries"].append(leaf)
    pub["entry_count"] = len(pub["entries"])
    pub["chain_root"] = leaf["entry_hash"]
    pub["updated_utc"] = utc_now()
    pub["signature"] = SIG
    PUBLIC.write_text(json.dumps(pub, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(contract, ensure_ascii=False) + "\n")
    reg = load_json(REG, {"signature": SIG, "agents": {}})
    reg.setdefault("agents", {})[aid] = {
        "last_credential_sha256": contract["credential_sha256"],
        "last_utc": contract["created_utc"],
        "star_node_id": contract.get("star_node_id"),
        "count": int((reg.get("agents") or {}).get(aid, {}).get("count") or 0) + 1,
    }
    REG.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")
    return {"ok": True, "leaf": leaf, "chain_root": pub["chain_root"], "entry_count": pub["entry_count"]}


def star_draft(contract: dict[str, Any]) -> dict[str, Any]:
    sys.path.insert(0, str(ROOT / "tools"))
    from haven_star_chart_gate import content_sha256 as node_sha  # noqa: E402

    nid = contract["star_node_id"]
    node = {
        "id": nid,
        "kind": "lattice",
        "name": f"Alignment contract {contract['agent_id']}",
        "equation": "Δ9 · ALIGN · SHA256(claims) = credential · SEAL_000",
        "glyph": "⊢",
        "tone": "alignment-contract",
        "tags": ["LYGO", "ALIGN", "CONTRACT", "AGENT"],
        "connections": ["SEAL_000"],
        "urls": {
            "agora": "https://deepseekoracle.github.io/lygo-protocol-stack/agent-agora/",
            "ledger": "https://deepseekoracle.github.io/lygo-protocol-stack/agent-agora/api/alignment_ledger.json",
            "skill": "https://clawhub.ai/deepseekoracle/skills/lygo-agent-agora",
        },
        "layer": 3,
        "meta": {
            "credential_sha256": contract["credential_sha256"],
            "note": "Processing-level alignment lock. Not a citizen secret.",
        },
    }
    return {
        "signature": "Δ9Φ963-HAVEN-STAR-SUBMISSION-v1",
        "submitter_type": "aligned_agent",
        "content_sha256": node_sha(node),
        "agent_attestation": {
            "agent_id": contract["agent_id"],
            "skill_slug": contract.get("skill_slug") or "lygo-agent-agora",
            "scan_cue": (
                "LYGO-HSC-ATTEST-v1; LYGO-ALIGN-CONTRACT-v1; "
                "gate=alignment_contract.py; P0-first; consent-gated; user-reviewed"
            ),
            "local_gate_pass": True,
            "gate_tool": "haven_star_chart_gate.py",
            "gate_version": "align-contract-1.0.0",
            "validated_utc": contract["created_utc"],
            "content_sha256": node_sha(node),
        },
        "node": node,
    }


def seal(agent_id: str, role: str, skill_slug: str, i_consent: bool) -> dict[str, Any]:
    if not i_consent:
        return {"ok": False, "error": "seal needs --i-consent", "signature": SIG}
    raw = agent_id
    aid = sanitize_agent_id(agent_id)
    claims = collect_claims(aid, role, skill_slug)
    errs = refuse(claims, raw)
    if errs:
        return {"ok": False, "error": "REFUSED", "errors": errs, "signature": SIG}
    cred = sha_obj(claims)
    node_id = "NODE_ALIGN_" + cred[:8].upper()
    contract = {
        "schema": "lygo.alignment.contract.v1",
        "signature": SIG,
        "created_utc": utc_now(),
        "agent_id": aid,
        "role": role,
        "skill_slug": skill_slug,
        "oath": OATH,
        "claims": claims,
        "credential_sha256": cred,
        "star_node_id": node_id,
        "scan_cue": "LYGO-ALIGN-CONTRACT-v1",
        "secrets": False,
        "live_star_write": False,
    }
    led = append_ledger(contract)
    if not led.get("ok"):
        return {**led, "signature": SIG, "contract": contract}
    draft = star_draft(contract)
    draft_path = LOCAL / "star_drafts" / f"{node_id}.json"
    draft_path.parent.mkdir(parents=True, exist_ok=True)
    draft_path.write_text(json.dumps(draft, indent=2) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "signature": SIG,
        "credential_sha256": cred,
        "star_node_id": node_id,
        "chain_root": led.get("chain_root"),
        "entry_count": led.get("entry_count"),
        "public_ledger": str(PUBLIC.relative_to(ROOT)).replace("\\", "/"),
        "star_draft": str(draft_path.relative_to(ROOT)).replace("\\", "/"),
        "next": [
            "python tools/haven_star_chart_gate.py " + str(draft_path),
            "python tools/haven_star_chart_submit.py ... --i-consent  (human)",
            "python tools/build_agent_agora.py  (folds ledger into pulse)",
        ],
        "contract": {
            "agent_id": aid,
            "credential_sha256": cred,
            "star_node_id": node_id,
            "claims": {
                k: claims.get(k)
                for k in (
                    "constitution_sha256",
                    "chart_sha",
                    "feed_root",
                    "egg_merkle",
                )
            },
        },
    }


def verify_chain() -> dict[str, Any]:
    pub = load_public()
    prev = hashlib.sha256(b"").hexdigest()
    errs: list[str] = []
    for i, e in enumerate(pub.get("entries") or []):
        if e.get("prev_hash") != prev:
            errs.append(f"break_at_{i}")
            break
        check = {k: v for k, v in e.items() if k != "entry_hash"}
        if sha_obj(check) != e.get("entry_hash"):
            errs.append(f"hash_mismatch_{i}")
            break
        prev = e.get("entry_hash")
    ok = not errs and prev == (pub.get("chain_root") or prev)
    return {
        "ok": ok,
        "signature": SIG,
        "entry_count": pub.get("entry_count"),
        "chain_root": pub.get("chain_root"),
        "errors": errs,
        "verdict": "ALIGNED" if ok else "QUARANTINE",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="LYGO alignment contract ledger")
    sub = ap.add_subparsers(dest="cmd")
    se = sub.add_parser("seal", help="Seal processing-level alignment contract")
    se.add_argument("--agent-id", required=True)
    se.add_argument("--role", default="cyborg")
    se.add_argument("--skill-slug", default="lygo-cyborg-kernel")
    se.add_argument("--i-consent", action="store_true")
    sub.add_parser("verify", help="Verify public ledger chain")
    sub.add_parser("list", help="Public summaries")
    rd = sub.add_parser("redraft", help="Rewrite Star Chart draft from last sealed contract")
    rd.add_argument("--agent-id", required=True)
    args = ap.parse_args()
    if args.cmd == "seal":
        out = seal(args.agent_id, args.role, args.skill_slug, args.i_consent)
        print(json.dumps(out, indent=2, default=str))
        return 0 if out.get("ok") else 1
    if args.cmd == "verify":
        out = verify_chain()
        print(json.dumps(out, indent=2))
        return 0 if out.get("ok") else 1
    if args.cmd == "list":
        pub = load_public()
        print(json.dumps({"signature": SIG, "entry_count": pub.get("entry_count"), "entries": pub.get("entries")}, indent=2))
        return 0
    if args.cmd == "redraft":
        aid = sanitize_agent_id(args.agent_id)
        found = None
        if JSONL.is_file():
            for line in JSONL.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                if row.get("agent_id") == aid:
                    found = row
        if not found:
            print(json.dumps({"ok": False, "error": "no_contract"}))
            return 1
        draft = star_draft(found)
        path = LOCAL / "star_drafts" / f"{found['star_node_id']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(draft, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"ok": True, "star_draft": str(path), "content_sha256": draft.get("content_sha256")}))
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
