"""CLI: compress file/stdin, run proxy."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pxpipe_lygo.compressor import compress_text


def cmd_compress(args: argparse.Namespace) -> int:
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8", errors="replace")
    else:
        text = sys.stdin.read()
    result = compress_text(text, provider=args.provider)
    if args.out_png and result.get("action") == "compress":
        import base64

        Path(args.out_png).write_bytes(base64.b64decode(result["png_base64"]))
        result = {k: v for k, v in result.items() if k != "png_base64"}
    print(json.dumps(result, indent=2))
    return 0


def cmd_proxy(_: argparse.Namespace) -> int:
    from pxpipe_lygo.proxy_server import main as proxy_main

    return proxy_main()


def main() -> int:
    ap = argparse.ArgumentParser(description="LYGO pxpipe-lygo — sovereign context compression")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("compress", help="Compress text to PNG manifest")
    c.add_argument("--file", "-f", help="Input file (else stdin)")
    c.add_argument("--provider", choices=("grok", "claude", "gemini", "openai"))
    c.add_argument("--out-png", help="Write PNG bytes to path")
    c.set_defaults(func=cmd_compress)

    p = sub.add_parser("proxy", help="Run local HTTP proxy")
    p.set_defaults(func=cmd_proxy)

    args = ap.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())