# Roadmap: Forged Alliance on the Mac through OpenSupCom

Settled decisions are in [STATUS.md](STATUS.md).

**End:** a Mac app that finds the player's GOG or Steam files, starts into FAF by
default (or the plain game), runs full screen at the highest quality without
upscaling, smoothly at 120 fps, faithful to the original. No Wine, CrossOver or
Rosetta. The engine work lands upstream in OpenSupCom (OSC).

Two support levels (JStar, 2026-10-17, as LunarG advises): Modern, Apple Silicon with
macOS 26 or later on KosmicKrisp (Metal 4), tuned and tested on every change; and
Compatibility, Apple Silicon on macOS 14-25 on the bundled MoltenVK, best effort (Intel
unsupported until someone can build and test it; JStar, 2026-10-19). One
Vulkan renderer; the game prefers KosmicKrisp whenever it reports a device.

Codes: **M1 … M7** are milestones in order; **REF** is the reference-capture track
(deadline: macOS 28 removes Rosetta). Each deliverable names its check; it is done
when the check passed and the result is recorded in STATUS.md or a log.

## M1 A first-class Mac build (the first upstream contribution)

| Deliverable | Check |
| --- | --- |
| Interface scale on Retina displays | Done 2026-10-17 (merge `1e4af415`): right size and sharp in JStar's play test ([notes](notes/play-test-2026-10-17.md)) |
| Anti-aliasing options work (no Lua error; real MSAA only if JStar wants it) | Done 2026-10-17 (merge `1e4af415`): no Lua warning; the option reads Off |
| KosmicKrisp drives the arm64 build through Metal 4 | Done 2026-10-17: loader debug shows `libvulkan_kosmickrisp.dylib`; hidden captures, zero validation errors |
| OSC links the Vulkan SDK loader, and vk-bootstrap uses it (`vkb::InstanceBuilder(vkGetInstanceProcAddr)`, `src/renderer/renderer.cpp`), so it never opens `libMoltenVK.dylib` by name | Done 2026-10-17 (merge `a416dc0d`): loader debug shows one loader and KosmicKrisp |
| KosmicKrisp and MoltenVK ship beside the executable (`vulkan/icd.d` next to it); the game prefers the KosmicKrisp device | Done 2026-10-18 (merge `dde2665a`): a run with no environment variables logs KosmicKrisp; with the KosmicKrisp manifest removed it logs MoltenVK |
| The same drivers inside the `.app`; a clear message when no device is found | Fresh `.app` runs with no environment variables |
| Full screen on the main display, or the one last used | Done 2026-10-18 (merge `da8ff2ba`); JStar's check by eye is open (STATUS.md) |
| A frame-rate cap, absolute or below the display's refresh rate (`--fps-cap`) | Done 2026-10-18 (merge `7d39ac25`); JStar's check by eye is open (STATUS.md) |
| Low-end Modern Mac: JStar's M1 with 8 GB plays a skirmish on default settings | JStar's play notes and the engine's frame log |
| `macos-arm64` CMake preset; the zlib and minizip vcpkg fixes (today in `mac/recipe/overlays/`): from upstream #745 (another contributor), which the fork builds on | Fresh clone, preset, build |
| macOS arm64 CI job (`macos-26`) running what CI runs elsewhere (`ctest -LE data`; needs no Vulkan driver) | Green on the PR |
| The provenance doc's "Not yet: macOS" changed, in its own PR as upstream asks | Part of the PR set |
| The seven golden-image tests on Mac (missing baselines, not a Mac bug) | They run with local goldens |
| Cross-platform lockstep: the Mac joins OSC's cross-OS replay check | A Mac replay matches Linux and Windows checksums |

## M2 Measure what the player feels

| Deliverable | Check |
| --- | --- |
| A timestamped frame-interval log from the engine (sim, render, present) | Histogram from a live rendered run |
| Display modes compared ("looks like" 2880x1620, 2560x1440, native): pixels rendered, frame time, UI size; a recommended Mac setup | Measured table plus JStar's play notes |
| Render scale or render-size choice, if the measurements show a cost | Frame time before and after |
| Agent-runnable profiling: Metal HUD, `xctrace` Metal System Trace export, frame capture through KosmicKrisp (`MESA_KK_GPU_CAPTURE`) | One trace of a slow frame read by an agent |
| First-use shader hitches: a persistent pipeline cache, if traces show hitches | Hitch count on a second run |
| 120 Hz pacing in full screen on the target display | p95 frame interval at or below 8.3 ms in a late-game four-AI run |

## M3 Compare with the original

| Deliverable | Check |
| --- | --- |
| The capture hooks run through OSC's `--init <file.lua>` (blueprint dump with 4-byte float rounding, Lua call trace with an equal-count proof, `motion-unit`) | Each proof's result written down |
| An OSC-side runner writing the same logs and `.setup` manifests; `/supcom-capture:compare` on both sides | One command compares OSC with the original |
| Every human observation reproducible: a replay plus a screenshot at a tick (first case: the nuclear explosion, #3) | The test fails before the fix, passes after |
| Look comparison at fixed cameras with thresholds JStar sets | Scores within threshold, or on JStar's exception list |

## M4 Automated play

| Deliverable | Check |
| --- | --- |
| AI soak: four AIs, 30+ game minutes, completion marker, error budget, summary JSON | Passes; an injected Lua error fails it |
| Tech-tree session per faction (scripted resources, real build orders, each weapon class) on OSC and the original | Coverage list; an injected build failure is reported |
| Recorder for JStar's play: hitch log, Lua errors, screenshots, a mark key, the replay; a findings report | Each mark has its screenshot |

## M5 Fidelity

Behaviour and look differences found by M3 and M4, fixed upstream with evidence, or
recorded as accepted exceptions. Inventory of known findings:
[carry-over-inventory.md](notes/carry-over-inventory.md) §5.

## M6 A Mac app anyone can install

`.app` bundle with the Vulkan loader, KosmicKrisp and MoltenVK inside, signed
and notarized; first run imports the game
(GOG install, GOG installer, files from a PC, Steam files); settings and logs in macOS
folders; an install test on a clean account.

## M7 FAF by default

FAF's data provisioned natively; FAF Lua and M28AI as the default; the FAF client
launching OSC on macOS; installer choice between FAF and the plain game; the M2 120 Hz
run repeated on this configuration.

## REF Reference captures

Recapture with manifests the captures M3 needs (`motion-unit`, `icx-600`,
`long-1800`, the 60 s skirmish trace); the tech-tree script on the original; the
queued items (save/load trace's load half, animation frames, water and sky,
combat effects, loading screen, menus, score screen); reference shots at 2560x1440.
