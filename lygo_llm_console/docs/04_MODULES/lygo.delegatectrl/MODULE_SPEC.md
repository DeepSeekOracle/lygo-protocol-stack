# lygo.delegatectrl - MODULE_SPEC

`src/modules/lygo.delegatectrl/` - version 1.0.0, introduced 1.7.0.
Routes `GET /api/delegate` and `POST /api/delegate`, pane `dock.delegatectrl` (slot `dock`).
Owns `save/delegate`, writes through `atomicio`, sits behind the `p0` gate.

## What it is

The card and the buttons for the side-agent pair in `delegate_tools` (`subagent_run`, `subagent_pool`),
which are the 43rd and 44th tools in the EXTENDED schema and were already registered in `limbs.py`. It
renders nothing itself and registers NO limb: every call goes through the same two functions the
brain's own tools call, so a button and the agent can never disagree about what happened. The strip
publishes four buttons, and every one is an action the tool's own table accepts.

| button | action | what it does | what it costs |
| --- | --- | --- | --- |
| Probe pool | `probe` | asks each engine in the roster to answer once and records which did | one request per engine on a METERED free tier |
| Smoke test | `smoke` | hands one tiny task (`SIDE_OK`) to the default engine and records exactly what it did | one request |
| Use free brain | `brain_on` | points the console's OWN turns at the free pool (through the `free_brain` adapter) and snapshots what to restore | one free request per turn, and every turn gets SLOWER (20-65 s) |
| Back to paid / local | `brain_off` | restores the provider, model and on/off that were there before, then stops the adapter | nothing |

The engine half is the `opencode` CLI: the free pool is free (no key, no account) and it calls tools,
but it is reachable ONLY by driving that client - a plain HTTP call to the same endpoint answers
`403 FreeTierError: "OpenCode's free tier can only be used from within OpenCode."` - so this is a
harness, never a provider row in the engine list.

## The switch - the console's own turns, on the free pool

`Use free brain` is the other half of this card: not a side task, but the turns the OPERATOR sends.
It exists because the console's brain is chosen in exactly one place (`cloud_api`: provider + url +
model + key + enabled) and the free pool cannot be a row there directly - a plain call answers `403
FreeTierError`, and `opencode serve` is a web UI, not an OpenAI-shaped API. So `free_brain` runs a
LOCAL ADAPTER inside the console process: an OpenAI-shaped endpoint (`/v1/chat/completions`) that
answers each request by driving the CLI, which is the one client the free tier accepts.

The switch rides cloud_api's EXISTING `custom` row ("OpenAI-compatible URL"), so no core file changes
and there is no second brain path to keep in step. Three details are worth knowing:

* **It saves a placeholder key, and that is not a credential.** `cloud_api.chain_for` only offers a
  provider that holds a key, so a keyless row is dropped in silence and the switch would look broken
  with nothing anywhere saying why. The shim ignores the value; a test pins that the row is really in
  the chain, because "the config says custom" and "the console will use custom" are different claims.
* **A long prompt travels as a FILE, never through argv.** Measured on this box: `opencode` on PATH
  is the npm `.CMD` wrapper, which re-parses its line through cmd.exe, so the real ceiling is cmd's
  ~8191 - not Windows' 32767. A 2,164-character prompt answered (66.5 s); an 18,168-character one came
  back exit 0 with NO answer in 0.06 s, because the text never reached the model. Real console turns
  carry a system prompt, a tool schema and history, so they cross that line constantly. Past
  `ARGV_PROMPT_CHARS` (7000) the prompt is written to a file and the argv carries one sentence naming
  it; the CLI reads it with its own `read` tool - measured working at 17,783 characters: exit 0 in
  12.0 s, the answer exactly as asked, the event stream reporting `cost: 0`. Past `MAX_PROMPT_CHARS`
  (120000) the shim refuses by name (`prompt_too_long`) and spends nothing, and the console's own walk
  hands that turn to the next provider. The receipt ring at `/health` says which way each request
  travelled (`via: argv` or `via: file`).
* **`off` restores, it does not guess.** The snapshot (provider, model, enabled) is taken at switch
  time and put back on the way out; key material is NEVER copied into this module's state file.

## Contract

* `POST /api/delegate` takes `{action, task?, engine?, dir?, timeout?, read_only?, consent?}` and
  answers with the code the caller reads: 200 for a thing that happened, 409 for a pool that answered
  nothing or a run that failed, 403 for a gate or a missing consent, 400 for `no_task` or an unknown
  action. `GET /api/delegate` is the card alone.
* Every action that spends a request or changes the machine leaves a receipt (`probe`, `run`, `smoke`),
  and the answer carries the fresh card.
* State is `save/delegate`: `verified.json` (what the last probe heard) and `runs.json` (one record per
  task handed out, capped at 25). Both through `atomicio`.

## Honesty rules

* **The roster is not evidence.** `Probe pool` is the only thing that asks a metered engine anything,
  and the card reads `not checked` (grey, never green) until it has. A green pool light means engines
  answered, at a stated time.
* **A console start spends nothing.** `health` is a local read - no socket, no subprocess, no probe -
  and says `probed_at_boot: false`. The pane's own refresh never probes either.
* **A masked error is reported as masked.** "Unexpected server error. Check server logs for details." is
  what a spent cap, a rate limit, a retired model id and a broken directory all look like, so the card
  carries the CLI's own ref and the hint that gets the real cause (`--print-logs`), never a diagnosis.
* **A run is read-only unless the caller says otherwise.** `read_only` defaults true and denies `edit`,
  `bash` and `webfetch` through the CLI's own OBJECT-map permission shape, which is the only shape it
  honours: the list-of-`{permission,pattern,action}` form parses and is silently ignored (measured - a
  read-only run still wrote a file, which is why the shape is pinned by a test).
* **A directory outside the workspace needs `consent`.** A side agent RUNS where it is put, so the
  limb refuses an outside folder by name until consent is given, the same rule the film and plexo
  limbs follow.
* **Private operator context is never handed to a free tier.** The pool is metered and its per-model
  data terms differ; the card says so beside the button that would do it.
* **The switch reports what it found, not what it asked for.** `brain_on` re-reads
  `cloud_api.public_status()` after saving and answers with the provider, model and url it actually
  sees there; `status` marks the brain `free` only when the configured url really points at the
  adapter's own loopback port AND the adapter is listening. Stop the adapter and the same call stops
  claiming it.
* **The adapter's failures are the CLI's words.** A 502 carries the engine error with its ref, the
  model, the elapsed seconds and the prompt length, and the last eight requests are kept in a ring
  readable at the adapter's `/health` - so "the adapter returned 502" is never a dead end.
