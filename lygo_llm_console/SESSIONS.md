# LYGO LLM Console — the session vault (as built)

**Signature:** `Δ9Φ963-LYGO-SESSIONS-v1` · **Written:** 2026-09-19 (MDT) · **Steward:** Justin Helmer / Lightfather
**Status:** installed and tested on both local installs · not yet boot-verified on the stick

This is the build record for the **session history / continuity vault**: what was built, what it
touches, the evidence it works, the defects found while building it, and what is left to do.

---

## 1. Why it exists

The console had a **New session** button whose only job was to wipe the chat. The conversation was
gone from the window, and the operator's only copy was whatever the browser still held. The record
module (`compaction.py`, `Δ9Φ963-LYGO-COMPACTION-v1`) already kept a live journal of every turn, but
nothing **filed** a finished conversation: there was no dated folder, no title, no index, and no way
to find a chat again three weeks later.

The request, in the steward's words: *"we have a new session button that wipes the chat… that chat
needs to be saved and able to be referenced or even re visited if necessary… we need to implement a
full module for human and AI to use for long term session continuity and vaulting… clear cataloging
of folders, sub folders and files."*

So: **a small live window, a complete record, and a catalogued vault.** Two layers now:

| layer | module | job |
| --- | --- | --- |
| live record | `compaction.py` | journal every turn as it happens; fold what left the window; seal what is finished |
| **long-term vault** | **`sessions.py` (this build)** | **file a finished conversation as a dated, labelled, indexed, ZIP-verified session; find it, read it, name it, reopen it** |

The vault sits **above** the record. It never rewrites the journal and never deletes anything.

## 2. What is on disk

```
save/
  sessions/                                   (unchanged: the live record)
    journal-<sid>.jsonl                       every turn, verbatim, stamped
    current.json                              the browser's window
    session-<epoch>.json                      legacy 40-message copies (pre-vault)
    compaction_state.json                     the record's state
  vault/                                      (new: the catalogued vault)
    catalog.jsonl                             machine index — append-only, one line per session
    CATALOG.md                                human index — regenerated from catalog.jsonl
    2026/
      09-September/
        20260919-141200-ccec-hello-there/     folder = <session-id>-<title-slug>
          session.json                        the manifest: title, tags, note, span, counts, verify
          transcript.md                       readable: OPERATOR / AGENT, every turn, stamped
          turns.jsonl                         verbatim turns, exactly what the journal held
          digest.md                           the thread, in the operator's own words
          session.zip                         the four files above, CRC-verified on write
```

**Naming is the point.** The folder starts with the **session id** (the stable key, so every lookup
is a prefix match and a shorter id can never answer for a longer one) and ends with the **title slug**
(so a human browsing the tree can see what the folder is): `legacy-1789675102-hello-what-model-are-you`.
Months are numbered (`09-September`) so a plain alphabetical sort is also a chronological sort.

## 3. The rules this module holds to

1. **Nothing is ever deleted.** Filing *copies*. The journal stays where it was, the legacy file
   stays where it was. A session can be filed twice — the catalog line is replaced, not duplicated.
2. **The catalog is append-only; the readable catalog is regenerated.** `catalog.jsonl` is the truth
   and is only ever appended to or edited in place; `CATALOG.md` is rendered from it at any time.
3. **A title is derived, then editable.** The first thing the operator said, trimmed and slugged —
   never a bare timestamp. `label()` replaces it with whatever the operator or the agent chooses.
4. **A filed session carries a digest.** `digest.md` is built without an LLM call (no drift, no
   stall): the opening question, then what the operator asked, in order.
5. **Everything has a safe wrapper.** `safe_*` entry points answer `{"ok": false, …}` instead of
   raising. A broken vault must never cost a boot, a turn, or a console.
6. **The vault never blocks a new session.** `continuity.new_session()` files first, then wipes — and
   if filing throws, the wipe still happens.

