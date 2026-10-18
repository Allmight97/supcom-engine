# 2026-10-14 Reference capture backlog (CrossOver track)

Session: faf (owner of the CrossOver bottle). Captures of the original game for
S1 (render, UI) and S2 (sim) while Rosetta lasts, all scripted, no real input.

## Decisions

- JStar: stay on CrossOver 26.3 (Rosetta) until CrossOver 27 ships; capture the
  original while that still works (main session, STATUS.md).
- Main session: S1/S2 may request runs of existing tools directly; new options
  and shot sets need no OK; new tools and Game.prefs changes go via main.
- Main session: captures include the map's civilian armies by default.
- Bottle backend left at CrossOver Auto: terrain shots matched wined3d's
  within 0.05% of pixels.

## Done

- Tool options: lua-trace /tracemenuais, /autosave, /autoexit, /autoload
  (exit-based timing under tracing); ref-shot /refui (no "Game Paused"
  banner), per-shot `select`, optional camera, `sim` orders (move, build via
  SimCallback), `resume`, per-tick ACU pose and build fraction; sim-capture
  /simscript (motion-unit), /siminterval, /simvel, /simfactions, /simthreat,
  /simecon, /simintel, /simcombat, /simticks, /simbots, /simtrace;
  tools/lib/civilians-hook.
- Delivered: menu-skirmish-2a/4a; ref-ui-*; S1 HUD, move order, fog
  default, four faction ACUs, build progress; S2 motion-unit, long-1800,
  icx-600 (intel + economy).

## Failures, causes and fixes

- `git commit -- <paths>` skipped new (untracked) files: two pushed commits
  referenced missing hooks and scripts (S2 caught it); fixed in 552d5bd;
  now `git add` new files first.
- Blueprint ids: structures are `ueb…`, not `uel…`; the build order and the
  motion script failed silently or with "Unknown unit type" until fixed.
- Combat lines: wrapping Lua class methods missed subclasses that had already
  copied them; wrapping the engine methods (CreateProjectile, AdjustHealth)
  in a globalInit hook works. The first hook version ran in the user state
  too and called a missing global (HasCommandLineArg) in the sim.
- Tracing slows the game below real time, so a wall-clock wait ended the
  save run before its save; lua-trace now waits for the game's own exit.
- Editing a capture script while it runs broke its last lines twice (shell
  reads scripts incrementally); finished the rename by hand.
- Civilians: the GOG and FAF command-line launch read teams.ExtraArmies; maps
  keep them in customprops. First fix in the launch hook shifted entity ids
  and briefly failed S2's ctest; replaced by a GetExtraArmies hook, and
  motion-unit runs leave civilians out.

## Left open

- Pending captures (notes/scratchpad.md): S2 combat-600 (stopped at tick
  840 for the pause), main C save/load trace, S1 #6-9.
