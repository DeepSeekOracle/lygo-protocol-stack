# Phase 7 — Human-AI Interface Platform (HAIP)

**Signature:** `Δ9Φ963-PHASE7-v1.0`

## Scope

- **Device abstraction** — Apple Watch, Garmin, Oura, custom (simulated until BLE/HealthKit).
- **Biometric pipeline** — multi-device buffer + aggregation.
- **Ethical mapping** — Truth / Love / Freedom → Solfeggio frequency + Light Code.
- **Entropy harness** — IBI detrend → min-entropy estimate → von Neumann debias → HMAC-SHA256 P0 seed.

## Stack

```python
from stack.lygo_stack import deploy_stack

s = deploy_stack("NODE")
s.register_biometric_device("apple_watch", "watch_001", "simulated")
state = s.get_biometric_state()
guidance = s.process_biometric_ethical_query()
```

## Node API (port 8787)

| Method | Path |
|--------|------|
| POST | `/device/register` |
| GET | `/biometric/state` |
| GET | `/biometric/history?seconds=60` |

Optional FastAPI on **8788**: `uvicorn protocol7_human_ai_interface.api:app` (requires `fastapi`).

## Tools

```bash
python tools/register_device.py --type apple_watch --id watch_001 --connection simulated
python tools/simulate_biometric_data.py
python tools/run_phase7_audit.py
python tools/p7_entropy_harness.py --ibi-from simulate
```

## Pending

- BLE GATT 0x180D live driver
- HealthKit / WatchKit bridge
- Mesh gossip of attested biometric weights