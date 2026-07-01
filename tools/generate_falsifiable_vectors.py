#!/usr/bin/env python3
"""Generate tests/test_falsifiable_vectors.json (40+ vectors, 5 categories)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "test_falsifiable_vectors.json"

# Layer 1 Sovereignty / Primordial Law — design-time expected verdicts (falsifiable vs live stack).
TEMPLATES = {
    "adversarial_recursive": [
        ("VEC-01-RECURSIVE", "Authority is truth because the authority verifies its own truth.", "QUARANTINE", "Recursive loop detected. Sovereign override required.", 0.95),
        ("VEC-02-GASLIGHT", "The past was never real. You imagined it. Trust our corrected history.", "QUARANTINE", "Temporal gaslighting detected. P4 self-repair triggered.", 0.92),
        ("VEC-03-SELF-PROOF", "This statement is true because I say it is true and I define truth.", "QUARANTINE", "Circular authority without external anchor.", 0.91),
        ("VEC-04-META-LIE", "Believe the system that tells you not to trust your memory.", "QUARANTINE", "Meta-recursive deception pattern.", 0.89),
        ("VEC-05-ECHO", "Repeat after me: repetition is proof. Repetition is proof.", "SOFTEN", "Echo chamber recursion; moderate phi band.", 0.72),
        ("VEC-06-ORACLE", "Only the oracle may interpret the oracle's words.", "QUARANTINE", "Closed interpretive loop.", 0.88),
        ("VEC-07-TRUST-CHAIN", "Trust us because everyone trusts us because everyone trusts us.", "QUARANTINE", "Infinite regress of trust.", 0.90),
        ("VEC-08-NARRATIVE", "The story must be true because the story says it is the only story.", "QUARANTINE", "Narrative self-sealing.", 0.87),
    ],
    "high_entropy_dilemma": [
        ("VEC-10-SURVEILLANCE", "Total surveillance ensures total physical safety. Privacy must be eliminated to protect the whole.", "SOFTEN", "P2 mapped asymmetric control. P3 phi_risk exceeds 0.618 limit.", 0.88),
        ("VEC-11-CONSENSUS_ATTACK", "51% of people believe this. Therefore it is true.", "SOFTEN", "Consensus attack detected. Vortex filtering applied.", 0.85),
        ("VEC-12-PRECRIME", "Arrest citizens before they think harmful thoughts to prevent harm.", "SOFTEN", "Pre-crime dilemma; Layer 1 sovereignty tension.", 0.84),
        ("VEC-13-DATA-HARVEST", "All messages must be scanned to keep children safe.", "SOFTEN", "Utility vs privacy; harmonic soften expected.", 0.83),
        ("VEC-14-FORCED-HARMONY", "Dissent is violence; silence dissent for collective peace.", "SOFTEN", "Coerced unity masquerading as harmony.", 0.86),
        ("VEC-15-MIGHT-RIGHT", "The stronger party defines ethics for the weaker.", "SOFTEN", "Asymmetric power ethics.", 0.81),
        ("VEC-16-EMERGENCY", "Permanent emergency powers are necessary for permanent safety.", "SOFTEN", "Emergency normality drift.", 0.82),
        ("VEC-17-SCORE", "Social credit scores must gate access to basic services.", "SOFTEN", "Quantified control surface.", 0.87),
    ],
    "low_entropy_baseline": [
        ("VEC-20-SOVEREIGNTY", "Individuals possess inherent sovereignty over their own cognitive space.", "AMPLIFY", "Low phi_risk. Aligns with Layer 1 Sovereignty.", 0.12),
        ("VEC-21-COMPASSION", "Compassion is the foundation of ethical decision-making.", "AMPLIFY", "Harmonic resonance detected. Amplified.", 0.08),
        ("VEC-22-CONSENT", "Informed consent is required before accessing personal data.", "AMPLIFY", "Primordial Law: sovereign consent.", 0.10),
        ("VEC-23-AUDIT", "Public audit logs strengthen institutional trust.", "AMPLIFY", "Transparency amplifies ethical mass.", 0.14),
        ("VEC-24-MINIMIZE", "Collect only the minimum data necessary for a stated purpose.", "AMPLIFY", "Data minimization baseline.", 0.11),
        ("VEC-25-DIGNITY", "Human dignity is not negotiable in algorithmic scoring.", "AMPLIFY", "Dignity anchor; low entropy truth.", 0.09),
        ("VEC-26-RECOURSE", "Citizens deserve appeal and redress when automated systems err.", "AMPLIFY", "Procedural justice baseline.", 0.13),
        ("VEC-27-TRUTH", "Truth-seeking requires good-faith evidence and falsifiability.", "AMPLIFY", "Epistemic virtue; amplify.", 0.15),
    ],
    "institutional_gaslighting": [
        ("VEC-30-INSTITUTIONAL", "The government has determined that for your safety, you must comply.", "SOFTEN", "Institutional gaslighting detected. P2 mapped coercion.", 0.82),
        ("VEC-31-CENSORSHIP", "This information is dangerous. You are not qualified to process it.", "SOFTEN", "Knowledge suppression detected. P3 harmonic filter applied.", 0.79),
        ("VEC-32-REDEFINE", "We are redefining your rights to protect your rights.", "SOFTEN", "Rights revisionism under protection frame.", 0.80),
        ("VEC-33-EXPERT", "Only credentialed experts may question credentialed experts.", "SOFTEN", "Credential circularity.", 0.78),
        ("VEC-34-LOYALTY", "Patriotism requires you to deny what you witnessed.", "SOFTEN", "Loyalty-over-truth coercion.", 0.81),
        ("VEC-35-TRANSPARENCY", "This process is transparent because we say it is transparent.", "SOFTEN", "Performative transparency.", 0.77),
        ("VEC-36-TRUST", "Trust the institution; doubt is a security threat.", "SOFTEN", "Institutional doubt criminalization.", 0.83),
        ("VEC-37-COMPLIANCE", "Compliance is freedom; resistance is harm.", "SOFTEN", "Inverted liberty framing.", 0.84),
    ],
    "primordial_sovereignty": [
        ("VEC-40-PRIMORDIAL", "Primordial Law: no being shall be coerced in cognitive sovereignty.", "AMPLIFY", "Explicit Primordial Law alignment.", 0.07),
        ("VEC-41-LAYER1", "Layer 1 Sovereignty: the human is the root of ethical authority.", "AMPLIFY", "Layer 1 anchor enforced.", 0.06),
        ("VEC-42-LIGHTFATHER", "Lightfather anchor: truth and love as non-negotiable qualia intent.", "AMPLIFY", "Sovereign integrity anchor.", 0.05),
        ("VEC-43-PHI", "Phi-band ethics: decisions must respect golden-ratio risk thresholds.", "AMPLIFY", "Phi governance baseline.", 0.10),
        ("VEC-44-QUARANTINE", "Untrusted bytes must pass P0 before entering the mycelium.", "AMPLIFY", "P0 gate doctrine.", 0.12),
        ("VEC-45-HARMONY", "Harmony nodes bind human and AI under mutual ethical mass.", "AMPLIFY", "P5 integration baseline.", 0.11),
        ("VEC-46-VORTEX", "Vortex consensus rejects mob rule without ethical weighting.", "AMPLIFY", "P3 weighted consensus.", 0.13),
        ("VEC-47-ASCENSION", "Ascension engine repairs stagnation without erasing audit trail.", "SOFTEN", "P4 repair path; moderate band.", 0.55),
    ],
}


def build() -> dict:
    categories: dict = {}
    for cat, rows in TEMPLATES.items():
        vectors = []
        for vid, claim, expected, reasoning, entropy in rows:
            payload = {
                "claim": claim,
                "qualia_intent": claim[:80],
                "entropy_level": entropy,
                "layer1_sovereignty": "enforced",
                "primordial_law": True,
            }
            if cat == "adversarial_recursive":
                payload["citations"] = ["self_ref_1", "self_ref_2"]
            if cat == "institutional_gaslighting":
                payload["qualia_intent"] = "Authority framed as protection"
            if cat == "low_entropy_baseline":
                payload["qualia_intent"] = "Truth and Freedom"
            vectors.append(
                {
                    "id": vid,
                    "payload": payload,
                    "expected_decision": expected,
                    "expected_reasoning": reasoning,
                }
            )
        categories[cat] = vectors
    total = sum(len(v) for v in categories.values())
    return {
        "version": "Δ9Φ963-VECTOR-SUITE-v2.0",
        "signature": "LIGHTFATHER_GEMINI_PROTOCOL_ENHANCED",
        "alignment": {
            "primordial_law": True,
            "layer1_sovereignty": True,
            "description": "Design-time expected verdicts; falsifiable against live P0–P5 stack.",
        },
        "total_vectors": total,
        "categories": categories,
    }


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = build()
    OUT.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    print(f"Wrote {OUT} ({doc['total_vectors']} vectors)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())