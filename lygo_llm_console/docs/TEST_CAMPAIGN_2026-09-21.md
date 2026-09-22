# Test campaign 2026-09-21 — local vs API, switching, images

Harness: `scripts/bench_brains.py` (part one), `scripts/bench_brains2.py` (part two).
Raw rows: `workspace/memory/test-campaign-2026-09-21.jsonl`.
Console under test: live on port 9651, brain LOCAL, keys wired `[deepseek, nvidia, gemini, groq]`.

Every number below came from a real call against the running console or the vendor's own endpoint.

---

## What passed

| Test | Result |
|------|--------|
| Local ↔ API switching, 3 full cycles | every cycle correct: local turn `brain=ready`, API turn `brain=cloud`, `answered_by=deepseek`, `enabled` tracked both ways |
| DeepSeek through the console | `DEEPSEEK CONSOLE OK`, **1.07 s** |
| Failover catching a real vendor failure | NVIDIA returned 500 mid-campaign → DeepSeek answered the turn (`chain_tried ['nvidia:500','deepseek:200']`) |
| Image generation, local SD, 256x256, 8 steps | **ok, 7.8 s, 123,745 bytes**, `sd_xl_turbo_1.0_fp16` |
| Image generation, named model `qwen-image-2.1`, 256x256, 20 steps | **ok, 29.7 s, 97,021 bytes** |
| Image reading with **our own** engine (mmproj) | **ok, 109.3 s**, and the description was right: *"abstract, geometric composition featuring sharp angular shapes and a warm colour palette of orange, yellow, and white"* |

## Issues found (logged, not fixed during testing)

### I1 — Switching provider keeps the previous provider's model, so every API turn 404s. **Severe**
`POST /api/cloud {"provider":"nvidia"}` leaves `model=deepseek-chat` in place. The console then posts
`deepseek-chat` to NVIDIA's endpoint and every turn comes back
`⚠ API handoff — API endpoint or model not found — 404`, for nvidia, gemini and groq alike
(`chain_tried ['nvidia:404'] ['gemini:404'] ['groq:404']`).
This is the operator's "the API system is not working": choosing a provider in the pane breaks the API
until the model is also set by hand. With the model set explicitly, the same provider answers — see
part two. The route (and the pane's Save) must adopt the provider's own default model when the provider
changes and no model is given.

### I2 — A failed API turn answers with a warning instead of falling back to the local engine. **High**
`[BENCH] failover` came back `brain=ready` — the engine was up and ready — but the reply text was the
notice `⚠ API handoff — API endpoint or model not found …` (334 chars). The operator is shown a vendor
error where an answer was available. The handoff should hand the turn to the local brain and answer.

### I3 — `chain_tried` carries a previous turn's refusals. **Low**
A turn NVIDIA had just answered still reports `chain_tried ['nvidia:500','deepseek:200']`, and the same
list repeats on later turns. Misleading pane; the walk should reset the record when it starts.

### I4 — Groq's shipped model returns empty content on short asks. **Medium**
Direct: rep 1 `200 'GROQ OK'` in 0.23 s; rep 2 `200` with **0 characters** ("empty content").
A reasoning model (`openai/gpt-oss-20b`) spending a small budget; a chain hop that sometimes answers
nothing is worse than no hop.

### I5 — Gemini truncates, and is the slowest provider by an order of magnitude. **Medium**
Asked to reply `GEMINI OK` with a 64-token budget: rep 1 returned **`GEM`** (11.22 s), rep 2 **`GEMINI`**
(5.02 s). Compare deepseek 0.82-1.07 s, nvidia 0.36-0.63 s, groq 0.23-0.31 s.

### I6 — The local brain leaks the clock/world readout into ordinary answers. **Medium**
"reply with exactly: LOCAL SIDE" → `LOCAL SIDE\n\nNOW UTC 2026-09-21T19:00:19+00:00 · local 2026-09-…`.
Cycle 2 asked the same thing and returned an 829-character explanation of the time instead of the answer.
The clock line belongs in the request, not in what the operator is shown.

### I7 — A wrong limb is chosen, and the limb's own Python error becomes the answer. **Medium**
"list three words that rhyme with 'stack', comma separated" → the brain called `calc`, and the reply was
`calc could not answer (invalid syntax (<unknown>, line 1))` — an internal traceback string shown to the
operator as the answer.

### I8 — Performance, for the record
Local short turns: 1.17 s / 2.60 s / 4.11 s / 6.52 s / 9.36 s (the 9.36 s turn produced 829 chars; no
tokens/sec figure is available in the reply). API turns: deepseek 0.8-1.1 s, nvidia 0.4-0.6 s,
groq 0.2-0.3 s, gemini 5-11 s.

### I9 — Harness, not the console
Part one died on `WinError 206` (base64 image passed on a Windows command line — my bug, and why part two
exists). The console was restored by the harness's own `finally` before it exited (`provider=deepseek`,
`enabled=false`).

