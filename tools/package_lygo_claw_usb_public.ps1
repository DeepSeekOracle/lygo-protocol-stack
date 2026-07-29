# Zip the public LYGO CLAW USB kit (no models, no secrets).
# Output: dist/LYGO-CLAW-USB-PUBLIC-v1.2.zip
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Kit = Join-Path $Root "docs\lygo-claw-usb"
$Dist = Join-Path $Root "dist"
$Ver = "1.2.0"
$Name = "LYGO-CLAW-USB-PUBLIC-v$Ver"
$Stage = Join-Path $env:TEMP $Name
$Zip = Join-Path $Dist "$Name.zip"

if (-not (Test-Path (Join-Path $Kit "LYGO_USB_BOOT.bat"))) {
    throw "Kit missing: $Kit"
}

if (Test-Path $Stage) { Remove-Item $Stage -Recurse -Force }
New-Item -ItemType Directory -Force -Path $Stage, $Dist | Out-Null

# Reuse build script into stage
& (Join-Path $Kit "scripts\build_public_usb.ps1") -OutDir $Stage

if (Test-Path $Zip) { Remove-Item $Zip -Force }
Compress-Archive -Path (Join-Path $Stage '*') -DestinationPath $Zip -CompressionLevel Optimal

$len = (Get-Item $Zip).Length
Write-Host "OK $Zip ($([math]::Round($len/1KB,1)) KB)"
Remove-Item $Stage -Recurse -Force -ErrorAction SilentlyContinue
exit 0

