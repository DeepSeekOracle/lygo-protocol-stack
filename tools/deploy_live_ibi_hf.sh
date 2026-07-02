#!/usr/bin/env bash
set -euo pipefail
STACK="$(cd "$(dirname "$0")/.." && pwd)"
HF="${LYGO_HF_ROOT:-$STACK/../Hugging face}"
cp -f "$STACK/tools/live_ble_gradio.py" "$HF/live_ble_gradio.py"
grep -q websocket-client "$HF/requirements.txt" 2>/dev/null || echo websocket-client >> "$HF/requirements.txt"
echo "[+] Synced live_ble_gradio.py"
echo "Run: python $STACK/tools/run_live_ble_pipeline.py"
echo "Set HF secret LYGO_BLE_WS_URL=wss://your-tunnel"