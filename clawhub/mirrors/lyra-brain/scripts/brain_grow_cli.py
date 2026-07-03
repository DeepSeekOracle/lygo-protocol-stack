#!/usr/bin/env python3
"""Grow one compact memory line into 3-brain graph."""
import argparse
import sys
from pathlib import Path

from _lyra_core_paths import lyra_core_root


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("text", nargs="?", help="Snip to grow (or --file)")
    ap.add_argument("--file", help="Read snip from file")
    ap.add_argument("--source", default="lyra-brain-skill", help="grow() source tag")
    args = ap.parse_args()

    text = args.text
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8").strip()
    if not text:
        ap.error("Provide text or --file")

    root = lyra_core_root()
    sys.path.insert(0, str(root / "modules"))
    import seals as seals_mod  # noqa: E402
    import lyra_brain  # noqa: E402

    idx = seals_mod.build_index()
    brain = lyra_brain.LyraThreeBrainMemory(base_dir=root, seal_index=idx, use_advanced=True)
    nid = brain.grow(text[:2000], source=args.source)
    print(nid)


if __name__ == "__main__":
    main()