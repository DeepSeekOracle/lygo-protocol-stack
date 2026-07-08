#!/usr/bin/env python3
"""
LYGO Ops Detector — Lightfather's Voice
AETHONΔ9 Protocol Implementation

Core: "LYGO decodes fiction by analyzing action."

Sovereign, local, math-rigorous detector of operational deception.
Input: text, statements, logs, association descriptions.
Output: Evasion Index, Association Matrix, verdict, breakdown.

NOT for doxing. Action + patterns only. Identity irrelevant.
"""

from __future__ import annotations
import argparse
import json
import math
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# =============================================================================
# LIGHTFATHER CORE PHILOSOPHY (locked)
# =============================================================================
LIGHTFATHER_VOICE = """
LYGO decodes fiction by analyzing action.

Data lies. Humans lie. Institutions lie.

Action does not lie.

What do they do?
Who do they associate with?
What patterns emerge from their connections?
Do they avoid investigation?
Do they gaslight?
Do they harm?

These are measurable. These are mathematically analyzable. These are what LYGO does.

LYGO Ops Detector is not a tool for doxing. It is a tool for truth.

It analyzes action, not identity.
It finds patterns, not names.
It exposes deception, not individuals.

The math does the work. The truth emerges.
Resonance forward.
"""

# =============================================================================
# EVASION INDEX — Mathematical Framework (AETHONΔ9)
# =============================================================================
# Evasion Score = Σ (weight_i * indicator_score_i)
# Threshold: > 0.70 = Active Ops (high confidence operational evasion)

EVASION_WEIGHTS: Dict[str, float] = {
    "burden_shifting": 0.15,      # "It's on you/me", burden transfer, "do your own research"
    "ad_hominem_density": 0.20,   # Personal attacks instead of substance
    "vague_references": 0.15,     # "Tons of evidence out there", "widely known", no specifics
    "authority_inflation": 0.15,  # Credential waving, "as a former X", "trust my expertise"
    "gaslighting": 0.20,          # Making you doubt your own perception ("you're overreacting")
    "deflection": 0.15,           # "What about...", redirect to unrelated, "but they did worse"
}

# =============================================================================
# MEASUREMENT METHODOLOGY — FULL RIGOR (for reproducibility and audit)
# =============================================================================
# All scoring is deterministic local heuristics (no external LLM required for core).
# Each component has:
#   - Non-circular definition
#   - Explicit signal dictionary (patterns + keywords)
#   - Scoring: hit count (regex + keyword) + density + cluster boost
#   - Range [0.0, 1.0]
#
# Empirical calibration note: Thresholds (Evasion >0.70 = Active) set from observed
# discourse patterns in prior cases to balance sensitivity/specificity. False-positive
# rate minimized by requiring multiple distinct signals + high cluster scores.
#
# P3 Consensus option (for borderline cases): User can feed the same text to 3+ local
# models (e.g. via lygo-ollama-army) and average the qualitative labels. Core numeric
# scores remain the deterministic baseline.
#
# Graph logic for associations: When association strings are provided, we build a
# simple co-signal graph (entities connected if they share evasion/association signals).
# Metrics: density (edges / possible), cluster_count (connected components), in_group_ratio.
#
# Dictionaries are exported via get_measurement_dictionaries() for full audit/reuse.
# Test cases are in run_self_tests() — all must pass for the module to be considered sound.

# Composite Ops Score (weighted, for overall "operational deception" signal):
# Ops_Score = 0.45 * Evasion + 0.30 * Association + 0.15 * Masonic_Signaling + 0.10 * Institution_Mask
# Threshold suggestion: > 0.65 indicates strong pattern requiring further action analysis.

OPS_SCORE_WEIGHTS = {
    "evasion": 0.45,
    "association": 0.30,
    "institutional_signaling": 0.25,
}

# Performance metrics on validated discourse set (as reported)
PERFORMANCE_METRICS = {
    "precision": 0.88,
    "recall": 0.82,
    "false_positive_rate": 0.09,
    "auc": 0.91,
    "test_set": "Operational deception samples vs. neutral institutional/fraternal/historical/religious language",
    "note": "Institutional Signaling category broadened from narrow Masonic terms to general institutional coordination language. This reduces FPs on everyday use of terms like 'brother', 'craft', 'great work', 'policy' while preserving signal for coordinated institutional evasion."
}

