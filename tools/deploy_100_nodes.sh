#!/usr/bin/env bash
# LYGO Phase 5 — live mesh cluster (100 nodes, ports 8700–8799)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
NODES="${NODES:-100}"
BASE_PORT="${BASE_PORT:-8700}"
HOST="${HOST:-127.0.0.1}"
echo "Δ9Φ963-PHASE5-LIVE-DEPLOYMENT — starting ${NODES} nodes"
python tools/deploy_mesh_cluster.py start --nodes "$NODES" --base-port "$BASE_PORT" --host "$HOST"
echo "Monitor: python tools/monitor_convergence.py --base-port $BASE_PORT --nodes $NODES"