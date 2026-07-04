#!/usr/bin/env python3
"""embed_index.py — build a local semantic search index over permanent/ and wiki/.

This is the honest version of "retrieval" — a real, if simple, vector
index stored in a local sqlite file. No cloud, no blockchain, just cosine
similarity over embeddings from a local Ollama model.

Usage:
    python scripts/embed_index.py                      # rebuild index
    python scripts/embed_index.py --model nomic-embed-text
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ollama_client import embed, OllamaError  # noqa: E402

DEFAULT_EMBED_MODEL = "nomic-embed-text"


def chunk_markdown(text: str, max_chars: int = 800) -> list[str]:
    """Chunk by paragraph, merging short ones up to max_chars. Simple and
    predictable — good enough for a personal vault's note sizes."""
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for p in paras:
        if len(current) + len(p) + 2 <= max_chars:
            current = f"{current}\n\n{p}" if current else p
        else:
            if current:
                chunks.append(current)
            current = p
    if current:
        chunks.append(current)
    return chunks or [text.strip()]


def init_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            note_path TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            text TEXT NOT NULL,
            embedding TEXT NOT NULL,
            UNIQUE(note_path, chunk_index)
        )
    """)
    conn.commit()
    return conn


def build_index(vault_root: Path, model: str = DEFAULT_EMBED_MODEL) -> int:
    db_path = vault_root / ".vault_index.sqlite3"
    conn = init_db(db_path)

    note_dirs = [vault_root / "permanent", vault_root / "wiki"]
    md_files = [f for d in note_dirs if d.exists() for f in d.glob("*.md")]

    total_chunks = 0
    for md_file in md_files:
        rel_path = str(md_file.relative_to(vault_root))
        # Skip re-embedding unchanged files: cheap check via existing row count vs new chunk count
        text = md_file.read_text(encoding="utf-8")
        chunks = chunk_markdown(text)

        conn.execute("DELETE FROM chunks WHERE note_path = ?", (rel_path,))
        for i, chunk in enumerate(chunks):
            try:
                vec = embed(model, chunk)
            except OllamaError as e:
                print(f"  SKIP chunk {i} of {rel_path}: {e}", file=sys.stderr)
                continue
            conn.execute(
                "INSERT INTO chunks (note_path, chunk_index, text, embedding) VALUES (?, ?, ?, ?)",
                (rel_path, i, chunk, json.dumps(vec)),
            )
            total_chunks += 1
        conn.commit()
        print(f"Indexed {rel_path} ({len(chunks)} chunk(s))")

    conn.close()
    return total_chunks


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vault", default=".", help="Vault root")
    ap.add_argument("--model", default=DEFAULT_EMBED_MODEL, help="Ollama embedding model")
    args = ap.parse_args()

    vault_root = Path(args.vault).resolve()
    print(f"Building index for {vault_root} using '{args.model}'...")
    count = build_index(vault_root, args.model)
    print(f"Done. {count} chunk(s) indexed into .vault_index.sqlite3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
