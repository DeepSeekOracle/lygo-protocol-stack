# Biophase7 Objective — Live BLE → HF Space

**Source:** `LYRA SYSTEM RETORE/.../2026Biophase7/🧬 Objective.txt`  
**Signature:** `Δ9Φ963-PHASE7-BLE-LIVE-HARNESS` · `Δ9Φ963-PHASE7-LIVE-STREAM-v1`

## What ships

| Piece | Path |
|-------|------|
| BLE GATT ingest | `tools/live_ble_telemetry_ingest.py` |
| WebSocket hub (8788 public) | `tools/ble_ws_broadcast_server.py` |
| Shared live state | `protocol7_human_ai_interface/live_stream_hub.py` |
| One-command start | `tools/run_live_ble_pipeline.py` |
| HF Gradio consumer | `tools/live_ble_gradio.py` + HF `live_ble_gradio.py` |
| Harness (local) | `ws://127.0.0.1:8790` via `tools/lygo_control_center/websocket_server.py` |

## Cloud ↔ local fix (required for HF)

Hugging Face runs in the cloud. **`localhost:8788` inside the Space is not your laptop.**

1. On the LYGO node: `python tools/run_live_ble_pipeline.py` (or `--simulate-stream` without hardware).
2. Expose **port 8788** with **Cloudflare Tunnel** or **ngrok** → `wss://…`.
3. HF Space secret: `LYGO_BLE_WS_URL=wss://your-tunnel-host/…`
4. Open Space → **Phase 7** → **Live BLE stream** → connect (or rely on secret URL).

## Local verification

```powershell
cd "I:\E Drive\lygo-protocol-stack"
pip install -r requirements-p7-ble.txt
python tools/live_ble_telemetry_ingest.py --simulate
python tools/run_live_ble_pipeline.py --simulate-stream
# In another shell: wscat -c ws://127.0.0.1:8788
```

| Check | Expected |
|-------|----------|
| BLE found | `[+] Candidate: …` |
| IBI | `[+] IBI: …ms \| buffer n/64` |
| WS | `LYGO BLE WebSocket ws://0.0.0.0:8788` |
| Seed | After 64 IBIs: `H_min=… seed=…` |

## Anchor hook

When a seed is generated, `latest_seed.json` is written under `tools/lygo_control_center/workspace/`. Node API: `GET /biometric/live_seed`. Optional anchor drain via existing stack anchor worker.

## Deploy HF

```powershell
.\tools\deploy_live_ibi_hf.ps1
```

Copies `live_ble_gradio.py` into `I:\E Drive\Hugging face\` and documents push steps (human `git push` to Space repo if not automated).