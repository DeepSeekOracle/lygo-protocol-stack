# LYGO LLM Console — the wiring map

Written 2026-09-20 from the code and from live readings on this box, not from memory. Every arrow below
is a call that exists today; every port and file path was re-derived. When the code and this map
disagree, the code is right and this page is the defect.

## 1. The spine — one question per layer, and nobody answers twice

The kit's shape is a chain of **questions**, each with exactly one owner. Most of the wiring bugs found
this pass were one layer answering another layer's question (a plan read as proof; our CPU-only binary
asked whether the host has a GPU).

```
  THE RIG                    THE PLAN                    THE IDENTITY
  ┌───────────────┐          ┌───────────────┐           ┌────────────────────┐
  │ nvidia-smi    │  (total, │ model_fit     │  verdict  │ scanner            │
  │ perf.*        │──free)──▶│ .verdict()    │──(+ngl)──▶│  .find_stores()    │
  │ backends.*    │          │  gpu_full /   │           │  ._store_records() │
  └───────────────┘          │  gpu_partial /│           └─────────┬──────────┘
   "what does the            │  cpu_ok /     │                     │ records
    hardware have?"          │  too_big      │                     ▼
         │                   └───────────────┘           ┌────────────────────┐
         │ can OUR engine    "would it fit, and          │ registry           │
         │ use it?            where?"                    │  .upsert()         │
         ▼                                                 │  ._file_identity() │
  ┌───────────────┐                                        │  .dedupe_by_file() │
  │ backends      │  proven / not proven                   └─────────┬──────────┘
  │  .report()    │──────────────┐                                  │ one record per file
  │  overlay|engine│             │                                  ▼
  └───────────────┘             │                        ┌────────────────────┐
   "has a real load proved      │                        │ model_check        │
    it on THIS host?"           │                        │  .check_one()      │
                                │                        │  boots through     │
                                │                        │  lygo_engine.boot  │
                                │                        │  on its OWN port   │
                                │                        └─────────┬──────────┘
                                │                                  │ measured facts
                                │                                  ▼
                                │                        ┌────────────────────┐
                                │                        │ save/model_check   │
                                └───────────────────────▶│  .json             │
                                   the amber is TRUE     └─────────┬──────────┘
                                   while it says no                │
                                                                   ▼
                                                         ┌────────────────────┐
                                                         │ model_route        │
                                                         │  .route()          │
                                                         │  .gpu_proven()     │
                                                         └─────────┬──────────┘
                                                                   │ the brain takes the turn
                                                                   ▼
                                                         ┌────────────────────┐
                                                         │ server.py ─ portal │
                                                         │  /api/chat etc.    │
                                                         └─────────┬──────────┘
                                                                   │ findings
                                                                   ▼
                                                         ┌────────────────────┐
                                                         │ modules/           │
                                                         │  lygo.llminfo      │
                                                         │  lygo.envwatch     │
                                                         └────────────────────┘
```

**The two questions that must never be merged**

| question | owner | reads | never |
|---|---|---|---|
| Does the card have room for this model? | `model_fit.verdict()` | `rig_vram_mib()` (the driver) | never guesses from our engine's opinion |
| Can OUR engine build use the GPU here? | `backends` | a **real model load**, proved per host | never inherits a fit verdict as evidence |

Measured 2026-09-20: merging them filed ten models `no_gpu_device` on a box with an idle RTX 4060 Ti
(the reading came from the CPU-only base binary), and a fit verdict was about to be accepted as proof the
GPU had carried a turn (it had not).

## 2. The engine — who launches what

```
  config/console.json ──┐
  registry record ──────┼──▶ lygo_engine.plan()  ──▶ pl = {"llama": {...}, "ngl": …, "profile": …}
                        │        │                     │
  backends.report() ────┘        │                     └─ offload lives at pl["llama"]["ngl"]
                                 ▼
                        lygo_engine.boot(rec, api_key=…, state=…, port=…)
                                 │
                                 ├── colibri  ─▶ state["engine"]="lygo-colibri"
                                 └── llama    ─▶ engine.Runner ─▶ llama-server.exe
                                                    │  log: save/logs/llama-server-<PORT>.log
                                                    ▼  (the log is named BY PORT — a tool that
                                                        boots on the console's port writes into
                                                        the console's log; that is how "engine
                                                        fault x119" appeared on a healthy box)
```

