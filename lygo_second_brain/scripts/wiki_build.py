#!/usr/bin/env python3
"""wiki_build.py — generate a concept page by retrieving and synthesizing existing notes.

Usage:
    python scripts/wiki_build.py "second brain"
    python scripts/wiki_build.py "second brain" --model llama3.2 --top 8

Honesty check built in: if the vault has no relevant notes on the topic,
this says so and does not generate a page from the model's general
knowledge alone — a wiki page here should represent what's actually in
your vault, not what the model already "knows."
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vault_lib import git_commit, now_iso, slugify, write_note  # noqa: E402
from ollama_client import generate, OllamaError  # noqa: E402
from search import search as vault_search  # noqa: E402

MIN_RELEVANT_SCORE = 0.45  # below this, don't count the hit as genuinely relevant

SYNTH_PROMPT = """You are building a wiki page for a personal knowledge vault, synthesizing
ONLY the note excerpts provided below. Do not add outside facts or general
knowledge beyond what's here — this page should reflect what's actually in
the vault, not general knowledge about the topic.

Cite the source note filename after each claim, like: "...as noted [note-name.md]."

TOPIC: {topic}

NOTE EXCERPTS:
{excerpts}

Write a concise wiki page (headings + prose, 200-500 words) synthesizing these
notes on the topic. If the excerpts don't actually cover the topic well, say so
plainly instead of padding with generalities."""


def build_wiki_page(vault_root: Path, topic: str, model: str, top: int) -> tuple[str, list[str]]:
    try:
        hits = vault_search(vault_root, topic, top=top)
    except FileNotFoundError as e:
        raise RuntimeError(str(e)) from e

    relevant = [h for h in hits if h["score"] >= MIN_RELEVANT_SCORE]
    if not relevant:
        return (
            f"No notes in the vault currently meet the relevance threshold for "
            f"'{topic}' (best match scored {hits[0]['score']:.2f} if any). "
            f"Ingest more sources on this topic before generating a wiki page — "
            f"a page built from nothing would just be the model's general "
            f"knowledge, not your vault's.",
            [],
        )

    excerpts = "\n\n".join(f"[{h['note_path']}]\n{h['text']}" for h in relevant)
    prompt = SYNTH_PROMPT.format(topic=topic, excerpts=excerpts)
    page = generate(model, prompt)
    sources = sorted({h["note_path"] for h in relevant})
    return page, sources


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("topic")
    ap.add_argument("--model", default="llama3.2", help="Ollama model for synthesis")
    ap.add_argument("--vault", default=".", help="Vault root")
    ap.add_argument("--top", type=int, default=8, help="How many note chunks to consider")
    args = ap.parse_args()

    vault_root = Path(args.vault).resolve()
    print(f"Building wiki page for '{args.topic}'...")

    try:
        page, sources = build_wiki_page(vault_root, args.topic, args.model, args.top)
    except (RuntimeError, OllamaError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if not sources:
        print(page)
        return 0

    slug = slugify(args.topic)
    frontmatter = {
        "title": args.topic,
        "generated_at": now_iso(),
        "sources": sources,
        "model": args.model,
    }
    note_path = vault_root / "wiki" / f"{slug}.md"
    write_note(note_path, frontmatter, page)
    print(f"Wrote wiki page: {note_path.relative_to(vault_root)} (from {len(sources)} source note(s))")

    commit_result = git_commit(vault_root, f"wiki: {args.topic}")
    print(f"Git: {commit_result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
