# Sets $env:LYGO_OLLAMA_EXE (USB portable first, then host PATH)
# Public kit: host Ollama is the default path; portable is optional.
param([switch]$Quiet)
$Key = $env:LYGO_BUILDER_KEY_ROOT
if (-not $Key) {
    $Key = Split-Path -Parent $PSScriptRoot
    $env:LYGO_BUILDER_KEY_ROOT = $Key
}
$portable = Join-Path $Key "product\runtime\ollama\ollama.exe"
if (Test-Path $portable) {
    $env:LYGO_OLLAMA_EXE = $portable
    $dir = Split-Path $portable
    if ($env:PATH -notlike "*$dir*") { $env:PATH = "$dir;$env:PATH" }
} elseif (Get-Command ollama -ErrorAction SilentlyContinue) {
    $env:LYGO_OLLAMA_EXE = (Get-Command ollama).Source
} else {
    $env:LYGO_OLLAMA_EXE = $null
}
if (-not $Quiet) {
    if ($env:LYGO_OLLAMA_EXE) { Write-Host "LYGO_OLLAMA_EXE=$($env:LYGO_OLLAMA_EXE)" }
    else { Write-Warning "No Ollama - install from https://ollama.com/download then run scripts\install_public_model.ps1" }
}
