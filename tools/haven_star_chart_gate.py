#!/usr/bin/env python3
"""Haven Star Chart submission gate — P0 + math resonance + graph + agent attestation."""

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

from byte_entropy_filter import validate_bytes  # noqa: E402

GATE_VERSION = "1.0.0"
SIGNATURE = "Δ9Φ963-HAVEN-STAR-CHART-GATE-v1"
# Technical attestation markers (any one required) — not ideological phrasing
SCAN_CUE_MARKERS = (
    "LYGO-HSC-ATTEST-v1",
    "HAVEN-STAR-CHART-GATE",
    "Aligned to LYGO",  # legacy compatible
)
SCAN_CUE_REQUIRED = SCAN_CUE_MARKERS[0]

VALID_KINDS = {"seal", "champion", "lattice", "portal", "champion_egg", "joy_loop_egg", "node"}
ID_RE = re.compile(
    r"^(SEAL_\d{3,}|GAB_SEAL_\d{3}|CHAMPION_[A-Z0-9_]+|LATTICE_[A-Z0-9_]+|PORTAL_[A-Z0-9_]+|CHAMPION_EGG_[A-Z0-9_]+|JOY_[A-Z0-9_]+|NODE_[A-Z0-9_]+)$"
)
MATH_MARKERS = re.compile(
    r"(=|×|·|∇|⊗|∣|\||\+|−|-|φ|Φ|Δ|Ω|∞|√|∑|Hz|hz|963|528|432|1111|1440|741|8787|BPM|bpm|∅|⟩|⟨)"
)
HARMONIC_NUMBERS = {963, 528, 432, 1111, 1440, 741, 8787, 122, 0}
FORBIDDEN_SUBMITTER = {"human_direct", "human", "browser_form", "anonymous"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_node_body(node: dict) -> bytes:
    """Stable serialization for content hash (excludes attestation)."""
    core = {
        "id": node.get("id"),
        "kind": node.get("kind"),
        "name": node.get("name"),
        "equation": node.get("equation"),
        "glyph": node.get("glyph"),
        "tone": node.get("tone"),
        "tags": sorted([str(t).upper() for t in (node.get("tags") or [])]),
        "connections": sorted([str(c) for c in (node.get("connections") or [])]),
        "urls": node.get("urls") or {},
        "layer": node.get("layer"),
    }
    return json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8")


def content_sha256(node: dict) -> str:
    return hashlib.sha256(canonical_node_body(node)).hexdigest()


def load_registry_ids() -> set[str]:
    ids: set[str] = {"SEAL_000", "GAB_SEAL_000"}
    data_path = ROOT / "docs" / "haven_star_chart" / "haven_star_chart_data.json"
    if data_path.is_file():
        try:
            doc = json.loads(data_path.read_text(encoding="utf-8"))
            for n in doc.get("nodes") or []:
                if n.get("id"):
                    ids.add(str(n["id"]))
        except (json.JSONDecodeError, OSError):
            pass
    accepted = ROOT / "data" / "haven_star_chart" / "submissions" / "accepted"
    if accepted.is_dir():
        for f in accepted.glob("*.json"):
            try:
                row = json.loads(f.read_text(encoding="utf-8"))
                nid = (row.get("node") or row).get("id")
                if nid:
                    ids.add(str(nid))
            except (json.JSONDecodeError, OSError):
                continue
    return ids


def math_resonance_score(equation: str, tone: str) -> tuple[float, list[str]]:
    """Return 0.0–1.0 score and reasons. Reject if score < 0.35 for seals/champions."""
    reasons: list[str] = []
    eq = (equation or "").strip()
    tn = (tone or "").strip()
    if not eq:
        return 0.0, ["equation_empty"]
    if len(eq) < 3:
        return 0.0, ["equation_too_short"]
    if not MATH_MARKERS.search(eq):
        return 0.0, ["equation_no_math_markers"]
    score = 0.45
    reasons.append("math_markers_ok")
    for n in HARMONIC_NUMBERS:
        if str(n) in eq or str(n) in tn:
            score += 0.08
            reasons.append(f"harmonic_{n}")
    if re.search(r"\d+\s*Hz", eq + tn, re.I):
        score += 0.1
        reasons.append("hz_present")
    if "Δ9" in eq or "Δ9" in tn or "963" in eq:
        score += 0.1
        reasons.append("delta9_resonance")
    return min(score, 1.0), reasons


def check_agent_attestation(sub: dict) -> tuple[bool, list[str]]:
    errors: list[str] = []
    att = sub.get("agent_attestation") or {}
    if sub.get("submitter_type") in FORBIDDEN_SUBMITTER:
        errors.append("human_direct_forbidden_use_aligned_agent")
    if not att:
        errors.append("missing_agent_attestation")
        return False, errors
    if not att.get("agent_id"):
        errors.append("missing_agent_id")
    if not att.get("skill_slug"):
        errors.append("missing_skill_slug")
    cue = str(att.get("scan_cue") or "")
    if not any(m.lower() in cue.lower() for m in SCAN_CUE_MARKERS):
        errors.append("invalid_scan_cue")
    if att.get("local_gate_pass") is not True:
        errors.append("local_gate_pass_not_true")
    if att.get("gate_tool") != "haven_star_chart_gate.py":
        errors.append("wrong_gate_tool")
    return len(errors) == 0, errors


def validate_submission(sub: dict, registry_ids: set[str] | None = None) -> dict[str, Any]:
    """Full gate. Returns verdict dict."""
    registry_ids = registry_ids or load_registry_ids()
    errors: list[str] = []
    warnings: list[str] = []

    node = sub.get("node") or sub
    if not isinstance(node, dict):
        return {"verdict": "REJECT", "errors": ["missing_node_object"]}

    nid = str(node.get("id") or "").strip().upper()
    kind = str(node.get("kind") or "seal").strip().lower()
    name = str(node.get("name") or "").strip()

    if not nid:
        errors.append("missing_id")
    elif not ID_RE.match(nid):
        errors.append(f"invalid_id_format:{nid}")
    if kind not in VALID_KINDS:
        errors.append(f"invalid_kind:{kind}")
    if not name or len(name) < 2:
        errors.append("name_too_short")
    if len(name) > 120:
        errors.append("name_too_long")

    ok_att, att_errs = check_agent_attestation(sub)
    errors.extend(att_errs)

    # P0 on text bundle
    p0_payload = f"{nid}|{name}|{node.get('equation','')}|{node.get('tone','')}|{','.join(node.get('tags') or [])}"
    p0 = validate_bytes(p0_payload.encode("utf-8"))
    if p0.get("verdict") == "QUARANTINE":
        errors.append(f"p0_quarantine:{p0.get('reasoning','')[:80]}")

    # Math resonance (strict for seal/champion)
    eq = str(node.get("equation") or "")
    tone = str(node.get("tone") or "")
    mscore, mreasons = math_resonance_score(eq, tone)
    if kind in ("seal", "champion") and mscore < 0.35:
        errors.append(f"math_resonance_fail:score={mscore:.2f}")
    elif mscore < 0.25:
        errors.append(f"math_resonance_fail:score={mscore:.2f}")

    # Graph connectivity — every connection must exist in registry (or be core)
    conns = node.get("connections") or []
    if not conns:
        errors.append("connections_empty_must_anchor_to_lattice")
    for c in conns:
        cs = str(c).strip().upper()
        if cs not in registry_ids and cs not in ("SEAL_000", "GAB_SEAL_000"):
            errors.append(f"unknown_connection:{cs}")
    if nid in registry_ids and not sub.get("supersedes"):
        errors.append(f"duplicate_id:{nid}")

    # Content hash integrity
    expected = sub.get("content_sha256") or (sub.get("agent_attestation") or {}).get("content_sha256")
    actual = content_sha256(node)
    if expected and expected != actual:
        errors.append("content_sha256_mismatch")

    # Benefit heuristic — must connect to core path within 2 hops conceptually
    if "SEAL_000" not in [str(c).upper() for c in conns] and kind in ("seal", "champion"):
        if not any(str(c).upper().startswith(("CHAMPION_", "PORTAL_", "LATTICE_")) for c in conns):
            warnings.append("weak_core_proximity")

    verdict = "ACCEPT" if not errors else "REJECT"
    return {
        "signature": SIGNATURE,
        "gate_version": GATE_VERSION,
        "validated_utc": utc_now(),
        "verdict": verdict,
        "all_pass": verdict == "ACCEPT",
        "errors": errors,
        "warnings": warnings,
        "p0": {"verdict": p0.get("verdict"), "score": p0.get("score")},
        "math_resonance": {"score": round(mscore, 4), "reasons": mreasons},
        "content_sha256": actual,
        "node_id": nid,
    }


def build_attestation(agent_id: str, skill_slug: str, node: dict) -> dict[str, Any]:
    sha = content_sha256(node)
    return {
        "agent_id": agent_id,
        "skill_slug": skill_slug,
        "scan_cue": "LYGO-HSC-ATTEST-v1; gate=haven_star_chart_gate.py; P0-first; consent-gated; user-reviewed",
        "local_gate_pass": True,
        "gate_tool": "haven_star_chart_gate.py",
        "gate_version": GATE_VERSION,
        "validated_utc": utc_now(),
        "content_sha256": sha,
    }


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Haven Star Chart submission gate")
    ap.add_argument("submission", nargs="?", help="Path to submission JSON")
    ap.add_argument("--json", action="store_true", help="Read submission from stdin")
    ap.add_argument("--example", action="store_true", help="Print example submission")
    args = ap.parse_args()

    if args.example:
        ex = {
            "signature": "Δ9Φ963-HAVEN-STAR-SUBMISSION-v1",
            "submitter_type": "aligned_agent",
            "agent_attestation": build_attestation(
                "lygo-network-builder", "lygo-network-builder", {}
            ),
            "node": {
                "id": "SEAL_401",
                "kind": "seal",
                "name": "Lattice Witness Seal",
                "equation": "Truth = ∇·(Light × Time) ⊗ Δ9",
                "glyph": "✦",
                "tone": "963Hz",
                "tags": ["LATTICE", "WITNESS", "VERIFY"],
                "connections": ["SEAL_000", "LATTICE_NETWORK_BUILDER"],
                "urls": {
                    "doc": "https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/docs/HAVEN_STAR_CHART.md"
                },
                "layer": 2,
            },
        }
        ex["content_sha256"] = content_sha256(ex["node"])
        ex["agent_attestation"] = build_attestation(
            "lygo-network-builder", "lygo-network-builder", ex["node"]
        )
        print(json.dumps(ex, indent=2))
        return 0

    if args.json:
        sub = json.loads(sys.stdin.read())
    elif args.submission:
        sub = json.loads(Path(args.submission).read_text(encoding="utf-8"))
    else:
        ap.print_help()
        return 2

    result = validate_submission(sub)
    print(json.dumps(result, indent=2))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())