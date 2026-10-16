---
name: unity-2d-3d-building
description: >
  Use when an agent must build, wire, or ship a Unity game - 2D, 3D, or 2D art over a real 3D stage:
  installing the engine, creating a project from a template, driving the editor through Unity's own
  CLI bridge or an MCP server, sourcing CC0 assets, and building to WebGL that you verify in a browser.
  Carries the Battle TV painted-broadcast house style as a worked reference, and a living art-method log.
  Use for Unity, Unity 6, 6000.x, Unity MCP, the unity CLI, WebGL build, sprite, Shader Graph,
  URP vs built-in, Kenney, licence-cleared assets, or /unity-2d-3d-building.
version: 1.1.0
license: MIT-0
metadata:
  openclaw:
    emoji: "🎮"
    homepage: "https://chatagent.ca/"
  publisher: deepseekoracle
---

# Unity 2D-3D Building

An agent's guide to Unity: get the engine, make a project, drive the editor without a human clicking,
source art you are allowed to ship, build it for the browser, and prove it runs. The Battle TV painted
broadcast style is the worked example at the end, with its method log kept alive.

Author's home: https://chatagent.ca/ · worked picture: https://deepseekoracle.github.io/battle-tv-unity/

## When to use this

- An agent must produce or change a Unity project, and no human is going to click through the editor.
- A game has to run **in a browser page** and look like a real engine built it.
- Assets, templates or a licence answer are needed for a game build.
- A Unity WebGL build exists and must be served, verified, and shown.

## When not to use this

- **A 2D page game in a day.** Canvas/JS beats Unity for a quick 2D web game: instant load, no
  10-20 GB pipeline, no rebuild-to-change-anything loop. Say so instead of reaching for an engine.
- **A downloadable Unreal game.** Different engine, different guide. (Unreal cannot target the web at
  all - see the table below.)
- **A mobile/console shipping pipeline.** This covers getting to a playable, verified build; store
  submission, IAP, and platform certification are out of scope.
- **Retuning a live game's fight math.** Presentation work is guided here; balance numbers belong to
  the game that owns them.

## 1. Decide the target before anything is installed

Ask *where the game must be playable*. That one question eliminates engines:

| Target | Engine |
|---|---|
| **Plays in the browser page itself** | **Unity 6 (native WebGL build)** or Godot |
| A download the page offers | Unity or Unreal, either one |
| A quick 2D page game | canvas/JS - an engine is the wrong tool |
| Unreal, in-page | **does not exist**: Epic removed HTML5 export after UE 4.24 |

- **Unreal cannot target the web.** The official answer is Pixel Streaming (renders on a GPU server and
  streams video) - not a standalone web build, and not fit for games. A UE game is always a download.
- **The engine does not make the game good, it makes it look good.** State the trade rather than
  implying a Unity rewrite upgrades a game by itself.
- Budget: Unity editor + WebGL module is roughly **10-20 GB**. Unreal 5 is roughly **110 GB**.

## 2. Get the engine

1. **Unity Hub**, then **Unity 6 (6000.x)** plus the **WebGL Build Support** module *for that exact
   version*. The Hub download is small; the editor is the download.
2. **Put it on a real SSD and check the medium, not the free space.** A drive letter says nothing:
   `Get-PhysicalDisk | Select-Object DeviceId,FriendlyName,MediaType,BusType,Size` and
   `Get-Partition | Where-Object DriveLetter`. On one rig this showed `D:` as a SATA SSD and `C:` as
   NVMe while two USB external HDDs held the most free space - shader compilation belongs on the SSD.
3. **Unity requires a Unity ID login.** Never guess, ask for, or handle those credentials: the operator
   signs in on their own machine.
4. **Do not install Unreal "as well" to compare.** Section 1 already decided it, and 110 GB is a cost
   to the very drive the rest of the work needs.

## 3. Make a project from a template, never from an empty scene

```
unity templates list --editor 6000.5.9f1        # what this editor can actually pull
unity projects new "<Name>" --path "<parent-dir>" --editor-version 6000.5.9f1 --template com.unity.template.fps
```

- Templates are marked `ready` / `upgradable` / `downloadable`; creating one downloads and imports it.
- **`templates list` is authoritative, not the Hub GUI**, and the offering differs per editor version:
  on 6000.5 the only Learning *game* template is the FPS Microgame (Karting / 2D Platformer / LEGO
  microgames are not offered for it).
- Free complete playable bases exist for **FPS, 2D platformer/side-scroller, kart racer, board/chess,
  card, tower defence, puzzle/RPG**. They do **not** exist for **sports, boxing/fighting, farming/sim**
  - those are paid templates. Genre choice is constrained by budget; say that instead of searching longer.
- Kenney's *Starter Kits* are Godot, not Unity: his CC0 **assets** import fine, his **kits** do not.

## 4. Drive the editor as an agent

