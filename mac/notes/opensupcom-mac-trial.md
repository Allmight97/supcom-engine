Superseded by `mac/STATUS.md` and `mac/roadmap.md` (2026-10-18); kept as history.

# OpenSupCom on this Mac: trial results (2026-10-14)

OpenSupCom ([bwiemz/supcom-engine](https://github.com/bwiemz/supcom-engine),
MIT) at `1a87378`, built and run on JStar's Mac (M4 Max, macOS 27.2, arm64)
with Homebrew MoltenVK 1.4.2. Clone and all evidence are local:
`work/ref/opensupcom`, evidence in `build/experiment/evidence` (Codex run,
sandboxed) and `build/experiment/evidence2` (main session, outside the
sandbox). Codex's report: `work/logs/opensupcom-moltenvk.md`.

## Results

| Check | Result |
| --- | --- |
| Native arm64 build | Builds unmodified (empty source diff); two vcpkg ports needed a working zlib download URL (local overlay) |
| Game data | Reads the player's GOG install (`work/game`) |
| Headless AI skirmish | SCMP_009, 2 AIs, 6,000 ticks (10 game minutes), exit 0, no Lua errors |
| Rendering through MoltenVK | Main menu, loading screen and a 5-minute AI game with the full HUD render correctly on the M4 Max |
| Render performance, 1920x1080, ~290 units | CPU 7.4 ms mean (p99 9.0), GPU 4.5 ms mean per frame |
| Unit tests (Catch2) | 1,492 passed, 0 failed, 3 skipped (Linux-only font and memory tests) |
| Gate tests (windowed and data flows) | 249 passed, 1 failed, 7 golden-image tests skipped (cause not checked) |
| The one failure | `data.trail-render-test` check 8b, trail interpolation halfway into a tick; 18 of 19 trail checks pass |
| Multiplayer checks | 4 of 4 passed (lockstep, desync, drop, slow peer) |

The only blocker in the first run was Codex's sandbox, which hides the GPU.
From a normal shell Metal sees the M4 Max with compressed-texture support and
Vulkan creates its instance through MoltenVK.

## What it would mean to contribute

- A macOS port is mostly done by their design already: no source changes were
  needed to build and play. Realistic first contributions: a macOS CMake
  preset and CI job, the zlib download fix for vcpkg, the trail-test failure,
  the golden-image skips, Mac polish (Retina, native fullscreen, input).
- Our capture tooling against the original (`tools/`, `/capture`, `/compare`)
  is what the project lacks: its own docs say it has no reference captures.
  Running it against their engine is the highest-value contribution.
- Our sim findings are bug reports for them (4-byte Lua numbers, binding
  contract, movement and economy rules matched to captures).
- A native Metal backend is not needed for correctness or performance at this
  scale; MoltenVK handles it.
- Contributions are MIT; licensing for us is an open question (STATUS.md).
- Their pace is high and bursty with one main author: agree direction in
  their Discussions before sending pull requests.

## Not checked

Interactive play by a human, a full 30-minute rendered game, the cause of the
seven golden skips, modern FAF (client, AI mods) on their engine, and how
closely their sim matches our captures of the original.
