# BUILD NOTES — Δ9Φ963 · LYGO Local Agent Console

The release number lives in **`VERSION`** (line 1; optional human tag on line 2). Bump that one file and the
console header, `/api/health` and the runtime facts the model is told all move together — see
`src/version.py` for why that file exists (the release used to be stamped in three places that could
disagree).

Two installs, one code base:

| | PC LOCAL | USB CLAW |
|---|---|---|
| kit | `I:\E Drive\lygo-protocol-stack\lygo_llm_console` | `E:\LYGO_BUILDER_KEY\lygo_llm_console` |
| launcher | `LYGO_LLM_CONSOLE.bat` | `LYGO_AGENT_STICK.bat` (root shim `LYGO_CLAW.bat`) |
| ports | console 9641 / engine 11441 | console 9651 / engine 11451 / embed 11452 |
| default model | `gemma4-12b` (vision) | `llama3.1:8b` (text, from its own CAS) |
| its own storage | vault `I:\LYGO_MODELS` | `E:\LYGO_BUILDER_KEY\product\models\ollama` |

---

## 1.5.3 — the lyric sheet speaks the engine's own language

**What the engine actually accepts, from its own code** (`inference/gradio_server.py`):

```python
def split_lyrics(lyrics):
    pattern = r"\[(\w+)\](.*?)\n(?=\[|\Z)"
    segments = re.findall(pattern, lyrics, re.DOTALL)
```

Three consequences, and they decide the whole shape of this release:

* **One section per `[tag]`, and the tag is one word.** `[VERSE 1]` does not match this pattern at all -
  to the engine it is not a section, it is invisible. The operator's own sheet (`THE DEPARTURE LOUNGE`,
  four numbered verses) would have rendered as *nothing*. `[verse]` is a section.
* **Anything before the first `[tag]` is discarded** - so a header block is safe to write, and is
  read-only to the singer. Not so for `ARTIST:` / `ALBUM:` / `BEAT DIRECTION:` lines written *among* the
  words: those are sung. The `#` comment rule is what separates the two.
* **Genre, mood, instruments, voice and timbre do not belong in the lyrics at all.** They go in the
  style text beside the box - the app's own words: *"e.g., instrumental, genre, mood, vocal timbre,
  vocal gender"*. The engine ships its training vocabulary for exactly those five axes in
  `wav_top_200_tags.json` (~200 tags each), and the console now reads that file rather than guessing
  genre names.

**What the box shows by default.** `template_text()` - the engine-shaped sheet, with a `#` comment
header the operator fills in (`SONG`, `ARTIST`, `STYLE`, `BEAT`, `VOICE`, `NOTE`) and six singable
sections. `STYLE:` is read *out* of the header: press **make it singable** and it lands in the style box
on its own, so the operator writes his direction once.

**The sheet toolbar** (above the words, not in the number row): `template` puts it back, `clear` empties
it, `make it singable` re-cuts a sheet written in another shape, `check` says what is wrong *before* a
render is spent, `agent writes it` and `surprise me` fill it in.

**`convert` and `check` are actions on `POST /api/music`** and neither one writes anything: no gate, no
render, no card change. A refusal or a typo costs the operator nothing. `check` refuses out loud:
no words, no sections, header lines that would be sung, more sections than the engine sings.

**`[VERSE 1]` folds onto `[verse]`.** `_TAG_FIXES` always knew `verse1`, but the lookup ran before the
space was stripped, so `"verse 1"` never hit it and came back as the unknown tag `verse1`. A numbered
verse is the operator's bookkeeping, not a section type.

**Comment lines are read, never sung.** `#` and `//` lines are stripped before any plan is made, so the
header can ride in the same box as the words. This also fixed a real hazard: the old parser promoted
"words before the first marker" into a first verse, which would have **sung the ARTIST/ALBUM header**.

**The agent writes into the box.** One turn, off to the side: the writer's instruction
(`WRITE_FORMAT` - the rules stated once, next to the engine contract they come from) goes to
`/api/chat` with `stream: false`, on whichever brain the operator has selected, with whatever they
typed in the composer as the brief (or an invented one, or a random style built from the engine's own
tag vocabulary for `surprise me`). The reply is cut to the sheet - fences, titles and sign-off prose
are removed, because the engine would sing them - and then it is **checked**, so the operator sees
`written and clean: 6 sections (intro verse chorus verse chorus outro)` rather than a promise.

**Tests:** `tests/test_music_template.py` (18) runs **YuE's own regex** over what would be sent and
asserts the result is what the operator meant - the template, the numbered verse, the converted sheet,
and that no comment line reaches the singer. The engine's pattern is the contract; our parser does not
get to have an opinion.

**The debug pass on this same release found four more, all fixed and all verified live:**

* **The payload builder would have SUNG his own tags.** `_lyrics_text` recognised only bare
  `[verse]`-style markers, so a sheet written `[VERSE 1]` fell through to the untagged path and those
  bracket lines became lyrics. It is now built by `music_lyrics.singable()` - from the plan itself, so
  the words that render and the section count the operator was shown cannot disagree.
* **The last section of every song was being dropped.** The payload ended without a newline, and the
  engine's splitter only ends a section on a newline: a song written with 7 sections arrived as 6, the
  closing chorus being the one that vanished. Guarded by tests at the render boundary.
* **The cost line quoted the wrong engine.** `msEngine.onchange` (the engine switch) was silently
  replacing the estimate's own handler, so switching engines left the previous engine's number on
  screen - which is how the studio came to promise hours on this card for an engine with no adapter and
  no weights. The estimate's listeners are `addEventListener` now (a property can be overwritten, a
  listener cannot), and an engine that cannot render says so instead of lending it the other one's rate.
* **A sheet that changed in code never told the panel.** `value =` fires no event, so with the
  engine's template sitting in the box the line still read "no sections yet - write the words below".
  One `input` event from a single place (`msSheetChanged`) now covers the prefill, the template, clear,
  convert, restore and the agent's draft.

Also fixed: the engine dropdown read **"Stable Audio - declared (declared, not usable yet: ...)"** -
the server's note already opens with the state word, so it is said once now.

**Two more the suite itself caught, on the way to closing the version:**

* **Closing a version is a release step for the module that shipped with it.** `lygo.musicctrl` pinned
  `requires.console >=1.5.2` while its own test demands the manifest floor *equal* the shipped version,
  so the 1.5.3 bump turned it red. The floor is `>=1.5.3` - bump it in the same change as `VERSION`.
* **The suite was filing its own consoles' sessions into the operator's store.** Nothing set
  `LYGO_SAVE_DIR`, so a green run moved `save/sessions` from 386 files to 412 - the operator's own
  complaint (useless session info) being written by the tests. `tests/conftest.py` now points the whole
  run at a temp store at import time, before any test module can import `paths`, and says so on the
  session line. Verified: 217 module tests ran and the real store stayed at 412/292. A deliberate
  inspection of the real store opts back in with `LYGO_TEST_REAL_STORE=1`.
* **The identity block overran its own budget on a FRESH store - the case that ships on the stick.**
  Isolating the store (above) turned that up: with every Δ9 seat enabled at once the block composed
  16,561 chars against its 16,500 ceiling, while a used store fitted at 16,390. `prompt_catalog`'s cap
  was the whole budget for the ENABLED SKILLS section, and at 1,500 it covered a used store but not a
  fresh one; the seating rows also each repeated "Enable to align the agent with this seat." The
  sentence is said once now and the cap is 1,000. Both stores compose **16,390** chars - the block no
  longer depends on how empty the store is. Costs nothing at runtime: the rows are the agent's map to
  the seats, and the "… N enabled; skill_list for the rest" pointer already tells it what to call.

**State at close (2026-09-25).** `VERSION` / `LYGO_BUILD` **1.5.3**; cache-bust
**`?v=20260925sheet6`** (2 references in `portal/index.html`); `lygo.musicctrl` floor `>=1.5.3`;
`refresh_manifests.py` reports 0 entries pending; `certify_build.py` answers **CERTIFIED BUILD** - BRAND
11/11, SESSIONS 11/11, 10 modules validated against the contract, licence signature intact; the suite is
**1516 passed / 0 failed / 46 subtests in 253 s**, with the operator's store left at 412/292 because the
run no longer writes into it. Probe console on 9699 shut down; `music_engine: yue` untouched. The console's
own defects from this pass are logged in `docs/DEFECT_LEDGER.md` rows 130-138, including the one a fresh
install would have hit: **the USB edition is the next build, and a fresh store is the configuration this
release was hardened for.**

---

## 1.5.2 — the Song studio gets depth, and the take list becomes a list

**The complaint, in the operator's words:** *"the Song studio still needs more depth so its not
squished … the scroll for the songs i can only se one song … you have lots of room why are you giving
be a cramed mini suite? build it so i can use it"*

**Depth is now the operator's call.** The band opened at a flat `max-height: 26vh` while its content
measured 234px, so anything thicker than that lived behind a scroll inside the band. It now opens at
`clamp(19rem, 32vh, 30rem)` with a 15rem floor **and carries `resize: vertical`**: dragging its
bottom edge makes it as deep as the operator wants (up to 62vh), and the shell yields the room.

