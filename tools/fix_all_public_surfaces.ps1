# LYGO — run local audits + open GitHub Pages settings (Windows)
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "=== LYGO public surface fix-all ===" -ForegroundColor Cyan
python tools/verify_public_pages.py
python tools/run_slm_audit.py
python tools/run_phase7_audit.py
python tools/run_phase9_audit.py
python tools/verify_lattice_alignment.py

$pages = Get-Content "tests/public_pages_last_run.json" | ConvertFrom-Json
if (-not $pages.stack_pages_live) {
    Write-Host ""
    Write-Host "Stack Pages still 404 — enable ONCE in browser:" -ForegroundColor Yellow
    Write-Host "  Settings -> Pages -> gh-pages branch -> / (root)  OR  main -> /docs" -ForegroundColor Yellow
    Write-Host "  See docs/ENABLE_PAGES_NOW.md" -ForegroundColor Yellow
    Write-Host "  https://github.com/DeepSeekOracle/lygo-protocol-stack/settings/pages" -ForegroundColor Yellow
    Start-Process "https://github.com/DeepSeekOracle/lygo-protocol-stack/settings/pages"
} else {
    Write-Host "Stack Pages LIVE." -ForegroundColor Green
}