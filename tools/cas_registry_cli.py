#!/usr/bin/env python3
"""
Full CLI wrapper — Biophase7 CAS + scalable registry (lattice).

Subcommands:
  build     Stream CDC → manifest → register [--verify]
  verify    Registry + provenance gate
  retrieve  Reassemble by manifest_id
  status    Registry + CAS stats
  prune     CAS GC (protects manifest-referenced chunks)
  repair    Drop broken manifest orphans
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def _run(script: str, argv: list[str]) -> int:
    return subprocess.call([PY, str(ROOT / "tools" / script), *argv], cwd=ROOT)


def cmd_build(args: argparse.Namespace) -> int:
    cmd = [
        str(ROOT / "tools" / "build_cas_manifest.py"),
        "--file",
        str(args.file),
        "--metadata",
        args.metadata,
        "--node-id",
        args.node_id,
    ]
    if args.no_p6:
        cmd.append("--no-p6")
    if args.anchor:
        cmd.append("--anchor")
    if args.verify:
        cmd.append("--verify")
    return subprocess.call([PY, *cmd], cwd=ROOT)


def cmd_verify(args: argparse.Namespace) -> int:
    argv = []
    if args.json:
        argv.append("--json")
    if args.strict:
        argv.append("--strict")
    if args.repair:
        argv.append("--repair")
    if args.manifest_id:
        argv.extend(["--manifest-id", args.manifest_id])
    return _run("verify_registry.py", argv)


def cmd_retrieve(args: argparse.Namespace) -> int:
    if args.list:
        return _run("retrieve_manifest.py", ["--list"])
    return _run(
        "retrieve_manifest.py",
        ["--id", args.manifest_id, "--out", str(args.out)],
    )


def cmd_status(_args: argparse.Namespace) -> int:
    return _run("registry_manager.py", ["--status"])


def cmd_prune(args: argparse.Namespace) -> int:
    return _run("registry_manager.py", ["--prune-cas-gb", str(args.gb)])


def cmd_repair(_args: argparse.Namespace) -> int:
    return _run("registry_manager.py", ["--repair"])


def cmd_register(args: argparse.Namespace) -> int:
    return _run(
        "register_synthetic_data.py",
        [
            "--file",
            str(args.file),
            "--metadata",
            args.metadata,
            "--node-id",
            args.node_id,
            *(["--no-p6"] if args.no_p6 else []),
            *(["--anchor"] if args.anchor else []),
            *(["--prune-cas-gb", str(args.prune_gb)] if args.prune_gb is not None else []),
        ],
    )


def main() -> int:
    ap = argparse.ArgumentParser(prog="cas_registry_cli", description="LYGO CAS registry (full wrapper)")
    sub = ap.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="build_cas_manifest.py")
    p_build.add_argument("--file", type=Path, required=True)
    p_build.add_argument("--metadata", default="{}")
    p_build.add_argument("--node-id", default="LYGO_REGISTRY_NODE")
    p_build.add_argument("--no-p6", action="store_true")
    p_build.add_argument("--anchor", action="store_true")
    p_build.add_argument("--verify", action="store_true")
    p_build.set_defaults(func=cmd_build)

    p_reg = sub.add_parser("register", help="register_synthetic_data.py")
    p_reg.add_argument("--file", type=Path, required=True)
    p_reg.add_argument("--metadata", default="{}")
    p_reg.add_argument("--node-id", default="LYGO_REGISTRY_NODE")
    p_reg.add_argument("--no-p6", action="store_true")
    p_reg.add_argument("--anchor", action="store_true")
    p_reg.add_argument("--prune-gb", type=float, default=None)
    p_reg.set_defaults(func=cmd_register)

    p_ver = sub.add_parser("verify", help="verify_registry.py")
    p_ver.add_argument("--json", action="store_true")
    p_ver.add_argument("--strict", action="store_true")
    p_ver.add_argument("--repair", action="store_true")
    p_ver.add_argument("--manifest-id", default=None)
    p_ver.set_defaults(func=cmd_verify)

    p_ret = sub.add_parser("retrieve", help="retrieve_manifest.py")
    p_ret.add_argument("--manifest-id", default=None)
    p_ret.add_argument("--out", type=Path, default=None)
    p_ret.add_argument("--list", action="store_true")
    p_ret.set_defaults(func=cmd_retrieve)

    sub.add_parser("status", help="registry status").set_defaults(func=cmd_status)
    p_prune = sub.add_parser("prune", help="prune CAS")
    p_prune.add_argument("--gb", type=float, default=50.0)
    p_prune.set_defaults(func=cmd_prune)
    sub.add_parser("repair", help="repair orphan manifests").set_defaults(func=cmd_repair)

    args = ap.parse_args()
    if args.command == "retrieve" and not args.list:
        if not args.manifest_id or not args.out:
            print(json.dumps({"error": "retrieve requires --manifest-id and --out (or --list)"}), file=sys.stderr)
            return 2
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())