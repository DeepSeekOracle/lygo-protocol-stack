# Biophase7 Objective — sync live BLE UI into HF Space workspace
$ErrorActionPreference = "Stop"
$Stack = "I:\E Drive\lygo-protocol-stack"
$HF = "I:\E Drive\Hugging face"

Copy-Item -Force "$Stack\tools\live_ble_gradio.py" "$HF\live_ble_gradio.py"
Write-Host "[+] Copied live_ble_gradio.py to Hugging face"

$req = "$HF\requirements.txt"
$needle = "websocket-client"
if (-not (Select-String -Path $req -Pattern $needle -Quiet)) {
    Add-Content -Path $req -Value "websocket-client"
    Write-Host "[+] Added websocket-client to HF requirements.txt"
}

Write-Host ""
Write-Host "Next:"
Write-Host "  1) python $Stack\tools\run_live_ble_pipeline.py [--simulate-stream]"
Write-Host "  2) Tunnel :8788 -> set HF secret LYGO_BLE_WS_URL=wss://..."
Write-Host "  3) Push HF Space (huggingface.co/spaces/DeepSeekOracle/LYGO-Resonance-Engine)"
Write-Host "  Docs: $Stack\docs\BIOPHASE7_OBJECTIVE_LIVE_BLE.md"