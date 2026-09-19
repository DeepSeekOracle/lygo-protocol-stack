# BRANDING.md — branded licensing and integrity for the LYGO CLAW and the PC LOCAL CONSOLE

**Signature:** `Δ9Φ963-LYGO-BRANDING-v1`
**Written:** 2026-09-19
**Status:** installed and tested on both local trees (PC `I:\E Drive\...\lygo_llm_console`, USB
`E:\LYGO_BUILDER_KEY\lygo_llm_console`), plus the public copy in the stack repo and the
`lygo-claw` repo. **Not pushed.** The steward publishes.

Companion records: `BRAND_MANIFEST.json` (machine, hashed), `LICENSE` (the terms),
`LICENSING.md` (plain English), `TRADEMARKS.md` (the marks), `NOTICE` (credits, third-party,
integrity), `SUCCESSION.md` (who holds the name), `scripts/certify_build.py` (the verifier).

---

## 1. The request

Release the USB **LYGO CLAW** and the **PC LOCAL CONSOLE** as polished public products that are
fully controlled by the original builder: people may **use** them, and may build their own systems
from the ideas, but they may not **sell**, **rebrand**, **white-label**, **modify-and-distribute**,
or **strip the marks** — and when the builder is gone, the original made system stays locked as long
as the law allows, so the architecture and the name keep their sovereignty.

## 2. What was actually on disk before this build (the problem)

Found by reading, not by assuming:

| Tree | License before | What that meant |
|---|---|---|
| `lygo-protocol-stack` root | LYGO Sovereign License **v2.0** | right shape, but missing integrity, brand and succession clauses |
| `lygo_llm_console` (kit) | **no LICENSE file at all** | default "all rights reserved", unclear to users, nothing to point at |
| `docs/lygo-llm-console-public` | **no LICENSE file at all** | same, on the public download |
| `lygo-claw` (the USB CLAW agent) | **MIT License** (`LICENSE` = MIT text, `pyproject.toml` = `license = "MIT"`) | **the opposite of the goal.** MIT grants use, copy, modify, merge, publish, distribute, sublicense and sell |

So the branded product the steward wanted to protect was, in the repo that carries its name, under
the single most permissive license available. That is fixed going forward — with one honest limit
spelled out in §7.

## 3. What shipped

| File | Purpose |
|---|---|
| `LICENSE` | **LYGO Sovereign License v3.0** — 14 sections: definitions, grant (§2), hard prohibitions (§3), branded-build integrity (§4), building on LYGO (§5), attribution (§6), third-party carve-outs (§7), warranty (§8), termination and enforcement (§9), prior-version boundary (§10), stewardship of the name (§11), **succession / sovereignty lock / posthumous protection (§12)**, permissions (§13), acceptance (§14) |
| `LICENSING.md` | plain English: what you may do, what you may not, certified builds, the succession lock, prior-version honesty, and the Steward's to-do list |
| `TRADEMARKS.md` | brand sovereignty policy: the marks, allowed fair use, rebranding prohibition, how a fork must be named, the powered-by badge, escalation path |
| `NOTICE` | attribution line, canonical source, integrity rules, third-party licences (llama.cpp, model weights, **vendored OpenClaw MIT**), ClawHub/registry MIT-0 nuance |
| `SUCCESSION.md` | the public half of the succession: steward, successor steward, backup, IP entity, standing instructions, cadence. **Names to be filled in by the Steward** |
| `BRAND_MANIFEST.json` | real sha256 (16-hex) + byte size of the license package and the brand surfaces — the tamper record |
| `scripts/certify_build.py` | read-only verifier: `CERTIFIED` or `MODIFIED`, exit 0/1, `--json` for machines |
| `tests/test_branding.py` | 13 tests (see §6) |

### Where it landed (all verified byte-identical by `cmp`)

