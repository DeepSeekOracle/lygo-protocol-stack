# Plan — a full Python limb and a full Rust limb for the console agents

Recon done 2026-09-21. The contract, exactly as the console already has it:

- `src/limbs.py`
  - `_SHELL_DENY` (line 26) — the deny regex shared by `shell` and `python_exec`.
  - `EXTRA_SCHEMA` (line 33) — the limb specs the model sees (`shell` 36, `python_exec` 37).
  - `canonicalize(name, args)` (156) — argument aliases; line 124 maps `python_exec` -> `code`.
  - `_win_env()` 195, `_ws()` 202, `_kill_tree()` 208.
  - `_run_capture(argv, timeout=, cwd=, env=) -> (rc, out, err, timed_out)` (229) — the one runner.
  - `extra(name, args)` (258) — dispatch: `shell` at 268, `python_exec` at 285.
- `src/tools.py` — `TOOLS_SCHEMA` (42), `DENY_SUB` (28), `dispatch()` (366); calls `limbs.extra()`.

## What already exists
`python_exec` — runs a snippet in the workspace and captures stdout/stderr. Not yet "full": no
explicit interpreter choice, no argv, no exit-code/stderr report, no artifact listing.

## What to build
1. `python_exec` (full)
   - `code`, optional `argv`, `timeout`, `cwd`, `interpreter` (default: the console's own python).
   - Report `returncode`, `stdout`, `stderr`, `timed_out`, and the files it wrote into the workspace.
   - Keep `_SHELL_DENY` refusal and the existing one-line result shape.
2. `rust_exec` (new)
   - `code` (a single-file program) or `crate` (a cargo project name under `workspace/rust/`).
   - Resolve `rustc`/`cargo` via `shutil.which` then `%USERPROFILE%\.cargo\bin`.
   - Single file: write under `workspace/rust/<slug>/main.rs`, `rustc -O` to a binary, run it.
   - Cargo: `cargo run --quiet` in the project dir.
   - Report `returncode`, `stdout`, `stderr`, `timed_out`, compiler diagnostics verbatim.
   - If no toolchain: `{"ok": false, "error": "rust_missing", ...}` — never a traceback.
   - Refuse anything `_SHELL_DENY` would refuse; run inside the workspace only.
3. Tests first (RED), in `tests/test_limbs_python_rust.py`
   - python: argv reaches the program; non-zero exit is reported not raised; timeout kills the tree;
     a refused snippet stays refused; stderr is captured separately.
   - rust: the toolchain is detected; the version call answers; a missing toolchain fails soft;
     a compile error returns diagnostics (not a traceback); a real program prints its result.
4. Register, then prove
   - `EXTRA_SCHEMA` + `canonicalize` + `extra()`; `python -m pytest tests/ -q`;
     `scripts/refresh_manifests.py`; `scripts/certify_build.py`.

Measured on this machine: `rustc 1.93.1`, `cargo 1.93.1` at `C:\Users\justi\.cargo\bin`,
`C:\Python313\python.exe`, `python 3.11.11`.
