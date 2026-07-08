# P0 vector manifest (42) — for @grok review

Regenerate: `python tools/build_p0_vectors.py`

| Category | IDs (count) |
|----------|-------------|
| canonical | `json_minimal`, `null_1k`, `pattern_3byte`, `seq_0_199`, `oversize_9000` (5) |
| boundary | `zeros_0` … `zeros_8192`, `at_max_bytes` (13) |
| recursive | `repeat_a_320`, `repeat_aaaa_800`, `repeat_deadbeef`, `nested_json` (4) |
| adversarial | `all_ff_512`, `alternating_512`, `utf8_delta9`, `mono_*_96` ×5 (8) |
| high_entropy | `hash_entropy_0`…`5`, `seq_0_255`, `seq_128_255`, `seq_128_255_x4` (9) |
| structured | `bmp_like`, `pe_like`, `xml_snippet` (3) |

**Golden SHA-256** (canonical lines, Python ≡ Rust):

`7e8d18fda979cbefec14c3fc86f43f2a020b494b6052acccb6f865f2b4fae1d3`

**Demo one-liner:**

```bash
python tools/run_p0_demo.py --id json_minimal
```