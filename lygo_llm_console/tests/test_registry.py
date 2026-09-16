from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class RegistryTests(unittest.TestCase):
    def test_upsert_roundtrip(self):
        import paths
        import registry

        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            with mock.patch.object(paths, "SAVE", t), mock.patch.object(registry, "REGISTRY_PATH", t / "registry.json"), mock.patch.object(paths, "REGISTRY_PATH", t / "registry.json"):
                import importlib
                importlib.reload(registry)
                data = registry.upsert([{"id": "tiny", "kind": "chat", "runnable": True}], selected="tiny")
                self.assertEqual(data["selected"], "tiny")
                self.assertEqual(registry.get("tiny")["kind"], "chat")

    def test_prefer_qwen(self):
        import importlib
        import paths
        import registry
        from unittest import mock
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            with mock.patch.object(paths, "SAVE", t), mock.patch.object(registry, "REGISTRY_PATH", t / "registry.json"), mock.patch.object(paths, "REGISTRY_PATH", t / "registry.json"):
                importlib.reload(registry)
                data = registry.upsert(
                    [
                        {"id": "deepseek-r1:14b", "kind": "chat", "runnable": True, "bytes": 9_000_000_000},
                        {"id": "qwen2.5:3b", "kind": "chat", "runnable": True, "bytes": 1_900_000_000},
                    ]
                )
                self.assertEqual(data["selected"], "qwen2.5:3b")


if __name__ == "__main__":
    unittest.main()