**The take list showed one song for a mechanical reason, not a data one.** Every row painted a native
`<audio controls>` bar - about 54px of band height per take - under a `max-height: 6rem` cap, so the
list was one take plus a scrollbar. Rows are compact now: a `play` button that drives the (hidden but
real) `<audio>` element, the name, the facts, `get` to download, and `again` to put that take's own
style and seed back in the boxes. One take plays at a time, on purpose. The cap is gone - the list
takes the height its rows need and scrolls past that.

**The number boxes are the engine's contract, which is why they were unusable.** `3000 tokens` is
about 30 s of song; nobody wants to do that arithmetic to hear their own words. So the band now
carries length picks (`~30 s` / `~60 s` / `~2 min` / `from the words` plus `seed die`), a style
datalist of ten starting points, and a live line saying what the current words and numbers will
BECOME: sections, seconds of song, and what that costs on the engine selected right now.

**Why the estimate is the panel's own arithmetic and not a server field:** the server has no
per-input plan endpoint, and inventing one would set a second source of truth beside the engine's own
log. The line is labelled `~` and is derived from the engine's documented rate (1000 tokens ~ 10 s)
and the render cost measured on this card (1500 tokens = 3850 s at profile 3), the same facts the
tooltips already carry.

**Driven live, not just described** (probe console on 9697, `getBoundingClientRect` +
`elementsFromPoint`, two sizes; every number below is measured, none of it is intent):

- a lyric sheet of `[verse] / [chorus] / [verse]` reported `3 sections -> ~1:30 of song · ~6.4 h on
  this card at profile 3`; the `~2 min` pick wrote `sections=4, tokens=3000` and the line followed;
  `from the words` cleared the box back to the sheet's own count; `seed die` rolled `0 -> 865324579`.
- the sizes, after the correction below: working area `main` **736px** (the chat column 736, its log
  544 **scrolling inside itself**, the rail and aside 736 each with their own scroll); the studio band
  **640px** with its lyric sheet 493px and its take list 457px - **11 compact take rows fit** where the
  old 6rem cap fitted one; the control strip 165px; the modules at the foot of the page.
- the page is genuinely long and scrolls: the transcript, the rail, the aside and the take list each
  scroll inside themselves, and the page scrolls between SECTIONS (chat -> studio -> controls ->
  modules). The fixed media dock is cleared by `body { padding-bottom: 5rem }` (verified: modules
  bottom 502, dock top 569).

**The correction that mattered more than any of it.** The first pass still kept the shell at
`height: 100vh`, so it tried to buy room by capping things - which is exactly what produced a 192px
chat column, a 12rem aside and a 235px studio to begin with. The operator's verdict: *"now you have
made the left box too small, the chat box too skinny for depth and the right scroll bar too small...
THE WHOLE PAGE SCROLLS MAN WHY ARE YOU MAKING THIS HARD?"* The page scrolling was never the problem.
So: `.app-shell` is `height: auto; min-height: 100vh`; `main` is a definite 46rem (each column scrolls inside itself), `#log` 34rem, the
studio 40rem (lyric sheet 20rem, take list 14rem) and `resize: vertical`; the fixed media dock is paid for with `body { padding-bottom:
5rem }` instead of by shrinking the shell; and every ladder rung that capped a working box (band caps,
`main { min-height: 12rem/14rem }`, the header's 42vh cap, the strip's 7rem cap) is deleted. The page
scrolls; every box has a real height; the studio and the modules are at the bottom where they belong.

**Two traps worth the ink, because they are what made this hard:** a `1fr` grid row inside an
auto-height grid resolves to its CONTENT size, so `main { min-height: 46rem }` plus
`grid-template-rows: minmax(0, 1fr)` still measured **5,243px** - the fix is a definite `height` on the
container. And a textarea with no cap (`#np-body`, an ID, not the `.np-body` class the first fix
targeted) grew to its whole note, 4,743px, which stretched every column of the working area to match.
Both were found by measuring, not by reading the CSS.

## 1.5.1 — the controls leave the header, and the Song studio leaves the sidebar

**What the operator gets.** Scan drives / Boot LLM / the brain switch / the API row and the health
readout are now one bar at the foot of the window: **under the chat's composer, above the module
strip, always on screen**. The header is the brand block. The Song studio, the rail and the chat
column gain every pixel those bars used to take, and on a short window they are no longer pushed
below the fold at all.

**Why it was worth moving — measured, not inferred.** The bars carry selects, inputs and buttons, so
stacked in the header they wrapped into ~500px of chrome above the working area. At 1264x569 the
header measured 606px, `main` landed 37px below the fold, and the opaque module strip painted over
the studio's box — three hit tests inside the studio landed on `llm-*` elements instead. 1.5.0 could
only patch that by capping the header at 42vh and letting it scroll inside itself
(`@media (max-height: 58rem)`), whose own comment admitted *"a known limit of the stacked header, not
of the strip"*. This is the structural fix: the bars are `<section id="controls-strip">`, a fixed row
inside the one-viewport shell, so the shell stops overflowing and the cap is belt-and-braces on a
three-line brand block.

**No id moved, so no contract moved.** `#scan`, `#models`, `#select`, `#tools`, `#brainbar` and its
five controls, the `#api-*` row and `#health` keep their ids, their labels and their order inside
their own bars — the script reaches every one of them by id, and the change is markup + CSS only. The
cache-bust moved with the sheet: `?v=20260925studioband2` on `style.css` and `app.js`.

**The correction.** The operator asked for the SONG STUDIO's controls under the chat box and above the
modules, and the first cut of this release moved the HEADER's bars instead and left the studio where it
was. Their words: "you have the studio controls CRAMMED into a side bar... i cant even use it". So the
studio is now a band of the shell in its own right - a sibling of `main`, directly under the chat box,
above the control strip and the module strip - laid out as a two-column grid: the lyric sheet gets the
tall cell on the left (the engine sings exactly what it is handed, so that is where the operator's work
lives), and engine, numbers, Generate/Cancel and the finished-song list stack on the right. It keeps
its ids, so `app.js` needed no change at all; the aside keeps Trace and Notepad. The band is
`flex: 0 0 auto` with a `max-height` - NOT `0 1`, which let the flex column shrink the band to 71px while
its grid still needed 296px, so the lyric sheet painted straight over the control strip (measured, and
the reason the band's own height and its content height are both checked now).

**What it measures, live, at the sizes the operator uses** (band height / its content height, and the
primary controls hit-tested with `elementFromPoint`):

| window | studio band | lyrics | main | Generate | lyrics select | the aside |
|---|---|---|---|---|---|---|
| 1440x1000 | 235px (content 234) | 694 x 296 | 320px | reachable | reachable | Trace + Notepad |
| 1440x900 | 235px (content 234) | 694 x 296 | 304px | reachable | reachable | Trace + Notepad |
| 1280x800 | 235px (content 234) | 612 x 296 | 204px | reachable | reachable | Trace + Notepad |

Band == content means nothing inside it is hiding behind a scroll, and the band's top edge lands exactly
on the composer's bottom edge: the studio is literally under the chat box. The lyric sheet is 694px wide
where the sidebar gave it ~260px. **The chrome pays for the band, not the transcript**: below 1024px tall
the city list goes, below 928px the control strip is capped and scrolls inside itself, and below 704px the
shell grows and the page scrolls (measured at 1264x569: the studio is reached by scrolling, the composer
is not) - never the chat column, which was down to 32px of transcript in the first cut of this layout.

**The comments were part of the change.** A CSS comment that described a seven-bar header is a lie
the moment the bars leave, so the shell, `main`, the short-window block, the phone block and the
module strip's opacity rationale were all rewritten to say what the layout now is.

---

**The bug this pass found, and it was this build's own.** The bounds refusal added earlier checked the
values AFTER `music_lyrics.plan()`, and `plan()` normalises a token budget into a legal one - so
`max_new_tokens=200` came back as 300, the check passed, and a real engine was booted to sing it. The
refusal could therefore never fire, and this kit's own test suite rendered a song on the operator's
card (MEASURED: `workspace/audio/songs/20260925-161909_a-style`, `gradio_server.py --profile 3`,
14.3 GB resident, 329 CPU-seconds) before it was caught and killed. The same "normalised before it is
checked" mistake was hiding in `ml.sections_for_seconds()`, which returns at most MAX_SECTIONS and so
can never answer "is this too long for you?" - the seconds ceiling is now derived from the app's own
unit (1000 tokens = 10 s) with integer ceiling division.

**The request is what is checked, not the plan.** A value outside the engine's own sliders is refused
by name before any boot - `tokens_out_of_range`, `sections_out_of_range`, including a song longer than
the engine can sing (once silently shortened to 10 sections and rendered as a different song than the
one asked for). All in milliseconds. `tests/test_music_limb.py` now installs a spawn guard in `setUp`
that raises if `_start_server` is reached at all, so "a refusal costs nothing" is a fact the tests
prove rather than a claim they make.

## 1.5.0 — the engine room moves into the console, and a song exists

**What the operator gets.** A *Song studio* panel inside the console's own page (`portal/index.html`,
`app.js`, `style.css`; ids `ms-*`): pick the engine, type the style and the lyrics, set segments /
seed / tokens, press Generate, watch the engine's own progress line, press Cancel. Finished songs
appear under it as players that stream through the kernel's media route. Nothing needs the engine's
own Gradio page any more.

