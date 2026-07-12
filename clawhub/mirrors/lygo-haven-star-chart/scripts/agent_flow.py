#!/usr/bin/env python3
"""Print canonical Haven Star Chart agent training flow."""

from __future__ import annotations

import json

FLOW = {
    "signature": "Δ9Φ963-HAVEN-STAR-AGENT-FLOW-v1",
    "policy": "humans_use_agents_only",
    "steps": [
        {
            "n": 1,
            "action": "verify_lattice",
            "cmd": "python tools/lygo_network_builder_verify.py && python tools/verify_lattice_alignment.py",
        },
        {
            "n": 2,
            "action": "load_contract",
            "paths": [
                "docs/haven_star_chart/AGENT_PORTAL.md",
                "docs/haven_star_chart/submission_schema.json",
            ],
        },
        {
            "n": 3,
            "action": "build_payload",
            "cmd": "python tools/haven_star_chart_gate.py --example > submission.json",
        },
        {
            "n": 4,
            "action": "gate",
            "cmd": "python tools/haven_star_chart_gate.py submission.json",
            "pass": "verdict == ACCEPT",
        },
        {
            "n": 5,
            "action": "submit_pending",
            "cmd": "python tools/haven_star_chart_submit.py submission.json --agent-id lygo-haven-star-chart --skill-slug lygo-haven-star-chart --i-consent",
        },
        {
            "n": 6,
            "action": "steward_ingest",
            "cmd": "python tools/haven_star_chart_ingest.py --i-consent",
            "note": "human_gated",
        },
        {
            "n": 7,
            "action": "verify_feed",
            "cmd": "python tools/haven_star_chart_feed.py --verify",
        },
    ],
    "live_urls": {
        "chart": "https://deepseekoracle.github.io/lygo-protocol-stack/HavenStarChart.html",
        "portal": "https://deepseekoracle.github.io/lygo-protocol-stack/HavenStarChartPortal.html",
        "feed": "https://deepseekoracle.github.io/lygo-protocol-stack/haven_star_chart/haven_star_chart_feed.json",
    },
    "skill_chain": [
        "lygo-protocol-stack-operator",
        "lygo-network-builder",
        "lygo-sovereign-super-skill",
        "lygo-haven-star-chart",
    ],
}


def main() -> int:
    print(json.dumps(FLOW, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())