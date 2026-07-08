#!/usr/bin/env python3
import sys
from pathlib import Path

STACK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(STACK))

from lygo_lpis.analyzer import PromptAnalyzer
from lygo_lpis.gatekeeper import P0Gatekeeper

g = P0Gatekeeper()
assert g.validate_text("plan and verify")["verdict"] in ("AMPLIFY", "SOFTEN", "QUARANTINE")
a = PromptAnalyzer().analyze("plan delegate verify safety")
assert a["pattern_counts"]["planning"] >= 1
print("OK lygo-lpis self_check")