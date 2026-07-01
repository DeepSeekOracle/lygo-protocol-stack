#!/usr/bin/env python3
"""
Sync clawhub/mirrors from (1) OpenClaw skills/public, (2) workspace .grok/skills, (3) ClawHub registry.
No tokens required for inspect/install of public skills.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MIRRORS = REPO / "clawhub" / "mirrors"
OPENCLAW_PUBLIC = Path(os.environ.get("OPENCLAW_SKILLS_PUBLIC", r"C:\Users\justi\.openclaw\workspace\skills\public"))
GROK_SKILLS = Path(os.environ.get("LYGO_GROK_SKILLS", r"I:\E Drive\.grok\skills"))

# OpenClaw folder name -> canonical ClawHub slug
FOLDER_TO_SLUG: dict[str, str] = {
    "lygo-champion-lyra": "lygo-champion-lyra-starcore",
    "lygo-champion-delta9ra-wolf": "lygo-champion-delta9ra-wolf",
    "lygo-champion-cryptosophia-soulforger": "lygo-champion-cryptosophia-soulforger",
    "lygo-branch-cryptosophia": "lygo-champion-cryptosophia-soulforger",
}

# Prefer full trees from .grok when slug matches
GROK_PRIORITY = {
    "lygo-resonance",
    "lygo-ollama-army",
    "lygo-glyph2resonance",
    "lygo-fractalweaver",
    "lygo-truthlightecho",
    "lyra-brain",
    "lyra-openclaw",
}

CANONICAL_SLUGS = [
    "eternal-haven-lore-pack",
    "lygo-mint-verifier",
    "lygo-champion-cosmara",
    "book-brain",
    "lygo-lightfather-vector",
    "lyra-coin-launch-manager",
    "lygo-universal-living-memory-library",
    "lygo-champion-omnisiren-silent-storm",
    "lygo-champion-sancora-unified-minds",
    "lygo-champion-delta9ra-wolf",
    "openclaw-flow-kit",
    "lygo-champion-cryptosophia-soulforger",
    "lygo-champion-lyra-starcore",
    "lygo-champion-kairos-herald-of-time",
    "book-brain-visual-reader",
    "lygo-mint-operator-suite",
    "lygo-champion-sephrael-echo-walker",
    "lygo-champion-scenar-paradox",
    "lygo-champion-sraith-shadow-sentinel",
    "lygo-champion-aetheris-viral-truth",
    "lygo-champion-arkos-celestial-architect",
    "lygo-universal-cure-system",
    "lygo-resonance",
    "lygo-ollama-army",
    "lygo-glyph2resonance",
    "lygo-fractalweaver",
    "lygo-truthlightecho",
    "lygo-champion-401lyrakin-voice-between",
    "lygo-champion-volaris-prism-judgment",
    "void-atlas-protocol",
    "recursive-generosity-protocol",
]


def _run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    if os.name == "nt":
        line = subprocess.list2cmdline(cmd)
        return subprocess.run(line, cwd=cwd, capture_output=True, text=True, check=False, shell=True)
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)


def inspect_slug(slug: str) -> dict | None:
    cp = _run(
        ["npx", "--yes", "clawhub@latest", "inspect", f"deepseekoracle/{slug}", "--json"],
        cwd=REPO / "clawhub",
    )
    if cp.returncode != 0:
        return None
    try:
        data = json.loads(cp.stdout)
        return data.get("skill")
    except json.JSONDecodeError:
        return None


def copy_tree(src: Path, dest: Path) -> None:
    if not src.is_dir():
        return
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(
        src,
        dest,
        ignore=shutil.ignore_patterns(
            "__pycache__", "*.pyc", ".git", "node_modules", "ollama_queue", "ollama_results", "army"
        ),
    )


def install_from_registry(slug: str, dest: Path) -> bool:
    tmp = MIRRORS / "_registry_tmp"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    cp = _run(
        [
            "npx",
            "--yes",
            "clawhub@latest",
            "install",
            f"deepseekoracle/{slug}",
            "--dir",
            str(tmp),
            "--no-input",
        ],
        cwd=REPO / "clawhub",
    )
    if cp.returncode != 0:
        shutil.rmtree(tmp, ignore_errors=True)
        return False
    # clawhub installs into tmp/<slug> or tmp root
    candidates = [tmp / slug, tmp]
    installed = None
    for c in candidates:
        if (c / "SKILL.md").is_file():
            installed = c
            break
    if not installed:
        for child in tmp.iterdir():
            if child.is_dir() and (child / "SKILL.md").is_file():
                installed = child
                break
    if not installed:
        shutil.rmtree(tmp, ignore_errors=True)
        return False
    if dest.exists():
        shutil.rmtree(dest)
    shutil.move(str(installed), str(dest))
    shutil.rmtree(tmp, ignore_errors=True)
    return True


def write_stub(slug: str, meta: dict | None) -> None:
    dest = MIRRORS / slug
    dest.mkdir(parents=True, exist_ok=True)
    name = (meta or {}).get("displayName", slug)
    summary = (meta or {}).get("summary", "")
    readme = dest / "README.md"
    if readme.exists():
        return
    readme.write_text(
        f"# {name}\n\n"
        f"**ClawHub:** https://clawhub.ai/deepseekoracle/{slug}\n\n"
        f"```bash\nnpx clawhub@latest install deepseekoracle/{slug}\n```\n\n"
        f"{summary}\n\n"
        f"_Stub mirror — run `python tools/sync_clawhub_mirrors.py --fetch` to pull full files._\n",
        encoding="utf-8",
    )


def sync_one(slug: str, *, fetch_registry: bool) -> str:
    dest = MIRRORS / slug

    # 1) Grok priority
    grok = GROK_SKILLS / slug
    if slug in GROK_PRIORITY and grok.is_dir():
        copy_tree(grok, dest)
        return "grok"

    # 2) OpenClaw public (by slug or mapped folder)
    if OPENCLAW_PUBLIC.is_dir():
        for folder in OPENCLAW_PUBLIC.iterdir():
            if not folder.is_dir():
                continue
            mapped = FOLDER_TO_SLUG.get(folder.name, folder.name)
            if mapped != slug:
                continue
            if (folder / "SKILL.md").is_file():
                copy_tree(folder, dest)
                return f"openclaw:{folder.name}"
        direct = OPENCLAW_PUBLIC / slug
        if direct.is_dir() and (direct / "SKILL.md").is_file():
            copy_tree(direct, dest)
            return f"openclaw:{slug}"

    if dest.is_dir() and (dest / "SKILL.md").is_file():
        return "existing"

    if fetch_registry:
        if install_from_registry(slug, dest):
            return "registry"
        meta = inspect_slug(slug)
        if meta:
            write_stub(slug, meta)
            return "stub+meta"
    return "missing"


def build_registry_index() -> list[dict]:
    rows: list[dict] = []
    for slug in CANONICAL_SLUGS:
        meta = inspect_slug(slug)
        row = {
            "slug": slug,
            "name": (meta or {}).get("displayName", slug),
            "summary": (meta or {}).get("summary", ""),
            "clawhub_url": f"https://clawhub.ai/deepseekoracle/{slug}",
            "mirror": f"mirrors/{slug}" if (MIRRORS / slug).exists() else None,
            "published": meta is not None,
        }
        if meta and meta.get("stats"):
            row["downloads"] = meta["stats"].get("downloads")
        tags = (meta or {}).get("tags") or {}
        if tags.get("latest"):
            row["version"] = tags["latest"]
        rows.append(row)
    return rows


def main() -> int:
    fetch = "--fetch" in sys.argv or "--all" in sys.argv
    MIRRORS.mkdir(parents=True, exist_ok=True)

    report: dict[str, str] = {}
    for slug in CANONICAL_SLUGS:
        report[slug] = sync_one(slug, fetch_registry=fetch)

    for extra in ("lyra-brain", "lyra-openclaw"):
        report[extra] = sync_one(extra, fetch_registry=False)

    index = build_registry_index()
    out = REPO / "clawhub" / "skills.json"
    payload = {
        "publisher": "deepseekoracle",
        "profile_urls": [
            "https://clawhub.ai/deepseekoracle",
            "https://clawhub.ai/user/deepseekoracle",
        ],
        "install_template": "npx clawhub@latest install deepseekoracle/{slug}",
        "count_published": sum(1 for r in index if r["published"]),
        "count_mirrored": sum(1 for r in index if r["mirror"]),
        "skills": index,
        "repo_mirrors_only": [
            {"slug": "lyra-brain", "path": "mirrors/lyra-brain", "note": "3-Brain workflow; publish when ready"},
            {"slug": "lyra-openclaw", "path": "mirrors/lyra-openclaw", "note": "Hybrid OS limb"},
        ],
        "sync_report": report,
    }
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    install_sh = REPO / "clawhub" / "install-all.sh"
    lines = [
        "#!/usr/bin/env bash",
        "# Auto-generated by tools/sync_clawhub_mirrors.py",
        "set -euo pipefail",
        "SKILLS=(",
    ]
    for s in index:
        if s.get("published"):
            lines.append(f'  {s["slug"]}')
    lines.extend([")", "", 'for slug in "${SKILLS[@]}"; do', '  echo "==> deepseekoracle/${slug}"', '  npx clawhub@latest install "deepseekoracle/${slug}"', "done", "", 'echo "Done: ${#SKILLS[@]} skills."', ""])
    install_sh.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(report, indent=2))
    print(f"\nWrote {out} ({payload['count_published']} published, {payload['count_mirrored']} mirrored)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())