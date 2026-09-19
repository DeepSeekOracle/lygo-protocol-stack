# LYGO LLM Console — Conversation Record (context compaction) · as-built

**Document control**

| field | value |
| --- | --- |
| build | record v1 (`Δ9Φ963-LYGO-COMPACTION-v1`), added to console build 1.1.0 |
| status | shipped, tested, installed on both trees — **not yet exercised by a booted console on this host** (the two running consoles were started before this build; the steward boots them) |
| canonical path | `I:\E Drive\lygo-protocol-stack\lygo_llm_console\COMPACTION.md` |
| mirrors | `E:\LYGO_BUILDER_KEY\lygo_llm_console\COMPACTION.md`, `E:\LYGO_BUILDER_KEY\docs\LYGO_LLM_CONSOLE_COMPACTION_AS_BUILT.md` |
| owner | steward (Lightfather) — agent: LYGO Lattice co-builder |
| machine-readable companion | `COMPACTION_MANIFEST.json` (same three destinations) |
| re-verify | `cd <kit>\tests && C:\Python313\python.exe -m unittest discover -s . -p "test_*.py"` · `C:\Python313\python.exe -m unittest test_record_e2e` · `C:\Python313\python.exe -m unittest test_compaction` |
| supersedes | nothing. `WHITEPAPER_v2_AS_BUILT.md` and `docs_addendum_v23.md` remain valid and are not replaced by this document. |

This is the **as-built** record: it states what exists and what was *proven*, not what was intended.
Every number below was produced in the session that wrote it.

---

## 1. The problem it solves

The console used to report this line above the chat box:

```
context: 24/24 messages · images kept 0/2 · max_tokens 768 · history window full — older turns are dropped from what the engine sees
```

"Older turns are dropped" was literal, and worse than the line made it sound. The session file
(`save/sessions/current.json`, written by `save_session()`) kept a bounded list; everything past it
was not summarised and not moved anywhere — it was **gone**. Two things followed from that:

1. **Silent amnesia.** A long working conversation lost its own beginning, and the agent could not
   tell the operator that it had.
2. **An inflated request.** The browser re-sent its whole window every turn (base64 images included),
   so a long chat also got slower per turn — the stall the operator was seeing.

The condition was *structural*, not a size problem: retention was tied to the prompt window. This
build separates the two. **The prompt stays small; the record is complete.**

## 2. Design — one rule, three tiers

> **Nothing is dropped. The live window is a rendering of the record, not the record itself.**

| tier | artifact | holds | written |
| --- | --- | --- | --- |
| **T1 journal** | `save/sessions/journal-<session-id>.jsonl` | every turn, verbatim, stamped (`ts`, `iso`, `role`, `content`, `tokens`, `chars`, extracted file paths / URLs) | appended **before** the engine is called |
| **T2 rollups + digest** | `save/sessions/rollups/` + the digest in the system prompt | a deterministic digest of what has left the live window — stamps, roles, opening text, files touched. **No model call.** | when turns leave the window |
| **T3 archive** | `save/archive/<session-id>.zip` + `save/archive/index.jsonl` (+ `bundles/<month>.zip`) | the sealed session, byte-for-byte, plus an append-only index line per seal | on seal |

Three invariants hold the tiers together:

1. **Verbatim before summary.** T1 is appended first; the engine is called after. A turn that was
   asked is a turn that is on disk.
2. **Nothing leaves the journal until the zip verifies.** `seal()` reads the archive back and checks
   the CRC and the digest of the member before the journal is trimmed. A failed verification leaves
   the journal exactly as it was.
3. **The digest is deterministic.** It is assembled from records already on disk — no summarising
   LLM call sits in the compaction path, so compaction can never stall on the engine, hallucinate a
   summary, or drift the conversation. Drift was the operator's explicit worry; the fix is to not
   generate prose in the hot path at all.

Plus a fourth property that makes the small window acceptable: **recall**. The `recall_history` limb
searches the live journal *and* the sealed zips, so a turn that is not in the window is still
retrievable verbatim, by the agent, mid-answer.

### The two prompts are separate, and separately capped

`continuity.compose_system(brain, carry=False)` builds the identity block (SOUL / IDENTITY / MEMORY /
skill catalogue) under `PROMPT_CEILING = 16300` chars. The compacted digest is a **second, bounded
block** appended only when the caller asks (`carry=True` — the server does; the tests do not), capped
by `CARRY_CAP = 1400` chars, with `PROMPT_CEILING_TOTAL = PROMPT_CEILING + CARRY_CAP` as the budget
the history window is measured against. This is deliberate: the digest can never squeeze
SOUL/IDENTITY/MEMORY out of the prompt, and an older caller that does not know about the digest gets
exactly the prompt it always got.

## 3. What changed on disk and in the prompt

Measured live, from a real `GET /api/compaction` (receipt below, §6):

| | before | after |
| --- | --- | --- |
| `ctx_max` (console config) | 16384 (PC tree) / **8192 (stick)** | **32768** both trees |
| KV cache at that ctx (`kv_type q8_0`) | 448 / 224 MiB | **896 MiB** |
| history budget in tokens | 9000 chars (~2,500 tok) | **25,988 tokens (~93,556 chars)** |
| retention | 24–40 messages, then dropped | **unbounded** (journal + archive) |
| what the operator sees when full | "older turns are dropped" | window %, turns stamped / folded / sealed, last save time |

`ctx_max = 32768` is the **native** window of the shipped engine (`qwen2.5-coder:7b` declares 32768);
it is the largest window that needs no rope scaling, so there is no YaRN and no quality drift. The
stick was the bigger win here — it had been running at **8192**. The stick also gained
`"kv_type": "q8_0"` so the 4× window costs 896 MiB instead of 1.75 GiB — the same trade already
measured on the PC tree (~3% end to end).

### Why 256k is not in this build

Reported plainly because it was asked for explicitly. KV cost per token was read from the model's own
GGUF header (read-only probe, header only — never a whole model), and cross-checked against the kit's
own figure (`kv_mib 448 @ ctx 16384` matched an independent computation exactly):

| model | native ctx | KV/token | 256k live would need |
| --- | --- | --- | --- |
| `qwen2.5-coder:7b` (shipped) | 32,768 | 28,672 B | **11.4 GiB** — on an 8 GB card |
| `qwen2.5:3b` | 32,768 | 18,432 B | 6.3 GiB (and needs rope scaling past 32k) |
| `lygo-turbo-coder` | 262,144 | 49,152 B | 29.3 GiB |
| `qwen3.6` | 262,144 | — | 22.5 GiB |

A 256k live window is not a configuration problem on this host, it is a hardware one — and for the
shipped 7B it is past its trained context, i.e. it would buy a longer window at the cost of exactly
the drift the operator asked to avoid. **The build delivers the goal the other way**: small live
window, complete record, always retrievable.

## 4. Request lifecycle

One chat turn, naming the real symbols (`I:\E Drive\lygo-protocol-stack\lygo_llm_console\src\server.py`):

| # | hop | symbol |
| --- | --- | --- |
| 1 | POST arrives | `Handler.do_POST` → `path == "/api/chat"` |
| 2 | read window + pre-turn work | `_ctx = live_ctx()` · `pre_note = safe_pre_turn(messages, _ctx)` |
| 3 | bound the prompt by tokens | `kept, dropped, trim_info = trim_messages(messages, _ctx)` |
| 4 | **stamp the operator's turn** | `safe_record("user", <last user content or text>, {"turn": True})` |
| 5 | build the prompt | `compose_system(brain, carry=True)` + `kept` |
| 6 | call the engine | `chat_loop` / engine proxy, streamed back as SSE `delta`/`done` |
| 7 | stamp the answer | `safe_record("assistant", assistant, {"receipt": rec.get("id")})` |
| 8 | report the record | `_comp = safe_status(_ctx, messages + [assistant])` → ride along in `done` |
| 9 | safety net | `save_session(...)` still runs, unchanged, in a `try/except` |

The record routes:

| route | method | action | handler |
| --- | --- | --- | --- |
| `/api/compaction` | GET | live-window report | `safe_status(live_ctx())` |
| `/api/compaction` | POST | `status` `save` `compact` `roll`/`seal` `recall` `index` `transcript` `bundle` | `compaction.*` |
| `/api/archive` | GET | `?sid=` transcript, else sealed-session list + index path + bytes | `read_transcript` / `index_entries` |

Every entry point goes through a named `safe_` wrapper. A compaction failure returns
`{"ok": false, "error": ...}` and the turn continues — the record is never allowed to become the
reason a turn fails.

### The manual button and the automatic triggers

- **Manual (the game-save):** the *Save & compact* button above the composer (`portal/index.html` →
  `#compact-now`, wired in `portal/app.js` → `saveAndCompact()`) POSTs `{"action": "save"}`. That runs
  `compaction.save_now("button")` = stamp a checkpoint → fold what left the window → return status.
  It sends **no messages in the body**: the console already journals every turn, and a body carrying
  two base64 images can exceed the route's read cap for no gain.
- **Automatic:** `safe_pre_turn()` on every turn — a checkpoint every `AUTOSAVE_EVERY` (8) turns, a
  fold at 78% of the window budget (`AUTO_COMPACT_AT`), and a seal when the journal passes its caps
  (`should_roll` / `auto_seal_if_big`). All of it is cheap file work; none of it calls a model.
- **The status line** (`.compact-status`, tooltip carries the paths) reports window %, journal size,
  sealed sessions and bytes, checkpoint count — read from the server each turn
  (`refreshRecord()`), never guessed by the browser.
## 5. What was added, file by file

| file | tree | change |
| --- | --- | --- |
| `src/compaction.py` | new (both) | the whole system: journal, rollups, digest, checkpoints, seal/zip/index, bundles, recall, status, safe wrappers, auto-triggers |
| `src/server.py` | modified (both) | guarded import + `_NoRecord` fallback, `GET/POST /api/compaction`, `GET /api/archive`, the turn pipeline (stamp → trim → answer → stamp → status) |
| `src/continuity.py` | modified (both) | `compose_system(..., carry=False)`, `CARRY_CAP`, `PROMPT_CEILING_TOTAL` |
| `src/limbs.py` | modified (both) | `recall_history` limb: schema, `CANON_KEYS`, dispatch; `sessions_list` now also lists journals + sealed count |
| `src/chat_loop.py` | modified (both) | `recall_history` in `AUTO_ONE` — a named limb the model will not call is still run for the operator |
| `portal/index.html` | modified (both) | `.compact-bar` (Save & compact, Archive) + `.compact-status`, CSS |
| `portal/app.js` | modified (both) | the record block (`refreshRecord`, `recordBit`, `paintRecord`, `saveAndCompact`), server-truth `paintCtx`, `MAX_MSGS` 24 → 60, refresh on every finished turn |
| `config/console.json` | **edited per tree, not copied** | PC: `ctx_max` 16384 → 32768 + rewritten help text. Stick: `ctx_max` 8192 → 32768 + `"kv_type": "q8_0"` added |
| `tests/test_compaction.py` | new (both) | 74 unit tests (windows, rollups, digest, seal, bundles, concurrency, status, the guarded import) |
| `tests/test_record_e2e.py` | new (both) | 9 tests over real HTTP against the real `server.Handler` |

