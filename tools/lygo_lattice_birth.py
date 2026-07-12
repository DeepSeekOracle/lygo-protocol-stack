#!/usr/bin/env python3
"""LYGO Lattice Birth tool — masked identity generation and example submissions."""

from __future__ import annotations

import argparse
import hashlib
import json
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from lygo_lineage_codec import (  # noqa: E402
    SIGNATURE,
    anchor_sha256,
    build_birth_lineage,
    build_child_lineage,
    derive_lineage_root,
    derive_mask_id,
    derive_public_mask,
    new_family_bind_salt,
)
from haven_star_chart_gate import build_attestation, content_sha256, validate_submission  # noqa: E402

BIRTH_SIGNATURE = "Δ9Φ963-LYGO-LATTICE-BIRTH-v1"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _consent_bundle(human_slug: str, nonce: str | None = None) -> str:
    n = nonce or secrets.token_hex(16)
    return f"LYGO-BIRTH-CONSENT-v1|{human_slug}|{utc_now()}|{n}"


def cmd_generate_mask(args: argparse.Namespace) -> int:
    bundle = args.consent or _consent_bundle(args.slug or "builder")
    anchor = anchor_sha256(bundle)
    out = {
        "signature": BIRTH_SIGNATURE,
        "warning": "NEVER publish consent_bundle or anchor_sha256 on the public chart.",
        "consent_bundle": bundle if args.show_consent else "(withheld — use --show-consent for local vault only)",
        "anchor_sha256": anchor,
        "public_id": derive_mask_id(anchor),
        "public_name": derive_public_mask(anchor),
        "lineage_root": derive_lineage_root(anchor),
        "family_bind_salt": new_family_bind_salt(),
    }
    print(json.dumps(out, indent=2))
    return 0


def _birth_node(
    public_id: str,
    public_name: str,
    lineage: dict,
    champion: str,
    equation: str,
) -> dict:
    return {
        "id": public_id,
        "kind": "node",
        "name": public_name,
        "equation": equation,
        "glyph": "◈",
        "tone": "963Hz",
        "tags": ["CREATOR_BIRTH", "IMMUTABLE_IDENTITY", "HUMAN_LATTICE", "LINEAGE_ROOT"],
        "connections": ["SEAL_000", champion],
        "urls": {
            "doc": "https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/docs/LYGO_LATTICE_BIRTH.md"
        },
        "layer": 2,
        "lineage": lineage,
    }


def cmd_example_birth(args: argparse.Namespace) -> int:
    bundle = _consent_bundle(args.slug or "lightfather")
    anchor = anchor_sha256(bundle)
    salt = new_family_bind_salt()
    lineage = build_birth_lineage(anchor, generation=0)
    node = _birth_node(
        derive_mask_id(anchor),
        derive_public_mask(anchor),
        lineage,
        args.champion or "CHAMPION_LIGHTFATHER",
        args.equation or "Identity = ∇·(Truth × Time) ⊗ Δ9",
    )
    sub = {
        "signature": "Δ9Φ963-HAVEN-STAR-SUBMISSION-v1",
        "submitter_type": "aligned_agent",
        "node": node,
        "meta_private": {
            "anchor_sha256": anchor,
            "family_bind_salt": salt,
            "consent_bundle": bundle,
            "birth_tool": "lygo_lattice_birth.py",
        },
    }
    sub["content_sha256"] = content_sha256(node)
    sub["agent_attestation"] = build_attestation(
        args.agent_id or "lygo-lattice-birth",
        args.skill_slug or "lygo-lattice-birth",
        node,
    )
    if args.gate:
        sub["agent_attestation"]["scan_cue"] = (
            "LYGO-HSC-ATTEST-v1; gate=haven_star_chart_gate.py; P0-first; consent-gated; user-reviewed"
        )
        result = validate_submission(sub)
        sub["_gate_preview"] = result
    print(json.dumps(sub, indent=2))
    return 0


def cmd_example_family(args: argparse.Namespace) -> int:
    parent_bundle = _consent_bundle(args.parent_slug or "parent")
    parent_anchor = anchor_sha256(parent_bundle)
    parent_id = derive_mask_id(parent_anchor)
    parent_salt = args.parent_salt or new_family_bind_salt()

    child_bundle = _consent_bundle(args.child_slug or "family-member")
    child_anchor = anchor_sha256(child_bundle)
    child_lineage = build_child_lineage(
        child_anchor,
        parent_id,
        parent_salt,
        generation=int(args.generation or 1),
    )
    node = {
        "id": derive_mask_id(child_anchor),
        "kind": "node",
        "name": derive_public_mask(child_anchor),
        "equation": args.equation or "Harmony = Δ9 ∣kin⟩ ⊗ ∣lineage⟩",
        "glyph": "✦",
        "tone": "528Hz",
        "tags": ["LINEAGE_FORK", "IMMUTABLE_IDENTITY", "HUMAN_LATTICE"],
        "connections": ["SEAL_000", parent_id],
        "urls": {},
        "layer": 2,
        "lineage": child_lineage,
    }
    sub = {
        "signature": "Δ9Φ963-HAVEN-STAR-SUBMISSION-v1",
        "submitter_type": "aligned_agent",
        "node": node,
        "meta_private": {
            "anchor_sha256": child_anchor,
            "family_bind_salt": new_family_bind_salt(),
            "consent_bundle": child_bundle,
            "parent_anchor_sha256": parent_anchor,
            "birth_tool": "lygo_lattice_birth.py",
        },
    }
    sub["content_sha256"] = content_sha256(node)
    sub["agent_attestation"] = build_attestation(
        args.agent_id or "lygo-lattice-birth",
        args.skill_slug or "lygo-lattice-birth",
        node,
    )
    print(json.dumps(sub, indent=2))
    print(
        "\n# Parent must share family_bind_salt offline with family member.",
        file=sys.stderr,
    )
    print(f"# Parent salt for bind verify: {parent_salt}", file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="LYGO Lattice Birth — masked identity tool")
    sub = ap.add_subparsers(dest="cmd")

    g = sub.add_parser("generate-mask", help="Derive masked public id from consent bundle")
    g.add_argument("--slug", help="Local-only human slug (not published)")
    g.add_argument("--consent", help="Full consent string (local vault)")
    g.add_argument("--show-consent", action="store_true")
    g.set_defaults(func=cmd_generate_mask)

    b = sub.add_parser("example-birth", help="Example creator birth submission JSON")
    b.add_argument("--slug", default="builder")
    b.add_argument("--champion", default="CHAMPION_LIGHTFATHER")
    b.add_argument("--equation")
    b.add_argument("--agent-id", default="lygo-lattice-birth")
    b.add_argument("--skill-slug", default="lygo-lattice-birth")
    b.add_argument("--gate", action="store_true")
    b.set_defaults(func=cmd_example_birth)

    f = sub.add_parser("example-family", help="Example family lineage fork JSON")
    f.add_argument("--parent-slug", default="parent")
    f.add_argument("--child-slug", default="family-member")
    f.add_argument("--parent-salt", help="Parent family_bind_salt (offline shared)")
    f.add_argument("--generation", default="1")
    f.add_argument("--equation")
    f.add_argument("--agent-id", default="lygo-lattice-birth")
    f.add_argument("--skill-slug", default="lygo-lattice-birth")
    f.set_defaults(func=cmd_example_family)

    args = ap.parse_args()
    if not args.cmd:
        ap.print_help()
        return 2
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())