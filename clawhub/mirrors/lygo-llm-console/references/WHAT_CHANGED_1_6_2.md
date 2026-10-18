# What changed in 1.6.2 (console 1.5.8)

1.6.1 answered the scan report in prose for three items and declined two others. This release
changes the two that were declined, because a finding that stays open is a finding a reader has to
take on trust. Every change below is small, and each one is stated with the trade-off it costs.

| scan item | what it was | what changed in 1.6.2 |
|---|---|---|
| A.I.G T09, `kit/src/server.py:2212` — *"automatic URL prefetch exposes privileged local tools to indirect prompt injection"* | `host_prefetch` fetched any URL in the user's text **before** the model answered, and put the fetched page in the same context as the shell and python limbs. It was on by default. | **The default is off.** `LYGO_HOST_PREFETCH` must be `1`/`true`/`yes`/`on` for a prefetch to happen at all. Nothing is fetched on the agent's behalf unless the operator asked for it. |
| SkillSpector CRITICAL, Data Flow, `kit/src/chat_loop.py:748` — *"tainted flow: `req` from `os.environ.get` → `urllib.request.urlopen`"* | the local lyrics limb built its request URL by re-reading `LYGO_LLAMA_PORT` from the environment, bypassing the validated port in `paths.py`. The scanner read that as a credential-shaped environment value reaching a network sink. | **the request uses `paths.LLAMA_PORT` and nothing else** — an int already range-checked to 1..65535 by `_port_from_env`, with a junk value falling back to the default. No environment string enters the URL. |
| static analysis `suspicious.dynamic_code_execution`, `kit/src/modules/host.py:527` — `spec.loader.exec_module(module)` | a workspace limb is a plugin, and loading one executes code | **the loader is confined**: the adapter path is resolved (symlinks followed) and must lie inside the modules directory this host was given, must be a regular file, and its path and SHA-256 are recorded before the load. A `catalog.json` entry can no longer point at `../../save/uploads/x.py` or at a symlink that leaves the kit. Loading code is still loading code; what changed is which file is allowed to be it. |

## What each change costs, said plainly

**Prefetch off by default** means the small local models get less live context out of the box: paste
a link and the model reads the URL as text, and must choose to fetch it with `web_fetch`. That
choice is a tool call, and tool calls pass the P0 gate. To get the old behaviour back:

```
set LYGO_HOST_PREFETCH=1
```

or in PowerShell `$env:LYGO_HOST_PREFETCH = "1"`, then start the console. On the USB stick the same
line goes in the launcher. This is the documented work-around, and it is the operator's call: with
it on, a page someone else wrote shares a context with a shell that runs as your user.

**The confined loader** refuses an adapter that resolves outside `src/modules/`. A module the
operator drops into the kit by hand belongs in `src/modules/<name>/backend.py`, which is where the
catalog expects it anyway; a module symlinked in from another drive is now refused with the reason,
and the rest of the console keeps running (`REFUSED <mid>: adapter resolves outside the modules
directory (...)` in the module list).

**The lyrics limb** is unchanged in behaviour. The port it talks to is the same port; it is now read
from the one place that validates it.

## What is still true, and not a bug

- `shell`, `python_exec` and `rust_exec` execute code as your user. That is the product: a local
  agent that can act. Run it unprivileged and do not expose it to an untrusted network.
- A cloud brain configured by the operator sends the operator's key to the operator's endpoint.
  Where that key lives is a product decision; 1.6.2 does not move it.
- Chats, notes, indexes and scheduled jobs persist inside the kit folder until the folder is
  deleted. Nothing is uploaded, and nothing expires by itself.

## Verification

- `python scripts/verify_kit.py` — 152 files, every SHA-256 checked against `kit/KIT_SHA256SUMS.txt`
- `python scripts/self_check.py` — package gate, including "manifest matches the kit" and
  "claw.json console_release matches kit/VERSION"
- the loader was exercised against a real module (loads), a path outside the kit (refused), a
  symlink escape (refused) and a missing file (refused)
- `LYGO_HOST_PREFETCH` was exercised unset (off), `1` (on) and `0` (off)
