"""LYGOOpenClaw sovereign run pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from .anchor import KernelEggAnchor
from .consensus import P3VortexConsensus
from .gatekeeper import P0Gatekeeper
from .harmony import P5HarmonyNode
from .limbs import dispatch
from .memory import P1MemoryMycelium

SIGNATURE = "D9F963-OPENCLAW-SOVEREIGN-v1.0"


class LYGOOpenClaw:
    def __init__(
        self,
        config_path: Optional[Path] = None,
        mycelium: Optional[Path] = None,
    ):
        self.gatekeeper = P0Gatekeeper()
        self.memory = P1MemoryMycelium(mycelium)
        self.consensus = P3VortexConsensus()
        self.harmony = P5HarmonyNode()
        self.anchor = KernelEggAnchor()
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: Optional[Path]) -> dict[str, Any]:
        if config_path and config_path.is_file():
            return json.loads(config_path.read_text(encoding="utf-8"))
        default = Path(__file__).parent / "config" / "default.json"
        if default.is_file():
            return json.loads(default.read_text(encoding="utf-8"))
        return {"multi_agent": False, "anchor": True}

    def run(
        self,
        command: str,
        args: list[str] | None = None,
        *,
        skip_anchor: bool = False,
    ) -> dict[str, Any]:
        args = args or []
        node = self.harmony.create_node(command, args)
        validation = self.gatekeeper.validate(command + " " + " ".join(args))
        if validation.get("verdict") == "QUARANTINE":
            return {
                "error": "command_quarantined",
                "reason": validation.get("reasoning") or validation.get("reason"),
                "node_id": node.get("light_code"),
                "verdict": "QUARANTINE",
            }

        result = dispatch(command, args)
        bundle = {
            "signature": SIGNATURE,
            "command": command,
            "args": args,
            "node_id": node.get("light_code"),
            "verdict": validation.get("verdict"),
            "ethical_mass": node.get("ethical_mass"),
            "result": result,
        }

        if self.config.get("multi_agent"):
            consensus = self.consensus.achieve_consensus(bundle)
            bundle["consensus"] = consensus
            if not consensus.get("consensus_found"):
                return {"error": "no_consensus", "consensus": consensus, "node_id": node.get("light_code")}

        memory_id = self.memory.store(bundle)
        bundle["memory_id"] = memory_id
        anchor_info = self.anchor.anchor(bundle, enabled=self.config.get("anchor", True) and not skip_anchor)
        return {
            "ok": True,
            "result": result,
            "node_id": node.get("light_code"),
            "memory_id": memory_id,
            "anchor": anchor_info,
            "verdict": validation.get("verdict"),
            "ethical_mass": node.get("ethical_mass"),
        }


def run_command(command: str, args: list[str] | None = None, **kwargs: Any) -> dict[str, Any]:
    return LYGOOpenClaw().run(command, args, **kwargs)