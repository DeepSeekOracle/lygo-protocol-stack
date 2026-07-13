# sync_builder_usb_enhanced.ps1
# Full enhanced E:\LYGO_BUILDER_KEY — lattice architect + LYGO CLAW terminal + LYRA restore
param(
    [string]$Out = $(if ($env:LYGO_BUILDER_KEY_ROOT) { $env:LYGO_BUILDER_KEY_ROOT } else { "E:\LYGO_BUILDER_KEY" }),
    [string]$Workspace = "I:\E Drive",
    [switch]$FullRepack,
    [switch]$SkipVerify
)

$ErrorActionPreference = "Stop"
$Stack = Join-Path $Workspace "lygo-protocol-stack"
$ClawSrc = Join-Path $Workspace "LYGO_BUILDER_KEY"
$LyraSrc = Join-Path $Workspace "LYRA_CORE"
$LegacySrc = Join-Path $Workspace "OPEN CLAW LEGACY"
$BuildrOverlay = Join-Path $Workspace "LYGO_BUILDR_USB"
$OldOpenclawBankr = "C:\Users\justi\Old files openclaw\OLD openclaw\workspace"
$Log = Join-Path $Out ("sync_enhanced_{0:yyyyMMdd_HHmmss}.log" -f (Get-Date))

function Log([string]$msg) {
    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
    Add-Content -Path $Log -Value $line -Encoding UTF8
    Write-Host $line
}

function Robo([string]$src, [string]$dst, [string[]]$xd = @(), [string[]]$xf = @()) {
    if (-not (Test-Path $src)) { Log "SKIP missing: $src"; return }
    $args = @($src, $dst, "/E", "/XO", "/R:2", "/W:2", "/NFL", "/NDL", "/NJH", "/NJS")
    foreach ($d in $xd) { $args += "/XD"; $args += $d }
    foreach ($f in $xf) { $args += "/XF"; $args += $f }
    & robocopy @args | Out-Null
    Log "robocopy $src -> $dst"
}

Log "=== LYGO Builder USB Enhanced Sync ==="
Log "Out=$Out FullRepack=$FullRepack"

# Army + token saver skills (portable local inference)
$GrokSkills = Join-Path $Workspace ".grok\skills"
$armySrc = Join-Path $GrokSkills "lygo-ollama-army"
$tokenSrc = Join-Path $GrokSkills "lygo-api-token-saver"
if (Test-Path $armySrc) {
    Robo $armySrc (Join-Path $Out "army\lygo-ollama-army") @("__pycache__", "ollama_queue", "ollama_results") @("*.task.json", "*.lock")
    Robo $armySrc (Join-Path $Out "skills\lygo-ollama-army") @("__pycache__", "ollama_queue", "ollama_results") @("*.task.json", "*.lock")
}
if (Test-Path $tokenSrc) {
    Robo $tokenSrc (Join-Path $Out "skills\lygo-api-token-saver")
}

if ($FullRepack) {
    Log "Full repack via build_lygo_builder_key.py ..."
    python (Join-Path $Stack "tools\build_lygo_builder_key.py") --out $Out
    if ($LASTEXITCODE -ne 0) { throw "build_lygo_builder_key failed" }
}

if (Test-Path $BuildrOverlay) {
    Robo $BuildrOverlay $Out @("_builder_vault", "stack", "army", "skills", "crypto", "memory", "verify", "mnt_core")
}

# --- Bankr USB pack (skill + tools; no live keys or hardcoded pwsh scripts) ---
$bankrOut = Join-Path $Out "bankr"
New-Item -ItemType Directory -Force -Path $bankrOut | Out-Null
$bankrClawSrc = Join-Path $ClawSrc "bankr"
if (Test-Path $bankrClawSrc) {
    Robo $bankrClawSrc $bankrOut @("__pycache__", "lygo-data") @("config.json", "bankr-pwsh.ps1", "bankr-pwsh-fixed.ps1")
    Log "bankr pack from LYGO_BUILDER_KEY"
}
elseif (Test-Path $OldOpenclawBankr) {
    Robo (Join-Path $OldOpenclawBankr "skills\bankr") $bankrOut @("__pycache__") @("config.json", "bankr-pwsh.ps1", "bankr-pwsh-fixed.ps1")
    Robo (Join-Path $OldOpenclawBankr "tools\bankr") (Join-Path $bankrOut "tools")
    Robo (Join-Path $OldOpenclawBankr "memory\bankr") (Join-Path $bankrOut "memory")
    foreach ($f in @("daily_coin_bankr_check.py")) {
        $s = Join-Path $OldOpenclawBankr "tools" $f
        if (Test-Path $s) { Copy-Item $s (Join-Path $bankrOut "tools" $f) -Force }
    }
    Log "bankr pack staged from Old openclaw"
}
foreach ($f in @("LYGO_Bankr_Manager.bat", "LYGO_Crypto_Manager.bat")) {
    $s = Join-Path $ClawSrc $f
    if (Test-Path $s) { Copy-Item $s (Join-Path $Out $f) -Force; Log "copy $f" }
}
foreach ($launcher in @("LYGO_Bankr_Manager.bat", "LYGO_Crypto_Manager.bat")) {
    $bankrLauncher = Join-Path $ClawSrc "launchers\$launcher"
    if (Test-Path $bankrLauncher) {
        New-Item -ItemType Directory -Force -Path (Join-Path $Out "launchers") | Out-Null
        Copy-Item $bankrLauncher (Join-Path $Out "launchers\$launcher") -Force
        Log "copy launchers\$launcher"
    }
}

