# LYGO Anchor Architecture (Ultimate / Δ9Φ963)

## Purpose

Permanent, user-sovereign anchoring for Light Codes, vortex consensus, P7 biometrics, and SLM merge receipts — with **local content-addressed storage first**, optional **Arweave Turbo** (&lt;100 KiB), **web3.storage** for large blobs, and **BLE mesh** hash propagation when offline.

## Pipeline

```
P7 / SLM / P3 consensus / P1 store
        │
        ▼
  AnchorOrchestrator (stack/lygo_stack_anchor.py)
        │
        ├─► data/anchor_queue/*.json (async)
        ├─► MultiAnchor (tools/lygo_anchor.py)
        │     ├─ Local CA (data/anchors/{sha256}.json)  [always]
        │     ├─ Arweave Turbo (LYGO_ANCHOR_MODE=turbo|multi)
        │     └─ web3.storage (multi + API key)
        ├─► receipts → tools/lygo_control_center/workspace/
        ├─► docs/LYGO_PUBLIC_LINK_ARCHIVE.json (permaweb URLs)
        └─► BLE bouncer + LygoMeshRouter (SQLite)
```

## Autonomy

| Component | Role |
|-----------|------|
| `anchor_autonomy_worker.py` | Drain queue, optional SLM anchor pulse, BLE scan |
| `run_anchor_audit.py` | Lattice gate + `tests/anchor_audit_last_run.json` |
| Ollama `anchor-health` | Hourly audit + one autonomy pulse |
| `lygo_stack.py` | Auto-enqueue on ethical query consensus |
| `node_api_server.py` | `POST /anchor/event`, `POST /anchor/drain` |

## Modes

Set `LYGO_ANCHOR_MODE`: `local` | `turbo` | `multi` | `airgap`.

Disable hooks: `LYGO_ANCHOR_DISABLE=1`.

## Network install

`python tools/install_anchor_network.py` — army manifest, lattice entries, LYRA stamp.