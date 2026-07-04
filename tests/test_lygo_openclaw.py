from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_p0_gatekeeper() -> None:
    from lygo_openclaw.gatekeeper import P0Gatekeeper

    g = P0Gatekeeper()
    out = g.validate("status")
    assert out["verdict"] in ("AMPLIFY", "SOFTEN", "QUARANTINE")


def test_p5_harmony() -> None:
    from lygo_openclaw.harmony import P5HarmonyNode

    ident = P5HarmonyNode().create_node("test", ["a"])
    assert ident["light_code"].startswith("LF-")
    assert "ethical_mass" in ident


def test_p1_memory_roundtrip(tmp_path: Path) -> None:
    from lygo_openclaw.memory import P1MemoryMycelium

    mem = P1MemoryMycelium(tmp_path)
    mid = mem.store({"test": "openclaw"})
    assert mem.recall(mid) == {"test": "openclaw"}


def test_run_help_pipeline(tmp_path: Path) -> None:
    from lygo_openclaw.framework import LYGOOpenClaw

    oc = LYGOOpenClaw(mycelium=tmp_path)
    out = oc.run("help", skip_anchor=True)
    assert out.get("ok") is True
    assert out.get("result", {}).get("limbs")


def test_limb_dispatch_status() -> None:
    from lygo_openclaw.limbs import dispatch

    st = dispatch("status")
    assert "stack_root" in st
