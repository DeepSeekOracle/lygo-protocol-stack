# LYGO Local Agent Console 1.3.1 — installers built from this session

**Built 2026-09-22.** Payloads are the sealed 1.3.1 builds; nothing here was edited after sealing.

| installer | where it is | size | weights |
|---|---|---|---|
| `LYGO_LLM_CONSOLE_1.3.1_PC_SETUP.exe` | `D:\` | 1.10 GB | **not inside** — `models\fetch_models.py` pulls them from our own vault |
| `LYGO_LLM_CONSOLE_1.3.1_PC_SETUP_FULL.exe` + 4 × `.bin` | `D:\` | 13.6 GB | **all four inside**: gemma4-12b (7.4 GB) + its projector (175 MB) + qwen2.5-coder-7b (4.7 GB) + nomic-embed (274 MB) |
| `LYGO_LLM_CONSOLE_1.3.1_USB_SETUP.exe` | `E:\` (on the stick) | 562 MB | **not inside** — the stick has ~3 GB free; fetcher or the vault on the host |
| `LYGO_LLM_CONSOLE_1.3.1_USB_SETUP_CODER.exe` + 2 × `.bin` | `D:\` | 5.26 GB | **the coder inside** (4.7 GB); gemma4 via `--profile basic` |

Windows cannot load a single Setup.exe larger than ~4.2 GB, so the two weight-carrying installers
span files: **SETUP.EXE and its `.bin` slices must stay in the same folder.** The weights are stored
*nocompression* (they are already quantised); everything else is `lzma2/max`.

## What was proved, not assumed

- **The payload was sealed, not copied by hand.**
  `scripts/seal_build.py` → `D:\LYGO_CANON\2026-09-22_build-1.3.1_PC_LOCAL` (1423 files, hash list, read-only)
  and `…_USB_CLAW` (820 MB). Both are the reference you revert to.
- **A silent install was run, and the installed console was booted and measured** (PC installer,
  `/VERYSILENT /DIR=D:\LYGO_INSTALL_TEST_131`): exit 0, `VERSION` = 1.3.1, engine + backends landed,
  `config\console.json` carried, and the installed copy booted its own engine on **CUDA**
  (`backends.py status` → `active: cuda`) and answered:

  | ask | result from the *installed* copy |
  |---|---|
  | `Reply with exactly: INSTALLED BUILD OK` | 1.07 s · 4 generated / 4 shown · 0% unseen · cap 24 · `shape exact` · limbs 0 |
  | `In one sentence, what is the LYGO protocol stack?` | 1.96 s · 49 generated / 49 shown · 0% unseen · cap 72 · 51.6 tok/s |

  That is 1.3.1's whole point, running from an installer rather than from the dev tree.
- **The engine binaries are the kit's own**: `engine\llama-server.exe` (9,216 bytes, the modular
  loader) plus `engine\backends\{cuda, cuda-b10988, vulkan}` and the per-CPU `ggml-*.dll`s.

## The two defects this build had to fix before it could ship

1. **The shipped config would have booted an installed copy with no brain.** `scan_roots` was
   `["I:/LYGO_MODELS"]` — this machine's vault. The installers place weights in `<install>\models`,
   which nothing scanned. Both copies now ship `["I:/LYGO_MODELS", "./models"]`, so the vault still
   wins here and an installed copy scans what the fetcher fills. (Defect ledger 123.)
2. **Recovery went through the wrong tool.** `git checkout -- config/console.json` restored *committed*
   values (ctx_default 4096, ctx_max 32768, flash_attn off) because 1.3.0's settings only ever existed
   in the working tree. Recovered from the sealed 1.3.0 canon, which is the authority for what shipped.
   **Rule: on this tree, the sealed canon is the recovery source; git is not.** (Ledger 122.)

## How a future session rebuilds these

```bash
# 1. seal the payloads (reads the release number from VERSION)
python scripts/seal_build.py --root "I:/E Drive/lygo-protocol-stack/lygo_llm_console" --name PC_LOCAL --kit PC_LOCAL
python scripts/seal_build.py --root "E:/LYGO_BUILDER_KEY/lygo_llm_console"        --name USB_CLAW --kit USB_CLAW
# 2. compile (Inno Setup 6 is installed per-user)
"C:/Users/justi/AppData/Local/Programs/Inno Setup 6/ISCC.exe" lygo_pc_131.iss
```

The `.iss` sources live in `%LOCALAPPDATA%\Temp\lygo_installer\` (`lygo_pc_131.iss`,
`lygo_pc_131_full.iss`, `lygo_usb_131.iss`, `lygo_usb_131_coder.iss`) with the install notes each one
shows after the wizard. They are also copied into the tree at **`installer/`** (and the USB pair onto the
stick at `E:\lygo_installer_src\`), so the recipe outlives `%TEMP%` — a build recipe kept only in temp is
one cleanup away from being lost.

The **FULL** installer was silent-installed too (`/DIR=D:\LYGO_INSTALL_131_FULL`, exit clean, no restart
needed) and all four weights landed byte-for-byte against the vault: `gemma4-12b.gguf` 7,381,382,048 ·
`gemma4-12b-mmproj.gguf` 175,115,584 · `qwen2.5-coder-7b.gguf` 4,683,074,048 ·
`nomic-embed-text-latest.gguf` 274,290,656, beside `models.lock.json`, `fetch_models.py`, the vault
`manifest.json` and `sidecars\`. gemma4 itself was **not** booted in this pass (it wants ~10 GB of RAM,
and this box has an 8 GB card — the coder is the boot brain here, as instructed).

## Published (2026-09-22)

Everything below was rebuilt **after** the pre-publish scan and is what is live now.

| | |
|---|---|
| vault revision | `DeepSeekOracle/lygo-console-builds` @ **`console-v1.3.1`** (HuggingFace, public) |
| digests | `SHA256SUMS.txt` on that revision — verified byte-identical to the local file after upload |
| page | **https://chatagent.ca/lygoskillhub.html** (`#builds`, ALPHA box; catalog 1.5.0 → 1.6.0, 117 → 121 items) |
| commit | `chatagent` repo, "SkillHub: post LYGO LLM Console 1.3.1 ALPHA installers…" |

