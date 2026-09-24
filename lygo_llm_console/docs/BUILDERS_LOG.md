
## 2026-09-21 · 1.3.0 finalized for the PC — the campaign, the fixes, and the sweep

**Trigger.** The steward: *"do one final bug sweep on this upgraded version and finalize the version with all the new fixes … we can conclude this version is completed for the PC with many upgrades and fixes"*, then *"add the new updates to the USB version, test it and complete the update to the new version of the USB also"*.

**What this release carries.** Forever history (every turn filed to `workspace/memory/conversations/`, content-keyed so a trimmed window still files once) and the LYGO RAG (BM25, no model); the four-provider chain DeepSeek → NVIDIA NIM → Google Gemini → Groq with the model following the provider; image reading and generation measured both ways (our engine and the API); and answer fidelity — the readout is stripped, a failed limb is never the answer, and a picture the turn produced is named in the reply.

**Verified in the session that wrote this**, not remembered: full suite `1089 passed, 43 subtests passed`; four-scenario live re-verification `ALL PASS`; the picture check `PASS` (named and on disk); the `scripts/sweep_build.py` sweep `0 failure(s)` including the live smoke on the copy's own port 9641.

**New tooling shipped with the build:** `scripts/sweep_build.py` (re-runnable bug sweep: syntax, encoding, duplicate definitions, undefined names, bare excepts, markers, orphans, version agreement, manifest freshness, plus a live smoke), `scripts/verify_fixes_live.py`, `scripts/verify_artifact_live.py`, `scripts/bench_brains.py`, `scripts/bench_brains2.py`, `scripts/read_history.py`.

**Open, carried forward:** the stick's key material (row 61, the steward's call); `src/p3_note.py` is an orphan (`vortex_signature()` imported nowhere — wire it into receipts or retire it); the local agent's taskability is measured once; vulkan still on b10988; the photo-price calibration; the 5,428% window composition.
# Builder's log — lygo_llm_console

Newest first. One entry per focused pass: what was read, what was found, what changed, and the evidence
that says so. **Rule: an entry is struck or closed only by a measurement or a test**, never by "should be
fine now". Corrections to my own work are logged like any other finding — a builder whose log only
contains wins is not keeping a log.

## 2026-09-21 - pass: branding on boot, and the API key that was never broken

The engine now introduces itself. `src/banner.py` draws LYGO in ANSI Shadow above the three plain lines
the console has always printed, and it draws **live** facts, not typed ones: the card and its free
memory, RAM, CPU threads, backend, build, ports. The engine line follows when the model loads
(`◆ Δ9Φ963  loading qwen2.5-coder:7b   engine cuda · build b11074 · port 11441`), and the window title
carries the mark too. Every lookup is guarded and a missing one prints a blank with the reason: a banner
that can stop a boot is worse than no banner.

Two mistakes of mine in that work, both worth remembering:

1. The boot called `live_facts(url=…, kit=…, console_port=…, engine_port=…)`; `kit` did not exist. The
   guard caught it and the console booted - printing `[banner] degraded: TypeError` instead of the logo.
   The test that catches this is one that calls **what the boot calls**, not one that tests the renderer.
2. My `try:` went in at 4 spaces where the surrounding block was at 12, and the console would not start
   at all (`SyntaxError` at server.py:2632). A `py_compile` after every patch of that file is now part of
   the loop.

On the API report: the key was fine all along. `POST /v1/chat/completions` answers 200 with the token,
with the engine key, and with no key at all (loopback is trusted), the DeepSeek endpoint answers 200, and
`config/api.json` was `enabled: false` with a stale `deepseek:401` in `chain_tried`. The real defect was
that the console **knew** that 401 and threw it away - `chain_tried` had it, `last_code`/`last_error`
(what the panel prints) held zero and empty. The walk now records its own code and reason, in the
operator's words, and `POST /api/cloud {"action": "probe"}` asks the key directly and records the answer:
`{"ok": true, "code": 200, "seconds": 1.1, "why": "the key answered"}`.

---

## 2026-09-21 - pass: the picture that draws itself, and the harness that asks the box first

