from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from web_tools import _blocked, wikipedia_search  # noqa: E402


class WebToolsTests(unittest.TestCase):
    def test_block_loopback(self):
        self.assertEqual(_blocked("http://127.0.0.1/x"), "https_only")
        self.assertEqual(_blocked("https://127.0.0.1/x"), "host")
        self.assertIsNone(_blocked("https://en.wikipedia.org/wiki/Light"))

    def test_wikipedia(self):
        hits = wikipedia_search("International Space Station", n=3)
        self.assertTrue(hits)
        self.assertTrue(any("wikipedia.org" in (h.get("url") or "") for h in hits))


if __name__ == "__main__":
    unittest.main()
