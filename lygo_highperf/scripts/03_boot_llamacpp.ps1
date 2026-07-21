# LYGO High-Perf - boot llama-server OpenAI API on :8000
# Default: uncensored Qwen3.6-35B-A3B Q4_K_M (from Ollama AI-TAVS)
param(
  [string]$Root = "D:\LYGO_HIGHPERF",
  [int]$Port = 8000,
  [int]$Ctx = 8192,
  [int]$GpuLayers = 99,
  [int]$Parallel = 2,
  [string]$Model = "LYGO-Qwen3.6-35B-A3B-Uncensored-Q4_K_M.gguf"
)
$ErrorActionPreference = "Stop"
$binDir = Join-Path $Root "bin"
$bin = Join-Path $binDir "llama-server.exe"
$gguf = Join-Path $Root "models\$Model"
$log = Join-Path $Root ("logs\llamacpp_{0:yyyyMMdd_HHmmss}.log" -f (Get-Date))

if (-not (Test-Path $gguf)) {
  Write-Host "Staging model..."
  & (Join-Path $Root "scripts\01_stage_models.ps1")
}
if (-not (Test-Path $bin)) {
  Write-Host "Downloading llama-server..."
  & (Join-Path $Root "scripts\02_download_llama_server.ps1")
}
# ensure impl dll beside exe
$impl = Join-Path $binDir "llama-server-impl.dll"
if (-not (Test-Path $impl) -and (Test-Path (Join-Path $binDir "llama-cpp\llama-server-impl.dll"))) {
  Copy-Item (Join-Path $binDir "llama-cpp\llama-server-impl.dll") $binDir -Force
  Get-ChildItem (Join-Path $binDir "llama-cpp") -Filter "*.dll" | Copy-Item -Destination $binDir -Force
}

if (-not (Test-Path $bin)) { throw "llama-server.exe missing" }
if (-not (Test-Path $gguf)) { throw "GGUF missing: $gguf" }

# stop previous
Get-Process -Name "llama-server" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1

# Disable Qwen thinking so content is not empty (OpenClaw needs message.content)
$env:LLAMA_ARG_CHAT_TEMPLATE_KWARGS = '{"enable_thinking":false}'
$env:LLAMA_ARG_REASONING = "off"

$argList = @(
  "-m", $gguf,
  "--host", "127.0.0.1",
  "--port", "$Port",
  "-c", "$Ctx",
  "-ngl", "$GpuLayers",
  "-np", "$Parallel",
  "-cb",
  "-fa", "on",
  "-t", "8",
  "--jinja",
  "--reasoning", "off",
  "--metrics",
  "--alias", "lygo-qwen-uncensored"
)

Write-Host "================================================"
Write-Host " LYGO HIGH-PERF  (llama.cpp server)"
Write-Host " Model: $Model"
Write-Host " API:   http://127.0.0.1:$Port/v1"
Write-Host " Key:   lygo-local"
Write-Host " GPU layers: $GpuLayers  ctx: $Ctx  slots: $Parallel"
Write-Host " Log:   $log"
Write-Host "================================================"
Write-Host "OpenClaw env:"
Write-Host "  OPENAI_BASE_URL=http://127.0.0.1:$Port/v1"
Write-Host "  OPENAI_API_KEY=lygo-local"
Write-Host ""

New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
$p = Start-Process -FilePath $bin -ArgumentList $argList -WorkingDirectory $binDir -PassThru -WindowStyle Minimized -RedirectStandardOutput $log -RedirectStandardError "$log.err"
Write-Host "PID" $p.Id

$ok = $false
for ($i = 0; $i -lt 120; $i++) {
  Start-Sleep -Seconds 3
  if ($p.HasExited) {
    Write-Host "EXITED code" $p.ExitCode
    Write-Host "--- stdout ---"; Get-Content $log -Tail 50 -ErrorAction SilentlyContinue
    Write-Host "--- stderr ---"; Get-Content "$log.err" -Tail 50 -ErrorAction SilentlyContinue
    exit 1
  }
  try {
    $r = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/v1/models" -TimeoutSec 3
    Write-Host "[READY] " (($r.data | ForEach-Object { $_.id }) -join ", ")
    $ok = $true
    break
  } catch {
    if (($i % 5) -eq 0) { Write-Host "loading... $i (first load of 21GB may take several minutes)" }
  }
}
if (-not $ok) { Write-Host "Timeout - see $log"; exit 1 }

$modelId = (Invoke-RestMethod "http://127.0.0.1:$Port/v1/models").data[0].id
$body = @{
  model = $modelId
  messages = @(@{ role = "user"; content = "Reply with exactly: LYGO_OK" })
  max_tokens = 48
  temperature = 0.2
} | ConvertTo-Json -Depth 6
try {
  $chat = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/v1/chat/completions" -Method Post -Body $body -ContentType "application/json" -Headers @{ Authorization = "Bearer lygo-local" } -TimeoutSec 300
  Write-Host "SMOKE:" $chat.choices[0].message.content
} catch {
  Write-Host "SMOKE warn:" $_.Exception.Message
  if ($_.ErrorDetails) { Write-Host $_.ErrorDetails.Message }
}

Write-Host ""
Write-Host "Server running. Stop:  .\scripts\99_stop.ps1"
Write-Host "Replace Ollama URL in OpenClaw with http://127.0.0.1:$Port/v1"
