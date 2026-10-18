# Toolchain and procedures

Procedures for the Mac-developer toolkit in `mac/`: playing and building OpenSupCom
(OSC), reference captures of the original, comparisons, and the Ghidra
project. Read it when a task needs one of these procedures;
[STATUS.md](../STATUS.md) owns the current state. Run commands from the
checkout root (`~/Projects/OpenSupCom`, the fork) unless a step says otherwise.

## Play and build OpenSupCom

The checkout holds upstream's engine, the Mac engine changes and this toolkit
in `mac/`. The scripts find the checkout from their own path (`OSC_ROOT`
selects another). The Mac build recipe is in `mac/recipe/`:

- `mac/recipe/env.sh`: sourced from the checkout root. Points vcpkg, temp files
  and caches at the checkout's ignored `.local/`, the game at `mac/work/game`
  (`OSC_FA_PATH`), and `VULKAN_SDK` at the local SDK (used to configure the build;
  set `VULKAN_SDK` first to use another SDK). It does not choose a driver: the build
  ships both and the game prefers KosmicKrisp (Metal 4, Apple Silicon, macOS 26+).
  `VK_LOADER_DEBUG=driver` prints the driver the game loads.
- `mac/scripts/upstream-news`: fetches upstream, lists what landed since the fork's `main`
  (Mac-area items marked `MAC`) and open upstream PRs in Mac areas, and prints the merge
  command. Run it before starting any Mac change. `mac/scripts/play` prints a one-line note
  when `main` is behind upstream.
- `mac/recipe/build.sh`: configures and builds `build/play` (Ninja, RelWithDebInfo,
  arm64, triplet `arm64-osx`) with the vcpkg overlay ports in
  `mac/recipe/overlays/` (`minizip`, `zlib`). It prints `BUILD_OK` or
  `BUILD_FAIL`; logs are `.local/configure.log` and `.local/build.log`. After
  the SDK or the overlays move, delete `build/play/CMakeCache.txt` first: CMake
  keeps the old paths.