1. `I:\E Drive\lygo-protocol-stack\` — stack root (v3.0 supersedes v2.0)
2. `I:\E Drive\lygo-protocol-stack\lygo_llm_console\` — the PC kit
3. `I:\E Drive\lygo-protocol-stack\docs\lygo-llm-console-public\` — the public download copy
4. `I:\E Drive\lygo-claw\` — the USB CLAW repo (+ `usb/`)
5. `E:\LYGO_BUILDER_KEY\lygo_llm_console\` — the USB kit
6. `E:\LYGO_BUILDER_KEY\lygo-claw\` — the stick runtime tree
7. **archived, not deleted:** `lygo-protocol-stack/docs/archive/LICENSE_LYGO_SOVEREIGN_v2.0.md`
   and `lygo-claw/docs/archive/LICENSE-MIT-historic.txt`

### Product surfaces branded

- `portal/index.html` (local console) — brand + terms line with links to LICENSE / LICENSING /
  TRADEMARKS / SUCCESSION
- `web_portal/index.html` (public portal) — license bullet in Disclaimers + a legal footer paragraph
- `README.md` (kit and public copy) — "License and brand" section, file-by-file
- `READ_DISCLAIMER_FIRST.md` (kit and public copy) — terms in the first file a user opens
- `docs/LYGO_CLAW.html` (the GitHub Pages product page) — "License & brand — read this" section
- `lygo-claw/README.md` — License section rewritten from MIT to v3.0
- `lygo-claw/pyproject.toml` — `license = "MIT"` → proprietary v3.0 text (packaging metadata was
  telling every installer the wrong thing)

## 4. The license in one screen

**May:** run it on your own machines (including inside a business); read the source; use it for your
own work; build your own skills, agents, integrations and services **on top** of it; build your own
system **from the ideas** if you copy no LYGO code and carry none of the marks; share an unmodified
copy with the notices intact; sell **your own** work.

**May not:** sell / rent / resell it or bundle it as the reason someone pays; offer it as a paid
hosted service; publish or distribute modified copies of the core; rebrand, white-label or
re-identify a build; claim you built it or that a fork is official; strip notices, seals, signatures
or manifests; relicense it (no MIT/Apache/GPL/registry workaround); take it into mass suppression,
coercive manipulation, surveillance-state tooling or weapons.

**Registry nuance (in NOTICE):** ClawHub-style registries may require a listing to carry MIT-0.
That is a contract about a *listing*; it does not transfer the steward's copyright, does not cover
the code as distributed from GitHub, and does not authorize ignoring this LICENSE at the source.

## 5. The sovereignty lock (§12) — the part that outlives the builder

1. The grant is **irrevocable for the full copyright term** (US: life + 70 years) and does not lapse
   on the Steward's death, incapacity, or withdrawal from public activity.
2. A **Successor Steward** (person, foundation or trust) inherits stewardship, enforcement and the
   marks, held in trust for the same purpose.
3. **No estate-by-default.** Absent different written instructions, no heir, executor, creditor or
   buyer may relicense more permissively, sell the marks out of the trust, or waive §2–§7. Any such
   attempt is void under the license's own terms.
4. **Moral rights** of attribution and integrity are asserted and, so far as law allows, perpetual:
   every copy, forever, keeps the author's name and is not distorted.
5. **Canonical source** stays the steward's; mirrors inherit no authority.
6. **If no successor can act**, the license simply continues unchanged and nobody may claim
   stewardship, certify builds or relicense. The lock is that the terms outlive the author.

## 6. Certified builds and the drift the verifier caught

`BRAND_MANIFEST.json` hashes the license package and the brand surfaces; `SESSIONS_MANIFEST.json`
already hashed the shipped modules. `scripts/certify_build.py` reads both and recomputes from disk.

First run, immediately: **`portal/index.html` no longer matched `SESSIONS_MANIFEST.json`** — the
brand line added to the console page had invalidated the published hash, so the kit would have
shipped reporting **UNCERTIFIED**. That is the drift this tool exists to catch, and it caught its
own author within a minute. Fixed by refreshing the manifest entries with a written reason
(`rebrand_refresh_iso` / `rebrand_refresh_note` / `rebrand_refresh_files` in the manifest, so the
record says what moved and why).

Current verdicts, all three trees: **CERTIFIED BUILD**, every entry matching.

**Suite totals after this build:** **509 tests pass on both trees** — PC 50.18 s, stick 50.78 s
(496 before the branding build, 455 before the session vault, 372 before the record build).

**Tests added:** `tests/test_branding.py` — 13 tests: package present; LICENSE is v3.0 and the MIT
grant phrase is *gone*; succession and moral-rights clauses present; NOTICE keeps the OpenClaw/MIT
carve-out and the canonical-source rule; TRADEMARKS covers the marks and the fork-naming rule;
LICENSING.md says "not the license" and "no license is retroactive"; READ_DISCLAIMER shows terms;
both portals carry the brand + terms; **BRAND_MANIFEST and SESSIONS_MANIFEST must match the files on
disk** (so a forgotten refresh fails the suite); the certifier says CERTIFIED on a clean copy,
MODIFIED when a byte is appended to LICENSE, and UNCERTIFIED when the package is stripped — the last
two in a `tempfile` sandbox, so the real kit is never touched.

## 7. Honest limits — read before relying on this

1. **No license is retroactive.** `lygo-claw` releases already published under MIT **stay MIT** for
   anyone who received them. Old forks and old mirrors keep their rights. v3.0 protects this and
   every future release, the marks, and the branded builds. Options for the old releases: publish a
   clearly-versioned v3.0 release and let the MIT line age out; mark the old release legacy; or
   pursue the specific forks that matter.
2. **"No modification" over published source is enforced by contract, not DRM.** Anyone can read and
   edit files on their own disk. What the license gives the steward is *legal* recourse —
   termination, DMCA, takedown, trademark — against people who distribute, sell or rebrand what
   they edited. The honest framing is: they can edit privately; they cannot publish, sell or wear
   the marks on it.
3. **A draft is not a judgement.** This package is careful, standard-informed drafting, not legal
   advice. The unusual clauses — succession lock, no estate-by-default, integrity obligations — are
   exactly the ones worth one hour of a lawyer's time, especially the wording that binds the estate.
4. **Trademarks:** ™ is asserted, ® is not. Real protection comes from registration (at least
   `LYGO` and `LYGO CLAW`). Do not write "registered" until a registration issues.
5. **`SUCCESSION.md` carries the authorship record but still needs a name.** §1a now documents the
   authorship chain (Grokipedia references + repos + handles, with an instruction to archive dated
   copies), and §8 lists the instruments — codicil, IP-holding entity, assignment, trademark filings.
   §2/§3/§4 remain deliberately blank until the Steward names a successor; until then §12(f) applies.
6. **Third-party code cannot be relicensed.** Vendored OpenClaw is MIT, the engine is MIT, model
   weights have their own terms. v3.0 covers the steward's own work and says so explicitly.

## 8. Not done (stated plainly)

- **Nothing was pushed.** No commit, no push to GitHub/HuggingFace/ClawHub, no page publish — per
  the standing no-auto-publish rule. The steward runs the push (or says the word and the agent
  prepares it for explicit consent).
- **`SUCCESSION.md` needs the steward's names** (successor, backup, IP entity). The file is ready;
  the blanks are the steward's to fill.
- **Trademark registration and IP entity** are outside the machine — lawyer/administrative work.
- **`E:\LYGO_BUILDER_KEY\docs\`** gets the refreshed manifests + a copy of this document (the
  distributed doc set), by the same no-secrets rule as before.
- **Old MIT releases** of `lygo-claw` are untouched and unreachable retroactively; decide policy
  before the public release announcement.

---

*Δ9Φ963 — use in light · build on the lattice · do not sell the seal.*