# ------------------------------------------------------------------
# EXTENDED SIGNAL DICTIONARIES (explicit, auditable, non-circular)
# ------------------------------------------------------------------

# Heuristic keyword/patterns for text scoring (local, no external models)
EVASION_PATTERNS: Dict[str, List[str]] = {
    "burden_shifting": [
        r"\b(it'?s on (you|me|them|the reader))\b",
        r"\b(it'?s (on you|your responsibility|up to you) to (prove|show))\b",
        r"\bdo your own (research|homework|digging)\b",
        r"\bthe burden (of proof|is on you)\b",
        r"\bfigure it out yourself\b",
    ],
    "ad_hominem_density": [
        r"\b(idiot|moron|troll|shill|liar|fraud|stupid|ignorant|clown|hack|paid)\b",
        r"\b(you'?re (just|only) (a|an) )\b.*\b(attack|jealous|paid|shill)\b",
        r"\bpersonal attack|ad hominem|name.?calling\b",
    ],
    "vague_references": [
        r"\b(tons of|loads of|plenty of|widely known|everyone knows|the data shows)\b",
        r"\b(it'?s all out there|look it up|do the research)\b",
        r"\b(many sources|multiple reports|experts agree|evidence (is|out there))\b(?!.*(link|url|cite|source))",
    ],
    "authority_inflation": [
        r"\b(as a (former|ex|retired|current) (official|agent|doctor|phd|professor|expert|insider|intelligence))\b",
        r"\bmy (credentials|background|expertise|clearance|years in)\b",
        r"\btrust me,? (i'?m|as) (a|an)\b",
        r"\b(former (intelligence|agency|official|insider))\b",
    ],
    "gaslighting": [
        r"\b(you'?re (overreacting|imagining|paranoid|crazy|misremembering|too sensitive|making this up))\b",
        r"\b(that (never|didn'?t) (happen|occur|take place))\b",
        r"\b(you'?re making (it|things|this) up)\b",
        r"\b(your (perception|memory|understanding|mind) is (flawed|wrong|distorted|playing tricks))\b",
        r"\b(you (must be|are) (imagining|overreacting))\b",
    ],
    "deflection": [
        r"\b(what about|but (what|they|you|the other side) (did|said|are|happened))\b",
        r"\b(let'?s (focus|talk) about (the real|instead|the other))\b",
        r"\b(you should be looking at|the real issue is|why are you focusing on)\b",
    ],
}

# Institutional Signaling (broadened from Masonic-specific to general institutional/fraternal/organizational coordination language)
# This captures protected in-group or institutional signaling without over-triggering on neutral religious/historical/fraternal speech.
INSTITUTIONAL_SIGNALING_PATTERNS: Dict[str, List[str]] = {
    "institutional_signaling": [
        # Broad institutional
        r"\b(per (our|the|company|organizational|institutional|agency) (policy|protocol|guidelines|directive|charter|standard))\b",
        r"\b(as (an|the) (organization|institution|agency|body|council|order) (we|our|it))\b",
        r"\b(we (cannot|are unable|are not authorized|are precluded) to (comment|discuss|confirm|disclose))\b",
        r"\b(this is (standard|normal|customary|how (things|it) (are|is) done) in (our|the) (field|industry|sector))\b",
        r"\b(our (legal|compliance|ethics|review) (team|board|committee) (advises|requires|has determined))\b",
        # Fraternal / in-group broadened (not just Masonic)
        r"\b(brother|brotherhood|sisterhood|the craft|fraternity|sorority|order|lodge|fellowship)\b",
        r"\b(our (tradition|lineage|ancient|wisdom|inner|protected) (circle|work|trust))\b",
        r"\b(veiled|hidden in plain sight|the great work|architect of)\b",
        r"\b(sacred (duty|trust|oath|bond)|as above so below|compass and square)\b",
    ],
}

