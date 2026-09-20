"""A model the kit cannot hold must not be offered as if it could.

Measured on the USB stick 2026-09-19: 8 of its 14 registry records named files in this PC's home
Ollama store and even `D:\\Ollama` - the only vision model among them. `/api/models` handed those
records to the picker unexamined, so the stick advertised models it does not carry, and a photo
attached to one of them could not be looked at.

Two different questions, asked separately:

  * `reachable` - the files exist on this machine (a fact about now)
  * `portable`  - they sit in storage this kit carries (a fact about the road)

and one honest sentence when a picture is attached to a model that has no projector, so the operator
is never left believing a photo was considered when only the text was read.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import registry  # noqa: E402


def _src(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="replace")


class ReachTests(unittest.TestCase):
    def test_storage_roots_include_the_kit_itself(self):
        roots = [str(r).lower() for r in registry.kit_storage_roots()]
        self.assertTrue(any(str(ROOT).lower().startswith(r) for r in roots),
                        "the kit folder is storage the kit carries")

    def test_a_file_the_kit_carries_is_portable(self):
        inside = ROOT / "NOTICE"
        self.assertTrue(inside.is_file(), "NOTICE ships in the kit root")
        got = registry.reach({"id": "x", "path": str(inside)})
        self.assertTrue(got["reachable"] and got["portable"], got)
        self.assertIsNone(got["why"])

    def test_a_file_on_another_drive_is_reachable_but_not_portable(self):
        """The case the stick actually hit: the file is here *today* because the stick is plugged into
        this PC, and it is gone on the next machine."""
        kit_drive = Path(ROOT).drive.lower()
        other = next((d for d in ("C:\\", "D:\\", "F:\\") if d.lower() != kit_drive), "C:\\")
        with tempfile.NamedTemporaryFile(suffix=".gguf", delete=False) as fh:
            fh.write(b"GGUF")
            tmp = fh.name
        try:
            if Path(tmp).drive.lower() == kit_drive:
                self.skipTest("temp dir is on the kit's own drive")
            got = registry.reach({"id": "x", "path": tmp})
            self.assertTrue(got["reachable"], got)
            self.assertFalse(got["portable"], got)
            self.assertIn("not inside this kit", got["why"])
        finally:
            os.unlink(tmp)

    def test_a_vault_on_the_kits_own_drive_is_carried(self):
        """Same rule, two answers: the PC's vault is on the kit's drive and counts as carried; a stick
        whose kit sits on E: must not call that same vault its own."""
        roots = " ".join(str(r).lower() for r in registry.kit_storage_roots())
        kit_drive = Path(ROOT).drive.lower()
        same = [p for p in registry.KNOWN_VAULTS if Path(p).drive.lower() == kit_drive]
        if not same:
            self.skipTest("this kit is not installed on a vault drive")
        for p in same:
            self.assertIn(Path(p).drive.lower(), roots, "%s is on the kit's own drive" % p)

    def test_a_gone_file_is_not_reachable_and_says_which(self):
        got = registry.reach({"id": "x", "path": str(ROOT / "no_such_model_9f3.gguf")})
        self.assertFalse(got["reachable"])
        self.assertIn("not on this machine", got["why"])

    def test_a_missing_projector_counts_as_unreachable(self):
        """A record whose mmproj is gone cannot look at a picture, so it is not usable for vision."""
        got = registry.reach({"id": "x", "path": str(ROOT / "NOTICE"), "mmproj": str(ROOT / "no_such_mmproj.gguf")})
        self.assertFalse(got["reachable"])
        self.assertEqual(len(got["missing"]), 1)


class SelectedVisionTests(unittest.TestCase):
    def _with_registry(self, payload: dict):
        old = registry.REGISTRY_PATH
        tmp = Path(tempfile.mkdtemp()) / "registry.json"
        tmp.write_text(json.dumps(payload), encoding="utf-8")
        registry.REGISTRY_PATH = tmp
        try:
            return registry.selected_vision()
        finally:
            registry.REGISTRY_PATH = old

    def test_a_model_without_a_projector_cannot_see(self):
        self.assertFalse(self._with_registry({"selected": "a", "models": [{"id": "a", "path": str(ROOT / "NOTICE")}]}))

    def test_a_model_with_a_real_projector_can(self):
        self.assertTrue(
            self._with_registry({"selected": "a", "models": [{"id": "a", "path": str(ROOT / "NOTICE"),
                                                              "mmproj": str(ROOT / "NOTICE")}]})
        )

    def test_a_projector_that_is_not_here_does_not_count(self):
        self.assertFalse(
            self._with_registry({"selected": "a", "models": [{"id": "a", "path": str(ROOT / "NOTICE"),
                                                              "mmproj": str(ROOT / "gone.gguf")}]})
        )


class SurfaceTests(unittest.TestCase):
    def test_the_picker_is_told_where_each_model_lives(self):
        s = _src("src/server.py")
        self.assertIn('"models": [{**m, "reach": _reach(m)}', s)

    def test_booting_a_model_that_is_not_here_fails_by_name(self):
        s = _src("src/server.py")
        self.assertIn("model_not_on_this_machine", s)

    def test_health_publishes_whether_the_selected_model_can_see(self):
        self.assertIn('"vision": __import__("registry").selected_vision()', _src("src/server.py"))

    def test_a_picture_attached_to_a_blind_model_is_answered_honestly(self):
        s = _src("src/server.py")
        self.assertIn("VISION_BLIND_NOTE.format(model=str(model))", s)
        self.assertIn("the picture attached to this message was not looked at", s)

    def test_the_portal_marks_what_the_kit_does_not_carry(self):
        js = _src("portal/app.js")
        self.assertIn("not carried by this kit", js)
        self.assertIn("attach-note", js, "the strip carries the warning")
        self.assertIn(".attach-note", _src("portal/style.css"))


if __name__ == "__main__":
    unittest.main()
