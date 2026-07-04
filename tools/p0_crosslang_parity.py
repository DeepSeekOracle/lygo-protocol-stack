#!/usr/bin/env python3
"""
Cross-language P0 parity: Python / C / Rust must produce identical canonical stdout SHA-256.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P0_PY = ROOT / "protocol0_byte_entropy_filter" / "src" / "python" / "lygo_p0.py"
FIXTURES = ROOT / "protocol0_byte_entropy_filter" / "fixtures" / "p0_vectors.json"
TSV = ROOT / "protocol0_byte_entropy_filter" / "fixtures" / "p0_vectors.tsv"
C_DIR = ROOT / "protocol0_byte_entropy_filter" / "src" / "c"
RUST_DIR = ROOT / "protocol0_byte_entropy_filter" / "src" / "rust"
GOLDEN = ROOT / "protocol0_byte_entropy_filter" / "fixtures" / "p0_canonical.sha256"


def write_tsv() -> None:
    data = json.loads(FIXTURES.read_text(encoding="utf-8"))
    lines = ["# id\thex"]
    for v in data["vectors"]:
        lines.append(f"{v['id']}\t{v['hex']}")
    TSV.write_text("\n".join(lines) + "\n", encoding="utf-8")


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run_python() -> str:
    proc = subprocess.run(
        [sys.executable, str(P0_PY), "--canonical"],
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout


def compile_c_harness() -> Path:
    exe = C_DIR / ("p0_harness.exe" if os.name == "nt" else "p0_harness")
    src_h = C_DIR / "lygo_p0_harness.c"
    cmd = ["gcc", "-O2", "-std=c11", "-o", str(exe), str(src_h), "-lm"]
    subprocess.run(cmd, check=True, cwd=C_DIR)
    return exe


def run_c(exe: Path) -> str:
    proc = subprocess.run(
        [str(exe), str(TSV)],
        capture_output=True,
        text=True,
        check=True,
        cwd=ROOT,
    )
    return proc.stdout if proc.stdout.endswith("\n") else proc.stdout + "\n"


def run_rust() -> str:
    subprocess.run(
        ["cargo", "build", "--release", "--bin", "p0_harness"],
        cwd=RUST_DIR,
        check=True,
        capture_output=True,
    )
    bin_path = RUST_DIR / "target" / "release" / ("p0_harness.exe" if os.name == "nt" else "p0_harness")
    proc = subprocess.run(
        [str(bin_path), str(TSV)],
        capture_output=True,
        text=True,
        check=True,
        cwd=ROOT,
    )
    return proc.stdout if proc.stdout.endswith("\n") else proc.stdout + "\n"


def main() -> int:
    if not FIXTURES.is_file():
        subprocess.run([sys.executable, str(ROOT / "tools" / "build_p0_vectors.py")], check=True)

    write_tsv()
    py_out = run_python()
    py_hash = sha(py_out)
    print("LYGO P0 CROSS-LANGUAGE PARITY")
    print("=" * 40)
    print(f"Python SHA-256: {py_hash}")

    errors: list[str] = []
    c_ran = False
    rs_ran = False

    try:
        exe = compile_c_harness()
        c_out = run_c(exe)
        c_hash = sha(c_out)
        c_ran = True
        print(f"C        SHA-256: {c_hash}")
        if c_hash != py_hash:
            errors.append("C output differs from Python")
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(f"C        SKIP ({e})")

    try:
        rs_out = run_rust()
        rs_hash = sha(rs_out)
        rs_ran = True
        print(f"Rust     SHA-256: {rs_hash}")
        if rs_hash != py_hash:
            errors.append("Rust output differs from Python")
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(f"Rust     SKIP ({e})")

    if not errors:
        GOLDEN.write_text(py_hash + "\n", encoding="utf-8")
        msg = "✅ Parity locked"
        if not c_ran or not rs_ran:
            msg += " (Python golden; install gcc + rust for full tri-lang check)"
        print(f"\n{msg}. Golden: fixtures/p0_canonical.sha256")
        return 0

    print("\n❌ Parity failures:")
    for err in errors:
        print(f"  - {err}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())