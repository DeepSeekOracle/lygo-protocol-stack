# Recovery — bring the console back to a known-good state

Every command below runs from the kit root. On this box that is:

```bash
cd "/i/E Drive/lygo-protocol-stack/lygo_llm_console"
```

Python on this machine is `C:/Python313/python.exe`. (Paths in this file use MSYS form for `bash`;
native tools want `C:/…`-style forward slashes.)

---

## A. Sixty-second health check

```bash
C:/Python313/python.exe src/backends.py status
```

Expect, on this box, right now:

```json
"report": { "active": "cuda",
            "engine_dir": "…\\engine\\backends\\cuda",
            "installed": ["cuda", "vulkan"],
            "applied_overlays": ["vulkan"] }
```

and in `data/perf.json`, under this host's record, `verdict.cuda = ok` and `verdict.vulkan = ok`.
If `active` is `cpu`, go to §B. If a verdict reads `bad`, read the `detail` first — it is the engine's own
sentence — then §C.

```bash
C:/Python313/python.exe -m pytest -q          # expect: all green, 27 subtests (927 tests on 2026-09-20 - re-derive the count, never quote it)
C:/Python313/python.exe scripts/certify_build.py   # expect: VERDICT: CERTIFIED BUILD
```

## B. The console is on the CPU engine (or a GPU build is unproven)

```bash
C:/Python313/python.exe src/backends.py list           # what is installed: kind, tag, present, sha256 mask
C:/Python313/python.exe src/backends.py test cuda      # apply → device list → real model load
```

`test` proves it and records the verdict; `active` follows the first proven candidate in preference order.
For a rig with no NVIDIA card, `test vulkan` (the overlay) is the equivalent path.

**Check the card is idle before a test** — a `llama-server` already holding it is exactly how both GPU
verdicts got written off on 2026-09-20. The store now refuses to test a busy card (`gpu_busy_not_probed`)
and remembers nothing, but a manual test deserves the same care:

```bash
tasklist /FI "IMAGENAME eq llama-server.exe" /NH                                  # any strays?
nvidia-smi --query-gpu=name,memory.free --format=csv,noheader                     # free VRAM
```

### B2. If both verdicts read `bad` with `3221225477` / `0xC0000005`

That is **contention, not the build**: the self-test launched while another engine was still releasing the
card. Re-prove on an idle card — confirm `tasklist /FI "IMAGENAME eq llama-server.exe"` is empty first:

```bash
C:/Python313/python.exe src/backends.py test cuda     # expect: ok true, model_load_ok, ~11-15 s
```

That writes a fresh `ok` verdict and re-selects the backend. A build that is genuinely unusable fails
**differently**: a clean exit with the loader's own words (a key shape, a tensor shape). Since the fault rule
landed, a faulted launch no longer writes a verdict at all, so a stale `bad` of this shape can only predate it.

## C. A backend is condemned and you believe it should not be

Order of the checks, cheapest first:

1. **Is the verdict about *this* build?** A verdict is keyed by the backend's own file fingerprint, so a
   re-installed build re-tests itself. `src/backends.py list` shows the tag.
2. **Is it older than the retry window?** `VERDICT_RETRY_AFTER_S = 6 h` — past it, a `bad` verdict no longer
   blocks a retest automatically.
3. **Force it:** `C:/Python313/python.exe src/backends.py test <name>` (the CLI retests regardless).
   In code the same flag is `backends.ensure(..., allow_retest=True)`.
4. **Drop the record entirely** if the evidence that produced it is stale — the CLI's `drop` action
   removes a backend's remembered verdict without touching the files on disk.

**Never** "fix" a bad verdict by editing `data/perf.json` by hand: the verdict must be overwritten by a
load, or it will be silently believed again.

## D. A stray engine is holding the card

```bash
tasklist /FI "IMAGENAME eq llama-server.exe" /FO CSV /NH     # note the PID in the second column
taskkill /F /PID <pid>
```

**Never `taskkill /F /IM python.exe`** — that kills the console, the kernel and possibly your own session.
Ports are the fastest way to find the right process if a tool lied about stopping one: a stopped engine
frees its port immediately, so a port that still answers means the process is still up.

Port map (re-derive before quoting): **9641** console PC (9651 stick) · **11441** console's engine (11451
stick) · **11471** `backends.SELFTEST_PORT` · **11481** `model_check.CHECK_PORT` · **9744** live-proof
harness · **9631** CLAW agent stick.

## E. An overlay is applied and should not be

```bash
C:/Python313/python.exe -c "import sys;sys.path.insert(0,'src');import backends;print(backends.applied_overlays())"
```

An overlay (`ggml-vulkan.dll` in `engine/`) is copied in by `activate()`; `deactivate(name, info)` removes
exactly the files it owns. A leftover `ggml-*.dll` outliving its backend is the state that crashed the
engine on a bad driver (2026-09-18) — so if a backend stops being proven, deactivate it *before* suspecting
anything else. Note the current, deliberate state: `vulkan` is proven here and left applied, which makes the
shipped CPU engine GPU-capable as a fallback.