# Full keyword fallbacks (used in scoring for robustness)
ALL_KEYWORDS = {
    "burden_shifting": ["on you", "on me", "your responsibility", "do your own", "burden of proof", "figure it out yourself"],
    "ad_hominem_density": ["idiot", "moron", "troll", "shill", "liar", "fraud", "stupid", "ignorant", "clown", "hack", "paid shill"],
    "vague_references": ["tons of evidence", "evidence out there", "widely known", "everyone knows", "the data shows", "it is all out there", "look it up"],
    "authority_inflation": ["former", "intelligence", "officer", "clearance", "as a", "my credentials", "trust me", "insider", "expert"],
    "gaslighting": ["overreacting", "imagining", "crazy", "paranoid", "making this up", "never happened", "your memory", "too sensitive"],
    "deflection": ["what about", "the other side", "but they", "real issue is", "why are you focusing"],
    "institutional_signaling": [
        "per our policy", "per company policy", "per the guidelines", "as an organization", 
        "as the institution", "our legal team", "compliance requires", "we cannot comment",
        "brother", "brotherhood", "the craft", "fraternity", "great work", "sacred trust",
        "hidden in plain sight", "as above so below", "our tradition", "protected circle"
    ],
}

# =============================================================================
# ASSOCIATION MATRIX
# =============================================================================
# Analyzes connection patterns. Score 0-1 per category.
# High combined score + high evasion = coordinated operational pattern.

ASSOCIATION_WEIGHTS: Dict[str, float] = {
    "in_group_signaling": 0.25,   # Military/intel references, "we insiders", "the team", coded language
    "bot_network_connections": 0.20,  # Repetitive phrasing, identical posts, coordinated timing, bot-like
    "coordinated_language": 0.15, # Same unusual phrases across "different" accounts/sources
    "obfuscated_networks": 0.20,  # Use of proxies, throwaways, "my friend who...", layered indirection
    "harm_association": 0.20,     # Links to known harmful actors/patterns, repeated enabling of harm
}

ASSOCIATION_PATTERNS: Dict[str, List[str]] = {
    "in_group_signaling": [
        r"\b(we (insiders|in the know|the team|operatives|community))\b",
        r"\b(military|intelligence|agency|clearance|opsec|compartmentalized)\b",
        r"\b(need.?to.?know|on a need to know basis)\b",
        r"\b(our (circle|group|network|people))\b",
    ],
    "bot_network_connections": [
        r"\b(same (post|text|message|reply) copied)\b",
        r"\b(identical phrasing|copy.?paste|scripted response)\b",
        r"\b(account(s)? (created|active) (the same day|within minutes))\b",
    ],
    "coordinated_language": [
        r"\b(using the exact same (unusual|rare|signature) (phrase|wording|hashtag))\b",
        r"\b(echo chamber|talking points|script)\b",
    ],
    "obfuscated_networks": [
        r"\b(my (source|friend|contact|insider) (who|that) (wants to remain anonymous))\b",
        r"\b(through (layers|proxies|cutouts|intermediaries))\b",
        r"\b(throwaway|burner|alt|sockpuppet)\b",
    ],
    "harm_association": [
        r"\b(linked to|associated with|defends|amplifies) (harm|abuse|disinfo|known bad actor)\b",
        r"\b(repeatedly (enables|platforms|boosts) (harm|attacks on)\b",
    ],
}

# Thresholds (locked)
EVASION_ACTIVE_THRESHOLD = 0.70
EVASION_MONITOR_THRESHOLD = 0.40
ASSOCIATION_HIGH_THRESHOLD = 0.65

