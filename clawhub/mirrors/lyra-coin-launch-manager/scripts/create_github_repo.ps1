# Create DeepSeekOracle/lyra-crypto-operator and push (requires: gh auth login)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
  Write-Error "Install GitHub CLI: https://cli.github.com/"
}

gh auth status
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
gh repo view DeepSeekOracle/lyra-crypto-operator 2>$null
if ($LASTEXITCODE -ne 0) {
  gh repo create DeepSeekOracle/lyra-crypto-operator --public `
    --description "LYRA Clawnch crypto tools — lattice-separated from lygo-protocol-stack"
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
git push -u origin main
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Done: https://github.com/DeepSeekOracle/lyra-crypto-operator"