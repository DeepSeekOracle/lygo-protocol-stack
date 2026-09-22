"""The operator's own folders, and receipts that have to be earned.

A live test asked the console to "create a note on the desktop"; it answered with a receipt for
workspace/desktop_note.txt and no file existed anywhere. These pin both halves: the folders are real
and reachable, and a file claim has to come back with a path that is actually on disk.
"""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import limbs  # noqa: E402
import tools  # noqa: E402
import user_paths  # noqa: E402


class FoldersAreReal(unittest.TestCase):
    def test_the_operator_folders_resolve_to_directories_that_exist(self):
        found = user_paths.folder_map()
        self.assertTrue(found, "no user folder resolved at all")
        for name, path in found.items():
            self.assertTrue(Path(path).is_dir(), f"{name} resolved to {path}, which is not a directory")

    def test_what_an_operator_says_is_understood(self):
        for phrase, key in (("desktop", "desktop"), ("my documents", "documents"),
                            ("Downloads", "downloads"), ("home", "home")):
            got = user_paths.resolve(phrase)
            self.assertIsNotNone(got, f"{phrase!r} did not resolve")
            self.assertEqual(str(got), user_paths.folder_map().get(key), f"{phrase!r} resolved to the wrong place")

    def test_an_absolute_folder_is_taken_as_given(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(user_paths.resolve(tmp), Path(tmp))

    def test_a_place_that_does_not_exist_is_not_invented(self):
        self.assertIsNone(user_paths.resolve("the beach"))
        self.assertIsNone(user_paths.resolve(""))


class ReceiptsAreEarned(unittest.TestCase):
    def test_a_saved_note_comes_back_with_a_path_that_is_really_there(self):
        with tempfile.TemporaryDirectory() as tmp:
            got = limbs.extra("save_note", {"name": "note.txt", "text": "hello from the console",
                                            "where": tmp, "consent": True})
            self.assertTrue(got.get("ok"), got)
            dest = Path(got["path"])
            self.assertTrue(dest.is_file(), "the limb reported a file that is not on disk")
            self.assertTrue(dest.is_absolute(), "a receipt must be an absolute path")
            on_disk = dest.read_bytes()
            self.assertEqual(on_disk, b"hello from the console")
            self.assertEqual(got["bytes"], len(on_disk))
            self.assertEqual(got["sha256_12"], hashlib.sha256(on_disk).hexdigest()[:12])
            self.assertTrue(got.get("verified"))

    def test_the_receipt_names_the_folder_it_really_used(self):
        with tempfile.TemporaryDirectory() as tmp:
            got = limbs.extra("save_note", {"name": "deep/note.md", "text": "x", "where": tmp, "consent": True})
            self.assertTrue(got.get("ok"), got)
            self.assertEqual(Path(got["path"]).parent, Path(tmp).resolve())

    def test_writing_outside_the_workspace_needs_consent(self):
        with tempfile.TemporaryDirectory() as tmp:
            got = limbs.extra("save_note", {"name": "nope.txt", "text": "x", "where": tmp})
            self.assertFalse(got.get("ok"))
            self.assertEqual(got.get("error"), "consent_required")
            self.assertFalse((Path(tmp) / "nope.txt").exists(), "it wrote without consent")

    def test_an_unknown_place_is_refused_with_the_real_map(self):
        got = limbs.extra("save_note", {"name": "x.txt", "text": "x", "where": "the beach", "consent": True})
        self.assertFalse(got.get("ok"))
        self.assertEqual(got.get("error"), "unknown_place")
        self.assertIn("desktop", got.get("known") or {}, "the refusal must hand back the folders it does know")

    def test_the_workspace_default_needs_no_consent(self):
        got = limbs.extra("save_note", {"name": "scratch.txt", "text": "x"})
        self.assertTrue(got.get("ok"), got)
        self.assertIn("workspace", got["path"].lower().replace("\\", "/"))


class ItsVisibleToTheOnBoxBrain(unittest.TestCase):
    def test_the_limb_is_advertised_and_the_budget_holds(self):
        names = [t["function"]["name"] for t in tools.core_schema()]
        self.assertIn("save_note", names)
        self.assertLessEqual(len(names), 40)
        self.assertLess(len(str(tools.core_schema())), 18000)


if __name__ == "__main__":
    unittest.main(verbosity=2)