**One new module, wired like the others.** `lygo.musicctrl` (family `ctrl`, catalog order 80) is the
actuator: `GET /api/music` answers the whole studio state, `POST /api/music` takes `start` / `cancel` /
`engine`. It owns exactly one thing — `save/music`, the engine choice and one record per render —
written through atomicio behind the p0 gate. Host load: 10 modules, 0 refused.

**A render no longer blocks a turn.** `src/music_jobs.py` runs one job at a time in a worker thread,
answers `start` at once, reads its progress line out of the engine's own log, and cancels by killing
the engine process tree (the process holds the card; the thread does not). A job record says what
really happened; a kit that has never rendered says that instead of showing an empty list.

**Switching engines is real, and refused honestly.** Three are declared — **YuE** (installed: app, its
own python, all 6 weight files, 20 GB), **ACE-Step** (installed and wired as of the full-song pass
below: 11.45 GB of checkpoints and its own one-shot CLI), **Stable Audio** (app and python on disk,
checkpoints present under a scrambled repo name, no adapter in this build). `set_engine` refuses an
undeclared id (`unknown_engine`); a render for an engine with no adapter is refused by name
(`engine_not_wired`) rather than quietly rendered by a different engine. `installed` requires an
adapter: a select that says "usable" while the render refuses is the contradiction this rule exists to
prevent.

### The full-song transition — two engines, and the words decide the sections

**The reason every render was 15 seconds.** The engine's unit of song is a *section of lyrics*: its own
`split_lyrics()` matches `[tag]` markers, and `run_n_segments` is the "Number of Sequences (paragraphs in
Lyrics)" slider, 1..10. Plain lyrics carry no markers, so they parse to **zero** sections — and the
studio posted `run_n_segments=1` regardless. The render was wired, test-green and always one section.
`src/music_lyrics.py` is the missing system: it keeps the operator's own `[verse]`/`[chorus]` structure or
gives plain words the structure of their stanzas (a repeated stanza is the chorus, both times), emits the
engine's exact format, and states the length that follows. Its load-bearing test runs the ENGINE's own
regex over what it writes. The panel's section field now starts EMPTY, where 0 means "one section per part
of the words" — a 1 in that box capped every song at fifteen seconds.

**A song gets time proportional to its sections.** `music_timeout_s` is ONE section's budget; a
six-section job used to be killed after a sixth of the render. The budget is per section, capped at a day.

**Progress is read from the engine's own words.** `stage_progress()` reads `Stage 1: Generating Sequence 3
out of 6` out of the log — the LAST such line, whatever stage it belongs to, because the engine interleaves
its two stages per section (preferring any stage-2 line froze the display on section 1 for hours). The
running job record carries it, so hours of "rendering" cannot be mistaken for a hang.

**ACE-Step 1.5 turbo is the second engine, and it is the fast one.** Installed at
`C:\pinokio\api\acestep.git\app` (11.45 GB of checkpoints: turbo DiT, 5 Hz LM 0.6B, Qwen3 text encoder,
VAE), driven by its own one-shot CLI whose stdout IS the contract — `@@ACESTEP_PROGRESS@@` stage lines and
one final `@@ACESTEP_RESULT@@`, human noise on stderr. MEASURED: **30.0 s of 48 kHz stereo in 50.1 s of
render**, and on a clean card **180.0 s of song in 110.0 s**. Its own guard allows 600 s of diffusion and
it reports this card holds up to 480 s of audio.

**The first full song is on disk.** `workspace/audio/songs/20260925-150150_song_warm-indie-pop-female-lead-brigh/`
— six sections (`verse, chorus, verse, chorus, bridge, outro`) derived from the words, seed 20260925,
**180.0 s of audio** (the engine's own count: 8,640,000 frames at 48 kHz), 4.3 MB mp3, with the spec it was
made from, its record and the engine's logs beside it.

**Two engines at once do not fit in 8 GB.** A 180 s attempt died with the engine's own message — "GPU ran
out of VRAM or the diffusion loop stalled" — because a test run held the same card. One render at a time is
hardware, and it covers tests: a test that can spawn a real renderer must name its engine and stub the spawn.

**MEASURED, and it matters — a song exists, and it costs hours.** One 1500-token segment at profile 3
on the 8 GB card produced **15.0 s of audio in 3850 s (64 min)**: stage 1 alone was 60 m 41 s, and the
vocoder decode after it ran at 42–783× real time. 1000 tokens ≈ 10 s of audio, so a three-minute song
is a multi-hour render on this box. The panel's token field states that measurement.

**The bug that hid the song.** The engine writes into ITS OWN tree — `<app>/inference/output/…`,
because it runs with `inference/` as its working directory — which is where its own UI has always put
songs (the folder already held the operator's earlier renders). The limb searched only the kit's run
folder, so a render that had just been written and named in the log came back `song_failed`. Discovery
now snapshots and searches both trees and copies the song into the kit's run folder, which the
playlist, the players and the claim machinery all read; the engine's own file is left untouched, and
`engine_output` on the result and in the sidecar records where it really came from.

**Also fixed while proving it** — all three found by tests, not by reading. A finished render could be
recorded as `interrupted` (the worker popped itself from the registry before writing its record; the
two now move together under the lock, record first). A cancel could be overwritten by `done` when a
killed render came back `ok` (the operator's stop now wins, and a file it had already written is named
in the status rather than hidden). An engine's missing *weights* were masked by an
`engine_not_installed` refusal (the app half and the weight half are now separate facts, so the weight
check can name the exact file).

**Status, stated plainly.** A real song file — 15 s, 140 KB, vocal + instrumental mix, seed 963 — sits
in the kit's songs tree and the studio lists it. Its sidecar records that it came from the 12:39 probe
render of this same code path, copied in by the discovery fix: **the full end-to-end path has not been
re-run through the patched code**, which would cost another 64 minutes. `scripts/certify_build.py` runs
clean on this tree (11/11 brand files, 11/11 session files, 10 modules validated).

### The 1.5.0 debug pass — eight defects across both halves, every one found by a probe

Every finding below came out of a harness that boots the console in-process on a free port and asserts
the behaviour over real HTTP, plus a call-counter wrapping the probe function — and, for the panel half,
`tests/js/music_studio_panel.js` (now run by the suite through `tests/test_music_studio_panel_js.py`),
which loads the studio block into a stub DOM and drives it. All eight are pinned by regression tests:
`tests/test_music_studio_debug_pass.py` for the server half, the node harness for the panel half.

**The first four are the server's.**

1. **A song with a space in its name could not be played.** The media route took the name straight out
   of the request path, which is percent-encoded on the wire: `my song (final).mp3` and `café-sång.mp3`
   both answered **404 while the file sat on disk**. A song is a file a human may drop in the folder, so
   the studio listed songs it could not play. The name is now decoded at the HTTP layer that owns the
   encoding — and decoding FIRST is what keeps the traversal refusal honest, because `%2e%2e%2f` becomes
   `../` and is then refused by name rather than joined.
2. **A refused engine switch answered HTTP 200.** `POST /api/music {"action":"engine"}` returned the
   refusal with a success code, while its own sibling `cancel` already answered 409 — a panel that reads
   the status code would show a switch that never happened. A refusal now answers 4xx.
3. **One console poll spawned the GPU probe six times.** The route handler, the strip card and the
   module's own health each ask for the same reading, and `data()` built the card twice on top of that,
   so a single `GET /api/music` ran `music_status` 6× and `engines_state`/`songs` 3× each. At the panel's
   3-second interval that is two nvidia-smi processes a second, forever, for facts that had not changed.
   Only the expensive probe is now held (`music_tools.route_once()`, `READING_TTL_S = 1.5`), and the
   cheap state around it — engine resolution, weights, readiness — is read fresh on every call.
   **That split is itself a fix from this pass:** the first version held the WHOLE status and made a
   caller that had just changed the engine read back a stale answer, which one of the existing cards'
   tests caught within a minute. Measured: 6 probes → 1, and a poll tick 78 ms → 49 ms.
4. **A stop pressed while the engine was still booting killed nothing.** The engine's pid is only
   registered once it is serving, so a cancel in that window found no process, recorded `cancelled`, and
   left the engine to go on holding the card for an hour. `music_generate` now reads a stop flag before
   it posts any work (`mark_stopped` / `is_stopped`), shuts the engine down again, and says so; a cancel
   that had nothing to kill says that too instead of claiming a kill.

**The other four are the panel's — the half no Python test can see, found by an audit that read the
panel against the wire shapes the server really sends.**

5. **A finished render was reported as a failure.** The done branch read `j.song.name`, but the server's
   record carries the song as a **path string** (`_run` stores `str(out["path"])`), so `name` was always
   `undefined` and the operator was told, after a ~64-minute render, *"the job says done but names no
   song, so nothing here is claimed as finished — press Refresh"* — and Refresh could not clear it. The
   panel now reads the path, matches it against the playlist's own `path`/`name` (the object shape is
   still accepted, so a future record is never misread as "no song"), and takes the duration from the
   playlist row. **The harness is why this survived 51 passing assertions:** its fixtures fed the song
   as an object, i.e. the test double carried the wrong contract. Feeding the real shape makes the old
   logic go red on 5 assertions — verified by running the harness against a copy of the old block.
6. **Refusals arrived as a bare code.** The single error path kept `error` and dropped `hint`, and a p0
   refusal dropped `gate.reason`, so an empty lyrics box said `could not start: lyrics_required` instead
   of the remedy the server had already written. Both now reach the operator through `msWhy()`.
7. **The card reading was computed and thrown away.** `route` (the profile chosen, the free VRAM it
   read, who is holding it) and the whole `card` are sent on every poll; the panel used neither, so the
   one question an 8 GB box makes the operator ask before pressing Generate — *will it even fit* — had
   no answer on screen even though the server was paying an nvidia-smi probe to answer it. The idle and
   done lines now carry the server's own `why` sentence verbatim, not a second phrasing of the numbers.
8. **`msSet(text, true)` toggled a class nothing styled.** `.warn` exists only on `.brain-status`, so
   every warning, every refusal and every failed render looked exactly like the muted idle sentence. The
   studio's status line now has its own `.warn` rule.

**Suite state after the pass: 1449 passed, 0 failed**, including the panel harness (it was 1441 passed /
7 failed when the pass started: five of those seven were manifest drift and the two record corrections
below, and the other was a commented-out literal port in `public_gateway.py` that the portability scan
read as code — the comment now names the loopback origin without copying the number).

**Two record corrections this pass, both found by the suite rather than by review.** The studio module
declared `"family": "ctrl"` — but the naming law enforced in the tree knows only `info` and `watch`, and
nothing reads the field for behaviour, so the manifest now carries no family and the module's role lives
in its id (the way `lygo.notepad` does). And `manifest['family']`-style drift: `portal/index.html`,
`src/server.py` and `src/app.js` were edited after the last manifest stamp, so
`refresh_manifests.py --note …` was run and `certify_build.py` re-run to certify the tree again.

**Suite state after the pass: 1449 passed, 0 failed** (it was 1441 passed / 7 failed when the pass
started: five of those seven were the drift and the two record corrections above, and the other one was
a commented-out literal port in `public_gateway.py` that the portability scan read as code — the comment
now names the loopback origin without copying the number).

### The short-window pass — two defects found by driving the real page

The full-song pass was proven on the wire and in the engine's own files, but the page itself had only ever
been exercised in a stub DOM under node. Loading the live console in a real browser (a console of its own on
a spare port, `--mock`, so the operator's own session was never touched) found two things no Python test
could:

**1. The status line contradicted the playlist.** With two finished songs on disk and no job record, the
studio printed `no song rendered yet` directly above them, with working players underneath. The wording was
reporting on the absence of JOB RECORDS while claiming something about SONGS — and a song can legitimately be
written by the limb, by a script, or by an earlier console with no studio record at all. `music_jobs.state()`
now counts the songs and says which fact is actually absent (`2 songs on disk - nothing rendering`, or `no
song rendered yet` when that is true). Three tests pin it, the plural included.

**2. The working area could be buried under the module strip.** Measured at 1264x569: the header stack is
606px tall, so with `.app-shell` pinned at `height: 100vh` there was no leftover for `main`, which landed
37px BELOW the fold. Its whole 320px box fell inside the strip's box, and the strip — opaque by design, and
later in the document — painted over it. Three hit tests inside the Song studio (`elementFromPoint`) all
returned `llm-*` elements instead: the engine picker, sections box and lyrics box could not be clicked at
all. A first attempt at the fix (`body`/`.app-shell` `height: auto; min-height: 100vh` — the phone
treatment, whose width-gated twin already existed) removed the covering but cost the fixed working view: the
page grew to 16,043px and the chat column stopped scrolling inside itself. The shipped fix is the opposite
principle: **on a short window the header gives way, not the working area.**
`@media (max-height: 58rem) { header { max-height: 42vh; overflow-y: auto } main { min-height: 12rem } }` —
the header keeps its text and scrolls inside itself, `main` stays inside the shell, and the strip still
begins exactly at the fold. 58rem is where the header stack plus main's 20rem floor stop fitting on one
screen, so above it nothing changed: verified at 1440x1000 with the header natural, the query not matching,
and the layout identical to before.

**How it was verified, because a screenshot is not a measurement.** At 1264x569, 1440x900 and 1440x1000:
`main`-vs-strip vertical overlap **0**, `main` fully inside the shell, and hit tests inside the studio
landing on `SECTION#ms-studio` / `SELECT#ms-engine` / `TEXTAREA#ms-lyrics` — the pane owns its own pixels
again. The same geometry pass had already cleared the strip of any suspicion: seven module cards, **zero**
sibling overlaps, one card per module stacked in a column that scrolls, exactly as the strip's own CSS
comment intends.