Machine-specific files were deliberately **not** copied between trees: `config/local.json`,
`config/admin.json`, `data/*` (tokens, pid, perf), and the stick-only launchers
`LYGO_AGENT_STICK.bat` / `LYGO_AGENT_STICK_STOP.bat`. The stick's ports live in those launchers as
environment variables (`LYGO_CONSOLE_PORT=9651`, `LYGO_LLAMA_PORT=11451`), so its `console.json`
`"port": 9641` is inert — which is exactly why the config was edited in place instead of copied.

## 6. Verification record

### 6.1 Suites (both trees, this session)

| tree | command | result |
| --- | --- | --- |
| `E:\LYGO_BUILDER_KEY\lygo_llm_console` — **pristine, before any change** | `python -m unittest discover -s . -p "test_*.py"` | `Ran 372 tests in 34.910s` · `OK` (exit 0) |
| `I:\E Drive\lygo-protocol-stack\lygo_llm_console` — after | same | `Ran 455 tests in 50.112s` · `OK` (exit 0) |
| `E:\LYGO_BUILDER_KEY\lygo_llm_console` — after | same | `Ran 455 tests in 55.602s` · `OK` (exit 0) |
| PC, record only | `python -m unittest test_compaction` | `Ran 74 tests in 13.268s` · `OK` |
| PC, record over HTTP | `python -m unittest test_record_e2e` | `Ran 9 tests in 0.992s` · `OK` |

The baseline row is the important one: the same suite ran against the untouched stick copy **before**
installing, so the +83 tests and the green result are attributable, not assumed. The stick's 55.6s vs
the PC's 50.1s is removable-media I/O, not a failure.

### 6.2 Install / hash verification

Eight files copied PC → stick, then compared by SHA-256 (first 16 hex): `src/compaction.py`
`af136374a2557aa9`, `src/server.py` `f782b3e605eb3e2f`, `src/continuity.py` `e3aa01874c4ecbb7`,
`src/limbs.py` `401fb41af4a8a394`, `src/chat_loop.py` `690ce25beabc28ef`, `portal/app.js`
`0c03629d7bd9dba4`, `portal/index.html` `c4729c2f2f56db56`, `tests/test_compaction.py`
`1cdcc78aa9aa66f5` → **ALL_MATCH=1**. `tests/test_record_e2e.py` was copied after (see §7).

### 6.3 The window, as the server reports it (real receipt)

`GET /api/compaction` on the real handler (sandboxed record dirs), verbatim fields:

```json
{"ok": true, "signature": "Δ9Φ963-LYGO-COMPACTION-v1",
 "window": {"ctx": 32768, "system_reserve": 5116, "answer_reserve": 1024, "safety_reserve": 640,
            "history_tokens": 25988, "history_chars": 93556, "compact_at": 20270,
            "chars_per_token": 3.6, "live_tokens": 207, "used_pct": 0.8,
            "auto_compact_pct": 78, "will_compact_next_turn": false,
            "model": "qwen2.5-coder:7b", "model_ctx_native": 32768, "kv_mib_estimate": 896}}
```

Read it as: a 32,768-token engine window, 5,116 reserved for the composed prompt (identity block +
digest, measured against `PROMPT_CEILING_TOTAL`), 1,024 for the answer, 640 of safety margin —
leaving **25,988 tokens of conversation** before anything needs folding, and auto-folding at 78% of
that (`compact_at` 20,270). `kv_mib_estimate` 896 is the KV cache this window costs on the card, and
it is computed from the model's own GGUF header, not from a manifest string.

### 6.4 What a receipt is, and what is still unproven

