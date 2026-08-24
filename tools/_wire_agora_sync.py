#!/usr/bin/env python3
"""Copy grok FULL skills into stack mirrors + embed SkillHub catalog."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

GROK = Path(r"I:\E Drive\.grok\skills")
STACK = Path(r"I:\E Drive\lygo-protocol-stack")
DOCS = STACK / "docs" / "skills"

COPY_TREES = [
    "lygo-cyborg-kernel",
    "lygo-cyborg-onramp",
    "lygo-public-lattice-gate",
    "lygo-agent-lattice",
    "lygo-external-lattice-anchor",
    "lygo-sovereign-kernel-seeder",
    "lygo-kernel-egg-planter",
    "lygo-lattice-pulse",
]

COPY_FILES = [
    ("lygo-continuity-advisor", "SKILL.md"),
]


def copy_tree(name: str) -> None:
    src = GROK / name
    dst = DOCS / name
    if not src.is_dir():
        print("skip missing grok", name)
        return
    dst.mkdir(parents=True, exist_ok=True)
    for p in src.rglob("*"):
        if not p.is_file():
            continue
        if "__pycache__" in p.parts or p.suffix == ".pyc":
            continue
        if "state" in p.parts:
            continue
        rel = p.relative_to(src)
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, out)
    print("copied", name, "->", dst)


def embed_catalog(cat: dict, html_path: Path) -> None:
    if not html_path.is_file():
        print("no html", html_path)
        return
    text = html_path.read_text(encoding="utf-8")
    needle = '<script id="boot-catalog" type="application/json">'
    i = text.find(needle)
    if i < 0:
        print("no boot-catalog", html_path)
        return
    j = text.find("</script>", i)
    if j < 0:
        print("unclosed boot-catalog", html_path)
        return
    blob = json.dumps(cat, ensure_ascii=False, separators=(",", ":"))
    html_path.write_text(text[: i + len(needle)] + blob + text[j:], encoding="utf-8")
    print("embedded catalog", html_path)


def main() -> int:
    for name in COPY_TREES:
        copy_tree(name)
    for name, rel in COPY_FILES:
        src = GROK / name / rel
        dst = DOCS / name / rel
        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print("copied file", dst)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
