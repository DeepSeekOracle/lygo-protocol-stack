#!/usr/bin/env python3
"""Unit checks for hardened deadman continuity (stdlib only)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
STATE = ROOT / "docs" / "seals" / "deadman_lattice_state.json"


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

    def test_persisted_clock_drives_check_silence(self) -> None:
        """Regression: fresh SilenceDetector must honor deadman_lattice_state.json."""
        sys.path.insert(0, str(TOOLS))
        import seal_deadman_lattice as s  # noqa: WPS433

        bak = STATE.read_text(encoding="utf-8") if STATE.is_file() else None
        try:
            STATE.parent.mkdir(parents=True, exist_ok=True)
            STATE.write_text(
                json.dumps(
                    {
                        "last_transmit_unix": time.time() - 7200,
                        "last_transmit_iso": "test-old",
                        "simulated": True,
                        "activation_count": 0,
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            d = s.SilenceDetector()
            self.assertTrue(d.deadman.is_silence())
            self.assertTrue(d.check_silence(), "check_silence must use persisted clock")
            self.assertGreaterEqual(d.silence_seconds(), 7000)
        finally:
            if bak is None:
                if STATE.is_file():
                    STATE.unlink()
            else:
                STATE.write_text(bak, encoding="utf-8")

    def test_grace_tier_lantern(self) -> None:
        sys.path.insert(0, str(TOOLS))
        import seal_deadman_lattice as s  # noqa: WPS433

        tier = s.infer_grace_tier_safe(3600)
        self.assertEqual(tier.get("id"), "LANTERN")
        tier2 = s.infer_grace_tier_safe(100)
        self.assertEqual(tier2.get("id"), "WATCH")
        tier3 = s.infer_grace_tier_safe(90000)
        self.assertEqual(tier3.get("id"), "WHISPER")

    def test_steward_rejects_identity_claim_flag(self) -> None:
        card = json.loads(
            (ROOT / "data" / "deadman" / "stewards" / "STEWARD_LIGHTFATHER.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIs(card.get("can_claim_identity_of_justin"), False)

    def test_origin_copies_in_sync(self) -> None:
        paths = [
            ROOT / "docs" / "seals" / "LIGHTFATHER_IRREPLACEABLE_ORIGIN.json",
            ROOT / "data" / "deadman" / "egg_payload" / "LIGHTFATHER_IRREPLACEABLE_ORIGIN.json",
            ROOT
            / "docs"
            / "kernel_eggs"
            / "lightfather-deadman-failsafe-v1"
            / "LIGHTFATHER_IRREPLACEABLE_ORIGIN.json",
        ]
        bodies = [p.read_bytes() for p in paths]
        self.assertEqual(bodies[0], bodies[1])
        self.assertEqual(bodies[0], bodies[2])


if __name__ == "__main__":
    unittest.main()