**The cache-bust token moved** to `?v=20260925shortwin` (style.css and app.js). The stale-cache trap is
worth naming, because it bit during the fix: the corrected stylesheet was on disk while the browser kept
serving the old one, and the first re-measurement after the "fix" still showed the broken layout — a CSS fix
that does not bump the token ships to nobody.

### The health poll — a one-second stall the page paid every three seconds

Tuning the route the portal polls most. Measured over HTTP on this box: `GET /api/health` **1,092 ms**,
`GET /api/music` 55 ms. Timing every probe in the health payload in-process found the whole cost in one
line: `foreign_daemon_port_open()` at **1,000.6 ms**, while `_hardware_reading` 0.0 ms, `backends.report`
15.9 ms, `perf.report` 19.6 ms, everything else under a millisecond — and the portal calls this route on
`setInterval(refreshHealth, 3000)`, so a third of a worker thread was spent waiting out a timeout that
could never return anything but `False`.

The probe asks whether a legacy single-port daemon answers on its default port. So the cause is the host,
not the daemon: a raw TCP connect to a **closed** loopback port on this machine fails after **2,007 ms**
with `WinError 10061` instead of refusing instantly, so one `urlopen(..., timeout=1)` could only ever wait
out its full timeout first. A proxy was the first suspect and is not involved (no proxy variables, and
`proxy_bypass` exempts loopback). The fix bounds the "nothing is listening" case with a socket timeout and
holds the answer: a TCP connect at 0.25 s decides whether the HTTP answer is even worth asking for, and the
result is held for `FOREIGN_TTL_S = 20 s` so a 3-second poll pays it at most once per interval. Semantics
are unchanged — when the port *is* open the HTTP answer still decides, so a listening socket that is not
that daemon still reads as closed.

Measured after: probe **1,000.6 → 250 ms** cold and **0.0 ms** held; the whole health payload
**1,135 → 412 ms** cold and **1,093 → 20.6 ms** held; over real HTTP `GET /api/health` **1,092 → 45 ms**
median across ten calls, with `foreign_daemon_port_open: False` still answering correctly. Three tests pin
it in `tests/test_tuning.py` (bounded, held, and the payload is not held hostage), and `forget_foreign_reading()`
exists so a caller can force a re-probe.

**A process lesson recorded the hard way:** the first full suite run of this pass reported 3 failures, all in
`tests/test_branding.py`, and all three were the manifest refresh landing *while the suite was running* —
`refresh_manifests.py` rewrote `portal/index.html`'s hash mid-run. Re-run on the frozen tree: 13 passed.
Freeze the tree, refresh the manifests, then run the suite; never the other way round.

### The stall pass — five waits that could only ever end early on paper

The same host fact turned up five more times: **a connect to a closed loopback port on this box fails after
~2,007 ms (`WinError 10061`)** rather than refusing instantly, so any probe with a longer timeout just waits
out its whole budget to answer "no". Measured before → after, against a definitely-closed port:

- `engine._health` (two attempts) **4,162 → 1,001 ms** with the boot loop's `timeout=0.5`, so a boot-loop
  iteration went **7,004 → 4,002 ms** and readiness is noticed up to 3 s sooner. The default stays 2.0 s for
  the one caller that must not mistake a busy engine for a dead one (the runner reuse check).
- `backends._health_ok` **2,000 → 750 ms**, `music_tools._reachable` **1,500 → 600 ms** — both poll loops
  whose own deadline still governs how long they wait in total.
- `model_check._wait_health(port, 0.1)` **3,005 → 101 ms**: worse than slow, it was wrong — a flat
  `timeout=3` per attempt was only checked *between* attempts, so a 0.1 s budget overran 30×. Each attempt is
  now bounded by what is left of the budget, so the number passed in is the number honoured.
