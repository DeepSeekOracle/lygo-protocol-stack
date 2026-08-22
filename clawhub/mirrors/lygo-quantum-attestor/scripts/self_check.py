#!/usr/bin/env python3
"""Self-check lygo-quantum-attestor — no network/subprocess."""
from __future__ import annotations

import ast
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import attestor_cli as ac  # noqa: E402


def _banned(path: Path) -> list[str]:
    hits: list[str] = []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = (
                [a.name.split(".")[0] for a in node.names]
                if isinstance(node, ast.Import)
                else [(node.module or "").split(".")[0]]
            )
            for bad in ("subprocess", "socket", "requests", "urllib"):
                if bad in names:
                    hits.append(f"{path.name}:{bad}")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "os":
                if node.func.attr in {"system", "popen"}:
                    hits.append(f"{path.name}:os.{node.func.attr}")
    return hits


def main() -> int:
    checks: dict = {"signature": ac.SIG, "version": ac.VERSION, "ok": False}
    bad: list[str] = []
    for p in HERE.glob("*.py"):
        bad.extend(_banned(p))
    checks["ast_clean"] = not bad
    checks["ast_hits"] = bad

    import argparse

    attest = ac.cmd_attest(
        argparse.Namespace(
            node_id="selfcheck",
            truth="T",
            chaos="C",
            slm_root="",
            anchor_file="",
            allow_collapse=False,
            write=None,
            i_consent=False,
        )
    )
    checks["attest"] = bool(attest.get("ok")) and bool(attest.get("attest_sha256"))
    checks["non_collapsing"] = bool(attest.get("non_collapsing"))

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "attest.json"
        refuse = ac.cmd_attest(
            argparse.Namespace(
                node_id="selfcheck",
                truth="T",
                chaos="C",
                slm_root="",
                anchor_file="",
                allow_collapse=False,
                write=str(p),
                i_consent=False,
            )
        )
        checks["write_requires_consent"] = refuse.get("ok") is False
        okw = ac.cmd_attest(
            argparse.Namespace(
                node_id="selfcheck",
                truth="T",
                chaos="C",
                slm_root="deadbeef" * 8,
                anchor_file="",
                allow_collapse=False,
                write=str(p),
                i_consent=True,
            )
        )
        checks["write_ok"] = bool(okw.get("ok")) and p.is_file()
        sealed = ac.cmd_seal_delta9(
            argparse.Namespace(from_file=str(p), write=str(Path(td) / "sealed.json"), i_consent=True)
        )
        checks["seal_delta9"] = bool(sealed.get("ok")) and bool((sealed.get("delta9_seal") or {}).get("delta9_seal_sha256"))
        ver = ac.cmd_verify_node(argparse.Namespace(from_file=str(Path(td) / "sealed.json")))
        checks["verify_node"] = bool(ver.get("ok"))
        rec = ac.cmd_emit_receipt(
            argparse.Namespace(from_file=str(Path(td) / "sealed.json"), write=str(Path(td) / "receipt.json"), i_consent=True)
        )
        checks["emit_receipt"] = bool(rec.get("ok")) and len(rec.get("receipt_sha256") or "") == 64

    demo = ac.cmd_demo(argparse.Namespace())
    checks["demo"] = bool(demo.get("ok"))

    req = [
        ROOT / "SKILL.md",
        ROOT / "claw.json",
        ROOT / "references" / "SECURITY.md",
        HERE / "attestor_cli.py",
    ]
    missing = [str(r.relative_to(ROOT)) for r in req if not r.is_file()]
    checks["missing"] = missing
    checks["ok"] = all(
        [
            checks["ast_clean"],
            checks["attest"],
            checks["non_collapsing"],
            checks["write_requires_consent"],
            checks["write_ok"],
            checks["seal_delta9"],
            checks["verify_node"],
            checks["emit_receipt"],
            checks["demo"],
            not missing,
        ]
    )
    print(json.dumps(checks, indent=2))
    return 0 if checks["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
