# LYGO USB Agent Dashboard (working path)

**Signature:** `Delta9Phi963-LYGO-USB-AGENT-SERVER-v1.2`  
**Does not modify** `E:\LYGO_LATTICE_MEMORY`, steward vaults, or USB `restore/` contents (read-only status only).

## Boot (one command)

```bat
E:\LYGO_BUILDER_KEY\LYGO_USB_BOOT.bat
```

Or Master Manager → **9**.

This:

1. Bootstraps env  
2. **Syncs public lattice** from `D:\lygo-protocol-stack` (preferred) into `verify\lattice_live\`  
3. Starts **USB Ollama** (`ensure_ollama_serve.ps1`) with `OLLAMA_MODELS` on the stick  
4. Starts **gateway** on `:18789` (OpenClaw control plane, if binaries present) — does **not** kill host `node.exe`  
5. Starts **agent server** on `:9631` and opens the dashboard  

Lattice-only refresh (no services): Master Manager → **A**, or:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\sync_lattice_live_readonly.ps1
```

## URLs

| UI | URL |
|----|-----|
| **Agent dashboard (use this)** | http://127.0.0.1:9631/ |
| OpenClaw control UI | http://127.0.0.1:9631/control-ui/?token=lygo-usb-standalone-token |
| Status API | http://127.0.0.1:9631/api/status |
| Lattice API | http://127.0.0.1:9631/api/lattice |
| Synced public JSON | http://127.0.0.1:9631/lattice/IMMUTABLE_ANCHORS.json |
| Ollama | http://127.0.0.1:11434 |
| Gateway WS | ws://127.0.0.1:18789 |

## D: lattice authority

| Priority | Stack root |
|----------|------------|
| 1 | `LYGO_STACK_ROOT` env |
| 2 | `D:\lygo-protocol-stack` |
| 3 | `I:\E Drive\lygo-protocol-stack` |
| 4 | USB `stack\lygo-protocol-stack` (travel mirror) |

Synced files (public only, SHA-256 recorded in `LATTICE_LIVE_SYNC.json`):

- Dual ledgers: `IMMUTABLE_ANCHORS.json` + `haven_star_chart_feed.json`
- `public_verify_manifest.json`, `LYGO_LATTICE_MEMORY_SNAPSHOT.json`
- Optional: star meta/queue, agent memory snapshot, link archive, kernel registry
- Pointers: `LATTICE_POINTERS.json`, `DUAL_LEDGERS.json`

**Never copied / never mutated:** `restore\`, `lattice_master\steward_vault`, `E:\LYGO_LATTICE_MEMORY`, `E:\Data Vault`.

## Why the old dashboard felt “empty”

1. **OpenClaw Control UI** was often opened as `file://` → empty mount / auth fail.  
2. **`lygo-claw.html`** had a JS syntax error and a fragile WS auth handshake.  
3. **Ollama** was often not running, or `ensure_ollama_serve.ps1` was corrupted (fixed).  
4. Gateway auth/token challenges blocked chat even when the process was “up”.

The agent UI talks to **Ollama HTTP chat** directly (works offline once models are on USB). Gateway/Control UI is optional.

## Offline / first-time hydrate (online once)

```bat
scripts\bundle_ollama_to_usb.ps1
scripts\hydrate_usb_models.ps1
```

Primary model: see `product\models\MODEL_MANIFEST.json` (default `qwen2.5:3b`).

## Daemon tasks

From the agent UI “Daemon tasks” panel, or:

```http
POST http://127.0.0.1:9631/api/tasks
{"title":"nightly verify"}
```

Supervisor launcher (unchanged): `launchers\LYGO_Supervisor_Daemon.bat`

## Files (hardened 2026-07-29)

| Path | Role |
|------|------|
| `LYGO_USB_BOOT.bat` | One-button boot + lattice sync + D: stack prefer |
| `scripts\sync_lattice_live_readonly.ps1` | Public lattice snapshot v1.2 (SHA + dual ledgers) |
| `scripts\lygo_usb_agent_server.py` | Dashboard + chat + `/api/lattice` + `/lattice/*` v1.2 |
| `dashboard\agent-ui\index.html` | Agent UI + lattice summary panel |
| `scripts\ensure_ollama_serve.ps1` | Reliable USB Ollama serve |
| `dashboard\lygo-claw.html` | Redirect to agent UI |
| `LYGO_CLAW_Launch.bat` | Points at USB boot |
| `LYGO_Master_Manager.bat` | Options 9 / A / 6 (D: verify) |
