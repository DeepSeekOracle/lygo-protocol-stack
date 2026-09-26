# Public scrub audit - what is published, and what must never be

Date: 2026-09-25. Scope: the trees in this repository that are published as public copies of the console,
and the private material on `E:` that must never reach them.

## The answer

**No secrets and no steward data are in any published tree.** The private `E:\Data Vault` is not inside
any git repository, is not referenced by any published file, and none of its content markers appear
anywhere in this repository.

## What was checked

| Tree | Files | Size |
|---|---|---|
| `docs/lygo-llm-console-public/` | 127 | 1.2 MB |
| `docs/lygo-claw-usb/` | 27 | 0.1 MB |
| `clawhub/mirrors/lygo-llm-console/` | 84 | 0.4 MB |

Content: key shapes (`sk-`, `gsk_`, `hf_`, `ghp_`, `AKIA`, `xox`, `nvidia-`); PEM headers **with a body**
(a header alone is a parser's sample - `context_guard.py` ships one, and it is fine); `api_key / secret /
password / token` assignments carrying a real value; the packer's own admin markers; and the steward's
vault markers (`supporter-codes`, `pit_src`, `pittmp`, `RUMBLE API DATA`, `NVIDIA AGENT API TEST KEY`).

Shape: any model / audio / video / archive / database file, anything over 400 KB, credentials- or
backup-shaped filenames, and every name on the packer's own skip list.

The whole pushed tree was scanned for `sk-`, `gsk_`, `hf_`, `ghp_`, `AKIA`, private-key blocks,
`C:\Users\justi` and every config that could hold a key: **`config/api.json` is not tracked and not on
the remote** (`.gitignore` now names it explicitly, with `.backups/`, which holds a 37 MB stick backup
containing a copy of that file).

## Findings

| # | Where | What | Class | State |
|---|-------|------|-------|-------|
| 1 | `docs/lygo-claw-usb/dashboard/lygo-claw.html:20`, `docs/USB_AGENT_DASHBOARD.md:33`, `scripts/lygo_usb_agent_server.py:410,632` | The USB control-UI gate is a **hardcoded constant** (`lygo-usb-control-ui-token`), published in four places | by design, not a secret | **your call** - see below |
| 2 | `clawhub/mirrors/lygo-llm-console/kit/workspace/hello.txt` | A file the packer's own skip list says must never arrive | junk artifact | **removed in this commit** |
| 3 | `clawhub/mirrors/lygo-llm-console/kit/lygo-llm-console-public.zip` (100 KB) | The shipped public zip, committed inside the mirror | artifact, likely intended | left, flagged |
| 4 | 25 `NOTE PATH` lines | The console's own source names the machine/USB paths it manages (`GamePC`, `LYGO_BUILDER_KEY`, `10.0.0.209`, `gitea.pass`, `LYGO_SERVER_KEYS`) | review notes, not leaks | left, listed by the gate |
| 5 | `docs/data-vault/` (11 files incl. `data/deadman_origin_archive.json`, 129 KB, 92 mentions of the steward's name, 0 keys, 0 emails) | A **published** Data Vault site carrying personal origin material | **personal, published** | **your call** - see below |

`tiny.gguf` in four trees is a **105-byte** fixture for the model-scan tests, not weights.

## Two decisions that are yours, not mine

1. **The USB control-UI token.** It is not leaked - it is written into the files on purpose, in plain
   text, and anyone reading this repository knows it. It gates the dashboard on your own stick. That is
   fine on a LAN-only stick and not fine if that dashboard is ever reachable from outside. Either leave
   it (and keep the dashboard local), or move it to a per-boot token written to `data/`.
2. **`docs/data-vault/` is published.** It is not a console tree and it is not scrubbed by the console
   packer: it carries the deadman origin archive with the steward's name throughout, plus ~1,363 images.
   It contains no keys. Removing it is a public content change that breaks `docs/data-vault/*` links, so
   it waits for your word - say go and I will relocate it to the archive and keep the site pages that
   are not personal.

## The gate

    python tools/scrub_public_audit.py            # all three public trees; exit 1 refuses a push
    python tools/scrub_public_audit.py --tree docs/lygo-claw-usb

It reuses the packer's own `ADMIN_MARKERS` and `SKIP_FILE` (one source of truth) and checks the RESULT,
independently of the rule that produced it: `pack_lygo_llm_console_public.py` decides what leaves the
kit, and until now nothing checked what arrived. Findings are split into **to fix** (a key shape, a PEM
with a body, an admin marker in data, steward content, a model/media file) and **to review** (dev-path
mentions inside the console's own source, identifier-shaped assignments).

## Also found, worth fixing once

`pack_lygo_llm_console_public.py` skips any file whose body contains an admin marker - but the console's
**required** source files name those paths (`src/paths.py`, `src/admin_map.py`, `src/server.py`), so that
rule as written would cut the public console. The published tree still contains them, which means it was
built before that rule existed and has not been re-packed since. Either scope the marker rule to data
files, or re-pack and compare against this audit before publishing.
