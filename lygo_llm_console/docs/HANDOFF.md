# Handoff — `lygo_llm_console`: continue the debug + enhancement pass

**Written 2026-09-20 by the session that completed CUDA. Written for a fresh session with no memory of that
pass. Read it top to bottom before touching code.** Every number below was measured on this box; where a number
can drift, the command that re-derives it is given beside it. Its procedure companion is `docs/RECOVERY.md`
(health check, CPU fallback, contended verdicts, strays, overlays, logs). The record behind both is
`docs/BUILDERS_LOG.md` (entries C1-C15) and `docs/DEFECT_LEDGER.md` (24 findings, 8 open).

**Nothing in this pass was committed, pushed or sealed.** 59 entries sit uncommitted in the stack repo.

---

## 0. Start here — the first ten minutes

```bash
cd "/i/E Drive/lygo-protocol-stack/lygo_llm_console"          # the LIVE tree; always this one
C:/Python313/python.exe -m pytest -q                          # expect: 915 passed, 27 subtests (~3-4 min)
C:/Python313/python.exe scripts/certify_build.py              # expect: VERDICT: CERTIFIED BUILD
C:/Python313/python.exe src/backends.py status                # expect: active "cuda", engine_dir ...\engine\backends\cuda
```

Then read, in this order: this file, `docs/DEFECT_LEDGER.md` (open rows only), `docs/ARCHITECTURE_MAP.md`
(2: the engine chain; 4: the invariants). Then choose work from sections 7 and 8 below.

**Before any engine work, check the card is free** — a self-test beside a live engine is what wrote off a
working GPU twice on 2026-09-20:

```bash
tasklist /FI "IMAGENAME eq llama-server.exe" /FO CSV /NH   # must say "No tasks are running"
nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv
```

## 1. What this kit is, and where it lives

A portable local-LLM console: Python host + its **own** llama.cpp engine + a browser portal, built as one
product in three stand-alone editions that must stay in step. **Zero-Ollama is the architecture rule** — the
kit runs its own engine, its own model stores, its own ports; a daemon path must never enter a limb or a
service.

| edition | path | ports |
|---|---|---|
| **PC** (the reference build; author here) | `I:\E Drive\lygo-protocol-stack\lygo_llm_console` | console 9641 · engine 11441 |
| **USB** (`ESD-USB`, 28.8 GB, 3 GB free) | `E:\LYGO_BUILDER_KEY\lygo_llm_console` | console 9651 · engine 11451 · embed 11452 |
| **WEB** (`chatagent.ca/portal/`) | `D:\chatagent\portal` | browser limbs only |

- **Repo root is the stack, not the kit**: `I:/E Drive/lygo-protocol-stack`. Commit with explicit paths
  (`lygo_llm_console/src/...`), never `git add -A`; `docs/lygo-claw-usb/**` and other subdirs share the repo.
- **Version**: `VERSION` (line 1 `1.3.0`, line 2 a human tag) is the single source; `src/version.py` exposes it,
  `server.BUILD = version.stamp()`, `/api/health` serves `build`/`release`/`release_tag`. Current tag:
  *build-line 2026-09-20 · module-strip · memory + guard modules · long-reply tuning · media limbs ·
  standalone vocabulary*.