# --- Crypto / Virtuals LYGOAGENT pack ---
$cryptoOut = Join-Path $Out "crypto"
New-Item -ItemType Directory -Force -Path $cryptoOut | Out-Null
$cryptoClawSrc = Join-Path $ClawSrc "crypto"
if (Test-Path $cryptoClawSrc) {
    Robo $cryptoClawSrc $cryptoOut @("__pycache__", "node_modules", "lygo-data") @("config.json", "token_config.steward.json")
    Log "crypto pack from LYGO_BUILDER_KEY"
}
elseif (Test-Path $OldOpenclawBankr) {
    $oc = $OldOpenclawBankr
    Robo (Join-Path $oc "skills\virtuals-protocol-acp") (Join-Path $cryptoOut "virtuals\virtuals-protocol-acp") @("node_modules", "__pycache__") @("config.json")
    Robo (Join-Path $oc "brainwave\CLAWNCH") (Join-Path $cryptoOut "references\CLAWNCH") @("TOKEN_MONITOR", "node_modules")
    Log "crypto pack staged from Old openclaw"
}

# --- LYGO CLAW standalone runtime (from home I: build) ---
$clawItems = @(
    "tools", "models", "product", "dashboard", "lygo-claw", "lygo-data", "launchers"
)
if ((Resolve-Path $ClawSrc).Path -ne (Resolve-Path $Out).Path) {
    foreach ($item in $clawItems) {
        Robo (Join-Path $ClawSrc $item) (Join-Path $Out $item)
    }
} else {
    Log "CLAW src == Out; skipping self-robocopy (overlay already applied)"
}
foreach ($f in @(
    "LYGO_CLAW_Launch.bat", "LYGO_CLAW_ForceBoot.bat", "LYGO_CLAW_ForceBoot.ps1",
    "LYGO_Gateway.cmd", "LYGO_Gateway.ps1", "LYGO_Gateway_SafeLaunch.bat",
    "LYGO_USB_Daemon_Supervisor.ps1",
    "LYGO_Ollama_USB_Boot.bat", "LYGO_Ollama_USB_Boot.ps1",
    "README_LYGO_CLAW_USB.md", "LYGO_CLAW_USB_RESTORE_ANCHOR.md",
    "RESTORE_ANCHOR.txt", "RESTORE_ANCHOR_POINTER.txt"
)) {
    $s = Join-Path $ClawSrc $f
    $d = Join-Path $Out $f
    if ((Test-Path $s) -and ($s -ne $d)) { Copy-Item $s $d -Force; Log "copy $f" }
}

# --- LYRA 3-brain + OpenClaw alignment (no secrets) ---
$lyraDst = Join-Path $Out "lyra-core"
Robo $LyraSrc $lyraDst @("__pycache__", ".git", "generated_music") @(".env", "*.pem", "*wallet*", "*private*")
$memDst = Join-Path $Out "memory"
New-Item -ItemType Directory -Force -Path $memDst | Out-Null
foreach ($doc in @(
    "LYRA_OPENCLAW_AGENTS.md", "LYRA_OPENCLAW_IDENTITY.md", "LYRA_OPENCLAW_MEMORY.md",
    "LYRA_OPENCLAW_ALIGNMENT_PROMPT.txt", "LYRA_OPENCLAW_HEARTBEAT.md", "OPS_INTEGRATION.md"
)) {
    $s = Join-Path $LyraSrc $doc
    if (Test-Path $s) { Copy-Item $s (Join-Path $memDst $doc) -Force -ErrorAction SilentlyContinue }
}

