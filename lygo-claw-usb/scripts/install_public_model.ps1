# LYGO CLAW PUBLIC — download a small offline chat model (one-time, needs internet)
# Does NOT ship weights in the repo. Safe for public builds.
# Signature: Delta9Phi963-PUBLIC-MODEL-INSTALL-v1
param(
    [string]$Model = "llama3.2:1b",
    [switch]$AlsoPullQwen
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "bootstrap_env.ps1")
. (Join-Path $PSScriptRoot "resolve_ollama.ps1") -Quiet

if (-not $env:LYGO_OLLAMA_EXE -or -not (Test-Path $env:LYGO_OLLAMA_EXE)) {
    Write-Host ""
    Write-Host "Ollama is not installed."
    Write-Host "  1. Download Windows installer: https://ollama.com/download"
    Write-Host "  2. Install, then re-run this script."
    Write-Host "  Optional portable: place ollama.exe under product\runtime\ollama\"
    exit 1
}

# Ensure serve is up
& (Join-Path $PSScriptRoot "ensure_ollama_serve.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "Pulling model: $Model"
Write-Host "  Models dir: $($env:OLLAMA_MODELS)"
Write-Host "  (May take several minutes; needs internet once.)"
Write-Host ""

& $env:LYGO_OLLAMA_EXE pull $Model
if ($LASTEXITCODE -ne 0) {
    Write-Error "pull failed for $Model"
    exit 1
}

if ($AlsoPullQwen) {
    Write-Host "Also pulling qwen2.5:3b (better quality, larger)..."
    & $env:LYGO_OLLAMA_EXE pull "qwen2.5:3b"
}

# Manifest for agent server primary
$root = Split-Path $PSScriptRoot -Parent
$manifestDir = Join-Path $root "product\models"
New-Item -ItemType Directory -Force -Path $manifestDir | Out-Null
$manifest = [ordered]@{
    signature = "Delta9Phi963-PUBLIC-MODEL-MANIFEST-v1"
    updated_utc = (Get-Date).ToUniversalTime().ToString("o")
    primary = @{ name = $Model }
    fallbacks = @("llama3.2:1b", "qwen2.5:3b")
    note = "Public kit — weights installed locally via ollama pull; not in git."
}
$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $manifestDir "MODEL_MANIFEST.json") -Encoding utf8

Write-Host ""
Write-Host "OK model ready: $Model"
Write-Host "Next: double-click LYGO_USB_BOOT.bat  →  open http://127.0.0.1:9631/"
exit 0
