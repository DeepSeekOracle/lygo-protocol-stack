#!/usr/bin/env bash
# LYGO Protocol Stack — one-click community setup (Linux/macOS)
set -euo pipefail

SIGNATURE="Δ9Φ963-PHASE2-DEPLOYMENT"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

echo "=== LYGO Phase 2 setup ($SIGNATURE) ==="

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 required"; exit 1
fi

python3 -m pip install -q -r requirements.txt
if [[ -f requirements-docker.txt ]]; then
  python3 -m pip install -q -r requirements-docker.txt
fi

python3 tools/generate_falsifiable_vectors.py
python3 -m pytest protocol0_byte_entropy_filter/tests/ -q
python3 tools/verify_alignment_badge.py --format=both

if command -v docker >/dev/null 2>&1 && command -v docker compose >/dev/null 2>&1; then
  echo "Docker detected — building lygo-node image..."
  docker compose build lygo-node
  echo "Start node: docker compose up -d lygo-node"
  echo "Scale workers: docker compose --profile scale up -d"
else
  echo "Docker not found — local Python stack is ready."
  echo "Optional API: python tools/node_api_server.py --host 127.0.0.1 --port 8787"
fi

echo "=== Setup complete ==="