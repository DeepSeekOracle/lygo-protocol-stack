# Start Ollama if not already reachable. Public kit: host install or portable.
# Signature: Delta9Phi963-ENSURE-OLLAMA-PUBLIC-v1
$ErrorActionPreference = "SilentlyContinue"
. (Join-Path $PSScriptRoot "bootstrap_env.ps1")
. (Join-Path $PSScriptRoot "resolve_ollama.ps1") -Quiet

if (-not $env:LYGO_OLLAMA_EXE -or -not (Test-Path $env:LYGO_OLLAMA_EXE)) {
    Write-Error "No ollama.exe found. Install Ollama: https://ollama.com/download  then re-run, or place portable ollama.exe under product\runtime\ollama\"
    exit 1
}

$hostAddr = $env:OLLAMA_HOST
if (-not $hostAddr) { $hostAddr = "127.0.0.1:11434" }
$hostAddr = $hostAddr -replace '^https?://', ''
$env:OLLAMA_HOST = $hostAddr

$root = Split-Path $PSScriptRoot -Parent
if (-not $env:OLLAMA_MODELS) {
    $productModels = Join-Path $root "product\models\ollama"
    $usbModels = Join-Path $root "models\ollama"
    if (Test-Path (Join-Path $productModels "blobs")) {
        $env:OLLAMA_MODELS = $productModels
    } else {
        $env:OLLAMA_MODELS = $productModels
        New-Item -ItemType Directory -Force -Path $productModels | Out-Null
    }
}

function Test-OllamaReady {
    param([string]$Addr)
    try {
        Invoke-RestMethod -Uri "http://$Addr/api/tags" -TimeoutSec 2 | Out-Null
        return $true
    } catch {
        return $false
    }
}

if (Test-OllamaReady $hostAddr) {
    Write-Host "Ollama already up at http://$hostAddr"
    exit 0
}

Write-Host "Starting Ollama serve"
Write-Host "  EXE:    $($env:LYGO_OLLAMA_EXE)"
Write-Host "  MODELS: $($env:OLLAMA_MODELS)"
Write-Host "  HOST:   $hostAddr"

# Modern Ollama: no null/file: origins
$env:OLLAMA_ORIGINS = "*,http://127.0.0.1,http://localhost,http://127.0.0.1:9631,http://localhost:9631"
if (-not $env:OLLAMA_KEEP_ALIVE -or $env:OLLAMA_KEEP_ALIVE -match '^\d+$') {
    $env:OLLAMA_KEEP_ALIVE = "30m"
}
if (-not $env:OLLAMA_NUM_PARALLEL) { $env:OLLAMA_NUM_PARALLEL = "1" }

$exeDir = Split-Path $env:LYGO_OLLAMA_EXE -Parent
$logDir = Join-Path $root "verify\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$outLog = Join-Path $logDir "ollama_serve.out.log"
$errLog = Join-Path $logDir "ollama_serve.err.log"

$p = Start-Process -FilePath $env:LYGO_OLLAMA_EXE `
    -ArgumentList "serve" `
    -WorkingDirectory $exeDir `
    -WindowStyle Hidden `
    -RedirectStandardOutput $outLog `
    -RedirectStandardError $errLog `
    -PassThru

Write-Host "  PID:    $($p.Id)"

$ready = $false
for ($i = 0; $i -lt 45; $i++) {
    Start-Sleep -Seconds 1
    if (Test-OllamaReady $hostAddr) {
        $ready = $true
        break
    }
    if ($p.HasExited) {
        Write-Host "  ollama process exited code=$($p.ExitCode)"
        break
    }
}

if ($ready) {
    Write-Host "Ollama ready at http://$hostAddr"
    exit 0
}

Write-Host "--- ollama stderr (tail) ---"
if (Test-Path $errLog) { Get-Content $errLog -Tail 30 }
Write-Error "Ollama failed to become ready on $hostAddr"
exit 1
