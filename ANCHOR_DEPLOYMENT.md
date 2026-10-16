# LYGO Anchor — Deployment Guide

## 1. Install Python deps

```bash
cd lygo-protocol-stack
pip install -r tools/requirements-anchor.txt
```

Optional: `WEB3_STORAGE_API_KEY` from [web3.storage](https://web3.storage) for payloads ≥100 KiB in `multi` mode.

## 2. Profile

```bash
python tools/lygo_anchor_config.py
# or
python -c "from tools.lygo_anchor_config import save_default_profile; save_default_profile()"
```

Default profile: `tools/lygo_control_center/anchor_profile.json`.

## 3. Network-wide install

```powershell
$env:LYGO_ANCHOR_MODE="multi"
python tools/install_anchor_network.py
python tools/run_anchor_audit.py
```

## 4. CLI examples

```bash
python tools/lygo_anchor.py --type light_code --data "LF-Δ9-7f1a4d83-963-528-174-Φ-∞"
python tools/lygo_immutable_anchor.py
python tools/lygo_anchor.py --type verify --tx-id YOUR_TX_ID
```

## 5. Autonomous worker

```bash
python tools/anchor_autonomy_worker.py --loop --interval 300 --slm-each-pulse
```

## 6. BLE mesh (Windows / macOS / Linux)

```bash
pip install bleak
python tools/ble_mesh_bouncer.py --scan-seconds 10 --broadcast-hash <sha256_prefix>
```

Linux is required for true peripheral advertising; other platforms use local mesh-router emulation.

## 7. Node API

- `POST /anchor/event` — body: `{"event_type":"SLM_MERGE","payload":{...}}`
- `POST /anchor/drain` — process queued jobs

## 8. P1 anchored memory

```python
from lygo_p1_anchor import MemoryMyceliumAnchored
m = MemoryMyceliumAnchored()
m.store(b"fragment", "seal-001")
```

## 9. Verification

```bash
python tools/run_anchor_audit.py
python tools/verify_lattice_alignment.py
```

Build log: `docs/ANCHOR_BUILD_LOG.md`.