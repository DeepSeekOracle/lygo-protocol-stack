#!/usr/bin/env python3
"""search.py — query the local vault index built by embed_index.py.

Usage:
    python scripts/search.py "sovereign AI frameworks"
    python scripts/search.py "sovereign AI frameworks" --top 5
"""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ollama_client import embed, OllamaError  # noqa: E402
from embed_index import DEFAULT_EMBED_MODEL  # noqa: E402


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError(f"Embedding dimension mismatch: {len(a)} vs {len(b)}")
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def search(vault_root: Path, query: str, model: str = DEFAULT_EMBED_MODEL, top: int = 5) -> list[dict]:
    db_path = vault_root / ".vault_index.sqlite3"
    if not db_path.exists():
        raise FileNotFoundError(
            f"No index found at {db_path}. Run embed_index.py first."
        )

    query_vec = embed(model, query)

    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT note_path, chunk_index, text, embedding FROM chunks").fetchall()
    conn.close()

    scored = []
    for note_path, chunk_index, text, embedding_json in rows:
        vec = json.loads(embedding_json)
        try:
            score = cosine_similarity(query_vec, vec)
        except ValueError:
            continue
        scored.append({"note_path": note_path, "chunk_index": chunk_index, "text": text, "score": score})

    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:top]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("query", help="Search query")
    ap.add_argument("--vault", default=".", help="Vault root")
    ap.add_argument("--model", default=DEFAULT_EMBED_MODEL, help="Ollama embedding model")
    ap.add_argument("--top", type=int, default=5, help="Number of results")
    args = ap.parse_args()

    vault_root = Path(args.vault).resolve()
    try:
        results = search(vault_root, args.query, args.model, args.top)
    except (FileNotFoundError, OllamaError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if not results:
        print("No results.")
        return 0

    for r in results:
        print(f"\n[{r['score']:.3f}] {r['note_path']} (chunk {r['chunk_index']})")
        print(f"  {r['text'][:200]}{'...' if len(r['text']) > 200 else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