| file | bytes | sha256 (first 8) |
|---|---|---|
| `LYGO_LLM_CONSOLE_1.3.1_PC_SETUP.exe` | 1,104,854,694 | `53b35c19` |
| `LYGO_LLM_CONSOLE_1.3.1_USB_SETUP.exe` | 562,567,133 | `65b2dd3d` |
| `LYGO_LLM_CONSOLE_1.3.1_PC_SETUP_FULL.exe` + 4 `.bin` | 13,617,574,663 | `13489007` + slices |
| `LYGO_LLM_CONSOLE_1.3.1_USB_SETUP_CODER.exe` + 2 `.bin` | 5,245,668,019 | `899ee95f` + slices |

Post-upload verification (read back from the remote, not from the uploader's log): every file resolves
at exactly the byte count that was hashed, and the remote `SHA256SUMS.txt` has the same SHA-256 as the
local one. The page's own links were fetched live and the alpha box is present.

**Pre-publish scan — the gate that mattered.** The installed tree was scanned for credentials and for
the steward's own runtime state before anything was posted. It found the transcript archive (778 files)
and a bench log inside every installer, and — from the earlier pass — a scan root that only worked on
the studio PC. Both fixed, all four installers rebuilt, scan re-run clean (defect ledger 123–125).
A note on a fresh *public* install: the cloud API endpoints read "not configured" because no keys ship
(by design) — two of `scripts/verify_fixes_live.py`'s four cloud scenarios therefore fall back to the
local brain on a fresh machine, while the same four are **ALL PASS** on the dev copy.

## Known, stated plainly

- The USB installer builds the **stick** copy (ports 9651 / 11451, own Python). Its default target is
  derived from where the installer runs: run it from the stick and it installs to the stick's own layout.
- The stick has ~3 GB free, so **no** weight-carrying installer can be written to it directly; the coder
  variant writes to `D:\` and is meant to be copied to a roomier stick.
- The FULL installer's brains land in `<install>\models`; the copy boots the coder first per
  `prefer_ids` (the operator's "use the coder on both"), with gemma4-12b one click away.
- `tools\` and `web_portal\` ship as-is; the gauntlet's T7/T11/T12 mechanism gaps are unchanged by 1.3.1.
