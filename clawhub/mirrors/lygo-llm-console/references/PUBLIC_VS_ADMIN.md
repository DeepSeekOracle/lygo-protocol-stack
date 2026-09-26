# Public kit vs admin tree

| | Public (this package, and the site zip) | Admin / steward |
|---|---|---|
| Where | `kit/` here, and <https://chatagent.ca/lygo-llm-console.html> | the steward's own `lygo_llm_console/` checkout and stream-node copies |
| Identity | seeds **your** Soul / Identity / Memory on first run | the steward's own identity and notes |
| Roots | the kit folder (`workspace/`, `save/`) | extra read/write roots, `config/admin.json`, `config/api.json`, vaults, keys |
| Models | none; you supply GGUF and the engine | the steward's own model vaults and CAS |
| Publish | never | the steward's own release process |

What the public kit never carries: `config/admin.json`, `config/api.json`, `config/local.json`,
`save/`, `data/`, `engine/` binaries, model weights, the test fixtures, and any absolute path that
belongs to the steward's machine.

The admin-map-shaped limbs (`steward_map`, `self_check`, `self_seal`) exist in the public limb
registry. Measured on a clean unpacked copy: `steward_map` answers `role: "public_kit"` with
`drives: {}` and only the kit's own read/write roots. There is no steward data on a stranger's machine
for them to return.

If a copy you find mentions operator key folders, unlocked write roots beyond the kit, or vault
paths — it is not the public kit, and it is not this skill's artifact.
