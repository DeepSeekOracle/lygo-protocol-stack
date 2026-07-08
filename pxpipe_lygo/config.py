"""Configuration for pxpipe-LYGO (env + honest P0 gates)."""

from __future__ import annotations

import os
from pathlib import Path

STACK_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = STACK_ROOT / "data" / "pxpipe_lygo" / "manifests"

MIN_CHARS_TO_COMPRESS = int(os.environ.get("LYGO_PXPIPE_MIN_CHARS", "800"))
MIN_TOKEN_SAVINGS_RATIO = float(os.environ.get("LYGO_PXPIPE_MIN_SAVINGS", "1.35"))
MAX_PNG_WIDTH = int(os.environ.get("LYGO_PXPIPE_MAX_W", "1928"))
MAX_PNG_HEIGHT = int(os.environ.get("LYGO_PXPIPE_MAX_H", "1928"))
FONT_SIZE = int(os.environ.get("LYGO_PXPIPE_FONT_SIZE", "14"))
LINE_SPACING = int(os.environ.get("LYGO_PXPIPE_LINE_SPACING", "4"))
PROXY_PORT = int(os.environ.get("LYGO_PXPIPE_PORT", "47821"))

PROVIDER_ORDER = ("grok", "claude", "gemini", "openai")

USE_P1 = os.environ.get("LYGO_PXPIPE_USE_P1", "1").strip() not in ("0", "false", "no")
USE_P3 = os.environ.get("LYGO_PXPIPE_USE_P3", "1").strip() not in ("0", "false", "no")
ANCHOR_MANIFESTS = os.environ.get("LYGO_PXPIPE_ANCHOR", "0").strip() in ("1", "true", "yes")