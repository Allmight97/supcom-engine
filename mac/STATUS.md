# Status

Current facts, decisions, open questions and next actions for the Mac port of
OpenSupCom (OSC). Rewrite in place as facts change; history goes to `mac/log/`.

## Facts

- First Mac trial (2026-10-14, Homebrew MoltenVK, history): [notes/opensupcom-mac-trial.md](notes/opensupcom-mac-trial.md).
- Fork: [Allmight97/supcom-engine](https://github.com/Allmight97/supcom-engine)
  (created 2026-10-17). One checkout, `~/Projects/OpenSupCom`: `origin` = the fork,
  `upstream` = bwiemz (push disabled). Deferred Mac work: [fork issue #1](https://github.com/Allmight97/supcom-engine/issues/1).
- Fork `main` (2026-10-18): upstream `d98ad203` plus the Mac branches for UI scale,
  the SDK loader, bundled drivers, full screen on the main display and an FPS cap
  (merges `1e4af415`, `a416dc0d`, `dde2665a`, `da8ff2ba`, `7d39ac25`), full screen from a
  maximized window (`69830c38`) and the nuke's effect techniques (`b4b857f5`, #3), and this
  toolkit in `mac/`. Built arm64
  RelWithDebInfo with `mac/recipe/build.sh`; ships the loader and both drivers in `build/play`.
  After the move (2026-10-18): unit tests pass, `ctest -L mp` 4/4, `ctest -L gate` 269/269,
  smoke and render check pass ([consolidation log](log/2026-10-18-consolidation.md)); again
  after `b4b857f5` ([agent play-test log](log/2026-10-18-agent-playtests.md)).
- Mac driver: KosmicKrisp, SDK 1.4.363.0 installed locally in
  `mac/work/vulkan-sdk/1.4.363.0/`; `mac/recipe/env.sh` sets only `VULKAN_SDK`. The game
  prefers KosmicKrisp and loads `libvulkan_kosmickrisp.dylib` (loader debug, `mac/work/logs/archive-pre-2026-10-18/metal4/driver-proof.stderr`).
  Hidden menu and SCMP_009 smoke captures render with validation on: zero errors,
  unused shader-output/attribute warnings. Not yet compared with the original or
  measured for frame time. Evidence: [Metal 4 switch](log/2026-10-17-metal4-kosmickrisp.md).
- Upstream has no macOS preset and no macOS CI job; its provenance doc says
  "Not yet: macOS". A Mac contributor already landed `src/platform/native_fullscreen.mm`.
- First human play, 2026-10-16 (`mac/notes/play-test-2026-10-16.md`): skirmish on
  SCMP_039, 8.4 game minutes, 0 errors, normal exit. Title bar showed 120 fps
  (not measured by the engine). Audio perfect (JStar). Loads much faster than CrossOver.
- Display: Studio Display XDR, 5120x2880 panel, 120 Hz maximum, set to "looks like"
  2880x1620 at 2x backing; built-in display also 120 Hz.
- Defects still open (2026-10-17 play test, [notes](notes/play-test-2026-10-17.md)):
  anti-aliasing unavailable (single-sample renderer); one Lua warning, `terranunits.lua:517`
  (#4: cause traced, not fixed). Seven mesh shader names still draw as opaque units
  (`docs/current-state.md`, M211o).
- Fixed and confirmed by JStar in play (2026-10-18, 21:30): the nuke (#3: mesh techniques, the
  dome's scale and culling, light particles feed bloom) and the glow/aura (the frame and bloom in
  8-bit targets as FA's: GOG exe 0x007F4D10, format table 0x00D41E84). Merges `b4b857f5`,
  `e959494b`, `073b18e5`.
- New play-test bugs (2026-10-18, replay `mac/work/playtests/2026-10-18-jstar/assist-beam-and-drones.oscreplay`):
  an ACU assisting a factory keeps its build beam on the factory after other orders, until a
  second queued build; engineering drones (UEF engineering station, ACU) hover without building
  and show no beam. Filed as fork issues #7 and #8.
- Build sparks (2026-10-18 check): OSC creates and draws them as retail's rules say; they are 1-3 px
  at zoom 30-60, vanish past zoom ~115 (LODCutoff 100), and a build ordered while zoomed out never
  gets them (CreateIfVisible). Retail's emitter LOD rule (GOG exe CanSeeCam 0x0065C3A0: the view's
  width at depth times a per-fidelity scale) differs slightly from OSC's eye distance.
- Reference captures of the original in CrossOver draw no emitter particles (smoke, sparks,
  emitted glows): six probe emitters, including a control, drew nothing; Wine logs about 28,900
  "Map box is invalid" (a zero-size buffer lock). Meshes, decals, beams and light particles draw.
  Particle comparisons need another D3D backend or capture path first.
- JStar's play, 2026-10-18 evening (full screen 2560x1440, cap 118, KosmicKrisp; replay and log in
  `mac/work/playtests/2026-10-18-jstar/`): smooth; the nuke looks better than the sphere but not
  like the original, and clips with zoom; lighting effects show a glow or aura unlike the original
  (bloom? unverified); the M4 Max's fans spin up at 1440p and 118 fps (unmeasured: M2). The
  original in CrossOver at `/windowed 2560 1440` looked fuzzy (not sharp); it closed normally.
- Full screen at "looks like" 2560x1440 renders the 3D scene at 5120x2880 (log: `Frame targets
  created (5120x2880)`; Retina framebuffer, `renderer.cpp:218`): four RGBA16F targets, full-res
  reflection and normal passes, redrawn at 118 fps from a 10 Hz sim. Two read-only opinions
  (Fable 5.1, GPT 6.1 Sol) call it brute force: `mac/work/logs/perf-opinions-2026-10-18.md`.
  Measured with upstream's `--render-bench` (battle scene, M4 Max): GPU p50 9.59 ms at 5120x2880
  against 5.35 at 2560x1440, plus about 3.9 ms that no size changes (three whole-map terrain draws,
  inferred). Plan: [fork issue #6](https://github.com/Allmight97/supcom-engine/issues/6).
- Agent soaks (2026-10-18, headless, 8 AIs): 0 Lua errors; late-game sim 93 ms per tick of
  100; unverified: script threads 7,614 to 24,929 from minute 30 to 60, no unit gains
  veterancy. `test_net_lobby.cpp:356` (LaunchGame) failed once, then passed: a flake.
- Upstream: another Mac contributor opened PRs on 2026-10-18 (bwiemz #734 to #746: macOS
  presets and vcpkg triplet, `~/Library` data, MoltenVK ICD, peak memory in bytes). Upstream
  takes about 30 PRs a day, most by agents; the owner lands outside PRs in batches ("Land #A to
  #B"). Watch: `mac/scripts/upstream-news` (MAC and OVERLAP PRs), at each session start, in the
  fork's daily issue "Upstream Mac watch", and `/supcom-upstream:shape` before an upstream PR.
- FAF on the Mac (FAForever repos, 2026-10-18): no released Mac client; `develop` has an arm64
  client (downlords-faf-client #3504, June 2026, one author, quiet since May) that runs
  `ForgedAlliance.exe` through one old CrossOver Wine build under Rosetta 2, chosen for Rosetta's
  x87 lockstep precision. It ends with Rosetta in macOS 28. The client launches only
  `ForgedAlliance.exe` (its command-line format is configurable); FAF has nothing on OpenSupCom.
- OSC's game-folder search order is command line, `OSC_FA_PATH`, FAF, Steam, chosen
  folder; GOG is never searched. Without `OSC_FA_PATH` it picks FAF's files.
- The original (GOG 1.5.3599) runs only in CrossOver 26.3 under Rosetta; the dev Mac
  stays on macOS 27 until CrossOver's ARM64 (FEX) build runs it.

## Identities

| File | Bytes | SHA-256 |
| --- | --- | --- |
| `setup_supreme_commander_forged_alliance_1.5_(38101).exe` | 1,096,744 | `19812dd0f932d41188ba2e9b8c864acea9a3cb9757312bfc413e6333ce5c56da` |
| `…(38101)-1.bin` | 4,293,877,758 | `f49948685831f3cb5c82814eea4393f70b5522cc5a2dc005834bde8054793331` |
| `…(38101)-2.bin` | 973,738,535 | `1b774a72ceb88480d90a3a57a4f35840fbf6bfece6f8c1e05621811ed7c7ab72` |
| `bin/SupremeCommander.exe` (v1.5.0.1, linked 2008-02-19) | 12,440,832 | `79074e294ea72fb179914cc393525720c523b65d6c9e300f11d31edceccdb887` |
| `bin/MohoEngine.dll` | 9,827,584 | `3e6e1a698a57d051e8ee6120d81d4af373321b9bf5f10071e291c96c08a7c3b5` |
| FAF `ForgedAlliance_base.exe` (linked 2009-06-30) | 12,444,928 | `e7ccac34412ee2652efe356bf4613952f22634f418e20e627b54fe256b1046e5` |

The GOG and FAF executables are different builds: functions sit 48 to 528 bytes
apart, so FAF addresses never apply directly.

## Decisions (JStar)

- The Mac build follows what macOS 26/27 formally supports (LunarG's Vulkan SDK
  loader and KosmicKrisp) even where that diverges from upstream. Divergent work
  lands on JStar's fork; upstream may pull or adopt it later.
- Two Mac support levels, following LunarG's advice (2026-10-17): Modern (Apple
  Silicon, macOS 26+) runs KosmicKrisp and is tested on every change, including
  JStar's M1 with 8 GB; Compatibility (Intel Macs, older macOS) runs the bundled
  MoltenVK, best effort, tested by others (JStar cannot). The game prefers
  KosmicKrisp whenever it reports a device; no player picks a driver. Players
  whose Mac runs neither can use the original game in CrossOver
  (docs/crossover-recipe.md). The Vulkan SDK (which carries both drivers) stays pinned and is upgraded only after the new
  version passes the smoke, a rendered capture and JStar's play test
  (docs/toolchain.md).
- All effort goes to OSC. The native SupCom engine is archived (tag
  `native-engine-final` in Allmight97/SupCom; `~/Projects/SupCom-archive-2026-10-16.tar.gz`).
- CrossOver serves only reference captures of the original; no further work on it.
- JStar is OSC's macOS developer. First complete contribution: a formal Mac build.
- One repo (2026-10-18): the toolkit lives in the fork's public `mac/` folder, MIT
  (JStar is its only author); Allmight97/SupCom is archived after the move.
- Goal beyond the build: a faithful copy of the original that also runs FAF and its
  improvements; adapting FAF's open code is fine.
- Design bugs away (2026-10-19): fix a bug's class at its source (a deep module, an enforced
  boundary, a ratchet test) where it earns its keep; a plain patch only when unavoidable.
- FAF is tracked apart from the engine roadmap, in fork issue #9.
- Play (2026-10-18): JStar sets the frame rate in the game's Video options, not on the command line.
  `mac/scripts/play` passes no window or cap, keeps the Metal HUD on, and on macOS full screen at a
  60 Hz mode caps at 60 (merge a364666d). Video settings at the game's highest (Fidelity,
  Shadows, Textures and Level of detail High, Bloom on).
- Focus (2026-10-18), where no one else upstream is: KosmicKrisp and Metal 4 runtime quality,
  frame pacing and 120 fps on high-resolution displays, effect-rendering fidelity checked against
  captures of the original, and FAF on the Mac. Not volume: the Mac build presets come from
  another contributor's upstream PR #745, which the fork builds on.

## Open questions

- Where the second copy of the reference corpus goes (`mac/work/corpus-manifest.txt`
  lists it; about 1.6 GB that cannot be recaptured after Rosetta ends).
- Best Mac display setup for the game: "looks like" 2880x1620, 2560x1440 or native.
- FAF on a Mac after Rosetta: OSC launched by FAF's client (GPGNet is in OSC's tests), and
  lockstep between a native arm64 OSC and Windows players (OSC's cross-OS replay check).

## Next actions

1. JStar checks by eye (`mac/scripts/play`):
   - Bundled drivers, no setup script: in a shell that has not sourced `mac/recipe/env.sh`,
     run `build/play/opensupcom --fa-path ~/Projects/OpenSupCom/mac/work/game`. Expect
     normal play (agents saw `driver KosmicKrisp` in a hidden run).
   - Full screen (Studio Display main, MacBook screen on): `mac/scripts/play --full` from the
     MacBook screen: expect the Studio Display. Windowed, drag to the MacBook, maximize there,
     Full Screen: expect the MacBook; quit in full screen and relaunch with `--full`: the
     MacBook; Windowed: maximized on the MacBook; un-maximize: the size from before, at the
     MacBook's top-left corner. Drag back to the Studio Display and repeat: the Studio.
   - The nuke: a UEF ACU death or nuke in a skirmish. The dome should be translucent and
     fade, not an opaque sphere; compare with the original as remembered.
   - Frame rate: pick "Full Screen (60 Hz)" or "(120 Hz)" in Video; the Metal HUD and the log line "Frame cap 60.0 (the Video option's 60 Hz ...)" show it took effect.
2. Upstream draft PR bwiemz/supcom-engine#750 (the nuke and the 8-bit frame; branch `up/nuke-effects`
   in the worktree `~/Projects/OpenSupCom-up`; two read-only audits, all checks on upstream main
   merged in). Watch its CI and review; rebase or merge upstream main when it moves.
3. #4: look the pod's id up through `blueprint_name()` in `brain_GetUnitBlueprint`, with a
   failing test first.
4. Render less per frame on Retina (#6): render scale first, then per-pass GPU timing, terrain
   culling.
5. Play-test findings still open: Game Mode through the `.app`, the play recorder (#2).
6. Build on upstream #745 (macOS presets) once it lands; drop the fork's own preset work and
   keep `mac/recipe/` only for what #745 lacks. Fork issue #1 holds the packaging.
## Tracks

Track detail goes in the session's log.

None: the checkout is free.
