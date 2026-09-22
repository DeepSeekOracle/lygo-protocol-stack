# What this console can actually do, locally — capability log

Written 2026-09-21 because the question was the right one: *which of these jobs can this machine do at
all, which need a better model, and which need the console to stop depending on a model.* Three separate
answers, and conflating them is how a system ends up promising work it cannot finish.

## 1. The three jobs you named

| job | can this machine do it? | how, today | what is actually missing |
|---|---|---|---|
| **git push** | **Yes.** git 2.47.1.windows.2 present. Not blocked: the limb layer's refusal lists are paths (`I:\LYGO_SERVER_KEYS`, tokens, `save/logs`, `C:\Windows`, `Data Vault`) and destructive shell commands (`format c:`, `diskpart`, `bcdedit`, `shutdown`, `iex`). Neither mentions git. | `python_exec` (120 s budget) or `shell` (25 s, and it refuses `\|&><\`$` metacharacters). Credential pointers already exist: `gitea_admin` -> `I:\LYGO_SERVER_KEYS\gitea.pass`. | A **git limb** — one call that stages, commits, pushes and returns the remote hash it verified. `python_exec` works but leaves the sequence to the model, which is exactly the thing measured to be unreliable. |
| **build a PDF properly** | **Yes, today.** reportlab 5.0.0, jinja2 3.1.6, markdown 3.10.1, requests 2.34.2 all import. | `python_exec` with reportlab — real typeset PDF, not a text dump. | A **document limb** (markdown/html -> PDF) so the console runs it on the host the way it now runs file writes, instead of trusting the model to pick `python_exec`. |
| **build a website and push it to git** | **Yes, in pieces.** File writing works (verified on disk by the gauntlet), jinja2 for templates, git for the push. | `save_note` for each file + `python_exec` for git. | A **scaffold limb** (write a small site tree from a template, then optionally commit+push). And a policy decision: the kit's standing rule is **no automatic push** — the operator's word is the gate. |

**Verdict: none of the three is blocked by capability.** All three need the same thing — the work moved
onto the host, where it is deterministic — rather than a smarter model calling limbs in the right order.

## 2. What is on the box (the model vault, `I:\LYGO_MODELS\`)

| file | size | what it is for |
|---|---|---|
| `gemma4-12b.gguf` | 7.38 GB | the current brain. Chosen for **image generation** — that was the test. |
| `gemma4-12b-mmproj.gguf` | 0.18 GB | its vision projector (image input). |
| `qwen2.5-coder-7b.gguf` | **4.68 GB** | **a tool-using coder model, already here** — the switch you are asking about. |
| `nomic-embed-text-latest.gguf` | 0.27 GB | embeddings for the RAG/recall index. |

The coder is smaller than the vision model, so it costs *less* to run, not more. The console's
`config/console.json` already carries `scan_roots` and `prefer_by_ram`, so model choice is a config
matter, and `#brain-local` / `#brain-api` already switch brains at runtime.

## 3. What is proven, and what is not

**Proven, measured, on disk:**
- gemma4-12b unaided: **5/12** on graded tasking. Reliable at single-step work; it *can* call the right
  limb (it called `save_note` twice, correctly, for the multi-file task) but will not do so to order.
- gemma4-12b assisted by the console: **11/12** (confirmed on a re-run after the last fixes). The
  six-point gap was closed by making the console deterministic - host-run writes, host-run listings,
  the ladder as backstop - not by asking the model to improve. The single remaining failure is T6,
  and it is the model's: it will not chain a read into a write.
- It does not chain: read-then-write failed in **every** run, including the assisted ones.
- It is **non-deterministic**: the same task passed one run and failed the next on identical code.
- It reports refusals honestly (it told the operator our own consent gate had blocked it).

**Not proven — do not assume it:**
- `qwen2.5-coder-7b` has **not been run against these tasks**. It is the right candidate on paper
  (purpose-built for code, tool-calling template), and it is on disk, but no number exists yet.
- No git push, PDF build or site scaffold has been executed end-to-end through the console by *any*
  model. The tooling is present; the loop is untested.
- The API chain (DeepSeek -> NVIDIA -> Gemini -> Groq) has not been run against this task set either, so
  there is no local-vs-API comparison number yet — only the local baseline.

## 4. What to do with this

1. **Two brains, chosen by task** — not one model for everything. `qwen2.5-coder-7b` for coding, tooling
   and building; `gemma4-12b` for vision and images (that is what it was selected for, and it has the
   projector). The console already has the runtime switch; the missing piece is choosing per turn.
2. **Run the same gauntlet against the coder** before believing anything about it. `scripts/gauntlet_agent.py`
   exists precisely so this is a number rather than an opinion.
3. **Then add the three limbs** — git, document, scaffold — each host-run and each returning a receipt
   read back from disk. Determinism where the model is unreliable, which is the pattern the whole
  10/12 was built on.
4. **API for the ceiling, local for the floor.** The API chain proves what the *task* looks like when it
   goes right; the local model proves what this machine can hold without it. Both numbers, side by side,
   or neither is worth much.