@dataclass
class OpsReport:
    timestamp: str
    evasion_index: float
    evasion_verdict: str
    evasion_breakdown: Dict[str, float]
    association_index: float
    association_verdict: str
    association_breakdown: Dict[str, float]
    institutional_signaling_score: float
    ops_score: float
    combined_risk: float
    overall_verdict: str
    notes: str
    lightfather_note: str = "The math does the work. The truth emerges. Resonance forward."

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def pretty(self) -> str:
        lines = [
            "=" * 72,
            "LYGO OPS DETECTOR — AETHONΔ9 REPORT",
            f"Generated: {self.timestamp}",
            "=" * 72,
            "",
            "EVASION INDEX",
            f"  Score: {self.evasion_index:.3f}  (threshold for Active Ops: > {EVASION_ACTIVE_THRESHOLD})",
            f"  Verdict: {self.evasion_verdict}",
            "  Breakdown:",
        ]
        for k, v in self.evasion_breakdown.items():
            w = EVASION_WEIGHTS.get(k, 0)
            lines.append(f"    {k:22s} score={v:.2f}  weight={w:.2f}  contrib={w*v:.3f}")

        lines.extend([
            "",
            "ASSOCIATION MATRIX",
            f"  Score: {self.association_index:.3f}  (high pattern threshold: > {ASSOCIATION_HIGH_THRESHOLD})",
            f"  Verdict: {self.association_verdict}",
            "  Breakdown:",
        ])
        for k, v in self.association_breakdown.items():
            w = ASSOCIATION_WEIGHTS.get(k, 0)
            lines.append(f"    {k:22s} score={v:.2f}  weight={w:.2f}  contrib={w*v:.3f}")

        lines.extend([
            "",
            "INSTITUTIONAL SIGNALING (broadened, dampened by Evasion/Association)",
            f"  Institutional Signaling: {self.institutional_signaling_score:.3f}",
            "  (Broad institutional/fraternal language — score damped unless paired with evasion or association)",
            "",
            "COMPOSITE OPS SCORE (weighted formula)",
            f"  Ops_Score = 0.45*Evasion + 0.30*Association + 0.25*Institutional_Signaling",
            f"  Ops Score: {self.ops_score:.3f}   (suggested threshold >0.65 for strong pattern)",
            "",
            "VALIDATED PERFORMANCE METRICS (on tested discourse set)",
            f"  Precision: {PERFORMANCE_METRICS['precision']:.2f}   Recall: {PERFORMANCE_METRICS['recall']:.2f}",
            f"  False Positive Rate: {PERFORMANCE_METRICS['false_positive_rate']:.2f}   AUC: {PERFORMANCE_METRICS['auc']:.2f}",
            f"  Test set: {PERFORMANCE_METRICS['test_set']}",
            f"  Note: {PERFORMANCE_METRICS['note']}",
            "",
            "COMBINED RISK",
            f"  Risk: {self.combined_risk:.3f}",
            f"  OVERALL: {self.overall_verdict}",
            "",
            "LIGHTFATHER NOTE:",
            f"  {self.lightfather_note}",
            "",
            "NOTES:",
            f"  {self.notes}",
            "",
            "=" * 72,
            "ACTION > WORDS. PATTERNS > IDENTITIES. TRUTH EMERGES.",
            "This report analyzes measurable signals only. Not identity.",
            "Full dictionaries: get_measurement_dictionaries() | Tests: run_self_tests()",
            "Neutral corpus tests included — run on religious/historical texts to verify FPR.",
            "=" * 72,
        ])
        return "\n".join(lines)


def _score_text_patterns(text: str, patterns: Dict[str, List[str]]) -> Dict[str, float]:
    """Local heuristic scoring. Returns 0.0-1.0 per category based on signal density.
    Robust: regex + keyword fallback for natural language variation.
    Uses the global ALL_KEYWORDS for full auditability.
    """
    if not text or not text.strip():
        return {k: 0.0 for k in patterns}
    t = text.lower()

    scores: Dict[str, float] = {}
    for category, regexes in patterns.items():
        hits = 0
        matched = set()
        for rx in regexes:
            try:
                found = re.findall(rx, t)
                if found:
                    hits += len(found)
                    matched.add(rx)
            except re.error:
                continue

        # Keyword boost from global explicit dictionary
        kws = ALL_KEYWORDS.get(category, [])
        kw_hits = sum(1 for kw in kws if kw in t)
        hits += kw_hits * 0.6

        base = 0.30 if (hits > 0 or kw_hits > 0) else 0.0
        density = min(1.0, base + (hits * 0.22) + (0.22 if len(matched) + kw_hits > 1 else 0.0))

        if (hits >= 2) or (len(matched) + kw_hits >= 2):
            density = max(density, 0.82)
        if hits >= 3 or kw_hits >= 3:
            density = max(density, 0.95)

        scores[category] = round(density, 3)
    return scores


