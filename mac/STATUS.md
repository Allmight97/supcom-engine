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
  (work/logs/overnight-2026-10-18.md), and this toolkit in `mac/`. Built arm64
  RelWithDebInfo with `mac/recipe/build.sh`; ships the loader and both drivers in `build/play`.
  After the move (2026-10-18): unit tests pass, `ctest -L mp` 4/4, `ctest -L gate` 269/269,
  smoke and render check pass ([consolidation log](log/2026-10-18-consolidation.md)).
- Mac driver: KosmicKrisp, SDK 1.4.363.0 installed locally in
  `mac/work/vulkan-sdk/1.4.363.0/`, selected by `mac/recipe/env.sh`. The game loads
  `libvulkan_kosmickrisp.dylib` (loader debug, `mac/work/logs/metal4/driver-proof.stderr`).
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
- Defects seen: interface draws very small on 5K (OSC lays out in framebuffer
  pixels; no UI scale); anti-aliasing option greyed, Lua warning
  `options.lua:481 aaoptions` (OSC's `GetAntiAliasingOptions` likely returns
  nothing); team colour on moving units fades from solid to dim pink (JStar).
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
- First fixes: interface scale, then anti-aliasing options.

## Open questions

- Where the second copy of the reference corpus goes (`mac/work/corpus-manifest.txt`
  lists it; about 1.6 GB that cannot be recaptured after Rosetta ends).
- Best Mac display setup for the game: "looks like" 2880x1620, 2560x1440 or native.
- Cause of the team-colour fade; JStar will screenshot it.

## Next actions

1. JStar checks by eye: the overnight changes (bundled drivers, full screen, FPS cap;
   work/logs/overnight-2026-10-18.md) and `mac/scripts/play --hud` after the move.
2. Fork issue #1: the rest of the packaging, then the M1 8 GB play test.
3. Play-test findings (notes/play-test-2026-10-17.md): Game Mode through the `.app`,
   the nuke effect, the `terranunits.lua:517` warning.
4. The Mac build contribution: macOS preset, vcpkg fixes, CI job (`mac/roadmap.md`).

## Tracks

Track detail goes in the session's log.

None: the checkout is free.