Base engine `engine/llama-server.exe` is **CPU-only on purpose** (the stick must boot on any PC):
`--list-devices` → `(none)`. GPU builds live in `engine/backends/<name>/` in two shapes:
**`engine`** (a complete launch directory — `cuda`, tag `b10988`: `llama-server.exe` + `llama.dll` +
`ggml-cuda.dll` + the CUDA 13 runtime + a sha256 manifest) or **`overlay`** (a `ggml-<name>*.dll` copied
into `engine/` beside the base binary — `vulkan`). Activating an `engine` backend is a pointer swap;
activating an overlay copies one file. Either way the build is only ever *used* after a real load.

```
  engine/backends/<name>/backends.json  (or backend.json)   info: kind, tag, present, sha256 mask
  data/perf_active.json ──────────────────────────────────▶ active: {backend, engine_dir, at}
        ▲                                                        │
        │ set_active(name, ed, reason=…)                          │ read by paths.engine_dir()
        │                                                        ▼
  ensure(models, threads, host, allow_retest, refresh)      engine.resolve_binary()
        │                                                        = <active dir>/llama-server.exe
        │ 1 remembered ok  ─▶ activate + set_active (no test)
        │ 2 remembered bad ─▶ stands down UNLESS retested or older than VERDICT_RETRY_AFTER_S (6 h)
        │ 3 unproven       ─▶ card_busy()? then gpu_busy_not_probed, NOTHING is remembered
        │                     else activate → device list → self_test (a real model load) → remember
        ▼
  data/perf.json · host records · verdict[name] = {verdict, key, detail, device, seconds, at}
```

**A verdict is evidence about a moment, not a life sentence.** `key` is the backend's own file
fingerprint, so a re-installed build re-tests itself; `at` plus `VERDICT_RETRY_AFTER_S` means a bad
verdict ages out; and a card that is *busy* is never tested at all. Measured 2026-09-20: both GPU
backends were condemned by self-tests taken at 21:08–21:09 while our own sweep held the card, which is
why the console sat on the CPU build while a working CUDA build was installed.

**State on this box (2026-09-20, after this pass):** `report()` → `active: "cuda"`,
`engine_dir: …\engine\backends\cuda`, `installed: ['cuda','vulkan']`, overlays `['vulkan']`; verdicts
`ok` for both (`cuda` 10.7 s, `vulkan` 10.6 s, device `NVIDIA GeForce RTX 4060 Ti`). Measured worth,
one variable at a time on `gemma4-12b.gguf` (6.87 GiB): `-ngl 99` **21.6 tok/s** vs `-ngl 0`
**7.1 tok/s** → **3.0×**, at the cost of an 87 s longer first load.

**Ports, re-derived, one owner each**

| port | who | note |
|---|---|---|
| 9641 | console (PC) | 9651 on the stick |
| 11441 | console's engine | 11451 on the stick |
| 11471 | `backends.SELFTEST_PORT` | the GPU proof load — reserved |
| 11481 | `model_check.CHECK_PORT` | a tool must never share the console's port |
| 9744 | live proof harness | |
| 9631 | CLAW agent stick | still Ollama-based, separate |

## 3. Data — one writer per file

| file | written by | holds |
|---|---|---|
| `save/registry.json` | `registry.upsert()` | one record per weights file; `selected` + `selected_source` (the pin) |
| `save/model_check.json` | `model_check` | per model: verdict, fit, probe, boot_s, the engine's own reason on failure |
| `data/perf.json` | `perf` | host records keyed by an *installed-RAM* fingerprint |
| `data/perf_active.json` | `backends` | which backend build is active, and the remembered verdict |
| `config/console.json` | the steward | the only place a pin or a default may be set |
| `save/logs/` | engines, one file per port | archived to `save/logs/archive/` (never scanned) |

### Adding a backend — the gate any new engine add-on walks through

1. Put the build in `engine/backends/<name>/`: either a **complete launch directory** (`kind: "engine"` —
   `llama-server.exe` + `llama.dll` + `ggml-<name>.dll` + its runtime DLLs) or a **`ggml-<name>*.dll`
   overlay** for the shipped CPU engine (`kind: "overlay"`), with a `backend.json` carrying per-file sha256.
