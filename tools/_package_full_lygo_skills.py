#!/usr/bin/env python3
"""Package top FULL LYGO engineer skills (not ClawHub public surface)."""
from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

STACK = Path(r"D:\lygo-protocol-stack")
ROOT = STACK / "docs" / "lygo-full-skills"
DIST = ROOT / "dist"
PACK = ROOT / "packages"

SOURCES = {
    "lygo-protocol-stack-operator": [
        STACK / "clawhub" / "mirrors" / "lygo-protocol-stack-operator",
        Path(r"I:\E Drive\.grok\skills\lygo-protocol-stack-operator"),
    ],
    "lygo-kernel-egg-planter": [
        STACK / "docs" / "skills" / "lygo-kernel-egg-planter",
        STACK / "clawhub" / "mirrors" / "lygo-kernel-egg-planter",
        Path(r"I:\E Drive\.grok\skills\lygo-kernel-egg-planter"),
    ],
    "lygo-ollama-army": [
        STACK / "clawhub" / "mirrors" / "lygo-ollama-army",
        Path(r"I:\E Drive\.grok\skills\lygo-ollama-army"),
    ],
}

ROLES = {
    "lygo-protocol-stack-operator": "P0–P9 stack integrator + audits (self-check spine of the lattice)",
    "lygo-kernel-egg-planter": "Merkle eggs, plant/verify, modular lattice limbs",
    "lygo-ollama-army": "Local army + sentinel + queue (continuous self-audit loop)",
}

SKIP_PARTS = {
    ".git",
    "__pycache__",
    "node_modules",
    "results",
    "logs",
    "workspace",
    "ollama_results",
    "ollama_queue",
    ".bak",
}
SKIP_SUFFIX = {".pyc", ".pyo", ".log"}


def pick_src(cands: list[Path]) -> Path | None:
    best = None
    n = -1
    for c in cands:
        if not c.is_dir():
            continue
        cnt = sum(
            1
            for p in c.rglob("*")
            if p.is_file() and not any(x in p.parts for x in SKIP_PARTS)
        )
        if cnt > n:
            n = cnt
            best = c
    return best


def should_copy(p: Path) -> bool:
    if any(x in p.parts for x in SKIP_PARTS):
        return False
    if p.suffix.lower() in SKIP_SUFFIX:
        return False
    if p.name.endswith(".result.json"):
        return False
    if p.name.endswith(".task.json") and "tasks" in p.parts:
        return False
    return True


def copy_tree(src: Path, dest: Path) -> int:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    n = 0
    for p in src.rglob("*"):
        if not p.is_file() or not should_copy(p):
            continue
        rel = p.relative_to(src)
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, out)
        n += 1
    return n


def main() -> int:
    for d in (ROOT, DIST, PACK):
        d.mkdir(parents=True, exist_ok=True)

    catalog = {
        "signature": "Delta9Phi963-FULL-LYGO-SKILLS-v1",
        "version": "1.0.0",
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "channel": "FULL_LYGO_ENGINEER",
        "clawhub": "never",
        "paypal": "https://www.paypal.com/paypalme/ExcavationPro",
        "steward": "Justin Helmer / Excavationpro (Lightfather)",
        "purpose": "Engineer-grade FULL packages for self-auditing LYGO lattice — not ClawHub public safety shells",
        "skills": [],
    }

    for slug, cands in SOURCES.items():
        src = pick_src(cands)
        if not src:
            print("MISSING", slug)
            continue
        pkg = PACK / f"{slug}-full"
        n = copy_tree(src, pkg)
        stamp = [
            f"# FULL LYGO package — {slug}",
            "",
            "Channel: **FULL_LYGO_ENGINEER** (not ClawHub public safety surface).",
            "",
            "For operators building a **self-auditing LYGO lattice**.",
            "Integrity is expected from the lattice (P0, consent planter, sentinel, dual ledgers) —",
            "not from corporate gutted skill shells alone.",
            "",
            f"Steward: {catalog['steward']}",
            f"Source: `{src}`",
            f"Packaged: {catalog['updated_utc']}",
            f"Files: {n}",
            "",
            "Not malicious by design. Good-faith LYGO policy. Engineer autonomy.",
            "You are responsible for how you run extended systems.",
        ]
        (pkg / "FULL_LYGO.md").write_text("\n".join(stamp) + "\n", encoding="utf-8")
        # Ensure disclaimer present
        (pkg / "READ_DISCLAIMER_FIRST.md").write_text(
            "You must accept the FULL LYGO gate on LYGOSKILLHUB before using this package.\n"
            "https://chatagent.ca/lygoskillhub.html#full-lygo\n",
            encoding="utf-8",
        )

        zpath = DIST / f"{slug}-full.zip"
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in pkg.rglob("*"):
                if p.is_file():
                    zf.write(p, arcname=str(Path(f"{slug}-full") / p.relative_to(pkg)))
        h = hashlib.sha256(zpath.read_bytes()).hexdigest()
        catalog["skills"].append(
            {
                "slug": slug,
                "name": slug.replace("-", " ").title() + " (FULL LYGO)",
                "package": f"{slug}-full",
                "zip": f"{slug}-full.zip",
                "zip_rel": f"dist/{slug}-full.zip",
                "zip_sha256": h,
                "bytes": zpath.stat().st_size,
                "file_count": n + 2,
                "role": ROLES.get(slug, ""),
                "source_path": str(src),
            }
        )
        print("packed", slug, "files", n, "zip_kb", zpath.stat().st_size // 1024)

    (ROOT / "catalog.json").write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")

    extras = [
        Path(r"D:\chatagent\data\lygo-full-skills"),
        Path(r"D:\Excavationpro\data\lygo-full-skills"),
        STACK / "docs" / "data" / "lygo-full-skills",
    ]
    for extra in extras:
        extra.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / "catalog.json", extra / "catalog.json")
        d2 = extra / "dist"
        if d2.exists():
            shutil.rmtree(d2)
        shutil.copytree(DIST, d2)
        print("mirrored", extra)

    print("OK skills", len(catalog["skills"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