- `_port_free` (0.4 s) left untouched: already bounded, and "no HTTP answer" is a different question.

Every one is a poll loop, so a smaller per-attempt budget buys responsiveness, not a shorter patience. Each
site carries the measurement and the reason in its own docstring.

**The suite's one flake, and it was not a ghost.** The frozen-tree run came back **1 failed / 1,486 passed**,
in the pictures-off route test: `ConnectionAbortedError: [WinError 10053]` client-side while the server
logged `503`. It passes 3/3 alone, so it was ordering- or load-dependent — but the mechanism is real: this
route's early refusals (403/503/429) answered **without reading the posted body**, and a socket closed with
unread data is a reset, not a refusal. The kit already had exactly this policy (`http_body.drain`, defect 27)
and used it in the too-large branch; `_post_image` now drains before every refusal via `_drop_body`, and the
pin is on the rule rather than the race: `test_a_refusal_reads_the_body_it_is_refusing`.

### The engine's own sliders are the contract — a bound refused *after* boot

The first end-to-end run of YuE's multi-section path (two sections, through the studio's own worker) came
back `song_failed` after 91 s, and the real error existed only in the engine log:

    gradio.exceptions.Error: 'Value 200 is less than minimum value 300.'

YuE's `gradio_server.py` declares `max_new_tokens` as `Slider(300, 6000, step=300)` and its sequences slider
as `Slider(1, 10)` — the engine's own UI is its input contract. Gradio enforces both in its preprocess, which
runs *after* the engine has booted and pinned ~10 GB of weights, so the operator pays a full boot to learn a
number was out of range. The limb now reads those bounds itself and refuses by NAME before spawning anything:
`tokens_out_of_range` / `sections_out_of_range`, the range in the hint, answered in milliseconds. Two tests
pin it, one of them asserting the refusal does not boot the engine.

## 1.4.0 — the console can make a song

**Released 2026-09-25.** Pictures and voice were wired; a song was not. An operator who asked for a
song got prose about one, because no limb existed to make one — the console could draw and could
speak and could not sing.

A song is now a limb, `music_generate`, wired the same way the picture limb is wired: registered in
`limbs.py` (schema, canonical keys `style` + `lyrics`, alias pool so a model reaching for "genre" or
"words" is served instead of refused, dispatcher branch), offered to the on-box brain in
`tools.CORE_NAMES` and the core schema (**39 of the capped 40**, schema still under its char budget
in `test_tool_battery.py`), described in the runtime facts, and driven from the host path in
`chat_loop.py` so "write me a song about the lattice" makes a song rather than a poem about one.

**The engine is the one already on this machine** — YuE (the YuEGP fork), lyrics and style tags in,
a sung stereo track out. It is harnessed where it lives and never copied into the kit: no weights
are redistributed, nothing is downloaded, and a machine with no engine is told so by name
(`no_music_engine`) together with the config key that fixes it. `music_root`, `yue_root`,
`music_engine`, `music_timeout_s` and `music_profile` join `config/console.json` in full sentences,
the way every other key there is documented.

**The engine is driven one-shot, and MEASURED, because the obvious entry does not work.** The fork
ships a command-line entry (`inference/infer.py`) that reads `args.sdpa` and never declares
`--sdpa` — it cannot start at all. So the limb starts the app's OWN server on a free port, waits for
it to really serve, posts the job, reads the result, and terminates it in a `finally`: the same
one-shot service shape `image_see` uses for llama-server, and nothing left listening afterwards. The
watch card checks for a leftover engine process, because that rule is only real if something checks it.

**The job payload was measured too.** Gradio silently requires a placeholder for the trailing
`gr.State` the server owns: a 10-slot body answers `ValueError: An event handler (generate_song)
didn't receive enough input values (needed: 11, got: 10)` — no song, and nothing in the message
saying why. It is 11 slots with a null state, and that is now commented where it happens.

**The route is chosen from the live card reading, and reported.** A card with room renders on the
fast quantized profile; a card the chat model holds renders with offload. Every result carries the
route it used and the reason, so a slow song says why it was slow.

**A song is a file claim, exactly like a picture.** The claim machinery (`CLAIM_PICTURE`, the
drawn-trace checks, `surface_artifacts`) is extended to songs: "I generated the song" with no render
behind it is caught, and the answer names the path the limb really wrote. Building this found a bug
in the older code of the same family, and it is fixed: a limb that RAN and FAILED was being filtered
out by an `ok or path` test, so a dead render was reported to the operator as "nothing was written"
with the engine's own error and remedy thrown away. A failed render now carries its error name and
its hint to the person who asked.

**Two cards join the strip**, the same info/watch pair as memory and guard:

* `lygo.musicinfo` — the facts. Which engine this machine reaches (and the search order, so "not
  found" is a claim about a named search), every declared weight file by name and size, the route a
  song would take right now, and the last song really written with its length, seed and profile read
  back from the file and its sidecar. "No song rendered yet on this kit" is a true fact and stays
  green, the way an empty vault does on the memory card.
* `lygo.musicwatch` — the faults. Engine, entry script, its python, every weight file by name with
  the remedy, the model cache, **whether the on-box brain is actually offered the limb** (a limb
  missing from `CORE_NAMES` is invisible to the local model while the source says otherwise — the
  fault no human can see), the dispatcher branch, the songs folder, the audio tools, a leftover
  engine process, and past runs that logged an engine and produced no audio *each with the log line
  it died on*. It fixes nothing, downloads nothing, deletes nothing: its own test scans its source,
  by AST, for write calls.

**Measured while building, and pinned in tests:** a live render read as a *failed* one until the
watch card required a run's engine log to be **quiet** before calling it dead — calling a working
engine a failure is the same class of lie as calling a missing file done.

Carried from 1.3.2: the CPU picture engine travels inside the package (`tools/sd-cpu`),
`media_root()` falls back to the kit root so a fresh install draws with no config, and no checkpoint
is redistributed.

## 1.3.2 — the picture engine travels inside the package

**Released 2026-09-24.** The console could draw a picture through `image_generate` since 1.3.1, but only
on a machine that already had an engine somewhere else: the media root was a config key pointing at a
folder the installer never created. A fresh install therefore answered `image_failed` — the software was
complete and the package was not.

This release puts the engine in the package and makes it self-finding.

**What is inside now.** `tools/sd-cpu/` — the CPU build of stable-diffusion.cpp: `sd-cli.exe`,
`sd-diffusion.dll`, the ggml CPU kernels and the image encoders it needs. 20 files, 45 MB, no CUDA, no
card, no Python, no service, no admin rights, nothing on PATH. It is the same engine the steward's studio
box runs from `D:\LYGO_MEDIA`, at 45 MB instead of 1.1 GB of CUDA DLLs.

**What changed in the code, not just in the payload.** `media_root()` (`src/media_tools.py`) falls back
to the kit root when the machine has no media root of its own — a fresh install finds its own engine with
no config file and no editing:

| machine | media root | engine used |
|---|---|---|
| fresh all-in-one install | none configured | the kit's own `tools/sd-cpu/sd-cli.exe` |
| studio PC (`media_root: D:/LYGO_MEDIA`) | declared | `tools/sd/sd-cli.exe`, exactly as before |

The packaged engine is a fallback for machines that have nothing, never an override of a machine that has
something. Four hermetic tests (`tests/test_packaged_engine.py`) build a fake kit on disk and pin both
rules plus the checkpoint path, because a drive-specific assertion would pass on this PC and fail the USB
kit while the USB kit was right.

**No checkpoint is redistributed, on purpose.** They are 4-7 GB and their licences are their authors':
SDXL Turbo is Stability's non-commercial research licence, SD 1.5 is CreativeML Open RAIL-M. So the
package carries the fetcher instead — `tools/sd-cpu/get_model.ps1`, double-clickable as
`FETCH_IMAGE_MODEL.bat` — which pulls from the author's own repo, resumes (`curl -C -`), checks the byte
count, deletes a file that fails the check rather than keeping a bad one, and prints which licence it is
pulling. `-List` shows the choices, `-From <url>` takes your own host.

**Measured, this box** (8 GB card, chat model resident): 512×512 in ~55 s, 1024×1024 in 272-300 s on the
CPU route; 12.5 s on the CUDA build with the card free. Distilled checkpoints are detected by filename
and run at 4 steps, cfg 1.0.

**The release number moved because the bytes moved.** 1.3.1 installers are published and frozen; an
installer that carries an engine is a different package, so it is a different release. Manifests
refreshed with `scripts/refresh_manifests.py --note "..."`.

---

## 1.3.1 — the turn you pay for is the turn you see

**Released 2026-09-22.** The console could always say how fast the engine generates; it could not say how
much of that generation ever reached the operator. It turns out that is where most of a turn's time was
going — and it was invisible to every surface the kit had.

Measured on the PC copy (qwen2.5-coder:7b, RTX 4060 Ti, ngl 99, 16k window), the same two-word ask
`Reply with exactly: CACHE TEST`:

| | before | after |
|---|---|---|
| wall | 2.84 s | **1.03 s** |
| tokens generated | 106 | **2** |
| tokens shown | 6 | 2 |
| unseen | 94% | **0%** |
| reply cap | 4096 | 24 |
| limb schema | 24 tools | none |

The engine's own cumulative counter agreed with the console both times (three turns of 137 tokens each
under the old behaviour; 5 tokens for the whole probe after). Two things were wrong, and neither was the
engine:

