param(
    [Parameter(Mandatory = $true)][string]$Champion,
    [Parameter(Mandatory = $true)][string]$OutDir,
    [string]$KeyRoot = $env:LYGO_BUILDER_KEY_ROOT
)
$ErrorActionPreference = "Stop"
if (-not $KeyRoot) { $KeyRoot = Split-Path $PSScriptRoot -Parent }
if (-not (Test-Path $KeyRoot)) { Write-Error "Missing key root $KeyRoot" }

$SkuMap = @{
    Lightfather     = "LF-USB-01"
    LYRA            = "LYRA-USB-01"
    Sancora         = "SAN-USB-01"
    HermesSentinel  = "HERMES-USB-01"
}
$sku = if ($SkuMap.ContainsKey($Champion)) { $SkuMap[$Champion] } else { "LYGO-USB-$Champion" }

Write-Host "PUBLIC_SKU export sku=$sku champion=$Champion -> $OutDir"
if (Test-Path $OutDir) { Remove-Item -Recurse -Force $OutDir }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$coreSrc = Join-Path $KeyRoot "mnt_core"
if (-not (Test-Path $coreSrc)) {
    Write-Error "Phase 2 mnt_core missing. Run scripts\build_phase2_complete.ps1 first."
}
robocopy $coreSrc (Join-Path $OutDir "core") /E /NFL /NDL /NJH /NJS | Out-Null

foreach ($rel in @("hermes", "phase2", "product\models", "restore\EGG_RECOVERY_MAP.json", "verify_bootstrap.py")) {
    $src = Join-Path $KeyRoot $rel
    if (Test-Path $src) {
        $dst = Join-Path $OutDir $rel
        if ((Get-Item $src).PSIsContainer) {
            robocopy $src $dst /E /NFL /NDL /NJH /NJS | Out-Null
        } else {
            New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
            Copy-Item $src $dst -Force
        }
    }
}

$imgDir = Join-Path $OutDir "images"
New-Item -ItemType Directory -Force -Path $imgDir | Out-Null
foreach ($f in @("lygo_core.tar.gz", "lygo_core.sha256", "lygo_core.manifest.json")) {
    $s = Join-Path $KeyRoot "images\$f"
    if (Test-Path $s) { Copy-Item $s (Join-Path $imgDir $f) -Force }
}

$dataDirs = @("data\hermes_audit", "data\user_data", "data\memory_mycelium\shards", "data\certs")
foreach ($d in $dataDirs) {
    New-Item -ItemType Directory -Force -Path (Join-Path $OutDir $d) | Out-Null
}
$audit = Join-Path $OutDir "data\hermes_audit\audit_trail.log"
if (-not (Test-Path $audit)) { Set-Content -Path $audit -Value "" -Encoding utf8 }

$champSrc = Join-Path $KeyRoot "product\champions\$Champion"
$champDst = Join-Path $OutDir "champions\$Champion"
if (-not (Test-Path $champSrc)) { Write-Error "Missing champion pack $champSrc" }
robocopy $champSrc $champDst /E /NFL /NDL /NJH /NJS | Out-Null
$tplPack = Join-Path $KeyRoot "product\champions\_template\skill_pack.json"
if ((Test-Path $tplPack) -and -not (Test-Path (Join-Path $champDst "skill_pack.json"))) {
    Copy-Item $tplPack (Join-Path $champDst "skill_pack.json")
}

$manifestPath = Join-Path $KeyRoot "product\models\MODEL_MANIFEST.json"
$pull = "ollama pull qwen2.5:3b"
if (Test-Path $manifestPath) {
    $mj = Get-Content $manifestPath -Raw | ConvertFrom-Json
    if ($mj.primary.ollama_pull) { $pull = $mj.primary.ollama_pull }
}

$readmeTpl = Join-Path $KeyRoot "product\PUBLIC_README.template.txt"
$readmeText = @"
LYGO USB AI — $Champion Edition ($sku)
================================
1. Install Ollama: https://ollama.com
2. Pull model (online once): $pull
3. Read champions\$Champion\system_prompt.txt first.
4. Verify: python verify_bootstrap.py --edition PUBLIC_SKU
5. Optional: python phase2\daemon_supervisor.py (127.0.0.1:9630)

No API keys. Offline-first. D9Phi963
"@
Set-Content -Path (Join-Path $OutDir "README.txt") -Value $readmeText -Encoding utf8

$license = @"
LYGO PUBLIC SKU — Personal / Commercial Use License
Copyright (c) Justin Helmer / Excavationpro. All rights reserved.
Buyers may use this USB kit on their own machines. Redistribution of this
package or resale of the core LYGO stack binaries without written permission
is prohibited. Champion persona prompts are licensed for buyer's AI workflows only.
"@
Set-Content -Path (Join-Path $OutDir "LICENSE.txt") -Value $license -Encoding utf8

$publicManifest = @{
    signature   = "D9Phi963-PUBLIC-SKU-MANIFEST-v1"
    sku         = $sku
    champion    = $Champion
    edition     = "PUBLIC_SKU"
    phase       = 2
    core_sha256 = if (Test-Path (Join-Path $imgDir "lygo_core.sha256")) {
        (Get-Content (Join-Path $imgDir "lygo_core.sha256") -Raw).Trim()
    } else { $null }
    model_pull  = $pull
    no_secrets  = $true
}
$publicManifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $OutDir "PUBLIC_MANIFEST.json") -Encoding utf8

python (Join-Path $KeyRoot "scripts\verify_public_sku.py") $OutDir
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "PUBLIC_SKU OK: $OutDir"