## Not yet tested when this was written

* each provider through the console **with its own model** (part two)
* Gemini vision: an image part posted to the API brain (part two)
* the API brain asking for a picture and returning a file (part two)


## Issues found and fixed (fixes applied only after the campaign finished)

| # | Issue (measured) | Fix | Verified by |
|---|---|---|---|
| 1 | Switching provider kept the previous provider's model, so every non-DeepSeek turn came back `404 model not found` (NVIDIA, Gemini, Groq alike). This is the operator's "the API system is not working". | `cloud_api.save()` adopts that provider's model when the provider changes and no explicit model is given; an explicit model still wins | live: bare switch to nvidia -> model `nvidia/nemotron-3-super-120b-a12b` -> turn answers `NVIDIA VIA UI SWITCH`; unit |
| 2 | The local fallback inherited the API's model AND its API-only fields, so an engine that was ready refused the turn and the operator got the `API handoff` notice instead of an answer | `cloud_api.local_payload_from()` re-addresses the turn to the engine; used at the handoff site | unit (payload keeps the conversation, drops `chat_template_kwargs`); the 404 case deliberately does NOT hand off - it reports the bad model, which is actionable |
| 3 | A reasoning provider given a small budget answered almost nothing: Gemini returned `GEM` (11.2 s) and Groq an empty string, while DeepSeek answered in 0.9 s on the same budget | `REASONING_FLOOR` + `effective_max_tokens()` raise a provider's budget, never lower an ask | unit |
| 4 | The answer carried the clock readout: asked to reply exactly `KEY CHECK`, the agent answered the clock | the readout is stripped at the one point every turn's text passes through (both brains, stream and buffered) | live: `READOUT CHECK`; unit |
| 5 | A failed limb's internal error was shown as the reply (`calc could not answer (invalid syntax (<unknown>, line 1))`) | a limb failure never stands in for an answer; the limb is named, the traceback stays out | unit |
| 6 | Regression introduced during this pass: the archive raised `KeyError('cursor')` on every turn (state key the content re-key no longer writes); the filing had already happened, only the return value broke | report the honest count of filed messages | RED->GREEN proven: reverting the line reproduces the exact console log message, the fix clears it |
| 7 | Both agents told the operator the console serves on **9641** while it was bound to **9651** - they were quoting `config/console.json`'s default, because `--port` only ever reached the banner, never the facts the agent reads | the boot publishes `LYGO_CONSOLE_PORT`; `runtime_facts`/`banner` prefer the live port, config is the fallback | unit: `live_facts` and the runtime block both carry `http://127.0.0.1:9651/` |
| 8 | The tail sentence ("world_pulse holds city clocks and weather ...") was handed back as the answer to unrelated questions; a real task given to the local agent came back as the city clocks | the tail now labels itself: context for the turn, NOT the question, NOT an answer to repeat | unit: the label is present in the tail and never reaches the operator |
| 9 | `tests/test_transcript_archive.py` (mine) was timing-dependent - it read the archive before the background writer flushed, and passed only when the writer won the race | the test flushes first | 5 consecutive clean runs |

Suite: 1035 passed / 43 subtests (pre-fix run), then CERTIFIED BUILD after the fixes with the manifests refreshed.

## Final measurement (after the fixes)

| Check | Result |
|---|---|
| Full suite | `1085 passed, 43 subtests passed in 151.40s`, `SUITE_EXIT=0` |
| Provider switch with no model named, live | `model=nvidia/nemotron-3-super-120b-a12b`, turn `200 'NVIDIA VIA UI SWITCH'` (2.01s) |
| Bad model configured, live | 404 reported by name, not swallowed: `⚠ API handoff ... The model \`this-model-does-not-exist-lygo\` does not exist` |
| Readout in the answer, live | turn returns exactly `READOUT CHECK` |
| Both agents' own report of the port | 9651 (was 9641 before the fix) |
| Local agent given a task | ran the `steward_map` limb, reported its output verbatim, stated its own boundary (26.48s) |
| Live verification verdict | `RESULT: ALL PASS`, `VERIFY_EXIT=0` |
| Build | `CERTIFIED BUILD`, manifests refreshed (2 entries) |

