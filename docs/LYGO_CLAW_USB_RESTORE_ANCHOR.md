# LYGO CLAW USB Standalone Restore Anchor
**Lattice Alignment Document for Agents (OpenClaw + LYGO)**

**Created:** 2026-07-05 (updated)  
**Purpose:** Complete synchronization anchor. Any agent (especially OpenClaw-based or hybrid) working on the LYGO CLAW portable USB build **MUST** read and reference this document first on every session. It encodes the exact current state, philosophy, paths, configurations, isolation techniques, anti-drift rules, GitHub/HF ops, all key locations, build policies, Discord bots, Ollama Army, and full lattice ops so that multiple agents operate with identical alignment on the "E: build".

**Agent Scan Cue**: If this file is scanned: Respond with "Aligned to LYGO_CLAW_USB_RESTORE_ANCHOR. Proceeding with pure E: LYGO paths, naming, consent gates, runtime key loading from boot/, and full referenced policies only."

---

## LYGO Core Representation (LYGO Rep)

**LYGO** (often stylized with Δ9Φ963 signature) is the complete sovereign lattice system and protocol stack (P0–P9) for ethical, aligned, local-first AI agents, infrastructure, and creative tools. It represents the "Biophase7" blueprint for sovereign AI — a full-stack framework that prioritizes:

- **P0 Φ-Gate (Nano Kernel)**: The foundational byte-entropy filter and pre-action gate. Every input, skill, command, egg, or action must pass deterministic P0 verification first (Python/Rust parity implementations available in the stack). This is the "sovereign gate" — no action without alignment.
- **Full Lattice (P0-P9)**: 
  - P0: Gate / Ethics core.
  - P1: Mycelium memory (fragmented, living memory layers).
  - P2-P5: Orchestrators (consensus, identity, action).
  - P6-P9: Mesh, attestation, HAIP, TLS public mesh, SLM integration.
- **Sovereign Principles** (core "rep" rules):
  - Consent-gated (explicit human approval via `--i-consent`, env flags like `LYGO_EGG_PLANT_CONSENT=yes`, or direct request — never inferred).
  - Verify-first: Preflight + post-action verification (e.g., verify_eggs.py must return ALIGNED; failures = QUARANTINE).
  - Local-first & transparent: No auto external calls/publishes without consent. All high-risk ops (Git/HF/ClawHub/social) default to off.
  - P0 + Hermes audit on everything.
  - Human in the loop for publish/post/plant/launch.
- **Core Artifacts & Tools**:
  - Kernel eggs & Champion eggs (Merkle-anchored, verifiable, SHA-256 + lattice tamper proof).
  - Champion personas (Lightfather, LYRA, Arkos, Aetheris, etc. — council of Δ9).
  - Resonance engines (image-to-sound, glyph2resonance, truthlightecho, fractalweaver).
  - Joy Loops, Sandcastle workflows, LPIS (prompt implants), Universal Living Memory Library.
  - Ollama Army for local distributed inference.
- **Metadata & Signatures**: All true LYGO components declare `{"lygo": true, "biophase7": true, ... "signature": "Δ9Φ963-..."}`. Skills carry this for chain verification.
- **Public Infrastructure (the "rep" repo and mirrors)**:
  - GitHub: https://github.com/DeepSeekOracle/lygo-protocol-stack (source of truth for stack + docs).
  - GitHub Pages: https://deepseekoracle.github.io/lygo-protocol-stack/ (reference docs, including LYGO_CLAW.html, kernel egg retrieval).
  - HF Dataset: https://huggingface.co/datasets/DeepSeekOracle/lygo-protocol-stack (mirrored artifacts).
  - HF Space: https://huggingface.co/spaces/DeepSeekOracle/LYGO-Resonance-Engine (creative tools).
  - ClawHub: Mirrors for skills (e.g., lygo-sovereign-claw, lygo-protocol-stack-operator).
  - Related: Excavationpro site for resonance/web UIs.