- **A pure echo was treated as a task.** "Reply with exactly X" was offered the full 24-limb schema and a
  4096-token budget, so the model answered the clock readout that rides every message and the console
  stripped it: 105 of 106 tokens were text nobody asked for. Now the asked shape is read from the
  operator's own words, the cap is that shape's cost, and a pure echo gets no limb schema at all. A shape
  ask that also names work (a file, a folder, a limb, a URL) keeps every limb — the veto list is what makes
  that safe.
- **A streamed turn was unmeasurable.** The engine reports its timings in the *final* chunk of a stream,
  and only when `stream_options.include_usage` asks for them — so the one path the operator actually
  watches recorded nothing at all. Now it does, and the read stops the instant the asked shape is complete,
  which closes the connection and cuts the generation itself rather than waiting it out.

Published: `last_perf` in `/api/health` (generated, shown, unseen %, unattributed residual, limb calls,
prefill new/cached, wall, and what was dropped), one line per turn in `save/logs/console-<date>.log`, and
in the console itself a "Shown to you" row plus `shown N/M (X unseen, Y%)` on the status line. `LYGO_TURNPERF=0`
puts every turn back exactly as it was, without editing code.

Carried from 1.3.0: every turn filed verbatim into `workspace/memory/conversations/`, the cloud chain,
images both ways, the fabrication detector, the 16384 engine window, straight sampling, and the gauntlet
baseline (9/12 PC, 8/12 USB — T7/T11/T12 are mechanism gaps, not model).

### Shipped as installers (this release)

Four Inno Setup 6 installers were built from the sealed payloads and one of them was installed and booted
before it was called done — details, sizes and the proof: `docs/RELEASE_1.3.1_INSTALLERS.md`. Two
pre-ship fixes came out of that pass: the shipped `scan_roots` now carries `./models` (or an installed
copy boots with no brain), and recovery of this tree's config goes through the sealed canon, not `git`
(the settings only exist in the working tree — ledger 122).

### The standing rule this release establishes

**Every prompt token is paid on every turn.** The identity block is re-sent whole on each message, so a
new watch, panel, digest line or instruction is a *permanent* prefill tax on every future turn — not a
one-off cost at the moment it is added. Budget it against the window and the clock before adding it, and
prefer replacing something over appending to something. The volatile parts of the prompt (the clock
readout, live VRAM, environment watch, session counts) also destroy the engine's prefix cache for every
token after them, which is why `cache_hit_pct` is now published per turn: a warm session should show the
head being reused, and a number that falls is the signal that a volatile line moved to the head.



---

## 1.3.0 — the forever history, the four-provider chain, and both copies signed off

**Released 2026-09-21.** This release is what the PC build has been running since the campaign closed, and
the USB copy now carries it too.

Carried: every turn filed, verbatim and permanent, into `workspace/memory/conversations/` and pointed at
from `MEMORY.md`, with the LYGO RAG recalling trimmed history without a model; the cloud chain
DeepSeek → NVIDIA NIM → Google Gemini → Groq, with the model following the provider on a switch;
images read and drawn both ways, by our own engine and through the API; and answer fidelity — the clock
readout stripped from answers, a failed limb never standing in for the reply, a produced picture named under
it, the walk record labelled with the walk it belongs to, and the completion line naming only the brain that
actually answered.

**Verified:** `1089 passed, 43 subtests passed` on the PC tree, exit 0. On the USB copy: `1080 passed,
9 skipped, 43 subtests passed`, exit 0 — the 9 skips are the PC-build assertions (shipped-config values and
the git checkout above the kit) that a stick cannot satisfy, each printing its reason. `scripts/sweep_build.py`
reports `0 failure(s)` on both trees and `VERDICT: CERTIFIED BUILD` on both.

**Tested on the stick itself:** booted from its own bundled Python on its own ports (banner
`LYGO LLM Console v1.3.0 http://127.0.0.1:9651`), identified itself as `usb_local` from the volume type, ran a
real turn through the calc limb (`17*23` → 391 in 6.9 s, local brain), and filed it verbatim in its own
forever history.

**Open:** the stick has no model blobs of its own — its canonical store `%USB%\product\models\ollama` is
missing (the duplicate CAS was archived to `I:\LYGO_STICK_ARCHIVE\dup_cas_20260918`). It is a cloud-only
console until that store is put back; that is the steward's call. Also carried: the stick still holds key
material (row 61), `src/p3_note.py` is an orphan, vulkan is still b10988, and the photo-price calibration and
the 5,428% window composition remain as recorded.

**Signature** Δ9Φ963-LYGO-LLM-CONSOLE-v1 · LYGO Sovereign License v3.0 · steward LIGHTFATHER
## THE FREEZE RULE — read this before you change anything

