# Security notes — lygo-llm-console v1.6.0

## What changed in this release, and why

Findings from the v1.2.0 scan, and what 1.6.0 does about them:

| Finding | Cause | Fix in 1.6.0 |
|---|---|---|
| AE1 "referenced artifact was not completely inspected" (x2, HIGH) | `SKILL.md` referenced `kit/lygo-llm-console-public.zip`, which a scanner cannot fully read | the kit ships as an unpacked tree; no archive is referenced or shipped |
| AE3 "text artifact contains embedded NUL bytes" (x2, HIGH) | binary test fixtures (`tests/fixtures/tiny.gguf`, a fake CAS blob) inside that zip | `tests/` is not shipped on ClawHub; those fixtures are generated at test time anyway, and the site build carries the suite |
| SSRF1 "cloud metadata access" (HIGH) | `src/web_tools.py` named a link-local metadata address and concatenated a metadata hostname inside its **deny** list | both literals deleted in the console source; the numeric link-local rule and the `.internal` suffix check already covered them, and `tests/test_web_tools.py::test_block_link_local_and_internal` now proves it |
| install-mechanism concern | the shipped BAT was hardcoded to the steward's own path, so it could run code outside the verified kit | the kit carries the console's drive-portable launcher (`%~dp0`), which runs the folder it was unpacked into |

## Declared, not implied

- Loopback only by default (9641 portal, 11441 engine). LAN bind requires `--lan --i-consent`.
- Outbound `https` GET only, to public hosts. Loopback, RFC1918, link-local, `.local`, `.internal`
  refused by range and suffix.
- Writes inside the kit (`workspace/`, `save/`). Desktop/Documents/Downloads/home writes via
  `save_note` require explicit consent and report an absolute path read back from disk.
- The kit spawns the pinned `llama-server.exe` and local `python -c` / `cmd.exe /c` snippets.

## The honest limit

`shell`, `python_exec` and `rust_exec` are **arbitrary local code execution as your user**, gated only
by metacharacter rules and the LYGO P0 policy checks (which refuse OS-wipe and credential-read shapes).
Treat the kit as code you chose to run, and run it unprivileged. Do not describe these limbs as a
sandbox, and do not expose the console to an untrusted network or an untrusted user.

## Steward data

The kit is built from the console tree by `tools/build_clawhub_llm_console_kit.py`, which copies an
explicit include list and rewrites the steward's absolute paths in the copy only — refusing to build
if a pattern it expects has moved, and refusing to ship if any forbidden path or key shape survives.
`kit/PUBLIC_KIT.json` records which files were patched and which were left out.

Report a problem: <https://github.com/DeepSeekOracle/lygo-protocol-stack/issues>
