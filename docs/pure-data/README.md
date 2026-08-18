# LYGO Pure-Data Witness

**Design:** [LYGO_PURE_DATA_WITNESS.md](../LYGO_PURE_DATA_WITNESS.md)  
**UI:** [data-vault/pure-data.html](../data-vault/pure-data.html)  
**Ledger:** [ledger.json](./ledger.json)

## Commands

```bash
python tools/pure_data_witness.py fetch --url https://example.com/page
python tools/pure_data_witness.py digest --file ./local.html
python tools/pure_data_witness.py egg --card data/pure_data/PDW-….json
python tools/pure_data_witness.py continuum-claims --card data/pure_data/PDW-….json
python tools/pure_data_witness.py all --url https://example.com/page
python tools/pure_data_witness.py ledger
python tools/pure_data_witness.py verify --card data/pure_data/PDW-….json
python tools/pure_data_witness.py hf-pack
```

HF pack output: `data/pure_data/hf_pack/` — upload as a public dataset when ready (digests + redacted text; no secrets).

## Continuum

```bash
python path/to/continuum.py seal --claims data/continuum/pdw_system_claims.json --base . --out data/continuum/pdw_system_capsule.json --i-consent
```
