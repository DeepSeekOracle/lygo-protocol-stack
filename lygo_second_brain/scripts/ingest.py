#!/usr/bin/env python3
"""ingest.py — process a raw source into a permanent, atomic note.

Usage:
    python scripts/ingest.py raw/paper.pdf
    python scripts/ingest.py raw/article.txt --model llama3.2

What it actually does (no mysticism):
  1. Reads the source (.txt/.md directly, .pdf via pdftotext).
  2. Hard-caps input size before sending to the model — a real, useful
     guard against feeding something absurdly large into a local model's
     context window. (This is the honest version of "P0 validates
     entropy" — it's a size/corruption check, not a content judgment.)
  3. Asks the local model to extract: title, 3-6 key points, tags.
     Falls back to storing the raw text if the model's output isn't
     parseable JSON, rather than silently dropping content.
  4. Writes a note to permanent/ with frontmatter: title, source path,
     ingestion timestamp, sha256 of the raw file, tags.
  5. Copies the raw file to archive/.
  6. git commits the vault (if it's a git repo) — this is the honest
     version of "anchoring": a timestamped, diffable, revertible commit,
     not a blockchain write.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vault_lib import (  # noqa: E402
    append_stack_manifest,
    git_commit,
    now_iso,
    read_text_source,
    sha256_of_file,
    slugify,
    write_note,
)
from ollama_client import generate, OllamaError  # noqa: E402

MAX_INPUT_CHARS = 40_000  # guard against feeding something absurd into the model

EXTRACTION_PROMPT = """You are extracting a structured note from a source document.
Read the text below and respond with ONLY valid JSON, no commentary, no markdown fences.

{{
  "title": "a concise, specific title (max 12 words)",
  "summary": "2-4 sentence summary in your own words",
  "key_points": ["3 to 6 atomic, standalone bullet points"],
  "tags": ["3 to 6 lowercase single-or-hyphenated-word tags"]
}}

SOURCE TEXT:
---
{text}
---

JSON:"""


def extract_note(text: str, model: str) -> dict:
    prompt = EXTRACTION_PROMPT.format(text=text[:MAX_INPUT_CHARS])
    raw = generate(model, prompt)
    # Models sometimes wrap JSON in fences despite instructions — strip if present.
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    try:
        return json.loads(cleaned.strip())
    except json.JSONDecodeError:
        return {
            "title": None,
            "summary": None,
            "key_points": [],
            "tags": ["unstructured"],
            "_raw_model_output": raw,
        }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", help="Path to a raw source file (.txt, .md, .pdf)")
    ap.add_argument("--model", default="llama3.2", help="Ollama model to use for extraction")
    ap.add_argument("--vault", default=".", help="Vault root (default: current directory)")
    args = ap.parse_args()

    vault_root = Path(args.vault).resolve()
    source_path = Path(args.source).resolve()

    if not source_path.exists():
        print(f"ERROR: source not found: {source_path}", file=sys.stderr)
        return 1

    print(f"Reading {source_path.name}...")
    try:
        text = read_text_source(source_path)
    except (ValueError, RuntimeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if not text.strip():
        print("ERROR: extracted no text from source (empty or unreadable file).", file=sys.stderr)
        return 1

    if len(text) > MAX_INPUT_CHARS:
        print(f"NOTE: source is {len(text)} chars, truncating to {MAX_INPUT_CHARS} for extraction.")

    print(f"Extracting note via Ollama model '{args.model}'...")
    try:
        note_data = extract_note(text, args.model)
    except OllamaError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    title = note_data.get("title") or source_path.stem
    slug = slugify(title)
    file_hash = sha256_of_file(source_path)

    frontmatter = {
        "title": title,
        "source": str(source_path.relative_to(vault_root)) if vault_root in source_path.parents else source_path.name,
        "ingested_at": now_iso(),
        "sha256": file_hash[:16],
        "tags": note_data.get("tags", []),
        "model": args.model,
    }

    body_parts = []
    if note_data.get("summary"):
        body_parts.append(f"## Summary\n\n{note_data['summary']}")
    if note_data.get("key_points"):
        points = "\n".join(f"- {p}" for p in note_data["key_points"])
        body_parts.append(f"## Key points\n\n{points}")
    if note_data.get("_raw_model_output"):
        body_parts.append(
            "## Unstructured (model output was not valid JSON)\n\n"
            f"{note_data['_raw_model_output']}"
        )
    if not body_parts:
        body_parts.append("## Raw source (extraction produced no structured content)\n\n" + text[:4000])

    body = "\n\n".join(body_parts)
    note_path = vault_root / "permanent" / f"{slug}.md"
    write_note(note_path, frontmatter, body)
    print(f"Wrote note: {note_path.relative_to(vault_root)}")

    archive_path = vault_root / "archive" / source_path.name
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, archive_path)
    print(f"Archived source: {archive_path.relative_to(vault_root)}")

    commit_result = git_commit(vault_root, f"ingest: {title}")
    print(f"Git: {commit_result}")

    append_stack_manifest(
        vault_root,
        "ingest",
        {
            "title": title,
            "note": str(note_path.relative_to(vault_root)).replace("\\", "/"),
            "sha256": file_hash[:16],
            "git": commit_result,
        },
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
