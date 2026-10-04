# Excavationpro Music Stream — Parquet catalog

**Signature:** `Δ9Φ963-MUSIC-PLAYLIST-PARQUET-v1`  
**Dataset:** [DeepSeekOracle/excavationpro-music-stream](https://huggingface.co/datasets/DeepSeekOracle/excavationpro-music-stream)  
**Steward:** Justin Helmer / Excavationpro / Lightfather

## What is Parquet?

Apache Parquet is a **columnar** file format used for:

- lower memory when scanning catalogs  
- fast filter / projection (title, album, moniker, UPC)  
- efficient storage vs giant JSON  

Hugging Face uses Parquet for the **dataset viewer** and for `datasets` / DuckDB / Pandas / Polars loads.

## Two Parquet surfaces

| Surface | Path / ref | Role |
|---------|------------|------|
| **Steward catalog Parquet (canonical for agents)** | `catalog/public_stream_playlist.parquet` on **main** | Compact track index (sha256, title, album, stream_url, …) |
| **HF auto-convert branch** | [`refs/convert/parquet`](https://huggingface.co/datasets/DeepSeekOracle/excavationpro-music-stream/tree/refs%2Fconvert%2Fparquet) | Built by the parquet-converter bot for Hub viewer / unified access |

**Audio streams stay MP3** under `stream/` (flat + sharded). Parquet does **not** replace streams — it indexes them.

If the dataset were already fully Parquet, files under `refs/convert/parquet` would be links to originals. Here, **MP3 + JSON remain source of truth for playback**; Parquet is the **query layer**.

### Auto branch URL

```text
https://huggingface.co/datasets/DeepSeekOracle/excavationpro-music-stream/tree/refs%2Fconvert%2Fparquet
```

Hub docs: [Datasets → Parquet](https://huggingface.co/docs/hub/en/datasets-viewer) · advantages of Parquet on the Hub.

## When agents should use Parquet

| Need | Use |
|------|-----|
| Play audio in browser / listen portal | `stream_url` from playlist / listen HTML |
| Filter 10k+ tracks by album / moniker / UPC | **Parquet** or playlist JSON |
| Dataset viewer on HF | auto `refs/convert/parquet` |
| Offline steward tools | local `data/music_catalog/parquet/public_stream_playlist.parquet` |

## Load examples

### Hugging Face `datasets` (catalog file on main)

```python
from datasets import load_dataset

ds = load_dataset(
    "DeepSeekOracle/excavationpro-music-stream",
    data_files="catalog/public_stream_playlist.parquet",
    split="train",
)
print(ds[0]["title"], ds[0]["stream_url"])
```

### Pandas

```python
import pandas as pd

df = pd.read_parquet(
    "hf://datasets/DeepSeekOracle/excavationpro-music-stream/catalog/public_stream_playlist.parquet"
)
hollow = df[df["album"].str.contains("HOLLOW", case=False, na=False)]
```

### DuckDB

```sql
SELECT title, moniker, stream_url
FROM read_parquet(
  'hf://datasets/DeepSeekOracle/excavationpro-music-stream/catalog/public_stream_playlist.parquet'
)
WHERE album ILIKE '%HOLLOW%' OR upc = '825192882162'
LIMIT 20;
```

### Polars

```python
import polars as pl

df = pl.read_parquet(
    "hf://datasets/DeepSeekOracle/excavationpro-music-stream/catalog/public_stream_playlist.parquet"
)
```

## Rebuild / publish (steward)

```bash
# From lygo-protocol-stack
python tools/export_music_playlist_parquet.py
python tools/export_music_playlist_parquet.py --publish-hf   # consent: HF token
```

Outputs:

| File | Location |
|------|----------|
| Parquet | `data/music_catalog/parquet/public_stream_playlist.parquet` |
| Meta JSON | `data/music_catalog/parquet/public_stream_playlist_parquet_meta.json` |
| Docs mirror | `docs/data/public_stream_playlist.parquet` |
| HF | `catalog/public_stream_playlist.parquet` |

## Columns (catalog parquet)

`sha256`, `title`, `artist`, `album`, `moniker`, `upc`, `size`, `stream_url`, `hf_path`, `isrcs`, `aliases`, `release_date`, `label`

## Related

- Listen portal: https://deepseekoracle.github.io/Excavationpro/excavationpro-listen.html  
- Vault policy: `docs/SOVEREIGN_MUSIC_VAULT.md`  
- Skill map: `lygo-excavationpro-music-lattice` → `references/MUSIC_PORTAL.json`  
- Full playlist JSON (source): `public_stream_playlist.json` on HF main + Pages mirror  

**Δ9Φ963 — streams for ears · parquet for queries · human holds publish.**