- `mac/scripts/play` builds (`--build`) and starts the game: windowed 2560x1440 by
  default; `--full`, `--size W H`, `--prefs` (the game's Video options decide),
  `--hud` (Metal performance HUD), `-- ARGS` for extra `opensupcom` arguments.
  It passes `--fps-cap -2` (2 below the display's refresh rate) unless ARGS hold
  their own `--fps-cap`; the game reads only the first one.
  The game log is `~/.local/state/opensupcom/logs/opensupcom.log`.
- `mac/scripts/setup` (idempotent; `--check` reports differences and writes
  nothing) installs the guards outside the tree, so they also run on branches
  without `mac/`: it copies `mac/agents/githooks/` (`pre-commit`, `pre-push`) to
  `.git/mac-hooks/` and sets `core.hooksPath` there, and copies the Claude hooks
  in `mac/agents/hooks/` to `.git/mac-hooks/claude/`. It writes those Claude
  hooks, Apple's game-porting-skills and the `supcom` plugin marketplace into
  `.claude/settings.local.json` (other keys kept), adds `.local/` and `/mac/work/`
  to `.git/info/exclude`, and disables pushes to upstream. Rerun it after a
  hook changes or the checkout moves; `mac/scripts/check` fails until then.
- The pre-commit hook refuses game files, PNG/JPG images, saves and replays,
  Windows executables, new files over 1 MiB, anything under `mac/work/`, and
  edits of earlier `mac/log/` entries. A commit that touches `mac/`, `AGENTS.md`,
  `CLAUDE.md` or `README.md` also needs `mac/scripts/check` to have passed on
  exactly the staged content. The pre-push hook refuses an `up/*` branch when any
  commit in `upstream/main..` touches `mac/`, `AGENTS.md` or `CLAUDE.md`.

Engine changes are proven by OSC's own tests, not by `mac/scripts/check`.
OSC's CONTRIBUTING.md names them: Catch2 unit tests (no game data, run in
CI), `ctest -L mp` (two-process multiplayer), and the regression gate
`ctest -L gate` on machines with the game, to run before every PR:

```sh
source mac/recipe/env.sh
build/play/tests/osc_tests
ctest --test-dir build/play -L mp --output-on-failure
ctest --test-dir build/play -L gate --output-on-failure
```

`mac/scripts/osc-render-check` renders the hidden SCMP_009 capture and fails unless the game's log line names the KosmicKrisp
driver and has no `[error]` lines. The smoke below does not touch the driver.

`mac/scripts/osc-smoke` runs the headless SCMP_009 skirmish:

```sh
mac/scripts/osc-smoke
```

It uses `--map /maps/SCMP_009/SCMP_009_scenario.lua --ai-skirmish
--ai-armies 2 --ticks 3000 --seed 4242`, with `--log` pointing to the
checkout's `.local/mac-smoke.log`. It prints that path and fails on a non-zero
exit or any `[error]` line. `mac/scripts/check` tests the runner with a stub;
it does not run the game.

Play tests: each session's game log and replay are copied to
`mac/work/playtests/YYYY-MM-DD/`.

### KosmicKrisp setup

The pinned Vulkan SDK is 1.4.363.0, installed under the ignored
`mac/work/vulkan-sdk/1.4.363.0/`. From the checkout root, download and verify it,
then install locally without changing system libraries or opening a window:

```sh
mkdir -p mac/work/downloads
curl -fL --output mac/work/downloads/vulkansdk-macos-1.4.363.0.zip https://sdk.lunarg.com/sdk/download/1.4.363.0/mac/vulkansdk-macos-1.4.363.0.zip
curl -fsSL https://sdk.lunarg.com/sdk/sha/1.4.363.0/mac/vulkansdk-macos-1.4.363.0.zip.txt | (cd mac/work/downloads && shasum -a 256 -c -)
unzip -q mac/work/downloads/vulkansdk-macos-1.4.363.0.zip -d mac/work/downloads/vulkan-sdk-1.4.363.0
QT_QPA_PLATFORM=offscreen mac/work/downloads/vulkan-sdk-1.4.363.0/vulkansdk-macOS-1.4.363.0.app/Contents/MacOS/vulkansdk-macOS-1.4.363.0 --root "$PWD/mac/work/vulkan-sdk/1.4.363.0" --accept-licenses --default-answer --confirm-command install copy_only=1
```

The SDK archive is 396,088,200 bytes, SHA-256
`163431e0203c8215286a17cf393643ce6b951f77d1b4f74ab30821a1f0beb09b`.
The installer also supplies MoltenVK. The game build ships both drivers and prefers
KosmicKrisp; it uses MoltenVK only when no KosmicKrisp device is found.

Identify the selected driver:

```sh
source mac/recipe/env.sh
DYLD_LIBRARY_PATH="$VULKAN_SDK/lib" "$VULKAN_SDK/bin/vulkaninfo" --summary
```

Expect `driverID = DRIVER_ID_MESA_KOSMICKRISP`. The SDK tool needs its library
path because this is a local installation. The build copies the SDK's loader and both
drivers beside the game (`build/play/vulkan/icd.d`); fork issue #1 tracks the rest of the
packaging. A graphics
check must render, as the headless smoke does not exercise the driver. For example:

```sh
mkdir -p mac/work/logs/metal4
OSC_VK_VALIDATION=1 VK_ADD_LAYER_PATH="$VULKAN_SDK/share/vulkan/explicit_layer.d" build/play/opensupcom --fa-path "$OSC_FA_PATH" --map /maps/SCMP_009/SCMP_009_scenario.lua --screenshot "$PWD/mac/work/logs/metal4/scene.png" --screenshot-frame 600 --log "$PWD/mac/work/logs/metal4/scene.log"
```

`--screenshot` keeps the window hidden and preferences in memory. Inspect
the image and log; unused shader-output warnings are distinct from validation
errors. SDK installation and driver-selection details:
[LunarG's macOS guide](https://vulkan.lunarg.com/doc/view/1.4.363.0/mac/getting_started.html).

Upgrading the SDK upgrades KosmicKrisp and MoltenVK: they ship as one version. Install the new
SDK beside the pinned one (same steps, new version), point `VULKAN_SDK` at it,
then run `mac/scripts/osc-smoke`, `mac/scripts/osc-render-check`, and a play test by
JStar. Only when all three pass, change the version in `mac/recipe/env.sh` and in the
`mac/scripts/check` pin, and keep the old folder until the new one has been played.
On this Mac (Modern level) the game must log KosmicKrisp; MoltenVK serves only
Intel Macs and older macOS (Compatibility level).

## Installed stack (macOS 27.2 arm64)

| Tool | Version and location | Role |
| --- | --- | --- |
| Ghidra | 12.1.4, `~/Applications/ghidra_12.1.4_PUBLIC`, Mac natives built locally | Primary decompiler and the saved project |
| OpenJDK | Homebrew `openjdk@21` 21.0.12.1 | Java for Ghidra |
| innoextract | Homebrew 1.9_14 (pulls Boost) | Extracts the GOG installer without running setup |
| uv | `~/.local/bin/uv` | Runs the pinned Python scripts (`pyghidra==3.1.0`, Python 3.12) |
| REA | `rea-agents`, latest, npm global install (`rea update`); `mac/scripts/rea` runs it | Evidence dossiers; temporary Ghidra imports |
| CrossOver | 26.3, bottle `SupCom` | Reference runs of the original game |
| Command Line Tools | 27.0, Apple clang 21.0.0, macOS SDK 27.0 | Not selected |
| Xcode-beta | 27.0 (27A5218g), `/Applications/Xcode-beta.app` | Selected (`xcode-select -p`); builds OpenSupCom |
| Vulkan SDK / KosmicKrisp | SDK 1.4.363.0, Mesa 26.2.99 (`269a955c89`), `mac/work/vulkan-sdk/1.4.363.0/macOS` | Vulkan on Metal 4 for Apple Silicon; the SDK the build uses |

Ghidra archive `mac/work/downloads/ghidra_12.1.4_PUBLIC_20260921.zip` (569,649,598
bytes) matched the official release digest
`ddac49f903da9d5bac833e5cc79395098b9c33cfd3279be5f31bd00387d2d4db`.

## Fresh setup

1. Clone the fork to `~/Projects/OpenSupCom`
   (`git clone https://github.com/Allmight97/supcom-engine.git ~/Projects/OpenSupCom`),
   add upstream (`git remote add upstream https://github.com/bwiemz/supcom-engine.git`),
   and run `mac/scripts/setup`: it installs the commit and push guards before anything is staged.
2. Supply your own game: place the three GOG installer parts in `mac/work/downloads/`,
   compare their SHA-256 with the identities in STATUS.md (`shasum -a 256
   mac/work/downloads/setup_*`), and extract into an absent directory:

   ```sh
   innoextract --extract --gog --output-dir mac/work/game 'mac/work/downloads/setup_supreme_commander_forged_alliance_1.5_(38101).exe' > mac/work/logs/extraction.log 2>&1
   ```

3. Install `brew install innoextract openjdk@21`, unpack the official Ghidra
   12.1.4 release into `~/Applications/` (verify the digest above, keep the
   execute bits), and build its Mac components:

   ```sh
   cd "$HOME/Applications/ghidra_12.1.4_PUBLIC/support/gradle"
   JAVA_HOME="$(brew --prefix openjdk@21)/libexec/openjdk.jdk/Contents/Home" ./gradlew buildNatives --no-daemon
   ```

4. Install the Mac build tools: `brew install cmake ninja` and the Vulkan SDK
   using **KosmicKrisp setup** above, then provision vcpkg in the checkout:

   ```sh
   mkdir -p .local
   git clone https://github.com/microsoft/vcpkg.git .local/vcpkg
   .local/vcpkg/bootstrap-vcpkg.sh -disableMetrics
   ```

   Then `mac/scripts/play --build`.
5. Run `mac/scripts/check`.

## The saved Ghidra project

The project `mac/work/ghidra/SupCom.gpr` holds every name, type and comment for
the GOG executable and FAF's base executable. Ghidra allows one writer: run
`mac/scripts/ghidra-lock` first and stop any holder it reports, and run pyghidra
scripts through `mac/scripts/ghidra-py`, which sets the Ghidra environment and
waits up to `GHIDRA_LOCK_WAIT` seconds (default 300) for the lock. The
rebuild scripts (FAF and faf-re name ports, C++ class recovery, Lua binding
names) and the per-binding dossier generator were retired with the native
engine; the tag `native-engine-final` in the archived repository Allmight97/SupCom keeps
them and their procedure (`docs/toolchain.md` at tag `native-engine-final` in the archived repo Allmight97/SupCom, or in `~/Projects/SupCom-archive-2026-10-16.tar.gz`).
Their outputs stay in
`mac/work/`: `mac/work/lua-bindings.json`, `mac/work/dossiers/`, `mac/work/game-analysis.json`.

## Querying the project

- Scripts: write a small `uv run` pyghidra script that opens the project
  read-only and run it through `mac/scripts/ghidra-py`. Keep large output in `mac/work/logs/`.
- REA: `mac/scripts/rea` for Evidence dossiers. REA imports into a temporary
  project (about 10 minutes, no saved names), so do not keep annotations there.
  Long commands need `REA_GHIDRA_STARTUP_TIMEOUT_MS=900000`; bound output with
  `--token-limit`. REA's reconstruction ledger builds obligations only from
  application graphs and process captures, not from native function lists.

## Maintenance

- REA is never pinned: `mac/scripts/rea` runs the `rea` on PATH. Install it with
  `npm install --global rea-agents` (not bun or npx; only an npm install can
  `rea update`). After a REA release, run `rea update`, then `rea setup --yes`
  for each client, and restart agent sessions.
- Ghidra version change: install the candidate beside the current version,
  verify its digest, build natives, rerun the project rebuild on a copy, and
  only then update the pins here and in the scripts.
- Corpus: `mac/work/corpus-manifest.txt` lists path, size and SHA-256 of the kept
  corpus (`mac/work/traces`, `mac/work/logs`, `mac/work/ghidra`, `mac/work/lua-bindings*.json`,
  `mac/work/dossiers`, `mac/work/playtests`), with paths relative to `mac/`. Verify a copy from
  its `mac/` folder with `awk -F'\t' '{print $3"  "$1}' work/corpus-manifest.txt | shasum -a 256 -c --quiet`.
  Regenerate it from `mac/` after the corpus changes:
  `find work/traces work/logs work/ghidra work/lua-bindings*.json work/dossiers work/playtests -type f ! -name .DS_Store -print0 | sort -z | while IFS= read -r -d '' f; do printf '%s\t%s\t%s\n' "$f" "$(wc -c < "$f" | tr -d ' ')" "$(shasum -a 256 "$f" | cut -d' ' -f1)"; done > work/corpus-manifest.txt`.
- Keep originals and evidence; delete nothing under `mac/work/`
  without asking JStar.

## When analysis is blocked

Classify the failure before changing tools:

- **I** (integration): a bridge or session problem. Test the operation with a
  pyghidra script on the saved project first.
- **D** (decompiler recovery): wrong boundaries, types or calls. Compare the
  same function in another decompiler (IDA Home is the candidate; Hopper is not
  recommended for MSVC x86 C++).
- **P** (port proof): behavior questions. Compare against a reference run.

## Reference runs (original game in CrossOver)

`mac/agents/faf-crossover` launches the FAF client (`client`), rebuilds it
(`build`, from `mac/work/downloads/faf-client`), runs the GOG game from its `bin`
directory (`original args…`), or runs any game executable in the bottle
(`game EXE args…`). The client and its rebuild need an arm64 Java 25 JDK
(`brew install openjdk@25`, or `FAF_JAVA_HOME`). FAF's settings use it as the game command
(`~/Projects/OpenSupCom/mac/agents/faf-crossover game %s`, set in the client's
settings, `~/.faforever/client.prefs`). Bottle setup,
preferences, fullscreen and FAF workarounds are owned by
[the CrossOver recipe](crossover-recipe.md).

Launch a 1680×1050 window:

```sh
mac/agents/faf-crossover original /nomovie /windowed 1680 1050 \
    /log 'Z:\Users\jstar\Projects\OpenSupCom\mac\work\logs\<name>.log'
mac/scripts/game-window wait    # presses Return past the black splash screen
```

- `mac/tools/mouse-probe/run [faf]` starts the game fullscreen and prints live
  how far the game's cursor is from the Mac pointer, plus the window's
  bounds and whether it took over the display. It sends no input; the player
  moves the mouse.
- Saves and replays go to the bottle's `Documents`, which CrossOver links to
  `~/Documents/My Games/Gas Powered Games/Supreme Commander Forged Alliance/`.
- Wine's stderr goes to `~/.faforever/logs/wine-<time>.log`. For Wine debug
  channels set `WINEDEBUG` (for example `err+all,warn+d3d`); the script passes
  it through CrossOver's `--debugmsg`.

FAF's own Mac recipe:
[downlords-faf-client scripts/mac/README.md](https://github.com/FAForever/downlords-faf-client/blob/develop/scripts/mac/README.md).

### FAF's own executable (client path)

Hosting a custom game makes the client download FAF's `ForgedAlliance.exe`
(game version 3839, 12,537,600 bytes, SHA-256
`53bb09f2e0d5f09e5f05eb29818ce1f6139b6a68041eea0391d3b12ea793ded2`) and its
`gamedata/*.nx2` into `~/.faforever/bin` and `~/.faforever/gamedata`; the game
log is `~/.faforever/logs/game_<id>.log`. The client's game command is
`faf-run.sh`; the same executable runs directly with
`mac/agents/faf-crossover game ~/.faforever/bin/ForgedAlliance.exe /init init.lua /nobugreport /windowed 1680 1050 /log <file>`
(run it from `~/.faforever/bin`; without `/gpgnet` it starts the front end).

- The FAF lobby, started by the client, opened in the bottle and drew its UI.
- Drive FAF's game with `GAME_WINDOW_OWNER=ForgedAlliance mac/scripts/game-window …`.
- Offline skirmish without the client: run the game directly (windowed),
  main menu → Skirmish opens the local "FAF Game Lobby" (nothing is visible to
  other players); close the changelog, pick an AI in an open slot, Launch Game.
  Save from F10 → Save Game; load from the same lobby's Load button.
  Main-menu Campaign fails in FAF 3839 (`operationbriefing.lua(40)`: `gsub`
  got a table) and leaves a black screen.
- Mods load from the client's vault folder
  `~/My Games/Gas Powered Games/Supreme Commander Forged Alliance/` (`mods/`,
  `maps/`), which the client passes to the game as the custom vault path.
  Install one from the client's Mods tab (it unzips into that folder).
For the client path, mods, missing textures and sound failures, use
[the CrossOver recipe](crossover-recipe.md#4-faf-forged-alliance-forever).

### Shared launcher for capture tools

`mac/tools/lib/game-run.sh` is the one place that starts a game in the bottle for
`mac/tools/lua-trace/capture`, `mac/tools/bp-dump/capture`, `mac/tools/sim-capture/capture`,
`mac/tools/ref-shot/capture` and `mac/agents/faf-autorun/run`; each tool sources it
and keeps its own command line. `game_run_start original|faf INIT LOG ARGS…`
refuses if a game is running and starts the GOG game (1680×1050 window) or
FAF's game (1024×768) with the tool's init file; `game_run_wait_marker TEXT
TIMEOUT [HOOK]` waits for an end marker (ref-shot's hook captures each READY
shot); `game_run_wait_exit LIMIT` waits for a self-exiting game; and
`game_run_finish` stops the game and renames the log. `game_run_shoot_ready
PREFIX [SUFFIX]` (a wait hook) saves the unscaled window for each
`REFSHOT|READY|NAME` log line as `PREFIXNAMESUFFIX.png`. `game_run_prefs FILE`
swaps in a `Game.prefs` for one run and restores the original on exit. An
exit trap always stops the game this run started (matched by its own log
name, never another game). Wine's stderr stays in
`~/.faforever/logs/wine-<time>.log`.

Each run also:

- takes `mac/work/bottle.lock` before touching `Game.prefs` (a stale lock of a
  dead process is cleared); an original-game run refuses when `active_mods`
  names a mod the original would load (its `Documents` mods folder or
  `gamedata/mods.scd`); mods only FAF has, such as JStar's M28AI, are ignored;
- copies `mac/tools/` and `mac/agents/faf-autorun` to `mac/work/capture-run/NAME/` and
  runs from there, so editing a hook during a run changes nothing; capture
  scripts run from `main() { …; }; main "$@"` for the same reason;
- checks itself every 5 s (`mac/tools/lib/capture.py watch`): it stops on the
  first Lua error or unknown unit type, when a hook the game loaded has not
  logged `HOOKCHECK|/<mount>/<path>|ok` within 90 s (every hook ends with
  that line), or when a checkpoint fails (`GAME_RUN_CHECKPOINTS="TEXT@TICK;…"`;
  sim-capture sets FIRE, INTEL, ECON and SIMSCRIPT checkpoints from its
  options); `mac/tools/lib/capture-hook` logs `SETUP|TICK|n` every 100 ticks;
- writes `NAME.setup` (JSON) next to the finished log: arguments, git HEAD
  and dirty flag, sha256 of every snapshot file, the resolved armies
  (including civilians), options, seed, last tick and how it ended.

The `supcom-capture` plugin (`mac/agents/mods`) offers the captures as
`/supcom-capture:capture` and the comparisons as `/supcom-capture:compare` (see "Comparisons"), with a skill
on when a capture is worth it and how to read a divergence.
`python3 -I mac/tools/lib/capture.py --self-test` tests the preflight and manifest
logic.

### Capture outputs are complete when they exist

`mac/tools/lua-trace/capture`, `mac/tools/bp-dump/capture`, `mac/tools/ref-shot/capture`,
`mac/tools/sim-capture/capture` and `mac/agents/faf-autorun/run` have the game log to `NAME.log.partial` (and
`ref-shot` writes each image as `NAME.png.partial`) and rename to the final
name only after the run ends: end marker or time limit, game stopped. A
reader that finds `NAME.log` or `NAME.png` sees a finished file; a leftover
`.partial` means the run failed or is still going. `faf-autorun` also renames
after a time-limit kill; its log check reports that run as failed.

### Scripted FAF runs (no mouse or keyboard)

Prefer these for validation: they never take the real mouse or keyboard, so
JStar can keep working, and each run ends in a pass/fail log check.

- `mac/scripts/game-prefs show | adapter | mods [NAME …]` edits the bottle's
  `Game.prefs` safely: it refuses while a game runs (the game rewrites the
  file on exit), backs up to `Game.prefs.bak-<time>`, replaces whole
  multi-line tables and checks braces. `adapter` sets `primary_adapter` to
  the macOS main display.
- `mac/scripts/game-log-check LOG [--expect TEXT] [--allow TEXT]` exits 1 on known
  failures: unresolved data paths, settings not loaded, 3D audio, D3D9
  device, Lua errors, autorun failures, and no `Run time` line (no normal
  exit). Wine's own stderr stays in `~/.faforever/logs/wine-<time>.log`.
- `mac/agents/faf-autorun/run NAME LIMIT_SECONDS ARGS…` runs FAF's game with
  FAF's own `init.lua` plus hooks in `mac/agents/faf-autorun/hook/`, logs to
  `mac/work/logs/NAME.log`, kills it after `LIMIT_SECONDS`, then runs the log
  check (requiring the marker of each `/auto…` action). FAF's `/map NAME
  /faction N` starts a skirmish directly with an AI in every other army; the
  hooks add `/autoai KEY`, `/autoais N`, `/autosave SECONDS NAME`,
  `/autoexit SECONDS` and `/autoload NAME`. Example, checked 2026-10-12
  (skirmish vs M28 Easy saved at 2:00, then reloaded in a new process and
  exited at 3:20):

  ```sh
  mac/scripts/game-prefs mods M28AI
  mac/agents/faf-autorun/run m28-a 600 /map X1MP_006 /faction 1 /autoai m28aie /autoais 1 /autosave 120 m28-a /autoexit 130
  mac/agents/faf-autorun/run m28-b 600 /autoload m28-a /autoexit 200
  mac/scripts/game-prefs mods
  ```

- FAF's command-line skirmish skips two lobby steps that AI mods need; the
  hook adds them: `ScenarioInfo.Options.Ratings` (M28 failed in
  `m28chat.lua` without it) and each active mod's
  `lua/AI/LobbyOptions/lobbyoptions.lua` defaults. It also renames the AI
  for the chosen personality.
- Loading a save logs FAF's harmless "Unable to reset selection sets"; the
  runner allows it.

### Driving the game window without a person

`mac/scripts/game-window` screenshots the Wine game window and sends clicks, drags,
keys and text (`shot NAME`, `click X Y [right]`, `drag X1 Y1 X2 Y2`,
`scroll X Y LINES`, `key CODE`, `type TEXT`, `wait [SECONDS]`; coordinates are pixels of the
800-px-wide screenshot it writes to `mac/work/logs/screens/`).
Every action except `shot` takes JStar's real mouse and focus, so it runs only
while `~/.supcom-input-ok` exists (JStar runs `touch ~/.supcom-input-ok`, and
`rm` it to take control back); otherwise it exits 4. Prefer input-free
validation: `mac/agents/faf-autorun/run` for the original and FAF, scripted input
and OpenSupCom's offscreen test modes.
`GAME_WINDOW_OWNER` selects another window owner by process name: `ForgedAlliance` for FAF's game, `java` for the FAF client. It needs
macOS Screen Recording and Accessibility permission for the app running the
shell. The game window belongs to a bare Wine process, so Claude's
computer-use tools cannot see it; this script can. Bring-to-front (native,
no AppleScript, so no Automation prompts) is automatic; macOS uses the first
click only to activate. It activates the process that owns the window it
measured (by PID), checks before each event that this process is still
frontmost, and stops (exit 3) as soon as it is not. It sets the Accessibility
`AXFrontmost` attribute:
on 2026-10-12, with Claude in front and no Java process running,
`NSRunningApplication.activate` alone left FAF's game behind (exit 3) and
`AXFrontmost` brought it to front. Input is refused (exit 3) unless the target app is
confirmed frontmost, so keys never land in another app. Only the 800-px copy of a screenshot is kept. Synthetic clicks do
not reach macOS permission prompts, and a prompt over the game swallows clicks
in its area. Typing into the game's text fields can drop letters while the
simulation runs at high speed. Keys: 36 Return, 53 Escape, 69 keypad plus
(game speed up), 109 F10 (game menu).

### Claude mods for this project

Claude Code plugins live in `mac/agents/mods/`, a folder marketplace named
`supcom`. `mac/scripts/setup` declares it in `.claude/settings.local.json`; install
each plugin for this checkout from its root:
`claude plugin marketplace add "$PWD/mac/agents/mods"`, then
`claude plugin install supcom-capture@supcom --scope local`. Installed plugins
run from a cache copy keyed by version. After editing a
plugin, bump `version` in its `plugin.json` and run
`claude plugin update NAME@supcom --scope local`; after removing one, run
`claude plugin uninstall NAME@supcom --scope local`. `mac/scripts/check` fails
while installed supcom plugins differ from the source.

- `supcom-capture` adds `/supcom-capture:capture`, `/supcom-capture:compare` (see "Comparisons")
  and `/supcom-capture:game shot [name] | click X Y | key CODE | wait [SECONDS]` with
  `--owner java|ForgedAlliance`, which runs `mac/scripts/game-window` (input
  actions need `~/.supcom-input-ok`; exit 3 means the frontmost guard refused).
- Apple's `game-porting-skills` (marketplace `game-porting-toolkit`) is enabled
  by `mac/scripts/setup` for Mac renderer work.

### Comparisons

`/supcom-capture:compare KIND ORIGINAL OSC` runs one comparator on a capture of the original
and the matching OpenSupCom file:

- `motion`: `python3 -I mac/tools/motion-compare/motion_compare.py ORIGINAL.log OSC.log`
- `intel`: `python3 -I mac/tools/intel-compare/intel_compare.py ORIGINAL.log OSC.log [--check]`
- `bp`: `python3 -I mac/tools/bp-dump/compare.py ORIGINAL.log OSC.log`
- `image`: `uv run -q mac/tools/image-compare/compare.py REF.png OSC.png`

Motion and intel read `MOTION` and `INTEL` lines in the mac/tools/sim-capture
format. OpenSupCom writes no such log yet, so those two have only the
original's side today.

### Reference screenshots of the original

`mac/tools/ref-shot/capture SET [GAME ARGS]` (default `/map X1MP_006`) starts the
original with a hook that, at the first sim tick, hides the UI, pauses, and
for each shot in `mac/tools/ref-shot/shots/SET.lua` (`name`, focus `pos`, `hpr`
in radians, `zoom`) snaps the world camera, waits 3 s and logs
`REFSHOT|SETTINGS` (the camera's `SaveSettings` plus `GetMaxZoom`/`GetMinZoom`:
the focus height follows the terrain and the focus can move inward) and
`REFSHOT|READY`. The script then saves the unscaled window as
`mac/work/logs/screens/ref-SET-NAME$REFSHOT_SUFFIX.png` (2x on a Retina display,
title bar included) and closes the game. `/refshadows 0` runs the console
command `shadow_Fidelity 0` first (shadows off). `/refwait N` lets the game
run N seconds before the pause (the ACU needs about 15 s to warp in), and a
`simInit.lua` hook logs each commander's pose every 10 ticks as
`REFSHOT|ACU|tick|army|entity|blueprint|x,y,z|qx,qy,qz,qw` (the last line
before the pause is the pose in the images). `/reffactions 1,4,1,2` sets the
armies' factions in order (1 UEF, 2 Aeon, 3 Cybran, 4 Seraphim; otherwise the
AIs' factions are random) and `REFSHOT|ARMY` lines log them. `/refui` keeps the
game UI (no `HideGameUI`); a shot's `select = 'COMMAND'` (any
`UISelectionByCategory` expression) or `select = false` sets the selection
before the snap; a shot without `pos` keeps the game's current camera.
`shots/ui.lua` frames the bottom bar and the selected ACU with its build bar,
`shots/hud.lua` uses the default camera, `shots/faction-acu.lua` frames army
1's ACU. SETTINGS lines end with the user-side `GameTime` in seconds. A shot's
`sim = { action = 'move'|'build', dx, dz, blueprint }` orders army 1's ACU
through `SimCallback` (a `SimCallbacks.lua` hook), and `resume = S` runs the
game S seconds before the shot (`shots/hud-move.lua`,
`shots/build-progress.lua`). The sim hook logs each ACU's pose and
`REFSHOT|BUILD|tick|army|entity|blueprint|fraction` every tick. `/refclean` hides the
overlays `HideGameUI` leaves: range rings (`ren_Ranges false`), icons
(`ui_RenderIcons false`), the faction map-border panels (`ren_MapBorderClear`),
the playable boundary (`ren_PlayableBoundary false`) and the deposit icons
(world view `EnableResourceRendering(false)`); deposit pads at close zoom are
terrain decals. `/refbare` also runs `ren_Decals false` (all terrain decals)
and `ren_MeshStatic false` (props such as rocks) before each shot. For no fog
of war pass the game's own `/nofog` (game option FogOfWar = 'none'); the
console variable `ren_FogOfWar` took effect only intermittently. A shot set may give a
top-level `RefConsole` list and per-shot `console` lists of console commands,
run in order and kept for later shots. No mouse or keyboard; the
window may sit on another Space (`winid --all` finds it). Log:
`mac/work/traces/ref-SET.log`.

### Unit motion and threat capture of the original

`mac/tools/sim-capture/capture NAME [GAME ARGS]` (default `/map X1MP_006`: the
player plus three "rush" AIs) starts the original with a `/lua/simInit.lua`
hook that, from the start of the session, logs one line per live unit every 5
ticks, `MOTION tick entity blueprint army x y z heading layer moving`
(`Entity:GetHeading()`, moving 0/1; the format `mac/tools/motion-compare` reads),
and at ticks 600, 1200, 1800, 2400 and 3000, for each AI brain,
`THREAT tick army type (x,z,threat),…` for `GetThreatsAroundPosition(start,
16, true, type)` with types Overall, Land, Structures, Commander, Unknown and
`HIGHEST tick army (x,y,z) threat` for `GetHighestThreatPosition(16, true,
'Overall')`. It stops at `SIMCAP|END|3000` (5 game minutes, about 6 minutes of
wall time). The log has CRLF line endings and an `info: ` prefix per line.
Captures include the map's civilian armies. A lobby launch creates them from
the scenario's `customprops.ExtraArmies` (for example `ARMY_9
NEUTRAL_CIVILIAN` on X1MP_006); the command-line launch every capture tool
uses reads only `teams.ExtraArmies` (in the GOG game and in FAF), so it
created none. `mac/tools/lib/capture-hook` (mounted first by ref-shot, lua-trace,
sim-capture, bp-dump and faf-autorun) makes `maputil.GetExtraArmies` read
`customprops` too and drops repeated army names; `/nocivilians` leaves them
out; motion-unit runs leave them out to stay comparable. Captures made before
2026-10-14 15:00 have no civilian armies. Options (game args): `/simfactions 3,1,1,1`, `/simbots` (all armies AI,
`/ai KEY`), `/simticks N` (end tick), `/siminterval N` (MOTION every N ticks),
`/simvel` (`VEL tick entity vx vy vz`), `/simthreat N`, `/simecon N`
(`ECON tick army mass income requested stored ratio energy … units bp=n,…`),
`/simintel N` (`INTEL tick army entity blueprint radar sonar omni seen
seenever fake [blip x,y,z]` for each enemy unit an AI army has a blip for),
`/simcombat` (`FIRE tick unit weapon target projectile muzzleBone` and
`DAMAGE tick target instigator healthChange` from the engine methods
`CreateProjectile` and `AdjustHealth`, wrapped in a `globalInit.lua` hook
before Lua classes copy them; `DEATH tick unit blueprint killer`),
`/simscript NAME` (runs `mac/tools/sim-capture/scripts/NAME.lua`'s `SimScript()`
in the sim; it logs `SIMSCRIPT` lines; `gallery` spawns every tech 2, tech 3
and experimental unit and structure per faction with `/simfactions 1,2,3,4`,
orders upgrades, sets the galleries fighting and logs `SHIELD tick unit
health max`; `motion-unit` scripts single-unit moves; both leave civilians
out), `/simspeed N` (game speed N, set by `mac/tools/lib/capture-hook`; about 6 to
8 times real time is held at speed 10 while recording) and `/simtrace` (adds
the lua-trace call tracer to the same run). Captures without screenshots run
in a 640x480 window (`GAME_RUN_WINDOW`).

### Lua call trace of the original

`mac/tools/lua-trace/capture NAME SECONDS [/map X1MP_006]` launches the original
with `/init …/tools/lua-trace/init-trace.lua`: the game's normal mounts plus a
`/tracehook` hook folder, whose `hook/lua/globalInit.lua` runs `trace.lua` in
every user and sim Lua state. It wraps every global engine function, the
`moho.*` method tables and each class's `__spec` table (Lua classes copy
methods from it). `mac/tools/lua-trace/summarize.py` writes first-call order and
counts to `mac/work/traces/summary-NAME.md`. Calls before the hook runs, and the
blueprint-loading state, are not traced. `/tracemenuskirmish` (no `/map`)
drives main menu → skirmish lobby → launch with no input: it calls the
menu's own `ButtonSkirmish` (hides the menu, hosts a lobby on the profile's
`LastScenario`), adds easy AIs (`/tracemenuais N`, default 1), saves the lobby as
`mac/work/logs/screens/ref-lobby.png`, then presses Launch through a reference
kept by a `uiutil.lua` hook; SECONDS count from the sim's start.
`mac/tools/lua-trace/diff.py mac/work/traces/menu-boot.log OTHER.log` compares two
traces.

### Blueprint dump of the original

`mac/tools/bp-dump/capture NAME [/map X1MP_006]` launches the original with
`mac/tools/bp-dump/init-dump.lua`, whose `/lua/simInit.lua` hook logs every
`__blueprints` entry of the sim state as `BPDUMP|<id>|<value>` (keys sorted),
waits for `BPDUMP|END`, stops the game and leaves `mac/work/traces/NAME.log`
(about 9 MB; 3,778 blueprints on GOG 1.5.3599). `mac/tools/bp-dump/compare.py
ORIGINAL.log OTHER.log` lists blueprints and fields only one side has and values
that differ.
