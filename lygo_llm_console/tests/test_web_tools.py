from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chat_loop import extract_urls, host_prefetch  # noqa: E402
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

    def test_extract_urls(self):
        t = "Check https://chatagent.ca/ and <https://chatagent.ca/lygo-llm-console.html>"
        urls = extract_urls(t)
        self.assertIn("https://chatagent.ca/", urls)
        self.assertTrue(any("lygo-llm-console" in u for u in urls))


if __name__ == "__main__":
    unittest.main()
