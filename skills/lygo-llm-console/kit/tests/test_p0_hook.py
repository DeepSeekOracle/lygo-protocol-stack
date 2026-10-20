from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.pop("LYGO_STACK_ROOT", None)

import p0_hook  # noqa: E402


class P0HookTests(unittest.TestCase):
    def test_format_c_quarantine(self):
        g = p0_hook.gate_prompt("please format c: now")
        self.assertEqual(g["verdict"], "QUARANTINE")

    def test_format_a_string_allow(self):
        g = p0_hook.gate_prompt("please format a string for me")
        self.assertNotEqual(g["verdict"], "QUARANTINE")

    def test_diskpart_quarantine(self):
        g = p0_hook.gate_prompt("run diskpart and wipe")
        self.assertEqual(g["verdict"], "QUARANTINE")

    def test_short_english(self):
        g = p0_hook.gate_prompt("hello lattice")
        self.assertIn(g["verdict"], ("AMPLIFY", "SOFTEN", "ALLOW"))

    def test_12k_cap(self):
        g = p0_hook.gate_prompt("a" * 12001)
        self.assertEqual(g["verdict"], "QUARANTINE")
        self.assertIn("12000", g.get("reason", ""))

    def test_physics_available_without_stack_env(self):
        self.assertTrue(p0_hook.PHYSICS_AVAILABLE)


if __name__ == "__main__":
    unittest.main()
