# LYGO — local OpenAI-compatible API for OpenClaw (Qwen uncensored)
# Plug-in: OPENAI_BASE_URL=http://127.0.0.1:8787/v1  OPENAI_API_KEY=ollama
param(
  [string]$Model = "AI-TAVS/Qwen3.6-35b-a3b-Uncensored:35b",
  [int]$Port = 8787
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pkg = Join-Path $root "lygo-qwen-uncensored-api"
$env:OLLAMA_MODEL = $Model
$env:BRIDGE_PORT = "$Port"
$env:OLLAMA_BASE = "http://127.0.0.1:11434"

Write-Host "Checking Ollama on 11434..."
try {
  Invoke-RestMethod -Uri "$($env:OLLAMA_BASE)/api/tags" -TimeoutSec 5 | Out-Null
} catch {
  Write-Host "ERROR: Start Ollama first (system tray or 'ollama serve')."
  exit 1
}

# Ensure model present
$tags = (Invoke-RestMethod -Uri "$($env:OLLAMA_BASE)/api/tags").models | ForEach-Object { $_.name }
if ($tags -notcontains $Model -and -not ($tags | Where-Object { $_ -like "AI-TAVS/Qwen3.6*" })) {
  Write-Host "Pulling $Model ..."
  ollama pull $Model
}

Write-Host ""
Write-Host "========================================"
Write-Host " LYGO Uncensored OpenAI API (local)"
Write-Host " BASE:  http://127.0.0.1:$Port/v1"
Write-Host " KEY:   ollama"
Write-Host " MODEL: $Model"
Write-Host "========================================"
Write-Host "OpenClaw / gateway env:"
Write-Host "  OPENAI_BASE_URL=http://127.0.0.1:$Port/v1"
Write-Host "  OPENAI_API_KEY=ollama"
Write-Host "  model id = $Model  OR  lygo-qwen-uncensored (alias in clients)"
Write-Host ""
Write-Host "HF model card: https://huggingface.co/DeepSeekOracle/LYGO-Qwen3.6-35B-Uncensored-OpenClaw"
Write-Host "Remote Docker Space needs HF PRO + GPU — see OPENCLAW_HF_API.md"
Write-Host ""

Set-Location $pkg
python -m app.local_ollama_bridge
