#!/usr/bin/env python3
"""
Agent + multi-tool CLI for pxpipe-LYGO.

Examples (Grok Build / shell / other agents):
  python tools/pxpipe_lygo_for_agent.py --file huge_prompt.txt --target grok
  python tools/pxpipe_lygo_for_agent.py --text "..." --target anthropic --png out.png
  python tools/pxpipe_lygo_for_agent.py --shrink-file tools/big.log
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pxpipe_lygo.agent_helper import (  # noqa: E402
    compress_file_for_tool,
    compress_text_for_tool,
    maybe_compress_context,
    write_tool_json,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="pxpipe-LYGO for agents and multi-provider tools")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", "-f", help="Input text file")
    src.add_argument("--text", "-t", help="Inline text")
    src.add_argument("--shrink-file", help="Print shortened pointer text for chat context")
    ap.add_argument(
        "--target",
        choices=("auto", "anthropic", "openai", "grok", "gemini", "raw"),
        default="auto",
        help="API block format (default: auto → openai-compatible)",
    )
    ap.add_argument("--png", help="Write PNG alongside JSON blocks")
    ap.add_argument("--include-png-base64", action="store_true", help="Include raw base64 in JSON")
    args = ap.parse_args()

    if args.shrink_file:
        text = Path(args.shrink_file).read_text(encoding="utf-8", errors="replace")
        print(maybe_compress_context(text, target=args.target))
        return 0

    if args.file:
        payload = compress_file_for_tool(
            args.file,
            target=args.target,
            keep_png_path=args.png,
        )
    else:
        payload = compress_text_for_tool(
            args.text or "",
            target=args.target,
            keep_png_path=args.png,
        )

    if not args.include_png_base64:
        payload.pop("png_base64", None)
    write_tool_json(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())