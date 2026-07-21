# Download llama.cpp Windows CUDA release (llama-server)
param(
  [string]$OutDir = "D:\LYGO_HIGHPERF\bin"
)
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$api = "https://api.github.com/repos/ggerganov/llama.cpp/releases/latest"
Write-Host "Fetching latest llama.cpp release..."
$rel = Invoke-RestMethod -Uri $api -Headers @{ "User-Agent" = "LYGO-HIGHPERF" }
Write-Host "Release" $rel.tag_name

# Must start with llama- not cudart-
$asset = $rel.assets | Where-Object { $_.name -match "^llama-.*-bin-win-cuda-12\.4-x64\.zip$" } | Select-Object -First 1
if (-not $asset) {
  $asset = $rel.assets | Where-Object { $_.name -match "^llama-.*-bin-win-cuda-13\.[0-9]+-x64\.zip$" } | Select-Object -First 1
}
if (-not $asset) {
  $asset = $rel.assets | Where-Object { $_.name -match "^llama-.*-bin-win-cuda.*x64\.zip$" } | Select-Object -First 1
}
if (-not $asset) {
  $rel.assets | Where-Object { $_.name -match "win" } | ForEach-Object { Write-Host " -" $_.name }
  throw "No llama win-cuda zip found"
}

$cudart = $rel.assets | Where-Object { $_.name -match "^cudart-llama-bin-win-cuda-12\.4" } | Select-Object -First 1
if (-not $cudart) {
  $cudart = $rel.assets | Where-Object { $_.name -match "^cudart-llama-bin-win-cuda" } | Select-Object -First 1
}

$zip = Join-Path $OutDir $asset.name
Write-Host "Downloading" $asset.name
Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zip -UseBasicParsing

$extract = Join-Path $OutDir "llama-cpp"
if (Test-Path $extract) { Remove-Item $extract -Recurse -Force }
Expand-Archive -Path $zip -DestinationPath $extract -Force

if ($cudart) {
  $czip = Join-Path $OutDir $cudart.name
  if (-not (Test-Path $czip)) {
    Write-Host "Downloading" $cudart.name
    Invoke-WebRequest -Uri $cudart.browser_download_url -OutFile $czip -UseBasicParsing
  }
  $cdir = Join-Path $OutDir "cudart"
  if (Test-Path $cdir) { Remove-Item $cdir -Recurse -Force }
  Expand-Archive -Path $czip -DestinationPath $cdir -Force
  Get-ChildItem $cdir -Recurse -Filter "*.dll" | ForEach-Object { Copy-Item $_.FullName $OutDir -Force }
}

$server = Get-ChildItem $extract -Recurse -Filter "llama-server.exe" | Select-Object -First 1
if (-not $server) { throw "llama-server.exe not found in archive" }
Copy-Item $server.FullName (Join-Path $OutDir "llama-server.exe") -Force
Get-ChildItem $server.DirectoryName -Filter "*.dll" -ErrorAction SilentlyContinue | ForEach-Object {
  Copy-Item $_.FullName $OutDir -Force
}
Get-ChildItem $extract -Recurse -Filter "*.dll" | ForEach-Object {
  Copy-Item $_.FullName $OutDir -Force -ErrorAction SilentlyContinue
}

Write-Host "[OK] llama-server ready"
Write-Host "Asset:" $asset.name
Get-Item (Join-Path $OutDir "llama-server.exe") | Format-List FullName, Length