`image_generate` stopped reporting the busy card and started treating it as an instruction. The limb asks
`hardware.picture_route(644)` before it spawns anything: when the chat model holds the card it takes the CPU
route itself and says so in the note. Measured: 172.1 s for a 1024x1024 SDXL-Turbo picture alone, and
333.0 s end-to-end through the console ("I have generated the image of the red cube on a white table ...
gen-20260921-112236.png"), gemma4-12b resident throughout.

`src/hardware.py` is the new sense organ: one `nvidia-smi` process per 2 s for the card's free memory and
utilisation, exact RAM from `GlobalMemoryStatusEx`, CPU from the first available of psutil/powershell/wmic,
and a decision - cuda or cpu, with a sentence saying why - that a limb can act on. It is deliberately hard
to make it raise: an unreadable counter is a blank with a reason, never an exception.

Two mistakes of my own, caught by measuring rather than by any test:

1. The first `_proc_name()` shelled out to `tasklist` per holder. `snapshot()` cost **3.678 s** and
   `/api/health` **4.766 s**; it is **0.103 s** now (Win32 `QueryFullProcessImageNameW` + a 300 s cache).
2. `holder_note()` picked the largest graphics context - and this desktop has ~23 of them at 0 MiB. It
   said "dwm.exe (pid 1504) holds 0 MiB of the card". Only a holder with memory is a holder now.

One thing this box cannot do: per-process VRAM is not accounted on this driver (Windows/WDDM). With
gemma4-12b resident, `--query-compute-apps` reported 0 MiB for llama-server. Free VRAM is reliable; naming
the holder may not be. The route decision does not depend on the name.

---

## 2026-09-21 · pass: the picture that now draws itself, and the harness that asks the box first

Trigger: **"focus on getting the basic image reading and generation working with the gemma4 … then i will
test myself"** plus **"make harnesses for this console that better scan this PC so it can use the vram,
gpu and cpu better in real time"**. Ollama / a from-scratch reader for the two unreadable models was put
on the shelf by the steward - not needed now.

**W8 — the picture route was measured, then taken, then proven.** The limb used to report the busy card
and stop; on this box the chat model holds the whole card on every working boot, so that is the same as
never drawing. Measured alone: the CPU build renders a real 1024×1024 SDXL-Turbo picture in **172.1 s**
(`ok True`, `engine sd-cpu`, 1,299,042 bytes). Measured through the operator's own route
(`POST /api/chat`, gemma4-12b resident): **200 in 333.0 s**, reply *"I have generated the image of the red
cube on a white table. The file is saved at …gen-20260921-112236.png"*, a real **957,430-byte** PNG on
disk. The limb now decides by itself, and `image_generate` says which route drew the picture and why.

**W9 — the harness the steward asked for.** New `src/hardware.py`: live card readings (total/used/free
VRAM, utilisation, temperature, power through one `nvidia-smi` process), **who is holding the card**
(pid + MiB per process, named through `tasklist`), exact RAM through `GlobalMemoryStatusEx`, CPU busy +
cores, a 2-second cache so a polling panel cannot spawn a process per view, `reset_cache()` to ask again,
and one decision the limbs actually use: `picture_route(need_mib)` → `("cuda"|"cpu", why)`. Nothing in it
raises: an unreadable counter is a blank with a reason. Wired into `media_tools.image_generate` **before**
an engine is spawned, so a card that cannot take the render costs nothing instead of ~20 s and a CUDA
warning. `tests/test_hardware.py` (10 tests: real-line parsing, a busy card read as busy, no card at all,
a raising reading, the decision both ways with the holder named, the cache, and the box's own RAM/CPU
measured for real).

**W10 — what the measurements corrected.** (a) `media_tools`' design note claimed sd.cpp's `--auto-fit`
lets a render proceed on a shared card - measured false (died asking 644.05 MB with 0.00 available);
struck. (b) `mock.patch.object(mt.subprocess, "run", …)` patches the global module, so the new sensor
read through the test's own fake - the busy-card tests now pin `picture_route`. (c) A comment inside a
backslash-continued `with` chain is a syntax error; removed.

**W11 — one live defect found, in a class claimed closed.** `GET /api/health` answered **500** three times
while gemma4 was loading (500/200/500/200/200/500 in the access log) and 40/40 **200** once the engine was
up. Defect 34 closed that class by contract, and its proof forced each probe to raise - so something
outside that coverage fails in the boot window. Not fixed; the reproduction is cheap (poll health through
a boot, read the 500 body's `detail`). Until then the ledger's own "never 500" is too strong, and this is
the first thing owed next, along with the full-suite run for this pass.

---

## 2026-09-21 · pass: the photo the engine refused — and the two models the engine cannot read

Trigger: the steward's **"image read + create broke after the switch to gemma4 … we need to re wire it
all.. test it"**, then **"seems the engine also needs a small update so it reads the two models it cant
read like nemo"**. Read: `save/receipts/7cbd2802*.json`, `save/logs/console-20260921.log`,
`save/logs/llama-server-11441.log`, `save/registry.json`, `src/server.py`, `src/compaction.py`,
`src/image_tools.py`, `src/media_tools.py`, `src/openai_proxy.py`, `portal/app.js`,
`scripts/fetch_engine.ps1`, `engine/backends/*/backend.json`, `D:\Ollama\`.

**W1 — the photo was turned into text before it was ever sent.** A receipt from the failing turn
(`7cbd2802`, 09:56:59, `has_image: true`) carried `output_sha256: e3b0c442…b855` — the SHA-256 of the
**empty string** — and the engine's log ended `request (133868 tokens) exceeds the available context size
(32768 tokens)`. The cause sat in one line of `src/server.py`: the volatile tail was appended with
`str(msgs[-1].get("content") or "")`, and on an image turn `content` is a **list** of parts, so `str()`
wrote the parts out as Python source — the photo's **base64 data URL as plain text**, ~74,000 tokens per
photo. The engine refused, zero frames came back, and the page raised its banner. Fixed: the tail rides as
a part (`list(content) + [{"type": "text", …}]`).

**W2 — and nothing could have caught it, because the console had no price for a picture.**
`compaction.est_tokens` billed any content list a flat **900** tokens and `trim_messages` exempts the
newest messages, so the last control before the engine literally could not see the photo. New
`src/vision.py` prices a picture per patch of its real pixels, fits the newest photo to the window, sheds
older ones to `[image]`, and answers in words when a turn still cannot fit.

**W3 — reading, proven live.** `[vision] {"used": 16381, "window": 32768, "shed": 0, "shrunk": 1, "over":
false}` on a **2400×1600** photo (downscaled first, previously unbounded); and through the console's own
engine path the engine described a picture this pass built on purpose: *"The picture has three horizontal
bands, which are red, green, and blue from top to bottom, and a circle sits in the middle."* — `finish:
stop`, empty `reasoning_content`, **6.7 s**. `tests/test_vision_budget.py` (18 passed).

**W4 — creation was never mis-wired; it was the card.** `sd-cli.exe` loaded the 6.9 GB checkpoint and died
19.8 s later: `need 644.05 MB device / 132.05 MB budget, available 0.00 MB device` — gemma4-12b holds the
whole 8 GB. The limb now says so in plain words (`memory_hint()`) and names the CPU route
(`retry_with_cpu` → `D:\LYGO_MEDIA\tools\sd-cpu\`). RED first: `AttributeError: media_tools has no
attribute 'memory_hint'`, then 3 passed.

**W5 — the engine update the steward asked for, and what it did and did not buy.** `qwen3.6:latest` and
`nemotron-3-super:latest` fail to boot on this kit. They are **Ollama** models (`source: legacy_cas`,
manifests under `registry.ollama.ai/library/`), and both refuse **identically** on the pinned build and on
the newest release — so the engine build was never the blocker: `check_tensor_dims: tensor
'blk.1.ffn_down_exps.weight' has wrong shape` (`nemotron_h_moe`, 80.9 GiB) and `key
qwen35moe.rope.dimension_sections has wrong array length; expected 4, got 3` (`qwen35moe`, 22.3 GiB). I
fetched the newest anyway (the kit's own `scripts/fetch_engine.ps1 -Backend cuda -Tag b11074`): the cuda
backend is now **`version: 0.4.1-dev (build 11074, commit 26394b4e)`**, the previous build is preserved at
`engine\backends\cuda-b10988\` (tag verified), and the script's pin was raised so a re-run cannot
silently downgrade. The engine that *can* read those two files is **Ollama's**, a different patch set
(`D:\Ollama\lib\ollama\llama-server.exe`, `version: 1 (cb295bf59)`); Ollama 0.32.1 is installed and its
own updater has already downloaded **v0.34.2** — the install is the steward's click, and that is the whole
of L3 now.

**W6 — my own errors this pass, logged like any other finding.** (a) I claimed a newer engine build would
read the two models; the A/B shows four bounded load attempts (2 models × 2 builds) all `exit 1` in ≤0.8 s
with byte-identical loader sentences. (b) The one suite failure was mine: `test_shipped_engine_purity.py`
read the backend store *while my fetch had `cuda/` deleted mid-replacement* — alone on the settled store it
passes (4 passed). (c) The first end-to-end photo probe died `ConnectionResetError` because I killed the
engine mid-turn (it was a child of the console instance I had started) — not a defect. (d) The
0.0092/px photo price is **conservative, not calibrated**: it comes from a two-point *difference* between
two console turns, and the live fitted turn implies it over-charges; recalibration is queued, not claimed.

**W7 — state left behind.** Nothing committed, pushed, sealed, swept, promoted or written to the stick kit.
Nothing is listening on 9631/9641/9651/11441. Engine fallback kept. Older, unchanged items stay open: L10
needs the steward's hands (unplug `E:`), L6 (cloud-brain image parts) untouched, `engine\backends\vulkan`
still on the old pin b10988.

**Suite:** **979 passed, 43 subtests, 1 failed** (the fetch race above; passes alone) — before the refresh
**978 passed, 43 subtests, 2 failed** (manifest identity, expected). **CERTIFIED** 11/11 both manifests.

---

## 2026-09-21 · pass: the greeting that answered with the clock — and the 500 that reads as a death

Trigger: the steward's **"do another pass complete anthing hung, de bug and fix the LLM struggling to
reply properly"**. Read: a fresh boot of this tree on port 9641 (`--no-browser`, stderr captured),
`save/logs/console-20260921.log`, `save/logs/llama-server-11441.log`, `data/engine.pid.json`,
`src/chat_loop.py`, `src/continuity.py`, `src/server.py` (turn path, tail site, health route),
`portal/app.js`, and the tree itself for anything left hung. Every number below is a live reading on this
box through the console's own transport and its own message shape.

**W1 — nothing was hung, and that had to be said with evidence.** No `*.lock`, `*.pid`, `*.tmp` or
in-flight marker anywhere in the tree; no `llama-server` process; ports 9631/9641/9651/11441/11471/11481
all free; the console and engine from the previous pass were gone. The one piece of stale state —
`data/engine.pid.json` naming a dead pid — turns out to be read in exactly one place,
`engine.kill_recorded_pids()`, which verifies the process image before killing anything. **I had claimed
in the previous pass's ledger row that "a stale pid reads as a live engine"; that was carried, not
measured, and it is corrected here** (`engine.pid.json` is cosmetic; no self-invalidation is owed). The
sweep is what let me say "nothing hung" rather than "I didn't find anything".

**W2 — the greeting defect had a second half the last pass never touched.** Booted fresh, the console
answered all ten turns of my first pass through it: real asks correct (`17*23` → `calc` → 391, "what time
is it?" → `now`, Tokyo → `weather`, recursion → prose), limbs withheld on greetings as designed — and two
greetings still wrong: `hi` → **"UNKNOWN (named SHADOW)"** and `thanks` → **"Understood. I'll adhere to
the guidelines and provide answers based on the information provided."** Sent again a second time, with
the session now holding the first run's answers, the pattern had *spread*: `thanks` → **"Understood. The
current time is UTC 2026-09-21T15:25:05+00:00…"** and `you there?` → **"Yes, I'm here.  NOW: - UTC: …"**.
The model was reciting the volatile tail — the clock line and the capability line — back at the
operator, and once the session held one such answer every later greeting inherited it.

**W3 — my first hypothesis for this half was wrong too, and the A/B said so.** I thought the heavy
identity block (the limb inventory, the skills catalog, SHADOW-as-known-missing) was what the model was
imitating, so I built a lean system block as arm C. On a fresh session **all three arms were 6 of 6
clean** — including the shipped one — which is how I learned the defect needs *history*: with a
contaminated session the shipped tail scores **7 of 12** (0 of 4 on `"thanks"`), the directive arm
**12 of 12**, and the lean block was no better than the shipped one. The history condition, not the block,
is what makes it reproduce, and the tail is what it recites.

**W4 — the fix, and what it cost.** `chat_loop.CONVERSATIONAL_DIRECTIVE` states the turn and asks for one
short warm line; `server._api_chat` appends it to the newest message on a turn that asks nothing and sends
the tail without the clock. Cost: nothing. The tail rides the newest message, so it is re-prefilled every
turn either way, and the greeting turn is now *cheaper* — the live console answers greetings in **0.5–1.8 s**
where the same turns took 1.6–4.8 s before. The wording is deliberately a statement, not an order: a bare
imperative under a greeting is what caused defect 30, and there is a test that the directive names no limb.

**W5 — the 500 in the access log is not the console dying, it is the health route giving up.** The
operator's own console at 00:16 ended its log with `GET /api/health → 500`, and mine did the same. This
pass I caught it live: five polled 200s, **one 500**, then 200s again while the engine was still loading —
so the last line is a symptom of the answer being impossible to build, not of a crash. The cause of *that*
one stays unreadable (the body, which carries the exception, goes only to a loopback caller, and both
callers that saw it threw it away — one of them my own startup wait loop, while the counting thread
happily reported "non-200: 0"), so instead of guessing I closed the class: `server.health_payload()` puts
each of ~14 live probes behind a `safe()` that blanks its own field and names itself in `degraded`, and the
route answers 200 even if the builder itself raises. Twelve probes forced to raise, twelve answers still
whole.

**Also measured, and neither is a product defect.** `test_media_limbs.py` needs the GPU: the console I had
booted for the live proof was holding the chat engine's 4.8 GB, so that file fails while a console is up
and passes with it stopped (28 passed). The two `test_branding.py` failures in the mid-pass run were this
pass's own source edits moving the manifest identity, cleared by `refresh_manifests.py`.

**Untouched:** no commit, no push, no seal, no sweep, no promotion or stick writes; `E:\LYGO_BUILDER_KEY`
and `I:\E Drive\lygo-protocol-stack\lygo_llm_console` are the operator's own trees and only this one was
edited. **Certify:** CERTIFIED (11/11 both manifests, 7 modules) after the refresh that this pass's edits
made necessary.

---

## 2026-09-21 · pass: the booted model answered a greeting with the weather — and my first diagnosis was wrong

Trigger: the steward booted the console and wrote **"i booted the model and its not responding properly =
heloo?"**. Read: `save/logs/console-20260921.log`, `save/logs/llama-server-11441.log`,
`data/engine.pid.json`, `src/continuity.py`, `src/chat_loop.py`, `src/server.py` (`_api_chat` and the limb
loop), `src/limbs.py`, `src/tools.py`, `tests/test_security_hardening.py`'s neighbours. Every number below
is a live reading on this box, measured through the console's own transport and its own parser.

**V1 — both processes were already dead when I looked, and the last line of the access log is a 500.**
The console (9641) and its engine (11441) were gone; `engine.pid.json` still named pid 82336, and the
engine's log ends mid-task with no shutdown line. The last access line is `GET /api/health HTTP/1.1 500`.
I booted the tree myself to work against (console 89432, engine 78172, `active cuda`, brain ready) and the
route answers **200 in 6,868 bytes** on a clean boot, in-process, so the 500 is real but unattributed — the
old console's stderr died with its window. Logged as **L11**, with the stale-pid wart beside it: a pid file
that outlives its process reads as a live engine.

**V2 — reproduced in one turn: "heloo?" comes back as clocks and weather.** `POST /api/chat` with the
operator's own text returns `text/event-stream`, 407 frames in 10.1 s, and a `done` frame carrying
`traces: [world_pulse]` — the console ran a limb and the answer was a city-clock and weather report. That
is the same block that arrived attached to the steward's own message.

**V3 — my first diagnosis was wrong, and this log says so.** The volatile tail (the one piece of prompt
text that rides the operator's own message) carried `Call world_pulse for city clocks + weather.` — an
order glued to "heloo?". I reworded it, wrote three tests, watched them fail then pass, and the greeting
**still** called a limb. Then I found my own first A/B was worthless: it printed `shipped line present in
tail: False`, because I had already fixed the file, so its "shipped" arm was the fixed text — a probe that
appeared to prove the wording was innocent. Redone with the shipped sentence hard-coded and the console's
own `extract_tool_calls` (so a call written as prose counts):

    operator text            limbs offered              limbs withheld
    "hi"                     world_pulse call  3/3      greeting  8/8
    "heloo?"                 world_pulse call  2/3
    "explain recursion"      prose, no call    3/3
    "what is 17 * 23?"       calc call         3/3
    "weather in Tokyo?"      weather call      2/3, wrapped in <tools>
    "what time is it?"       now / world_pulse 3/3

    wording, 8 reps each, same conditions: shipped sentence 6/6 calls · reworded 3/8 clean ·
    clock-only tail 4/8 clean · limbs withheld 8/8 clean

So the rewording is kept — it is a genuine improvement, 100% → about 60% — and logged as **not the fix**.

**V4 — the real defect: 24 limbs offered on a turn that asks for nothing.** The brain routes every real
ask correctly and reaches for a limb anyway on a greeting, so the console turned a hello into an errand
and narrated the errand's readout as the answer. `chat_loop.is_conversational()` now recognises a turn
that asks for nothing — strictly, the whole message and nothing else, ≤60 chars — and `server._api_chat`
withholds the limb schema on such a turn: nothing is offered, so nothing can be called. `"hi, what's the
weather in Tokyo?"` keeps every limb, which is the point of keeping the rule strict.

**V5 — a call this model actually emits was never parsed.** ```json fences and `<tool_call>` were handled;
`<tools>…</tools>` was not — measured: fence → parsed, `<tool_call>` → parsed, `<tools>` → `[]`. Two of
three weather calls arrived in that wrapper, so the limb the model asked for never ran and the operator was
shown raw JSON as the answer. The regex now accepts both tags.

**V6 — two of the failures in the 948-run were mine, not the product's.** The two `test_branding.py`
failures were my own edits moving the manifest identity (refreshed, then CERTIFIED). The live image test
failed with `model manager cannot make enough memory available on CUDA0: available 0.00 MB device` because
the console I had booted was holding the chat engine's 4.8 GB — with it stopped and the ports clear, that
file runs **28 passed**. Recorded here so a fresh session does not chase either as a defect, and because
the same contention shows up as a *product* symptom when the operator runs the image limb beside a live
chat engine.

**Suite:** 948 passed, 27 subtests (was 937). **Build:** CERTIFIED (11/11 both manifests, 7 modules), after
a manifest refresh that moved `src/server.py` `043e680c → e7b28af5`, `src/continuity.py`
`b7fee42c → 9e08deb2`, `src/chat_loop.py` `3f3ef511 → 1bc8e698`. **Untouched:** no commit, no push, no
seal, no sweep, no promotion, no stick writes. The console I booted for testing was stopped and both ports
left free — a booted console holds the GPU, which is exactly what the media test needs.

---

## 2026-09-20 · pass: reading the handoff back — four defects the 22:59 pass left behind

Read first: `docs/HANDOFF.md` (all 409 lines, to see whether a session with no memory could actually
resume from it), then §0's four commands run for real, `docs/RECOVERY.md`, `docs/DEFECT_LEDGER.md`,
`data/perf.json`, `data/perf_active.json`, `src/backends.py`, `src/lygo_engine.py`, `src/model_check.py`,
`src/registry.py`, `portal/app.js`. Every number below is a live reading on this box.

**V1 — the handoff's §3 backend row was false at the moment it was written.** The row says the console
was live on `cuda` with `vulkan` proven and left applied as a GPU-capable fallback. What `status` said
was `active "cpu"`, empty reason, `engine_dir …\engine`, and `data/perf_active.json` **gone** — so the
rule-4 silent CPU drop had already happened. `perf.json` carried both write-offs: `cuda` → `bad` at
**22:54:00** and `vulkan` → `bad` at **22:29:28**, both with the detail `launch_failed: RuntimeError:
llama-server exited 1` and no loader sentence anywhere in the record. The card was idle the whole time.

**V2 — the root cause was not the self-test, it was a boot.** Row 21 had already taught this box that a
*self-test* must not condemn a build. But `lygo_engine._drop_backend()` wrote a `bad` verdict,
deactivated the build and cleared the proven selection on **any** launch failure — including a contended
one ~74 s after the sweep's last GPU boot (22:52:46, `lygo-turbo-agent` on 11481, whose log was still
being written at 22:54). The busy-card and fault rules lived only in `ensure()`, so the boot path
bypassed every one of them, and a verdict is believed for six hours: the console just ran on CPU and
said nothing. **The clue was in the healthy records**: a good run reports `"rc": 1` beside `"ok": true,
model_load_ok` — this build's shim exits 1 on a healthy load, so nothing may key `bad` on an exit code.
Fix: `backends.boot_condemnation()` owns the question and refuses four ways a boot lies — the card was in
use, the launch faulted, the engine's own words blame the *model's* metadata (L3's class), or there are
no engine words at all. Only the accelerator refusing to come up still condemns. Five cases in
`tests/test_backends.py`; an idle-card self-test 12 minutes later: `cuda` `ok` 10.7 s, `vulkan` `ok`
10.7 s → `active "cuda"`, `applied_overlays ["vulkan"]`, `perf_active.json` rebuilt.

**V3 — two rows in this ledger read FIXED while the code had no fix.** #23's fix column described "let
the fit plan decide first" and #24's described driving the sweep from the deduped record set; neither
call site existed — `classify_failure()` took no fit plan, and the sweep enumerated both names of one
weights file. Both rows are corrected in place above (a Fix column that describes an intention is a
claim, not a measurement) and both are now built, with `tests/test_model_check.py` +4 cases. **This is
the same failure mode as the rest of this pass: a document asserting a state the tree was not in.**

**V4 — L10's label.** `reach()` answered *reachable* and *portable* but never *why*, so with the stick
out the choice box called its model "not found here" — the same words a file he had deleted gets. It now
returns a `state` (`available` / `not_plugged_in` / `missing`) and a `label` from the new
`drive_present()`, and `portal/app.js` renders the server's label. Three cases in
`tests/test_portable_models.py`. **I could not prove this one live:** that needs `E:` unplugged, and the
stick carries this very tree. Reading `registry.reach()` across the operator's own 19 records gives
`not reachable: 0 of 19` — correct, because the stick is in. Proof owed on hardware.

**V5 — the suite is green per run, not deterministically.** Three full runs: 1 failed/914 passed, then
915 passed/27 subtests, then 927 passed/27 subtests. The one failure was
`test_security_hardening.py::OversizedBodyTest::test_oversized_body_is_413_not_400` — the server answered
correctly (its stderr carries `POST /api/session … 413`) and then closed without draining the 600 kB
body, so Windows reset the connection and the client raised `ConnectionAbortedError [WinError 10053]`
before it could read the status. It passes in isolation and on rerun. Logged open as row 27: a test that
can lose its assertion to a TCP reset hides real breaks.

**Build identity moved, and I said so rather than hiding it.** `portal/app.js` is
`SESSIONS_MANIFEST`-tracked, so the picker change made the tree read `MODIFIED / UNCERTIFIED COPY`.
`scripts/refresh_manifests.py --note "portal/app.js: picker names a drive that is not plugged in (L10)"`
refreshed 1 of 11 entries (`85f5f139330d3bb3 → 313fb3150852bfb6`); `certify_build.py` returns
**CERTIFIED** (11/11 both manifests, 7 modules). This build is therefore **not** the identity the 22:59
handoff describes.

**V6 — the same defect was fixed on one surface and left on the other.** `_read_body`'s own docstring,
written by this pass, lists the ways a body read had gone wrong: a negative length, a non-numeric
length answered as a 500, an over-limit body emptied into a misleading `400 no_input`. Every one of
those was fixed in `server.py`. The **public gateway** — the one surface the internet can reach —
still parsed `Content-Length` with a bare `int()` (so `abc` closed the connection with **no answer at
all** and a traceback on the operator's stderr) and still refused an over-limit body **unread** (so an
outside caller still writing lost the reason to a reset, defect 27's exact mechanism). Found by asking
where else the same shape appears, not by reading the handoff. Both fixed; the refusal policy now
lives once, in `src/http_body.py`, and both `_send`s declare `Connection: close`. Two socket tests and
two malformed-envelope tests in `tests/test_public_gateway.py`; the pre-fix runs put the `ValueError`
traceback in pytest's captured stderr, which is what the operator would have seen in the console's
stderr too.

**V7 — the workaround outlived the bug.** `_api_chat()` and `_v1_chat()` each carried a second 413
branch for "the body came back empty with a large declared length" — written when a refused body was
*emptied*. With the refusal raising and the body drained, neither branch could be reached. Removed,
with a pointer to `_read_body`.

**V8 — there are two trees, and the stick's is pre-pass.** `I:\E Drive\lygo-protocol-stack\lygo_llm_console`
is this pass's tree (the stack: it has `src/model_check.py`, `tests/test_model_check.py`,
`docs/HANDOFF.md`, the whole checker/balancer pass, and the live `data/perf.json` whose verdicts I
repaired). `E:\LYGO_BUILDER_KEY\lygo_llm_console` is the stick's kit — and it has **no** `model_check.py`,
**no** `test_model_check.py`, **no** `docs/HANDOFF.md`: it predates the whole pass. Promotion debt (§10)
is therefore larger than a list of differing files, and nothing this pass did is on the stick until
someone promotes it. I wrote nothing to the stick.

**Untouched by me:** no commit, no push, no seal, no sweep, no promotion, no stick writes. L2
(kernel-side checker routes) and L3 (the engine fetch) stay the steward's calls and were not started.
`HANDOFF.md` itself was left as written — §3's backend row is still stale and is the first thing to
correct.

---

## 2026-09-20 · pass: completing CUDA — the engine the console could not use

Read first: `engine/backends/cuda/` and `engine/backends/vulkan/` (contents, manifests, sizes),
`backends.py` (store, `ensure`, self-test, verdict store, its own CLI), `engine.py` (`resolve_binary`,
`spawn_runner`), `paths.engine_dir()`, `lygo_engine.py` (`backend_selection`, `boot`), `perf.py` (the VRAM
reader), `model_check.py`, `model_route.py`. Every number below is a live reading on this box.

**C1 — the GPU build was already here: complete, matching, and usable.** `engine/backends/cuda/` is
`kind: "engine"`, tag `b10988` (the same build as the base engine), holding `ggml-cuda.dll` (138 MB), the
full CUDA 13 runtime (`cudart64_13`, `cublas64_13`, `cublasLt64_13`) plus the tools, and a per-file sha256
manifest. A complete launch directory means activating it is a **pointer swap, not a copy**. Cheapest
proof first — the build's own device list:

```
engine/backends/cuda/llama-server.exe --list-devices
Available devices:
  CUDA0: NVIDIA GeForce RTX 4060 Ti (8187 MiB, 7075 MiB free)      driver 616.92
```

The console could always have used this card. Nothing was missing but a proof.

**C2 — why it never did: two GPU verdicts taken while our own sweep held the card.** The per-host verdict
store in `perf.json`:

```
GamePC|20 · cuda   "bad" · launch_failed: llama-server exited 1        · 41.9 s · 21:08:56
GamePC|20 · vulkan "bad" · sha256-183715c4…: 0xC0000005 …             ·  3.1 s · 21:09:30
```

Those are the exact minutes my checker sweep was booting engines through the card. A verdict keyed by the
backend's own files never expires (L1), so both GPU backends stayed condemned: `active: "cpu"`, and
envwatch's amber was telling the truth about the consequence.

**C3 — two rules in `backends`, closing L1 and the defect class behind it.**
`VERDICT_RETRY_AFTER_S = 6h` with `_verdict_age_s()`: a remembered "bad" verdict is evidence about a
*moment*; past the window it no longer blocks a retest, and `allow_retest=True` still forces one on
request. And `card_busy()` with `SELFTEST_MIN_FREE_MIB = 3072`: a self-test only runs when no
`llama-server` is up **and** the card has room — otherwise `ensure()` returns `gpu_busy_not_probed` and
**remembers nothing**. Measuring the moment must never become a verdict about the backend.

**C4 — CUDA proven, then active.** `ensure(allow_retest=True)` → `self_test` loaded a real model on the
CUDA build in **10.7 s** (`gpu_ok: true`, `reason: self_test_passed`, device
`NVIDIA GeForce RTX 4060 Ti`), the verdict was remembered `ok`, and `set_active` pointed the launch dir at
`engine/backends/cuda`. `paths.engine_dir()` and `engine.resolve_binary()` now resolve there, so the
console's own launches use it — confirmed from the running console: `/api/health` →
`engine_dir: …\engine\backends\cuda`.

**C5 — the Vulkan overlay proven too, through the kit's own receipt CLI.**
`python src/backends.py test vulkan --threads 6` → `model_load_ok`, 10.6 s, device
`NVIDIA GeForce RTX 4060 Ti`, verdict `ok`. Both engine add-ons this box can carry are now proven, and
preference re-selected `cuda` (`reason: backend_proven_on_this_host`). The overlay stays applied on
purpose: it is proven here, and it makes the shipped CPU engine GPU-capable as a fallback.

**C6 — measured: the GPU is worth 3.0×, one variable at a time.** `gemma4-12b.gguf` (6.87 GiB), identical
build, identical flags, only `-ngl` differs:

| leg | boot | 200 tokens | rate |
|---|---|---|---|
| `-ngl 99` | 90.7 s | 9.26 s | **21.6 tok/s** |
| `-ngl 0` | 3.7 s | 28.29 s | **7.1 tok/s** |

Sustained generation is 3.0× faster; the first load costs 87 s extra (6.87 GiB into 8 GB of VRAM), so it
pays back inside the first ~10 turns. Small models gain more: `qwen2.5:1.5b`, 128 tokens in 0.94 s =
**135.8 tok/s**, where the CPU sweep on the same model recorded ~49.

**C7 — my own evidence reader was wrong, in two different ways.** (a) `_log_tail`/`_log_text` tried UTF-16
first and *succeeded with mojibake* on this build's UTF-8 log, because a wrong decode raises nothing — so a
recorded "why" could be garbage, and my own first reading of the offload line ("0 layers") came within one
step of becoming a fabricated finding. `_decode()` now scores `utf-8`/`utf-16`/`utf-16-be` and takes the
printable one. (b) `gpu_evidence()` recorded `gpu_layers_used: 0, devices_seen: 0` whenever the line was
simply absent — a **false zero**, the same defect class as `no_gpu_device`. It now records
`gpu_backend` (which build answered), `gpu_device` (that build's own device list) and
`gpu_layers_used = None` when unstated.

**C8 — two more false numbers removed.** `perf.gpu_free_mib()` asked the CPU-only base binary for devices
and answered `0` on a box with a free card (L9); `perf.gpu_vram_mib()` now reads the driver and both
`gpu_free_mib()` and `model_fit.rig_vram_mib()` use it — one owner — which also fixed the reader in
`registry.py`. And a rate is only recorded when the sample can carry it: a two-token answer had recorded
16.6 tok/s for a model that does 135.8, and that is the number a human reads in the choice box;
`rate_from()` requires ≥16 generated tokens and otherwise records the count and says "too few tokens to
rate".

**C9 — my retry rule broke the store path first, and the suite said so.** The new `stale =` line called
`.get()` on a **None** verdict, which is what a host that has never been tested has; the old code was safe
only because `fresh` short-circuited before it. `tests/test_backends.py` failed five times at
`backends.py:660` (`AttributeError: 'NoneType' object has no attribute 'get'`), the guard fixed it, and the
five pass. Logged as ledger #19, in the same table as everything else: a builder whose log only contains
wins is not keeping a log.

**Measured state after this pass.** `backends.report()` → `active: "cuda"`, `installed: ['cuda','vulkan']`,
overlays `['vulkan']`. `probe()` → `gpu_ok: True`, `vram_gib: 6.95`, `devices: [CUDA0 … 7075 MiB free]`,
`threads: 6`. Box: RTX 4060 Ti 8 GB (driver 616.92), i5-13600KF 6 P / 14 physical, 31.8 GB RAM. Drives
re-derived: C: fixed 930 GB, D: "LYGO TURBO DRIVE" fixed (vault), **E: `ESD-USB` removable 28.8 GB — the
stick**, F: empty reader, I: "MUSIC ONLY" fixed (the kit), J: "BULK SAVE" fixed.

**C10 — the sweep, on the GPU (648 s).** `model_check.run()` over the whole lineup: **14 of 17 run**, every
run recorded `gpu_backend: cuda`. `Gemma-4-12B-It` → `not_a_model` (a projector — correct not to boot);
`qwen3.6:latest` → `failed_soft`, class **engine** (`key qwen35moe.rope.dimension_sections has wrong array
length; expected 4, got 3`); `nemotron-3-super:latest` → `failed_soft`, class **rig** (86 GB against 24 GB
usable) — reclassified from `engine` now that the VRAM reading comes from the driver. `gpu_layers_used` is
`null` on every record: this build prints no offload line at its default verbosity, and an unstated count is
recorded as unknown, never as zero.

**C11 — the probe could not earn a rate, so it does now.** The measured turn was "Reply with exactly: OK"
(`max_tokens: 8`) → two tokens → `rate_from()` correctly *refused* to rate it, which left the choice box
with no speed labels at all. The turn is now a 64-token counting prompt: deterministic for every model and
long enough to carry a real number. The lineup is being re-measured with it, and the same sweep is the
widest exercise of the new wiring.

**C12 — handoff written for the next session.** `docs/HANDOFF.md` (state, the evidence behind each change,
the measured lineup, box facts, open queue in priority order, the laws verbatim, the do-nots) and
`docs/RECOVERY.md` (sixty-second health check, proving/reproving a backend, stray-engine cleanup, overlay
removal, log decoding, manifest scope, evidence paths). No push this round: the steward publishes, and the
debugging round is not finished.

**C13 — the suite was host-state dependent, and real work exposed it.** With the sweep holding the card,
six `tests/test_backends.py` cases failed — not because the store was wrong, but because my new busy-card
policy (correct in production) pre-empted their faked self-tests and they read this box's card state. Two
consequences, both fixed: the fixture holds `card_busy` open so a store test measures the store, and the
policy now has its own tests — a busy card is skipped and remembers **nothing**, and a `bad` verdict older
than the retry window is retested. The suite also went from 220 s back to its usual pace, because six tests
stopped shelling out to `tasklist`/`nvidia-smi` per call. Logged as ledger #20.

**C14 — my own pass took the GPU away, and the test suite was innocent.** After the first GPU sweep the
console was back on the CPU engine: `data/perf_active.json` was gone and both backends carried `bad` verdicts
written at 22:14:14 (cuda) and 22:16:16 (vulkan), each reading `launch_failed: RuntimeError: llama-server
exited 3221225477` — 0xC0000005 — on a box where that same build had self-tested clean at 11.7 s and answered
a live turn at 135.8 tok/s. I checked every test rather than assume: **no test in `tests/` touches the real
store** (all of `test_backends.py` patches the active file and the self-test). The writes came from the
checker's own sweep, whose per-model `ensure()` re-ran a **real** self-test, beside its own live engine. Three
defects, three fixes, each with a test:

- **a fault is not a verdict.** An access violation on launch is the card being taken away mid-teardown, so it
  remembers **nothing** (`backend_faulted_not_probed`) instead of condemning a working build; a build is
  condemned by a clean exit carrying the loader's own words (a key shape, a tensor shape) — which is what the
  `bad` path is for.
- **a proven selection is never withdrawn by a failed test.** `clear_active()` now runs only when nothing on
  this host is proven.
- **the memo was keyed by the thread count** (`host|enabled|threads`), so a varying `-t` re-tested for every
  model in a sweep — another launch beside a live engine each time. The key is now `host|enabled`: what the
  decision actually depends on.

Recovered through the kit's own receipt path on an idle card: `python src/backends.py test cuda` → `ok:
true`, `model_load_ok`, **14.3 s**, `active: "cuda"`. This is the **second** time today a contended self-test
wrote off a working GPU build; what is logged is the rule, not the incident.

**C15 — the sweep, completed on the CUDA build, with the fix holding under it.** 14 of 18 records now carry
`gpu_backend: cuda` and 14 carry a rate measured on the GPU: `llama3.2:1b` **166.9**, `qwen2.5:3b` 109.3,
`qwen2.5:1.5b` 92.7, `qwen2.5-coder:7b` 55.4, `llama3.1:8b` 52.5, `gemma2:9b` 40.4, `gemma-4-12B-qat` 29.2,
`gemma4-12b` 17.0, `lygo-turbo-coder` 8.6, `lygo-turbo-agent` 6.9, `deepseek-r1:14b` 4.1, `qwen2.5-coder:14b`
3.9, `phi4:14b` 3.7 tok/s, `nomic-embed-text` the embeddings endpoint (no generation rate to give). **Not one
`bad` backend verdict was written during the whole sweep** — the fault rule from C14 held under exactly the
condition that broke it twice before. Two findings came out of reading the finished records rather than the
run's console lines: `nemotron-3-super` was classed `engine` here and `rig` in another pass because
`classify_failure()` reads the class off the **log tail** (ledger #23), and the colon twin `gemma4:12b` holds a
stale CPU rate because the checker enumerated both names of one file (ledger #24).

**Verification.** `pytest -q` and `scripts/certify_build.py` re-run at the end of this pass (numbers in the
ledger's closing block). Live console proof: `/api/health` answered in 11.3 s with
`engine_dir: …\engine\backends\cuda`; `/api/models` → **19 records / 26 names**, every file present
(13 vault CAS · 5 `I:\LYGO_MODELS` · 1 stick CAS). Nothing committed, pushed or sealed.

---

## 2026-09-20 · focused pass: the engine, the harness, and the wiring between them

Read: `perf.py` (engine_devices / gpu_free_mib / physical_cores), `backends.py` (store, self-test,
verdicts), `lygo_engine.py` (plan → boot → state), `model_fit.py`, `model_check.py`, `model_route.py`,
`registry.py`, `modules/lygo.envwatch/backend.py`, `modules/lygo.llminfo/backend.py`, `server.py`,
`portal/app.js`. Every number below is from a live reading on this box, not from memory.

**B1 — the engine is not on the GPU, and the amber said so.**
`engine/llama-server.exe --list-devices` → `Available devices: (none)` (`rc 0`). `backends.report()` →
`active: "cpu"`, `installed: ['cuda','vulkan']`, `applied_overlays: []`. The base engine directory holds
only `ggml-cpu-*.dll`: the shipped engine is CPU-only by design, and the two GPU builds sit installed but
**unproven**. Consequence: the console runs the CPU-only path here, and envwatch's
"the GPU backend is not proven on this host" is a **true** finding.

**B2 — my own regression, found and corrected: I had silenced that true amber.**
`model_route.gpu_proven()` was built on `fit.mode == "gpu_full"`. A fit verdict is arithmetic over sizes —
it says a model *would* fit in the card. Eight records said `gpu_full` while the engine in use could not
see a device. A plan is not proof of use. Changed: `gpu_proven()` now requires `devices_seen` or
`gpu_layers_used` from a real launch (nothing records those yet, so the amber stands, correctly), and
envwatch's issue call is restored. Test:
`tests/test_model_route.py::test_a_plan_is_never_accepted_as_proof_the_gpu_carried_a_turn`.
**Recorded plainly: an earlier report of mine called this amber a false fault. It was not. The panel was
right and my guard was wrong.**

**B3 — ten models were mislabelled `no_gpu_device` on a box with an idle card.**
The reading came from the wrong place: `perf.gpu_free_mib()` → `engine_devices()` →
`llama-server --list-devices` on the **CPU-only base binary** → `[]` → `0`. So a caller's `0` (or a `0`
measured while another process held the card) was recorded as "this host has no GPU".
Changed: `model_fit.rig_vram_mib()` reads the **driver** (`nvidia-smi --query-gpu=memory.total,memory.free`)
— the rig's truth for planning — and a passed `0` now asks the driver instead of concluding. `no_gpu_device`
and `gpu_busy_at_check` are separate answers with separate next moves.
Measured after: this box reports `(8188, 7157)`; a 20 GB model plans `gpu_partial, ngl 28 of 99` (was
`cpu_tight / no_gpu_device`), a 7 GB model `ngl 78 of 99`. Tests: `tests/test_fail_soft_evidence.py`
(4 rig cases) and `tests/test_model_fit.py`'s host assumption made explicit (`setUp` pins a no-card host
instead of implying it with a `0` argument).

**B4 — a failure's reason is the engine's own sentence, and it never carries a hash.**
`boot raised RuntimeError: llama-server exited 1` is true and useless: the loader had already written the
cause. Added `model_check.own_words()` (lifts the loader's line — a known engine limit first, then any
error line) and `model_check.redact()` (32+ hex runs). The record now reads
`key qwen35moe.rope.dimension_sections has wrong array length; expected 4, got 3` and is classified
`engine`, not `rig`.

**B5 — the panel's own rule now holds at its edge.**
A GPU crash detail remembered from an older build still named a CAS blob
(`183715c4…`), because only the log-quote path had been redacted. Added `envwatch._safe_row()`: every
string the card renders is redacted on the way out, whichever module or stored record it came from.
Test: `tests/test_module_envwatch.py::TestWritesNothing::test_no_secret_material_reaches_the_panel`.

**B6 — a tool must never write into the console's log.**
The log is named by port (`save/logs/llama-server-<PORT>.log`), so the checker booting on the console's
port put 119 `failed to load model` lines into the *console's* engine log and envwatch reported
"engine fault ×119" on a healthy box. The checker now boots on its own port (11481; 11471 belongs to
`backends.SELFTEST_PORT`), and the polluted log was archived to `save/logs/archive/` rather than deleted.

**B7 — one weights file is one record.**
`gemma4-12b` (`I:\LYGO_MODELS\gemma4-12b.gguf`) and `gemma4:12b` were the same 7.38 GB listed twice: a CAS
blob hides the content hash in its *filename* (`sha256-1278394b…`) while the store copy carries it in
`sha256`, so path-keyed identity could not see it. Added `registry._file_identity()` — content hash first,
path as fallback; the dropped name survives as `also_known_as`, which the picker already renders.
Tests: `tests/test_registry_identity.py` (3).

**B8 — the plan's offload number is visible again.** `planned_ngl` read `plan["ngl"]` (always absent) —
the engine's own arg builder reads `plan["llama"]["ngl"]`. Now recorded with fallbacks.

**Verification.** `pytest -q` → **904 passed, 27 subtests**. `scripts/certify_build.py` →
**CERTIFIED** (11/11 both manifests, 7 modules validated). Nothing committed, pushed or sealed.

**Still open (see `DEFECT_LEDGER.md` and `ARCHITECTURE_MAP.md` §5).** L1 a remembered backend verdict
never expires; L2 the checker's routes are kernel-side (steward's call, Law 6); L3 two models need a
newer engine build; L5 no local sound model; L6 cloud image parts unproven; L8 cold first turn ~190 s;
plus the standing fact that `cuda`/`vulkan` remain unproven until `backends` proves a real load.

---

## 2026-09-20 · pass: LLM checker & balancer (earlier the same day)

Booted every model through the console's own launch path: **15 of 18 run**; the 3 that do not are one
projector (`Gemma-4-12B-It` — correct not to boot) and two loader limits
(`qwen3.6`, `nemotron-3-super` — engine build 10988 cannot read their GGUF metadata). Smallest first:
`qwen2.5:1.5b` 49.1 tok/s · `llama3.2:1b` 46.2 · `qwen2.5:3b` 24.1 · `lygo-turbo-coder` 7.4 (18.6 GB) ·
`lygo-turbo-agent` (21.2 GB). Every failure carries the engine's own reason, fails soft in ~7 s, and
leaves the port clean. Character dials raised to 48,000 per message / 600,000 per conversation. Thirteen
defects found and closed — the table lives in `DEFECT_LEDGER.md`.

---

## 2026-09-21 · pass: branded boot banner, the API-key answer, and the UI interface

Two asks: a futuristic ASCII LYGO logo on the PowerShell boot line, and "the API system is not working -
the Agent does not respond using API key". A third arrived mid-pass: *make sure the UI Local/API
switching button and the interface work cleanly.*

**Banner.** `src/banner.py` (NEW): the block-glyph LYGO wordmark, `Δ9Φ963 · LYGO PROTOCOL STACK ·
STEWARD: LIGHTFATHER`, live facts read at print time (VRAM/RAM/CPU threads, backend, ports, engine
build), wrapped rather than truncated at narrow widths, every call guarded so a banner can never break
a boot. Wired into the real boot path; `set_window_title()` sets the window title. **No key material
is printed.**

**The API key was never the problem.** `config/api.json` said `chain_tried: ["deepseek:401"]` beside
`last_code: 0` - a stale console-side record. Calling the provider exactly as the console calls it
(the stored `url` is the full endpoint) returned **200, `deepseek-flash`, "pong"**, and the live route
probe now returns `{"ok": true, "code": 200, "provider": "deepseek", "seconds": 1.1, "why": "the key
answered"}`. The walk now owns its own failure facts, so no caller can drop the reason, and
`POST /api/cloud {"action": "probe"}` answers "is my key alive?" in one call. The cloud brain is
`enabled: false` by choice - local is the default, and the switch is the switch.

**The UI, driven for real.** Both segments were clicked in a live browser, not just called:
`LOCAL -> API -> API off -> LOCAL` each returned the right state (`aria-pressed`, the status line, the
health box agreeing) with **zero JavaScript errors**. Two real defects came out of that pass and both
are closed: the sticky media dock that hid the page tail (row 50 - now `fixed` with its height
reserved, measured no-overlap) and the client-leaves-mid-answer 500 (row 51 - three socket errors
caught, one honest `[client-gone]` line, no traceback). A third was my own: the probe route crashed on
its first live call because its test only grepped the source (row 52) - replaced with a real route test.

**Verification.** `tests/test_errors_are_named.py` **7 passed**; route tests **9 passed**;
`refresh_manifests.py` (server.py, app.js) then `certify_build.py` -> **CERTIFIED BUILD** (7 modules
validated). Live measurements on the operator's own page: dock `position=fixed top=498 bottom=569`,
tail ending at `b=476` -> **no overlap**; four-way switch with no JS errors. The full suite was run
after the last edit and its result is recorded in the next entry. Nothing committed, pushed or sealed;
the USB kit tree was not touched.

**Still open.** L1 remembered backend verdicts never expire; L2 the checker's routes are kernel-side;
L3 two models need a newer engine build; L5 no local sound model; L6 cloud image parts unproven; L8 a
cold first turn is ~190s. The photo price is still uncalibrated (console priced a turn at 16,381
tokens where the engine counted 4,817), and `HANDOFF.md` §3's backend row is deliberately stale.


---

## 2026-09-21 · later the same day: the UI interface, the flashing, and the other test keys

Asked to make the Local/API switch and the interface "work cleanly", then to wire in a NVIDIA test key
for the ADMIN console only - and, if keys did not work, to disregard them and to try the Gemini one and
any test keys found on the system.

**What the keys actually did.** NVIDIA: the key answers, `GET /v1/models` -> 200 (81 ids), and the
account is answer-only on four of them - `nemotron-3-super-120b-a12b`, `nemotron-3-nano-omni`,
`nemotron-3.5-lightning`, `llama-3.2-11b-vision`. Everything else is listed but not enabled for it, and
it has worker rate limits (one `503 ResourceExhausted` mid-test). Gemini: the key in the DeepSeek vault
file answers in **both** shapes (native `generateContent` -> "GEMINI OK", and the OpenAI-compatible
route the kit uses -> 200). DeepSeek: already wired, key fine. Groq: the key is valid, but
`api.groq.com` answers plain urllib with **Cloudflare Error 1010**, and even with a browser
User-Agent + Accept the shipped model `openai/gpt-oss-20b` returns an **empty `content`** on a short ask
(its reasoning eats the token budget). Left unwired rather than put a model in the chain that answers
nothing.

**Wired.** `keys_wired: [deepseek, nvidia, gemini]`, chain DeepSeek -> NVIDIA NIM -> Google Gemini, the
operator's primary untouched (DeepSeek), cloud brain off, local engine the default. NVIDIA is also in
the page's provider dropdown, and a per-provider `body` field was added so a provider can turn
thinking off - measured necessary for the nemotron ids.

**The flashing.** The operator saw the console flashing erratically. Cause measured, not guessed: the
weather row was rebuilt with `innerHTML = ""` every second, the dock strip was blanked and refilled
every five, and **my own verification tabs** were multiplying the six polled endpoints (the log showed
`/api/health` x831 in one window). Fixed by reusing the city nodes (only the clock text ticks), swapping
the pane strip atomically instead of blanking it, halving the pane poll to 10s, and closing the
duplicate tabs. Verified: mutations 220/10s -> 98/12s, text-only, clock still ticking, 13 cards alive.

**Verification.** `tests/test_nvidia_provider.py` 6 passed; `tests/test_errors_are_named.py` 7 passed;
the two turn-shape files 16 passed with the cloud brain off; `refresh_manifests.py` (server.py, app.js,
index.html) then `certify_build.py` -> **CERTIFIED BUILD**. The full suite was **not** re-run after the
final edits - the last full run was 1020 passed / 9 failed, and those nine are the live-flag isolation
finding above, measured to pass 16/16 with the switch off. Nothing committed, pushed or sealed; the USB
kit tree was not touched.

**Unconfirmed, seen twice in screenshots:** at a mid-page scroll position, panel text appears to overlap
panel text (e.g. a search hint over a Mon-Fri boundary line). Two independent screenshots show it, but
measurement did not reproduce it - the probe strings were absent when I measured and the surviving pair
did not intersect. Not claimed as a defect; measure it the same way before fixing.

## 2026-09-21 (evening) - forever history, LYGO RAG, and four fixes found on the way

Built the console's conversation archive and the RAG that reads it, both asked for in the operator's own
words ("Conversations to flow unlimited", "even design a LYGO rage into it all"): `src/transcript_archive.py`
files every message to `workspace/memory/conversations/` on a background writer, once each, labelled, and
`src/lygo_rag.py` recalls the passages that match when the window had to drop history. Reader:
`scripts/read_history.py`. Pointer in `workspace/MEMORY.md`.

Found on the way, and fixed: the failover chain dropped the house default's key when the primary moved
(fresh-process proof: `keys_wired ['nvidia','deepseek']`); the suite inherited the operator's live cloud
switch (now pinned - 16 passed either way); Groq was judged a dead key when the budget was the problem.
Left open and reported: `chain_tried` is not cleared per walk, and the portable stick holds key material
that the kit's own rule says must not live there.

**My own mistakes, logged so the next pass does not repeat them.** (1) `_ensure()` returned `build()`'s
*stats* dict where an index was expected, so `stats()` read an int as a block list - the tests caught it,
the fix is to read the rebuilt file. (2) I patched `src/server.py` with `read_text`/`write_text`, which
normalises CRLF to LF, and my patterns then did not match the bytes on disk; worse, one patch hard-coded an
indentation and de-indented a nested `def live_ctx` out of its `except` block, leaving the file unable to
compile until I reverted that hunk by reading the exact bytes with `read_bytes().decode()`. The file is CRLF:
patch it with the newlines it actually has and write with `newline=""`. (3) I read "still no DeepSeek in the
chain" from a persistent interpreter that had imported `cloud_api` before the fix - a stale module, not a
result; a fresh process must be used to judge a change. (4) I stamped a completed turn with the configured
model rather than the provider that answered it - a label that lies is a defect, not cosmetic.

### The USB copy, brought to 1.3.0 (same day, same pass)

The steward: *"add the new updates to the USB version, test it and complete the update to the new version of
the USB also … we dont need to do the web portal yet"*. Backed the stick's 1.2.2 tree up first
(`.backups/stick-1.2.2-20260921`, 269 files), mirrored the synced surface — never its `config/`, its own
launchers, `engine/`, `python/`, `models/`, `save/`, `workspace/` — and tested it on its own tree: sweep
`0 failure(s)`, suite `1080 passed, 9 skipped`, a real local turn through the calc limb, and the turn filed in
the stick's own forever history. Two defects were found *by testing the stick* and fixed: the completion line
credited a cloud provider for a local answer, and five standing tests asserted PC-only invariants. The stick's
model store is empty — recorded as the steward's open decision, not papered over.

- **2026-09-22 — closing the 1.3.0 pass. Status: running, stable, tested.**
  The pass made the existing pipeline *answer* where it had been failing, rather than adding mechanism:
  `emit_sse` defined above its first use and one idempotent `_start_sse()` (both over-window and streaming
  paths), the engine window set to the 16,384 the identity block was sized for, `continuity._fits_total()`
  holding `PROMPT_CEILING_TOTAL` by construction, sampling defaults at one chokepoint, a COMPLEX TASKS +
  STYLE section in `prompts/LYGO_ALIGN.txt`, and `chat_loop.verify_output_claims()` — the fabrication
  detector for a claimed limb output, counted in `/api/health` as `fabrications_caught`.
  Defect ledger rows 113-119. Gauntlet: PC 9/12, USB 8/12 (T7/T11/T12 fail on both brains — mechanism, not
  model). Final pass: `verify_fixes_live` ALL PASS, 1247 tests green, both copies CERTIFIED.
  Evidence, settings and the carry-forward gaps: `docs/VERSION_CLOSEOUT_1.3.0_2026-09-22.md`.
