"""vault_lib.py — shared helpers for the second-brain scripts.

No mysticism, no blockchain. Frontmatter is plain YAML-ish key:value,
"anchoring" is a git commit, "validation" is a corrupted-file check.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def slugify(text: str, max_len: int = 60) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text[:max_len] or "untitled"


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_note(path: Path, frontmatter: dict, body: str) -> None:
    lines = ["---"]
    for k, v in frontmatter.items():
        if isinstance(v, list):
            lines.append(f"{k}: [{', '.join(str(x) for x in v)}]")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    lines.append(body.rstrip() + "\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def read_note(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    fm_raw, body = parts[1], parts[2]
    fm: dict = {}
    for line in fm_raw.strip().splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            v = [x.strip() for x in v[1:-1].split(",") if x.strip()]
        fm[k.strip()] = v
    return fm, body.strip()


def read_text_source(path: Path) -> str:
    """Read a raw source file as plain text. Handles .txt/.md natively.
    For .pdf, requires `pdftotext` (poppler-utils) on PATH — raises a clear
    error rather than silently failing if it's missing."""
    suffix = path.suffix.lower()
    if suffix in (".txt", ".md"):
        return path.read_text(encoding="utf-8", errors="replace")
    if suffix == ".pdf":
        try:
            result = subprocess.run(
                ["pdftotext", "-layout", str(path), "-"],
                capture_output=True, text=True, check=True,
            )
            return result.stdout
        except FileNotFoundError as e:
            raise RuntimeError(
                "pdftotext not found. Install poppler-utils "
                "(e.g. `apt install poppler-utils` or `brew install poppler`) "
                "to ingest PDFs."
            ) from e
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"pdftotext failed on {path}: {e.stderr}") from e
    raise ValueError(f"Unsupported source type: {suffix}. Supported: .txt, .md, .pdf")


def git_commit(vault_root: Path, message: str) -> str:
    """Commit all changes in the vault. Returns 'ok', 'nothing-to-commit',
    or 'not-a-git-repo' — never raises, so ingest scripts don't crash if
    the vault hasn't been git-initialized yet."""
    if not (vault_root / ".git").exists():
        return "not-a-git-repo"
    subprocess.run(["git", "add", "-A"], cwd=vault_root, capture_output=True)
    result = subprocess.run(
        ["git", "commit", "-m", message], cwd=vault_root, capture_output=True, text=True
    )
    if result.returncode != 0:
        if "nothing to commit" in (result.stdout + result.stderr).lower():
            return "nothing-to-commit"
        return f"error: {result.stderr.strip()}"
    return "ok"


def stack_manifest_path(vault_root: Path) -> Path | None:
    """Lattice ledger at data/second_brain/manifest.jsonl (optional)."""
    env = os.environ.get("LYGO_STACK_ROOT", "").strip()
    if env:
        return Path(env) / "data" / "second_brain" / "manifest.jsonl"
    stack = vault_root.parent.parent
    if not (stack / "tools" / "lygo_second_brain.py").is_file():
        return None
    return stack / "data" / "second_brain" / "manifest.jsonl"


def append_stack_manifest(vault_root: Path, event: str, detail: dict) -> None:
    path = stack_manifest_path(vault_root)
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"ts": now_iso(), "event": event, **detail}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")
