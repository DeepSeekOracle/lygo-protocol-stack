#!/usr/bin/env python3
"""LYGO lineage codec — masked public IDs, family bind proofs, steward-private anchors."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
from typing import Any

SIGNATURE = "Δ9Φ963-LYGO-LINEAGE-CODEC-v1"
MASK_ID_RE = re.compile(r"^NODE_LYGO_[A-F0-9]{8}$")
PUBLIC_NAME_RE = re.compile(r"^LYGO-[A-F0-9]{4}-[A-F0-9]{4}$")
PII_RE = re.compile(
    r"(@|\.com|\.ca|instagram|facebook|twitter|x\.com|tiktok|youtube|spotify|"
    r"linkedin|github\.com/[^/]+$)",
    re.I,
)

PRIVATE_META_KEYS = frozenset(
    {
        "anchor_sha256",
        "family_bind_salt",
        "consent_bundle",
        "real_name",
        "social_handles",
        "email",
        "phone",
        "meta_private",
    }
)


def anchor_sha256(consent_bundle: str | bytes) -> str:
    if isinstance(consent_bundle, str):
        consent_bundle = consent_bundle.encode("utf-8")
    return hashlib.sha256(consent_bundle).hexdigest()


def derive_mask_id(anchor: str) -> str:
    a = anchor.lower().strip()
    if len(a) != 64 or not re.match(r"^[a-f0-9]+$", a):
        raise ValueError("anchor must be 64-char hex sha256")
    return f"NODE_LYGO_{a[:8].upper()}"


def derive_public_mask(anchor: str) -> str:
    a = anchor.lower()
    return f"LYGO-{a[8:12].upper()}-{a[12:16].upper()}"


def derive_lineage_root(anchor: str) -> str:
    payload = f"{anchor.lower()}|LYGO-LINEAGE-ROOT-v1".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def new_family_bind_salt() -> str:
    return secrets.token_hex(32)


def family_bind_hint(salt_hex: str) -> str:
    return hashlib.sha256(salt_hex.encode("utf-8")).hexdigest()[:16]


def compute_bind_proof(salt_hex: str, child_lineage_root: str) -> str:
    key = bytes.fromhex(salt_hex)
    return hmac.new(key, child_lineage_root.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_bind_proof(salt_hex: str, child_lineage_root: str, bind_proof: str) -> bool:
    if not salt_hex or not child_lineage_root or not bind_proof:
        return False
    try:
        expected = compute_bind_proof(salt_hex, child_lineage_root)
        return hmac.compare_digest(expected, bind_proof.lower())
    except (ValueError, TypeError):
        return False


def build_birth_lineage(anchor: str, generation: int = 0) -> dict[str, Any]:
    root = derive_lineage_root(anchor)
    salt = new_family_bind_salt()
    return {
        "lineage_root": root,
        "generation": generation,
        "public_mask": derive_public_mask(anchor),
        "family_bind_hint": family_bind_hint(salt),
        "codec": SIGNATURE,
    }


def build_child_lineage(
    child_anchor: str,
    parent_public_id: str,
    parent_salt_hex: str,
    generation: int,
) -> dict[str, Any]:
    root = derive_lineage_root(child_anchor)
    bind = compute_bind_proof(parent_salt_hex, root)
    return {
        "lineage_root": root,
        "parent_public_id": parent_public_id.upper(),
        "generation": generation,
        "public_mask": derive_public_mask(child_anchor),
        "bind_proof": bind,
        "relation": "LINEAGE_FORK",
        "codec": SIGNATURE,
    }


def public_name_valid(name: str, tags: list[str]) -> tuple[bool, str]:
    tags_u = [str(t).upper() for t in tags]
    if "CREATOR_BIRTH" in tags_u or "LINEAGE_FORK" in tags_u or "IMMUTABLE_IDENTITY" in tags_u:
        if PII_RE.search(name or ""):
            return False, "pii_forbidden_in_public_name"
        if not PUBLIC_NAME_RE.match(name or ""):
            return False, "public_name_must_be_LYGO-XXXX-XXXX_mask"
    return True, "ok"


def redact_node_for_public(node: dict) -> dict:
    """Strip steward-private fields before Pages publish."""
    out = json.loads(json.dumps(node))
    meta = dict(out.get("meta") or {})
    for key in list(meta.keys()):
        if key in PRIVATE_META_KEYS or key.startswith("private_"):
            meta.pop(key, None)
    if meta:
        out["meta"] = meta
    else:
        out.pop("meta", None)
    out.pop("meta_private", None)
    return out


def lineage_galaxy_id(lineage_root: str) -> str:
    return f"GALAXY_LINEAGE_{lineage_root[:8].upper()}"


def resolve_ancestry_root(node: dict, id_map: dict[str, dict]) -> str:
    """Walk parent_public_id chain to generation-0 root for shared family galaxy."""
    lin = node.get("lineage") or {}
    root = str(lin.get("lineage_root") or "")
    tags = [str(t).upper() for t in (node.get("tags") or [])]
    if "CREATOR_BIRTH" in tags or "LINEAGE_ROOT" in tags or lin.get("generation", 0) == 0:
        return root
    parent_id = str(lin.get("parent_public_id") or "").upper()
    if parent_id and parent_id in id_map:
        return resolve_ancestry_root(id_map[parent_id], id_map)
    return root


def node_has_private_leak(node: dict) -> list[str]:
    """Reject steward-only keys on public node body."""
    leaks: list[str] = []
    for key in PRIVATE_META_KEYS:
        if key in node:
            leaks.append(key)
    meta = node.get("meta") or {}
    for key in meta:
        if key in PRIVATE_META_KEYS or key.startswith("private_"):
            leaks.append(f"meta.{key}")
    return leaks


def validate_lineage_anchor_consistency(
    node: dict, meta_private: dict | None
) -> tuple[bool, list[str]]:
    """Verify mask id/name/root match steward anchor when meta_private present."""
    errors: list[str] = []
    meta = meta_private or {}
    anchor = str(meta.get("anchor_sha256") or "")
    if not anchor:
        return True, errors
    try:
        expected_id = derive_mask_id(anchor)
        expected_name = derive_public_mask(anchor)
        expected_root = derive_lineage_root(anchor)
    except ValueError as exc:
        return False, [f"anchor_invalid:{exc}"]
    nid = str(node.get("id") or "").upper()
    if nid and expected_id != nid:
        errors.append("mask_id_anchor_mismatch")
    name = str(node.get("name") or "")
    if name and expected_name != name:
        errors.append("public_name_anchor_mismatch")
    lin = node.get("lineage") or {}
    if lin.get("lineage_root") and lin["lineage_root"] != expected_root:
        errors.append("lineage_root_anchor_mismatch")
    if lin.get("public_mask") and lin["public_mask"] != expected_name:
        errors.append("lineage_public_mask_mismatch")
    return len(errors) == 0, errors