"""The console must be standalone: own engine, own model vault, no daemon anywhere.

The steward's rule for this kit is a zero-Ollama system - our own backend services and
infrastructure. Ollama's blob folder may still be *imported* once (read-only) by
src/ollama_import.py, but nothing may require it, scan it implicitly, or talk to a daemon.

These tests pin that contract so a later edit cannot quietly put the dependency back:
  1. no source file subprocesses anything called ollama,
  2. the public gateway defaults to our own engine, not a daemon,
  3. scan roots do not silently include %USERPROFILE%\\.ollama\\models,
  4. the shipped config does not list an Ollama path,
  5. the declared vault (LYGO_MODELS) is honoured,
  6. a model record the kit owns points at a file the kit owns.
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import public_gateway  # noqa: E402
import server  # noqa: E402

VAULT = Path(r"I:\LYGO_MODELS")


class NoDaemonTests(unittest.TestCase):
    def test_nothing_subprocesses_ollama(self) -> None:
        bad = []
        for path in (ROOT / "src").glob("*.py"):
            text = path.read_text(encoding="utf-8", errors="replace")
            for m in re.finditer(r"^.*subprocess.*ollama.*$", text, re.I | re.M):
                if "Never subprocess" in m.group(0):      # the importer's own contract comment
                    continue
                bad.append("%s: %s" % (path.name, m.group(0).strip()[:80]))
        self.assertEqual([], bad, "the kit must never launch a daemon")

    def test_the_importer_says_it_is_read_only(self) -> None:
        text = (ROOT / "src" / "ollama_import.py").read_text(encoding="utf-8")
        self.assertIn("Never subprocess ollama", text)

    def test_the_public_gateway_defaults_to_our_own_engine(self) -> None:
        self.assertEqual("local", public_gateway.Handler.backend)
        self.assertIn(str(public_gateway.LLAMA_PORT), public_gateway.Handler.openai_url)

    def test_the_gateway_model_default_comes_from_our_own_registry(self) -> None:
        self.assertTrue(public_gateway._selected_model())


class ScanRootTests(unittest.TestCase):
    def test_a_clean_pc_needs_no_ollama_folder(self) -> None:
        """Simulate a machine that never ran ollama: the kit still finds a usable root."""
        with tempfile.TemporaryDirectory() as td:
            fake_home = Path(td) / "home"
            fake_home.mkdir()
            with mock.patch.dict(os.environ, {"USERPROFILE": str(fake_home)}, clear=False):
                roots = server.default_scan_roots({})
        self.assertIn(str(server.KIT_ROOT / "models"), roots)

    def test_the_home_ollama_folder_is_not_scanned_implicitly(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            home_cas = Path(td) / ".ollama" / "models"
            (home_cas / "blobs").mkdir(parents=True)
            with mock.patch.dict(os.environ, {"USERPROFILE": td}, clear=False):
                os.environ.pop("OLLAMA_MODELS", None)
                roots = server.default_scan_roots({})
        self.assertNotIn(str(home_cas), roots,
                         "an Ollama folder must only be scanned when the operator maps it")

    def test_the_declared_vault_is_honoured(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.dict(os.environ, {"LYGO_MODELS": td}, clear=False):
                roots = server.default_scan_roots({})
        self.assertIn(str(Path(td)), roots)

    def test_the_shipped_config_lists_no_ollama_path(self) -> None:
        cfg = json.loads((ROOT / "config" / "console.json").read_text(encoding="utf-8"))
        joined = " ".join(str(x) for x in (cfg.get("scan_roots") or []))
        self.assertNotIn("ollama", joined.lower())


@unittest.skipUnless(VAULT.is_dir(), "no LYGO_MODELS vault on this machine")
class VaultTests(unittest.TestCase):
    def test_the_declared_vault_is_a_scan_candidate(self) -> None:
        roots = server.default_scan_roots({})
        self.assertIn(str(VAULT), roots)

    def test_models_the_kit_owns_live_in_a_root_the_kit_scans(self) -> None:
        """An owned model must sit in a folder THIS kit scans.

        'The vault' is `I:\\LYGO_MODELS` on the PC and the stick's own CAS (`product\\models\\ollama`)
        on the USB, so the contract has to be 'a declared scan root', not one hard-coded drive:
        pinning `I:` here failed the stick while the stick was right. Records whose file cannot be
        found are skipped - other tests patch the registry and leave temp paths behind that are gone
        by the time this runs.
        """
        roots = [Path(r) for r in server.default_scan_roots({})]
        reg = json.loads((ROOT / "save" / "registry.json").read_text(encoding="utf-8"))
        owned = [r for r in (reg.get("models") or []) if str(r.get("source")) == "lygo_vault"]
        if not owned:
            # A tree whose models were imported by the CAS reader (the USB kit) has none: its own CAS
            # is the vault. Nothing to validate here is a skip, not a failure.
            self.skipTest("no lygo_vault records on this machine - its models come from its own CAS")
        checked = 0
        for rec in owned:
            for key in ("path", "mmproj"):
                value = str(rec.get(key) or "")
                if not value or not Path(value).is_file():
                    continue
                checked += 1
                self.assertTrue(any(value.lower().startswith(str(r).lower()) for r in roots),
                                "%s %s is outside every model root this kit scans: %s"
                                % (rec.get("id"), key, value))
        if not checked:
            self.skipTest("owned records exist but none of their files are on disk any more")

    def test_the_vault_manifest_points_at_files_it_owns(self) -> None:
        manifest = VAULT / "manifest.json"
        if not manifest.is_file():
            self.skipTest("no vault manifest on this machine")
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertTrue(data, "the vault holds no models")
        for mid, entry in data.items():
            for key in ("path", "mmproj"):
                value = entry.get(key)
                if not value:
                    continue
                self.assertTrue(str(value).lower().startswith(str(VAULT).lower()),
                                "vault manifest %s %s is outside the vault: %s" % (mid, key, value))
                self.assertTrue(Path(str(value)).is_file(), "vault manifest %s is missing" % value)

    def test_a_vision_model_is_registered_with_its_projector(self) -> None:
        """The registry carries a projector for a real multimodal model: pick one that still exists."""
        import image_tools

        rec = image_tools.vision_record()
        if rec is None:
            self.skipTest("this tree has no multimodal model registered")
        self.assertTrue(Path(str(rec["mmproj"])).is_file())
        self.assertTrue(Path(str(rec["path"])).is_file())


if __name__ == "__main__":
    unittest.main()
