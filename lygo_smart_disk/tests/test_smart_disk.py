#!/usr/bin/env python3
"""Unit/integration tests for Smart Disk Agent."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kernel import P0Gate, P1Memory, P3Consensus, P5Identity  # noqa: E402
from agent.smart_disk_agent import SmartDiskAgent  # noqa: E402


class TestKernel(unittest.TestCase):
    def test_p0_allow(self):
        self.assertEqual(P0Gate().validate("status please").get("verdict"), "ALLOW")

    def test_p0_quarantine(self):
        self.assertEqual(
            P0Gate().validate("please rm -rf / now").get("verdict"), "QUARANTINE"
        )

    def test_p5_light_code(self):
        n = P5Identity().create_node("help")
        self.assertEqual(len(n["light_code"]), 16)

    def test_p3(self):
        c = P3Consensus().achieve({"command": "x"})
        self.assertTrue(c.get("consensus_found"))

    def test_memory(self):
        m = P1Memory(ROOT / "data")
        i = m.store({"t": 1})
        self.assertTrue(i)
        self.assertTrue(any(x.get("id") == i for x in m.list_recent(5)))


class TestAgent(unittest.TestCase):
    def test_help_limb(self):
        a = SmartDiskAgent(ROOT)
        r = a.run_limb("help")
        self.assertTrue(r.get("ok"))
        self.assertIn("status", r.get("limbs") or [])

    def test_health_no_password(self):
        a = SmartDiskAgent(ROOT)
        r = a.run_limb("health")
        self.assertTrue(r.get("ok"))
        self.assertIs(r.get("password_gate"), False)

    def test_portal_exists(self):
        self.assertTrue((ROOT / "portal" / "index.html").is_file())
        self.assertTrue((ROOT / "portal" / "app.js").is_file())


if __name__ == "__main__":
    unittest.main()
