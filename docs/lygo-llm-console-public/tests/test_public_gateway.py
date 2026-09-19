from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from public_gateway import ALLOW_ORIGINS, _cors_ok, _rate  # noqa: E402


class PublicGatewayTests(unittest.TestCase):
    def test_cors_allowlist(self):
        self.assertTrue(_cors_ok("https://chatagent.ca"))
        self.assertTrue(_cors_ok("https://eternalhaven.ca"))
        self.assertTrue(_cors_ok("https://foo.hf.space"))
        self.assertFalse(_cors_ok("https://evil.example"))

    def test_rate_limit(self):
        ip = "203.0.113.9"
        ok = 0
        for _ in range(40):
            if _rate(ip):
                ok += 1
        self.assertLessEqual(ok, 24)
        self.assertGreater(ok, 0)

    def test_web_portal_files(self):
        p = ROOT / "web_portal"
        self.assertTrue((p / "index.html").is_file())
        html = (p / "index.html").read_text(encoding="utf-8")
        self.assertIn("LYGO Free LLM Portal", html)
        self.assertIn("Hugging Face", html)
        self.assertNotIn("LYGO_SERVER", html)


if __name__ == "__main__":
    unittest.main()
