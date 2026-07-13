from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_analyzer_patterns() -> None:
    from lygo_lpis.analyzer import PromptAnalyzer

    out = PromptAnalyzer().analyze("plan the task and verify with tests; delegate to subagent")
    assert out["pattern_counts"]["planning"] >= 1
    assert out["p0"]["verdict"] in ("AMPLIFY", "SOFTEN", "QUARANTINE")


def test_vault_ingest_roundtrip(tmp_path: Path) -> None:
    from lygo_lpis.vault import PromptVault

    sample = tmp_path / "sample.txt"
    sample.write_text("delegate and verify safety rules", encoding="utf-8")
    v = PromptVault(tmp_path / "vault")
    ing = v.ingest("test", file_path=sample)
    assert ing["ok"]
    rec = v.load(ing["prompt_id"])
    assert rec and "delegate" in rec.get("content", "")


def test_ingest_requires_authorization(tmp_path: Path) -> None:
    from lygo_lpis.framework import LYGPromptImplantSystem

    lpis = LYGPromptImplantSystem(vault=tmp_path / "vault")
    sample = tmp_path / "p.txt"
    sample.write_text("plan execute verify", encoding="utf-8")
    blocked = lpis.ingest("t", file_path=sample)
    assert not blocked["ok"]
    assert blocked["error"] == "ingest_not_authorized"


def test_generate_variant(tmp_path: Path) -> None:
    from lygo_lpis.framework import LYGPromptImplantSystem

    lpis = LYGPromptImplantSystem(vault=tmp_path / "vault")
    sample = tmp_path / "p.txt"
    sample.write_text("plan execute verify", encoding="utf-8")
    ing = lpis.ingest("t", file_path=sample, authorized=True)
    assert ing["ok"]
    gen = lpis.generate(ing["ingest"]["prompt_id"], target="grok")
    assert gen["ok"]
    assert gen["variant"]["variant_id"].startswith("sovereign_")