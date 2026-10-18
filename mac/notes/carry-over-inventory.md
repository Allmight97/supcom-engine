# Carry-over inventory: what SupCom built, and what could move to OpenSupCom

Date: 2026-10-14. Read-only study for the planner. Nothing was built or run for this file: every "proven
result" is copied from our docs, logs and tests (STATUS.md, docs/, engine/*/*.md, log/), and every statement
about OpenSupCom (OSC) rests on reading `work/ref/opensupcom` at `1a873786` (grep and docs), not on running it.

2026-10-16: the engine, its tools and the older session logs this file cites went to `~/Projects/SupCom-archive-2026-10-16.tar.gz` and the tag `native-engine-final`.

Verdict codes, used in every table:

- **BRING**: works for any engine; move it as it is (paths and names aside).
- **ADAPT**: useful, but needs a named change for OSC.
- **ARCHIVE**: ours only (the Metal 4 stack); keep in this repo, do not move.
- **DROP**: OSC already does it better, or nobody needs it. Nothing is deleted without JStar's word.

Other codes: **O** observed in a run, **S** static (Ghidra), **I** inferred. "Original" is the GOG 1.5.3599 game;
"bottle" is the CrossOver bottle `SupCom`.

## 0. Read this first: constraints and the 12 items worth the most

Constraints that shape every verdict:

- **Licence.** Our code is GPL-3.0 (LICENSE); OSC is MIT. Any file we contribute upstream becomes MIT only by
  JStar's decision (STATUS.md leaves it open). Vendored `third_party/lua-lang` is MIT. vkd3d (LGPL-2.1+) is run
  as a command-line tool, never linked. This file does not settle it.
- **Game data stays out of git, on both sides.** OSC's provenance policy forbids game text, game art and
  captured traces in the repo. So everything in `work/traces` (80 MB), `work/logs/screens` (368 MB, 286 files)
  and `work/logs/s2-*-spec.md` is local-only. Our hooks and comparators hold no game text and are safe to commit.
- **Most of our evidence is not in git.** `.gitignore` excludes all of `work/`. The captures, the Ghidra project
  (875 MB) and the sim specs (`work/logs/s2-motion-spec.md` 46 KB, `s2-collision-spec.md` 38 KB,
  `s2-intel-spec.md` 49 KB, `s2-threat-spec.md` 45 KB, `s2-targeting-spec.md` 24 KB, `s2-derived-rules.md` 49 KB)
  exist only on this Mac. Copy them, or point the new project at them, before anything is cleaned up.
- **Deadline for new captures.** The original runs only in CrossOver 26.3 under Rosetta, which macOS 28 (2027)
  removes. JStar keeps the dev Mac on macOS 27 until CrossOver 27 (FEX) runs the game. Captures still queued
  (notes/scratchpad.md): load half of the save/load trace (`save-5min.log` exists, `load-5min` does not), S1 items
  #6-9 (idle/walk animation frames, a water and sky map, combat effects, loading screen, Escape menu, Save and
  Load dialogs, score screen).
- **One bottle, one game at a time.** `work/bottle.lock` serialises runs; the bottle and `Game.prefs` are shared.
- **Test convention conflict.** Our `scripts/check` fails when `work/game/gamedata` is missing; OSC's tests exit
  77 (skipped) without game data and CI runs `ctest -LE data`. Pick one before merging any capture ctest.

The 12 highest-value items (details in the tables):

1. Capture hooks plus comparators (sections 1.2 to 1.5): original-side Lua and log-only Python; engine-agnostic.
2. `tools/lua-trace/trace.lua` and `diff.py`: runs in any engine that supports `--init` hooks; shows which
   bindings the original really calls (217 sim and 134 user in 60 s).
3. `tools/bp-dump` hook plus `compare.py`: 3,778-blueprint dump of the original; the fastest way to measure
   OSC's blueprint-table gap.
