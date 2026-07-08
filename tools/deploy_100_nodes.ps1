# LYGO Phase 5 — live mesh cluster (Windows)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
$nodes = if ($env:NODES) { [int]$env:NODES } else { 100 }
$base = if ($env:BASE_PORT) { [int]$env:BASE_PORT } else { 8700 }
Write-Host "Δ9Φ963-PHASE5-LIVE-DEPLOYMENT — starting $nodes nodes"
python tools/deploy_mesh_cluster.py start --nodes $nodes --base-port $base --host 127.0.0.1
Write-Host "Monitor: python tools/monitor_convergence.py --base-port $base --nodes $nodes"