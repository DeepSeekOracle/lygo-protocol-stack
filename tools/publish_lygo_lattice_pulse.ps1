# Publish @deepseekoracle/lygo-lattice-pulse to ClawHub (Windows-safe)
param(
  [string]$Version = "1.1.0"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Pkg = Join-Path $Root "clawhub\packages\lygo-lattice-pulse"
$Tgz = Join-Path $env:USERPROFILE "lygo-lattice-pulse-$Version.tgz"

Push-Location $Pkg
try {
  npx -y esbuild@0.25.0 src/index.ts --bundle --platform=node --format=esm `
    --external:openclaw/plugin-sdk/plugin-entry --external:typebox --outfile=dist/index.js
  npm.cmd pack --pack-destination $env:USERPROFILE | Out-Null
  $packed = Get-ChildItem (Join-Path $env:USERPROFILE "deepseekoracle-lygo-lattice-pulse-*.tgz") |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if ($packed.FullName -ne $Tgz) { Copy-Item $packed.FullName $Tgz -Force }

  $commit = (git -C $Root rev-parse --short HEAD).Trim()
  npx clawhub@latest package validate .
  npx clawhub@latest package publish $Tgz `
    --family code-plugin `
    --name "@deepseekoracle/lygo-lattice-pulse" `
    --display-name "LYGO Lattice Pulse" `
    --version $Version `
    --source-repo "DeepSeekOracle/lygo-protocol-stack" `
    --source-commit $commit `
    --source-path "clawhub/packages/lygo-lattice-pulse" `
    --changelog "v$Version — alignment_ready, registry compare, star chart gate, full docs" `
    --topics "lygo,lattice,haven,verification,agent-tools" `
    --no-input
  Write-Host "Published @deepseekoracle/lygo-lattice-pulse@$Version"
}
finally {
  Pop-Location
}