- **Project hub** (design, module contract, parity, build log): `D:\LYGO_LLM_CONSOLE_PROJECT\` —
  `00_START_HERE`, `01_DESIGN` (PARITY_MATRIX_v1.md, MODULE_REGISTER_v1.md), `02_BUILD_FRAMEWORK`
  (BUILD_LOG.md, BUILD_WORKFLOW.md, the release checklist), `03_ARCHIVE`, `04_MODULES`, `05_WORK_ORDERS`
  (WO-0001…WO-0005), `06_SOURCE_NOTES` (333 hash-verified archive copies + `REFERENCE_INDEX.md`),
  `99_REFERENCE`. **Read `06_SOURCE_NOTES/REFERENCE_INDEX.md` before re-deriving anything.**
- **Interpreter is always `C:/Python313/python.exe`**, never the system `python`.
- `python src/backends.py` — not `python -m src.backends`.
- Ports in use by neighbours that this kit must never claim: `8080` (host studio web apps), `11434`
  (Ollama's own default, if a daemon runs), `9631` (CLAW agent UI), `9744` (proof port), `9651` (the
  steward's running stick console — **never stop it**).

## 2. The laws (verbatim, still in force) and the working conventions

1. *"Parity law: every functional or UI change lands on all three editions, or carries a written
   DEGRADED(reason) / N/A(reason). Silence is not an answer."*
2. *"Ladder: author on PC only -> test there -> promote to USB per-file (never a recursive kit overwrite),
   hash-verified -> test on the stick -> web or declared N/A -> register + BUILD_LOG row -> seal -> the steward
   publishes. A fix found on the stick goes to PC first."*
3. *"Publish gate: nothing goes to HF/GitHub/ClawHub/the live site until the module is complete, tested and
   sealed — and the steward publishes, not you. Do not push."*
4. *"No secrets anywhere — code, docs, hub, git, stick."*
5. *"Commit with explicit paths (never git add -A); never force-push."*
6. *"Modules never grow the kernel sideways: if the module needs a kernel change, stop and say so."*
7. *"Do not stop the steward's consoles — the stick console on 9651 is his running session."*
8. *"Re-derive versions, counts and ports; never quote them from memory."*

Conventions this pass proved worth keeping:

- **Log the defect the moment you see it, then fix one at a time** (the steward's ordering). `docs/DEFECT_LEDGER.md`
  gets the row when it is found, not when it is fixed.
- **A fix is closed by a test or a measurement, never by reasoning.** Add the failing case first where you can.
- **Correct your own work in the same log.** Entries C10, C13, C14 exist because the fix was wrong or the
  measurement was misread.
- **An unstated value is not a zero, and a skip is not a verdict** (map invariants 9-12).
- **Verify the field, not the guess**: twice in one pass a wrong key looked like a missing feature
  (`gpu_ok` on `backends.report()`; a top-level `gen_tps` in `/api/models`). Ask each owner for its own field.
- **No push, no seal, no canon write** this round — the steward publishes.

## 3. Verified state at handoff (claim -> how to re-prove it)

| claim | re-prove with | expected |
|---|---|---|
| suite green | `C:/Python313/python.exe -m pytest -q` | **915 passed, 27 subtests** |
| build certified | `C:/Python313/python.exe scripts/certify_build.py` | `VERDICT: CERTIFIED BUILD` (11/11 BRAND + 11/11 SESSIONS, 7 modules) |
| console runs the GPU build | start it, read `/api/health` | `engine_dir …\engine\backends\cuda`, `build v1.3.0` |
| CUDA backend proven on this host | `C:/Python313/python.exe src/backends.py status` | `active "cuda"`, verdict `ok`, `model_load_ok`, ~11-15 s |
| Vulkan path exists for non-NVIDIA rigs | `C:/Python313/python.exe src/backends.py test vulkan --threads 6` | `ok`, `model_load_ok`, ~10.6 s (writes a verdict; leave CUDA active after) |
| model box complete | console `/api/models` | 19 records / 26 names, every file present |
| rates reach the picker | console `/api/models` -> each record's **`checked`** block | `checked.gen_tps`, `checked.prefill_tps`, `checked.boot_s`, `checked.why` |
| uncommitted, unsealed | `git -C "I:/E Drive/lygo-protocol-stack" status --short` | 59 entries (38 modified, 21 untracked) |
| stick is behind | `diff -rq --strip-trailing-cr -x __pycache__ <live>/src <stick>/src` | 27 files to promote (section 10) |

Box, re-derived 2026-09-20 (re-read it, do not quote this table): RTX 4060 Ti **8187 MiB, driver 616.92** ·
i5-13600KF **6 P / 8 E / 14 physical / 20 logical**, `auto_threads()` = **6** (fast cores, not logical) ·
RAM **~31.8 GB** installed (~20.6 GiB free at the time) · `C:` 930 GB (48 free) · `D:` "LYGO TURBO DRIVE" 476 GB
(208 free) · `E:` "ESD-USB" 28.8 GB (3 free) — **the stick** · `F:` SmartDisk removable (empty reader) ·
`I:` "MUSIC ONLY" 3725 GB (2114 free) — the kit · `J:` "BULK SAVE" 3725 GB (723 free). `perf.host_id()` =
**`GamePC|20`**. `wmic` is gone from Windows 11 — use `tasklist`/`nvidia-smi`/`perf`.

## 4. The engine: how a boot picks a backend, and the seven rules

`engine/backends/cuda/` is a **complete launch directory** (`kind: "engine"`, tag `b10988` — the same build as
base — `ggml-cuda.dll` plus the CUDA 13 runtime, 740,119,724 bytes, per-file sha256 manifest, `verified: true`).
Activating it is a **pointer swap, nothing is copied**. `engine/.gitignore` is `*`, so the 780 MB backend store
can never reach the repo.

Chain: `lygo_engine.boot()` -> `backends.ensure(host=perf.host_id())` -> remembered verdict, else apply/look
for a device, else load a real model -> on success `activate()` + `set_active()` -> `paths.engine_dir()` ->
`engine.resolve_binary()` returns the build that answers. `/api/health` and every checker record quote that path.

**Rules that must not regress** (each cost a real outage; tests in `tests/test_backends.py`, 28 cases):

1. **A remembered `bad` expires** — `VERDICT_RETRY_AFTER_S` (6 h); `allow_retest=True` forces a retest now.
2. **A busy card is never tested** — `card_busy()` refuses beside *any* `llama-server` or under
   `SELFTEST_MIN_FREE_MIB` of free VRAM, and a **skip remembers nothing**.
3. **A fault is not a verdict** — an access violation (`0xC0000005` / `3221225477`) writes **no** verdict
   (`backend_faulted_not_probed`). Only a clean exit carrying the loader's own words condemns a build.
4. **A proven selection is never withdrawn** because a test failed elsewhere: `clear_active()` runs only when
   nothing on this host is proven. A missing `data/perf_active.json` = the console silently on the CPU engine.
5. **Never key the `ensure()` memo on a per-call value.** It was `host|enabled|threads`, so a varying `-t`
   re-ran a **real self-test per model** in a sweep. It is `host|enabled`.
6. **One owner per fact** — `perf.gpu_free_mib()`/`gpu_vram_mib()` read the **driver**; `model_fit` judges
   whether there is *room*, `backends` judges whether *our build* can use it. Never merge the two questions.
7. **A rate needs a sample** — `rate_from()` requires **>= 16 tokens**; `gpu_layers_used` is `None` when the
   build prints no offload line (never `0`).

Receipts / CLI: `python src/backends.py status | list | test <name> | drop <name> | apply <name>`.
Self-test port **11471** (`backends.SELFTEST_PORT`); the checker sweep uses its own **11481**; never the
console's 11441. Self-test log: `save/logs/selftest-cuda.log`.

**Measured worth of the GPU** (one variable, `gemma4-12b` 6.87 GiB, identical flags): `-ngl 99` boot 90.7 s /
200 tok in 9.26 s = **21.6 tok/s** vs `-ngl 0` boot 3.7 s / 28.29 s = **7.1 tok/s** -> **3.0x**, at ~87 s extra
on the first load (pays back in ~10 turns). A live 128-token turn measured **135.8 tok/s**; `/api/health`
answered in 11.3 s. Flash-attn `on` was adopted on measurement (8.7 s/112.6 tok/s off vs 6.5 s/**123.3** on);
big-batch `-b/-ub` and `--spec-default` were **rejected** — the ninja rule is *"any NINJA boosting without
loosing function or stability"*, so nothing lands unmeasured.

Reason strings the console can report (`ensure()` result), each a different repair:

| reason | meaning | first move |
|---|---|---|
| `backend_proven_on_this_host` | a remembered `ok` verdict was reused | none — healthy |
| `self_test_passed` | proved in this call | none — healthy |
| `gpu_busy_not_probed` | skipped: the card was in use | run it when the box is idle |
| `backend_faulted_not_probed` | launch faulted (card taken mid-launch) | retry on an idle card |
| `backend_failed_on_this_host` | a fresh `bad` verdict stands | `backends.py test <name>` if you disagree |
| `backend_sees_no_device` | the build found no device | driver/VRAM (`RECOVERY.md` B) |
| `backend_activation_failed`, `backend_crashed_on_this_host`, `backend_self_test_incomplete` | apply or load failed | read `save/logs/selftest-<name>.log` |
| `engine_cpu_only`, `gpu_disabled_by_config` | no backend installed / `gpu` off in config | expected on a CPU-only box |

## 5. Which file owns which fact (and the field-ownership trap)

| fact | owner | note |
|---|---|---|
| what ran, capabilities, boot time, GPU evidence | `save/model_check.json` | per record: `verdict`, `why`, `fit`, **`gpu_backend`**, `gpu_device`, `gpu_layers_used`, `boot_s`, `probe` |
| what the operator sees in the picker | `save/registry.json` -> `/api/models` | per record: **`checked`** (`gen_tps`, `prefill_tps`, `boot_s`, `why`), `fit`, `caps`, `status`, `also_known_as` |
| which backend is proven and selected | `data/perf.json` (verdicts, keyed by the backend's own files, under `perf.host_id()`) + `data/perf_active.json` | deleting/clearing the active file silently drops the console to the CPU engine |
| operator config | `config/console.json` | measured now: `flash_attn "on"`, `max_tokens 4096`, `kv_type "q8_0"`, `ngl "auto"`, `threads "auto"`, `media_root "D:/LYGO_MEDIA"`, `scan_roots ["./models"]` |
| module set | `src/modules/catalog.json` (order = load = pane order) | 7 modules: health 10, world 20, llminfo 30, envwatch 40, **meminfo 50**, **guardwatch 55**, notepad 60 |
| engine logs | `save/logs/llama-server-<port>.log` (**UTF-8**), `save/logs/selftest-<name>.log` | `model_check._decode()` scores encodings — a wrong decode raises nothing and a "why" becomes mojibake |
| models on disk | `I:\LYGO_MODELS` (PC vault) · `D:\LYGO_MODEL_VAULT\cas` (73 hard-linked blobs + 18 manifests, 203.6 GB represented, 0 MB extra) · the stick's own CAS | `LYGO_MODELS` is **not** an env var on this box — do not key any rule on it |

**Trap:** a check for a top-level `gen_tps` (or a `probe` sub-dict) in `/api/models` reads as "the choice box
has no speed labels" while the labels are right there in `checked`. The same class as looking for `gpu_ok` on
`backends.report()`, which never had that key.

## 6. The lineup measured on the CUDA build (sweep of 2026-09-20 22:47, port 11481)

**14 of 18 records carry `gpu_backend: cuda`; 14 carry a rate.** Rates in tok/s, with the boot time:

| model | tok/s | boot s | | model | tok/s | boot s |
|---|---|---|---|---|---|---|
| `llama3.2:1b` | **166.9** | 3.7 | | `gemma-4-12B-it-qat-UD-Q4_K_XL` | 29.2 | 18.8 |
| `qwen2.5:3b` | **109.3** | 6.7 | | `gemma4-12b` | 17.0 | 94.4 |
| `qwen2.5:1.5b` | 92.7 | 12.7 | | `lygo-turbo-coder:latest` | 8.6 | 46.5 |
| `qwen2.5-coder:7b` | 55.4 | 58.0 | | `lygo-turbo-agent:latest` | 6.9 | 78.1 |
| `llama3.1:8b` | 52.5 | 12.7 | | `deepseek-r1:14b` | 4.1 | 25.2 |
| `gemma2:9b` | 40.4 | 15.8 | | `qwen2.5-coder:14b` | 3.9 | 27.8 |
| `phi4:14b` | 3.7 | 27.5 | | `nomic-embed-text` | embed (no generation rate) | 6.8 |

- Not a model: `Gemma-4-12B-It` -> `not_a_model` (it is a projector; correct not to boot it).
- Failed soft: `qwen3.6:latest` (loader limit) and `nemotron-3-super:latest` (86 GB) — see defects L3/#23.
- `gpu_layers_used` is `null` on every record: this build prints no offload line at default verbosity.
  `gpu_backend: cuda` is the engine's own evidence, not an inference.
- One weights file = one record; other names live in `also_known_as`. Read from `save/registry.json`:
  `lygo-turbo-agent:latest` (19.71 GB) = `Qwen3.6-35b-a3b-Uncensored:35b` + `lygo-turbo-hermes:latest` +
  `lygo-turbo-uncensored:latest`; `lygo-turbo-coder:latest` (17.28 GB) = `qwen3-coder:30b`;
  `gemma4-12b` (6.87 GB) = `gemma4:12b` — **one file, two records, which is defect #24**;
  `qwen2.5-coder:7b` = "Qwen2.5 Coder 7B Instruct"; `nomic-embed-text:latest` = `nomic-embed-text-v1.5`.
- Media engines (wired, proven): `sd-cli.exe -m MODEL -p PROMPT -n NEG -o OUT -W -H --steps --cfg-scale -b`
  and `piper.exe -m VOICE.onnx -c VOICE.json -f OUT.wav`; weights outside the git tree in `D:\LYGO_MEDIA`
  (`qwen_image_2.1-Q4_K.gguf`, `qwen_image_2.1_vae_bf16.safetensors`, `Qwen3VL-8B-Instruct-Q4_K_M.gguf`).
  **Measured rules in `media_tools`** (not an assumption — read them): a distilled checkpoint is detected by
  name (`_is_turbo`: turbo/schnell/lightning/lcm/dmd/hyper) and gets distilled settings (**4 steps at cfg 1.0**)
  instead of 20 at 7.0, because 20 steps on a turbo model is the wrong shape; and a **declared heavyweight
  model must never take the default path** — `tests/test_media_limbs.py` asserts exactly that, so a model
  "wired for a much larger machine" cannot silently become the default.

## 7. Open defects — reproduction, cause, fix, proof

**L10 — a record that lives on the removable stick.** The PC registry carries one record whose file is
`E:\LYGO_BUILDER_KEY\…` on `ESD-USB`. With the stick out, fail-soft covers the boot and the llminfo pane says
it cannot see it, but **the choice box does not say why**. Fix: mark such records in `/api/models`
(`not plugged in` / `missing`) rather than leaving them looking bootable. Prove: unplug `E:`, read `/api/models`
and the picker, then plug it back and re-read.

**L2 — the checker's routes are kernel-side.** `/api/models/check` and `/api/models/route` live in
`server.py`; under Law 6 the module should own them. **The steward's call, not yours** — raise it, don't act.

**L3 — two models the engine build cannot load.** `qwen3.6:latest`: `key qwen35moe.rope.dimension_sections has
wrong array length; expected 4, got 3`. `nemotron-3-super:latest`: 86 GB against ~24 GB usable. Both fail soft
in seconds with the engine's own words. Fix: a newer engine build (a fetch — needs the steward) or another quant.

**#23 — a failure class that flips between runs.** `model_check.classify_failure()` decides `engine` vs `rig`
by sniffing the engine's **log tail**, so `nemotron-3-super` reads `engine` in one sweep and `rig` in another.
Fix: let the fit plan decide first — a `model_fit` verdict of `too_big` is a rig limit whatever the tail says.
Prove: run the sweep twice and assert the class is identical.

**#24 — the checker enumerated both names of one weights file.** `gemma4:12b` kept a stale CPU-pass rate (6.8,
no `gpu_backend`) while `gemma4-12b` was measured at 17.0. Fix: drive the sweep from the deduped record set
(`registry.dedupe_by_file`). Prove: sweep, then assert no record carries a rate from a different backend.

**L8 — the cold first turn is still ~190 s** at 7.6 k context (an honest 54 tok/s prefill), plus the GPU's
+87 s first load. `--cache-prompt` is on. The gemma4 latency regression (a clock inside the system block
forcing a full re-prefill) **is fixed** — moving it to the tail fragment took turn 2 from 146.1 s to 2.5 s.
A warm-keep strategy is **unmeasured**: measure before claiming any improvement.

**L5 — no local sound model exists** in any store. The label schema covers sound (`sound-in` via a cloud
brain, `sound-out` via piper), so the wiring is ahead of the weights: a small local STT model is the gap.

**L6 — cloud-brain image parts were never proven against a provider.** `image_url` landed in `cloud_api.py`
but no live turn has exercised it. Prove it, or declare it `DEGRADED(reason)` under Law 1.

**Also open, from the failures this pass *prevented* rather than found:** the fail-soft route has not been
proven **live** end to end (a turn routed to the API brain *with an image*, and the "pick a different route"
UI path) — it is built and unit-tested only. And the vault's wide HTTP `/api/scan` walk has never been
exercised through a **running** console.

## 8. The enhancement queue (the steward's own priorities)

1. **"Ninja boosting" without losing function or stability** — adopt only measured wins (rule above). The next
   honest candidates: a warm-keep strategy for the first load (L8) and `-ngl` per-model tuning, both measured
   before/after on the same prompts.
2. **Labels and characters** — *"make clear labeling on what they can do as far as image, sound, text, coder"*
   is partly delivered (`caps` per record, `checked.why`, the media limbs). Next: make a capability the
   operator can *see* fail (a model with no projector, a store with no sound model) name itself in the pane.
3. **"I should see every single LLM on this pc or drives in the LLM choice box"** — delivered (19 records /
   26 names, vault CAS adopted as linked mirrors). Next: the L10 marker and a `rescan` that cannot lose aliases.
4. **Media generation** — proven; owes the ship-policy paperwork (section 11). Ship the **wiring** plus a vendor
   pointer, never the weights.
5. **Archive / vault** — the large one. `D:\LYGO_CANON` (read-only, ~10 sealed snapshots) is reference only.
6. **Module programme** — M1 shipped; the shell data-driven pass (M2, WO-0002) is where the next module work
   lands. A new module must need **zero** edits to `server.py` or `portal/index.html`; that empty diff is the
   acceptance test.
7. **The standalone vocabulary and the character tuning** (per-message 48,000 chars; per-conversation 600,000;
   a blob guard at one unbroken run over 4,000) — in place; keep the reply-length rule honest rather than
   hiding limits.
8. **Ollama as an external service only** — the three consoles must not depend on it (`src/ollama_import.py` was
   replaced by `src/cas_import.py` on this tree; the stick still ships the old file — section 10).

## 9. Module 03: where it actually stands

**The PC half is built, green and certified** — this is easy to misjudge from the work-order list, so check
before redoing it:

- `src/modules/lygo.meminfo/` and `src/modules/lygo.guardwatch/` exist, each with `module.json` + `backend.py`.
- `src/modules/catalog.json` carries them at **order 50** and **55**; the console reports **7 modules**.
- `tests/test_module_meminfo.py` and `tests/test_module_guardwatch.py` exist and pass inside the 915.

What is **not** done is the close-out around them (the preserved list, s1-s12):

1. **s1** WO-0004 (`lygo.meminfo`) + WO-0005 (`lygo.guardwatch`) in `05_WORK_ORDERS` — `in_progress`.
2. **s2** register both: `01_DESIGN/MODULE_REGISTER_v1.md` + `module_register.json`.
3. **s3** specs: `04_MODULES/<id>/MODULE_SPEC.md` for both.
4. **s4**/**s6** build both (already true on the PC tree — verify against the spec, then tick).
5. **s5** prove meminfo's scaffold + backend in-process; **s7** the two test files (already present — tick with
   evidence); **s8** live proof on port **9744** (`/api/health`, `/api/modules`, both routes, a traceback grep,
   a clean shutdown).
6. **s9** release PC (bump `VERSION`; note the console already reports **1.3.0** — decide whether this is 1.3.1);
   **s10** promote both modules to USB per-file sha256; **s11** PARITY_MATRIX + BUILD_LOG rows; **s12** seal
   `PC_LOCAL` + `USB_CLAW` and hand the steward the publish list.

Paths are the LYGO stack convention: the stack root resolves via `paths.stack_root_status()` ->
`I:\E Drive\lygo-protocol-stack`, verified by `LYGO_STACK_ROOT_POINTER.md`.

## 10. The promotion debt (exact, LF-normalised, measured)

The stick's `src/` is 51 `.py` files against the live tree's 57. **27 files need promoting** — 7 that exist only
on the live tree and 20 whose contents differ (comparing LF-normalised bytes, so line endings are not the
reason; `diff -rq --strip-trailing-cr` says the same). One file exists **only on the stick**:
`ollama_import.py`, which this tree replaced with `cas_import.py`.

```
  cas_import.py, media_tools.py,
  model_check.py, model_fit.py,
  model_route.py, modules/lygo.guardwatch/backend.py,
  modules/lygo.meminfo/backend.py, backends.py,
  cloud_api.py, compaction.py,
  continuity.py, engine.py,
  image_tools.py, install.py,
  limbs.py, lygo_engine.py,
  modules/host.py, modules/lygo.envwatch/backend.py,
  modules/lygo.llminfo/backend.py, p0_hook.py,
  paths.py, perf.py,
  public_gateway.py, registry.py,
  scanner.py, server.py,
  tools.py

