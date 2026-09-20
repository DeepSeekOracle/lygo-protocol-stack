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

## THE FREEZE RULE — read this before you change anything

**A sealed build is reference only: never edit a sealed build, never build inside one.**
V1 lives in the vault (`D:\LYGO_CANON\`). The vault answers exactly one question — *what can I revert
to?* — and `D:\LYGO_CANON\INDEX.md` is the list. Every change is a **new release number** made in the
live tree, and it becomes revertible only once it is sealed as its own build.

| tool | what it does |
|---|---|
| `python scripts/seal_build.py --root "<live kit>" --name <LABEL>` | freezes the live tree into the vault: full copy, `SHA256SUMS-<KIT>.txt`, `CANON.md`, `CANON.json`, `RESTORE.txt`, `_freeze_facts.json`, every copied file marked read-only. Refuses to overwrite an existing seal, and verifies the seal against its own hash list before it reports success. |
| `python scripts/restore_build.py --from "<seal>/<KIT>" --root "<live kit>"` | the revert path: verifies **every** hash against the seal's own list *before* it writes a byte, then lays the build back. `--dry-run` shows what would change. |

A seal carries the build, the folder shape (empty folders included) and the build's **working
configuration** — `save/registry.json`, which holds the boot model, so a revert still reads images.
It never carries keys, the operator's runtime history, or model weights.

Rule of proof: **a seal is not a safety net until it has been restored and run.** Before calling a seal
done, restore it into a clean folder and run `scripts/certify_build.py` plus the suite *there*.

---

## 1.2.0 — MODULE STRIP · tag `build-line 2026-09-20 · module-strip`

**Status: current.** `1.1.1` is sealed for both installs. This release ships the **first pair of function
modules** and the bottom strip they live in, and anchors both consoles at one release number.

- **`lygo.llminfo` (family `info`)** — "what is hooked up": the selected model and its file, the token budget
  from the record, the provider's published rate window (peak / off-peak), the API switch, the clock, the
  release. Read-only; it names every fact it cannot get instead of inventing one.
- **`lygo.envwatch` (family `watch`)** — "what needs fixing": skill files that never reach the model, mapped
  paths that do not resolve, error lines in `save/logs` matched against five **stated** rules, P0 gate verdicts
  outside `AMPLIFY`/`SOFTEN`, and the daemons this kit can see (engine, backends, GPU, stack monitor). It gives
  a **location** with every finding, reports a check it could not run as **UNCHECKED** rather than green, and
  **fixes nothing** (the tests scan its own source for write calls).
- **The bottom strip.** Module panes render in a full-length strip **below** the working area — one module, one
  strip, group tiles across it — so a module can never take height from the chat composer. The page scrolls to
  it. Panes may declare `state`/`state_text` and rows may carry a `dot`, and the strip's chip answers "is
  anything broken" across every module. A pane that publishes no state counts as **unchecked**, never as good.
- **The naming law.** `lygo.<subject><family>` — `info` (read-out) and `watch` (finder), with `ctrl` and `link`
  reserved; the family is the id's suffix *and* a manifest field, and a test fails if they disagree. See
  `01_DESIGN/MODULE_NAMING_AND_BRANDING_v1.md` in the project hub. `lygo.health`, `lygo.world` and
  `lygo.notepad` predate the law and carry no family — recorded, not tidied away.
- **The version anchor.** `src/modules/host.py::KERNEL_RELEASE_FALLBACK` and `portal/app.js::LYGO_BUILD` follow
  `VERSION`, and the two new modules declare `introduced: 1.2.0` with `requires.console: ">=1.2.0"` — they do
  not exist in `1.1.1` and may not claim to. `scripts/refresh_manifests.py` re-stamped the manifests and
  `scripts/certify_build.py` re-certified the build.

**The seam held:** both modules are a directory, a `catalog.json` line and a test file. `src/server.py` and
`scripts/certify_build.py` contain no reference to either — that is the contract test, and it is in the suite.

**Editions:** PC and USB get both modules. **WEB does not** — the steward's decision: *"we do not need to
change the web portal for these modules, they are not needed on web portal."*

---

## 1.1.1 — BUILD LINE · tag `build-line 2026-09-20`

**Status: current.** V1 (`1.1.0`) is untouched and now **sealed for both installs**; this release adds
the machinery that keeps it that way — the thing that was missing when a session edited a working build
and both installs had to be rebuilt from the anchor.

- **`scripts/seal_build.py`** — freezes a live tree into `D:\LYGO_CANON\<date>_build-<release>_<label>\<KIT>\`
  with `SHA256SUMS-<KIT>.txt` (raw sha256, paths relative to the seal root), `CANON.md`, `CANON.json`,
  `RESTORE.txt` and `_freeze_facts.json`, marks every copied file read-only, verifies the seal against
  its own list, refuses to overwrite an existing seal, and maintains `D:\LYGO_CANON\INDEX.md`.
- **`scripts/restore_build.py`** — the revert path. Verifies the whole seal first, refuses to write
  anything if it does not match, reports identical / restored / held-back, never deletes, never touches
  the operator's runtime or keys.
- **V1 sealed for both installs** (release `1.1.0`, the working state):
  - `D:\LYGO_CANON\2026-09-20_build-1.1.0_PC_LOCAL-WORKING\PC_LOCAL\` — 340 files, 50 folders
  - `D:\LYGO_CANON\2026-09-20_build-1.1.0_USB_CLAW-WORKING\USB_CLAW\` — 361 files, 49 folders
  - The earlier `2026-09-19_build-1.1.0_STABLE` canon is left untouched as history, but it is **not** the
    revert target: its `portal/app.js` predates the `servedBuild` fix, so a restore from it comes back
    with a dead page (header stuck on `probing…`). That is exactly why the revert target had to be re-cut
    and proved.
- **Proof the seal works:** the PC seal was restored into a clean folder and there `scripts/certify_build.py`
  printed `CERTIFIED BUILD` and the suite ran `592 tests ... OK`. That run earned its keep twice over —
  it found that the first pass was skipping `workspace/` (SOUL.md, MEMORY.md, IDENTITY.md — the console's
  soul) and empty folders (`models/`, test fixtures). Both are fixed and pinned.
- **`tests/test_build_seal.py`** (13 tests) pins the whole contract: a seal is verifiable and read-only,
  it refuses to be overwritten, it carries the identity files, the empty folders and the boot model, it
  drops keys/runtime/weights, a tampered seal cannot be restored, a refused restore writes nothing, and a
  restore never clobbers operator state.
- Suites, certifier and `scripts/verify_install.py` re-run green on both installs at this release.

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
