# Scratchpad

Working notes that are not yet facts for STATUS.md: hypotheses, half-finished
reasoning, questions to check, ideas worth keeping across context compaction.
Any agent may add a dated entry at the top. Move settled facts to STATUS.md,
procedures to docs/toolchain.md, history to log/; delete entries once moved
or abandoned.

## 2026-10-17 (main: draft note to zooldoo, for JStar to post; not sent)

Where: upstream's GitHub Discussions (enabled), or a comment on #729. JStar posts it.

> Hi zooldoo, I'm JStar, working on OpenSupCom on macOS (M4 Max, macOS 27, a 5K
> 120 Hz display). I've seen your Mac PRs (#240, #485, #687) and want to avoid
> duplicating you: I just rebuilt the HiDPI interface scale before seeing #687.
> What I have that may help: OSC runs unmodified on KosmicKrisp (LunarG's Mesa
> driver on Metal 4, in Vulkan SDK 1.4.363) with zero validation errors; vk-bootstrap
> falls back to opening libMoltenVK.dylib by name unless given the linked loader's
> vkGetInstanceProcAddr; GetAntiAliasingOptions is a nil stub, which breaks retail's
> Video options (a small fix is ready). Which driver and loader do you run, and on
> which macOS? If useful, I could take driver, packaging (a .app with the loader and
> driver inside) and macOS CI, and leave renderer and interface work to you. Happy to
> coordinate however suits you.

## 2026-10-14 (CrossOver track: FAF, reference runs, capture backlog) — resume here

- State: bottle free, no game running; `Game.prefs` is JStar's (2560,1440,120;
  M28AI active; nologo). Bottle backend is CrossOver Auto (= wined3d for this
  DX9 game; terrain shots identical). Stay on CrossOver 26.3 (Rosetta) until
  CrossOver 27; captures of the original are made while Rosetta lasts.
- Tools (docs/toolchain.md): `tools/lib/game-run.sh` shared launcher;
  `tools/ref-shot` (camera shots, /refui, /refclean, /refbare, /nofog,
  /refwait, /reffactions, per-shot select/sim orders/resume),
  `tools/sim-capture` (MOTION/VEL/THREAT/ECON/INTEL/FIRE/DAMAGE/DEATH,
  /simscript, /simtrace), `tools/lua-trace` (/tracemenuskirmish /tracemenuais,
  /autosave /autoexit /autoload), `tools/bp-dump`, `.agents/faf-autorun`.
  `tools/lib/civilians-hook`: captures include civilian armies; /nocivilians.
- Resume step 1: run the pending queue below in order, one game at a time,
  delivering each to its requester with a one-line copy to the main session.
- Pending (in order):
  1. S2 combat-600: `tools/sim-capture/capture combat-600 /map X1MP_006
     /simticks 6000 /simfactions 3,1,1,1 /siminterval 100000 /simthreat 600
     /simecon 10 /simintel 10 /simcombat` (~13 min; stopped at tick 840 for
     the pause).
  2. Main C, save/load trace: `tools/lua-trace/capture save-5min 1800 /map
     X1MP_006 /autosave 300 trace-5min /autoexit 320`, then `capture
     load-5min 60 /autoload trace-5min` (tracing runs the game slower than
     real time, so the save run waits for its own /autoexit).
  3. S1 #6 idle and walk animation frames (ref-shot `resume` shots, 0.5 s),
     #7 water/sky map, #8 combat effects (spawn enemy tanks via a sim order),
     #9 loading screen, Escape menu, Save and Load dialogs, score screen.
- Delivered 2026-10-14: menu-skirmish-2a/4a traces + lobby shots; ref-ui-*;
  S1 HUD unselected/selected, move order, fog default, 4 faction ACUs, build
  progress; S2 motion-unit (every tick to 2000), long-1800 (30 min + trace),
  icx-600 (intel + economy; no FIRE/DAMAGE, fixed since).
- Open: FAF fullscreen that fills the screen with an on-target mouse (the
  fullscreen session found the cause; see docs/crossover-recipe.md), FAF
  Campaign Lua error, input without focus (needs JStar's OK).