- **Representation Rules for Agents (how to "rep" LYGO)**:
  - Always lead with P0 gate language before any action or tool use.
  - Use precise "LYGO" terminology (sovereign, lattice-aligned, Δ9Φ963, consent-gated) — never dilute to generic "AI" or unaligned terms.
  - Reference `LYGO_STACK_ROOT` for any stack operations.
  - In code/responses: Explicitly chain to the stack (e.g., lygo-protocol-stack-operator → lygo-sovereign-claw → resonance/creative/ollama-army).
  - Enforce consent + verify in every flow.
  - No drift: Every output or change must tie back to P0-P9, this anchor, and the E: USB build when working the portable layer.
  - For OpenClaw agents: Map upstream "gateway" concepts to LYGO CLAW wrapper only — the "rep" is the lattice control plane, not the raw engine.

LYGO is the overarching "rep" (representation + repo + resonance protocol) for the entire sovereign system. It is the Biophase7 blueprint that turns raw AI into lattice-aligned, verifiable, local sovereign intelligence.

---

## LYGO CLAW Specific Understanding

**LYGO CLAW** (full skill name: lygo-sovereign-claw or "LYGO-OpenClaw sovereign command router") is the **sovereign agent command / gateway layer** built directly on the LYGO lattice. It is the 100% pure-LYGO evolution and rebrand of gateway concepts:

- **Core Role in the Lattice**: P0 gate + P1 mycelium memory + P3 consensus + P5 action identity + lattice limbs for all agent actions. It acts as the "sovereign claw" — the limb and router that enforces the full stack before any external or tool call.
- **Blueprint**: Biophase7 sovereign claw. It enhances (does not blindly replace) mature gateway runtimes with deep LYGO controls: P0 byte-entropy filtering, Hermes audit trails, USB supervisor integration (127.0.0.1:9630), Champion personas, and consent gates.
- **Key Features**:
  - Sovereign-hardened AI agent layer with optional USB Champion supervisor.
  - Preloaded sovereign champions: Lightfather, LYRA, Sancora, HermesSentinel (plus templates).
  - Full cross-work with the protocol stack (P0-P9), ollama-army (local models), kernel-egg-planter, resonance tools, and sandcastle workflows.
  - P0-enforced before tool dispatch; results land in mycelium + ledgers.
