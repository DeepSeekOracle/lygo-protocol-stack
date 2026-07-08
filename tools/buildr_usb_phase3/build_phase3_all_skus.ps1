# Export all retail champion SKUs (Phase 3) — requires Phase 2 gate on key root
$ErrorActionPreference = "Stop"
$Workspace = "I:\E Drive"
$Key = if ($env:LYGO_BUILDER_KEY_ROOT) { $env:LYGO_BUILDER_KEY_ROOT } else { "E:\LYGO_BUILDER_KEY" }
$ExportRoot = Join-Path $Workspace "LYGO_BUILDR_EXPORTS"
$Champions = @("Lightfather", "LYRA", "Sancora", "HermesSentinel")

Write-Host "Phase 3 gate: verify Phase 2 on $Key"
python (Join-Path $Key "verify_bootstrap.py") --edition GROK_BUILDR --phase2
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

New-Item -ItemType Directory -Force -Path $ExportRoot | Out-Null
foreach ($c in $Champions) {
    $out = Join-Path $ExportRoot $c
    & (Join-Path $Key "scripts\export_public_sku.ps1") -Champion $c -OutDir $out -KeyRoot $Key
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
Write-Host "All PUBLIC_SKU exports under $ExportRoot"