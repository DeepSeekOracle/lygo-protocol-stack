$env:LYGO_STACK_ROOT = "I:\E Drive\lygo-protocol-stack"
$env:LYGO_AGENT_ID = "LIGHTFATHER_STEWARD"
$env:LYGO_NODE_ID = "LIGHTFATHER_HOME"
Set-Location $env:LYGO_STACK_ROOT
& "$env:LYGO_STACK_ROOT\tools\launch_cyborg_lattice.ps1" | Out-Null
python tools/cyborg_lattice_heartbeat.py --pulse --peer http://127.0.0.1:8791
exit $LASTEXITCODE
