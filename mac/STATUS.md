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
- Build sparks: no OSC bug; retail's CreateIfVisible and LODCutoff rules hide them (2026-10-18).
- Reference captures of the original in CrossOver draw no emitter particles (smoke, sparks,
  emitted glows): six probe emitters, including a control, drew nothing; Wine logs about 28,900
  "Map box is invalid" (a zero-size buffer lock). Meshes, decals, beams and light particles draw.
  Particle comparisons need another D3D backend or capture path first.
- Full screen at "looks like" 2560x1440 renders the 3D scene at 5120x2880 (Retina framebuffer);
  battle-scene GPU p50 9.59 ms there against 5.35 ms at 2560x1440, measured before the 8-bit
  targets. Plan: [fork issue #6](https://github.com/Allmight97/supcom-engine/issues/6).
- Agent soaks (2026-10-18, headless, 8 AIs): 0 Lua errors; late-game sim 93 ms per tick of
  100; unverified: script threads 7,614 to 24,929 from minute 30 to 60, no unit gains
  veterancy. `test_net_lobby.cpp:356` (LaunchGame) failed once, then passed: a flake.
- Upstream: another Mac contributor opened PRs on 2026-10-18 (bwiemz #734 to #746: macOS
  presets and vcpkg triplet, `~/Library` data, MoltenVK ICD, peak memory in bytes). Upstream
  takes about 30 PRs a day, most by agents; the owner lands outside PRs in batches ("Land #A to
  #B"). Watch: `mac/scripts/upstream-news` (MAC and OVERLAP PRs), at each session start, in the
  fork's daily issue "Upstream Mac watch", and `/supcom-upstream:shape` before an upstream PR.
- FAF on the Mac: FAF's Mac client runs FA.exe under Rosetta 2, which macOS 28 removes;
  OSC games through FAF's client are tracked in fork issue #9.
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
  JStar's M1 with 8 GB; Compatibility (Apple Silicon on macOS 14-25) runs the bundled
  MoltenVK, best effort. Intel Macs are unsupported until someone can build and test an
  Intel executable (JStar, 2026-10-19: KosmicKrisp is arm64-only; upstream's presets
  build arm64 for macOS 14). The game prefers
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
- Roadmap decisions (2026-10-19, [decision page](https://claude.ai/artifact/SZwjqSDf98x1Rq5YLrj4Mr)):
  the fork deletes upstream's installed-SDK driver discovery (its bundled drivers are the one
  path); "without upscaling" stays, render scale only if 120 Hz still misses after per-pass
  timing and terrain culling; upstream PRs carry one logical change each, related ones opened
  together (GitHub's stacked PRs do not work across forks); after the sync, try DXVK or
  D3DMetal on the capture bottle (with a backup) to finish a frozen reference corpus; the
  focus-army desync: prove first, then leave script threads out of the compared checksum.
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

Roadmap of 2026-10-19 ([log](log/2026-10-19-issue-audit.md)); each step eases the next.
1. Sync fork main with upstream main (merge commit): drop upstream's installed-SDK driver
   discovery, keep the 8-bit targets, the loader and the KosmicKrisp preference; keep
   `mac/recipe/build.sh`. Full checks, a play by JStar (with the 10-18 full-screen display steps:
   maximize on the MacBook, then Full Screen, then relaunch), his powermetrics baseline at 60 Hz, a
   build without `mac/recipe/overlays/` (delete them if it passes).
2. The focus-army desync (#10): prove, gate test (record a windowed game, replay it
   headless), fix. Upstream PR.
3. #4 at its root: one blueprint lookup owner plus a ratchet; the ShaderName vocabulary ratchet.
   Upstream PRs.
4. macOS CI job and the provenance line: upstream PRs opened together.
5. #7, then #8 (the pod auto-assist task, after a capture of the original's pods). Upstream PRs.
6. #6: per-pass GPU timing, terrain culling; the emitter LOD rule (#11). Upstream PRs.
7. Fork-only: the capture backend (DXVK/D3DMetal), the .app (#1), the M1 8 GB check, the Mac in
   the cross-OS lockstep check, #2 when needed. FAF: #9.
Keep bwiemz #750 current with upstream main until it lands.

## Tracks

Track detail goes in the session's log.

None: the checkout is free.