If `status` instead shows `applied_overlays []` while `cuda` and/or `vulkan` read `bad` with a
`launch_failed: ... exited 1` detail, that is the **contention signature** of 2026-09-20, not a broken
build: something tested (or booted) while the card was still being released, and a complete CUDA build
was sitting installed the whole time. Restore it on an idle card with

```bash
C:/Python313/python.exe src/backends.py test vulkan --threads 6
C:/Python313/python.exe src/backends.py test cuda
```

Measured 2026-09-20 23:54:43 and 23:54:56: both `ok`, `model_load_ok`, 10.7 s each, ending at
`active "cuda"` with `vulkan` applied — this state. Since defect 25 a **boot** can no longer write that
verdict at all; only a self-test can, and only when the engine's own words blame the accelerator. Note
both runs report `"rc": 1` beside `"ok": true`: this build's shim exits 1 on a healthy load, so a
non-zero exit is never by itself a condemnation — read the `detail`, not the code.

## F. The console will not start

```bash
C:/Python313/python.exe LYGO_LLM_CONSOLE.bat         # by hand, so the error is visible
C:/Python313/python.exe -c "import sys;sys.path.insert(0,'src');import paths;print(paths.ENGINE_DIR, paths.LOGS)"
```

- **Port already in use** → something is still up on 9641: find it with §D.
- **Engine never becomes healthy** → the engine's own log is per port:
  `save/logs/llama-server-<PORT>.log`. **Decode it with the kit's reader, not by eye** —
  `model_check._decode()` scores `utf-8` / `utf-16` / `utf-16-be` because this build writes UTF-8 while
  other builds write UTF-16, and a wrong decode returns *gibberish without raising*.
- **A polluted log** (a tool wrote into the console's engine log) → `save/logs/archive/` is where the kit
  moves such a file; the archive is deliberately never scanned.

## G. A model file is gone (the stick is out)

Expected behaviour: the boot raises, `model_check`/`model_route` classify it as a **rig** condition, the
turn fails soft and can be routed to another model or the API brain. `lygo.llminfo` shows
"cannot see it" for that record.

To re-point a record, the registry is keyed by content, so the honest fix is to let the scan find the same
weights in another store and let dedupe fold them (other names become `also_known_as`) — never hand-edit
two records for one file. This is open item **L10**: the choice box does not yet say "not plugged in".

## H. Verifying a build before handing it on

```bash
C:/Python313/python.exe -m pytest -q
C:/Python313/python.exe scripts/refresh_manifests.py
C:/Python313/python.exe scripts/certify_build.py
```

`refresh_manifests` is only needed when a manifest-tracked file changed (**BRAND_MANIFEST**: LICENSE,
NOTICE, TRADEMARKS.md, LICENSING.md, SUCCESSION.md, BRANDING.md, README.md, READ_DISCLAIMER_FIRST.md,
portal/index.html, web_portal/index.html, scripts/certify_build.py — **SESSIONS_MANIFEST**: `src/sessions.py`,
`src/compaction.py`, `src/server.py`, `src/continuity.py`, `src/limbs.py`, `src/chat_loop.py`,
`portal/app.js`, `portal/index.html`, `tests/test_sessions.py`, `tests/test_record_e2e.py`, `SESSIONS.md`).
`docs/` is not manifest-tracked, so the map, log, ledger and handoff can be edited freely.

Certify compares **LF-normalised** bytes, so a CRLF checkout of a clean build still certifies.

## I. Where the evidence lives

| path | holds |
|---|---|
| `save/registry.json` | one record per weights file; `selected` + `selected_source` (the operator pin) |
| `save/model_check.json` | per model: verdict, fit, probe (including `gpu_backend`, `gpu_device`, `gpu_layers_used`, `gen_tps`), `boot_s`, the engine's own reason on failure |
| `data/perf.json` | host records keyed by an *installed-RAM* fingerprint, including `verdict.<backend>` |
| `data/perf_active.json` | which backend build is active, and why |
| `config/console.json` | the only place an operator pin or default may be set (`"gpu": "auto" \| "off"`) |
| `save/logs/` | engine logs, one per port; `save/logs/archive/` for retired ones |
| `docs/` | `ARCHITECTURE_MAP.md` (the wiring), `BUILDERS_LOG.md` (the pass log), `DEFECT_LEDGER.md` (every fault + its evidence), `HANDOFF.md` (this session's state), `RECOVERY.md` (this page) |

## J. Running the checker again

The checker has no CLI; drive it from Python (own port 11481, never the console's):

```bash
C:/Python313/python.exe C:/Users/justi/AppData/Local/Temp/gpu_sweep_all.py   # the sweep used this pass
```

or in one line:

```bash
C:/Python313/python.exe -c "import sys;sys.path.insert(0,'src');import model_check;model_check.run()"
```

Small models first, each booted through the console's own launch path (`lygo_engine.boot`), each failure
recorded with the engine's own sentence and classified `rig` vs `engine` vs `wiring`. Expect ~11 minutes
for the full lineup on the GPU path.
