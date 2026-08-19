# Optional Windows Scheduled Task installer for deadman watchdog.
# Does NOT install unless you pass -IConsent.
param(
  [switch]$IConsent,
  [int]$IntervalMinutes = 15,
  [switch]$WithTouch
)
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
if (-not (Test-Path (Join-Path $Root "tools\seal_deadman_lattice.py"))) { $Root = "I:\E Drive\lygo-protocol-stack" }
if (-not $IConsent) {
  Write-Host "Dry-run only. Re-run with -IConsent to register Scheduled Task LYGO-Deadman-Watchdog."
  Write-Host "Root=$Root IntervalMinutes=$IntervalMinutes WithTouch=$WithTouch"
  exit 0
}
$py = (Get-Command python).Source
$script = Join-Path $Root "tools\deadman_watchdog.py"
$args = if ($WithTouch) { "once --touch" } else { "check" }
$action = New-ScheduledTaskAction -Execute $py -Argument "`"$script`" $args" -WorkingDirectory $Root
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration ([TimeSpan]::MaxValue)
Register-ScheduledTask -TaskName "LYGO-Deadman-Watchdog" -Action $action -Trigger $trigger -Force | Out-Null
Write-Host "Installed Scheduled Task: LYGO-Deadman-Watchdog"