4. `.setup` manifests and the preflight in `tools/lib/capture.py`: stops bad runs early, stops bad comparisons.
5. `tools/lib/game-run.sh` and the CrossOver scripts: the Mac launcher for the original.
6. `tools/ref-shot` plus `tools/image-compare`: the only look-against-the-original comparison; OSC says it has none.
7. Reference corpus in `work/` (captures, screenshots): irreplaceable after Rosetta goes.
8. Ghidra project and `scripts/ghidra-py`, `dossier.py`, `lua_bindings.py`: evidence beyond faf-re (about 1 in 10
   of faf-re's byte matches disagree with earlier names).
9. The 1,218-binding contract (`work/lua-bindings.json`) as a finding beside OSC's `binding_baseline_retail.txt`.
10. Sim findings with numbers (section 5): float Lua numbers, 395 blueprint defaults per kind, `Entity:Kill` flag,
    1 u pathing with the vertex-step slope rule, steering and threat-map specs.
11. Guards: pre-commit game-file guard, git-bypass block, input gate. OSC has none of the three.
12. Process rules that were paid for in failures (section 4), each already enforced by a script or hook.

## 1. Validation and reference-capture tooling

### 1.1 Launch, preflight and manifests (original side, CrossOver)

| Path | What it does | Proven result | Verdict |
| --- | --- | --- | --- |
| `tools/lib/game-run.sh` (195 lines) | One launcher for every capture: start the original (1680x1050) or FAF's game (1024x768) in the bottle; wait for an end marker; atomic `.partial` logs renamed on finish; bottle lock; swaps `Game.prefs`; refuses an original run with `active_mods`; copies hooks to `work/capture-run/NAME/` so edits mid-run change nothing; exit trap stops only its own game | Used by all five capture tools; delivered about 12 captures on 2026-10-14; syntax-checked in `scripts/check` | BRING (the Mac launcher for the original). Hard-wired to bottle `SupCom` and `Z:` paths; OSC's `tools/retail_ref/retail_ref.py` is the Linux/Proton equivalent, so merge as a second backend |
| `tools/lib/capture.py` (186) | `watch`: stops a run on first Lua error, unknown unit type, a loaded hook with no `HOOKCHECK` line in 90 s, or a missed checkpoint; `setup`: writes the manifest; `mods`: refuses active mods | `python3 -I tools/lib/capture.py --self-test` runs inside `scripts/check` | BRING (parses logs only; the `HOOKCHECK` idea works for OSC runs too) |
| `NAME.setup` manifests (JSON) | Arguments, git HEAD and dirty flag, sha256 of every hook and script, resolved armies (civilians too), options, seed, last tick, how the run ended | Prevented the civilians and factions detective work; comparators refuse a mismatch. Only `combat-600.setup` and `gallery.setup` exist; older captures predate manifests | BRING; ADAPT the schema to record OSC commit and flags for OSC-side runs |
| `tools/lib/capture-hook/` (Lua: `simInit`, `SinglePlayerLaunch`, `gamemain`, `maputil`) | Mounted first in every capture: civilians (the command-line launch reads `teams.ExtraArmies`, maps keep them in `customprops`), `SETUP|TICK|n` every 100 ticks, `/simspeed` | Civilian armies now in every capture; motion-unit runs use `/nocivilians` | BRING (original side only) |
| `.agents/faf-crossover` (46) | Starts the FAF client, rebuilds it, or runs any exe in the bottle; deletes `dosdevices/y:` before each run | Fixed "no textures" (Y: drive path bug); all four FAF-track goals pass (log 2026-10-12) | BRING (Mac launcher); low priority once FAF runs natively |
| `.agents/faf-autorun/run`, `hook/`, `init.lua` | Runs FAF's game with `/auto...` actions (`/autoai`, `/autosave`, `/autoexit`, `/autoload`) and checks the log | M28 Easy skirmish saved at 2:00, reloaded in a new process, exited at 3:20 (2026-10-12) | BRING as the reference for FAF behaviour. Overlaps OSC `tools/faf_custom_game.py` (see section 6) |
| `.agents/faf-app/install` (builds `/Applications/FAF Client.app`) | Launches the FAF client through `.agents/faf-crossover client` | Client signs in and hosts a private game with M28AI, fullscreen 2560x1440 (log 2026-10-12) | ARCHIVE once FAF runs natively through OSC |
| `scripts/game-prefs` (147) | Safe edits of the bottle's `Game.prefs`: refuses while a game runs, backs up, balances braces | Self-test in `scripts/check` | BRING |
| `scripts/game-log-check` (64) | Exit 1 on known failures: unresolved data paths, no settings, 3D audio, D3D9 device, Lua errors, no `Run time` line | Self-test (4 cases) in `scripts/check` | BRING |
| `scripts/game-window` (82), `.agents/game-window/{input,winid}.swift` | Finds and screenshots the Wine window (also on another Space); clicks and keys behind the input gate | Screenshot half used in every ref-shot; input half used only in JStar's AFK window | BRING the screenshot half; the input half stays gated |
| `tools/mouse-probe/` (`run`, `live.py`, `macprobe.swift`, Lua hook) | Prints how far the game cursor is from the Mac pointer; sends no input | Found a -31 point offset in FAF's game (menu-bar height), 0 in GOG; fix recorded in `docs/crossover-recipe.md` | ADAPT: needed again for MAC-3 (fullscreen mouse on target); the Mac half is reusable, the Lua half is original-side |

### 1.2 Reference captures of the original

| Path | What it does | Proven result | Verdict |
| --- | --- | --- | --- |
| `tools/ref-shot/` (`capture`, `init-shot.lua`, `hook/`, `shots/*.lua`: terrain, units, ui, hud, hud-move, build-progress, faction-acu, team-colour) | Pauses the original at the first sim tick, snaps the camera per shot, logs `REFSHOT|SETTINGS` (camera) and `REFSHOT|ACU` poses, saves the unscaled window (Retina, title bar included). Options `/refui /refclean /refbare /refwait /reffactions /refshadows`, per-shot `select`, `sim` orders, `resume` | Delivered terrain (clean, bare, lit, fog, noshadows), units, four faction ACUs, HUD selected/unselected, 13 build-progress frames, lobby, menu. Basis of every render number in section 5 | BRING on the original side. OSC side is ADAPT: OSC `--camera` takes x,z,zoom only (no height, heading, pitch); `--screenshot` exists; OSC's goldens need a headless surface that MoltenVK may lack (I) |
| `tools/lua-trace/` (`capture`, `init-trace.lua`, `trace.lua`, `hook/`, `summarize.py`, `diff.py`) | Wraps every global engine function, `moho.*` table and class `__spec` in each user and sim state; logs first-call order and counts. `/tracemenuskirmish` drives menu to lobby to launch with no input; `/autosave /autoexit /autoload` | Our menu boot calls exactly the original's 57 bindings (`lua_boot`); 60 s skirmish: 217 sim and 134 user bindings called; 10-minute skirmish: 301 sim bindings; traces `menu-skirmish`, `-2a`, `-4a`, `skirmish`, `skirmish-600`, `long-1800` | BRING. The tracer is Lua: it should run under OSC `--init` unchanged (I, unchecked) and gives the call counts OSC's static `check_retail_hooks.py` lacks |
| `tools/bp-dump/` (`capture`, `init-dump.lua`, `hook/`, `compare.py`, `defaults.py`) | Logs every `__blueprints` entry of the sim state as `BPDUMP` lines; `compare.py` lists blueprints, fields and values only one side has; `defaults.py` regenerates our defaults table | 3,778 blueprints (9 MB) on GOG 1.5.3599; ours matches in blueprint set and ordinals, apart from derived fields | BRING. Run the same hook on OSC through `--init` and diff: measures the blueprint gap in one step (section 5). Check first that OSC's Steam 3599 files hash equal to GOG's |
| `tools/sim-capture/` (`capture`, `init-capture*.lua`, `hook/`, `scripts/gallery.lua`, `scripts/motion-unit.lua`) | Logs `MOTION` (every N ticks), `VEL`, `THREAT`, `ECON`, `INTEL`, `FIRE/DAMAGE/DEATH`, `SHIELD`, `SIMSCRIPT`; scripted scenarios; `/simspeed 10` holds 6 to 8 times real time | `motion-300` (5 min), `motion-unit` (every tick to 2000), `long-1800` (30 min, 23 MB), `icx-600` (intel and economy), `gallery` (248 T2/T3/experimental units in 5 min), `combat-600` (+ `.setup`) | BRING (original-side hooks). Hard-coded `C:\GOG Games\...` and `SHGetFolderPath('PERSONAL')` in `init-capture.lua`: OSC has both functions, so the file needs only its paths replaced (ADAPT). Scripted scenarios beat natural games: the idea alone is worth carrying |
| `tools/input-scripts/*.txt`, `tools/slice-check/run` | Scripted input for our engine; the save/reload chain through the game's own menus | `ctest slice_save_load`: menu, skirmish, play a minute, save, exit; load, select, move, build, exit; 0 Lua errors | ARCHIVE (our `--script` format). Keep the idea for the automated play sessions JStar wants |

### 1.3 Comparators (log-only; no engine needed)

| Path | What it does | Proven result | Verdict |
| --- | --- | --- | --- |
| `tools/motion-compare/motion_compare.py` (138) | Per-blueprint speed, acceleration and turn rate; per-unit drift; `--max-drift ID=LIMIT` fails the run | `ctest sim_motion_capture`: tank within 1.0 u for 1,960 ticks (arrives tick 524, original 526); engineer within 3.2 u (301 vs 297); the test fails above 1.5 u and 4 u | BRING |
| `tools/intel-compare/intel_compare.py` (63) | First contact and blip counts per tick; `--check` needs first contact within 60 ticks and counts within 25% | `ctest sim_intel_capture`: first contact tick 1520 (original 1540); tick 6000: 161 remembered structures and 54 units in sight (original 151 and 49) | BRING |
| `tools/bp-dump/compare.py`, `defaults.py` | See 1.2 | Same 3,778 blueprints | BRING |
| `tools/lua-trace/diff.py`, `summarize.py` | Diffs a boot or run against the original's trace; first-call order and counts | `diff-menu-boot.md`: 57 of 57 boot bindings match | BRING |
| `tools/binding-report/binding_status.py` (82) | Per-binding support level (real, partial, noop, stub) beside the original's and our call counts | 60 s skirmish: of 217 called, 125 real, 68 partial, 21 noop, 3 stubs; 10 minutes: of 301, 145/106/26/24 | ADAPT: OSC has no support-level table, only `--binding-coverage` (names scripts call but nothing binds); feed it OSC's coverage output |
| `tools/image-compare/compare.py` (54; uv script, numpy and pillow) | Crops and halves a Retina reference (rows 56 on), searches a +-N px offset, prints mean difference of 255 and the share within 8 and 16; `--diff` writes a map | Main menu 0.13/255; terrain 2.12 to 3.40; props 2.88; corner with ACU 3.04; ACU close-up 14.56 (render.md) | BRING. ADAPT the crop and scale for 2560x1440 frames; no ctest and no perceptual metric yet |
| `tools/compare` (61) | Reads the `.setup`, builds `sim_probe` arguments, runs the matching comparator; refuses a capture without a manifest | Ran combat-600 after a fix on 2026-10-14 | ADAPT: the runner is hard-wired to `build/engine/sim/sim_probe --tool --option --factions --no-civilians`. Replace with OSC's `opensupcom --init ... --map ...` |
| Stub accounting: `sim_probe --allowed-stubs`, `engine/sim/tests/allowed-stubs.txt`, `lua::BindingTable` | A capture ctest fails when a stub not on the list is called, or a listed binding stops being a stub; list only shrinks | 19 stubs at start (2026-10-14); used by `sim_motion_capture`, `sim_intel_capture`, `sim_ten_minutes` | ADAPT: merge with OSC `tools/check_lua_stubs.py` (static baseline) by adding the dynamic "was it called" half |

### 1.4 Gaps in what we have (work the new project needs and nobody built)

| Missing | Why it matters | State |
| --- | --- | --- |
| Economy comparator | ECON lines are read by hand | `tools/combat-compare` and an economy comparator were planned, not written |
| Combat comparator | Combat-600 numbers (hit rate 75%, 27 scout deaths, 9 mass extractors lost in the icx-600 setup) are not pinned in a test | Uncommitted weapon patch `work/logs/s2-combat-wip.patch` |
| Image compare in a ctest, with regions and masks | Look checks run by hand | None |
| Automated play session through the tech tree | JStar's headline contribution | Closest parts: `gallery.lua`, `menu-skirmish.txt`, `slice-check/run` |
| Play recorder (idea P3 in notes/roadmap-opensupcom-mac.md) | Findings from human play | Not started |

## 2. Agent infrastructure

| Path | What it does | Proven result | Verdict |
| --- | --- | --- | --- |
| `.agents/githooks/pre-commit` (55) | Rejects `downloads/`, `work/`, game types (`.exe .dll .bin .scd .scmap .sca .scm .dds .gpr .rep .gzf`), files over 1 MiB, an `MZ` header, untracked files in touched folders (merges exempt), a bad `STATUS.md`, and any commit not covered by a passing check receipt | `scripts/check` runs 10 synthetic commit cases (plain text, MZ header, 1.1 MB file, `downloads/`, `.scd`, receipt edited after check, failed check, merge before check, ...) | BRING. OSC has no such hook (`core.hooksPath` unset; `.gitignore` lacks game types) though its policy bans game data and golden PNGs; ADAPT the list: add `.nx2 .oscsave .oscreplay` and `*.png` outside test fixtures |
| `.agents/hooks/block-git-bypass.sh` (8) | Claude PreToolUse hook: blocks `--no-verify`, `-n`, `add -f`, `-c core.hooksPath` | 6 cases in `scripts/check` | BRING |
| `.agents/hooks/block-real-input.sh` (14) | Blocks `osascript`, `cliclick`, `game-window click/drag/scroll/key/type/wait` and computer-use tools unless JStar created `~/.supcom-input-ok` | 3 cases in `scripts/check`; real input used only in JStar's AFK window 11:51-12:45 on 2026-10-14 | BRING (it is JStar's global rule, not SupCom's) |
| `.claude/settings.json` | Wires both hooks, the `supcom` folder marketplace, and `game-porting-skills@game-porting-toolkit` | Plugins load | ADAPT: the marketplace path is absolute (`/Users/jstar/Projects/SupCom/.agents/mods`) |
| Check receipt: `scripts/tree-snapshot` (12), `work/check-last.{txt,manifest}` | Records a content hash of the tree the check ran on; the commit hook compares | Replaced a time-based receipt after "committed past a failing check" twice | BRING |
| `scripts/check` (208) | Mixed: syntax checks of scripts, hook self-tests, capture.py self-test, STATUS limits, Lua-test guard, then engine build and ctest (40 tests), then ASan rerun | Last runs passed | Split: hook and script self-tests BRING; engine build and ctest ARCHIVE; OSC already has clang-tidy ratchet, format check, `check_*` ratchets and 18 `arch` tests |
| `scripts/land` (106), `scripts/pause-report` (61), `scripts/status-track` (52), `scripts/worktree-setup` (18), `scripts/status-limits` (12) | Merge a branch in the clean worktree `work/land-tree`, replace the track's STATUS block, run the check, fast-forward main; report what a pause would lose | 6 land cases in `scripts/check` (failed check leaves main alone, dirty main refused, good branch becomes one merge commit) | ADAPT: STATUS block logic assumes our `## Tracks` layout; `worktree-setup` symlinks `work/*` where OSC uses `OSC_FA_PATH` and `$OSC_GOLDEN_DIR`; OSC merges PR batches ("Land #650 ... one commit per PR") |
| `.agents/mods/supcom-session` (`/land`, `/handoff`; skills `session-practice`, `landing`) | Plugin around the scripts above, plus guidance on choosing evidence, proposing interface changes, writing a handoff | In use since 2026-10-14 | ADAPT with the scripts |
| `.agents/mods/supcom-capture` (`/supcom-capture:capture`, `/supcom-capture:compare`, `/supcom-capture:game`; skill `capture-practice`) | Commands that wrap the capture tools, with a watcher posting phase changes, errors and a 5-minute heartbeat; skill on when a capture is worth its cost | In use | BRING (commands name our tool paths: ADAPT the `allowed-tools` lines) |
| `.agents/mods/supcom-metal` (`/gpu-frame`, skill `metal-work`, reminder hook) | Points an editing session at Apple's Metal 4 skills; captures one GPU frame | Hook syntax-checked only; `--gpu-trace` is our engine's flag | ARCHIVE (Metal 4 renderer) |
| `scripts/gpu-frame` (14) | Runs the engine hidden with `--gpu-trace`, then `gpudebug -t` | Needs `build/supcom --gpu-trace`, which S1 never added | ADAPT for MAC-3: use `MTL_CAPTURE_ENABLED` under MoltenVK |
| Apple `game-porting-skills` plugin (marketplace `apple/game-porting-toolkit`) | Metal 4 and GPU debugging skills | Enabled project-wide | ADAPT: keep `using-gpucapture`, `using-gpudebug`, `debugging-rendering-issues`, `using-metal-validation` (work under MoltenVK); ARCHIVE the Metal 4 translation, synchronization, resources and pipeline skills |
| `lldb` MCP (project-local, `DYLD_FALLBACK_LIBRARY_PATH` set to Xcode-beta's LLDB libraries) | Lets an agent run a native build under LLDB | `claude mcp list` shows it connected; no recorded crash session | BRING (any native Mac build) |
| `scripts/status-page` (775) and `work/status/{dashboard.json,index.html}` | One data model writes the JSON for agents and the HTML for people; reads `sim_probe`, `lua_boot_probe` and the last check; weights milestone 0.60, fidelity 0.25, coverage 0.15 (62.7% on 2026-10-14); published to https://claude.ai/artifact/3qYQhuVHbSpCQf7Wxwv9Pb | Regenerates in seconds; overlap with OSC `tools/status_metrics.py` | ADAPT: replace `MILESTONE_STEPS` and the probes with OSC's; today the HTML does not read the JSON (both are generated), JStar's plan wants that |
| `scripts/ghidra-py` (16), `ghidra-lock` (31), `ghidra-rtti-classes` (34), `rea`, `rea-refresh`, `dossier.py` (246), `lua_bindings.py` (312), `faf_names.py` (331) | Ghidra and REA tooling: waits for the one-writer lock, ignores a stale lock, RTTI class recovery with a local fix for Ghidra's infinite loop, per-binding dossiers, binding list, FAF name port | Rebuild recipe in `docs/toolchain.md`; lock tests in `scripts/check`; `dossier.py --all` writes 1,218 dossiers in seconds | BRING, but they stay where the Ghidra project lives; OSC gets their output, not the tools |
| `scripts/asan-rerun` (17), `cmake/sanitize.cmake` | Reruns signal-killed tests under ASan and UBSan | One synthetic test in `scripts/check` | DROP: OSC has a `linux-asan` CI job; add a macOS preset instead |
| `AGENTS.md` (173 lines), `STATUS.md` (167; limit 170), `docs/toolchain.md` (634), `docs/architecture.md` (229) | Project rules, current state, procedures, module map | Docs kept short by `scripts/status-limits` | ADAPT: carry the rules in section 4; OSC has no AGENTS.md (its `.gitignore` excludes `/.claude`), so decide where agent guidance lives |

## 3. Knowledge and evidence

Top constraint repeated: rows marked "local store" are never committed to a repo that follows OSC's policy.

| Item | What it is | Proven result | Verdict |
| --- | --- | --- | --- |
| `work/ghidra/SupCom.gpr` (875 MB) | Saved Ghidra project: GOG and FAF executables | 64,918 functions; 345 FAF names by Function ID hash; 3,891 C++ classes from RTTI; 1,195 bindings named `Lua::<Side>::<Class>::<Name>`; 14,001 faf-re matches (11,022 renamed); 18,285 (28%) still `FUN_` | BRING (local store; one opener at a time). Our own check of faf-re: its 728 shared binding addresses agree with ours; about 1 in 10 byte matches disagree with earlier names; a struct layout was wrong (FA-Binary-Patches PR 176) |
| `work/lua-bindings.json` (1,218) and `work/lua-bindings-vs-faf.json`, `work/logs/missed-bindings.md` | Sim 686, User 461, Core 70, `SHGetFolderPath` 1, each with class, description, native address; 4 found as data Ghidra missed | GOG has every FAF-documented function except 19 globals and 19 methods that match FAF's patch notes | BRING as a finding: compare with OSC `tests/integration/binding_baseline_retail.txt` (12 globals and 7 methods unbound). Theirs is derived from the executable's strings; ours has addresses |
| `work/traces/` (80 MB, 57 files) | Captures in section 1.2 plus `Game.prefs.before` | See 1.2 | BRING (local store). Captured on GOG 1.5.3599, CrossOver 26.3, Rosetta |
| `work/logs/screens/` (368 MB, 286 files) | Reference PNGs: `ref-terrain-{overview,center,corner}-{clean,bare,lit,fog}`, `ref-units-*`, `ref-faction-acu-acu-{uef,aeon,cybran,seraphim}`, `ref-hud*`, `ref-build-progress-*` (13), `ref-lobby`, `ref-ui`, `ref-team-colour` | Terrain from CrossOver Auto backend matches wined3d within 0.05% of pixels | BRING (local store, like OSC's `$OSC_GOLDEN_DIR`) |
| `work/game` (8 GB, extracted GOG install) and `downloads/` | The player's own game | Identities in STATUS.md (sha256) | BRING by reference only; never committed |
| `work/logs/s2-*-spec.md` (7 files, about 250 KB) | Decompile-derived specs: motion (CAiPathSpline::Generate 0x5b2f10), collision, intel (CIntelGrid::Raster 0x00507470), threat (CInfluenceMap), targeting, derived blueprint rules, trace table | Each drove a capture-checked change (section 5) | BRING; commit concise versions with addresses and no game text, because they exist nowhere else |
| `engine/sim/sim.md` (677 lines) | Rules, tick, commands, threat, orders, determinism, saves, recon, snapshot, bindings | See section 5 | BRING as findings (the facts, not the code) |
| Blueprint defaults: `engine/sim/blueprint_defaults.inc` (395 constants per kind), `blueprint_defaults.cpp`, derived-field rules in sim.md | What the original's C++ merges into every `.bp` table | Dump match: same 3,778 blueprints and ordinals; known misses: footprints of 62 of 194 mobile units, last-digit `InertiaTensor` | BRING the method (dump, defaults.py); the `.inc` is generated from game data, so regenerate locally rather than commit |
| `engine/render/render.md` (476), shader path decision | The 11 `.fx` files parse (266 techniques, 290 passes, 88 samplers); 254 of 254 bindings translate with vkd3d 1.19 plus SPIRV-Cross and compile with Metal 4 | `ctest fx_corpus`, `shader_import_corpus`, `msl_compile` | BRING as a design option for OSC (they hand-port GLSL); needs a maintainer agreement and a check of their ban on HLSL text in the repo (runtime translation of the player's own files copies nothing) |
| vkd3d findings (`notes/scratchpad.md`, 2026-10-12) | Three repros: `vertexShader` as a function name, `sincos` not lowered for `vs_1_1` (14 bindings), `texkill` write mask ignored; fx_2_0 effect compile fails on all 11 files | Workarounds in the importer; not posted upstream (JStar decides) | BRING (findings for vkd3d, not OSC) |
| D3D9 state mapping notes (render.md "Render states with no Metal pipeline equivalent") | Alpha test as `clip()`, quantised to 0-255; `ColorWriteEnable` bit order reversed; half-pixel correction; `COLOR0` is BGRA; unbound textures read black | Menu pixel-identical to the first hand-written MSL; menu 0.13/255 | BRING as cross-checks for OSC's GLSL port |
| `engine/formats/*.md` (dds, sca, scd, scm, scmap) | Format notes | Every file in the corpus parses (`ctest scd/dds/scmap/scm/sca`) | ARCHIVE: OSC reads the same formats ("every retail map to its last byte") |
| Save format (sim.md "Game setup and saves", `save.h`, format 2) | Replay-style text save: setup, seed, order log, digest every 600 ticks | `ctest sim_save`; 5-minute games reload to an identical state | DROP: OSC's full-state save (Lua heap and coroutines) and `.oscreplay` supersede it |
| Determinism notes (sim.md) | Two 18,000-tick runs on different heaps give identical logs (2,176,551 lines); Lua tables keyed by tables iterate in address order | `ctest sim_determinism`; a first attempt proved nothing because both runs shared heap addresses | DROP the code; BRING the heap-shift trick as a test idea (OSC already has `data.determinism`) |
| `docs/crossover-recipe.md` (265) | Player recipe for the original and FAF 3839 in CrossOver: bottle, `Game.prefs`, fullscreen 2560x1440, FAF walkthrough, checklist, known problems | Checked 2026-10 on macOS 27.2, CrossOver 26.3 | BRING (reference run setup; a user doc for the fork if CrossOver stays a fallback) |
| Direction papers: `work/logs/opensupcom-eval.md` (28 KB), `direction-fable.md`, `direction-gpt.md`, `review-codex.md`, `review-opus.md`, `opensupcom-moltenvk.md` | Evaluation of OSC and second opinions; MoltenVK trial | Both second opinions recommend contributing to OSC | BRING as context for the planner |
| `notes/opensupcom-mac-trial.md` | OSC builds unmodified on this Mac (M4 Max, macOS 27.2, MoltenVK 1.4.2): 6,000-tick 2-AI game, exit 0; 1,492 unit tests pass; 249 gate tests pass, 1 fails (`data.trail-render-test` check 8b); 1080p, about 290 units: CPU 7.4 ms, GPU 4.5 ms mean | Evidence in `build/experiment/evidence*` | BRING |
| `log/` (15 files), `notes/tooling-plan.md`, `notes/roadmap-opensupcom-mac.md` | Session history and plans | Never edited after the fact | BRING as history |

## 4. Process lessons (each with the failure and what now enforces it)

| Lesson | Failure it came from | Enforced by | Verdict |
| --- | --- | --- | --- |
| A commit needs a passing check on exactly the content committed | Committed past a failing check twice (2026-10-12) | Pre-commit receipt on a tree hash (`scripts/tree-snapshot`) | BRING |
| One worktree per session; land in a clean tree | S1's files landed in S2's commit; checks red on others' work | `scripts/worktree-setup`, `scripts/land` | ADAPT (see section 2) |
| Never rebase main; push plainly | `git pull --rebase` flattened merges on origin; six commits exist twice | AGENTS.md rule; JStar's global rule | BRING |
| `git add` new files before a path-limited commit | `git commit -- <paths>` skipped untracked files; two pushed commits pointed at missing hooks | Pre-commit untracked-in-touched-folders check (merges exempt) | BRING |
| Real mouse, keyboard and focus belong to JStar | A session used his mouse before any gate existed | Input file `~/.supcom-input-ok` plus hook; scripted, hidden validation otherwise | BRING |
| Never read a capture that is still being written | Captures read mid-write | `.partial` logs renamed on finish | BRING |
| A running shell script must not be edited in place | Editing a capture script mid-run broke its last lines twice; a subagent edited `scripts/check` while others ran it | `main() { ...; }; main "$@"`; hooks copied to `work/capture-run/`; edit a scratch copy, then swap | BRING |
| Compare a failing setup with a known-good recipe step by step before replacing a component | Proposed replacing all of Wine before diffing the bottle against FAF's recipe | JStar's global CLAUDE.md lesson | BRING |
| Match what the comparison is keyed on | Motion compare matched wrong units (the original reuses entity ids, factions differed); civilians changed entity ids | Key by id and blueprint; `.setup` manifests; comparators refuse a mismatch | BRING |
| A determinism check must change what it could depend on | Two runs of one binary share heap addresses, so the first check proved nothing | `MallocNanoZone=0` and a shifted heap in `sim_determinism` | BRING |
| Compare lighting only against fog-free references | The "shadow factor 0.5" was fog of war | `/nofog` for light comparisons (render.md Traps) | BRING (rendering) |
| Wrap the engine method, not the Lua class method | Wrapping class methods missed subclasses that had copied them | `globalInit.lua` hook wraps `CreateProjectile` and `AdjustHealth` | BRING |
| Do not time a traced run by the wall clock | Tracing slows the game below real time; the save run ended before its save | Wait for the game's own `/autoexit` | BRING |
| A stalled job needs a heartbeat | RTTI class recovery spun 35 minutes before anyone saw it; `jstack` found the loop | JStar's global rule (watcher with 5-minute heartbeat); `/supcom-capture:capture` command | BRING |
| Protect Lua calls in tests | `lua_dostring` in Lua 5.0 ends the process on a script error with no output | `scripts/check` rejects it; `tests::runLua` | ADAPT (OSC uses C++ unwinding, so the hazard differs) |
| Specs from agents propose; captures decide | Sonnet research agents wrote the motion, collision and intel specs from the executable | When sources disagree, the capture of the original wins over a decompiler reading (`session-practice` skill) | BRING |
| Scripted scenarios beat natural games | Tier gallery covered 248 T2/T3/experimental units in 5 minutes at speed +10 | `capture-practice` skill | BRING |
| Dropped by both reviewers: scheduled landing, a Haiku merge minder, a 24-hour smoke cache, a capture registry, a blocking pause gate | Codex (GPT 6.1 Sol xhigh) and Opus 5.5 (xhigh) reviewed `notes/tooling-plan.md` | Plan kept to items that prevent an observed failure | BRING (a template for the reviews JStar wants on the new plan) |
| Bound tool output | Twelve outputs hit truncation; one REA print cost 57,000 tokens (retro R3) | `--token-limit`, full results in `work/logs/` | BRING |
| A test run must not overwrite a delivered capture | A test run overwrote S1's reference images | Test runs use their own names | BRING |
| Worktree runs use their own binary by absolute path | `work/logs` is a symlink into the main checkout, so relative paths ran main's binary | render.md Commands | ADAPT |
| Metal 4 tracks no hazards: queue barrier at each pass start | Terrain normal target had a garbage top band | render.md Traps | ARCHIVE |

Rules from `~/.claude/CLAUDE.md` "How I like agent work run" (all six carry over; they are JStar's, not SupCom's):

- Enforce, do not remind: a repeated rule becomes a script, hook or plugin command; prose holds only judgement.
- Vertical slices first: the thin end-to-end path, then polish; step back to check feedback loops and wasted effort.
- Long sessions report the key result and any ask in the first three lines; heartbeats go to the watcher.
- Budget: check plan usage before long runs; cheapest model that does the job; pause at a documented point.
- Second opinion (another model at high effort) on plans that shape many later sessions, before building.
- Real input only inside a window JStar grants, with an automatic end.

## 5. Engine code: what OSC has, and what our findings could improve

Our engine is 31,806 lines with tests (about 27.8k without), 40 ctests, 381 commits. OSC `src/` is about 148,000
lines (sim 46.6k, lua 38.4k, renderer 36.6k, app 9.3k, ui 4.2k) with 1,495 unit cases and 257 gate tests. All
code verdicts below are ARCHIVE; what moves is the finding. "Check" says how OSC could confirm a finding.

| Module (lines) | Our state (proven) | OSC coverage (docs/current-state.md) | Findings that could improve OSC | Verdict |
| --- | --- | --- | --- | --- |
| `engine/sim` (12,095) | AIs play X1MP_006 headless, upgrade to T2, 30 game minutes in about 30 s, 0 Lua errors; economy tracks `long-1800` (8-11 mass/s at 20-30 min vs original 5-10 at 20, 11-23 at 30); motion within 1 u/1,960 ticks; recon first contact within 20 ticks; 19 stubs allowed | Far ahead: orders, combat, air, naval, transports, shields, veterancy, capture, enhancements, silos, campaign, 18,000-tick four-AI games, Moho drive, formations, intel grids, influence map | See the list below this table | ARCHIVE |
| `engine/render` (3,936; Metal 949) | Menu 0.13/255; terrain 2.1-3.4/255; props 2.88; corner with ACU 3.04; ACU close-up 14.56. Meshes drawn, no water, sky, shadows, fog, effects | Far ahead in coverage: terrain, water, sky, shadows, bloom, particles, beams, decals, fog, strategic icons; Vulkan only, no backend interface; its look is unmeasured against the original (current-state.md "no reference captures exist here") | Original-referenced numbers (above); the `.fx` translation pipeline; mesh facts (instanced only, `material` and `colorLookup` fields, `time` = tick + fraction mod 36000); `environment` cube per technique; fog darkens explored terrain to about half (I) | ARCHIVE (tag the Metal 4 renderer; no tag exists, `git tag` is empty) |
| `engine/audio` (3,430) | All 181 XACT files read; RPC curves, ducking, listener, loops; `sim_sounds`: 159 requests, 88 started, 26 cues, all resolve; hardware ran once, nobody listened | Has XWB/XSB parsers, categories, RPC curves, ducking, instance limits through miniaudio; "checked by data and timing tests only"; listening pass needs a person | Variable-length cue entries (step by the stored entry length; 75 banks failed otherwise); every wave in the corpus is PCM16; 19 cue refusals are the original's rules (once per frame, LOD cutoff, instance limits); `StopLoop(entity, handle)`; open in both: X3DAudio pan matrix, `Rumble*` variables, `WaitFor(handle)` | ARCHIVE |
| `engine/ui` (2,772), `engine/text` (487) | Menu runs 1,200 headless frames calling exactly the original's 57 bindings; `CMauiItemList` (19 bindings); stb_truetype with GDI metrics; skirmish setup screen | Full MAUI, input, focus, key map, minimap, build templates (4.2k lines) | MAUI bitmap drawn size is texture size minus 2 times border (explained a 10-point offset); item list row height = font height + external leading; the 0.13/255 menu match is a check OSC cannot make today | ARCHIVE |
| `engine/app` (4,789) | One process, one thread: `WorldSession`, `UserSession`, lobby, saves, `WorldInput`, scripted input; `slice_save_load`, `ingame_ui`, `world_session`, `world_sound` | Complete game loop, lobby, score, campaign, replays, LAN and GPGNet | Camera constants from GOG decompiles: wheel scales target zoom by 2^(-0.4 x notches), log2 easing, 4 px drag tolerance, 90 px arrow pan, FOV 65 to 60, pitch 40 to 89.9 degrees (research agent, S/O mix) | ARCHIVE |
| `engine/lua` (1,918), `third_party/lua-lang` | lua-lang (MIT) with GPG changes; `lua_Number` is `float`; boot probe; `lua_corpus`: 2,320 `.lua` and 4,066 `.bp` compile | Own patched Lua 5.0.3, `lua_Number` is `double` (`third_party/lua-5.0/lua.h:93`) | Original stores numbers in 4 bytes (`lua_pushnumber` 0x0090c5a0 uses MOVSS; `lua_tonumber` 0x0090c250 returns `(float)slot[1]`); mixed-type `<` compares type tags (0x00928f40, `aibrain.lua` `GetAllianceEnemy` relies on it); indexing a non-table falls back to the type's metatable; thread-metatable out-of-bounds bug in lua-lang (NUM_TAGS 8; upstream draft pending) | ARCHIVE |
| `engine/vfs` (600), `engine/formats` (1,105), `engine/platform` (414) | Mount precedence as `CVFSImpl`; all formats parse; fixed-size AppKit window | Same capabilities (VFS, formats, GLFW) | None beyond format notes | ARCHIVE |
| Tests (40 ctests) | Capture tests: `sim_motion_capture`, `sim_intel_capture`, `sim_ten_minutes` | Gate, golden, arch, mp labels | The pattern: a capture-backed test that skips without the corpus | ADAPT (pattern only) |

Sim findings OSC could use, each with its check:

| Finding | Number or address | Check against OSC |
| --- | --- | --- |
| Lua numbers are 32-bit floats in the original | 0x0090c5a0 MOVSS, 0x0090c250 `(float)slot[1]`; `SuspendCurrentThread` pushes 0x3f800000 | Run a script that accumulates tick time or positions past 2^24 on both; OSC keeps doubles (I: visible effect unknown) |
| Blueprint defaults merged into every `.bp` table | 395 constants per kind; type coercion (`ReclaimMassMax = ''` becomes 0, `ManualFire = 1` becomes `true`); derived footprint, skirt, inertia, `MaxSpeedReverse` rules | Run `tools/bp-dump` on OSC. In `src/` I found `kRangeDefaults` for particle physics and prop reclaim coercion only, and no `BlueprintOrdinal` (grep, I) |
| `Entity:Kill` runs `OnKilled` once | 0x691cc0, flag at entity+0x99; without it chained death explosions stalled a run after 15 game minutes | Death-chain scenario in the gallery |
| Movement per tick | `CAiPathSpline::Generate` 0x5b2f10: turn at most `max(TurnRate, speed/TurnRadius)`, slip limit `MaxSteerForce`; steering starts 4 ticks after a Lua order (3 if applied at tick start); tank accelerates 0.034 u per tick and pivots 9 degrees per tick | `motion-unit` capture through `motion_compare.py --max-drift` |
| Pathing granularity | 1 u cells with the vertex-step slope rule (FUN_005649f0); our 2 u averaged slope made groups arrive about 150 ticks early (climbed cliffs); with the rule tank 13 travels 146 u in both and arrives 1149 vs 1157 | OSC default is a 2-unit grid; `--moho-pathing` is opt-in (23 of 24 units through the gap). Compare route lengths on `motion-unit` |
| Formation speed | Units drive at most 0.85 x the slowest member's `MaxSpeed` (CalcFormationSpeed 0x59a540); slots via RunScript 0x567240 | `motion-unit` formed group: original arrives ticks 1447-1497, ours 1365-1401 |
| Recon passes | Army k repaints on ticks where tick mod army count equals k (Sim::SimBeat 0x00749E90); asymmetric disk rows (CIntelGrid::Raster 0x00507470) | `intel_compare.py --check` on `icx-600` |
| Threat map | 14 lanes per source army; entries hold strength 9 updates then lose 0.02 per update; update when tick mod 30 equals army index | `THREAT` lines in `long-1800` and `motion-300` (ticks 600 to 3000) |
| Targeting | Candidates from the army's blips within `MaxRadius`, ranked by `TargetPriorities`, rank kept only with LOSEver, re-pick every ceil(`TargetCheckInterval` x 10) ticks (`s2-targeting-spec.md`) | `combat-600`: original hit rate 75%, 27 scout deaths; 9 mass extractors lost in `icx-600` (ours lost 52 before targeting existed) |
| Economy | Requests met in proportion to stored plus income; 30-minute curve | `ECON` lines in `long-1800` (OSC reports 639 units at tick 6,000 for its AIs; our original-side unit counts are in `ECON ... units bp=n`) |
| Open problems we never closed | Footprints of 62 of 194 mobile units; `InertiaTensor` last digit; reversing and backing up; formation catch-up; jammers and stealth | Same list likely applies to OSC |

## 6. OSC already has: merge, do not duplicate

| Ours | Theirs | How they differ | Suggested merge |
| --- | --- | --- | --- |
| `tools/sim-capture` hooks, `.setup` | `tools/moho_probes/` (about 14 probe scenes on SCMP_009, `PROBE` lines, answers in a README table, run on Proton by hand) and `tools/retail_ref/retail_ref.py` | Theirs: small hand-written scenes, no comparator, manual table. Ours: long-game tick logs, scripted scenes, comparators, manifests | Express their scenes as `/simscript` files; one log format; keep their README table as the result record |
| `tools/ref-shot` and `image-compare` | `--screenshot`, `--golden`, `$OSC_GOLDEN_DIR` (7 pixel tests at 0.1%), `retail_ref.py --screenshot` | Their baselines are their own output (regression, not fidelity) | Ours supplies original-side images; their golden framework supplies the fixed clock and offscreen path |
| `tools/binding-report`, `scripts/lua_bindings.py` | `--binding-coverage`, `tests/integration/binding_baseline_retail.txt`, `tools/check_lua_stubs.py` | Theirs is static; ours adds call counts from the original | Feed the original's call counts into their coverage report |
| `tools/bp-dump` | `tools/check_blueprint_fields.py` (fields only the engine reads, 304 engine-only fields) | Theirs is a static name check; ours compares values | Add the dump diff as a second ratchet |
| `tools/lua-trace` | `tools/check_retail_hooks.py` (167 callbacks, static list) | Theirs lists callbacks; ours records which are actually called, in order | Use the trace to rank their baseline |
| `sim_determinism`, replay saves | `data.determinism`, `--checksum-trace`, `tools/checksum_diff.py`, `tools/cross_os_replay.py`, CI `cross-os-play` | Theirs is stronger (domains, cross-compiler, Windows with Linux) | DROP ours |
| `.setup` manifests | `docs/validation/YYYY-MM-DD-<sha>.md` records | Theirs is prose per commit; ours is machine-readable per capture | Keep both: manifest for a run, record for a commit |
| `scripts/status-page`, `dashboard.json` | `tools/status_metrics.py` (metric markers in `current-state.md`), `docs/ROADMAP.md` (464 lines) | Theirs keeps prose numbers true; ours renders a tracker | Use their markers as a data source for the tracker |
| `scripts/check`, pre-commit | CI (GCC 14, Clang 18, ASan, MSVC, cross-OS Wine), `tools/check_*.py` (9), `check_format.sh`, clang-tidy ratchet (baseline 30), 18 `arch` tests | Theirs runs on a server and has no local commit gate; no macOS job | Add a macOS arm64 job; keep our pre-commit guard locally |
| `tools/faf-autorun`, FAF client app | `tools/faf_custom_game.py` (scripted GPGNet client hosts SCMP_009 on FAF data), `tools/faf_regression.py` | Theirs drives OSC; ours drives the original | Both are needed: same scenario on both |
| none | `tools/bench.py`, `--bench`, `--render-bench` (CPU/GPU frame times at 1080p) | We have `sim_probe --profile` only | Use theirs for MAC-3 |
| `/land`, `worktree-setup` | CONTRIBUTING.md: one logical change per commit, PRs, worktrees for parallel checkouts | Similar intent | Adopt their commit style; keep landing only if the fork needs it |

Cheapest proofs, in order (none has been run):

1. Mount `tools/bp-dump/hook` through `opensupcom --init`, then `tools/bp-dump/compare.py` against `work/traces/bp-dump.log`.
2. Run `tools/lua-trace/trace.lua` under OSC for the 60 s skirmish and diff with `work/traces/skirmish.log`.
3. Run the `motion-unit` script through OSC and `motion_compare.py --max-drift`.
4. Check that OSC runs `/map X /faction N` command-line launches (`SinglePlayerLaunch` appears in `src/lua/session_manager.cpp`; `GetCommandLineArg` exists, M147d).
5. Run `image-compare` on an OSC `--screenshot` against `ref-terrain-*`.

## 7. Not checked

- Nothing was built or run. No result in this file was reproduced; all come from our docs, logs and test names.
- OSC statements rest on `grep` and docs at `1a873786`. Not checked: that our hooks run unchanged under `--init`,
  that OSC's camera flags can be extended, that MoltenVK offers a headless surface, the line-level provenance of
  OSC files that cite faf-re, and OSC's behaviour on any capture.
- `work/logs/opensupcom-eval.md` carries a longer comparison; this file does not repeat it.
- Counts of lines come from `wc -l` on the current tree; counts of tests come from `ctest -N` (40 tests).
- Not in the inventory: other agents' uncommitted work (`s2-sim`, `claude/s3-audio-222d6a`, `claude/quizzical-saha-6fc0c0`
  branches exist; the combat patch is `work/logs/s2-combat-wip.patch`).
