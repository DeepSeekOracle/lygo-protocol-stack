# Publish lygo-champion-council + deprecated legacy champion bumps (consolidation wave)
$ErrorActionPreference = "Stop"
$M = "I:\E Drive\lygo-protocol-stack\clawhub\mirrors"

npx --yes clawhub@latest publish "$M\lygo-champion-council" --slug lygo-champion-council --name "LYGO Champion Council (Δ9 unified v2)"

Get-ChildItem $M -Directory -Filter "lygo-champion-*" | Where-Object { $_.Name -ne "lygo-champion-council" } | ForEach-Object {
  $name = ($_.Name -replace "lygo-champion-", "LYGO Champion: ") -replace "-", " "
  npx --yes clawhub@latest publish $_.FullName --slug $_.Name --name $name
}

Write-Host "Done champion consolidation ClawHub wave"