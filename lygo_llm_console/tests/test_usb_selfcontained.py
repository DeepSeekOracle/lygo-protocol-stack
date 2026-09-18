"""The stick must find its OWN model store on a PC that has never run ollama.

Verified by simulation: with %USERPROFILE% pointing at an empty folder (a foreign PC) and
LYGO_USB_ROOT set the way the launcher sets it, these roots are what decide whether the console
sees its own brains or reports brain=missing with the models sitting unused on the stick.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import server  # noqa: E402

STICK_CAS = Path(r"E:/LYGO_BUILDER_KEY/product/models/ollama")


class ScanRootTests(unittest.TestCase):
    def test_the_declared_stick_model_folder_is_always_scanned(self) -> None:
        """LYGO_MODELS is set by the launchers: ignoring it means booting empty on a clean PC."""
        with tempfile.TemporaryDirectory() as td:
            cas = Path(td) / "product" / "models" / "ollama"
            (cas / "manifests").mkdir(parents=True)
            (cas / "blobs").mkdir()
            with mock.patch.dict(os.environ, {"LYGO_MODELS": str(cas)}, clear=False):
                roots = server.default_scan_roots({})
            self.assertIn(str(cas), roots)

    def test_a_declared_parent_folder_is_descended_to_the_cas(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cas = Path(td) / "models" / "ollama"
            (cas / "manifests").mkdir(parents=True)
            (cas / "blobs").mkdir()
            with mock.patch.dict(os.environ, {"OLLAMA_MODELS": str(Path(td) / "models")}, clear=False):
                roots = server.default_scan_roots({})
            self.assertIn(str(cas), roots)

    def test_the_kits_own_models_folder_survives_a_stale_config(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            roots = server.default_scan_roots({"scan_roots": [str(Path(td) / "does-not-exist")]})
        self.assertIn(str(server.KIT_ROOT / "models"), roots)

    def test_usb_root_extras_still_work(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "models").mkdir()
            (Path(td) / "product" / "models" / "ollama").mkdir(parents=True)
            with mock.patch.dict(os.environ, {"LYGO_USB_ROOT": td}, clear=False):
                roots = server.default_scan_roots({})
            self.assertIn(str(Path(td) / "models"), roots)
            self.assertIn(str(Path(td) / "product" / "models" / "ollama"), roots)

    @unittest.skipUnless(STICK_CAS.is_dir(), "real stick CAS not attached on this machine")
    def test_the_real_stick_cas_is_scanned_and_yields_models(self) -> None:
        import scanner

        with mock.patch.dict(os.environ, {"LYGO_USB_ROOT": r"E:/LYGO_BUILDER_KEY"}, clear=False):
            roots = server.default_scan_roots({})
        self.assertIn(str(STICK_CAS), roots)
        found = {str(m.get("id")) for m in (scanner.scan_roots([str(STICK_CAS)], wall_s=20.0).get("models") or [])}
        self.assertTrue(found, "the stick's own CAS must yield at least one model")


if __name__ == "__main__":
    unittest.main()
