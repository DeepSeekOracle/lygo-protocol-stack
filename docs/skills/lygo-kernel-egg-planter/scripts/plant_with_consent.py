#!/usr/bin/env python3
"""Plant kernel eggs — consent required; post-plant tamper verify always runs (no skip)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from _stack_paths import require_consent, resolve_stack_root  # noqa: E402


def run_verify(stack: Path) -> int:
    return subprocess.call(
        [sys.executable, str(SCRIPT_DIR / "verify_eggs.py"), "--stack-root", str(stack)]
    )


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "LYGO kernel egg planter (opt-in). "
            "Local registry/anchor only unless surfaces request prep for human publish. "
            "Never auto git-push / ClawHub skill publish / social."
        )
    )
    ap.add_argument("--i-consent", action="store_true", help="Required human consent for plant")
    ap.add_argument("--stack-root", default=None)
    ap.add_argument(
        "--surfaces",
        default="local,turbo,registry",
        help=(
            "Comma list: local,turbo,registry,pages,stubs,clawhub,champions. "
            "clawhub = local skills.json catalog pin only (not clawhub.ai publish). "
            "pages = prepare KernelEggRegistry.json for human Pages push."
        ),
    )
    ap.add_argument(
        "--local-only",
        action="store_true",
        help="Skip Turbo/permaweb attempt; local CA + registry only",
    )
    ap.add_argument("--dry-run", action="store_true", help="No plant writes; preflight only path")
    args = ap.parse_args()
    require_consent(args.i_consent)

    stack = resolve_stack_root(args.stack_root)
    subprocess.check_call([sys.executable, str(SCRIPT_DIR / "preflight.py"), "--stack-root", str(stack)])

    surfaces = {s.strip().lower() for s in args.surfaces.split(",") if s.strip()}
    tools = stack / "tools"

    print("Δ9Φ963 Kernel Egg Planter v1.3")
    print(f"  stack: {stack}")
    print(f"  surfaces: {sorted(surfaces)}")
    print("  verify: ALWAYS (no --skip-verify)")
    print("  publish: NEVER from this skill (human git/HF/ClawHub outside)")

    reg_path = stack / "data" / "kernel_eggs" / "registry.json"
    if reg_path.is_file() and not args.dry_run:
        print("[*] Pre-plant tamper verify (baseline)")
        if run_verify(stack) != 0:
            print("[FAIL] Pre-plant verify QUARANTINE — fix stack before plant", file=sys.stderr)
            return 1

    if "champions" in surfaces:
        subprocess.check_call(
            [
                sys.executable,
                str(tools / "champion_egg_planter.py"),
                "--i-consent",
            ],
            cwd=stack,
        )

    if "clawhub" in surfaces:
        # Local catalog pin only — does NOT call clawhub.ai publish API
        cmd = [
            sys.executable,
            str(SCRIPT_DIR / "plant_clawhub_catalog.py"),
            "--i-consent",
            "--stack-root",
            str(stack),
        ]
        if args.dry_run:
            cmd.append("--dry-run")
        subprocess.check_call(cmd)

    if args.dry_run:
        print("[dry-run] would run build + anchor + mandatory verify")
        return 0

    subprocess.check_call([sys.executable, str(tools / "build_kernel_eggs.py")], cwd=stack)
    anchor_cmd = [sys.executable, str(tools / "anchor_kernel_eggs.py")]
    if args.local_only or "turbo" not in surfaces:
        anchor_cmd.append("--local-only")
    subprocess.check_call(anchor_cmd, cwd=stack)

    # Mandatory — no bypass flag
    if run_verify(stack) != 0:
        print("[FAIL] Post-plant verify QUARANTINE — do not distribute", file=sys.stderr)
        return 1

    if "pages" in surfaces:
        src = stack / "docs" / "KernelEggRegistry.json"
        if src.is_file():
            print(f"[pages] prepared {src} — human must git push; skill does not publish")

    if "stubs" in surfaces:
        subprocess.check_call(
            [
                sys.executable,
                str(SCRIPT_DIR / "write_book_brain_stubs.py"),
                "--i-consent",
                "--stack-root",
                str(stack),
            ],
        )

    if reg_path.is_file():
        data = json.loads(reg_path.read_text(encoding="utf-8"))
        print(f"[done] registry_merkle_root={data.get('registry_merkle_root', '')}")
        print("[done] ALIGNED — optional human publish is a separate explicit step")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
