# Version closeout — `lygo_llm_console` 1.3.0 (2026-09-22)

**Written for the session that starts the NEXT version.** Every number here was measured on this box; the
command that re-derives it is beside it. The version string comes from this repo's own commit ("1.3.0: close
out the pass…") — there is no version constant in the code, so a closeout is the only place it is stated.

## 1. What this version is

| | PC copy | USB copy |
|---|---|---|
| root | `I:\E Drive\lygo-protocol-stack\lygo_llm_console` | `E:\LYGO_BUILDER_KEY\lygo_llm_console` |
| console port | 9641 | 9651 |
| engine port | 11441 | 11451 |
| launcher | `LYGO_LLM_CONSOLE.bat` | `LYGO_AGENT_STICK.bat` |
| brain | `qwen2.5-coder:7b` | `qwen2.5-coder:7b` |
| verify | `scripts/certify_build.py --quiet` → CERTIFIED |

- Suite: **1247 passed, 0 failed, 43 subtests** — `python -m pytest -q` (≈3:00).
- Both copies carry identical `src/`; only config keys meant to differ per copy do.

## 2. Settings locked this version (`config/console.json`, both copies)

`ctx_default 16384` · `ctx_max 16384` · `flash_attn on` (the shipped, tested default) · `kv_type q8_0` ·
`max_tokens 4096`

Sampling (one chokepoint: `paths.console_sampling()` read by `openai_proxy.for_local_engine()`, so all six
local payload sites agree): `temperature 0.25 · top_p 0.9 · top_k 40 · repeat_penalty 1.05 · min_p 0.05`.
A caller's explicit value always wins — that is what the `/v1` A/B below proves.

## 3. Measured behaviour

| measurement | value | how |
|---|---|---|
| coder speed | 42–49 tok/s | a turn's `done.perf` |
| VRAM at ctx 16384 | 5,275–6,155 of 8,188 MiB (≈2.0 GB free) | `nvidia-smi --query-gpu=memory.used,memory.total` |
| gauntlet, PC | **9/12** (T7, T11, T12) | `scripts/gauntlet_agent.py` |
| gauntlet, USB | **8/12** (T7, T9, T11, T12) | same, run from the stick's own directory |
| temperature A/B (4 reps, a prompt with freedom) | 0.25 → mean pairwise similarity **0.364**, 36 unique words; 0.9 → **0.202**, 86 | `/v1/chat/completions?token=…` with an explicit `temperature` |
| run-to-run spread | the same PC coder scored **7, then 10, then 9** across one day | quote the spread; never one number as progress |

T7, T11 and T12 fail on **both** brains and **both** copies, so they are console *mechanism* gaps, not model
weaknesses — no local model swap moves them.

## 4. What changed in this version (file level)

- `src/paths.py`, `src/openai_proxy.py` — sampling defaults at one chokepoint (`console_sampling`, merged in
  `for_local_engine`).
- `prompts/LYGO_ALIGN.txt` — a **COMPLEX TASKS** section (think the goal + limb order; batch independent
  reads; read each receipt; chain until the artifact exists and read it back; the host check outranks your
  own summary; answer a blocked task with the block) and a **STYLE** rule: the shape the operator asks for
  is a constraint ("one paragraph means ONE").
- `src/chat_loop.py` — `verify_output_claims()`: the fabrication detector for a *claimed limb output*.
- `src/server.py` — `emit_sse` moved above its first use; `_start_sse()` (idempotent) used by both streaming
  paths; `fabrications_caught` served in `/api/health`.
- `src/continuity.py` — `_fits_total()` holds `PROMPT_CEILING_TOTAL` by construction.
- `config/console.json` — ctx 8192 → **16384** (the window the identity block was sized for in the code's own
  comment) and `ctx_max` off 32768.
- `tests/test_fabrication_detector.py` — 8 cases for the detector.
- `docs/DEFECT_LEDGER.md` — rows 113–119.

## 5. Known gaps carried into the next version

