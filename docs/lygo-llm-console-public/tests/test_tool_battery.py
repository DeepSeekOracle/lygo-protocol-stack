from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tools import core_schema, dispatch  # noqa: E402


class ToolBattery(unittest.TestCase):
    def test_core_schema_small(self):
        names = {(t.get("function") or {}).get("name") for t in core_schema()}
        self.assertIn("steward_map", names)
        self.assertIn("self_check", names)
        self.assertIn("web_fetch", names)
        self.assertLessEqual(len(names), 24)

    def test_dispatch_core(self):
        checks = [
            ("steward_map", {}),
            ("self_check", {}),
            ("whoami", {}),
            ("kernel_status", {}),
            ("now", {}),
            ("calc", {"expr": "2+2"}),
            ("hash_text", {"text": "lygo"}),
            ("list_dir", {"path": ""}),
            ("workspace_map", {}),
            ("skill_list", {}),
        ]
        for name, args in checks:
            r = dispatch(name, args)
            self.assertTrue(r.get("ok"), f"{name} {r}")

    def test_placeholder_blocked(self):
        r = dispatch("web_fetch", {"url": "https://github.com/user/repo"})
        self.assertEqual(r.get("error"), "placeholder_url")


if __name__ == "__main__":
    unittest.main()
