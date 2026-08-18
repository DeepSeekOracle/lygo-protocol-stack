# LYGO Pure-Data Witness

**Design:** [LYGO_PURE_DATA_WITNESS.md](../LYGO_PURE_DATA_WITNESS.md)  
**UI:** [data-vault/pure-data.html](../data-vault/pure-data.html)  
**Registrar:** [data-vault/register.html](../data-vault/register.html)  
**Bot design:** [PURE_DATA_BOT_DESIGN.md](../PURE_DATA_BOT_DESIGN.md)  
**Ledger:** [ledger.json](./ledger.json)  
**ClawHub skill:** `clawhub/mirrors/lygo-pure-data-witness/`

## Register (humans + agents)

```bash
# Safety-gated register → digest + egg + ledger + Star Chart pending
python tools/pure_data_register.py --url https://example.com/page --i-consent
python tools/pure_data_register.py --file ./local.html --i-consent

# Rebuild PDW Star Chart nodes (hub + root + NODE_PDW_* fork chain)
python tools/map_pure_data_to_star_chart.py --json
python tools/build_haven_star_chart.py
```

Skill CLI (no subprocess; star submission JSON only):

```bash
cd clawhub/mirrors/lygo-pure-data-witness
python scripts/self_check.py
python scripts/pdw_cli.py register --url https://example.com --i-authorize-fetch --i-consent
```

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
