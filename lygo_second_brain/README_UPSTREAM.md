# Second Brain — real, tested, no mythology

A local-first Obsidian vault + scripts that actually ingest sources, build
a searchable index, generate wiki pages, and cross-check answers across
multiple local models. Every script here was tested with mocked model
responses before delivery — the logic is verified; the only thing you
need to add is a running Ollama instance.

## Setup

```bash
# 1. Install Ollama: https://ollama.com/download
ollama pull llama3.2          # or mistral, phi3 — any chat model
ollama pull nomic-embed-text  # required for search.py / wiki_build.py
ollama serve                  # if not already running as a service

# 2. Open this folder as an Obsidian vault (optional but recommended —
#    the folder structure is plain markdown, Obsidian isn't required to
#    use the scripts, just to browse/edit the notes nicely)

# 3. Initialize git so ingests get committed (the "anchor" — just git)
git init
git add -A && git commit -m "init vault"
```

## Folder structure

- `raw/` — drop source files here (.txt, .md, .pdf)
- `permanent/` — atomic notes land here after ingest
- `wiki/` — synthesized topic pages land here
- `archive/` — copies of raw sources, kept after ingest
- `scripts/` — everything below

## Usage

```bash
cd scripts

# Ingest a source into a permanent note
python ingest.py ../raw/paper.pdf --model llama3.2

# Build/refresh the search index over permanent/ and wiki/
python embed_index.py --vault ..

# Search the vault
python search.py "sovereign AI frameworks" --vault ..

# Ask 2+ local models the same question and check if they agree
python consensus.py "What are the risks of agent-managed crypto wallets?" \
  --models llama3.2,mistral,phi3 --vault .. --context-from-vault

# Generate a wiki page — only from what's actually in your vault
python wiki_build.py "second brain" --vault ..
```

## What's real vs. what's honest about its limits

| Script | What it actually does |
|---|---|
| `ingest.py` | Reads a file, asks a local model to extract title/summary/key points/tags as JSON, falls back to storing raw text if the model's output isn't parseable, writes a note, archives the source, commits to git. |
| `embed_index.py` | Chunks your markdown notes by paragraph, embeds each chunk with a local model, stores vectors in a local sqlite file. |
| `search.py` | Embeds your query, computes cosine similarity against every stored chunk, returns the top matches. Real vector search, just simple (no ANN index — fine at personal-vault scale, would need one past ~100k chunks). |
| `consensus.py` | Asks the same question to 2+ models, embeds their answers, flags disagreement via pairwise cosine similarity below a threshold. This is a real self-consistency check, not a placeholder. |
| `wiki_build.py` | Retrieves relevant note chunks and asks a model to synthesize *only* from those — and explicitly refuses to generate a page if nothing in your vault is actually relevant, rather than padding with the model's general knowledge. |

No blockchain, no "P0-P9," no resonance frequencies. "Anchoring" is a git
commit. "Validation" is a size/corruption check. "Consensus" is cosine
similarity between model outputs. Everything here does exactly what it
says and nothing more — verify that yourself by reading the ~250 lines
in `scripts/`, they're short on purpose.