**Check for Unity's own CLI bridge before installing anything** - it is often already live and it is
free:

```
unity status                       # open project, editor version, PID, port, state
unity list                         # ~142 built-in editor tools
unity command <tool> --project-path "<project>" --result-only --json
unity command <tool> ... --detach  # long jobs; poll the matching *_status tool
```

`unity list` covers scene/GameObject/component/asset authoring, `build` + `build_status` (full
BuildReport), `capture_game_view` / `capture_scene_view` (PNGs), `console` (log tail), `recompile`,
tests, audits, lighting and NavMesh bakes. `unity skill show` is Unity's own agent guide.

When a tool the CLI lacks is genuinely needed, fall back to a free MCP server - **`CoplayDev/unity-mcp`
(MIT, 34 tools)** or **`JESVN/unity-mcp-server` (free, 288 tools / 30+ categories)**. Unity's own Unity
MCP needs Unity Cloud + a Unity AI subscription and cannot be pointed at external models, so do not put
that paid gate in front of an experiment.

- **The first external connection is approved by the operator in the editor** (Project Settings > AI).
  Expect a dialog, not a silent connect - tell the user it is coming.
- **Verify every edit by reading the editor console back** through the same connection. Agent edits
  then confirms, then edits again; never chain edits on an unread result.
- Full command surface, detach/poll pattern and setup notes: `references/editor-cli.md`.

## 5. 2D, 3D, or 2D art over a 3D stage

| | Pick it when | Costs |
|---|---|---|
| **2D** | side view, flat art, precise silhouettes, painted cutouts | sprites, Physics2D, sorting order; no real lighting |
| **3D** | real camera movement, lighting, physics worth the weight | meshes, materials, LOD, a heavier WebGL payload |
| **2D art over a 3D stage** | a painted broadcast look that still needs depth, or one hero mesh | both pipelines; the mesh must be verified before it is wired |

- **A 3D mesh joins a 2D look only after a watched frame matches the 2D art.** Do not switch the whole
  project's render pipeline to chase one baker or one effect.
- **A deformed mesh is a broken mesh.** Imported FBX/GLB models can arrive with bad normals, scale or
  shape keys: a car with deformations will load, look wrong, and never drive. Verify the mesh
  (dimensions, normals, bounds) *before* wiring physics or a controller to it.
- **Decide built-in vs URP at the start.** Changing pipeline later re-shades every material. A WebGL
  build wants the smallest shader surface you can use, and the worked style here is built-in.
- Sorting in a sprite stack is **sibling order** (ring back, bodies, planted prop, ring front, spark),
  and a prop parented to a differently-scaled parent lands in the wrong place. Details:
  `references/2d-and-3d.md`.

## 6. Assets: licence first, download second

Nothing gets pulled until it is clear it can ship. The gate, in order:

- **CC0 is the target** - public domain, sellable, remixable, no attribution, safe in a public repo.
- **A free kit's art can be CC0 while its code is not** (Extension Asset EULA on the code). Take the
  CC0 art, write the logic yourself, and the kit never becomes a runtime dependency.
- **Never source from "free download" aggregators** that redistribute paid Asset Store packages
  (`unityassetpack.com`, `unityassetcollection.com`, `opengameasset.net`, "50 Unity Source Codes"
  bundles). Nothing built on them can be published.
- **A GitHub game repo needs a real licence at the file.** No LICENSE, or "for educational purposes",
  is **not** permission to ship. MIT/Apache only, read at the file.
- **Mixamo-class services are free to use but forbid redistributing raw files** - keep local copies,
  never commit them to a public repo.