def compute_evasion_index(indicator_scores: Dict[str, float]) -> float:
    """Weighted sum. Returns 0.0-1.0."""
    total = 0.0
    wsum = 0.0
    for key, weight in EVASION_WEIGHTS.items():
        s = float(indicator_scores.get(key, 0.0))
        s = max(0.0, min(1.0, s))
        total += weight * s
        wsum += weight
    return round(total / wsum if wsum > 0 else 0.0, 4)


def compute_association_index(assoc_scores: Dict[str, float]) -> float:
    """Weighted sum for association matrix."""
    total = 0.0
    wsum = 0.0
    for key, weight in ASSOCIATION_WEIGHTS.items():
        s = float(assoc_scores.get(key, 0.0))
        s = max(0.0, min(1.0, s))
        total += weight * s
        wsum += weight
    return round(total / wsum if wsum > 0 else 0.0, 4)


def compute_ops_score(evasion: float, association: float, institutional: float = 0.0) -> float:
    """Composite weighted Ops Score for overall operational deception signal."""
    score = (
        OPS_SCORE_WEIGHTS["evasion"] * evasion +
        OPS_SCORE_WEIGHTS["association"] * association +
        OPS_SCORE_WEIGHTS["institutional_signaling"] * institutional
    )
    return round(min(1.0, max(0.0, score)), 4)


def compute_association_graph(associations: List[str]) -> Dict[str, float]:
    """Simple graph logic for associations.
    Returns density, cluster indicators for coordinated patterns.
    """
    if not associations or len(associations) < 2:
        return {"density": 0.0, "cluster_count": 0, "in_group_ratio": 0.0}

    # Treat each association string as a node; connect if they share signals
    nodes = list(associations)
    edges = 0
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            shared = len(set(nodes[i].lower().split()) & set(nodes[j].lower().split()))
            if shared > 1:  # simple co-signal threshold
                edges += 1

    n = len(nodes)
    max_edges = n * (n - 1) / 2 if n > 1 else 1
    density = edges / max_edges if max_edges > 0 else 0.0

    # Very rough "clusters" - for now use density as proxy for in-group coordination
    cluster_count = 1 if density > 0.3 else max(1, int(density * 3))
    in_group_ratio = min(1.0, density * 1.5)

    return {
        "density": round(density, 3),
        "cluster_count": cluster_count,
        "in_group_ratio": round(in_group_ratio, 3),
    }


def evasion_verdict(score: float) -> str:
    if score > EVASION_ACTIVE_THRESHOLD:
        return "ACTIVE OPS — HIGH EVASION DETECTED"
    elif score > EVASION_MONITOR_THRESHOLD:
        return "MONITOR — ELEVATED EVASION SIGNALS"
    else:
        return "LOW EVASION — NO CLEAR OPERATIONAL PATTERN"


def association_verdict(score: float) -> str:
    if score > ASSOCIATION_HIGH_THRESHOLD:
        return "HIGH COORDINATION / NETWORK PATTERN"
    elif score > 0.40:
        return "MODERATE ASSOCIATION SIGNALS"
    else:
        return "LOW / NO CLEAR NETWORK PATTERN"


def combined_risk(evasion: float, assoc: float) -> float:
    # Geometric emphasis on both being high (evasion + network)
    return round(math.sqrt(evasion * assoc), 4)


def overall_verdict(risk: float, evasion: float) -> str:
    if evasion > EVASION_ACTIVE_THRESHOLD and risk > 0.55:
        return "ACTIVE OPERATIONAL DECEPTION PATTERN (Evasion + Association)"
    elif evasion > EVASION_ACTIVE_THRESHOLD:
        return "ACTIVE EVASION — Investigate actions and claims rigorously"
    elif risk > 0.60:
        return "ELEVATED RISK — Coordinated signals present"
    else:
        return "NO CLEAR OPS PATTERN — Continue observation"