2. `python src/backends.py test <name>` — the store applies it, asks *that build* for its device list, then
   loads a real model. That load is the **only** thing that sets `ok`; nothing else counts as proof.
3. **Nothing unproven lands in the proven launch directory.** Activating an `engine` backend is a pointer
   written to `data/perf_active.json`; an overlay is copied into `engine/` and `deactivate()` removes
   exactly its files. `engine/` is git-ignored (`*`) so a 780 MB backend can never reach the repo.
4. `config/console.json` → `"gpu": "auto" | "off"` is the operator's own switch: `off` means CPU, always
   (`ensure(enabled=…)`), and it is the only place that setting belongs.

## 4. Invariants the wiring must keep

1. **A plan is not a proof.** `fit.mode` says a model *would* fit; only `devices_seen` /
   `gpu_layers_used` from a launch say the GPU *carried* it. `model_route.gpu_proven()` requires the latter.
2. **One weights file = one record.** Identity is the content hash — a CAS blob carries it in its
   filename (`sha256-<64 hex>`), a store copy in `sha256`; other names become `also_known_as`.
3. **A tool gets its own port.** Tools boot beside the console, never into its log.
4. **No hash-shaped run ever reaches a panel.** Redacted at the edge (`envwatch._safe_row`), so the rule
   holds whatever module or stored record the text came from.
5. **A failure names its class**: `engine` (our loader is older than the file — a newer build or another
   quant is the fix) vs `rig` (the box). Never blame the operator's machine for our build, and never
   blame our build for the machine.
6. **Reasons come from the engine's own words.** `own_words()` lifts the loader's sentence out of the
   log; our `RuntimeError: exited 1` is kept as `raised`, never as the reason.
7. **The clock sits after the history** in the prompt, or every turn re-prefills from scratch.
8. **Modules do not grow the kernel.** A module needing a `server.py` change stops and says so (see the
   open decision L2: the checker's routes are still kernel-side).
9. **Never test a busy card, and never remember a verdict from one.** A self-test taken while another
   engine holds the GPU measures the moment; recording it condemns a working build. `card_busy()` gates
   the test, and a skip remembers nothing.
10. **An unstated value is not a zero.** A missing offload line is `gpu_layers_used: None`, not `0`; a
    device list that fails to read is "unknown", not "no GPU". Every false figure this pass came from a
    zero standing in for an absent reading (`no_gpu_device`, `gpu_layers_used: 0`).
11. **A rate needs a sample.** No tok/s label under 16 generated tokens — record the count and say
    "too few tokens to rate". A two-token answer rated 16.6 tok/s for a model that does 135.8.
12. **Read the log the way it was written.** `_decode()` scores `utf-8`/`utf-16`/`utf-16-be`: decoding the
    wrong way returns mojibake *without raising*, which silently became a recorded reason.

## 5. Open structural gaps (mirrors `DEFECT_LEDGER.md`)

- **L10** the PC registry carries one record whose file lives on the **removable stick** (`E:` — `ESD-USB`,
  28.8 GB): with the stick out that model dangles. Fail-soft covers the boot; the picker does not yet say
  "not plugged in".
- **L2** the checker's routes live in `server.py` (kernel-side) — steward's call under Law 6.
- **L3** `qwen3.6` / `nemotron-3-super` need a newer engine build (loader limits, not the box).
- **L5** no local sound model exists; the label schema covers it.
- **L6** cloud-brain image parts unproven against a provider.
- **L8** cold first turn ~190 s at 7.6 k context (honest 54 tok/s prefill); on the GPU path the first load
  adds ~87 s to put 6.87 GiB into VRAM, then every turn is 3.0× faster. Worth measuring a warm-keep
  strategy before claiming a fix.

**Closed this pass: L1** (a verdict never expired → retry window + busy-card rule; both GPU backends are
now proven and `cuda` is active) and **L9** (`perf.gpu_free_mib()` asked the CPU-only base binary → it now
reads the driver, one owner for both callers). The GPU is no longer a gap: the console runs on the card.
