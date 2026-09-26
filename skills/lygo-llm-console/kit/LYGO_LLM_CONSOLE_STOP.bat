@echo off
rem Port-scoped only. Do not Get-Process llama-server (High-Perf collision).
powershell -NoProfile -Command ^
  "foreach ($p in 11441,11442,9641) { Get-NetTCPConnection -LocalPort $p -State Listen -EA SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -EA SilentlyContinue } }"
echo stopped listeners on 9641/11441/11442
