#!/usr/bin/env python3
"""consensus.py — ask the same question to 2+ local models and flag disagreement.

This is the real, working version of "P3 Vortex Consensus": no mysticism,
just self-consistency checking. Multiple models answering the same
question and disagreeing is a genuine signal that the answer isn't solid
enough to trust blindly — a real, well-known technique for reducing
single-model hallucination.

Usage:
    python scripts/consensus.py "What are the tradeoffs of local vs cloud LLMs?"
    python scripts/consensus.py "..." --models llama3.2,mistral,phi3
    python scripts/consensus.py "..." --context-from-vault   # pulls relevant notes in first
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ollama_client import generate, embed, OllamaError  # noqa: E402
from search import cosine_similarity, search as vault_search  # noqa: E402
from embed_index import DEFAULT_EMBED_MODEL  # noqa: E402

DISAGREEMENT_THRESHOLD = 0.80  # below this pairwise similarity, flag for human review


def ask_all(question: str, models: list[str], context: str = "") -> dict[str, str]:
    prompt = question if not context else (
        f"Use the following notes as context if relevant. If they don't help, ignore them.\n\n"
        f"CONTEXT:\n{context}\n\nQUESTION:\n{question}"
    )
    answers = {}
    for model in models:
        print(f"  Asking {model}...")
        try:
            answers[model] = generate(model, prompt)
        except OllamaError as e:
            print(f"    SKIP {model}: {e}", file=sys.stderr)
    return answers


def pairwise_agreement(answers: dict[str, str], embed_model: str = DEFAULT_EMBED_MODEL) -> tuple[float, list[tuple]]:
    """Returns (min_pairwise_similarity, list of (model_a, model_b, score))."""
    models = list(answers.keys())
    vectors = {}
    for m in models:
        try:
            vectors[m] = embed(embed_model, answers[m])
        except OllamaError as e:
            print(f"  Could not embed {m}'s answer for comparison: {e}", file=sys.stderr)

    pairs = []
    for i in range(len(models)):
        for j in range(i + 1, len(models)):
            a, b = models[i], models[j]
            if a in vectors and b in vectors:
                score = cosine_similarity(vectors[a], vectors[b])
                pairs.append((a, b, score))

    if not pairs:
        return 1.0, []
    min_score = min(p[2] for p in pairs)
    return min_score, pairs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("question")
    ap.add_argument("--models", default="llama3.2,mistral,phi3", help="Comma-separated Ollama model names")
    ap.add_argument("--vault", default=".", help="Vault root")
    ap.add_argument("--context-from-vault", action="store_true",
                     help="Pull top-3 relevant notes from the vault index as context")
    args = ap.parse_args()

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    if len(models) < 2:
        print("ERROR: need at least 2 models to check agreement.", file=sys.stderr)
        return 1

    context = ""
    if args.context_from_vault:
        vault_root = Path(args.vault).resolve()
        try:
            hits = vault_search(vault_root, args.question, top=3)
            context = "\n\n".join(f"[{h['note_path']}]\n{h['text']}" for h in hits)
            print(f"Pulled {len(hits)} relevant note chunk(s) from the vault as context.")
        except FileNotFoundError:
            print("No vault index found — proceeding without context. Run embed_index.py first.")

    print(f"\nAsking {len(models)} model(s): {', '.join(models)}\n")
    answers = ask_all(args.question, models, context)

    if len(answers) < 2:
        print("ERROR: fewer than 2 models responded successfully — can't check agreement.", file=sys.stderr)
        return 1

    for model, answer in answers.items():
        print(f"\n--- {model} ---\n{answer.strip()}")

    min_score, pairs = pairwise_agreement(answers)
    print("\n--- Agreement ---")
    for a, b, score in pairs:
        flag = "  <-- LOW AGREEMENT" if score < DISAGREEMENT_THRESHOLD else ""
        print(f"  {a} vs {b}: {score:.3f}{flag}")

    if min_score < DISAGREEMENT_THRESHOLD:
        print(f"\n⚠ Models disagree (min similarity {min_score:.3f} < {DISAGREEMENT_THRESHOLD}). "
              f"Treat this answer as unresolved — review manually before saving it as a note.")
    else:
        print(f"\n✓ Models agree (min similarity {min_score:.3f}). Still worth a skim before saving.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
