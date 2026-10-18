# 2026-10-18: agent play tests, full screen from a maximized window, the nuke's dome

Main session (Opus medium) with JStar away; helpers: one Opus-medium test agent, two Opus-medium
fix agents, GPT 6.1 Sol (read-only plan opinion and branch review). Evidence:
`mac/work/playtests/2026-10-18-agent/` (report.md, render-loop-plan.md, codex-opinion.txt,
codex-review.txt, A-/B-/C-/D-/E-/F-/S- files).

## Decisions

- JStar: no more agent work on the FPS cap; he watches it with `mac/scripts/play --hud`. Testing
  infrastructure for it only if it later earns its keep.
- JStar: the minimum test-and-fix loop for the nuke and every render element with its failure mode.
- JStar: engine fixes land on the fork first. An upstream PR only when the change works and upstream
  gains: a draft, a single PR if upstream's practice allows, its commits coherent vertical slices.
- The old toolkit clone `~/Projects/SupCom` went to the Trash (JStar approved; repo archived, nothing
  unpushed; its `work/` held only check stamps). The tarball stays.

## Done

- Agent play tests without JStar (hidden runs only): bundled drivers pass in a clean environment
  (KosmicKrisp from `build/play`); full screen 6 of 8 display cases right in a model of JStar's
  layout, the maximized case wrong; FPS cap measured (mean 8.525 ms at 118, sd 1.06; no per-frame
  log); three headless AI soaks (30 and 60 min, 8 AIs; 30 min, 4 AIs) exit 0 with 0 Lua errors.
- Full screen follows a maximized window's display: merge `69830c38` (commit `1d277216`); its test
  failed first.
- Issue #4 rewritten with the traced cause: `brain:GetUnitBlueprint('XEA3204')` looks up an
  uppercase id in lowercase-keyed `__blueprints`.
- Issue #3: unknown mesh ShaderNames fell back to the opaque Unit technique. The UEF nuke's only
  mesh is its dome (`NukeUEF`). Merge `b4b857f5` (`d53c82f4`, `fc8c39ce`) adds NukeUEF, Effect, Cloud and
  OuterCloud from mesh.fx, extends `--effect-mesh-test` (plates plus a real ACU-death nuke, PNGs
  through `OSC_EFFECT_MESH_TEST_PNG`), and a docs/plans record. A read-only review found OuterCloud's depth compare too loose (fixed: strict LESS) and asked for that record and fade checks. Before: the opaque maroon sphere
  reproduced offscreen; after: a translucent noise-textured dome.

## Failures, causes, fixes

- The test agent's nuke capture spent minutes replaying from a save: the camera ignores `--camera`
  after `--load`/`--watch`, and `--screenshot-frame` counts from the load. The fix was a direct
  trigger in an offscreen test mode, not replays.
- The test agent could not write report.md (subagent report files are blocked); the main session
  saved it.
- `test_net_lobby.cpp:356` (LaunchGame) failed once in a full unit run, then passed 8 of 8 alone
  and in a rerun: a flake, unrelated.

## Open

- JStar by eye: the nuke dome against the original; the full-screen steps (STATUS).
- Upstream PR for the shaders: prepare `up/effect-shaders` after JStar's look; draft.
- Another Mac contributor opened upstream PRs today (#734-#746: macOS presets, ~/Library data,
  MoltenVK ICD, peak memory); they overlap M1's build contribution.
- Unverified soak signs: script threads 7,614 -> 24,929 from minute 30 to 60; no unit gained
  veterancy; late 8-AI sim 93 ms per tick of 100.
- Seven shader names still draw as Unit (Explosion, NukeEMP, NukeQuantum, GlassAlpha,
  PhalanxEffect, UEFQuantumGate, Flat); the coverage check that lists them is not built.
