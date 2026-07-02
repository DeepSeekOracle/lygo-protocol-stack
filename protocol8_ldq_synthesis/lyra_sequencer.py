"""Block structure generator for LDQ live synthesis."""

from __future__ import annotations


class LYRASequencer:
    def __init__(self, seed_int: int) -> None:
        self.seed_int = int(seed_int) & 0xFFFFFFFFFFFFFFFF

    def generate_structure(self, num_blocks: int = 8) -> list[dict]:
        blocks: list[dict] = []
        for i in range(num_blocks):
            s = (self.seed_int >> (i * 3)) ^ (i * 0x9E3779B9)
            blocks.append(
                {
                    "block": i,
                    "accent": bool(s & 1),
                    "density": 0.25 + ((s >> 1) % 8) / 16.0,
                    "gate": [3, 6, 9][(s >> 4) % 3],
                }
            )
        return blocks