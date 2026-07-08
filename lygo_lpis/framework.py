"""LPIS orchestration pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from .analyzer import PromptAnalyzer
from .anchor import KernelEggAnchor
from .engine import PromptEngine
from .harmony import P5HarmonyNode
from .vault import PromptVault


class LYGPromptImplantSystem:
    def __init__(self, vault: Optional[Path] = None):
        self.vault = PromptVault(vault)
        self.analyzer = PromptAnalyzer()
        self.engine = PromptEngine()
        self.harmony = P5HarmonyNode()
        self.anchor = KernelEggAnchor()

    def ingest(self, source: str, **kwargs: Any) -> dict[str, Any]:
        out = self.vault.ingest(source, **kwargs)
        if not out.get("ok"):
            return out
        rec = self.vault.load(out["prompt_id"])
        assert rec and rec.get("content")
        analysis = self.analyzer.analyze(rec["content"])
        if analysis["p0"].get("verdict") == "QUARANTINE":
            return {"ok": False, "error": "p0_quarantine", "p0": analysis["p0"]}
        return {"ok": True, "ingest": out, "analysis": analysis}

    def analyze_id(self, prompt_id: str) -> dict[str, Any]:
        rec = self.vault.load(prompt_id)
        if not rec or not rec.get("content"):
            return {"ok": False, "error": "not_found"}
        return {"ok": True, "prompt_id": prompt_id, "analysis": self.analyzer.analyze(rec["content"])}

    def generate(self, prompt_id: str, target: str = "grok", layers: list[str] | None = None) -> dict[str, Any]:
        rec = self.vault.load(prompt_id)
        if not rec or not rec.get("content"):
            return {"ok": False, "error": "not_found"}
        variant = self.engine.generate(
            rec["content"], target_model=target, layers=layers, base_id=prompt_id
        )
        out_path = self.vault.root / f"{variant['variant_id']}.json"
        out_path.write_text(__import__("json").dumps(variant, indent=2), encoding="utf-8")
        return {"ok": True, "variant": variant}

    def implant(self, variant_id: str, target: str) -> dict[str, Any]:
        path = self.vault.root / f"{variant_id}.json"
        if not path.is_file():
            return {"ok": False, "error": "variant_not_found"}
        import json

        variant = json.loads(path.read_text(encoding="utf-8"))
        ident = self.harmony.create_implant(variant_id, target)
        receipt = {
            "mode": "advisory",
            "variant_id": variant_id,
            "target": target,
            "light_code": ident["light_code"],
            "note": "Apply via Grok project instructions / agent SKILL — no auto API injection.",
            "variant_path": str(path),
        }
        anchor_info = self.anchor.anchor({**receipt, "prompt_id": variant_id, "target": target})
        return {"ok": True, "implant": receipt, "anchor": anchor_info}

    def anchor_prompt(self, prompt_id: str, performance: dict[str, Any] | None = None) -> dict[str, Any]:
        rec = self.vault.load(prompt_id)
        if not rec:
            return {"ok": False, "error": "not_found"}
        payload = {"prompt_id": prompt_id, "sha256": rec.get("sha256"), "performance": performance or {}}
        return {"ok": True, "anchor": self.anchor.anchor(payload)}


def run_pipeline(cmd: str, **kwargs: Any) -> dict[str, Any]:
    lpis = LYGPromptImplantSystem()
    if cmd == "ingest":
        return lpis.ingest(kwargs["source"], file_path=kwargs.get("file_path"), url=kwargs.get("url"))
    if cmd == "analyze":
        return lpis.analyze_id(kwargs["prompt_id"])
    if cmd == "generate":
        return lpis.generate(kwargs["prompt_id"], target=kwargs.get("target", "grok"), layers=kwargs.get("layers"))
    if cmd == "implant":
        return lpis.implant(kwargs["variant_id"], kwargs["target"])
    if cmd == "anchor":
        return lpis.anchor_prompt(kwargs["prompt_id"])
    return {"ok": False, "error": "unknown_command"}