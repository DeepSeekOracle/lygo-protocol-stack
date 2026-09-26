# Tasking console: work that outlives the turn, and a daemon that keeps it alive

Phase two of the self-build harness. Phase one gave the console the limbs to check, seal, restart and
equip itself (`docs/SELF_BUILD_HARNESS_PLAN.md`). This phase answers the next failure: a console that
can only work *inside* a turn stalls whenever the work is slow, and nothing it starts survives it.

## Where the design came from

The operator asked for the console to be wired like the assistant's own machinery. The parts that
actually answer this live in the Hermes tree at `%LOCALAPPDATA%\hermes\hermes-agent`:

| Hermes module | What was taken |
|---|---|
| `cron/jobs.py`, `cron/scheduler.py` | jobs are declared data, the scheduler is idempotent (it answers from the record of the last run, so a restart cannot double-fire) |
| `tools/todo_tool.py` | a durable list the operator can read, rather than state inside a model's head |
| `tools/delegate_tool.py` | work handed off and collected later instead of done in the asking turn |
| `agent/turn_liveness.py`, `agent/deadline.py` | a deadline per unit of work and a heartbeat, so *stalled* is distinguishable from *slow* |
| `agent/periodic_scheduler.py` | supervision as a sweep, not a pile of timers |

## What was built here

| File | What it is |
|---|---|
| `src/tasking.py` | JSONL-backed task queue + one daemon worker thread. `add()` returns an id at once; the worker heart-beats every 15s and runs one job at a time; a job that stops beating past `STALL_AFTER` (90s) or its deadline is reported **stalled**, and the queue moves on. A job is a *limb call*, never a command line, so every existing guard and consent rule still applies. |
| `src/crons.py` | schedules in `data/crons.json`. `every=<seconds>` or `at=HH:MM` daily. Being due is computed from `last_run`, so a keeper restart cannot double-fire. A due job is **enqueued**, never run inline - a slow job cannot delay the next sweep. |
| `tools/keeper.py` | the daemon: sweeps the two ports, brings back what is missing (doorbell, then console) behind a 90s cooldown so a crash loop cannot become a relaunch storm, drives the crons, writes `data/keeper.json` and `save/logs/keeper.log`. `sweep()` takes every probe as an argument, so the supervision policy is testable without a console. |
| 8 new limbs | `task_add`, `task_list`, `task_show`, `task_cancel`, `cron_add`, `cron_list`, `cron_remove`, `keeper_status` - all in the **local** schema, because the on-box brain is the one asked to do the work. |

The local schema is a measured budget, not a count: **36 tools, 13,123 chars, ~3.3k tokens** of a
32k window.

## What was proved, and how

- `tests/test_tasking_keeper.py` - 16 tests: the worker really runs a queued limb and records the
  result; a failing limb is recorded `failed`, not `done`; a task that stopped beating is reported
  **stalled**; the cron scheduler is idempotent; a disabled job is never due; the keeper rings a dead
  console **once** and then respects the cooldown; a dead doorbell gets started; due crons are started
  by the sweep.
- `tests/test_self_build_harness.py` - 11 tests: all four self-build limbs advertised, visible to the
  local brain, and refusing without consent.
- **Live**: the on-box agent was asked to queue a background `self_test` with `task_add`. It called
  the limb, got `{ok: true, id: t70d64b9679, state: queued}`, named the id in its reply, and the turn
  ended **while the job kept running** - the queue showed `running: 1` for that job and `done: 1` for
  a `self_check` the keeper had scheduled and completed on its own.
- **Live**: the keeper's first real log lines, catching a genuine outage (the kit's own suite stops
  the console as part of its tests):
  `console=False doorbell=True actions=['rung_doorbell:True'] crons=['healthcheck']`.

## Honest open items

1. `keeper.py --detach` returned success once while the child died before its first sweep, and the
   cause is not yet known; the keeper currently runs as a supervised background process instead. This
   is the difference between "supervised while the operator's shell lives" and "survives everything".
2. A queued task's timeout is the *limb's* timeout: limbs run in-process, so the worker can mark a job
   stalled but cannot kill it. Killing needs the jobs run out-of-process, which is the next step if it
   ever matters.
3. A turn is still bound by the model's own speed - 7 tok/s on this box - so "does not stall" means
   *the work* no longer blocks the turn, not that the model answers quickly.