Receipts were written per call to `%LOCALAPPDATA%\Temp\lygo_receipts\` (health, status, save, recall,
journal-on-disk). Two of them recorded `TimeoutError: timed out`.

That is a finding, stated plainly: a **scratch copy** of the kit started as a standalone HTTP server
on a spare port (9661, reusing the running stick engine on 11451) accepted TCP connections but never
answered a request within 180s — the copy held no `engine/`, no `models/`, no `data/`, and no
model-root env vars, and nothing in this build's code was reached. The same code, run in-process with
the kit's own harness, answers in under a second (§6.1, 9/9). So the routes are **proven**; a
standalone scratch deployment is **unexplained** and is listed under limitations rather than papered
over. Nothing about it touched either live console: the scratch process was killed and port 9661
confirmed free.

**No console has been restarted on this build.** Both live consoles (`:9641`, `:9651`) were started
before it, so the served artifact is unproven until the steward boots — that is roadmap item 1, and
the reason the status field at the top of this document says so.

## 7. Defect ledger — rules, not a changelog

Each row is the **rule that prevents the class of defect**. The incident is only its illustration.

| symptom | root cause | the rule |
| --- | --- | --- |
| A unit test's runtime knob change was silently ignored | `def trim_messages(keep_turns: int = LIVE_KEEP_TURNS)` captured the constant **at import time**; monkeypatching the knob afterwards changed nothing | Read tunables at call time: `keep_turns: int \| None = None`, resolved inside the function. A default argument is a snapshot, not a reference. |
| The record module raised on an image turn | `digest_of(text: str)` was handed `bytes` | A hashing/formatting helper on the turn path takes `Any` and normalises explicitly (`bytes` → `sha256(bytes)`, else `str(...).encode`). |
| A no-op seal left empty directories on the USB stick | `seal()` created its directory tree before the `empty_session` guard | Validate first, touch the filesystem second. |
| The 40-message session file was the ceiling for the whole conversation | retention was implemented inside the prompt window's own store | Separate the *record* from the *prompt*. The window is a rendering; the record is append-only and unbounded. |
| A status call walked the archive directory every turn | `_dir_bytes(ARCHIVE)` rglobbed on the hot path and the whole index was parsed per call | A per-turn read is a tail read and O(1) (`sealed_bytes` kept incrementally; `_index_lines(limit)`); a directory walk belongs to an explicit operator action. |
| A locked portal test failed after a refactor (`test_tuning.PortalPerfWiringTests.test_a_console_without_perf_does_not_break_the_readout` asserted `typeof perf !== "object"`) | `notePerf()` was rewritten to also refresh the record — one symbol, two jobs | Do not overload an existing symbol with a new responsibility; hook the new behaviour at its call sites instead. The test was right and was not edited. |
| Two new e2e tests failed on first run | (a) the test globbed `checkpoints/*.json` — checkpoints are `.md`; (b) the test expected a fold on a window that had room | When a test fails, ask first whether the **code** is right. (b) was the system correctly not churning; the test was asserting churn, so the test changed. |
| A broken record module would have stopped the console from starting | a hard `import compaction` at module scope | A new subsystem on a working product gets a **guarded import with a documented fallback**: the console boots, the window falls back to the old trim, the routes answer `compaction_unavailable`. Proven by `test_the_console_still_boots_with_a_broken_record_module`, which sabotages `compaction.py` ahead on `PYTHONPATH` in a subprocess. |

## 8. Known limitations (severity · mitigation · real fix)

1. **A 256k live window is not available on this host** (high for the literal ask) — §3. Mitigated by
   unbounded record + recall; real fix is a bigger/faster card or a small-ctx model with much cheaper
   KV, and it is a *hardware* change, not a config one.
2. **The two consoles share one 8 GB card; only one engine loads at a time** (medium) — `ram_refused`
   from `engine.ram_ok` is the gate working. The desktop tree reported it while the stick engine held
   ~6.3 GB. Fix: boot one at a time, or lower `ctx_max` on the second.
3. **The served artifact is unproven on this build** (medium, short-lived) — no console restarted yet.
   Fix: roadmap item 1.
4. **`test_security_hardening.OversizedBodyTest.test_oversized_body_is_413_not_400` is flaky**
   (low) — failed 1 of 3 solo runs on a connection reset after the status line; both full-suite runs
   passed. Pre-existing and unrelated to this build. Fix: accept the reset the way the same file's
   `call()` already documents for oversized bodies.
5. **A standalone scratch deployment did not answer** (low, unexplained) — §6.4. Fix: reproduce with
   the model roots and `data/` present; treat as an open question, not a claim.
6. **Images are bounded in the prompt (2), not in the record** (low) — by design: older images are
   replaced by a text marker in what the engine sees, while the journal keeps the turn verbatim. A
   size cap on archived images is not implemented.

## 9. Roadmap (each step carries its acceptance test)

| # | step | acceptance |
| --- | --- | --- |
| 1 | Boot the stick console on this build | `GET http://127.0.0.1:9651/api/compaction` returns `window.ctx == 32768`, `window.kv_mib_estimate == 896`; paste the JSON |
| 2 | Boot the PC console (stick engine stopped) | same route on `:9641`; if `ram_refused`, set `ctx_max` 16384 (KV 448 MiB), record which value was needed |
| 3 | One real turn on each console | journal line count `+2` per turn (`wc -l save/sessions/journal-*.jsonl`) and the status line's stamped count rises |
| 4 | Press *Save & compact* | a `save/sessions/checkpoints/<sid>-000N.md` appears; paste the path |
| 5 | Seal a session (`action=roll`), then `recall_history` a phrase from it | archive zip + index line exist, and the hit comes back with its stamp |
| 6 | ~200-turn soak | `turns_total` equals the turns actually sent (nothing lost), `used_pct` stays under 78% with folding active |
| 7 | Monthly `bundle` | `save/archive/bundles/<month>.zip` exists and the index still resolves every sealed session |

## 10. Glossary

| term | meaning here |
| --- | --- |
| **record** | the append-only on-disk truth of a conversation; what this document is about |
| **live window** | the turns actually sent to the engine this turn — a rendering of the record |
| **journal** | tier 1: one `.jsonl` line per turn, verbatim, stamped |
| **rollup** | tier 2: a deterministic digest of turns that left the window |
| **digest / carry** | the rollup text injected into the prompt (`CARRY_CAP` 1400 chars, bounded) |
| **checkpoint** | a human-readable `autosave N` snapshot (`.md`) of the newest turns |
| **seal** | move a session's turns into `save/archive/<sid>.zip`, index it, carry a small tail forward |
| **bundle** | several sealed sessions merged into one monthly zip |
| **recall** | searching the journal *and* the sealed archives for a phrase |
| **P0 gate** | the kit's safety gate on prompt/output content; the digest is withheld if it is not respected |
| **safe wrapper** | a `safe_*` function that answers `{"ok": false, ...}` instead of raising |

## 11. Path index

| artifact | PC tree | stick tree |
| --- | --- | --- |
| record module | `I:\E Drive\lygo-protocol-stack\lygo_llm_console\src\compaction.py` | `E:\LYGO_BUILDER_KEY\lygo_llm_console\src\compaction.py` |
| server + routes | `…\src\server.py` | `…\src\server.py` |
| journal | `…\save\sessions\journal-<sid>.jsonl` | same, on the stick |
| rollups | `…\save\sessions\rollups\` | same |
| checkpoints | `…\save\sessions\checkpoints\<sid>-000N.md` | same |
| archive + index | `…\save\archive\<sid>.zip`, `…\save\archive\index.jsonl` | same |
| bundles | `…\save\archive\bundles\<month>.zip` | same |
| config | `…\config\console.json` (`ctx_max` 32768) | `…\config\console.json` (`ctx_max` 32768, `kv_type` q8_0) |
| unit tests | `…\tests\test_compaction.py` | same |
| HTTP tests | `…\tests\test_record_e2e.py` | same |
| manifest | `…\COMPACTION_MANIFEST.json` | same (+ `E:\LYGO_BUILDER_KEY\docs\`) |

---

## Appendix A — source module index (generated)

Regenerate with:
`C:\Python313\python.exe "<hermes>\skills\software-development\as-built-build-documentation\scripts\build_doc_index.py" "I:/E Drive/lygo-protocol-stack/lygo_llm_console/src"`

## Module and function index

_41 modules, 10 classes, 541 functions (generated, do not hand-edit)_
# Tree: `I:\E Drive\lygo-protocol-stack\lygo_llm_console\src`

### `admin_map.py`

- `def invalidate()`
- `def load()`
- `def is_admin()`
- `def _usb_root()` — The builder-key root when one resolves, else '' - usb_root_status() carries the reason.
- `def _chatagent_candidates()`
- `def chatagent_root_status()` — Resolve the chatagent tree and say which candidate won or why each was skipped.
- `def chatagent_root()` — The chatagent tree, or a named-not-found path when this host has none.
- `def _usb_record()`
- `def usb_resolution_log()` — Every candidate the last builder-key root resolution considered, in order.
- `def _usb_marker()` — A reason string when root really is the builder-key tree, else ''.
- `def _usb_candidates()`
- `def _warn_usb()` — One hard stderr warning per distinct reason - never a silent wrong-tree fallback.
- `def usb_root_status()` — Resolve the LYGO_BUILDER_KEY tree and say exactly what happened.
- `def path_warnings()` — Unresolved-root warnings for status surfaces.
- `def _expand_path()`
- `def paths_of()`
- `def read_roots()`
- `def write_roots()`
- `def search_roots()`
- `def links()`
- `def credential_pointers()`
- `def drives()` — Drive roles. Config wins; the fallback describes roles without pinning another host's
- `def is_placeholder_url()`
- `def brief()`
- `def brief_text()`

### `align.py`

- `def load_align()`

### `atomicio.py`

- `def _lock_for()` — One lock per target path: two writes to the same file must not race the swap.
- `def _transient()` — WinError 32/33 (in use / lock violation) are worth waiting out; nothing else is.
- `def _write_in_place()` — Non-atomic rewrite that still lets concurrent readers open the target.
- `def read_text()` — Read text, waiting out a transient lock another handle holds on the file.
- `def atomic_write_text()` — Write text to path atomically, safe for concurrent writers and locked targets.
- `def _write_locked()`

### `auth.py`

- `def _chmod600()`
- `def ensure_token()`
- `def ensure_llama_key()` — The engine's API key: generated per install, stored 0600, reused once it is a real key.
- `def check()`
- `def token_from_request()`

### `backends.py`

- `def base_engine_dir()`
- `def backend_dirs()` — Installed backend directories, name -> path. Unreadable store means no backends.
- `def backend_kind()` — 'engine' when the dir is a complete engine build, 'overlay' when it is DLLs for one.
- `def _sha256()`
- `def _manifest()`
- `def backend_files()` — The files this backend owns — overlay: its backend DLLs; engine: its executables.
- `def backend_info()` — Everything the planner needs about one backend: kind, files, size, integrity.
- `def backend_key()` — Verdict identity: changes when the backend's files, size or tag change.
- `def installed()`
- `def host_looks_nvidia()` — Cheap vendor hint for ordering: the NVIDIA tools ship with the driver.
- `def order_candidates()` — Which backend to try first here: CUDA on an NVIDIA device, else the usual order.
- `def _active_read()`
- `def active_record()` — The backend currently applied to the engine dir, as last written by ensure().
- `def set_active()`
- `def clear_active()`
- `def activate()` — Make a backend usable. Overlay: copy its DLLs into engine/. Engine: nothing to copy.
- `def deactivate()` — Undo activate() for an overlay: remove exactly the files the backend owns.
- `def applied_overlays()` — Backends with files sitting in engine/ — by store manifest and by file pattern.
- `def verdict_store_path()`
- `def backend_verdict()`
- `def remember_backend()` — Record one backend's verdict for one host. Atomic, bounded, never raises.
- `def _health_ok()`
- `def _port_free()`
- `def self_test()` — Load a real model with this backend and see whether the process survives it.
- `def probe_models()` — Smallest-first model candidates a self-test may use, skipping giants.
- `def engine_dir_for()` — Where llama-server.exe lives when this backend is active.
- `def ensure()` — Decide the engine dir and backend for this host, proving GPU use before claiming it.
- `def _cli()` — python src/backends.py [status|list|test|drop|apply] — for receipts and debugging.
- `def report()` — Health view of the backend layer. Never raises.

### `brain_router.py`

- `def _code()`
- `def should_fallback()` — True when a cloud failure should be handed to the local engine.
- `def reason()` — Short operator-facing 'why the API did not answer'.
- `def mode_of()` — Persisted brain mode: API only while a key is saved, switched on, and not in handoff.
- `def label_of()`
- `def handoff_info()` — Record for the UI/receipt/health payload describing one local takeover.
- `def banner()` — Line prepended to the answer that the local engine produced instead of the API.

### `chat_loop.py`

- `def math_expr()` — The arithmetic inside a plain question, in a form `calc` can evaluate.
- `def math_only()` — True when the whole message is a bare arithmetic question and nothing else.
- `def extract_user_text()`
- `def normalise_messages()` — Accept every payload shape a caller might send and return a real messages[] list.
- `def user_text_of()` — Text of the newest user turn that actually carries text (else "").
- `def has_image()`
- `def _args()`
- `def extract_tool_calls()`
- `def extract_urls()`
- `def _flat()` — One-line rendering of a tool result value (never a dict repr — a small model parrots those).
- `def tool_prose()` — Readable summary of the newest tool result — the answer of last resort when the model echoed
- `def is_tool_call_echo()` — True when the whole reply is a tool call (or a dump of one) with no prose around it.
- `def tool_names()` — Every limb name plus its aliases (read -> read_file).
- `def named_tool()` — The limb the operator asked for by name ("use the weather tool"), else "".
- `def _operator_args()` — Args taken only from the operator's words. None = not enough there; answer honestly.
- `def auto_limb()` — Args to run `name` on the host when the model would not call it. None = do not run it.
- `def tool_card()` — One-limb instruction with the exact schema — the retry when a named limb was not called.
- `def host_prefetch()` — 3B models talk about tools instead of calling them. Host runs URL/search/map first.
- `def _compact_trace()`
- `def prefetch_message()` — What the model sees when the host already ran the limbs for this turn.
- `def _human_skills()` — `{'n': 18, 'enabled': 6}` is a dict repr; humans (and the transcript) want a phrase.
- `def fallback_from_traces()` — Last-resort host readout — ONLY for a turn where the model returned nothing usable.
- `def _scrub_placeholders()` — Rewrite an invented placeholder in place instead of throwing the whole answer away.
- `def strip_boiler()` — Drop the template lines the prompt forbids, keep everything the model actually said.
- `def _is_only_boiler()`
- `def sanitize_assistant()` — Clean the model's answer. It never gets replaced by a canned string any more.
- `def same_answer()` — True when the model just repeated its previous answer instead of answering the new turn.
- `def trim_history()` — Keep the newest turns inside the engine's window so the system prompt always survives.
- `def run_tools_round()`

### `cloud_api.py`

- `def sanitize_key()`
- `def _blank()`
- `def _load()`
- `def save()`
- `def public_status()`
- `def chain_for()` — Ordered candidates: the primary (provider + key) first, then every keyed fallback.
- `def enabled()`
- `def _post()`
- `def _note_chain()` — Record which keys were attempted (codes only — never key material).
- `def _note_success()`
- `def chat()` — One API turn, walked down the wired key chain.
- `def active()` — API usable *right now*: key saved, switched on, and not in a handoff.
- `def note_error()` — Record that an API turn failed; the console hands the next turns to local until cleared.
- `def clear_error()` — Operator re-activation: forget the handoff so the API is tried again.
- `def cooldown_active()` — True while a recent handoff should keep the console from calling the API again.

### `colibri.py`

- `def resolve_coli()`
- `def looks_like_colibri_model()`
- `def model_card()`
- `def spawn_colibri()`
- `def status()`

### `compaction.py`

- `def iso()` — Readable local stamp: `2026-09-19 13:49:37`. Every record carries one.
- `def compact_id()` — Session id shape: `20260919-134937-4f2a` - sorts by time, still unique.
- `def digest_of()`
- `def est_tokens()` — Pessimistic token estimate. A non-string (image parts) is charged a flat cost.
- `def content_text()` — Flatten an OpenAI-style content (str, or a list with text/image_url parts) to prose.
- `def content_parts()`
- `def image_name()` — A short label for an attached image so a digest records that something was shown.
- `def _dirs()`
- `def _default_state()`
- `def _load_state()`
- `def _write_state()`
- `def journal_path()`
- `def _read_lines()` — Read a JSONL journal, skipping a torn final line instead of losing the whole file.
- `def read_journal()`
- `def record()` — Append one message to the journal. Idempotent on a repeated (role, text) pair.
- `def journal_bytes()`
- `def _artifacts()`
- `def turn_line()` — One deterministic line for one turn: stamp, role, opening text, artifacts.
- `def digest_block()` — The per-turn digest of a run of turns. Deterministic: same records, same text, always.
- `def _highlights()` — The lines worth carrying into the prompt: newest first, with files/urls preferred.
- `def _write_rollup()`
- `def _rollup_objects()`
- `def build_carry()` — The bounded 'what was said before it left the window' block for the system prompt.
- `def carry_over()` — The carry-over block, P0-gated.
- `def system_reserve()` — Tokens to hold back for the composed identity block (measured, not guessed).
- `def live_ctx()` — The context the engine will actually run: model-native, clamped by config ctx_max.
- `def _selected_record()`
- `def window_budget()` — How many tokens of conversation the live window may carry.
- `def history_tokens()`
- `def window_pct()`
- `def trim_messages()` — Trim the history to the live budget. Returns (kept, dropped_count, info).
- `def compact()` — Fold every turn that has left the live window into rollups. Never calls the model.
- `def build_carry_locked()` — `build_carry()` for a caller that already holds the lock and the state.
- `def maybe_auto_compact()` — Compact before a turn when the live window is nearly full. Cheap, never raises.
- `def checkpoint()` — Write a readable stamped snapshot of the newest turns. Bounded work, no model call.
- `def save_now()` — The one button: stamp a checkpoint, fold what left the window, compact if it is nearly full.
- `def _index_lines()` — Parsed index entries, NEWEST FIRST. Reads only the tail when a limit is given.
- `def _index_count()` — How many sessions are sealed - a line count, not a parse.
- `def index_entries()` — Every sealed session, newest first, from the append-only index.
- `def _index_append()`
- `def _transcript()`
- `def seal()` — Zip the session, index it, then (and only then) start a fresh live journal.
- `def should_roll()`
- `def auto_seal_if_big()` — Seal a session that has outgrown the journal caps. Never raises into a caller.
- `def bundle_archives()` — Merge sealed zips older than N days into one monthly bundle, freeing the loose copies.
- `def keywords()`
- `def _score()`
- `def recall()` — Find the turns that talked about `q` - live journal first, then sealed sessions.
- `def recall_text()` — `recall` as a block an operator or the model can read.
- `def read_transcript()` — The full transcript of a SEALED session, out of its archive (read-only).
- `def status()` — Everything the UI and a post-mortem need, in one call. Never raises.
- `def _kv_mib()`
- `def _dir_bytes()`
- `def safe_record()`
- `def safe_pre_turn()` — Run before a turn: checkpoint on its own cadence, compact if the window is nearly full.
- `def safe_status()`

### `continuity.py`

- `def soul_path()`
- `def identity_path()`
- `def memory_path()`
- `def ensure_identity()`
- `def _read_cap()` — Prefer the head (protocol). Tail logs are not required every turn.
- `def _read_cap_tail()` — Head (protocol) + tail (what `remember` just wrote).
- `def _split_note()` — `- (2026-09-17 17:05) note text` → (stamp, note), else None.
- `def dedupe_notes()` — Collapse repeated `remember` lines, keeping the newest stamp.
- `def read_memory_block()` — MEMORY.md for the prompt: head (protocol) + tail (newest notes), de-duplicated first.
- `def _fits()` — Shrink the MEMORY.md block - never SOUL/IDENTITY - until the prompt fits the engine window.
- `def compose_system()` — The identity block. `carry=True` appends the compacted-conversation digest.
- `def append_memory()`
- `def load_session()`
- `def save_session()`
- `def new_session()`

### `engine.py`

- `def binary_forbidden()`
- `def resolve_binary()`
- **class `MEMORYSTATUSEX`**
- `def available_ram_bytes()`
- `def ram_ok()`
- `def _clean_env()`
- `def _assign_job()`
- **class `Runner`**
- `def _port_lock()`
- `def _log_keep_bytes()` — Newest bytes of each server log to keep; LYGO_ENGINE_LOG_MAX_BYTES=0 disables rotation.
- `def _open_engine_log()` — Open this port's server log for append, dropping all but the newest LOG_KEEP bytes.
- `def _close_log()` — Close a server log handle exactly once: on Windows the open handle locks the log file.
- `def _log_note()` — Best-effort one-liner into save/logs/engine.log - why the engine refused to do something.
- `def kill_tree()` — Kill pid and everything it spawned (taskkill /T /F; job objects only cover our own jobs).
- `def process_image_name()` — Full image path of a live pid, or None when it cannot be queried (gone, or access denied).
- `def pid_is_our_engine()` — True only when pid is alive AND its image really is our llama-server.exe.
- `def kill_pid()` — Kill a pid recorded in the pid file, but only after proving it is really our engine.
- `def kill_recorded_pids()` — Stop every engine pid in engine.pid.json, skipping any pid we cannot verify.
- `def stop_runner()`
- `def stop_port()`
- `def clamp_ctx()` — Context window: model-native (else the config default), capped by the config ctx_max.
- `def clamp_threads()` — CPU threads: a pin when given, else every core the host offers; always 2..16.
- `def clean_kv_type()` — A KV cache type the engine actually accepts, else '' (= let llama.cpp decide).
- `def spawn_runner()`
- `def _health()`
- `def _write_pids()` — Mirror the live runners into engine.pid.json, atomically.
- `def ollama_port_open()`
- `def runner_for()`

### `gguf_header.py`

- **class `Truncated`**
- **class `Cursor`**
  - `__init__()`
  - `need()`
  - `u32()`
  - `u64()`
  - `string()`
- `def _skip_value()`
- `def parse_gguf_header()`
- `def write_tiny_gguf()` — GGUF v3, tensor_count=0, kv general.name=tiny, general.architecture=llama.

### `image_tools.py`

- `def _in_ws()`
- `def image_info()`
- `def image_save()`
- `def image_list()`
- `def page_thumbnail()`

### `install.py`

- `def is_admin_tree()`
- `def _write_if_missing()`
- `def seed_identity()` — Copy public prompts into workspace. Skip if this is the steward admin tree unless force_public.
- `def ensure_layout()`
- `def write_first_run()`
- `def python_ok()`
- `def engine_present()`
- `def fetch_engine()`
- `def report()`
- `def main()`

### `limbs.py`

- `def _safe_arith()`
- `def canonicalize()` — Fill a limb's canonical argument names from the aliases a small model reaches for.
- `def _win_env()`
- `def _ws()`
- `def _kill_tree()` — Kill a pid and everything it spawned.
- `def _run_capture()` — Run argv, capturing text output; on timeout kill the whole process TREE.
- `def extra()`

### `lygo_engine.py`

- `def cpu_threads()` — One thread policy for the whole kit — see perf.auto_threads().
- `def vram_free_bytes()`
- `def backend_selection()` — Which engine build this host may use, straight from the backend layer.
- `def probe()`
- `def _is_colibri()`
- `def _is_moe()`
- `def flash_attn_on()` — console.json/local.json "flash_attn": "on" forces the flag; otherwise the measured default.
- `def plan()` — VRAM / RAM / SSD placement. Does not silently change precision.
- `def _drop_backend()` — Retire a GPU backend that just killed the engine on this host. Returns '' if there was none.
- `def boot()` — Spawn the planned backend. Returns brain status string.
- `def status()`

### `model_verdicts.py`

- `def _host()`
- `def _fingerprint()`
- `def _load()`
- `def _save()` — Write through the kit's atomic writer.
- `def entries()`
- `def _still_valid()`
- `def bad_ids()` — Ids this host proved unloadable, where the verdict still describes the file on disk.
- `def is_bad()`
- `def mark_bad()`
- `def clear()` — Forget one model's verdict, or every verdict for this host.

### `notepad.py`

- `def ensure()`
- `def _ok_id()`
- `def _note_path()`
- `def _load_index()`
- `def _save_index()`
- `def _rebuild_index()`
- `def list_notes()`
- `def read_note()`
- `def write_note()`
- `def delete_note()`
- `def new_note()`

### `ollama_import.py`

- `def _blob_path()`
- `def _display_id()`
- `def import_cas_tree()` — Read-only Ollama CAS. Never subprocess ollama.

### `openai_proxy.py`

- `def llama_chat()`
- `def llama_chat_stream()`

### `p0_hook.py`

- `def _try_import()`
- `def _init()`
- `def _policy()`
- `def gate_output_window()` — Policy regex only (no physics). QUARANTINE aborts the stream.
- `def gate_prompt()`

### `p3_note.py`

- `def vortex_signature()`

### `paths.py`

- `def under_workspace()` — Resolve a limb-supplied path against the workspace.
- `def engine_dir()` — The engine directory to launch: an activated GPU backend build, else engine/.
- `def _port_from_env()` — Ports are env-overridable so a USB stick can run *beside* a desktop console.
- `def console_cfg()` — Merged config/console.json + config/local.json (local wins). Cached, never raises.
- `def _cfg_int()` — Config integer. An explicit number is a pin (0 included); "auto"/absent means
- `def _cfg_str()` — Config text value, lowercased. Absent or junk means the default.
- `def console_limits()` — Engine launch limits from the kit config.
- `def ensure_dirs()`
- `def _record()`
- `def resolution_log()` — Every candidate the last stack-root resolution considered, in order, with its verdict.
- `def _stack_marker()` — A reason string when root really is the protocol stack, else ''.
- `def _as_path()`
- `def _stack_candidates()`
- `def stack_root_status()` — Resolve the protocol-stack root and say exactly what happened.
- `def stack_root()` — The protocol-stack root. Never None - stack_root_status() carries the reason.

### `perf.py`

- `def engine_path()` — The engine directory in play: an explicit one, else whatever is active for this host.
- `def engine_backends()` — GPU backends this engine build actually ships — a file scan, not a hope.
- `def parse_devices()` — Parse `llama-server --list-devices`: 'Vulkan0: NVIDIA GeForce RTX 4060 Ti (7949 MiB, 7181 MiB free)'.
- `def engine_devices()` — Ask the engine itself which devices it sees. Never raises: [] means none we can use.
- `def best_device()` — The device with the most free VRAM — where the layers would go.
- `def gpu_free_mib()` — Free VRAM on the best device, 0 when there is none. Never raises, never over-claims.
- `def auto_threads()` — Every core the host offers, one left for the console, capped for sanity.
- `def clamp_threads()` — CPU threads for llama-server: a pin is honored, else the host's own cores.
- `def sanitize_kv_type()` — A KV cache type this kit will plan around, else 'f16' (the engine's own default).
- `def kv_bytes_per_token()` — KV cache bytes for ONE token, read from the model's own GGUF header.
- `def kv_cache_mib()` — KV cache size in MiB for a context. An unknown model gets the flat allowance.
- `def plan_ngl()` — How many of 99 layers fit in the free VRAM. Returns (ngl, reason).
- `def _legacy_ngl()` — Pre-adaptive rule, kept for callers that cannot see a device list.
- `def host_id()` — This PC, for backend verdicts: no model, no live memory — the machine itself.
- `def fingerprint()` — Host identity: a stick carried to another PC must not inherit this PC's verdict.
- `def _load_store()`
- `def host_record()`
- `def remember_host()` — Merge one host's launch outcome. Atomic write, bounded history, never raises.
- `def _pin_int()` — An integer pin, or None. "auto", "", junk and a typo all mean "let the host decide".
- `def resolve()` — Probe facts + config pins + this host's memory -> the launch profile.
- `def ladder()` — Launch attempts, best first, CPU last: a GPU that cannot load must not kill the brain.
- `def report()` — The /api/health view of the launch profile. Never raises: health must always answer.

### `public_gateway.py`

- `def _warn_degraded_once()`
- `def _cors_ok()`
- `def _rate()`
- `def _ollama_chat()`
- `def _openai_chat()`
- **class `Handler`**
  - `log_message()`
  - `_origin()`
  - `_send()`
  - `_json()`
  - `do_OPTIONS()`
  - `do_GET()`
  - `do_POST()`
- `def main()`

### `receipts.py`

- `def _events_path()`
- `def _todos_path()`
- `def _keep_from_env()` — Positive int from the environment, else *default* (garbage is ignored, not fatal).
- `def _prune_receipts()` — Delete all but the newest *keep* receipt files, oldest first.
- `def _prune_lines()` — Keep only the newest *keep* lines of a jsonl store, rewritten atomically.
- `def prune_state()` — Bound the on-stick stores; returns counts/sizes so a caller can report them.
- `def prune_at_startup()` — Explicit startup prune (counts/sizes returned); safe to call before the first turn.
- `def _maybe_prune()` — Periodic prune after a write: throttled, and never allowed to fail a turn.
- `def create_node()`
- `def write_receipt()`

### `registry.py`

- `def registry_backup_path()` — registry.json.bak beside the live file (computed live: tests patch REGISTRY_PATH).
- `def load_status()` — What the last load() did — public so callers can surface a recovery.
- `def _log()` — Loud, dependency-free: stderr plus a line in save/logs/registry.log.
- `def tool_rank()` — How well this model does agentic TOOL CALLING — the console's actual job.
- `def _bad_on_this_host()` — Ids this host already proved it cannot load. A missing memory module is never fatal.
- `def _chats()`
- `def ranked()` — Every usable brain, best first: PREFER_IDS order, then tool rank, then size.
- `def candidates()` — Ordered ids to try as the brain: the default first, then every fallback.
- `def avail_ram_bytes()` — Available physical RAM, or 0 when it cannot be read (0 = 'unknown', never a refusal).
- `def vram_free_mib()` — This host's free VRAM (0 when there is none). Lazy + fail-safe: registry stays GPU-agnostic.
- `def _ram_floor_bytes()` — Half of INSTALLED RAM — a deterministic floor under the momentary-free measurement.
- `def prefer_by_ram()`
- `def ram_choice()` — Best tool-capable brain this host can actually RUN WELL; None when RAM/sizes are unknown.
- `def _fits()` — Would this model fit here? Unknown sizes/RAM return True — never move a human's pin blind.
- `def pick_default()` — Deterministic default (PREFER_IDS, else smallest). RAM-auto is opt-in via `prefer_ram`.
- `def _present()` — Only advertise a model whose weights are really on this machine.
- `def _read_registry()` — Parsed registry at *path*, or None when the file is absent, torn or not an object.
- `def load()` — Read registry.json, falling back to registry.json.bak instead of losing every model.
- `def save()`
- `def upsert()`
- `def get()`

### `repair_paths.py`

- `def _split()`
- `def _join()`
- `def _is_abs()`
- `def _drive_of()`
- `def _norm()`
- `def _under_root()`
- `def _tail()`
- `def _looks_pathish()`
- `def _is_path_key()`
- `def _is_secret_key()`
- `def _display()`
- `def _stamp()`
- `def _current_roots()` — Longest root first, so a workspace path tokenises as {workspace}, not {kit}.
- `def _infer_origin()` — Guess the drive/folders the config was written for, when it does not say.
- `def _collect_strings()`
- `def _ctx_for()`
- `def _host_owned()` — True for paths that belong to the machine rather than to the kit.
- `def _candidate_exists()` — True when a rewritten root would actually resolve on this host.
- `def rewrite_value()` — (new_value | None, kind, note) for one config string.
- `def _transform()`
- `def _stamp_policy()` — Record where this config's paths were written, so a later copy can still relocate them.
- `def plan()` — Load every config file and return [(path, mutated_data, ctx, rows), ...] without writing.
- `def print_plan()`
- `def apply()` — Back up then atomically rewrite every file that has changes. Returns what was written.
- `def repair_paths()` — Programmatic entry point. Without consent it prints the plan and refuses to write.
- `def main()`

### `runtime_facts.py`

- `def _server_module()`
- `def _state()`
- `def console_build()`
- `def selected_model()` — The weights actually answering this turn: live STATE first, then the registry.
- `def engine_name()`
- `def limb_names()`
- `def brain_mode()`
- `def cloud_info()`
- `def answering()` — Who generates the tokens this turn — the brain switch decides, the model never guesses.
- `def facts()`
- `def system_roles()` — The three systems and what each one is, in the compact form the prompt window can carry.
- `def prompt_block()`
- `def limb_catalog()` — Name + intent for every wired limb, so the agent knows what it can actually call.

### `scanner.py`

- `def _expand()`
- `def scan_roots()`
- `def _from_header()`

### `server.py`

- `def brain_port()`
- **class `_BadRequest`** — A malformed request envelope (Content-Length, transfer encoding) -> 400, not a 500.
- **class `_BodyTooLarge`** — Request body over the endpoint's limit: answers 413 instead of a misleading 400.
- `def _note_config_error()`
- `def _config_key()`
- `def load_console()` — config/console.json, optionally overlaid by config/local.json.
- `def default_scan_roots()`
- `def _next_model_rec()` — Next brain to try after one failed to load here: registry order, minus what we tried.
- `def maybe_spawn()`
- `def boot_async()`
- `def gate_all()` — Gate the WHOLE text, not just its head.
- `def _read_text_locked()` — Read a state file through the retrying reader - a writer may be mid-swap right now.
- **class `Handler`**
  - `log_message()`
  - `_query()`
  - `_headers_map()`
  - `_loopback()` — Is this request from this machine? Judged on the socket, never on the Host header.
  - `_ok_public()`
  - `_auth()`
  - `_send()`
  - `_json()`
  - `_read_body()` — Read the body, refusing a malformed or oversized Content-Length.
  - `_contain()` — Answer 500 instead of dropping the connection when a handler raises.
  - `do_GET()`
  - `_dispatch_GET()`
  - `do_POST()`
  - `_dispatch_POST()`
  - `_api_chat()`
  - `_v1_chat()`
- **class `_StickContainment`** — Console server that contains a failure instead of dying on it.
  - `handle_error()`
- `def main()`

### `skills_mod.py`

- `def core_root()` — Live LYRA core root, resolved at call time — never a frozen drive letter.
- `def _skill_md()`
- `def seed_bundled()`
- `def ensure()`
- `def load_state()`
- `def save_state()`
- `def _parse_skill_md()`
- `def _walk_skills()`
- `def extra_roots()`
- `def catalog()`
- `def list_skills()`
- `def read_skill()`
- `def set_enabled()`
- `def add_root()`
- `def prompt_catalog()`
- `def match_invoked()` — Which seats/skills the operator named. The most specific name wins.
- `def _http_json()`
- `def clawhub_search()`
- `def clawhub_inspect()`
- `def _download()`
- `def _safe_member()` — Relative target for one zip member, or None when the member must be skipped.
- `def _commit_staged()` — Move a fully-extracted skill tree into place, replacing any previous copy.
- `def _extract_skill_zip()`
- `def _load_catalogs()`
- `def skillhub_list()`
- `def skillhub_install()`
- `def clawhub_install()`

### `stack_health.py`

- `def run_stack_health()`

### `surface.py`

- `def drive_type()` — Windows volume type for a drive letter ("E:"), 0 when it cannot be read.
- `def media()` — Return ("usb"|"pc", why). Declaration wins, then the volume type, then the launchers.
- `def here()` — The system answering now: a LOCAL one while a local engine is ready, else the API-only portal.
- `def report()` — The label block: which system this is, what answers, and all three with one flagged.
- `def lines()` — Human-readable labels for a banner or a status screen: who this is, and all three.

### `tools.py`

- `def core_schema()`
- `def _strip_extended()` — Drop a Win32 extended-length / device prefix so the comparison sees the real target.
- `def _long_path()` — Ask Windows for the long form of a path, so an 8.3 short name (LYGOSE~1) cannot
- `def real_path()` — The final on-disk target a write would hit.
- `def _components()`
- `def write_allow_roots()` — The write allowlist: workspace, save/receipts plus the configured read/write roots.
- `def _refuse()`
- `def write_target()` — Resolve and authorise a write target: (real_path, None) or (real_path, refusal).
- `def _denied()` — True when the RESOLVED path names a denied location.
- `def _under()`
- `def _self_check()`
- `def _find_files()`
- `def dispatch()`
- `def parse_fence_tool()`

### `web_tools.py`

- `def _blocked()`
- `def _get()`
- `def x_status()` — (handle, post_id) when url is an x.com / twitter.com post URL, else None.
- `def _x_lines()`
- `def x_post()` — Read one X/Twitter post through a mirror API. RESOURCE, never CANON.
- **class `_DDG`**
  - `__init__()`
  - `handle_starttag()`
  - `handle_endtag()`
  - `handle_data()`
- `def _keywords()`
- `def wikipedia_extract()`
- `def wikipedia_search()`
- `def duckduckgo_search()`
- `def _json_get()`
- `def hn_search()`
- `def github_search()`
- `def stackexchange_search()`
- `def reddit_search()`
- `def wikidata_search()`
- `def searx_search()`
- `def jina_fetch()`
- `def web_search()`
- `def _wall()` — The marker that makes this body a wall instead of content, else None.
- `def _strip_html()`
- `def web_fetch()`

### `workspace_map.py`

- `def _load()`
- `def _save()`
- `def _norm()`
- `def _blocked_write()`
- `def _pinned_paths()`
- `def extra_paths()`
- `def revoked_set()`
- `def add_mount()`
- `def remove_mount()`
- `def list_mounts()`

### `world_clock.py`

- `def _wx_label()`
- `def _fetch_weather()`
- `def pulse_stamps()`
- `def pulse()`

### `vendor/p0/byte_entropy_filter.py`

- `def f32()`
- `def round4()`
- `def entropy_norm()`
- `def compression_ratio()`
- `def compute_phi_risk()`
- `def verdict_from_bucket()`
- `def build_reasoning()`
- `def validate_bytes()`
- `def canonical_line()`
- `def fixtures_path()`
- `def load_vectors()`
- `def run_vector_suite()`


## Appendix B — test index (generated)

Regenerate with:
`C:\Python313\python.exe "<hermes>\skills\software-development\as-built-build-documentation\scripts\build_doc_index.py" "I:/E Drive/lygo-protocol-stack/lygo_llm_console/tests"`

## Module and function index

_46 modules, 104 classes, 507 functions (generated, do not hand-edit)_
# Tree: `I:\E Drive\lygo-protocol-stack\lygo_llm_console\tests`

### `test_adaptive_perf.py`

- `def gpu_host()` — A probe result from a host with a proven, ready GPU.
- **class `DeviceParsingTest`**
  - `test_parses_a_real_list_devices_line()`
  - `test_an_empty_or_noisy_list_devices_is_just_an_empty_list()`
  - `test_total_without_a_free_figure_is_treated_as_free()`
  - `test_best_device_is_the_one_with_the_most_free_vram()`
- **class `LayerPlanningTest`**
  - `test_a_model_that_fits_is_fully_offloaded()`
  - `test_a_big_model_on_a_small_gpu_gets_a_partial_split()`
  - `test_no_spare_vram_leaves_the_model_on_the_cpu()`
  - `test_a_sliver_of_vram_is_not_worth_a_partial_split()`
  - `test_an_unknown_model_size_offloads_everything()`
  - `test_no_device_at_all_is_cpu()`
- **class `ProfileResolutionTest`**
  - `setUp()`
  - `tearDown()`
  - `_lim()`
  - `test_a_proven_device_gets_full_offload()`
  - `test_an_engine_build_without_a_backend_stays_on_the_cpu()`
  - `test_a_backend_with_no_device_stays_on_the_cpu()`
  - `test_config_pins_beat_a_proven_gpu()`
  - `test_threads_come_from_the_host_when_unpinned()`
  - `test_a_probe_that_cannot_see_devices_keeps_the_old_vram_rule()`
- **class `HostMemoryTest`**
  - `test_a_failed_launch_on_this_host_is_remembered_and_respected()`
  - `test_a_remembered_success_is_not_a_downgrade()`
  - `test_the_same_verdict_is_not_applied_to_a_different_model()`
  - `test_a_pin_is_never_overridden_by_host_memory()`
  - `test_the_record_survives_a_corrupt_file()`
  - `test_the_record_is_bounded()`
- **class `ConfigTokenTest`**
  - `setUp()`
  - `tearDown()`
  - `test_auto_is_not_a_pin()`
  - `test_explicit_numbers_stay_pins_zero_included()`
  - `test_numeric_strings_are_still_numbers()`
  - `test_the_shipped_config_asks_for_a_host_adaptive_launch()`
- **class `ThreadsTest`**
  - `setUp()`
  - `tearDown()`
  - `test_auto_uses_every_core_leaving_one_for_the_console()`
  - `test_clamp_honors_a_pin_and_caps_absurd_values()`
  - `test_clamp_falls_back_to_the_host_only_when_config_is_silent()`
  - `test_lygo_engine_keeps_one_thread_policy()`
- **class `LadderTest`**
  - `test_the_ladder_descends_and_always_ends_on_the_cpu()`
- **class `BootLadderTest`** — The GPU must be allowed to fail without taking the brain down.
  - `setUp()`
  - `tearDown()`
  - `_boot()`
  - `test_a_gpu_launch_that_dies_retries_a_smaller_split()`
  - `test_a_hung_gpu_launch_goes_straight_to_the_cpu()`
  - `test_a_launch_that_never_succeeds_reports_instead_of_hanging()`
  - `test_a_working_gpu_launch_is_remembered_for_this_host()`
- **class `ReportTest`**
  - `_state()`
  - `test_a_gpu_host_reports_the_device()`
  - `test_a_cpu_only_build_names_the_remedy_and_offers_the_api()`
  - `test_a_launch_fallback_is_surfaced()`
  - `test_report_never_raises_on_nonsense_state()`
  - `test_report_before_the_engine_is_planned_still_answers()`
- **class `PlanWiringTest`** — plan() must hand the adaptive profile to the launcher, not recompute it.
  - `setUp()`
  - `tearDown()`
  - `test_plan_exposes_the_profile_and_the_gpu_threads()`
  - `test_plan_on_a_backendless_build_is_honest_and_info_only()`
  - `test_plan_uses_a_real_file_size_when_the_record_omits_bytes()`
  - `test_flash_attention_is_opt_in_not_advertised_for_free()`

### `test_admin_train.py`

- **class `AdminTrainTests`**
  - `test_placeholder_urls()`
  - `test_web_fetch_rejects_placeholder()`
  - `test_steward_map()`
  - `test_find_soul()`
  - `test_credential_where_redacted()`
  - `test_system_has_brief()`
  - `test_host_prefetch_github()`

### `test_agent_io.py`

- `def isolate_workspace()` — Point `continuity` at a throwaway workspace for the duration of one test.
- **class `SanitizeTests`**
  - `test_model_answer_survives_boiler_words()`
  - `test_placeholder_is_rewritten_in_place()`
  - `test_empty_draft_falls_back_to_a_readable_readout()`
  - `test_fallback_humanises_skills()`
  - `test_boiler_only_draft_is_detected()`
- **class `PrefetchMessageTests`**
  - `test_instruction_is_plain_not_a_template()`
- **class `SameAnswerTests`**
  - `test_echo_is_detected()`
- **class `RuntimeFactsTests`**
  - `test_facts_name_the_live_model()`
  - `test_prompt_block_is_self_knowledge()`
  - `test_limb_catalog_lists_real_tools()`
- **class `SystemPromptTests`**
  - `test_compose_system_carries_runtime_and_limbs()`
  - `test_prompt_fits_the_engine_window()`
  - `test_newest_memory_notes_reach_the_model()`
  - `test_repeated_notes_do_not_flood_the_tail_window()`
  - `test_remembering_the_same_note_twice_writes_once()`
- **class `HistoryBudgetTests`**
  - `test_newest_turns_are_kept_and_old_ones_dropped()`
  - `test_short_sessions_are_untouched()`
- **class `AnsweringModelTests`** — The RUNTIME block has to name the model that actually generates this turn.
  - `_facts()`
  - `test_api_brain_reports_the_cloud_model_not_the_local_gguf()`
  - `test_local_brain_reports_the_local_weights()`
  - `test_prompt_block_promises_handoff_honesty()`
- **class `SeatTests`**
  - `test_architect_seat_is_installed()`
  - `test_most_specific_seat_name_wins()`
  - `test_architect_skill_md_carries_the_protocol()`
  - `test_whoami_reports_the_model_and_build()`
- **class `ChatInputTests`** — D13: an input the console did not understand used to be answered anyway.
  - `test_messages_is_the_contract()`
  - `test_shorthands_are_tolerated()`
  - `test_junk_entries_never_reach_the_prompt()`
  - `test_no_user_text_is_detectable()`
  - `test_image_only_turn_is_not_no_input()`
  - `test_newest_user_turn_wins()`

### `test_api_default.py`

- **class `ApiDefaultPolicyTests`**
  - `setUp()`
  - `tearDown()`
  - `wire()`
  - `test_deepseek_is_the_shipped_default()`
  - `test_blank_config_is_deepseek()`
  - `test_unshipped_provider_name_falls_back_to_deepseek()`
  - `test_deepseek_leads_the_backup_order_behind_an_explicit_primary()`
  - `test_explicit_primary_still_outranks_deepseek_but_deepseek_beats_other_fallbacks()`
  - `test_public_status_exposes_the_default_for_the_portal()`
  - `test_default_without_a_key_is_still_disabled_never_a_fake_call()`

### `test_backends.py`

- **class `BackendStoreTest`** — A fake kit laid out on disk: a shipped engine, a store, a data dir.
  - `setUp()`
  - `add_overlay()`
  - `add_engine_build()`
  - `verdict()`
  - `model_file()`
  - `fake_device_probe()` — Host-independent device probe: a GPU appears only once the overlay is applied.
  - `patch_devices()`
  - `test_store_kinds_are_detected()`
  - `test_broken_manifest_is_not_reported_as_installed()`
  - `test_no_backend_at_all_stays_on_cpu_and_launches_nothing()`
  - `test_half_applied_overlay_is_removed_when_nothing_is_installed()`
  - `test_gpu_disabled_by_config_never_tests_anything()`
  - `test_failed_self_test_is_remembered_and_leaves_engine_untouched()`
  - `test_a_bad_verdict_never_leaves_its_overlay_applied()`
  - `test_passing_self_test_applies_the_overlay_and_selects_it()`
  - `test_a_proven_engine_build_becomes_the_engine_dir_without_retesting()`
  - `test_verdicts_do_not_leak_between_hosts()`
  - `test_refetch_changes_the_key_and_earns_a_new_test()`
  - `test_leftover_overlay_without_a_store_entry_is_removed()`
  - `test_a_backend_that_names_no_device_is_recorded_bad_and_not_applied()`
  - `test_verdict_store_stays_inside_the_kit_data_dir()`
  - `test_probe_models_skip_embedding_models()`
  - `test_one_crashing_model_does_not_condemn_a_backend()`
  - `test_self_test_names_a_driver_crash_instead_of_guessing()`
  - `test_self_test_refuses_to_guess_without_an_engine_or_a_model()`
  - `test_probe_models_order_by_size_and_skip_giants()`
  - `test_plan_forces_cpu_when_the_backend_layer_says_not_proven()`
  - `test_plan_refuses_to_claim_a_gpu_the_backend_layer_did_not_prove()`
  - `test_health_reports_effective_not_planned_after_a_fallback()`
  - `test_backend_report_never_raises_with_a_broken_store()`
  - `test_stale_active_record_falls_back_to_the_shipped_engine()`

### `test_brain_switch.py`

- **class `RouterTests`**
  - `test_fallback_codes()`
  - `test_reason_names_the_failure()`
  - `test_mode_is_local_unless_api_is_on_and_healthy()`
  - `test_label_and_banner()`
  - `test_handoff_info()`
- **class `CloudStateTests`** — State machine on a throwaway config dir — never touches the operator's api.json.
  - `setUp()`
  - `tearDown()`
  - `test_default_is_local_and_cloud_off()`
  - `test_key_without_activation_stays_local()`
  - `test_activate_then_handoff_then_reactivate()`
  - `test_switching_back_to_local_keeps_the_key()`
  - `test_note_error_survives_restart_and_stays_local()`
  - `test_cooldown_expires()`

### `test_cloud_api.py`

- **class `CloudApiTests`**
  - `test_deepseek_provider()`
  - `test_sanitize_strips_junk()`
  - `test_public_status_never_has_key()`
- `def json_blob()`

### `test_cloud_chain.py`

- **class `_Stub`** — Minimal OpenAI-compatible endpoint that answers with a scripted code.
  - `log_message()`
  - `do_POST()`
- `def _serve()`
- **class `CloudChainTests`**
  - `setUp()`
  - `tearDown()`
  - `wire()`
  - `post()`
  - `test_402_on_primary_falls_through_to_second_key()`
  - `test_all_keys_failing_returns_last_failure_for_handoff()`
  - `test_malformed_request_does_not_burn_the_second_key()`
  - `test_single_key_config_unchanged()`
  - `test_no_key_at_all_still_401_no_api_key()`
  - `test_second_key_alone_can_carry_the_console()`
  - `test_neither_key_is_ever_echoed()`
  - `test_save_merges_a_backup_key_and_can_unwire_one()`
  - `test_chain_is_ordered_primary_first_and_skips_keyless_providers()`

### `test_colibri.py`

- **class `ColibriMapTests`**
  - `test_missing_launcher_is_ok()`
  - `test_detect_hf_dir()`
  - `test_plain_folder_not_colibri()`

### `test_compaction.py`

- `def fill_turns()` — Record n alternating turns with distinctive text and a file path in each.
- **class `CompactionCase`** — Every test runs against its own store: the live save/ tree is never touched.
  - `setUp()`
  - `tearDown()`
  - `fill()`
  - `test_journal_keeps_verbatim_text_and_stamps()`
  - `test_record_is_idempotent_on_a_repeated_turn()`
  - `test_index_is_monotonic_across_sessions()`
  - `test_empty_and_bad_roles_are_refused()`
  - `test_torn_last_line_does_not_lose_the_journal()`
  - `test_image_turns_are_recorded_with_a_label()`
  - `test_concurrent_writers_leave_only_valid_lines()`
  - `test_budget_leaves_room_for_prompt_and_answer()`
  - `test_trim_keeps_the_newest_turns_even_over_budget()`
  - `test_trim_keeps_short_history_whole()`
  - `test_window_pct_is_a_percentage()`
  - `test_compact_folds_only_what_left_the_window()`
  - `test_compact_is_idempotent()`
  - `test_carry_over_names_what_was_compacted()`
  - `test_carry_over_withholds_a_quarantined_digest()`
  - `test_auto_compact_only_fires_when_the_window_is_nearly_full()`
  - `test_auto_compact_never_raises()`
  - `test_autosave_cadence_and_rotation()`
  - `test_save_now_is_the_manual_button()`
  - `test_seal_zips_verifies_indexes_and_starts_a_new_session()`
  - `test_sealed_session_is_recallable_verbatim()`
  - `test_read_transcript_returns_the_whole_sealed_session()`
  - `test_seal_of_an_empty_session_refuses_without_touching_the_store()`
  - `test_auto_seal_fires_only_past_the_cap()`
  - `test_bundle_merges_old_archives_and_keeps_the_members()`
  - `test_keywords_drop_stopwords_and_short_words()`
  - `test_recall_without_keywords_explains_itself()`
  - `test_recall_reports_a_clean_miss()`
  - `test_recall_scores_matches_and_prefers_the_newest()`
  - `test_status_shape_and_consistency()`
  - `test_status_survives_a_missing_store()`
  - `test_safe_wrappers_never_raise()`
  - `test_legacy_current_json_is_not_the_record_of_truth()` — The old 40-message session file must not be what limits the record any more.
- **class `WiringCase`** — The surfaces the console prompt, the limb registry and the portal read.
  - `test_system_reserve_reserves_the_digest_too()`
  - `test_the_digest_is_opt_in_and_capped()`
  - `test_a_console_failure_never_becomes_a_prompt_error()` — compose_system must degrade, never raise, when the record is unreadable.
  - `test_recall_history_is_a_registered_limb()`
  - `test_a_named_recall_is_run_by_the_host()` — The operator naming a limb the model would not call still gets an answer.
  - `test_status_does_not_walk_the_archive()` — A status call runs every turn: it must not rglob the archive on a USB stick.
  - `test_index_reads_only_the_tail()` — The index grows with the archive; a status read must be a tail read.
  - `test_the_console_still_boots_with_a_broken_record_module()` — A broken record module must cost the record, never the console.

### `test_continuity.py`

- **class `ContinuityTests`**
  - `test_seed_and_append()`

### `test_continuity_ui.py`

- **class `ContinuityUiTests`**
  - `test_not_mashed()`

### `test_debug_pass.py`

- **class `FlashAttnConfigIsWiredTests`**
  - `test_config_paths_are_imported_not_free_names()`
  - `test_setting_on_reaches_the_flag()`
  - `test_setting_off_and_broken_config_stay_false_without_raising()`
- **class `BackendLayerFailurePathTests`** — The CPU answer must survive the backend layer dying — that is the whole point of it.
  - `_boom()`
  - `test_backend_selection_answers_cpu_instead_of_raising()`
  - `test_probe_survives_a_backend_layer_error()`
- **class `VerdictWriteTests`**
  - `test_verdict_write_is_atomic_and_leaves_no_debris()`
- **class `LaunchFlagTests`**
  - `test_the_invalid_no_mmap_flag_is_gone()` — `--no-mmap` is not a flag in this build: passing it aborts the launch. -lm none is.

### `test_donate_radio.py`

- **class `DonateRadioTests`**
  - `test_console_portal()`
  - `test_web_portal()`

### `test_engine.py`

- **class `EngineTests`**
  - `test_refuse_nested_ollama()`
  - `test_allow_kit_engine()`

### `test_lygo_engine.py`

- **class `LygoEnginePlanTests`**
  - `test_gguf_uses_llama_mmap()`
  - `test_kit_config_beats_the_hardware_auto_plan()` — An explicit ngl/threads is a pin, 0 included — the shipped config now says "auto".
  - `test_colibri_dir_uses_coli_backend()`

### `test_math_routing.py`

- **class `MathRecogniserTests`**
  - `test_bare_arithmetic_is_recognised()`
  - `test_questions_that_are_not_arithmetic_are_left_alone()`
- **class `HostPrefetchTests`**
  - `test_arithmetic_prefetches_calc_and_not_the_web()`
  - `test_the_sum_is_answered_not_merely_searched()`
  - `test_the_factual_control_still_goes_to_the_web()`
- **class `ModelCallRedirectTests`**
  - `_msg()`
  - `test_a_web_search_for_arithmetic_is_redirected_to_calc()`
  - `test_a_real_search_is_not_redirected()`

### `test_model_verdicts.py`

- **class `ModelVerdictTests`**
  - `setUp()`
  - `tearDown()`
  - `test_a_failed_model_is_remembered_and_never_picked_again()`
  - `test_the_verdict_is_per_host()`
  - `test_the_verdict_dies_when_the_file_changes()`
  - `test_clear_forgets_only_what_it_is_asked_to()`
  - `test_a_corrupt_store_never_breaks_a_boot()`
  - `test_coder_brains_are_offered_before_bigger_general_models()`

### `test_no_history_shadow.py`

- **class `NoHistoryShadowTests`**
  - `test_app_js_does_not_shadow_window_history()`

### `test_notepad.py`

- **class `NotepadTests`**
  - `setUp()` — Notes go to a throwaway notepad, never the operator's live save/notepad/.
  - `test_write_read_list()`
  - `test_bad_id()`
  - `test_tools_opt_in()`
  - `test_portal_has_notepad()`

### `test_openai_proxy.py`

- **class `FakeLlama`**
  - `log_message()`
  - `do_POST()`
- **class `ProxyTests`**
  - `test_forward()`

### `test_p0_hook.py`

- **class `P0HookTests`**
  - `test_format_c_quarantine()`
  - `test_format_a_string_allow()`
  - `test_diskpart_quarantine()`
  - `test_short_english()`
  - `test_12k_cap()`
  - `test_physics_available_without_stack_env()`

### `test_port_isolation.py`

- `def _fresh_copy()` — A throwaway copy of the config machinery, as a first boot of the kit would leave it.
- `def _lines()`
- **class `PortIsolation`**
  - `test_example_does_not_pin_concrete_ports()`
  - `test_seeded_copy_keeps_its_own_console_ports()`
  - `test_resolver_follows_console_json_then_env_wins()`
  - `test_launchers_resolve_through_the_kit_reader()`

### `test_ports_env.py`

- `def probe()`
- **class `PortEnvTests`**
  - `test_defaults_are_the_desktop_ports()`
  - `test_stick_env_moves_every_port()`
  - `test_junk_or_out_of_range_falls_back_to_the_default()`

### `test_public_gateway.py`

- **class `PublicGatewayTests`**
  - `test_cors_allowlist()`
  - `test_rate_limit()`
  - `test_web_portal_files()`

### `test_public_install.py`

- **class `PublicInstallTests`**
  - `test_bat_is_portable()`
  - `test_prompts_are_public_seeds()`
  - `test_install_skips_admin_tree()`
  - `test_pack_script_skips_admin()`

### `test_record_e2e.py`

- `def setUpModule()`
- `def tearDownModule()`
- `def call()`
- `def seed()`
- **class `RecordRouteTests`**
  - `test_status_route_reports_the_configured_window()` — The window the UI shows must be the window the engine is actually opened with.
  - `test_the_save_button_route_stamps_the_record()` — POST action=save is the manual button: it must stamp, fold and answer.
  - `test_the_save_button_route_is_idempotent_when_nothing_changed()`
  - `test_a_rollup_folds_what_left_the_window()` — With room in the window nothing is folded; asked to keep only 4 turns, the rest folds.
  - `test_the_recall_limb_route_finds_an_older_turn()`
  - `test_a_bad_action_answers_instead_of_raising()`
  - `test_the_archive_route_lists_the_index()`
  - `test_the_record_routes_survive_a_missing_store()`
  - `test_the_console_still_answers_after_a_broken_save()` — A save that cannot write must answer, not wedge the console for the next turn.

### `test_registry.py`

- **class `RegistryTests`**
  - `test_upsert_roundtrip()`
  - `test_prefer_qwen()`

### `test_registry_ram.py`

- **class `RamChoiceTests`**
  - `setUp()`
  - `test_big_host_prefers_the_tool_capable_model_over_the_bigger_weak_one()` — Policy: agentic tool-calling beats raw size. gemma2:9b is bigger, llama3.1:8b is the
  - `test_24gb_also_gets_the_tool_capable_8b()`
  - `test_a_coder_brain_outranks_a_bigger_general_model()`
  - `test_9gb_free_picks_the_3b()`
  - `test_4gb_free_picks_the_1b()`
  - `test_nothing_fits_still_returns_the_smallest_chat()`
  - `test_unknown_ram_returns_none_so_normal_order_applies()`
  - `test_embed_models_are_never_chosen_as_brain()`
  - `test_pick_default_without_ram_keeps_preference_order()`
  - `test_pick_default_falls_back_when_ram_unknown()`
  - `test_pick_default_uses_ram_when_asked()`
  - `test_plain_pick_default_stays_deterministic_even_with_the_flag_on()` — console.json enabling RAM-auto must not silently change pick_default's contract.
- **class `UpsertPinTests`**
  - `setUp()`
  - `tearDown()`
  - `test_first_scan_auto_picks_by_ram_and_records_the_source()`
  - `test_human_switch_wins_over_ram()`
  - `test_same_stick_retunes_when_the_human_pin_no_longer_fits()`
  - `test_auto_pins_follow_a_machine_change()`
  - `test_without_the_flag_the_source_is_auto_not_ram()`
  - `test_registry_is_json_round_trippable()`
- **class `VramAwareChoiceTests`** — A brain has to FIT THE GPU to be fast: placement is worth more than parameters.
  - `test_a_coder_that_fits_vram_beats_a_bigger_coder_that_does_not()`
  - `test_without_a_gpu_the_biggest_capable_model_still_wins()`
  - `test_a_momentarily_busy_host_does_not_downgrade_the_brain()`
  - `test_the_floor_never_lowers_a_healthy_reading()`

### `test_repair_guards.py`

- `def _ctx()` — Build the context with the module's own builder so it always carries every key.
- **class `RepairGuards`**
  - `setUp()`
  - `tearDown()`
  - `test_host_folders_are_never_adopted()`
  - `test_unresolvable_remap_keeps_the_original()`
  - `test_kit_owned_path_still_follows_the_drive()`
  - `test_portable_values_are_left_alone()`

### `test_request_envelope.py`

- `def setUpModule()`
- `def tearDownModule()`
- `def raw()` — Send a hand-built request; return status line, headers and the whole declared body.
- `def status_of()`
- `def get_json()` — GET a route and wait for the whole declared body.
- **class `RequestEnvelopeTest`**
  - `test_negative_content_length_is_rejected_instead_of_blocking()`
  - `test_non_numeric_content_length_is_400_not_500()`
  - `test_oversized_body_is_413()`
  - `test_request_handler_has_a_socket_timeout()`
  - `test_workspace_reports_the_true_entry_count()`

### `test_scanner.py`

- **class `GgufTests`**
  - `setUp()`
  - `test_tiny_header()`
  - `test_cas_qwen_id()`
  - `test_blob_missing()`
  - `test_scan_tiny()`

### `test_security_hardening.py`

- `def setUpModule()`
- `def tearDownModule()`
- `def call()`
- **class `LoopbackIsJudgedOnTheSocketTest`**
  - `test_spoofed_host_does_not_grant_loopback()`
  - `test_loopback_caller_needs_no_token()`
- **class `TokenIsNotServedToRemoteCallersTest`**
  - `test_remote_shell_omits_the_token()`
  - `test_loopback_shell_still_splices_the_token()`
  - `test_remote_api_accepts_header_query_and_cookie()`
  - `test_proving_the_token_to_the_shell_sets_a_strict_cookie()`
- **class `HealthIsPublicButNotInformativeTest`**
  - `test_remote_caller_gets_basenames_not_absolute_paths()`
  - `test_loopback_caller_keeps_the_full_paths()`
- **class `OversizedBodyTest`**
  - `test_oversized_body_is_413_not_400()`
- **class `ConsoleConfigTest`**
  - `test_a_torn_config_does_not_raise()`
  - `test_cache_returns_a_copy()`
- **class `GateReadsTheWholeTextTest`**
  - `test_pattern_past_the_old_8k_window_is_caught()`
  - `test_clean_text_still_allows()`
  - `test_short_text_matches_gate_prompt()`
- **class `PublicGatewayNeverFabricatesAnAllowTest`**
  - `test_the_fail_open_override_is_gone()`
- **class `ShellRouteTest`** — The shell is the only HTML, and the public routes stay public.
  - `test_raw_template_is_not_served()`
  - `test_public_assets_still_serve_to_a_remote_caller()`
  - `test_world_clock_stays_public()`
  - `test_remote_still_refused_on_a_data_route()`

### `test_shipped_engine_purity.py`

- **class `ShippedEnginePurityTests`**
  - `setUp()`
  - `_dlls_an_active_backend_owns()` — Dll names the backend store has deliberately placed in engine/ on THIS host.
  - `test_shipped_engine_directory_carries_no_unowned_gpu_dll()`
  - `test_cpu_kernels_are_present_next_to_the_server()`
  - `test_gpu_dlls_belong_to_the_backend_store()`
  - `test_stale_perf_active_cannot_point_the_console_at_a_missing_engine()`

### `test_skills.py`

- **class `SkillsTests`**
  - `test_fifteen_champions_seeded()`
  - `test_read_and_toggle()`
  - `test_prompt_has_catalog_not_full_bodies()`
  - `test_tools_and_prefetch()`
  - `test_portal_has_skills_panel()`
  - `test_skillhub_urls()`

### `test_surface_labels.py`

- **class `VocabularyTests`**
  - `test_three_systems_exactly()`
  - `test_labels_are_distinct_and_say_what_they_are()`
  - `test_every_system_explains_what_answers()`
- **class `MeasuringTests`**
  - `test_declaration_beats_the_probe()`
  - `test_removable_media_reads_as_usb_and_fixed_as_pc()`
  - `test_unreadable_volume_falls_back_to_the_launchers()`
  - `test_no_local_engine_means_the_api_only_portal()`
  - `test_local_ready_reports_the_media_system()`
- **class `ReportShapeTests`**
  - `test_report_lists_all_three_with_exactly_one_here()`
  - `test_banner_lines_name_the_current_system()`
- **class `WiringTests`** — The label is only real if the surfaces quote it. Source guards, because a health payload
  - `test_health_quotes_the_system()`
  - `test_runtime_facts_quote_the_system()`
- **class `BriefRoleTests`** — The prompt carries a compact form of the same three roles - and it must stay compact.
  - `test_brief_roles_cover_the_same_three_systems()`
  - `test_brief_roles_keep_the_point_of_each_system()`
  - `test_prompt_states_the_roles_and_still_fits()`
- **class `RoleTests`** — Each system says what it *is*, in the operator's own terms - three separate systems that
  - `test_every_system_has_a_role()`
  - `test_roles_say_what_the_operator_said()`
  - `test_report_and_lines_carry_the_role()`
  - `test_runtime_facts_quote_the_roles()`
  - `test_portals_state_the_roles()`
- **class `PortalLabelTests`** — Every surface a human reads must name the system it is. The console page is server-rendered
  - `test_console_page_carries_the_server_rendered_token()`
  - `test_server_renders_that_token()`
  - `test_public_portal_states_it_is_api_only()`

### `test_tool_battery.py`

- **class `ToolBattery`**
  - `test_core_schema_small()`
  - `test_dispatch_core()`
  - `test_placeholder_blocked()`

### `test_tool_routing.py`

- `def _fn()`
- **class `CoreSchemaRoutingTests`**
  - `test_priority_tool_leads_the_local_schema()`
  - `test_calc_is_described_for_arithmetic()`
  - `test_web_tools_rule_arithmetic_out()`
  - `test_cloud_schema_keeps_the_full_tool_order()`

### `test_tools.py`

- **class `ToolsTests`**
  - `test_source_forbid()`
  - `test_llama_key_denied()`
  - `test_workspace_write_read()`
  - `test_alias_read()`

### `test_tuning.py`

- `def _fake_llama_chat()`
- `def setUpModule()`
- `def tearDownModule()`
- `def post_json()`
- **class `ChatToolsFlagTests`** — `"tools": false` used to take the handler down with an UnboundLocalError.
  - `test_tools_false_is_answered_instead_of_500()`
  - `test_tools_true_is_answered()`
  - `test_missing_tools_key_defaults_to_tools_on()`
  - `test_a_plain_turn_reports_the_engine_timings()`
  - `test_health_carries_the_last_turn_timings()`
  - `test_the_streamed_done_event_carries_the_timings()`
  - `test_a_turn_the_engine_never_ran_has_no_perf_claim()` — No timing block, no number — telemetry must not invent a speed.
- **class `KvMathTests`** — The KV cache is the number the planner used to ignore.
  - `test_kv_bytes_per_token_comes_from_the_header()`
  - `test_gqa_is_honoured_not_the_attention_head_count()` — 28 attention heads would be 401 KiB/token — planning that would refuse every GPU.
  - `test_an_unknown_header_is_charged_flat_not_free()`
  - `test_the_cache_scales_with_context_and_type()`
  - `test_a_junk_kv_type_falls_back_to_f16()`
- **class `PlannerKvTests`** — plan_ngl keeps its verdicts, and now it knows what the cache costs.
  - `test_a_model_whose_cache_does_not_fit_is_not_fully_offloaded()`
  - `test_the_same_model_without_its_cache_still_fits()`
  - `test_kv_is_still_charged_when_nobody_measured_it()`
  - `test_the_resolved_profile_reports_the_kv_it_planned_with()`
- **class `EngineFlagTests`** — The launch flags are sanitised here, clamped there, and part of the launch signature.
  - `test_kv_type_is_whitelisted()`
  - `test_spawn_runner_accepts_the_tuning_knobs()`
- **class `ConsoleLimitTests`** — The engine knobs are read exactly where the rest of the launch limits are read.
  - `_limits()`
  - `test_the_knobs_are_part_of_the_launch_limits()`
  - `test_junk_reads_as_no_tuning()`
  - `test_a_shipped_kit_that_says_nothing_gets_no_flags()`
- **class `PlanKnobsTests`** — plan() must state the knobs boot() will really send.
  - `_plan()`
  - `test_plan_hands_the_kv_figure_to_the_planner()`
  - `test_the_knobs_travel_with_the_plan()`
  - `test_the_cache_is_sized_at_the_context_the_engine_will_run()` — A 32k-native model under a 16k cap: charge 16k of cache, not 32k (measured live).
  - `test_the_same_model_unquantised_costs_twice_the_cache()`
  - `test_a_junk_kv_type_in_config_becomes_f16()`
- **class `TunedFlagFallbackTests`** — A performance flag that breaks a launch must cost speed, never the brain.
  - `_boot()` — fail_first: the layer ladder tries 99/49/8/0, so four failures exhaust it.
  - `test_tuned_flags_are_sent_when_they_work()`
  - `test_a_flag_failure_retries_with_the_shipped_defaults()` — Four layer attempts fail, then the last resort runs with the shipped flags.
  - `test_the_effective_profile_names_the_flags_that_ran()`
- `def write_dim_gguf()` — A GGUF v3 header with architecture dimensions, in the order a converter writes them.
- **class `GgufHeaderDimTests`** — The KV cache size is read from the model's own header, whatever order it writes keys in.
  - `_write()`
  - `test_the_cache_is_read_when_context_length_comes_first()`
  - `test_no_kv_head_key_means_full_attention_not_a_guess()` — A model without attention.head_count_kv is MHA: the attention head count IS the KV count.
  - `test_a_header_with_no_attention_dimensions_gets_the_flat_allowance()`
- **class `EngineKeyTests`** — The engine key is generated per install; a placeholder in the file is not a permanent answer.
  - `setUp()`
  - `tearDown()`
  - `test_a_placeholder_key_is_replaced()`
  - `test_a_short_key_is_replaced()`
  - `test_a_real_key_is_kept_stable()`
  - `test_a_missing_key_is_generated()`
- **class `PortalPerfWiringTests`** — The console reports tok/s per turn; the portal has to actually show it.
  - `setUp()`
  - `test_both_turn_paths_feed_the_readout()`
  - `test_the_readout_says_tokens_per_second()`
  - `test_a_console_without_perf_does_not_break_the_readout()` — An older console sends no perf block: the line must degrade, not print undefined.

### `test_usb_atomic_writes.py`

- `def _run()`
- **class `TestAtomicWrite`**
  - `test_concurrent_writers_never_collide()`
  - `test_locked_target_is_retried_not_fatal()`
- **class `TestNotepadIndexUnderThreads`**
  - `test_concurrent_rebuild_index_does_not_raise()`
- **class `TestRequestContainment`** — A failing request must answer 500 and leave the console serving.
  - `setUpClass()`
  - `test_handle_error_never_raises_on_non_ascii()`
  - `test_dispatch_exception_answers_500_and_server_survives()`
- **class `TestIndexIsNotRewrittenWhenUnchanged`**
  - `test_unchanged_notes_do_not_rewrite_the_index()`
- **class `TestWritersSurviveReaders`**
  - `test_writer_is_not_broken_by_concurrent_readers()`
- **class `TestReadTextRetriesTransientDenials`** — The read side of the same defect: a denial in flight must not reach the caller.
  - `test_read_text_waits_out_a_transient_denial()`
  - `test_read_text_does_not_stall_on_a_missing_file()`

### `test_usb_portability.py`

- **class `PortsHaveOneSourceTest`**
  - `test_shipped_modules_hardcode_no_host_port()`
  - `test_engine_status_reports_the_stick_portal()` — The kit's own status feed must speak the port the stick is bound to.
- **class `ConfigLimitsTest`**
  - `setUp()`
  - `tearDown()`
  - `test_console_limits_reads_config_even_at_zero()`
  - `test_plan_lets_config_beat_the_hardware_auto_plan()`
  - `test_ctx_and_threads_clamps_follow_config()`
- **class `RegistryPortabilityTest`**
  - `_isolate()`
  - `_restore()`
  - `test_weights_that_left_the_machine_are_not_advertised()`
  - `test_pinned_brain_that_left_the_machine_is_repicked()`

### `test_usb_selfcontained.py`

- **class `ScanRootTests`**
  - `test_the_declared_stick_model_folder_is_always_scanned()` — LYGO_MODELS is set by the launchers: ignoring it means booting empty on a clean PC.
  - `test_a_declared_parent_folder_is_descended_to_the_cas()`
  - `test_the_kits_own_models_folder_survives_a_stale_config()`
  - `test_usb_root_extras_still_work()`
  - `test_the_real_stick_cas_is_scanned_and_yields_models()`

### `test_web_tools.py`

- **class `WebToolsTests`**
  - `test_block_loopback()`
  - `test_wikipedia()`
  - `test_multi_engine_search()`
  - `test_leech_query_has_hits()`
  - `test_extract_urls()`
- **class `XPostTests`** — x.com answers anonymous readers with a login wall; posts come from a mirror API.
  - `test_x_status_parses_post_urls()`
  - `test_x_post_reads_mirror_payload()`
  - `test_wall_detector()`
  - `test_web_fetch_wall_is_not_ok()`
  - `test_x_fetch_falls_back_to_mirror_error()`

### `test_workspace_map.py`

- **class `WorkspaceMapTests`**
  - `setUp()` — Mount into a throwaway map, never the operator's live save/workspace_map.json.
  - `test_add_remove_temp()`
  - `test_portal_has_mount_ui()`

### `test_world_clock.py`

- **class `WorldClockTests`**
  - `test_pulse_stamps()`


