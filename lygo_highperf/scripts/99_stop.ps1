# Stop LYGO high-perf servers
Get-Process -Name "llama-server" -ErrorAction SilentlyContinue | Stop-Process -Force
docker stop lygo-vllm-uncensored 2>$null
docker rm lygo-vllm-uncensored 2>$null
Write-Host "Stopped llama-server / lygo-vllm (if running)."
# free port 8000 holders
foreach ($port in 8000, 8001) {
  $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
  foreach ($c in $conns) {
    try { Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue; Write-Host "Killed PID $($c.OwningProcess) on :$port" } catch {}
  }
}
