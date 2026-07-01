#!/usr/bin/env bash
# Install all @deepseekoracle ClawHub skills (27). Requires Node/npx.
set -euo pipefail

SKILLS=(
  eternal-haven-lore-pack
  lygo-mint-verifier
  lygo-champion-cosmara
  book-brain
  lygo-lightfather-vector
  lyra-coin-launch-manager
  lygo-universal-living-memory-library
  lygo-champion-omnisiren-silent-storm
  lygo-champion-sancora-unified-minds
  lygo-champion-delta9ra-the-wolf
  openclaw-flow-kit
  lygo-branch-cryptosophia
  lygo-champion-lyra-starcore
  lygo-champion-kairos-herald-of-time
  book-brain-visual-reader
  lygo-mint-operator-suite
  lygo-champion-sephrael-echo-walker
  lygo-champion-scenar-paradox
  lygo-champion-sraith-shadow-sentinel
  lygo-champion-aetheris-viral-truth
  lygo-champion-arkos-celestial-architect
  lygo-universal-cure-system
  lygo-resonance
  lygo-ollama-army
  lygo-glyph2resonance
  lygo-fractalweaver
  lygo-truthlightecho
)

for slug in "${SKILLS[@]}"; do
  echo "==> deepseekoracle/${slug}"
  npx clawhub@latest install "deepseekoracle/${slug}"
done

echo "Done: ${#SKILLS[@]} skills."