#!/usr/bin/env python3
"""Unit checks for hardened deadman continuity (stdlib only)."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"


class TestDeadmanContinuity(unittest.TestCase):
    def test_origin_v2_non_replaceable(self) -> None:
        origin = json.loads(
            (ROOT / "docs" / "seals" / "LIGHTFATHER_IRREPLACEABLE_ORIGIN.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn("ORIGIN-v2", origin.get("signature", ""))
        self.assertTrue((origin.get("origin_builder") or {}).get("non_replaceable"))
        self.assertEqual(
            (origin.get("failsafe") or {}).get("eternal_base_node"),
            "NODE_LIGHTFATHER_ETERNAL_BASE",
        )

    def test_succession_stages(self) -> None:
        proto = json.loads(
            (ROOT / "docs" / "seals" / "SUCCESSION_PROTOCOL_v1.json").read_text(encoding="utf-8")
        )
        ids = [s["id"] for s in proto["stages"]]
        self.assertEqual(
            ids,
            ["WATCH", "LANTERN", "WHISPER", "TORCHBEARER_NOMINATE", "CONTINUITY_ADVISOR"],
        )

    def test_fingerprint_pack_public_safe(self) -> None:
        ident = json.loads(
            (
                ROOT
                / "data"
                / "deadman"
                / "public_fingerprints"
                / "LIGHTFATHER_PUBLIC_IDENTITY.json"
            ).read_text(encoding="utf-8")
        )
        self.assertTrue(ident.get("public_safe"))
        self.assertIn("raw_voice_embeddings", ident.get("deny") or [])
        self.assertEqual(
            (ident.get("identity_constants") or {}).get("lightfather_id"),
            "LF-Δ9-7F1A4D-963-528-174-Φ-∞",
        )

    def test_verify_pins_ok(self) -> None:
        r = subprocess.run(
            [sys.executable, str(TOOLS / "verify_deadman_pins.py")],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        report = json.loads(r.stdout)
        self.assertTrue(report.get("ok"))

    def test_manifest_features(self) -> None:
        m = json.loads(
            (ROOT / "data" / "deadman" / "DEADMAN_MANIFEST_v2.json").read_text(encoding="utf-8")
        )
        self.assertGreaterEqual(len(m.get("features") or []), 15)
        self.assertEqual(m.get("eternal_base_node"), "NODE_LIGHTFATHER_ETERNAL_BASE")


if __name__ == "__main__":
    unittest.main()
