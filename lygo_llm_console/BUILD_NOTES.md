# BUILD NOTES — Δ9Φ963 · LYGO Local Agent Console

The release number lives in **`VERSION`** (line 1; optional human tag on line 2). Bump that one file and the
console header, `/api/health` and the runtime facts the model is told all move together — see
`src/version.py` for why that file exists (the release used to be stamped in three places that could
disagree).

Two installs, one code base:

| | PC LOCAL | USB CLAW |
|---|---|---|
| kit | `I:\E Drive\lygo-protocol-stack\lygo_llm_console` | `E:\LYGO_BUILDER_KEY\lygo_llm_console` |
| launcher | `LYGO_LLM_CONSOLE.bat` | `LYGO_AGENT_STICK.bat` (root shim `LYGO_CLAW.bat`) |
| ports | console 9641 / engine 11441 | console 9651 / engine 11451 / embed 11452 |
| default model | `gemma4-12b` (vision) | `llama3.1:8b` (text, from its own CAS) |
| its own storage | vault `I:\LYGO_MODELS` | `E:\LYGO_BUILDER_KEY\product\models\ollama` |

---

## 1.1.0 — STABLE ANCHOR · tag `stable-anchor 2026-09-19`

**Status: STABLE.** Frozen as CANON in `D:\LYGO_CANON\2026-09-19_build-1.1.0_STABLE\` (`PC_LOCAL\` +
`USB_CLAW\`, SHA256SUMS beside them, marked read-only). The canon is *reference only* — build forward in the
live trees, never edit a canon copy.

**Verified on both installs, at this exact state:**

- **Suite:** 582 passed / 7 subtests — run on the PC tree *and* on the stick tree, each on its own tree.
- **`scripts/certify_build.py`:** `CERTIFIED BUILD` on both — files match the published manifest, license intact.
- **`scripts/verify_install.py`:** `ALL GOOD` — 27 checks, 0 failed, on both installs.
- **Zero-Ollama:** the kit boots its **own** `engine/llama-server.exe` (llama.cpp b10988) on GGUFs it owns;
  no daemon is started or subprocessed anywhere in the path.
- **Vision (PC), and this is the steward's own test:** `gemma4-12b` + `gemma4-12b-mmproj.gguf`, engine log
  `load_model: loaded multimodal model, 'I:\LYGO_MODELS\gemma4-12b-mmproj.gguf'`. A 64 px control photo
  (left half red, right half blue) answers `Red, blue.`; the steward pulled a real image through the portal
  and the model **described it correctly** (2026-09-19). `/api/health`: `selected=gemma4-12b vision=true`.
  The projector is wired by one rule (`registry.mmproj_for`) shared by the engine boot, the vision limb, the
  console's own guard and the scanner — a vision model cannot boot blind without the console saying so.
- **Attachments:** a photo rides the message as an `image_url` part (the engine's projector reads it, ≤1600 px
  JPEG); a small text file is inlined into the message; anything else lands in `workspace/uploads/` and the
  **host** reads it (`read_file`, `host: true`) so its text reaches the model without the model having to
  remember a limb call.
- **Launcher:** `LYGO_LLM_CONSOLE.bat` / `LYGO_LLM_CONSOLE_STOP.bat` print what `taskkill` actually answered,
  retry, escalate (`Stop-Process`, WMI terminate), and name an **elevation denial** with the fix instead of
  looping. Desktop twin: `LYGO PC CONSOLE STOP.bat`.

**Known limits at this anchor — do not overclaim:**

- **The stick does not carry a vision model.** 5 of its 14 registry records are its own (its `E:` CAS); the
  other 9 resolve to this PC's stores, `gemma4:12b` among them, so on another machine they simply are not
  there. Its default `llama3.1:8b` answers text. Photos on the stick need either an inlined file or a model
  the stick actually holds — a small VLM (~2 GB) as the `image_see` runner is the stand-alone answer.
- **Image generation is not in this kit.** `llama-server` is text + vision; generation needs its own
  diffusion service (e.g. `stable-diffusion.cpp`) behind a new limb.
- **Tool-choice bench:** the 24-ask run has not been repeated since the local schema grew 20 → 22 tools
  (the two vision limbs). A green suite does not measure tool *selection*.

**Signatures in force:** `Δ9Φ963-LICENSE-v3.0` · `Δ9Φ963-LYGO-BRANDING-v1` · `Δ9Φ963-LYGO-SESSIONS-v1` ·
`Δ9Φ963-LYGO-COMPACTION-v1` · `Δ9Φ963-SUCCESSION-PROTOCOL-v1`. `LICENSE` = `91a34b504e9e9ae7` / 26044 B.

---

## How the next release is made (the only way that keeps the anchor honest)

1. Change code/tests in the live tree `I:\E Drive\lygo-protocol-stack\lygo_llm_console`.
2. Bump `VERSION` line 1 — **next after this anchor is `1.2.0`** — and add a section at the top of this file.
3. `python scripts/refresh_manifests.py --note "<why>"` then `python scripts/certify_build.py`.
4. `python -m pytest -q` on **both** trees; mirror the changed files into the stick kit.
5. Commit from the repo root with **explicit paths** (never `git add -A`).
6. Hand the steward the ready-to-publish state. **Agents build and verify; the steward publishes.**

Agents do not push, and do not touch a canon copy.
