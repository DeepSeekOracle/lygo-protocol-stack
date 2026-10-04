# Agent / steward helper: assemble a LYGO CLAW PUBLIC USB folder from this kit.
# Copies kit → target stick path. NEVER copies model blobs unless -IncludeModels.
# Signature: Delta9Phi963-BUILD-PUBLIC-USB-v1
param(
    [Parameter(Mandatory = $true)]
    [string]$OutDir,
    [switch]$IncludeModels,
    [switch]$OpenExplorer
)

$ErrorActionPreference = "Stop"
$KitRoot = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $KitRoot "LYGO_USB_BOOT.bat"))) {
    # when script lives in kit\scripts
    if (-not (Test-Path (Join-Path $KitRoot "scripts\lygo_usb_agent_server.py"))) {
        throw "Kit root not found near $PSScriptRoot"
    }
}

$OutDir = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutDir)
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

Write-Host "Building LYGO CLAW PUBLIC USB"
Write-Host "  From: $KitRoot"
Write-Host "  To:   $OutDir"

$excludeDirs = @(
    '\.git\',
    '\\product\\models\\ollama\\blobs\\',
    '\\models\\ollama\\blobs\\',
    '\\product\\runtime\\ollama\\lib\\',
    '\\verify\\logs\\'
)

function ShouldSkip([string]$full) {
    $n = $full.ToLowerInvariant().Replace('/', '\')
    foreach ($e in $excludeDirs) {
        if ($n -like "*$($e.ToLowerInvariant())*") { return $true }
    }
    if (-not $IncludeModels) {
        if ($n -match '\\blobs\\' -and $n -match 'ollama') { return $true }
        if ($n -match 'ollama\.exe$') { return $true }
    }
    return $false
}

$copied = 0
Get-ChildItem $KitRoot -Recurse -File | ForEach-Object {
    if (ShouldSkip $_.FullName) { return }
    $rel = $_.FullName.Substring($KitRoot.Length).TrimStart('\')
    $dest = Join-Path $OutDir $rel
    $destParent = Split-Path $dest -Parent
    if (-not (Test-Path $destParent)) {
        New-Item -ItemType Directory -Force -Path $destParent | Out-Null
    }
    Copy-Item $_.FullName $dest -Force
    $copied++
}

# Ensure empty model dirs exist on stick
@(
    "product\models\ollama",
    "models\ollama",
    "product\runtime\ollama",
    "verify"
) | ForEach-Object {
    New-Item -ItemType Directory -Force -Path (Join-Path $OutDir $_) | Out-Null
}

$stamp = [ordered]@{
    signature = "Delta9Phi963-LYGO-CLAW-PUBLIC-USB-BUILD-v1"
    built_utc = (Get-Date).ToUniversalTime().ToString("o")
    source_kit = $KitRoot
    out_dir = $OutDir
    files_copied = $copied
    include_models = [bool]$IncludeModels
    next_steps = @(
        "Install Ollama from https://ollama.com/download (Windows)",
        "Run scripts\install_public_model.ps1  (pulls llama3.2:1b by default)",
        "Double-click LYGO_USB_BOOT.bat",
        "Open http://127.0.0.1:9631/ and chat"
    )
}
$stamp | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $OutDir "verify\PUBLIC_USB_BUILD.json") -Encoding utf8

Write-Host "OK copied $copied files → $OutDir"
Write-Host "Models NOT included (public default). On stick run: scripts\install_public_model.ps1"
if ($OpenExplorer) { Start-Process explorer.exe $OutDir }
exit 0
