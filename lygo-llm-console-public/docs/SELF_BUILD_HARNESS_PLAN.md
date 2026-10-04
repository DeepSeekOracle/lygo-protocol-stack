# Self-build harness: giving the console the limbs to fix, check and rebuild itself

Written before the code, per this kit's practice. Defect hooks: `docs/DEFECT_LEDGER.md`.

## What the console already has

67 limbs advertised globally: `read_file`, `write_file`, `edit_file`, `list_dir`, `find_files`,
`glob_files`, `shell`, `python_exec`, `rust_exec`, `self_check`, `workspace_map`, `p0_gate`,
`sessions_*`, `skill_*`, `clawhub_*`, `memory_*`. That is enough to *describe* a fix.

## What it cannot do - the four gaps

A limb that cannot run its own tests cannot verify a change it just made; one that cannot seal
cannot publish that change; one that cannot restart cannot pick it up; one that cannot install a
toolchain cannot escape a missing dependency. Asked to install a linker, the on-box agent answered
"I do not have the administrative permissions ... to install system-level dependencies." That is
only half true: `rustup target add x86_64-pc-windows-gnu` is a **user-space** download that needs no
administrator. What it actually lacked was a limb and the operator's consent.

| Gap | Limb | Changes the system? |
|---|---|---|
| cannot check itself | `self_test` | no writes; runs the kit's own suite |
| cannot seal a change | `self_seal` | writes manifests - **consent required** |
| cannot restart onto a change | `self_restart` | rings its own doorbell - **consent required** |
| cannot install what it lacks | `toolchain_install` | dry-run by default - **consent to apply** |

## Rules these limbs follow

1. **Consent, in the kit's own language.** `--i-consent` gates the kit's system-changing scripts;
   these limbs take `consent: true` and otherwise refuse with `error: consent_required` plus a hint.
   `toolchain_install` is **plan-only unless consent is passed** - the same posture as
   `src/repair_paths.py`, which prints a plan and refuses to write.
2. **A whitelist, never a command string.** `toolchain_install` accepts an action name, not a
   command line: `check`, `rust_gnu_target`, `pip`, `winget`. Package ids are validated against
   `[A-Za-z0-9._-]`, so the limb cannot be talked into arbitrary shell.
3. **Bounded work.** Paths resolve under the workspace or the kit; `self_test` accepts a test name
   under `tests/`, never an arbitrary path; every run is timeout-guarded and kills its process tree.
4. **The local schema is the point.** A limb the on-box brain cannot see does not exist for it
   (defect 103). All four join `CORE_NAMES`, and the schema cap becomes a measured **character
   budget** rather than a bare count, because characters are what a small model actually pays.

## The loop this closes

`read_file` / `edit_file` a fix -> `self_test` proves it -> `self_seal` certifies it -> `self_restart`
loads it. Today the console can take the first step only; the operator has to do the other three.

## Proof required before this is called done

- Each limb green in `tests/test_self_build_harness.py`.
- The consent refusals green (no writes, no installs, no restarts without consent).
- `self_test` runs a real suite file and reports real counts.
- The local schema still fits its budget with the four limbs in it.
- **Live**: the running console calls `self_test` and reports the kit's own numbers.