Ship-able CC0 sources, what each is good for, format/permission notes, and the license gate as a
checklist: `references/assets-and-licences.md`. (Kenney, Quaternius, Poly Haven, KayKit, Freesound /
Sonniss and the Unity Asset Store's free tier are all covered there with the caveat per source.)

**Enumerate before you fetch, then import selectively.** Keep one library directory outside the
project and import only what the levels call for - importing thousands of models inflates the project,
slows every import, and bloats the shipped build with assets nobody sees. A browser-rendered catalogue
can return zero links to `curl`; look for an index file (`kits.tsv`, an API) before writing a scraper.

## 7. Build it for the web, and prove it

```
unity build "<project>" --create-profile WebGL     # writes Assets/Settings/Build Profiles/WebGL.asset
unity build "<project>" --profile WebGL -o "<out-dir>" --no-tail --log-file "<log>"
```

- **`unity build --target WebGL` fails by design** ("Target WebGL has no built-in command-line build").
  Use a build profile, or `--execute-method`.
- **Never wrap a build in a shell `timeout`** and keep it off the foreground path: a microgame-sized
  WebGL build takes **~8-12 minutes**, and a killed run leaves a half-written `Build/` plus
  `exitCode: 143` provenance. Launch it as a tracked background process and poll the log and the output
  folder - arriving artifacts are the proof, not the exit code.
- `[license] ... LicensingClient has failed validation; ignoring` followed by
  `Exiting batchmode successfully now!` and code 0 is a **success**, not an error.
- **A gzip WebGL build will not run on a static host without the right header.** GitHub Pages serves
  `.gz` as `application/gzip` with no `Content-Encoding`, and the loader stalls at the progress bar
  forever. Ship the decompression-fallback build instead (`PlayerSettings.WebGL.decompressionFallback =
  true`, a project setting - set it with a small eval file and log the value back to confirm).
- **Serve it, then load it in a browser and click into gameplay.** The intro menu proves the loader;
  the first gameplay frame proves scene, scripts and wasm all came up. A file list proves nothing.
- Say the payload size out loud before it goes on a landing page (a microgame build is ~24 MB gzipped
  for a first visitor).

Full ship rules - canvas centring, fitting a short window, Escape never being a game key, proving the
new code shipped rather than an old bundle, numeric layout asserts: `references/webgl-shipping.md`.

## 8. The loop, and what "done" means

1. Pick the target (section 1). 2. Get the engine on an SSD (section 2). 3. Create from a template
   (section 3). 4. Connect the agent and read the console back (section 4). 5. Licence-clear the art
   (section 6). 6. Build, serve, load, click (section 7).

- **A verifiable milestone beats a long build.** Get the untouched template running and building to
  WebGL *first* - that proves editor, bridge, build and browser as one chain before a single asset or
  gameplay change is paid for.
- Every claim carries its evidence: the console read-back, the artifact on disk, the loaded page.
- **A WebGL build is not a live page you can edit.** Iteration is change -> rebuild -> reload; budget
  for it, because it is the real cost versus canvas/JS.

## 9. Traps that have actually cost time

- **The editor needs the GPU and a lot of RAM, and a resident local LLM holds both.** On a one-card box
  (8 GB measured), a loaded local model and a renderer or editor cannot coexist: park the engine before
  opening Unity or starting a render, with the wake in a `finally`. Measured on one rig: **719 MiB free
  of 8188 MiB VRAM** with the console up.
- **Slow work outlives a tool call.** Builds, imports, and bulk downloads must run as tracked
  background processes, polled by artifact; relaunching a live job races the first copy.
- **Never `git add -A` in a shared repo**, and delete `*_BurstDebugInformation_DoNotShip/` from build
  output (its name is the instruction, and it bloats the repo).
- **Report counted numbers, not download lists.** A claimed asset total that was never counted on disk
  is the kind of "done" that gets checked.
- Longer list with the failure it caused: `references/traps.md`.

## 10. The worked style: Battle TV painted broadcast

The house look this skill was born from - painted side-view fighters on a plate, additive shader
overlays, a ground ring as the quality bar, HUD on the canvas above the plate - is preserved whole in
**`references/battle-tv-style.md`**, including its standing rules (built-in pipeline, linear colour
space, one fighter at a time, presentation only, never retune fight math to fix a picture).

**Art methods have one home: `references/techniques.md`.** Read it before generating a frame, importing
a sprite, parenting a prop, writing a shader, or placing a hit. If the style file and the log disagree,
the log is current. Append **one dated line** under Confirmed only after a watched build shows the
picture you intended, naming the commit or page you watched; a method that was only tried does not get
logged, and a method a later watch overturns gets a new line that says what replaced it (leave the old
line, mark it replaced). Rejected tools and failed looks stay in the log's Rejected list so the next
session does not retry them as the production path.

## Files

| File | What it is |
|---|---|
| `references/getting-started.md` | the first-hour checklist, install to first verified build |
| `references/editor-cli.md` | the `unity` CLI surface, detach/poll, MCP fallback, console read-back |
| `references/2d-and-3d.md` | choosing a stage, sorting, sprites vs meshes, pipeline decision |
| `references/assets-and-licences.md` | CC0 sources with caveats, the licence gate, import rules |
| `references/webgl-shipping.md` | build to served-and-verified page, with the traps |
| `references/traps.md` | the failures that cost the most, and the fix for each |
| `references/battle-tv-style.md` | the worked painted-broadcast style, whole |
| `references/techniques.md` | the living art-method log (one home for methods) |

## Self-check

```bash
python scripts/check_skill.py           # add --json for machine-readable findings
```

Named rules, each answering with a named boolean: no absolute local paths in the shipped text, no
floating versions in install commands, version agreement across `SKILL.md` and `claw.json`, every
referenced file present, licence claims limited to hosts named in `assets-and-licences.md`.

## Install

```bash
npx clawhub@0.23.3 install deepseekoracle/unity-2d-3d-building@1.1.0   # pin BOTH sides: CLI and package
```

Do not republish this skill unless the user asks. Do not put a local disk path, drive letter, or user
folder in it: it is loaded on other people's machines.
