# LYGO High-Perf — stage Ollama GGUF blobs as named .gguf (hardlink, zero extra disk)
param(
  [string]$OllamaBlobs = "D:\Ollama\.ollama\models\blobs",
  [string]$ManifestRoot = "D:\Ollama\.ollama\models\manifests\registry.ollama.ai",
  [string]$OutDir = "D:\LYGO_HIGHPERF\models",
  [string]$DefaultModel = "AI-TAVS/Qwen3.6-35b-a3b-Uncensored:35b"
)
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

function Get-OllamaModelBlob([string]$NameTag) {
  # NameTag e.g. AI-TAVS/Qwen3.6-35b-a3b-Uncensored:35b
  $parts = $NameTag -split ":", 2
  $name = $parts[0]
  $tag = if ($parts.Count -gt 1) { $parts[1] } else { "latest" }
  $man = Join-Path $ManifestRoot ($name.Replace("/", "\") + "\$tag")
  if (-not (Test-Path $man)) {
    # try ollama show FROM line
    $mf = & ollama show $NameTag --modelfile 2>$null
    $from = ($mf | Select-String -Pattern "^FROM\s+(.+)$").Matches.Groups[1].Value.Trim()
    if ($from -and (Test-Path $from)) { return $from }
    throw "Manifest not found: $man"
  }
  $j = Get-Content $man -Raw | ConvertFrom-Json
  $layer = $j.layers | Where-Object { $_.mediaType -match "image\.model" } | Select-Object -First 1
  $dig = $layer.digest -replace "sha256:", "sha256-"
  $blob = Join-Path $OllamaBlobs $dig
  if (-not (Test-Path $blob)) { throw "Blob missing: $blob" }
  return $blob
}

function Link-Gguf([string]$Blob, [string]$Name) {
  $dest = Join-Path $OutDir $Name
  if (Test-Path $dest) { Remove-Item $dest -Force }
  try {
    New-Item -ItemType HardLink -Path $dest -Target $Blob | Out-Null
    Write-Host "[OK] hardlink $Name"
  } catch {
    cmd /c mklink "$dest" "$Blob" | Out-Null
    Write-Host "[OK] symlink $Name"
  }
  return $dest
}

Write-Host "=== LYGO High-Perf model staging ==="
Write-Host "Default uncensored: $DefaultModel"
$blob = Get-OllamaModelBlob $DefaultModel
Write-Host "Blob: $blob"
$gguf = Link-Gguf $blob "LYGO-Qwen3.6-35B-A3B-Uncensored-Q4_K_M.gguf"
Write-Host "Staged: $gguf"
Write-Host "Size GB:" ([math]::Round((Get-Item $gguf).Length / 1GB, 2))
Write-Host "Done."