**A sealed build is reference only: never edit a sealed build, never build inside one.**
V1 lives in the vault (`D:\LYGO_CANON\`). The vault answers exactly one question — *what can I revert
to?* — and `D:\LYGO_CANON\INDEX.md` is the list. Every change is a **new release number** made in the
live tree, and it becomes revertible only once it is sealed as its own build.

| tool | what it does |
|---|---|
| `python scripts/seal_build.py --root "<live kit>" --name <LABEL>` | freezes the live tree into the vault: full copy, `SHA256SUMS-<KIT>.txt`, `CANON.md`, `CANON.json`, `RESTORE.txt`, `_freeze_facts.json`, every copied file marked read-only. Refuses to overwrite an existing seal, and verifies the seal against its own hash list before it reports success. |
| `python scripts/restore_build.py --from "<seal>/<KIT>" --root "<live kit>"` | the revert path: verifies **every** hash against the seal's own list *before* it writes a byte, then lays the build back. `--dry-run` shows what would change. |

A seal carries the build, the folder shape (empty folders included) and the build's **working
configuration** — `save/registry.json`, which holds the boot model, so a revert still reads images.
It never carries keys, the operator's runtime history, or model weights.

Rule of proof: **a seal is not a safety net until it has been restored and run.** Before calling a seal
done, restore it into a clean folder and run `scripts/certify_build.py` plus the suite *there*.

---

## 1.3.0 — MEMORY AND GUARD MODULES · tag `build-line 2026-09-20 · module-strip · memory + guard modules`

**Why:** the module layer could say what the console *is*, but not what it *holds* or what it might be
*leaking*. Two read-only modules close that gap: `lygo.meminfo` (order 50, family `info`) reads the memory
the console keeps, and `lygo.guardwatch` (order 55, family `watch`) looks for credentials sitting where a
limb can read them and for secret-shaped files written into the tree. Both declare
`requires.console >=1.3.0` — that condition, not a feature, is why this release number exists.

- **`lygo.meminfo`** — one card over five fact owners (`compaction`, `sessions`, `paths`, `atomicio`,
  `receipts`). It owns no state, opens no gate and writes nothing. The window/token budget is
  `lygo.llminfo`'s to report; this card names that owner instead of re-deriving it.
- **The honesty gate, again** — a source that could not be read is a **named gap**, never a zero.
  `0 sessions filed` prints only when the vault was actually read and was empty; an unread store says
  UNCHECKED and drags the card off green. Both directions are pinned by a test.
- **`lygo.guardwatch`** — a finder. It asks the kernel's own `tools._denied()` for the authoritative deny
  decision rather than keeping a second deny list, and it **never opens a credential file**: it stats,
  resolves and compares paths, and prints pointers, never values. A check it could not run is reported as
  UNCHECKED, so green means *checked and clean*, not *not checked*.
- **Three defects found by RUNNING it, not by the suite** — (1) the kit is a *subfolder* of its repo
  (the checkout is rooted at `lygo-protocol-stack`), so looking for `.git` at the kit alone reported
  "not a git checkout" for a tree that plainly is one; (2) tier-2 name matching flagged
  `engine\llama-tokenize.exe` and hashed `*.d.ts` build output as secret-shaped — a false alarm on the
  engine's own tokenizer, which would have pinned the card amber *permanently*, and no operator reads a
  card that is always amber; tier 2 now requires an extension a secret is actually kept in; (3) one wide
  root (the stick tree) spent a **shared** scan budget and left six roots unread — each root now carries
  its own budget, and a walk that stops at its *stated* depth rule is no longer counted as an unrun check.
- **Two false alarms removed** — a committed template (`.env.example`, `*.credentials.example.json`) is
  not a finding, and the sibling kit's own declared keys read `expected` rather than contradicting the
  kit-scoped group that already called them expected.
- **Stamped in four surfaces from `VERSION`** — `VERSION` (1.3.0), `portal/app.js` (`LYGO_BUILD`),
  `src/modules/host.py` (`KERNEL_RELEASE_FALLBACK`), and the built manifest.
- **REPLY LENGTH — the 768-token wall, and the three numbers that disagreed** — every long answer
  stopped mid-sentence. Measured cause, not inferred: `portal/app.js` sent a hardcoded
  `max_tokens: 768` on every request, the engine honoured it exactly (`gen_tokens: 768`,
  `finish_reason: length`, 81.5 s at a measured **10 tok/s**), while `config/console.json` said
  **512** and `server.py` said **1024**. Three numbers, one of them live, and the operator's own
  config key had **no reader at all** — `console_limits()` never returned `max_tokens`, so the
  documented knob was dead config. Now one source of truth: the config key is read by
  `console_limits()`, the chat handler clamps to it (a request may lower, never raise), the portal
  seeds its cap from `/api/health` instead of carrying a constant, and the window budget
  **reserves** it.
- **The coupling that made the fix safe** — `ANSWER_RESERVE` was a 1024 constant with the comment
  "the portal's cap is 768", i.e. the window reserved room for a reply nobody asked for. Raising the
  cap and leaving it behind is how a long answer overflows the window and evicts the conversation it
  is answering, so `answer_reserve()` now reads the same config key: reserve 4096 (was 1024),
  history room 25,988 → 22,916 tokens. A 5.3× longer reply costs 12% of the live window, and the
  operator sees that trade in one number.
- **`config/console.json`: `max_tokens` 512 → 4096**, with the note rewritten to say what the key
  actually does and why it is sized against generation speed.
- **Client timeouts scale with the cap** — a local answer is still buffered (see the open item
  below), so the page's idle window must cover the whole generation, not the first token: a flat
  240 s aborted a long answer as "engine silent" moments before it arrived. Both the idle window and
  the hard ceiling now derive from the configured cap at a pessimistic 4 tok/s.

- **Editions** — PC is the authoring tree this release was built and tested on. The USB promotion is
  **pending** and each module says so in its own manifest: `surfaces.usb = DEGRADED(promotion pending)`,
  not `FULL`, until the per-file hash-verified promotion and the stick's own suite have run. Web is
  declared out of scope for the module layer.

- **Still buffered — the known limit of this release** — the engine call is **not** streamed yet: the
  console waits for the engine to finish the entire answer, then sends it in one burst. A long reply
  therefore arrives after a long silence, which is exactly why the client windows in this same change
  had to be sized off the cap. `openai_proxy.llama_chat_stream()` already exists in the tree and is
  currently called by **nothing**. Routing the answer through it is the next change, and the one that
  makes a long answer *appear as it is generated* instead of arriving after it.

## 1.2.2 — HARDENING SWEEP (PC, then the stick)

A debug pass over both trees, live and static: every route hit, hostile and malformed input sent,
the suites run, the module surfaces read back. Six defects, all fixed, all pinned by a test.

- **`src/auth.py`** — the token was looked up in the case the client sent it in, while header NAMES are
  case-insensitive (RFC 9110) and clients canonicalise them: urllib title-cases every part, HTTP/2
  lowercases them all. The same valid token answered **401** through `X-Lygo-Llm-Token` and **200**
  through `Authorization: Bearer`. Names are folded once, where the token is read.
- **`src/server.py`** — **OPTIONS was answered 501 with an HTML page.** `BaseHTTPRequestHandler` has no
  `do_OPTIONS`, so a capability probe for a method the console does implement got the stdlib's
  "Unsupported method" markup, where every other answer is JSON. Now 204 + `Allow` on the console's own
  surface, a JSON 404 elsewhere — and still no CORS headers: the console is loopback-bound and
  token-gated, and an `Access-Control-Allow-Origin` here would let any page the operator visits read
  their local console. The public web edition keeps its own allowlist.
- **`lygo.notepad` (module + the legacy handler)** — a body that was not JSON, or a save with no id and
  no text, reached `write_note(None, "", "")` and answered `{"ok": true, ...}` for a **phantom empty
  note**: one note per junk request, and the caller told a write had happened. Now 400
  `nothing_to_save`, store untouched. Emptying a note *by id* still works — the rule is "nothing to
  save", not "empty text".
- **`lygo.envwatch`** — the age came from `f.stat()` **after** the tail read, so `scripts/rotate_logs.py`
  moving a log inside that window raised `FileNotFoundError` out of the panel. A file that moved
  mid-read is now reported **undated and still loud** (no age means no downgrade). The same race is
  closed in the store size sum, and the redundant second `load_state()` is gone: `catalog()` already
  merges `enabled.json` into each row.
- **`src/image_tools.py`** — **26 lines of dead code** orphaned after `image_see`'s `finally`: the body
  of the old `/api/generate` helper, referencing `base`, `body`, `model`, `urllib` and `json` — all
  undefined. Unreachable, so nothing broke *yet*; one re-indent away from a NameError. Removed.
- **`src/modules/host.py`** — every module row now carries **`lifecycle`** (what the manifest declared)
  beside `state` (the effective status, which the host overwrites to REFUSED / DISABLED / DEGRADED).
  The row had only `state` — the same name a *pane* uses for its health colour — so a report reading
  `row["lifecycle"]` saw `None` for five healthy modules.

## 1.2.1 — ENVIRONMENT TRUTHFULNESS · tag `build-line 2026-09-20 · envwatch-clean`

**Why:** the first boot of the module strip on the stick reported three things that were not faults, and one
that was a real config defect. A watcher that cries wolf is worse than no watcher: an operator learns to
ignore the card, and then the one real fault goes unread. This release makes the card's "needs fixing" mean
*needs fixing*.

**What changed**

1. **A declared-optional root is no longer a fault.** `U:\LYGO` is the stream share, mapped only during
   steward ops - the config said so in prose ("when mapped") and `lygo.envwatch` reported it as a broken path.
   `config/admin.json` now declares `optional_roots`, `src/admin_map.py` owns the answer
   (`optional_roots()`, `is_optional_root()`), and the card shows such a root as
   *Absent (declared optional)* - visible, never a finding. An undeclared missing root still is one.
2. **A guard that holds is not a fault.** The notepad refuses a path carrying an embedded null byte, which is
   the writing guard working exactly as designed; the card was reporting it as `write refused`. Refusals of a
   path that cannot exist (null byte, empty target) are now reported as *correctly refused*, with the reason,
   and stay out of the fault count. A refusal of a real path is still amber.
3. **Old logs are rotated, never deleted** - `scripts/rotate_logs.py` (`--days`, `--root`, `--apply`; dry run
   by default). A fault line from a test run days ago held the strip amber for ever over something that cannot
   happen again, while deleting the log would destroy the record. Rotated logs move to `save/logs/archive/`,
   and the card **counts** the archive so the history cannot be hidden.
4. **The `{kit}\docs` mapping resolves.** Both trees had a config root pointing at a folder that did not
   exist; `docs/` now exists in both, with a README saying what belongs there (and what must never).
5. **The manifests stopped lying about their editions.** Both modules claimed `usb: N/A(not promoted yet)` and
   `web: DEGRADED(...)` after the 1.2.0 promotion; they now read `usb: FULL` with the promotion recorded in
   `notes`, and `web: N/A(by steward decision ...)`. Their tests pin that truth, not the old scope.

**Module version:** `lygo.envwatch` 1.0.0 → **1.1.0** (its behaviour changed); `lygo.llminfo` stays 1.0.0.

**Verified:** `python -m pytest tests -q` on both trees; `refresh_manifests.py` + `certify_build.py` on both;
both cards read green with the modules on `dock.llm` (LLM data) and `dock.env` (Environment watch).

## 1.2.0 — MODULE STRIP · tag `build-line 2026-09-20 · module-strip`

**Status: current.** `1.1.1` is sealed for both installs. This release ships the **first pair of function
modules** and the bottom strip they live in, and anchors both consoles at one release number.

- **`lygo.llminfo` (family `info`)** — "what is hooked up": the selected model and its file, the token budget
  from the record, the provider's published rate window (peak / off-peak), the API switch, the clock, the
  release. Read-only; it names every fact it cannot get instead of inventing one.
- **`lygo.envwatch` (family `watch`)** — "what needs fixing": skill files that never reach the model, mapped
  paths that do not resolve, error lines in `save/logs` matched against five **stated** rules, P0 gate verdicts
  outside `AMPLIFY`/`SOFTEN`, and the daemons this kit can see (engine, backends, GPU, stack monitor). It gives
  a **location** with every finding, reports a check it could not run as **UNCHECKED** rather than green, and
  **fixes nothing** (the tests scan its own source for write calls).
- **The bottom strip.** Module panes render in a full-length strip **below** the working area — one module, one
  strip, group tiles across it — so a module can never take height from the chat composer. The page scrolls to
  it. Panes may declare `state`/`state_text` and rows may carry a `dot`, and the strip's chip answers "is
  anything broken" across every module. A pane that publishes no state counts as **unchecked**, never as good.
- **The naming law.** `lygo.<subject><family>` — `info` (read-out) and `watch` (finder), with `ctrl` and `link`
  reserved; the family is the id's suffix *and* a manifest field, and a test fails if they disagree. See
  `01_DESIGN/MODULE_NAMING_AND_BRANDING_v1.md` in the project hub. `lygo.health`, `lygo.world` and
  `lygo.notepad` predate the law and carry no family — recorded, not tidied away.
- **The version anchor.** `src/modules/host.py::KERNEL_RELEASE_FALLBACK` and `portal/app.js::LYGO_BUILD` follow
  `VERSION`, and the two new modules declare `introduced: 1.2.0` with `requires.console: ">=1.2.0"` — they do
  not exist in `1.1.1` and may not claim to. `scripts/refresh_manifests.py` re-stamped the manifests and
  `scripts/certify_build.py` re-certified the build.

**The seam held:** both modules are a directory, a `catalog.json` line and a test file. `src/server.py` and
`scripts/certify_build.py` contain no reference to either — that is the contract test, and it is in the suite.

**Editions:** PC and USB get both modules. **WEB does not** — the steward's decision: *"we do not need to
change the web portal for these modules, they are not needed on web portal."*

---

## 1.1.1 — BUILD LINE · tag `build-line 2026-09-20`

**Status: current.** V1 (`1.1.0`) is untouched and now **sealed for both installs**; this release adds
the machinery that keeps it that way — the thing that was missing when a session edited a working build
and both installs had to be rebuilt from the anchor.

- **`scripts/seal_build.py`** — freezes a live tree into `D:\LYGO_CANON\<date>_build-<release>_<label>\<KIT>\`
  with `SHA256SUMS-<KIT>.txt` (raw sha256, paths relative to the seal root), `CANON.md`, `CANON.json`,
  `RESTORE.txt` and `_freeze_facts.json`, marks every copied file read-only, verifies the seal against
  its own list, refuses to overwrite an existing seal, and maintains `D:\LYGO_CANON\INDEX.md`.
- **`scripts/restore_build.py`** — the revert path. Verifies the whole seal first, refuses to write
  anything if it does not match, reports identical / restored / held-back, never deletes, never touches
  the operator's runtime or keys.
- **V1 sealed for both installs** (release `1.1.0`, the working state):
  - `D:\LYGO_CANON\2026-09-20_build-1.1.0_PC_LOCAL-WORKING\PC_LOCAL\` — 340 files, 50 folders
  - `D:\LYGO_CANON\2026-09-20_build-1.1.0_USB_CLAW-WORKING\USB_CLAW\` — 361 files, 49 folders
  - The earlier `2026-09-19_build-1.1.0_STABLE` canon is left untouched as history, but it is **not** the
    revert target: its `portal/app.js` predates the `servedBuild` fix, so a restore from it comes back
    with a dead page (header stuck on `probing…`). That is exactly why the revert target had to be re-cut
    and proved.
- **Proof the seal works:** the PC seal was restored into a clean folder and there `scripts/certify_build.py`
  printed `CERTIFIED BUILD` and the suite ran `592 tests ... OK`. That run earned its keep twice over —
  it found that the first pass was skipping `workspace/` (SOUL.md, MEMORY.md, IDENTITY.md — the console's
  soul) and empty folders (`models/`, test fixtures). Both are fixed and pinned.
- **`tests/test_build_seal.py`** (13 tests) pins the whole contract: a seal is verifiable and read-only,
  it refuses to be overwritten, it carries the identity files, the empty folders and the boot model, it
  drops keys/runtime/weights, a tampered seal cannot be restored, a refused restore writes nothing, and a
  restore never clobbers operator state.
- Suites, certifier and `scripts/verify_install.py` re-run green on both installs at this release.

---

## 1.1.0 — STABLE ANCHOR · tag `stable-anchor 2026-09-19`

**Status: STABLE.** Frozen as CANON in `D:\LYGO_CANON\2026-09-19_build-1.1.0_STABLE\` (`PC_LOCAL\` +
`USB_CLAW\`, SHA256SUMS beside them, marked read-only). The canon is *reference only* — build forward in the
live trees, never edit a canon copy.

**Verified on both installs, at this exact state:**

- **Suite:** 582 passed / 7 subtests — run on the PC tree *and* on the stick tree, each on its own tree.
- **`scripts/certify_build.py`:** `CERTIFIED BUILD` on both — files match the published manifest, license intact.
- **`scripts/verify_install.py`:** `ALL GOOD` — 27 checks, 0 failed, on both installs.
- **Zero-Ollama:** the kit boots its **own** `engine/llama-server.exe` (llama.cpp b10988) on GGUFs it owns;
  no daemon is started or subprocessed anywhere in the path.
- **Vision (PC), and this is the steward's own test:** `gemma4-12b` + `gemma4-12b-mmproj.gguf`, engine log
  `load_model: loaded multimodal model, 'I:\LYGO_MODELS\gemma4-12b-mmproj.gguf'`. A 64 px control photo
  (left half red, right half blue) answers `Red, blue.`; the steward pulled a real image through the portal
  and the model **described it correctly** (2026-09-19). `/api/health`: `selected=gemma4-12b vision=true`.
  The projector is wired by one rule (`registry.mmproj_for`) shared by the engine boot, the vision limb, the
  console's own guard and the scanner — a vision model cannot boot blind without the console saying so.
- **Attachments:** a photo rides the message as an `image_url` part (the engine's projector reads it, ≤1600 px
  JPEG); a small text file is inlined into the message; anything else lands in `workspace/uploads/` and the
  **host** reads it (`read_file`, `host: true`) so its text reaches the model without the model having to
  remember a limb call.
- **Launcher:** `LYGO_LLM_CONSOLE.bat` / `LYGO_LLM_CONSOLE_STOP.bat` print what `taskkill` actually answered,
  retry, escalate (`Stop-Process`, WMI terminate), and name an **elevation denial** with the fix instead of
  looping. Desktop twin: `LYGO PC CONSOLE STOP.bat`.

**Known limits at this anchor — do not overclaim:**

- **The stick does not carry a vision model.** 5 of its 14 registry records are its own (its `E:` CAS); the
  other 9 resolve to this PC's stores, `gemma4:12b` among them, so on another machine they simply are not
  there. Its default `llama3.1:8b` answers text. Photos on the stick need either an inlined file or a model
  the stick actually holds — a small VLM (~2 GB) as the `image_see` runner is the stand-alone answer.
- **Image generation is not in this kit.** `llama-server` is text + vision; generation needs its own
  diffusion service (e.g. `stable-diffusion.cpp`) behind a new limb.
- **Tool-choice bench:** the 24-ask run has not been repeated since the local schema grew 20 → 22 tools
  (the two vision limbs). A green suite does not measure tool *selection*.

**Signatures in force:** `Δ9Φ963-LICENSE-v3.0` · `Δ9Φ963-LYGO-BRANDING-v1` · `Δ9Φ963-LYGO-SESSIONS-v1` ·
`Δ9Φ963-LYGO-COMPACTION-v1` · `Δ9Φ963-SUCCESSION-PROTOCOL-v1`. `LICENSE` = `91a34b504e9e9ae7` / 26044 B.

---

## How the next release is made (the only way that keeps the anchor honest)

1. Change code/tests in the live tree `I:\E Drive\lygo-protocol-stack\lygo_llm_console`.
2. Bump `VERSION` line 1 — **next after this anchor is `1.2.0`** — and add a section at the top of this file.
3. `python scripts/refresh_manifests.py --note "<why>"` then `python scripts/certify_build.py`.
4. `python -m pytest -q` on **both** trees; mirror the changed files into the stick kit.
5. Commit from the repo root with **explicit paths** (never `git add -A`).
6. Hand the steward the ready-to-publish state. **Agents build and verify; the steward publishes.**

Agents do not push, and do not touch a canon copy.

## 1.3.0 — the Boot server button (unreleased, 2026-09-21)

* **A standalone `Boot server` button** in the BRAIN row, beside `Boot local`. It runs `LYGO_LLM_CONSOLE.bat`
  itself — the launcher keeps its port sweep, ownership check and refusal to double-start; nothing is copied.
* **`tools/doorbell.py`** — the reason a button can work at all: the page is served *by* the server it would start,
  and a browser cannot spawn a process. A tiny loopback listener on the console's port minus one rings the launcher.
  It serves its own page too (`http://127.0.0.1:<port-1>/`), which is the one bookmarked door worth having.
* Token in `data/.lygo_doorbell_token`; loopback only; `connect-src` in the console's CSP names the doorbell
  (derived from the bound port, so the USB copy gets its own); requests logged with the query stripped.
* It detaches (`--detach`, no window) and the console `ensure_running`s one on the way up, so the button is never
  a dead end. `LYGO_NO_DOORBELL=1` opts out; `LYGO_NO_BROWSER=1` stops a second tab when the doorbell boots.
* Verified live: page → doorbell `200` → launcher → console back on 9641, engine 11441, page `up=true`.

Ports: PC doorbell **9640** (console 9641) · USB doorbell **9650** (console 9651). Both derived, never hardcoded.
