"""
LYGO Sovereign Workflow Orchestrator (Sandcastle-aligned).

P0 gate · P1 mycelium manifests · P3 consensus · P5 run identity · optional Kernel Egg ledger.
Optional upstream: sandcastle-ai when installed; otherwise local dry-run executor.
"""

from __future__ import annotations

from .orchestrator import LYGOWorkflowOrchestrator, run_workflow_yaml

__version__ = "1.0.0"
__lygo_signature__ = "Δ9Φ963-SANDCASTLE-SOVEREIGN-v1.0"

__all__ = ["LYGOWorkflowOrchestrator", "run_workflow_yaml", "__version__", "__lygo_signature__"]