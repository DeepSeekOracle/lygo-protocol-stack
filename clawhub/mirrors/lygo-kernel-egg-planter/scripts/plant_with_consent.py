#!/usr/bin/env python3
"""Plant kernel eggs — consent-gated wrapper around stack tools."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]


def resolve_stack_root(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    env = os.environ.get("LYGO_STACK_ROOT", "").strip()
    if env:
        return Path(env).resolve()
    # sibling of skill in mirrors → lygo-protocol-stack
    for anc in SKILL_ROOT.parents:
        if (anc / "tools" / "build_kernel_eggs.py").is_file():
            return anc
    raise SystemExit("Set LYGO_STACK_ROOT to lygo-protocol-stack clone")


def require_consent(flag: bool) -> None:
    if flag:
        return
    if os.environ.get("LYGO_EGG_PLANT_CONSENT", "").lower() in ("yes", "1", "true"):
        return
    print("Consent required: pass --i-consent or set LYGO_EGG_PLANT_CONSENT=yes", file=sys.stderr)
    print("Read references/CONSENT_AND_ETHICS.md first.", file=sys.stderr)
    raise SystemExit(2)


def main() -> int:
    ap = argparse.ArgumentParser(description="LYGO kernel egg planter (opt-in)")
    ap.add_argument("--i-consent", action="store_true", help="User explicitly opts in")
    ap.add_argument("--stack-root", default=None)
    ap.add_argument(
        "--surfaces",
        default="local,turbo,registry",
        help="Comma list: local,turbo,registry,pages,stubs,clawhub",
    )
    ap.add_argument("--local-only", action="store_true", help="Skip Turbo permaweb")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    require_consent(args.i_consent)

    stack = resolve_stack_root(args.stack_root)
    surfaces = {s.strip().lower() for s in args.surfaces.split(",") if s.strip()}
    tools = stack / "tools"

    print("Δ9Φ963 Kernel Egg Planter")
    print(f"  stack: {stack}")
    print(f"  surfaces: {sorted(surfaces)}")

    if "clawhub" in surfaces:
        cmd = [sys.executable, str(SKILL_ROOT / "scripts" / "plant_clawhub_catalog.py"), "--i-consent", "--stack-root", str(stack)]
        if args.dry_run:
            cmd.append("--dry-run")
        subprocess.check_call(cmd)

    if args.dry_run:
        print("[dry-run] would run build_kernel_eggs.py + anchor_kernel_eggs.py")
        return 0

    subprocess.check_call([sys.executable, str(tools / "build_kernel_eggs.py")], cwd=stack)
    anchor_cmd = [sys.executable, str(tools / "anchor_kernel_eggs.py")]
    if args.local_only or "turbo" not in surfaces:
        anchor_cmd.append("--local-only")
    subprocess.check_call(anchor_cmd, cwd=stack)

    if "pages" in surfaces:
        src = stack / "docs" / "KernelEggRegistry.json"
        if src.is_file():
            print(f"[pages] registry ready at {src} — user git push to GitHub Pages")

    if "stubs" in surfaces:
        stub_script = SKILL_ROOT / "scripts" / "write_book_brain_stubs.py"
        subprocess.check_call(
            [sys.executable, str(stub_script), "--i-consent", "--stack-root", str(stack)],
            cwd=stack,
        )

    reg = stack / "data" / "kernel_eggs" / "registry.json"
    if reg.is_file():
        import json

        data = json.loads(reg.read_text(encoding="utf-8"))
        print(f"[done] registry_merkle_root={data.get('registry_merkle_root', '')[:32]}…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())