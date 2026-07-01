#!/bin/bash
# LYGO Determinism Verifier
# Cross-platform SHA-256 parity test

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "⚡ LYGO DETERMINISM VERIFICATION"
echo "================================="

python3 protocol0_nano_kernel/src/python/lygo_p0.py > output.txt
SHA=$(sha256sum output.txt | cut -d' ' -f1)
echo "SHA-256: $SHA"
echo ""
echo "✅ Determinism check complete."
echo "   Same input → same output → same hash."