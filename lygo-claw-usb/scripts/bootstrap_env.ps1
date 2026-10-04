# LYGO CLAW PUBLIC USB — session env (no secrets, no models shipped)
$Key = Split-Path -Parent $PSScriptRoot
if ($env:LYGO_BUILDER_KEY_ROOT -and (Test-Path $env:LYGO_BUILDER_KEY_ROOT)) {
    $Key = $env:LYGO_BUILDER_KEY_ROOT.TrimEnd('\', '/')
}

$UsbModels = Join-Path $Key "product\models\ollama"
if (-not (Test-Path (Join-Path $UsbModels "blobs"))) {
    $alt = Join-Path $Key "models\ollama"
    if (Test-Path (Join-Path $alt "blobs")) { $UsbModels = $alt }
}

# Optional lattice stack if present on host (never required for chat)
$prefer = $null
if ($env:LYGO_STACK_ROOT -and (Test-Path (Join-Path $env:LYGO_STACK_ROOT "docs"))) {
    $prefer = $env:LYGO_STACK_ROOT
} elseif (Test-Path "D:\lygo-protocol-stack\docs") {
    $prefer = "D:\lygo-protocol-stack"
} elseif (Test-Path (Join-Path $Key "stack\lygo-protocol-stack\docs")) {
    $prefer = Join-Path $Key "stack\lygo-protocol-stack"
}

$env:LYGO_BUILDER_KEY_ROOT = $Key
if ($prefer) { $env:LYGO_STACK_ROOT = $prefer }
$env:OLLAMA_MODELS = $UsbModels
$env:OLLAMA_HOST = if ($env:OLLAMA_HOST) { $env:OLLAMA_HOST } else { "127.0.0.1:11434" }
if (-not $env:OLLAMA_ORIGINS -or $env:OLLAMA_ORIGINS -match 'null|file:') {
    $env:OLLAMA_ORIGINS = "*,http://127.0.0.1,http://localhost,http://127.0.0.1:9631,http://localhost:9631"
}
if (-not $env:OLLAMA_KEEP_ALIVE -or $env:OLLAMA_KEEP_ALIVE -match '^\d+$') {
    $env:OLLAMA_KEEP_ALIVE = "30m"
}

New-Item -ItemType Directory -Force -Path $UsbModels | Out-Null
. (Join-Path $PSScriptRoot "resolve_ollama.ps1") -Quiet
Write-Host "LYGO_BUILDER_KEY_ROOT=$Key"
if ($prefer) { Write-Host "LYGO_STACK_ROOT=$prefer" } else { Write-Host "LYGO_STACK_ROOT=(none — chat still works)" }
Write-Host "OLLAMA_MODELS=$UsbModels"
if ($env:LYGO_OLLAMA_EXE) { Write-Host "LYGO_OLLAMA_EXE=$($env:LYGO_OLLAMA_EXE)" }
