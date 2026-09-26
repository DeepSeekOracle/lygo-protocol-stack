# What changed since skill v1.2.0 (console 1.2.x -> 1.5.6)

The console is the same product, but its body of work since the last skill release is large. The skill
now describes 1.5.6; the important differences:

**Runtime the skill must state correctly**

- **Recall / RAG over your own corpus** (`lygo_rag.py`): local index, incremental rebuild, now safe
  under concurrent writers (1.5.6 fixed a race that surfaced as misleading "could not write the index"
  lines).
- **Sessions and compaction** (`sessions.py`, `compaction.py`, `transcript_archive.py`): named
  sessions, resume, search, and context folding with a stated budget.
- **Vision** (`vision.py`, `image_tools.py`, colibri engine slot): image limbs when a projector is
  registered; image generation/save paths stay inside the kit.
- **Music and media** (`music_*.py`, `media_tools.py`): lyric and song jobs, media status, audio
  serving from the kit.
- **Model routing and fit** (`model_route.py`, `model_fit.py`, `model_check.py`, `backends.py`): which
  model can actually run on this box, and why it says no.
- **Tasking and crons** (`tasking.py`, `crons.py`): in-console task cards and scheduled jobs.
- **Hardware and performance facts** (`hardware.py`, `perf.py`, `turnperf.py`, `runtime_facts.py`):
  GPU/RAM reporting and per-turn cost, visible in `/api/health` and the portal.
- **Split storage / CAS** (`cas_import.py`, `registry.py`): kit-carried model storage, read-only
  Ollama CAS import, no daemon dependency.
- **Installer and public build** (`install.py`, `INSTALL.bat`): seeds identity for the installing user
  and fetches the engine at a pinned tag, without steward paths.
- **Skills module** (`skills_mod.py`): ClawHub/SkillHub install into the kit, with P0 gating.

**Package-level changes**

- Kit ships **unpacked** with a per-file manifest instead of a zip (see `references/SECURITY.md`).
- Steward absolute paths are removed at build time by
  `tools/build_clawhub_llm_console_kit.py`, which refuses to build on drift and refuses to ship on a
  surviving forbidden token.
- Version, pin and hash live in one place: `claw.json`, mirrored in `SKILL.md` frontmatter, checked by
  `scripts/self_check.py`.
