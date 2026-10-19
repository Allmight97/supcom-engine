# 2026-10-18: reference capture of the UEF nuke

## Decisions

- The nuke reference is a UEF ACU's death on X1MP_006 at a fixed camera (focus 74.5, 17.72, 62.5; heading
  0.785, pitch 0.7, zoom 90): before the kill, about 1.5 s after it and about 5 s after it.
- The original is captured at 1600x900 (`GAME_RUN_WINDOW="1600 900"`) because OSC's captures are fixed at
  1600x900 (`src/app/window.cpp:50`) and `image-compare` needs the same size and aspect.

## Done

- `SimCallbacks.lua` hook: `sim = { action = 'kill' }` kills army 1's ACU at once (`acu:Kill()`).
- `mac/tools/ref-shot/shots/nuke.lua`: shots `alive`, `kill-1500ms`, `kill-5000ms`.
- `mac/tools/ref-shot/osc-shot`: the same hook in OSC through `--init` and `--map`, one frame per run, checked
  against the log. OSC frames: alive 1730, kill-1500ms 2270, kill-5000ms 2930.
- Original (GOG, CrossOver):
  `GAME_RUN_WINDOW="1600 900" tools/ref-shot/capture nuke /map X1MP_006 /reffactions 1 /refwait 20 /nofog /refclean`.
  Images `mac/work/logs/screens/ref-nuke-{alive,kill-1500ms,kill-5000ms}.png` (3200x1856), log and manifest
  `mac/work/traces/ref-nuke.{log,setup}`; the manifest does not record the window size. A first run at the
  default 1680x1050 is kept as `ref-nuke-*-1680x1050.png` and `traces/ref-nuke-1680x1050.{log,setup}`.
  No Lua errors.
- OSC (fork main build, `build/play` in `~/Projects/OpenSupCom`):
  `OSC_ROOT=~/Projects/OpenSupCom tools/ref-shot/osc-shot nuke NAME FRAME X1MP_006 /refwait 20 /nofog /refclean`.
  Images `mac/work/logs/screens/osc-nuke-*.png` (1600x900), logs `mac/work/traces/osc-nuke-*.log`. No errors.

## Results

Age of each frame in sim ticks after the kill (from `REFSHOT|SIM` and the last `REFSHOT|ACU` tick before READY):
the original 16 and 53, OSC 14 and 49. The original's `resume` runs on wall-clock time, so its ages vary a little.

`uv run -q tools/image-compare/compare.py REF OSC [--region 200 130 1520 780]`
(`mac/work/logs/nuke-compare.txt`; diffs `mac/work/logs/screens/diff-nuke-*.png`). The region is a workaround
for OSC's HUD (below):

| Shot | Whole frame: mean, within 16 | Region: mean, within 16 |
| --- | --- | --- |
| alive | 16.15/255, 57.4% | 10.33/255, 69.3% (offset 0, 0: the framing matches) |
| kill-1500ms | 61.86/255, 1.2% | 50.17/255, 0.4% |
| kill-5000ms | 105.08/255, 0.1% | 101.99/255, 0.1% |

JStar sets the pass threshold.

Observed in the captures (not causes):

- 1.5 s: the original's flash washes the frame pale yellow-white; OSC shows a pink-brown cloud of large blocky
  smoke sprites.
- 5 s: the original shows a white-hot, bloomed dome over a scorched brown ring on brightened ground; OSC shows
  an orange fireball with horizontal banding inside a grey dust ring, and no dome is visible.

## What OSC lacks on this path

- `HideGameUI('on')` leaves the HUD up in a `--screenshot` run (binding at `src/lua/moho_bindings.cpp:3918`).
- `/refclean` leaves small yellow icons on the ground (inference: deposit markers, which the original hides with `EnableResourceRendering(false)`
  or `ui_RenderIcons`; not traced).
- `--map` skips `LaunchSinglePlayerSession`, so `/reffactions` has no effect; X1MP_006 makes every army UEF
  anyway. The original's armies 2 and 3 were Cybran (random); use `/reffactions 1,1,1,1` for full parity.

## Open

- Why OSC shows no dome and banded fire at 5 s (issue #3 follow-up).
- toolchain.md says the sim hook logs each ACU's pose "every 10 ticks" in one place; the code logs every tick.