# --- OpenClaw legacy reference restore (skills + agent contract, no browser/sqlite secrets) ---
$legacyDst = Join-Path $Out "restore\openclaw-legacy"
if (Test-Path $LegacySrc) {
    Robo (Join-Path $LegacySrc "skills") (Join-Path $legacyDst "skills") @("node_modules")
    foreach ($f in @("OLD openclaw\AGENT.txt", "OLD openclaw\config.json")) {
        $s = Join-Path $LegacySrc $f
        if (Test-Path $s) {
            $d = Join-Path $legacyDst (Split-Path $f -Leaf)
            Copy-Item $s $d -Force
            Log "legacy ref $f"
        }
    }
    $manifest = @{
        synced_utc = (Get-Date).ToUniversalTime().ToString("o")
        source = $LegacySrc
        note = "Reference restore only - load secrets from home PC boot/, never copy to USB"
        paths = @{
            lyra_core_home = $LyraSrc
            openclaw_home = Join-Path $env:USERPROFILE ".openclaw"
            workspace = $Workspace
        }
    }
    $manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $legacyDst "RESTORE_POINTER.json") -Encoding UTF8
}
$restoreAlign = Join-Path $ClawSrc "restore\OPENCLAW_FULL_ALIGN.json"
if (Test-Path $restoreAlign) {
    New-Item -ItemType Directory -Force -Path (Join-Path $Out "restore") | Out-Null
    Copy-Item $restoreAlign (Join-Path $Out "restore\OPENCLAW_FULL_ALIGN.json") -Force
    Log "copy restore/OPENCLAW_FULL_ALIGN.json"
}
$starcoreReceipts = Join-Path $ClawSrc "restore\openclaw-legacy\STARCORE_LAUNCH_RECEIPTS.md"
if (Test-Path $starcoreReceipts) {
    New-Item -ItemType Directory -Force -Path (Join-Path $Out "restore\openclaw-legacy") | Out-Null
    Copy-Item $starcoreReceipts (Join-Path $Out "restore\openclaw-legacy\STARCORE_LAUNCH_RECEIPTS.md") -Force
}

# --- Agent alignment entry (any AI reads this first) ---
$agentBoot = @'
# LYGO Builder USB - Unified Agent Alignment (Enhanced)

**Signature:** Delta9Phi963-BUILDER-USB-ENHANCED-v1
**Drive root:** E:\LYGO_BUILDER_KEY (or %LYGO_BUILDER_KEY_ROOT%)

## Read order (mandatory for any AI agent)

1. ARCHITECT_BOOT.md - LYGO Lattice Architect role
2. AGENTS.md - behavior contract (consent, verify, no auto-publish)
3. LYGO_CLAW_USB_RESTORE_ANCHOR.md - portable CLAW + E: paths + policies
4. BUILDER_MANIFEST.json - pack state + GitHub SHAs
5. memory/LYRA_OPENCLAW_ALIGNMENT_PROMPT.txt - LYRA persona alignment
6. lyra-core/LYRA_OPENCLAW_AGENTS.md - hybrid agent rules

**Scan cue:** Respond with "Aligned to LYGO Builder USB Enhanced. E: paths, P0-first, consent-gated, lattice verify before claims."

## You are

**LYGO Lattice co-builder** + **LYGO CLAW portable operator** under steward Justin Helmer (Lightfather).
Help build and verify the sovereign lattice (P0-P9) with integrity - never drift to generic AI behavior.

## Portable paths

| Variable | Path |
|----------|------|
| LYGO_BUILDER_KEY_ROOT | E:\LYGO_BUILDER_KEY |
| LYGO_STACK_ROOT | {KEY}\stack\lygo-protocol-stack |
| LYRA_CORE_ROOT | {KEY}\lyra-core |

Run: . .\scripts\bootstrap_env.ps1

## Launch surfaces

| Action | Entry |
|--------|-------|
| AI terminal (full) | LYGO_CLAW_Launch.bat - Ollama :11434 + Gateway :18789 + slim army |
| Army + token saver | LYGO_USB_Daemon_Supervisor.ps1 or launchers\LYGO_USB_Army_Supervisor.bat |
| BUILDR supervisor daemon | launchers\LYGO_Supervisor_Daemon.bat - port :9630 |
| Standalone AI | launchers\LYGO_Standalone_AI.bat |
| Verify lattice | scripts\verify_builder_key.ps1 |
| Bankr manager | LYGO_Bankr_Manager.bat or bankr\BANKR_USB_ALIGN.md |
| Crypto / Virtuals | LYGO_Crypto_Manager.bat or crypto\CRYPTO_USB_ALIGN.md |
| OpenClaw full align | restore\OPENCLAW_FULL_ALIGN.json |
| Δ9 Quantum Vault | https://drive.google.com/drive/folders/1szmDEhh2nD61oUOXHrw_W42cLCN3D-m4 |