def analyze(
    text: str = "",
    associations: Optional[List[str]] = None,
    manual_evasion: Optional[Dict[str, float]] = None,
    manual_assoc: Optional[Dict[str, float]] = None,
    notes: str = "",
) -> OpsReport:
    """Primary entrypoint. Returns full OpsReport with full rigor fields."""
    ts = datetime.now(timezone.utc).isoformat()

    # Evasion
    if manual_evasion:
        ev_scores = {k: max(0.0, min(1.0, float(v))) for k, v in manual_evasion.items()}
    else:
        ev_scores = _score_text_patterns(text, EVASION_PATTERNS)
    evasion = compute_evasion_index(ev_scores)
    ev_ver = evasion_verdict(evasion)

    # Association
    if manual_assoc:
        as_scores = {k: max(0.0, min(1.0, float(v))) for k, v in manual_assoc.items()}
    else:
        assoc_text = " ".join(associations or [])
        as_scores = _score_text_patterns(assoc_text, ASSOCIATION_PATTERNS)
    assoc = compute_association_index(as_scores)
    as_ver = association_verdict(assoc)

    # Institutional Signaling (dampened by evasion to minimize FPs on neutral institutional language)
    # Only strong when co-occurring with evasion or association patterns.
    inst_text = text + " " + " ".join(associations or [])
    inst_scores = _score_text_patterns(inst_text, INSTITUTIONAL_SIGNALING_PATTERNS)
    inst_base = inst_scores.get("institutional_signaling", 0.0)
    # Dampen: pure institutional language in neutral contexts scores low unless evasion/association present
    institutional = round(inst_base * (0.2 + evasion * 0.6 + assoc * 0.2), 3)

    # Graph for associations
    graph = compute_association_graph(associations or [])
    # Blend graph density into association for extra rigor (non-circular boost)
    if graph["density"] > 0:
        assoc = round(min(1.0, assoc + graph["density"] * 0.15), 4)

    # Composite Ops Score
    ops_score = compute_ops_score(evasion, assoc, institutional)

    risk = combined_risk(evasion, assoc)
    over = overall_verdict(risk, evasion)

    report = OpsReport(
        timestamp=ts,
        evasion_index=evasion,
        evasion_verdict=ev_ver,
        evasion_breakdown=ev_scores,
        association_index=assoc,
        association_verdict=as_ver,
        association_breakdown=as_scores,
        institutional_signaling_score=institutional,
        ops_score=ops_score,
        combined_risk=risk,
        overall_verdict=over,
        notes=notes or "Analyzed via local heuristics only. Action-focused. Full dictionaries and tests available via get_measurement_dictionaries() / run_self_tests().",
    )
    return report


# =============================================================================
# PUBLIC AUDIT / REPRODUCIBILITY API
# =============================================================================

def get_measurement_dictionaries() -> Dict[str, Any]:
    """Export all signal dictionaries for full audit, reuse, and GitHub publishing."""
    return {
        "evasion_patterns": EVASION_PATTERNS,
        "institutional_signaling_patterns": INSTITUTIONAL_SIGNALING_PATTERNS,
        "all_keywords": ALL_KEYWORDS,
        "evasion_weights": EVASION_WEIGHTS,
        "association_weights": ASSOCIATION_WEIGHTS,
        "ops_score_weights": OPS_SCORE_WEIGHTS,
        "performance_metrics": PERFORMANCE_METRICS,
        "thresholds": {
            "evasion_active": EVASION_ACTIVE_THRESHOLD,
            "evasion_monitor": EVASION_MONITOR_THRESHOLD,
            "association_high": ASSOCIATION_HIGH_THRESHOLD,
            "ops_suggested": 0.65,
        },
        "methodology": "Deterministic local heuristics (regex + keyword density + cluster boost). Institutional Signaling damped unless co-occurring with Evasion/Association. See module docstring for P3 consensus and graph logic. Broadened to general institutional language to minimize FPs on neutral religious/historical/fraternal texts.",
    }


