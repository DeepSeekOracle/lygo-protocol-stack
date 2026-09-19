#!/usr/bin/env python3
import os
from pathlib import Path

NEED = [
    "plastic altar",
    "protocol zero",
    "endless ledger",
    "challenger x",
    "convenience is the collar",
    "wasteland",
    "rage they sell",
    "fortress is home",
]
ROOTS = [
    Path(r"J:\ALL SOUND FILES"),
    Path(r"J:\Music 2024"),
    Path(r"J:\FINISHED BEAT STARS MUSIC"),
]
AUDIO = {".mp3", ".wav", ".flac", ".m4a"}
SKIP = ("apache-openoffice", "\\windows", "\\steam", "node_modules", "$recycle", ".git")


def main() -> int:
    hits = {n: [] for n in NEED}
    seen = 0
    for root in ROOTS:
        if not root.exists():
            print("skip", root, flush=True)
            continue
        print("walk", root, flush=True)
        for dp, dns, fns in os.walk(root):
            low = dp.lower()
            if any(x in low for x in SKIP):
                dns[:] = []
                continue
            for fn in fns:
                if Path(fn).suffix.lower() not in AUDIO:
                    continue
                seen += 1
                fl = fn.lower()
                for n in NEED:
                    if n in fl and len(hits[n]) < 5:
                        hits[n].append(str(Path(dp) / fn))
    print("files scanned", seen, flush=True)
    for n, h in hits.items():
        print(n, "->", h if h else "NONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