only on the stick: ollama_import.py  (decide: retire it with the CAS import, or keep a shim)
```

Promotion is **per-file, hash-verified**, never a recursive kit overwrite (Law 2), and a fix found on the stick
comes back to the PC tree first. **Law 1 rows are owed for this pass** — either all three editions declare the
change, or a written `DEGRADED(reason)` / `N/A(reason)` goes into `01_DESIGN/PARITY_MATRIX_v1.md`. The
temptation to promote before the debugging round finishes is real; **the steward said no pushes this round**.

## 11. Bookkeeping owed

- **Law 1 rows** for: the GPU/backends rules, the checker + balancer, `cas_import`/vault adoption, media limbs,
  model_fit/model_route, the reply-length change, the module strip.
- **Media ship policy**: the `DEGRADED`/`N/A` rows for image/sound per edition (weights are never shipped).
- **Seals**: PC_LOCAL + USB_CLAW for the next release (`scripts/seal_build.py` — **it refuses a duplicate name
  and still exits 0**: read the `SEALED <path>` line, never the exit code).
- **Stale kit docs**: `WHITEPAPER.md`, `STANDALONE.md`, `COMPACTION.md`, `MODELS.md`, `README.md`,
  `BUILD_NOTES.md`, `LYGO_ENGINE.md`, `prompts/IDENTITY.md`, `prompts/MAP.md`, `scripts/verify_install.py`,
  `PUBLIC_GATEWAY.bat`, `tools/pack_to_drive.py`, `BUILD_MANIFEST.json`, the stick's `config/local.json`.
- **`D:\LYGO_CONSOLE`** (legacy 1.1, 15-model registry): retire or re-point.
- **CLAW agent stick** (`LYGO_USB_BOOT.bat`, UI 9631, `OLLAMA_HOST=127.0.0.1:11434`, `qwen2.5:3b`) and
  **`lyra-core/`** are still Ollama-based subsystems. Ollama may live on as its own service; the consoles must
  not depend on it.
- **Credentials**: pointers only, `[REDACTED]` in every artefact. Guardwatch must never open a credential file.

## 12. Agent working notes for this box (traps that cost real time)

- **The terminal tool runs bash (git-bash), not PowerShell.** Native tools need native forward-slash paths
  (`git -C "I:/E Drive/..."`), and `diff`/`find` are MSYS tools — call them through a shell, not `subprocess`
  without one.
- **Never `rglob` a whole drive.** `I:` is 3.7 TB; a full-tree scan hung a cell for 300 s. Use `search_files`,
  or a bounded walk on a known root (`paths.stack_root_status()` gives the stack root).
- **`powershell Get-CimInstance` is minutes-slow here** — another 300 s cell lost. Prefer `tasklist`,
  `netstat -ano`, `nvidia-smi`.
- **`wmic` is gone** on this Windows 11.
- **Quote Windows paths containing spaces** (`"/i/E Drive/..."`), and keep terminal calls clean — a stray quote
  from a previous line leaks into the next call.
- **A background `sleep`/poll loop is the wrong tool for waiting**: use the process tool's `await`-style wait or
  a foreground command with a generous timeout.
- **Kill what you start.** A console started for a proof must be stopped by PID/port (`netstat -ano` ->
  `taskkill /F /PID`); `/api/shutdown` can time out while the engine is loading. Never leave a console holding
  9641/11441, and never touch the steward's 9651.
- **Test isolation matters more than it looks**: the suite is host-state sensitive — six store tests once went
  red *because a real sweep held the card*. The fixture now stubs `card_busy`; keep that pattern.
- **Editing rules that cost restores**: apply line-based edits in descending anchor order; validate every anchor
  before writing any file; `py_compile` after every patch (a syntax error shows as test *collection* failures);
  read/write `.bat` files as bytes with `newline=""` (they are CRLF).

## 13. Verification harnesses

| harness | what it proves |
|---|---|
| `%TEMP%\gpu_sweep_all.py` | boots every registered model on the current backend, writes `save/model_check.json` (~12-20 min; own port 11481) |
| `%TEMP%\gpu_ab_gemma.py` | one-variable A/B for `-ngl` (`21.6` vs `7.1` tok/s) |
| `%TEMP%\backend_vk_probe.py` | the Vulkan overlay through the kit's own CLI |
| `%TEMP%\console_live_proof.py` | a real console boot: `/api/health` -> `engine_dir` -> a gated turn -> shutdown |
| `%TEMP%\fa_prefill_probe.py`, `%TEMP%\cache_block_probe.py` | flash-attn and the clock-in-system-block A/Bs |
| `scripts/certify_build.py` | manifest + licence verdict (must say CERTIFIED) |
| `scripts/verify_install.py` | the install acceptance gate (PASS/FAIL/NOTE, exit 0 only when nothing failed) |
| `tests/test_backends.py` (28) | every backend-store rule above |

Full recovery procedures (a CPU fallback, contended verdicts, strays, overlays, log decoding) live in
**`docs/RECOVERY.md`** — sections A-J (health check · CPU fallback · a condemned backend · contended
verdicts · strays · overlays · logs · stick-out models · verifying a build · the evidence map · re-running the
checker), each with the exact command and the output to expect.

## 14. What NOT to do

- **Do not push, seal, or publish anything** — the steward publishes, and this round is still debugging.
- **Do not stop the steward's consoles** (the stick on 9651 is his running session).
- **Do not test a backend while any `llama-server` is up** — that is what wrote off a working GPU twice.
- **Do not `git add -A`** in the stack repo (it carries unrelated working trees), and never force-push.
- **Do not add a kernel change for a module** — stop and say so (Law 6).
- **Do not ship weights** — only wiring plus a vendor pointer.
- **Do not copy `config/api.json`, `data/.llama_api_key`, `data/.lygo_llm_token` anywhere**, and never print a
  credential value.
- **Do not trust a green suite for the UI** — the portal needs its own browser check (a `let` read above its
  declaration once killed every pane with 592 tests green).
- **Do not quote a number from this document** where a command is given — re-derive it.

## 15. A suggested first session

1. Section 0: suite, certify, `backends.py status` (10 minutes; if the GPU is not active, `RECOVERY.md` B).
2. Read the open rows of `docs/DEFECT_LEDGER.md` and pick **#23** or **#24** — both are small, both have a
   reproduction and a proof, and both make the checker's output honest.
3. Then **L10** (the picker's missing "not plugged in" marker) — it is the operator's own complaint, and the
   choice box is where he sees it.
4. Ask the steward the two questions only he can answer: **L2** (may the checker's routes move to the module?)
   and **L3** (fetch a newer engine build for `qwen3.6`?). Neither is a code problem.
5. Only when the debugging round is declared finished: the 27-file promotion, the Law 1 rows, a version bump,
   one seal, and the publish list for him — never a push from the agent.