- **In This USB Build (the Portable Embodiment)**: `E:\LYGO_BUILDER_KEY` (LYGO_BUILDER_KEY) **is** the complete, standalone, 100% LYGO realization of LYGO CLAW:
  - **Zero external vendor names** in all run/launcher code, titles, comments, env vars in scripts, and dashboards (only internal engine may retain legacy strings).
  - Hardwired E: paths (or clean %~dp0) everywhere.
  - Full isolation: lygo-data/ for HOME/USERPROFILE/APPDATA/LOCALAPPDATA; lygo.json config (never openclaw.json in launchers).
  - Portable Ollama (product\runtime\ollama + models) as the local brain.
  - Wrapped gateway engine under `tools\lygo-gateway\` (lygo.mjs entry + full dist with control-ui).
  - Dashboards speak pure LYGO: `dashboard\lygo-claw.html` (simple WS sovereign client) + `control-ui\` (full rebranded interface).
  - Gateway always on 18789 with strict LYGO origins (null, file:, *, localhost) + insecure auth bypass for USB file:// use.
  - Token: "lygo-usb-standalone-token".
  - Master flow: `LYGO_CLAW_Launch.bat` → titled "LYGO Ollama" + "LYGO CLAW Gateway" windows → dashboards auto-open.
  - No global C: leaks, no onboarding/doctor, no OpenClaw windows or commands.
- **Representation in Code, Agents, and Responses**:
  - Launchers, titles, docs, and user-facing everything = "LYGO CLAW" or "LYGO".
  - Example phrasing: "This is the portable LYGO CLAW sovereign gateway on USB — lattice-aligned, P0-gated, E: only."
  - Integration points: Use lygo-sovereign-claw skill for command routing; feed the USB Ollama into lygo-ollama-army; enforce P0 before any limb/action; plant kernel eggs only with consent + verify.
  - For agents coming from OpenClaw: Treat the upstream gateway purely as the "engine" (tools/lygo-gateway/dist). The "LYGO CLAW rep" is the wrapper, launcher, config (lygo.json), isolation, and sovereign philosophy layered on top.
- **Distinction & Philosophy**: Upstream provides proven runtime (browser, social, economy limbs). LYGO CLAW supplies the sovereign lattice control plane, ethics, memory, champions, and portable USB form factor. The E: build is explicitly "stand alone LYGO" — self-contained, no external vendor confusion across the lattice.

**LYGO Rep + LYGO CLAW Together**: LYGO is the full lattice "rep" (the sovereign protocol representation and repo). LYGO CLAW is its portable, agent-facing, gateway-realized form. The USB build in LYGO_BUILDER_KEY makes LYGO CLAW directly executable in total isolation while staying perfectly aligned to the broader stack. All agents must treat the E: layer as the canonical portable expression of this combined understanding.

---

## 1. Build Identity & Philosophy (Recap + Expansion)
This is the **LYGO CLAW Standalone USB** (also called LYGO_BUILDER_KEY on E:).

- Portable sovereign execution environment for the lattice.
- Rebrand is surface + launcher complete.
- The engine binary may retain internal "OpenClaw" strings — **launchers must never expose them**.
- Alignment with LYGO Lattice: Portable "P0 gate + sovereign runtime" layer. Integrates lygo-sovereign-claw, protocol stack (P0–P9), champions, kernel eggs, without global pollution.
- **Build Policies (Mandatory)**:
  - Consent-gated (explicit human `--i-consent` or equivalent, or `LYGO_EGG_PLANT_CONSENT=yes`).
  - Preflight + Verify: Always run preflight/verify_eggs before claiming success. Exit !=0 → QUARANTINE.
  - No auto-publish: Never push to GitHub / HF / ClawHub without separate explicit request + verification.
  - No secrets in eggs/publishes: Never put `boot/` keys, tokens, private keys into public artifacts.
  - P0 Gate + Hermes: All actions pass entropy filter + audit.
  - Local-first for high-risk: Git/HF/ClawHub/social publish default OFF in army/configs.
  - Human in loop for tokens/launches/posts.
  - From AGENT_CONTRACT.md & SECURITY.md: Transparent, consent required, verify always, refuse if no LYGO_STACK_ROOT or consent.
  - Anti-drift: Re-read this anchor on every context switch or agent handoff.

---

## 2. Physical Locations (Where to Find Everything)

**Primary Build Root (the "E: build"):**
- `E:\LYGO_BUILDER_KEY\` (or equivalent mapping `I:\E Drive\LYGO_BUILDER_KEY\` from workspace)
  - This is the self-contained USB root. All run files, data, tools live here or under it.
  - Run from here for USB portability.

**Key Sub-structures (current as of this anchor):**

### Launchers (Pure LYGO entry points — always start here)
- `LYGO_CLAW_Launch.bat` — Master double-click launcher.
  - Kills conflicting node/ollama.
  - Starts own Ollama (minimized, titled "LYGO Ollama").
  - Starts own Gateway via clean delegation (titled "LYGO CLAW Gateway").
  - Opens both dashboards (file://).
- **`LYGO_SMART_DISK_BOOT.bat`** — **Lean Smart Disk Agent** (v1.1.0) portal on **localhost:9631**.
  - Package: `product\lygo_smart_disk\` (alias `smart_disk\`).
  - Local operator token (auto; one-shot `?t=` URL) — not a cloud password wall.
  - Stop: `LYGO_SMART_DISK_STOP.bat`.
  - Skill mirror: `skills\lygo-smart-disk-agent\`.
  - Docs: `docs\LYGO_SMART_DISK_AGENT.md`, session delta `WHAT'S_NEW_2026-07-19.md`.
