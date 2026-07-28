#!/usr/bin/env python3
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download

REPO = "DeepSeekOracle/excavationpro-music-stream"
EXTRA = """

## Parquet catalog (agents / DuckDB / Pandas)

Hugging Face may auto-build a Parquet view under `refs/convert/parquet` (dataset viewer).

**Steward catalog Parquet (preferred for queries):**

| Path | Role |
|------|------|
| `catalog/public_stream_playlist.parquet` | Compact track index (~10k rows): title, album, moniker, upc, stream_url, sha256 |
| `public_stream_playlist.json` | Full JSON playlist (source for portal + parquet export) |

```python
from datasets import load_dataset
ds = load_dataset(
    "DeepSeekOracle/excavationpro-music-stream",
    data_files="catalog/public_stream_playlist.parquet",
    split="train",
)
```

Auto branch: https://huggingface.co/datasets/DeepSeekOracle/excavationpro-music-stream/tree/refs%2Fconvert%2Fparquet  
Stack docs: https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/docs/MUSIC_STREAM_PARQUET.md
"""


def main() -> int:
    p = hf_hub_download(REPO, "README.md", repo_type="dataset")
    text = Path(p).read_text(encoding="utf-8")
    if "Parquet catalog" in text or "catalog/public_stream_playlist.parquet" in text:
        print("README already documents Parquet catalog")
        return 0
    text = text.rstrip() + EXTRA + "\n"
    out = Path(__file__).resolve().parents[1] / "data" / "music_catalog" / "HF_DATASET_README.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    HfApi().upload_file(
        path_or_fileobj=str(out),
        path_in_repo="README.md",
        repo_id=REPO,
        repo_type="dataset",
        commit_message="docs: Parquet catalog + refs/convert/parquet",
    )
    print("README updated on HF →", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
