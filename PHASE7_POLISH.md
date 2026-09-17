# Phase 7 Polish — BLE + Live Harness

**Signatures:** `Δ9Φ963-P6-POLISH-v1.0` · `Δ9Φ963-PHASE7-POLISH-v1.0` · `Δ9Φ963-PHASE7-BLE-LIVE-HARNESS`

## P6 hardening

- `AttestationService.verify_badge_detailed()` — P0 match, HMAC, ethical gate, freshness
- `tools/verify_attestation_hardened.py` — `--local` or `--peer`

## P7 live BLE

```bash
pip install -r requirements-p7-ble.txt
python tools/run_live_ble_pipeline.py              # BLE + ws://0.0.0.0:8788 (tunnel → HF)
python tools/run_live_ble_pipeline.py --simulate-stream
python tools/live_ble_telemetry_ingest.py --simulate
python tools/lygo_control_center/websocket_server.py   # legacy harness :8790
```

- Seed file: `tools/lygo_control_center/workspace/latest_seed.json`
- Node API: `GET /biometric/live_seed`
- **Biophase7 Objective:** `docs/BIOPHASE7_OBJECTIVE_LIVE_BLE.md` — HF secret `LYGO_BLE_WS_URL`
- Harness page: `ws://127.0.0.1:8790` or public `ws://0.0.0.0:8788` with event stream

## Audits

```bash
python tools/run_phase6_audit.py   # includes P6-06 ethical gate
python tools/run_phase7_audit.py   # includes P7-08..P7-11 polish vectors
```