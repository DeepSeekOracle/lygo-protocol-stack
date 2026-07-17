# Launch Yandex with CDP (stable profile path — no spaces) + scrape DistroKid vault
# Usage: powershell -ExecutionPolicy Bypass -File tools\launch_yandex_distrokid_scrape.ps1

$ErrorActionPreference = "Continue"
$yandex = "C:\Program Files\Yandex\YandexBrowser\Application\browser.exe"
$ud = Join-Path $env:USERPROFILE ".agent-browser\distrokid-yandex-profile"
$stack = "I:\E Drive\lygo-protocol-stack"
New-Item -ItemType Directory -Force -Path $ud | Out-Null

Write-Host "Stopping existing Yandex processes..."
Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like '*Yandex*' } | ForEach-Object {
  Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 3

Write-Host "Starting Yandex with remote debugging on port 9222..."
Write-Host "Profile: $ud"
Write-Host ">>> Log into DistroKid and open Vault in the Yandex window that opens. <<<"

$arg = @(
  "--remote-debugging-port=9222",
  "--remote-allow-origins=*",
  "--user-data-dir=$ud",
  "--no-first-run",
  "--no-default-browser-check",
  "https://distrokid.com/vault/?ref=globalmenu"
)
Start-Process -FilePath $yandex -ArgumentList $arg

$ok = $false
for ($i = 1; $i -le 40; $i++) {
  Start-Sleep -Seconds 1
  try {
    $null = Invoke-RestMethod "http://127.0.0.1:9222/json/version" -TimeoutSec 2
    Write-Host "CDP is up ($i)"
    $ok = $true
    break
  } catch {}
}
if (-not $ok) {
  Write-Host "FAILED: CDP never started. Is Yandex installed at $yandex ?"
  exit 1
}

Write-Host "Waiting 15s for page load / for you to click through..."
Start-Sleep -Seconds 15

Set-Location $stack
Write-Host "Starting scrape (waits up to 5 min for login if needed)..."
python tools\distrokid_vault_browser_scrape.py --scrape --login-wait 300 --scrolls 80 --max-files 5000
Write-Host "Done. Check data\music_catalog\distrokid_vault_scrape.csv"
