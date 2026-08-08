# Continuum quickstart

```bash
python scripts/self_check.py
python scripts/continuum.py demo
```

## Seal a real task

`claims.json`:

```json
[
  {"id": "c1", "kind": "file_exists", "path": "README.md"},
  {"id": "c2", "kind": "file_sha256", "path": "README.md"},
  {"id": "c3", "kind": "file_contains", "path": "README.md", "needle": "Continuum"}
]
```

```bash
python scripts/continuum.py seal --claims claims.json --task "Document continuum" --base . --out capsule.json
python scripts/continuum.py verify --capsule capsule.json --base .
python scripts/continuum.py handoff --capsule capsule.json --verify --base .
```

## Portal

Open https://chatagent.ca/lygo-continuum.html — paste capsule, drop files, see HOLDS/BROKEN.
