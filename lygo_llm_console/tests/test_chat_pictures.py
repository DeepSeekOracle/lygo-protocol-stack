"""Generated pictures must be viewable in the chat bubble, not only as a path string."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import media_tools as mt  # noqa: E402


class WorkspaceImagePathTests(unittest.TestCase):
    def test_a_real_generated_png_is_found_by_basename(self):
        p = mt.workspace_image_path("gen-20260925-000614.png")
        self.assertIsNotNone(p)
        self.assertTrue(p.is_file())
        self.assertEqual(p.name, "gen-20260925-000614.png")

    def test_path_traversal_is_refused(self):
        self.assertIsNone(mt.workspace_image_path("../SOUL.md"))
        self.assertIsNone(mt.workspace_image_path("..\\SOUL.md"))
        self.assertIsNone(mt.workspace_image_path("/etc/passwd"))

    def test_a_non_image_is_refused(self):
        self.assertIsNone(mt.workspace_image_path("upload.bin"))
        self.assertIsNone(mt.workspace_image_path(""))


class PortalShowsThePictureTests(unittest.TestCase):
    def test_the_page_fetches_the_sandbox_image_route(self):
        js = (ROOT / "portal" / "app.js").read_text(encoding="utf-8")
        self.assertIn("/api/media/image/", js)
        self.assertIn("function finishBubblePictures", js)
        self.assertIn("function pictureNames", js)
        self.assertIn("bubble-pic", js)
        css = (ROOT / "portal" / "style.css").read_text(encoding="utf-8")
        self.assertIn(".bubble-pic", css)

    def test_the_server_owns_the_media_route(self):
        src = (ROOT / "src" / "server.py").read_text(encoding="utf-8")
        self.assertIn('/api/media/image/', src)
        self.assertIn("workspace_image_path", src)


if __name__ == "__main__":
    unittest.main()