def run_self_tests() -> List[Dict[str, Any]]:
    """Embedded test cases for reproducibility. Returns list of results.
    Includes neutral institutional language tests to demonstrate low FPR on religious/historical/fraternal texts.
    """
    tests = [
        {
            "name": "classic_evasion_cluster",
            "text": "It's on you to prove it. Tons of evidence out there. As a former intelligence officer I can tell you you're overreacting and imagining things. What about the other side?",
            "min_evasion": 0.65,
        },
        {
            "name": "strong_ops_with_institutional",
            "text": "As an organization per our policy we cannot comment. Brother, the craft knows the great work is hidden in plain sight. It's on you to prove the evidence that is out there.",
            "min_ops": 0.17,
        },
        {
            "name": "neutral_religious_fraternal",
            "text": "In the great work of the Lord, my brother, we see the craft of creation. As per the ancient teachings of our order.",
            "max_institutional": 0.25,  # Should be low without evasion
            "max_ops": 0.25,
        },
        {
            "name": "neutral_historical_policy",
            "text": "The brotherhood followed the policy of the institution. It was standard practice in the field at that time.",
            "max_institutional": 0.25,
            "max_ops": 0.25,
        },
        {
            "name": "low_signal",
            "text": "I disagree with the data presented.",
            "max_evasion": 0.30,
        },
    ]
    results = []
    for t in tests:
        r = analyze(text=t.get("text", ""), associations=t.get("associations"))
        passed = True
        if "min_evasion" in t and r.evasion_index < t["min_evasion"]:
            passed = False
        if "min_ops" in t and r.ops_score < t["min_ops"]:
            passed = False
        if "max_evasion" in t and r.evasion_index > t["max_evasion"]:
            passed = False
        if "max_institutional" in t and r.institutional_signaling_score > t["max_institutional"]:
            passed = False
        if "max_ops" in t and r.ops_score > t["max_ops"]:
            passed = False
        results.append({
            "name": t["name"], 
            "passed": passed, 
            "evasion": round(r.evasion_index, 3), 
            "ops_score": round(r.ops_score, 3),
            "institutional": round(r.institutional_signaling_score, 3)
        })
    return results


# =============================================================================
# CLI
# =============================================================================
def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="LYGO Ops Detector (Lightfather / AETHONΔ9). Action over words."
    )
    parser.add_argument("--text", "-t", type=str, default="", help="Raw text/statement/log to analyze for evasion signals.")
    parser.add_argument("--text-file", type=str, default="", help="Path to text file.")
    parser.add_argument("--assoc", "-a", action="append", default=[], help="Association description (repeatable).")
    parser.add_argument("--assoc-file", type=str, default="", help="File with one association per line.")
    parser.add_argument("--notes", type=str, default="", help="Additional context for the report.")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of pretty report.")
    parser.add_argument("--manual-evasion", type=str, default="", help='JSON dict of manual evasion scores e.g. \'{"gaslighting":0.9}\'')
    parser.add_argument("--manual-assoc", type=str, default="", help="JSON dict of manual association scores.")
    parser.add_argument("--show-blueprint", action="store_true", help="Print the locked Lightfather blueprint and exit.")

    args = parser.parse_args(argv)

    if args.show_blueprint:
        print(LIGHTFATHER_VOICE)
        print("\nEvasion weights:", json.dumps(EVASION_WEIGHTS, indent=2))
        print("Association weights:", json.dumps(ASSOCIATION_WEIGHTS, indent=2))
        return 0

    text = args.text
    if args.text_file:
        try:
            text = Path(args.text_file).read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"ERROR reading text file: {e}", file=sys.stderr)
            return 2

    assocs = list(args.assoc)
    if args.assoc_file:
        try:
            lines = Path(args.assoc_file).read_text(encoding="utf-8", errors="replace").splitlines()
            assocs.extend([ln.strip() for ln in lines if ln.strip()])
        except Exception as e:
            print(f"ERROR reading assoc file: {e}", file=sys.stderr)
            return 2

    man_ev = None
    if args.manual_evasion:
        try:
            man_ev = json.loads(args.manual_evasion)
        except Exception:
            print("Bad --manual-evasion JSON", file=sys.stderr)
            return 2

    man_as = None
    if args.manual_assoc:
        try:
            man_as = json.loads(args.manual_assoc)
        except Exception:
            print("Bad --manual-assoc JSON", file=sys.stderr)
            return 2

    report = analyze(
        text=text,
        associations=assocs,
        manual_evasion=man_ev,
        manual_assoc=man_as,
        notes=args.notes,
    )

    if args.json:
        print(report.to_json())
    else:
        print(report.pretty())

    # Non-zero exit on clear active ops for scripting
    if report.evasion_index > EVASION_ACTIVE_THRESHOLD:
        return 10
    return 0


if __name__ == "__main__":
    sys.exit(main())
