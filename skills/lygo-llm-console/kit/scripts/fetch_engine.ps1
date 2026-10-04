# Optional. Offline-first boot does not call this.
# CPU zip only. Pinned tag after first successful GamePC fetch.
$ErrorActionPreference = "Stop"
$Tag = if ($env:LYGO_LLAMA_TAG) { $env:LYGO_LLAMA_TAG } else { "b10988" }
$Dest = Join-Path $PSScriptRoot "..\engine"
New-Item -ItemType Directory -Force -Path $Dest | Out-Null
if ($Tag -eq "PIN_AFTER_FETCH") {
  Write-Host "Set LYGO_LLAMA_TAG to a ggml-org/llama.cpp release tag, then re-run."
  exit 2
}
$headers = @{ "User-Agent" = "LYGO-LLM-CONSOLE" }
$rel = Invoke-RestMethod -Headers $headers -Uri "https://api.github.com/repos/ggerganov/llama.cpp/releases/tags/$Tag"
$asset = $rel.assets | Where-Object { $_.name -match '^llama-.*-bin-win-cpu-x64\.zip$' } | Select-Object -First 1
if (-not $asset) { throw "no CPU zip on $Tag" }
$zip = Join-Path $env:TEMP $asset.name
Invoke-WebRequest -Headers $headers -Uri $asset.browser_download_url -OutFile $zip
Expand-Archive -Path $zip -DestinationPath $Dest -Force
Write-Host "engine extracted to $Dest"
