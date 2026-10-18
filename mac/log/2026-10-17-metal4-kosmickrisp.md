# Metal 4 through KosmicKrisp

JStar chose Metal 4 and Apple Silicon as the Mac direction, including switching
to KosmicKrisp. Correctness and performance tests guide implementation on that
path. STATUS.md and the roadmap now record the decision; the engine continues
to use Vulkan.

## Changed

- Installed Vulkan SDK 1.4.363.0 in ignored `work/vulkan-sdk/1.4.363.0/` with
  the official installer's `copy_only=1` and Qt's offscreen platform. No system
  installation or visible application was needed.
- Download: `downloads/vulkansdk-macos-1.4.363.0.zip`, 396,088,200 bytes,
  SHA-256 `163431e0203c8215286a17cf393643ce6b951f77d1b4f74ab30821a1f0beb09b`,
  verified against LunarG's version-specific checksum API before installation.
- Replaced the forced Homebrew MoltenVK driver in `osc/env.sh` with the local
  SDK's KosmicKrisp manifest. Standard `VULKAN_SDK` and `VK_DRIVER_FILES` overrides
  are honored; there is no automatic fallback. Added default and override checks
  for bash and zsh, including an SDK path containing a space.
- Updated setup, profiling and app-packaging guidance to use KosmicKrisp.
  Removed MoltenVK as the planned Mac default. No files or user data deleted.
- No engine changes or branch switch; the `mac-ui-scale` owner keeps the OSC
  checkout. All downloaded binaries, screenshots and runtime logs stay ignored.

## Observed checks

- Before the environment change, the assertion that the default driver was
  KosmicKrisp failed and printed Homebrew's MoltenVK manifest. After the change,
  both bash and zsh selected KosmicKrisp.
- `vulkaninfo --summary`: Apple M4 Max, macOS 27.2, driver ID
  `DRIVER_ID_MESA_KOSMICKRISP`, Mesa 26.2.99, driver build
  `vulkan-sdk-1.4.363 (git-269a955c89)`, Vulkan 1.4.363.
- Existing `build/play/opensupcom`: hidden menu capture at frame 120 and
  SCMP_009 capture at frame 600, both 1600x900, both exit 0. Images inspected:
  menu text and controls, then terrain, units, effects and the game interface.
  Validation enabled using the SDK layer. Each log has zero error lines and
  ten unused shader-output/vertex-attribute warnings (duplicate reporting capped).
- `scripts/osc-smoke`: SCMP_009, two AI armies, seed 4242, 3,000 ticks; exit 0,
  `SMOKE_OK`, no errors. This checks the sim, not graphics.
- `scripts/check`: passed, including the new environment checks.
- `git diff --check`: passed.

Evidence: `work/logs/metal4/` contains SDK identity, installer output,
`vulkaninfo.txt`, menu and scene PNGs/logs, and smoke/check output.

## Failures resolved and work remaining

- Local SDK `vulkaninfo` initially could not find its loader. Setting
  `DYLD_LIBRARY_PATH` to the SDK's `lib/` for that tool fixed it. The existing
  game already links its vcpkg loader and needed no library-path override.
- The first SCMP_009 capture at frame 120 showed the loading transition.
  Frame 600 reached the running game; the documented command uses 600.
- Longer gameplay, late-game frame pacing, first-use shader-hitch measurement,
  broader rendering gates, and a human play test remain. Unit/mp/gate suites
  were not rerun: this change touches only the toolkit and opens no engine PR.
  Validation warnings remain visible; their cause has not been compared across
  drivers. No frame-rate improvement is claimed.

Sources: [LunarG SDK guide](https://vulkan.lunarg.com/doc/view/1.4.363.0/mac/getting_started.html),
[SDK checksum API](https://sdk.lunarg.com/sdk/sha/1.4.363.0/mac/vulkansdk-macos-1.4.363.0.zip.json),
[Khronos porting guidance](https://vulkan.org/porting).
