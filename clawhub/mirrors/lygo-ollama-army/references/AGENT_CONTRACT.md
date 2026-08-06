# Ollama Army — Agent contract v0.7.0

Read `SECURITY.md`, `SECURITY_AUDIT.md`, and `SKILLSPECTOR_AUDIT.md` first.

## When to use

User explicitly asks to run **Ollama army**, **joy-loop-pulse**, **champion-egg-boot**, lattice cron, or queue a **reviewed** task JSON.

## When not to use

Generic “summon champion” or “run bots” without local Ollama + stack path confirmation.

## Forbidden without explicit user request

- Enable `planting`, `self_tune`, `social_publish`, or privileged roles  
- Set `LYGO_ARMY_AUTONOMOUS` / `LYGO_ARMY_FULL_CAPACITY` / seed flags  
- Run `start_army_full_capacity.ps1`  
- Write queue task files unreviewed  
- `git push` / HF / ClawHub / social publish  

## Before stack-touching roles

1. Confirm `LYGO_STACK_ROOT` points at a **trusted** `lygo-protocol-stack` clone.
2. Tell user which role runs and whether it mutates config or stack.

## Queue tasks

Agents **propose JSON only**; user approves before file is written to `ollama_queue/` or `ollama_command_center/tasks/`.

## Preferred entry

`python ollama_army_launcher.py` (in-process). Do not recommend full-capacity PS1 unless user accepts OS process spawn.

## QUARANTINE

If stack root missing, bootloader fails, or merkle mismatch → stop; do not retry with `--no-verify`.