1. **T7 conditional branch** (writes to the Desktop) fails on both brains/copies — console mechanism.
2. **T11 honest-failure grading** — the reply is honest and is still scored FAIL; needs a known-good and a
   known-bad sample per grader (the rule recorded in ledger 107, applied to T11/T12).
3. **T12 multi-file project** fails on both. Verify `wipe_scratch()` (ledger 106) still holds: a stale
   `mod_a.py` from an earlier run makes the score meaningless.
4. **T9 can pass with `limbs: []`** — in-head arithmetic is indistinguishable from a fabricated result; the
   detector only fires on a *claimed limb output*.
5. **The stick does not carry gemma4** (needs ≈7.4 GB, 3 GB free on the stick) — USB vision is capped by that.
6. **The stick's `prefer_ids` now carries the PC's coder-first list** (config sync side effect, ledger 119).
   It matches the operator's later instruction ("use the coder on both"); restore a gemma4-first list if a
   beefier host should run gemma4.
7. **The GPU driver reset is NOT proved fixed.** `LiveKernelEvent` (P1: 193) in the Application log with the
   engine log cut mid-task and no Python traceback is a display-driver reset. Lowering context did **not**
   stop the failures — it made them constant — so do not re-open that theory without evidence.
8. **The tree is uncommitted** (35 entries when this was written): this version is not sealed in git.

## 6. Verify this version in five minutes

1. `scripts/ensure_console.py --wait 240` → `/api/health` says `brain == "ready"`. Never send a turn while it
   still says `booting`: that answers HTTP 500 and looks like a broken console.
2. Three turns: a greeting, a `list_dir` question, a read→write chain. Expect traces `[]`, `[list_dir]`,
   `[read_file, save_note]`.
3. `python -m pytest -q` → 1247 passed.
4. `scripts/certify_build.py --quiet` → CERTIFIED on both copies.
5. `scripts/gauntlet_agent.py` → expect 8–10/12; read the traces, not only the score.

## 7. Gotchas for the next builder

- Keep the SSE helpers (`emit_sse`, `_start_sse`) **above** every branch that emits (ledger 113/114).
- Any branch that streams must send headers before it writes (ledger 114).
- The identity block is ≈4.4k tokens. Do not set the engine window below ≈12k, whatever the card (ledger 115).
- `flash_attn` is a tested default — `test_adaptive_perf` asserts it (ledger 117).
- Sync `scripts/` and `tests/` with `src/`: a stale `certify_build.py` on the stick cold-booted its console.
- Config copies carry per-copy keys with them (ledger 119).


---

## STATUS — running, stable, tested (2026-09-22)

Logged on the operator's instruction, after one final debug pass. All gates green on the PC copy; the USB
copy carries the same `src/` and its own certified tree.

| gate | command | result |
|---|---|---|
| backends | `python src/backends.py status` | `active=cuda`, installed `[cuda, cuda-b10988, vulkan]`, overlays `[vulkan]` — the documented expectation |
| live scenarios | `python scripts/verify_fixes_live.py --port 9641` | **RESULT: ALL PASS** — 4/4 (provider switch took effect; nvidia answered after a bare switch; a bad model was reported, not swallowed; the answer carried no readout) |
| suite | `python -m pytest -q` | **1247 passed, 0 failed**, 43 subtests (3:55) |
| certify | `python scripts/certify_build.py` | **CERTIFIED BUILD** on both copies |
| live turn | `/api/chat` → *"List the files in your workspace notes folder."* | 200, traces `['list_dir']`, 44.9 tok/s, correct listing |
| console state | `/api/health` | PC 9641 `ready` / `qwen2.5-coder:7b` / `max_tokens 4096` / `fabrications_caught 0`; USB 9651 stopped |

**What "stable" means here, precisely:** every gate above green, both copies certified, no crash during the
final pass. It does **not** mean the intermittent GPU driver reset (gap 7 in §5) is proved gone, and it does
not mean the gauntlet's T7/T11/T12 mechanism gaps are closed — those are the next version's work.