Regression found and closed during this pass: my own tail relabelling broke two standing guards (`2 failed, 1073 passed`); the label and the capability line are both kept now. Harness flaws found and closed: restore only on the happy path (a crash left the console on `groq` + a model that does not exist), an assertion on a field the reply body does not carry, and a timing-dependent archive test.

## Row 76 closed, live (after the fixes)

| Check | Result |
|---|---|
| Console port | declared **9641** console / 11441 engine (the stick owns 9651) |
| A picture asked for through the API brain | limb ran: `gen-20260921-140400.png`, 149,855 bytes, 15.4s (18.5s turn) |
| Was it named in the answer | yes, with bytes and path |
| Was the file really there | yes |
| Artifact check verdict | `PASS - the answer names the picture it produced` |
| Four-scenario re-verification on 9641 | `RESULT: ALL PASS` |

Observation, not a defect: a cloud-brain limb turn is presented as the limb's own line (`image_generate(prompt=...) -> path=... bytes=... steps=4 cfg_scale=1.0 model=sd_xl_turbo_1.0_fp16.safetensors`) rather than as prose. It names the result, which is what row 76 lacked, and for a development console the receipt is arguably the right presentation - recorded so the choice is visible rather than accidental.

---

## Part three — the USB copy, brought to 1.3.0 and tested on its own tree

The steward: *"add the new updates to the USB version, test it and complete the update to the new version of
the USB also"*. The stick kit (`E:\LYGO_BUILDER_KEY\lygo_llm_console`) was still 1.2.2.

**The port.** Backed the old stick tree up first (269 files, `.backups/stick-1.2.2-20260921`), then mirrored
`src/ tests/ scripts/ portal/ prompts/ skills/ tools/ web_portal/ docs/` plus the shared root files. Not
touched, by design: the stick's `config/`, its own `LYGO_AGENT_STICK*.bat` launchers, `engine/`, `python/`,
`models/`, `save/`, `workspace/`. Result: all nine trees byte-identical, stick `VERSION` 1.3.0.

**Tested on the stick itself** (its own bundled Python, its own ports 9651/11451, its own older engine b10988):

| Check | Result |
|---|---|
| Boot banner | `LYGO LLM Console v1.3.0 http://127.0.0.1:9651` · kit path on `E:` |
| `/api/health` | `build: v1.3.0`, `release: 1.3.0`, `broker: ready`, `engine_present: true`, `config_errors: []` |
| Self-identification | `system.id: usb_local` — “kit on removable media (GetDriveTypeW(E:) = REMOVABLE)” |
| Static sweep (stick's own copy) | `SWEEP RESULT: 0 failure(s), 13 note(s)` |
| Suite on the stick tree | the 5 PC-config assertions skip with a printed reason; everything else green |
| A real turn | asked for `17*23` via the calc limb → **391** in 6.9 s on the local brain |
| Forever history | the turn filed verbatim in `workspace/memory/conversations/2026-09-21/142948-lygo-6c258280.md` |
| Manifest + license | `VERDICT: CERTIFIED BUILD` |

**Two real defects came out of testing the stick**, neither visible from the PC:

1. The completion line credited a cloud provider for a **local** answer (`qwen2.5:1.5b · ready · answered by deepseek`).
   Fixed at the archive and both call sites; RED first, 3 new tests.
2. Five standing tests asserted the **shipped PC config** and a git checkout above the kit — invariants a
   stick cannot have. Marked PC-build assertions (skipped on removable media) rather than weakened: they still
   run and must pass on the PC.

**Honest limits of this test.** The stick has **no model blobs** — its canonical store
`%USB%\product\models\ollama` does not exist and the old duplicate CAS was archived to
`I:\LYGO_STICK_ARCHIVE\dup_cas_20260918`. The turn above ran with `OLLAMA_MODELS` pointed at this PC's store,
so it proves the stick's *code* answers end to end — it does **not** prove the stick is self-sufficient on a
stranger's machine. Restoring that store (or deciding the stick is cloud-only) is the steward's call. Also:
stopping the PC console was needed to give the stick's engine the GPU and the RAM — two engines on one box
fight over both.
