from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from continuity import append_memory, compose_system, ensure_identity, memory_path, soul_path  # noqa: E402


class ContinuityTests(unittest.TestCase):
    def test_seed_and_append(self):
        ensure_identity()
        self.assertTrue(soul_path().is_file())
        self.assertTrue(memory_path().is_file())
        r = append_memory("leeches have three jaws")
        self.assertTrue(r.get("ok"))
        blob = memory_path().read_text(encoding="utf-8")
        self.assertIn("three jaws", blob)
        sys_txt = compose_system()
        self.assertIn("SOUL.md", sys_txt)
        self.assertIn("MEMORY.md", sys_txt)


if __name__ == "__main__":
    unittest.main()