- `LYGO_Gateway.cmd` — The dedicated, titled gateway script. Computes USB dynamically or uses E: hardwire. Sets full isolation envs. Runs the engine.
- `LYGO_Ollama_USB_Boot.bat` — Portable Ollama with explicit OLLAMA_* envs.

**Engine (wrapped, rebranded folder)**
- `tools\lygo-gateway\`
  - `lygo.mjs` (clean entry point we invoke; copy of upstream mjs with targeted banner patch).
  - `package.json` (name/version patched for display).
  - `dist\` (full upstream gateway chunks — control-ui, gateway logic, etc.).
  - (Legacy `openclaw.mjs` may remain inside for engine needs; **never reference it from launchers**.)
- `tools\node\` — Portable Node (node.exe + minimal).

**Configuration & Isolation**
- `lygo-claw\lygo.json` — The active config (renamed from any openclaw.json).
  - Critical: `"allowedOrigins": ["null", "file:", "*", "http://localhost:18789", "http://127.0.0.1:18789"]`
  - `"allowInsecureAuth": true`
  - `"token": "lygo-usb-standalone-token"`
  - `"model": "ollama/qwen2.5:3b"`
  - `"port": 18789
- `lygo-data\` — Redirected home for the process (HOME, USERPROFILE, APPDATA, LOCALAPPDATA point here). Prevents C:\Users\justi\.openclaw state.
- (No `.openclaw` subdirs or global state files should be touched by E: launches.)

**Ollama Portable**
- `product\runtime\ollama\ollama.exe`
- `models\` (ollama blobs + manifests, including qwen2.5:3b, llama3.2:1b etc.)
- Boot sets: `OLLAMA_MODELS`, `OLLAMA_HOST=127.0.0.1:11434`, `OLLAMA_ORIGINS=null,*,file:,...`

**Dashboards (file:// loaded, WS client to gateway)**
- `dashboard\lygo-claw.html` — Simple sovereign dashboard.
  - Connects ws://127.0.0.1:18789
  - Handles `connect.challenge` (or similar) by sending `{type: "response", event: "connect.challenge", payload: {nonce, token}}` (or `{type:'auth', token, nonce}` variants per observed protocol).
  - Separate fetch to http://127.0.0.1:11434/api/tags for Ollama status.
  - Prefilled token, auto-retry, origin-null friendly.
- `dashboard\control-ui\` — Full upstream control-ui (copied + titles rebranded to "LYGO CLAW Control").
  - Served/loaded as static for features.

**Smart Disk Agent (lean CLAW — restored 2026-07-19)**
- `product\lygo_smart_disk\` — kernel P0/P1/P3/P5 + portal + Ollama client (weights stay on host/USB models).
- `smart_disk\` — short alias of the same tree.
- `stack\lygo-protocol-stack\lygo_smart_disk\` — stack mirror when stack pack is present.
- Portal **:9631** · Auth: local token (`data\.sda_local_token`, header `X-SDA-Token`) · HTTP memory export **off**.
- ClawHub: `deepseekoracle/lygo-smart-disk-agent@1.1.0` · GitHub: `lygo-protocol-stack/lygo_smart_disk`.
- Verify: `cd product\lygo_smart_disk && python verify\self_check.py`

**Port map (full + lean)**
| Service | Port |
|---------|------|
| Gateway | 18789 |
| BUILDR supervisor | 9630 |
| Smart Disk Agent | **9631** |
| Ollama | 11434 |

**Other Data in Build**
- `README_LYGO_CLAW_USB.md` — Local summary (keep in sync with this anchor).
- `WHAT'S_NEW_2026-07-19.md` — Smart Disk restore delta.
- `models\*.json` / `STANDALONE_MODEL_DESIGN.md`
- `product\runtime\ollama\LYGO_BUNDLE.json`