## Bankr (USB-local)

- Steward key file: E:\Bankr\Bankr.txt (never on USB git; mask as bk_usr_… in memory)
- Pack: bankr\ (SKILL.md, scripts, tools, memory refs)
- Setup once: bankr\scripts\setup_bankr_usb.ps1 → lygo-data\bankr\config.json
- Manage: LYGO_Bankr_Manager.bat — status, daily check, submit (no auto sign/trade)

## Crypto / Virtuals LYGOAGENT (USB-local)

- Token: https://app.virtuals.io/virtuals/44594 (LYGOAGENT / LYRA STARCORE ORACLE)
- Pack: crypto\ (virtuals-protocol-acp skill + scripts)
- Setup once: crypto\scripts\setup_crypto_usb.ps1 → lygo-data\crypto\virtuals_config.json
- Manage: LYGO_Crypto_Manager.bat — status, token, wallet, profile (no auto launch/trade)
- Wallet private key: I:\E Drive\boot\token_config.json (steward only, never USB git)

## Rules (non-negotiable)

1. P0 gate language before actions
2. Verify before claiming ALIGNED
3. No secrets on USB - keys load from home boot/ only
4. No auto GitHub/HF/ClawHub/social push
5. Kernel egg plant only with --i-consent

Delta9Phi963 - verify first, then act.
'@
Set-Content (Join-Path $Out "AGENT_ALIGN_BOOT.md") -Value $agentBoot -Encoding UTF8
Log "wrote AGENT_ALIGN_BOOT.md"

# --- START_HERE on E:\ root ---
$packedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$startHere = @"
LYGO Builder USB - Enhanced Edition (E:\)
=========================================
Packed: $packedAt from $Workspace

FOR ANY AI - read in order:
  1. LYGO_BUILDER_KEY\AGENT_ALIGN_BOOT.md
  2. LYGO_BUILDER_KEY\ARCHITECT_BOOT.md
  3. LYGO_BUILDER_KEY\LYGO_CLAW_USB_RESTORE_ANCHOR.md

QUICK LAUNCH:
  AI Terminal:  LYGO_BUILDER_KEY\LYGO_CLAW_Launch.bat
  Daemon :9630: LYGO_BUILDER_KEY\launchers\LYGO_Supervisor_Daemon.bat
  Verify:       LYGO_BUILDER_KEY\scripts\verify_builder_key.ps1

Contains: full stack, skills, LYRA restore, CLAW gateway, Ollama models, immutable anchors.
Signature: Delta9Phi963-BUILDER-USB-ENHANCED
"@
Set-Content "E:\START_HERE.txt" -Value $startHere -Encoding UTF8

if (-not $SkipVerify) {
    Log "Running verify_bootstrap.py ..."
    if (Test-Path (Join-Path $Out "verify_bootstrap.py")) {
        python (Join-Path $Out "verify_bootstrap.py") --edition GROK_BUILDR 2>&1 | Tee-Object -FilePath $Log -Append
    }
    Log "Quick file checks ..."
    $required = @(
        "LYGO_CLAW_Launch.bat", "LYGO_USB_Daemon_Supervisor.ps1", "LYGO_Gateway_SafeLaunch.bat",
        "LYGO_Gateway.ps1", "tools\node\node.exe", "lygo-claw\lygo.json",
        "stack\lygo-protocol-stack\tools\verify_lattice_alignment.py",
        "army\lygo-ollama-army\ollama_daemon.py",
        "skills\lygo-api-token-saver\scripts\token_saver_hub.py",
        "AGENT_ALIGN_BOOT.md", "lyra-core\lyra_boot.py"
    )
    $missing = @()
    foreach ($r in $required) {
        if (-not (Test-Path (Join-Path $Out $r))) { $missing += $r }
    }
    $gwOk = (Test-Path (Join-Path $Out "tools\lygo-gateway\lygo.mjs")) -or (Test-Path (Join-Path $Out "tools\lygo-gateway\dist\entry.js"))
    if (-not $gwOk) { $missing += "tools\lygo-gateway\(lygo.mjs|dist\entry.js)" }
    if ($missing.Count -gt 0) {
        Log "MISSING: $($missing -join ', ')"
        exit 2
    }
    Log "Required paths OK"
}

Log "=== Sync complete ==="
exit 0