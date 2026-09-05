# Stand local Layer D node + Layer E hub (loopback only). Does not publish.
$ErrorActionPreference = "Stop"
$env:LYGO_STACK_ROOT = "I:\E Drive\lygo-protocol-stack"
$env:LYGO_AGENT_ID = "LIGHTFATHER_STEWARD"
$env:LYGO_NODE_ID = "LIGHTFATHER_HOME"
$root = $env:LYGO_STACK_ROOT
$py = (Get-Command python).Source
$log = Join-Path $root "tests"

function Test-Port([int]$Port) {
  try {
    $c = New-Object System.Net.Sockets.TcpClient
    $c.Connect("127.0.0.1", $Port)
    $c.Close()
    return $true
  } catch { return $false }
}

if (-not (Test-Port 8787)) {
  Start-Process -FilePath $py -ArgumentList "tools\node_api_server.py","--host","127.0.0.1","--port","8787" -WorkingDirectory $root -WindowStyle Minimized
}
if (-not (Test-Port 8791)) {
  Start-Process -FilePath $py -ArgumentList "tools\agent_lattice_hub.py","--host","127.0.0.1","--port","8791" -WorkingDirectory $root -WindowStyle Minimized
}
$ok = $false
for ($i = 0; $i -lt 20; $i++) {
  Start-Sleep -Milliseconds 400
  if ((Test-Port 8787) -and (Test-Port 8791)) { $ok = $true; break }
}
if (-not $ok) { Write-Error "hubs did not bind"; exit 1 }
Write-Host "node :8787 and hub :8791 up (loopback)"
exit 0