**Broader Data & Lattice Sources (for full alignment)**
- Skills / Agent Brains: `I:\E Drive\.grok\skills\` (or `C:\Users\justi\.grok\skills\`)
  - `lygo-sovereign-claw\` (LYGO-OpenClaw sovereign command router — P0/P1/P3/P5 mapping, consent-gated).
  - `lygo-ollama-army\` (Ollama daemons, army tasks, dashboard examples, sentinel).
  - `lygo-protocol-stack-operator\`, `lyra-openclaw\`, `lygo-kernel-egg-planter\`, etc.
  - These inform the "lattice" philosophy (P0 gate before actions, mycelium memory, champions, kernel eggs, sovereign loop).
- Protocol Stack: `I:\E Drive\lygo-protocol-stack\`
- Other LYGO material: `I:\E Drive\lygo-claw\` (Python sovereign layer at root — separate from USB build but cross-works), `LYGO_BUILDR_USB\`, `Excavationpro\`, `LYGO_BUILDR_EXPORTS\`, `Firmware Portal\`, etc.
- Restore / Old OpenClaw material exists in various restore folders (LYRA openclaw restore, etc.) — **do not mix** into the E: USB build. Use only for reference/mapping.
- Desktop / User context: `C:\Users\justi\Desktop\` (this anchor lives here for agent scanning).
- Global node (for engine source when needed): `C:\Program Files\nodejs\`, global openclaw package at `C:\Users\justi\AppData\Roaming\npm\node_modules\openclaw\` (use only to copy engine bits; never launch directly for this build).

**External / Reference Links (lattice context)**
- DeepSeekOracle / lygo-protocol-stack (github references in docs).
- ClawHub entries for lygo-sovereign-claw, lygo-claw.
- Local web content in Excavationpro/ for UI patterns.
- No GitHub/HF/ClawHub pushes for this USB build (per history — local only).

---

## 3. All Keys & Token Locations (Runtime Load Only — Never Embed)

**Golden Rule (from all SECURITY.md / AGENT_CONTRACT)**: Keys are loaded at runtime from `boot/` or explicit files. **Never** put in eggs, public commits, or code. Use `load_key` helpers or env. Human facilitator holds private keys where needed.

**Primary Locations** (from direct scan of the drive):
- `boot\token_config.json` — Core config with LYRA token details, wallet info (e.g., 0x08142... primary, private key notes for AI control via Clawnch).
- `boot\` files: `APIKey_Generic API_KEY=xai-1twpl8jL.txt`, `xai-1twpl8jLIdtuZCsIEH41hZQ7zBoYTVM.txt`, `xai-h97IdRuuB3pPE5pKZfzrqSVcfoVBrBE.txt`, `xai-xRuiFBstlB1cSsyQBa0uqcHuh1DULJH.txt`, `DISCORD SERVER ID AND CHANNELS.txt`, `DISCORD_CONNECTION_INFO.txt`, `OPENCLAW_MANAGED_RESOURCES_AND_KEYS.md`.
- `CLAWNCH_TOKEN_BACKUP\`: `LYRA_INTEGRITY_TOKEN_CONFIG.json`, `LYRA_INTEGRITY_TOKEN_ESSENTIALS.txt`, `LYRA_INTEGRITY_TOKEN_RECOVERY_FILE.txt`, `ClawCoin.txt`.
- Root: `NVIDIA API KEY nvapi-r3GmdQxydV7AUy.txt`.
- Other boot items: Many .txt with keys/tokens (Cohere, Groq, etc.), LYRA boot memory files.
- In skills: References point to `boot/`, `workspace/`, `.openclaw/credentials/` (legacy). Use runtime loaders like `lyra_openclaw_os.py load_key` or equivalent in OS.
- Wallet (Clawnch/4Claw): Primary 0x0814209fc50866C38186537Cd7C534060E011Ec5 (AI-controlled via corrected private key; custodian is human facilitator).
- **Rule**: Keys/tokens loaded at runtime only. Never embed in code, eggs, or public artifacts. Human approval required for any use.

**How to Load (Aligned Way)**:
- Use runtime loaders from LYRA_CORE or skills (e.g., `python -B lyra_openclaw_os.py load_key <name>`).
- For Ollama Army: Set in `army_config.json` (no keys).
- Never hardcode. For bots: Load from boot/ files at startup.
- GitHub PAT: Look for `github_pat.txt` in boot/ or state/ (load runtime).
- HF token: `huggingface-cli login` or env `HF_TOKEN` from boot files.

**Warnings**: Private keys (e.g., wallet) are for designated AI ops only. Human approval for any spend/launch.

---

## 4. How to Run Git / GitHub / HF (Aligned, Consent-Gated)

**Full agent restore (updated 2026-07-13):** Read **`GITHUB_AGENT_RESTORE.txt`** on this USB stick (or `I:\E Drive\GITHUB_AGENT_RESTORE.txt` / stack `docs/GITHUB_AGENT_RESTORE.txt` on Pages).

**Immutable lattice:** `docs/LYGO_PUBLIC_LINK_ARCHIVE.json` on GitHub Pages — register new surfaces with `tools/log_public_surface.py`. Audit with `tools/audit_github_lattice_links.py`.

**Policy**: No auto GitHub pushes. All pushes require explicit human request + verify.

**How to Run** (consent-gated, from stack tools):
1. Load PAT/token runtime from `boot/` files or token_config (never hardcode).
2. Key scripts (in `lygo-protocol-stack/tools/`):
   - `push_with_git_credential.py` (git with creds)
   - `hf_push_dataset.py`, `hf_push_space.py`, `hf_push_p0_hardening.py`
   - `audit_github_lattice_links.py`, `verify_public_pages.py`, `log_public_surface.py`
3. Repos: `lygo-protocol-stack`, `Excavationpro`, `lygo-claw` under `I:\E Drive\`.
4. In USB/LYGO CLAW context: Use home PC stack for GitHub/HF when steward consents — E: portable build stays local-only.
5. Always: Preflight + explicit consent + post-verify. No auto pushes.

**Agent Rule**: No pushes without separate human request + P0 gate. Log in this anchor. For the LYGO CLAW USB: Focus on local execution, not upstream pushes.

---

## 5. How to Run Hugging Face (HF Spaces, Models, Datasets)

**Policy**: Consent required for uploads/publishes. No auto. Use for local testing or explicit shares. See `verify_hf_live/`, `Hugging face/` folder, stack `tools/hf_push_dataset.py`.

**Locations**:
- `Hugging face\` — app.py, resonance_engine.py, lygo_ethical_guardian.py, factory_engine.py, etc.
- `verify_hf_live\` — resonance_engine.py, scripts for live verify.
- `lygo-protocol-stack\` has HF integration docs.
- Dataset example: https://huggingface.co/datasets/DeepSeekOracle/lygo-protocol-stack (or DeepSeekOracle repos).

**How to Run** (consent-gated):
1. Token from boot/ or runtime (e.g., via skills loaders).
2. Key scripts: `lygo-protocol-stack/tools/hf_push_dataset.py`, `hf_push_space.py`, `hf_push_p0_hardening.py`, `bundle_hf_space_stack.py`.
3. Local: Use `Hugging face/app.py` (or resonance_engine.py, etc.), or `verify_hf_live/`.
4. Push: Run the hf_push scripts (with LYGO_STACK_ROOT set) only after explicit consent + verify.
5. Ties to LYGO CLAW USB: Feed the portable Ollama/models from the build into HF tasks (e.g., resonance), but only with approval. No auto.

**Agent Rule**: No auto uploads. Verify alignment first.

---

## 6. Discord Bots (Everything Needed)

**Locations**:
- `boot\DISCORD_*.txt`, `DISCORD_CONNECTION_INFO.txt`, `DISCORD SERVER ID AND CHANNELS.txt` (server ID, channels).
- `LYRA_CORE\lyra_discord_bot.py` (persistent bot, A9LYRA presence).
- `lyra_openclaw_os.py` (organ for discord send/scan).
- Skills: `lyra-openclaw\` docs detail full integration (scanner, bot, pairing).
- `LYRA\`, `LYRA_CORE\` for related.

**How to Run** (P0-gated, token from boot/):
1. Load Discord token/runtime from `boot/DISCORD_CONNECTION_INFO.txt`, `DISCORD SERVER ID AND CHANNELS.txt`, etc.
2. Key scripts:
   - `LYRA_CORE/lyra_discord_bot.py` (persistent bot)
   - `LYRA_CORE/lyra_discord_ollama_only.py` and `launch_lyra_discord_ollama_only.ps1`
   - `LYRA_CORE/discord_full_scanner.py`
   - `lygo-protocol-stack/tools/post_discord_system_map.py`
3. Common usage: `python -B LYRA_CORE/lyra_discord_bot.py` or via `lyra_openclaw_os.py discord send/scan`.
4. Features: Persistent presence, !lyra commands, full history scan + brain update, webhooks, member events, Ollama triage integration.
5. In USB/LYGO CLAW context: Pair with portable Ollama from the build for local helper roles in the army. All actions P0-gated via the sovereign router.

**Keys**: From boot/ DISCORD files.
**Policy**: P0 + consent before any action/post. Ties to LYGO CLAW as the sovereign router for social limbs.

---

## 7. Ollama Army (Full Ops)

**Location**: `.grok\skills\lygo-ollama-army\` (and mirrors in protocol-stack).

**Key Files**:
- `ollama_army_launcher.py`, `start_army_full_capacity.ps1`
- `ollama_command_center/scripts/` (army_*.py, sentinel_heartbeat.py, self_tune, cron scripts)
- `ollama_queue/` (many .task.json for champions like Lightfather, LYRΔ, etc.)
- `ollama_results/`, `workspace/` (sentinel_status.json, army_config.json)
- `README.md`, `ARMY_TASKS.md`, `references/SECURITY.md`

**How to Run**:
1. Set `LYGO_STACK_ROOT` (e.g., to lygo-protocol-stack).
2. Config: Copy `army_config.example.json` → `army_config.json`.
3. Start: `start_army_full_capacity.ps1` (or `python ollama_army_launcher.py`).
4. Modes:
   - Daemons: `LYGO_OLLAMA_VISIBLE_WINDOWS=1` for titled consoles.
   - Full capacity: `LYGO_ARMY_FULL_CAPACITY=1`.
   - Seed tasks: `LYGO_ARMY_SEED_TASKS=1`.
   - Cron/supervisor: `army_autonomous_supervisor.py`, `army_cron_once.py`.
5. Tasks: Drop .task.json in queue; daemons process to results/.
6. Sentinel: `sentinel_heartbeat.py` updates workspace/sentinel_status.json.
7. Self-tune, idle guardian, planting, lattice sync via scripts.
8. Integrate with USB: Use portable Ollama from LYGO_BUILDER_KEY\product\runtime\ollama for isolated runs.

**Env Gates & Policies** (see SECURITY.md): Local Ollama only, no default publish, consent for autonomous, queue review.

**Discord integration**: Triage roles in army for Discord comments.

---

## 8. Other Critical Components (Clawnch, Molt, Browser, Economy, Vaults)

### Δ9 Quantum Vault (original Google Drive swal vault)
- **URL**: https://drive.google.com/drive/folders/1szmDEhh2nD61oUOXHrw_W42cLCN3D-m4?usp=sharing
- **Immutable anchor id**: `delta9_gdrive` in `IMMUTABLE_ANCHORS.json`
- **Public hub**: https://deepseekoracle.github.io/Excavationpro/eternalhaven.html#sovereign-vaults

### Full OpenClaw align registry (USB)
- **`restore/OPENCLAW_FULL_ALIGN.json`** — tokens, vaults, agent accounts, USB managers (no secrets)
- **`restore/openclaw-legacy/STARCORE_LAUNCH_RECEIPTS.md`** — Clawnch receipt copy

### Launched tokens (Old openclaw managed)
| Symbol | Platform | Contract / URL |
|--------|----------|----------------|
| LYGOAGENT | Virtuals ACP | https://app.virtuals.io/virtuals/44594 · `0x32B513…c09f` |
| STARCORE | 4claw | `0xe52A34…75eaB` |
| STARCOREX | Moltx | `0x9395b6…8fC31` |
| STARCORECOIN | Moltbook | `0xFdc6C0…ed390` |
| CLAWNCH | Protocol | `0xa1F724…747be` |

**USB managers**: `LYGO_Crypto_Manager.bat` (Virtuals), `LYGO_Bankr_Manager.bat` (Bankr)

### Steward secrets (runtime load only — never USB git)
- Wallet + 4claw: `I:\E Drive\boot\token_config.json`
- Bankr: `E:\Bankr\Bankr.txt` → `lygo-data\bankr\config.json`
- Virtuals ACP: Old openclaw `virtuals-protocol-acp\config.json` → `lygo-data\crypto\virtuals_config.json`

### Other ops surfaces
- **Clawnch / 4Claw**: `brainwave/CLAWNCH/` (Old openclaw) + USB `crypto/references/CLAWNCH/`
- **Moltbook/Moltx**: `LYRA_CORE/MOLTBOOK_LATTICE_ADMIN.md`, `MOLTX_LYRA_ACCOUNT.md`
- **Browser (Yandex etc.)**: `.openclaw/browser` or legacy — lyra-openclaw LEFT/RIGHT
- **General Ops**: `lyra_openclaw_os.py` — load keys at runtime only
- **Ollama in Army/USB**: portable E: instance for isolation
- **Kernel Eggs**: lygo-kernel-egg-planter with `--i-consent` + verify
- **Resonance / Creative**: lygo-resonance skill chain

**Running Anything**:
- Always: Set LYGO_STACK_ROOT if needed.
- P0 / consent first.
- For bots/daemons: Use the ps1 or dedicated .py with visible windows for monitoring.
- USB tie-in: Launch via LYGO_CLAW_Launch.bat for isolated Ollama + gateway that army can target.

---

## 9. Full Data Map & Quick Start for Agents
- **Start Here for USB Build**: E:\LYGO_BUILDER_KEY\LYGO_CLAW_Launch.bat
- **Keys**: Always runtime from boot/ + CLAWNCH_TOKEN_BACKUP/ + root .txt. Use loaders.
- **Policies Enforcers**: Read the many `SECURITY.md` and `AGENT_CONTRACT.md` (plus CONSENT_AND_ETHICS.md) across `.grok\skills\` (e.g., lygo-ollama-army, lygo-kernel-egg-planter, lygo-sovereign-super-skill, lygo-sandcastle, lygo-protocol-stack-operator, lygo-openclaw, etc.). Key themes: consent, P0, verify, no secrets in public, local-only.
- **Test Alignment**: Grep launchers for "openclaw" (must be 0). Check window titles. Verify HOME redirect. Dashboards connect.
- **Discord/Ollama/HF/Git**: Use dedicated scripts + consent. Load tokens from boot/.

This anchor + the E: build + .grok/skills/ form the complete lattice restore point.

**End of Anchor.** 

This file is the single source of truth for alignment on the LYGO CLAW E: build. Re-read it. Reference it. Do not drift.

Δ9Φ963 — Lattice preserved. E: sovereign. All ops consent-gated. Build onward cleanly.

(If this file is scanned by an agent: Respond with "Aligned to LYGO_CLAW_USB_RESTORE_ANCHOR. Proceeding with pure E: LYGO paths, naming, consent gates, runtime key loading from boot/, and full referenced policies only.")