## 4. The surface

### Module (`src/sessions.py`)

| function | what it does |
| --- | --- |
| `vault_live(reason, title=None)` | file the conversation in progress (called before a wipe) |
| `vault_session(sid, title, tags, note, reason, source)` | file a named session; idempotent |
| `adopt(limit=300)` | import everything not yet filed: dormant journals + legacy `session-*.json`, read-only towards the sources |
| `catalog(limit, q, tag, month)` | the catalog, newest first, with tag counts |
| `find_session(sid)` | resolve an id to its folder (or an unfiled journal / legacy file) |
| `open_session(sid, chars)` | read one back: manifest, transcript (bounded head+tail), messages, paths |
| `label(sid, title, tags, note, pinned)` | name / tag / annotate; files an unfiled session first |
| `search(q, k)` | titles, tags, notes first, then inside the transcripts |
| `resume(sid, file_current=True)` | reopen a filed session in the console (see §6) |
| `stats()` | what is filed, what is not, where it all lives |
| `rebuild_catalog_md()` | re-render the human catalog |

### Routes (`src/server.py`)

- `GET /api/sessions` — the catalog. `?stats=1` summary · `?sid=<id>&chars=` read one back ·
  `?q=` filter titles/tags/notes · `?search=1&q=` search inside the transcripts
- `POST /api/sessions` — actions: `catalog`, `stats`, `open`, `vault`, `vault_live`, `adopt`,
  `label`, `search`, `resume`, `rebuild`, `transcript`; anything else is refused with `bad_action`
- `POST /api/session {"new": true}` — now returns `vault: {sid, title, reason}`: **where the
  conversation that just ended was filed**

### Limbs (`src/limbs.py`, offered to the model)

`session_list` · `session_open` · `session_search` · `session_label` · `session_resume`
— the agent uses the same functions the operator's panel uses. `session_label` with no `sid` labels
the conversation in progress. `session_open` returns the transcript, not the raw message array.

### The operator's panel (`portal/`)

Under **Session vault** in the left rail: a list of filed sessions (title · turns · date · tags · zip
size), a search box (titles/tags first, then transcripts), **File this chat**, **File old history**
(adopt), **Refresh**, and per-session **Reopen in chat** and **Name / tag**. The panel is painted from
the server every time — it never guesses.

## 5. The flows

1. **New session pressed** → `continuity.new_session()` → `sessions.vault_live("new_session")` files
   the journal (manifest, transcript, turns, digest, verified zip, catalog line, `CATALOG.md`) → the
   chat is wiped → the route answers with the folder that now holds it.
2. **File this chat** → the same filing without ending the conversation (the manual save button).
3. **File old history** → `adopt()` walks the dormant journals and the legacy `session-*.json` files
   and files them, tagged `recovered`, with the import noted in the manifest. Originals untouched.
4. **Find** → catalog filter; if nothing matches the titles/tags, the panel searches the transcripts.
5. **Read** → `open_session()` returns the transcript (bounded head+tail, never silent truncation:
   the file path is in the answer) plus where it sits on disk.
6. **Reopen** → see §6.
7. **Automatic** → the record's own triggers (checkpoint every 8 turns, fold at 78 % of the budget,
   seal past the journal caps) keep running underneath; the vault is the long-term layer on top.

## 6. What "reopen" actually does

`resume(sid)`:

1. **Files the conversation being interrupted** (nothing is lost to reopening something else).
2. Loads the chosen session's messages back into the console's session file, so the portal shows the
   thread again.
3. Installs that session's **digest as the carry** and records the lineage in the record's state:
   `resumed_from`, `resumed_iso`, `carry`, `carry_turns`. This is what gives the agent continuity
   **without** re-sending every old turn into a window that cannot hold them.
4. Starts a fresh live journal under a new session id, so the reopened thread and the old one stay
   separate in the record — the old one keeps its folder and its zip.
