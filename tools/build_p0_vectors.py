#!/usr/bin/env python3
"""Build protocol0_nano_kernel/fixtures/p0_vectors.json (35+ diverse cases)."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "protocol0_nano_kernel" / "src" / "python"))

from lygo_p0 import validate_bytes  # noqa: E402

OUT = ROOT / "protocol0_nano_kernel" / "fixtures" / "p0_vectors.json"


def v(vid: str, data: bytes, description: str, category: str) -> dict:
    res = validate_bytes(data)
    return {
        "id": vid,
        "category": category,
        "description": description,
        "hex": data.hex(),
        "len": len(data),
        "expected_verdict": res["verdict"],
        "expected_phi_risk": res["phi_risk"],
    }


def main() -> int:
    vectors: list[dict] = []

    vectors.append(v("json_minimal", b'{"a":1,"b":2}', "Minimal JSON object", "canonical"))
    vectors.append(v("null_1k", b"\x00" * 1000, "1 KiB zero padding", "canonical"))
    vectors.append(v("pattern_3byte", (b"\x01\x02\x03" * 1000)[:3000], "Repeating 3-byte pattern", "canonical"))
    vectors.append(v("seq_0_199", bytes(range(200)), "Byte sequence 0..199", "canonical"))
    vectors.append(v("oversize_9000", b"\x00" * 9000, "Over MAX_BYTES", "canonical"))

    for n in [0, 1, 16, 63, 64, 127, 128, 256, 512, 1024, 4096, 8192]:
        vectors.append(v(f"zeros_{n}", b"\x00" * n, f"All zeros length {n}", "boundary"))
    vectors.append(v("at_max_bytes", b"\x55" * 8192, "Exactly MAX_BYTES", "boundary"))

    vectors.append(v("repeat_a_320", b"a" * 320, "Single-byte repeat (text)", "recursive"))
    vectors.append(v("repeat_aaaa_800", b"aaaa" * 200, "4-byte window repeat", "recursive"))
    vectors.append(v("repeat_deadbeef", (b"\xde\xad\xbe\xef" * 120)[:480], "DEADBEEF pattern", "recursive"))
    vectors.append(v("nested_json", (b'{"x":{"y":1}}' * 40)[:640], "Nested JSON multiplied", "recursive"))

    vectors.append(v("all_ff_512", b"\xff" * 512, "Saturated 0xFF", "adversarial"))
    vectors.append(v("alternating_512", bytes([0, 255] * 256), "0x00/0xFF alternation", "adversarial"))
    vectors.append(v("utf8_delta9", "Δ9Φ963-LYGO-テスト".encode(), "UTF-8 mixed scripts", "adversarial"))
    for i in range(6):
        blob = hashlib.sha256(f"lygo-p0-vector-{i}".encode()).digest() * 5
        vectors.append(v(f"hash_entropy_{i}", blob[: 200 + i * 17], f"SHA-derived high entropy #{i}", "high_entropy"))

    for byte, name in [(0x00, "nul"), (0x01, "soh"), (0x7F, "del"), (0x80, "high"), (0xFF, "ff")]:
        vectors.append(v(f"mono_{name}_96", bytes([byte] * 96), f"Monobyte 0x{byte:02x} × 96", "adversarial"))

    vectors.append(v("bmp_like", b"BM" + b"\x00" * 126, "BMP-ish header + padding", "structured"))
    vectors.append(v("pe_like", b"MZ" + b"\x90" * 200, "PE-ish stub", "structured"))
    vectors.append(v("xml_snippet", b"<root><a>1</a><b>2</b></root>" * 8, "XML repetition", "structured"))

    vectors.append(v("seq_0_255", bytes(range(256)), "Full byte alphabet 0-255", "high_entropy"))
    vectors.append(v("seq_128_255", bytes(range(128, 256)), "Upper half byte range", "high_entropy"))
    vectors.append(v("seq_128_255_x4", bytes(range(128, 256)) * 4, "Upper range × 4", "high_entropy"))

    assert len(vectors) >= 30, len(vectors)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": "P0.4",
        "count": len(vectors),
        "categories": sorted({x["category"] for x in vectors}),
        "vectors": vectors,
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(vectors)} vectors → {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())