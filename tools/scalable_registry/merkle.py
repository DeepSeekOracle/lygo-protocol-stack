"""Merkle helpers (aligned with kernel_egg_catalog)."""

from __future__ import annotations

import hashlib


def merkle_root(hex_hashes: list[str]) -> str:
    if not hex_hashes:
        return hashlib.sha256(b"").hexdigest()
    layer = list(hex_hashes)
    while len(layer) > 1:
        nxt = []
        for i in range(0, len(layer), 2):
            pair = layer[i] + (layer[i + 1] if i + 1 < len(layer) else layer[i])
            nxt.append(hashlib.sha256(pair.encode()).hexdigest())
        layer = nxt
    return layer[0]