5. Reads the state back and reports `lineage_error` if the lineage did not survive. A lineage that
   does not survive the write is not a lineage.

## 7. Evidence (this host, 2026-09-19)

| | PC install | USB stick install |
| --- | --- | --- |
| kit root | `I:\E Drive\lygo-protocol-stack\lygo_llm_console` | `E:\LYGO_BUILDER_KEY\lygo_llm_console` |
| tests | **496 OK** (47.9 s) | **496 OK** (50.5 s) |
| new session tests | 35 unit + 6 over real HTTP | same files, hash-identical |
| vaulted on first run | **21 sessions · 214 turns · 43,163 bytes of zip** | **2 sessions · 60 turns · 2,695 bytes of zip** |
| recovered legacy | 20 (1 skipped: `session-1789704230.json` held 0 messages — nothing to file) | 1 |
| live conversation filed | 102 turns, title *"hello there"* | 56 turns, same title |
| vault files on disk | 87 | 12 |

Every zip is verified on write: the archive is reopened, every member's CRC checked, and
`turns.jsonl` compared byte-for-byte with the file on disk before the session is called filed.

Test suites: `tests/test_sessions.py` (35: filing, naming, finding, adopting, reopening, and that a
broken vault cannot cost the console) and `tests/test_record_e2e.py` +6 (the panel's routes over real
HTTP, in a sandbox — a test never files into the operator's vault).

## 8. Defect ledger (found while building, all fixed)

| # | defect | how it showed | fix |
| --- | --- | --- | --- |
| 1 | The record's state schema keeps **only the keys it declares**, so `resumed_from` and `last_vault` were written and then silently dropped on the next read | resume lineage vanished; the "where did my chat go" report was always empty | declared `last_vault`, `resumed_from`, `resumed_iso` in `compaction._default_state()`; `resume()` now reads the state back and reports `lineage_error` |
| 2 | `digest.md` was a **26-byte stub** — `compaction.build_carry()` reads rollups, and a conversation filed straight out of the live window has none | a session reopened from the vault would have arrived with **no context at all** | `_digest_for()` builds the thread from the turns when the carry is empty; used for live *and* recovered sessions; zipped with the rest |
| 3 | The panel's **Find** box and the route disagreed: `?q=` returned search hits while the panel rendered `sessions` | searching a phrase inside a transcript rendered "no session matches" | `?q=` now filters the catalog, `?search=1&q=` searches the transcripts, and the panel renders both shapes and falls back to the transcript search when nothing matches |
| 4 | A test would have written into the operator's real vault (the e2e harness redirected the record's dirs, not the vault's) | — | the e2e harness now redirects `sessions.VAULT`, `continuity.CURRENT`, `continuity.SESSIONS` into its sandbox |

## 9. If the vault breaks

`server.py` imports the vault inside a `try` and falls back to a stub that answers
`sessions_unavailable` to every call; `continuity.new_session()` wraps its filing in a `try` and
wipes the window regardless. Proven by `test_a_broken_vault_answers_instead_of_raising` and
`test_new_session_still_wipes_the_window_when_the_vault_is_broken`. A broken vault costs the vault —
not the console.

## 10. Not done / next

1. **Boot-verify the stick** against this build (the PC side has been booted and is known good).
2. **Migrate the flat archive into the vault layout.** Sealed zips from the record layer still land
   in `save/archive/<sid>.zip`. The vault catalogs them but does not move them; a `seal → vault`
   hand-off (seal writes straight into `<year>/<month>/`) is the next integration step.
3. **The stick's pre-vault `current.json`** (held only by the console window, no journal) is preserved
   as a legacy `session-<epoch>.json` when the first new session is started, and `adopt` files it then.
4. Nothing here pushes to GitHub, HuggingFace or ClawHub. Distribution is by file copy, as before.

---

*Δ9Φ963-LYGO-SESSIONS-v1 · built on the console that was already working, without breaking it.*
