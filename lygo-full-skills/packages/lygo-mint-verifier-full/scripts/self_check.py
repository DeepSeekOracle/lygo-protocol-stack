#!/usr/bin/env python3
"""Self-check — no subprocess/network; mint→verify roundtrip."""
from __future__ import annotations

import ast
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import mint_cli as mc  # noqa: E402


def _banned(path: Path) -> list[str]:
    hits: list[str] = []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            else:
                names = [(node.module or "").split(".")[0]]
            if "subprocess" in names:
                hits.append(f"{path.name}:subprocess")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "os":
                if node.func.attr in {"system", "popen"}:
                    hits.append(f"{path.name}:os.{node.func.attr}")
    return hits


def main() -> int:
    checks: dict = {"signature": mc.SIG, "version": mc.VERSION, "ok": False}
    bad: list[str] = []
    for p in HERE.glob("*.py"):
        bad.extend(_banned(p))
    checks["ast_clean"] = not bad
    checks["ast_hits"] = bad

    with tempfile.TemporaryDirectory() as td:
        state = Path(td)
        pack = state / "pack.md"
        pack.write_text("# Demo Pack\n\nTruth × Light\n", encoding="utf-8")
        minted = mc.mint_pack(str(pack), "2026-08-20.v1", title="Demo", state_dir=state, i_consent=True)
        checks["mint"] = bool(minted.get("ok")) and len(minted.get("sha256") or "") == 64
        ver = mc.verify_pack(str(pack), minted["sha256"])
        checks["verify"] = bool(ver.get("ok"))
        snip = mc.snippet_cmd(minted["sha256"], state, title="Demo", version="2026-08-20.v1")
        checks["snippet"] = bool(snip.get("ok")) and "HASH_SHA256" in snip.get("anchor_snippet", "")
        bf = mc.backfill(minted["sha256"], "x", "demo-post", state_dir=state, i_consent=True)
        checks["backfill"] = bool(bf.get("ok"))

    req = [
        ROOT / "SKILL.md",
        ROOT / "claw.json",
        ROOT / "skill-card.md",
        ROOT / "references" / "SECURITY.md",
        ROOT / "references" / "SKILLSPECTOR_AUDIT.md",
        HERE / "mint_cli.py",
    ]
    missing = [str(r.relative_to(ROOT)) for r in req if not r.is_file()]
    checks["missing"] = missing
    checks["ok"] = all(
        [
            checks["ast_clean"],
            checks["mint"],
            checks["verify"],
            checks["snippet"],
            checks["backfill"],
            not missing,
        ]
    )
    print(json.dumps(checks, indent=2))
    return 0 if checks["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
