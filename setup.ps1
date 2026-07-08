# LYGO Protocol Stack — one-click community setup (Windows)
$ErrorActionPreference = "Stop"
$Signature = "Δ9Φ963-PHASE2-DEPLOYMENT"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host "=== LYGO Phase 2 setup ($Signature) ==="

python -m pip install -q -r requirements.txt
if (Test-Path "requirements-docker.txt") {
    python -m pip install -q -r requirements-docker.txt
}

python tools/generate_falsifiable_vectors.py
python -m pytest protocol0_byte_entropy_filter/tests/ -q
python tools/verify_alignment_badge.py --format=both

if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "Docker detected — building lygo-node image..."
    docker compose build lygo-node
    Write-Host "Start node: docker compose up -d lygo-node"
    Write-Host "Scale workers: docker compose --profile scale up -d"
} else {
    Write-Host "Docker not found — local Python stack is ready."
    Write-Host "Optional API: python tools/node_api_server.py --host 127.0.0.1 --port 8787"
}

Write-Host "=== Setup complete ==="