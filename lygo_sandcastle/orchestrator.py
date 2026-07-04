"""LYGO Sovereign Workflow Orchestrator — main run pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import yaml

from .anchor import KernelEggAnchor
from .consensus import P3VortexConsensus
from .executor import execute_workflow, run_ollama_step
from .gatekeeper import P0Gatekeeper
from .harmony import P5HarmonyNode
from .memory import P1MemoryMycelium

SIGNATURE = "Δ9Φ963-SANDCASTLE-SOVEREIGN-v1.0"


class LYGOWorkflowOrchestrator:
    def __init__(self, config_path: Optional[Path] = None, mycelium: Optional[Path] = None):
        self.gatekeeper = P0Gatekeeper()
        self.memory = P1MemoryMycelium(mycelium)
        self.consensus = P3VortexConsensus()
        self.harmony = P5HarmonyNode()
        self.anchor = KernelEggAnchor()
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: Optional[Path]) -> dict[str, Any]:
        if config_path and config_path.is_file():
            return yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        return {}

    def run(self, workflow_yaml: str, *, skip_anchor: bool = False) -> dict[str, Any]:
        workflow = yaml.safe_load(workflow_yaml)
        if not isinstance(workflow, dict):
            return {"error": "invalid_yaml", "detail": "root must be a mapping"}

        lygo_cfg = workflow.get("lygo") or {}
        node_identity = self.harmony.create_node(workflow)
        validation = self.gatekeeper.validate(workflow_yaml)
        if validation.get("verdict") == "QUARANTINE":
            return {
                "error": "workflow_quarantined",
                "reason": validation.get("reasoning") or validation.get("reason"),
                "node_id": node_identity.get("light_code"),
                "verdict": "QUARANTINE",
            }

        threshold = float(lygo_cfg.get("ethical_mass_threshold", 0.0))
        if node_identity.get("ethical_mass", 0) < threshold:
            return {
                "error": "ethical_mass_below_threshold",
                "ethical_mass": node_identity.get("ethical_mass"),
                "threshold": threshold,
                "node_id": node_identity.get("light_code"),
            }

        exec_result = execute_workflow(workflow)
        if workflow.get("local_ollama") and workflow.get("prompt"):
            exec_result["ollama"] = run_ollama_step(
                str(workflow["prompt"]),
                model=str(workflow.get("model") or "llama3.2:1b"),
            )

        bundle = {
            "signature": SIGNATURE,
            "workflow_name": workflow.get("name"),
            "node_id": node_identity.get("light_code"),
            "verdict": validation.get("verdict"),
            "execution": exec_result,
            "ethical_mass": node_identity.get("ethical_mass"),
        }

        multi = workflow.get("multi_agent") or lygo_cfg.get("consensus") or self.config.get("multi_agent")
        if multi:
            consensus = self.consensus.achieve_consensus(workflow)
            bundle["consensus"] = consensus
            if not consensus.get("consensus_found"):
                return {
                    "error": "no_consensus",
                    "consensus": consensus,
                    "node_id": node_identity.get("light_code"),
                }

        memory_id = self.memory.store(bundle)
        bundle["memory_id"] = memory_id

        anchor_on = lygo_cfg.get("anchor", True) and not skip_anchor
        anchor_info = self.anchor.anchor(bundle, enabled=anchor_on)
        bundle["anchor"] = anchor_info

        return {
            "ok": True,
            "result": exec_result,
            "node_id": node_identity.get("light_code"),
            "memory_id": memory_id,
            "anchor": anchor_info,
            "verdict": validation.get("verdict"),
            "ethical_mass": node_identity.get("ethical_mass"),
        }


def run_workflow_yaml(workflow_yaml: str, **kwargs: Any) -> dict[str, Any]:
    return LYGOWorkflowOrchestrator().run(workflow_yaml, **kwargs)