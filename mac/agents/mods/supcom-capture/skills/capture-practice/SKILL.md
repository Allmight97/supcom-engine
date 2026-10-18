---
name: capture-practice
description: Running reference captures of the original game and reading divergences: scripted scenarios, arguments, setup manifests, and judging a difference between the original and OpenSupCom. Use before /supcom-capture:capture or /supcom-capture:compare. Not for OpenSupCom's own tests or play runs; see mac/docs/toolchain.md.
---

# Reference captures of the original

The original runs only in the CrossOver bottle, one game at a time. Procedures and every option:
mac/docs/toolchain.md (Shared launcher; Reference screenshots; Unit motion and threat capture; Lua call trace;
Scripted FAF runs).

## Before running one

Whether a capture is worth its cost is the requesting session's call. Check
`mac/work/traces/` and `mac/work/logs/screens/` for an existing capture with a matching `.setup` first, and run the
smallest capture that answers: the fewest ticks, one log type, one shot set.

## Scripted scenario first

- Default to a short scripted scenario (`/simscript NAME`, scripts in `mac/tools/sim-capture/scripts/`): it spawns
  exactly the units and orders the question needs, at tick 1, so the run takes minutes, not a full game.
  `gallery` spawns every tech 2, tech 3 and experimental unit and structure per faction with ample resources,
  orders upgrades and sets the galleries fighting; `motion-unit` scripts single-unit moves.
- Natural long games only for emergent behaviour: economy curves, AI build orders, AI decisions over time.
- Add `/simspeed 10` to a scripted run: the original holds a sim rate of about 6 to 8 while recording (measured
  2026-10-14; `SETUP|SPEED` and `SETUP|RATE` lines log it). Leave it off when real-time pacing matters
  (screenshots of motion, anything timed by wall clock).
- Captures without screenshots run in a 640x480 window (the launcher sets it); only ref-shot needs full size.

## Choosing arguments

- Match the setup you will compare against: map, factions (`/simfactions`, `/reffactions`), civilians (on by
  default; `/nocivilians` for older captures), AI type. The `.setup` manifest records what actually ran.
- Prefer event ends (`/autoexit`, `SIMCAP|END`) to wall-clock waits: tracing slows the game below real time.
- Structure blueprints are `ueb…`, mobile units `uel…`; a wrong id fails at spawn ("Unknown unit type").
- A new hook must log `HOOKCHECK|/<mount>/<path>|ok` as its last line, or the run stops after 90 s.

## Reading a divergence

- Match map, armies, factions, options, seed and tick range. Record each executable and hook identity;
  those identities need not match.
- AI choices diverge after a while: judge per-blueprint motion figures and early events (first build, first
  contact), not late positions.
- The original's state flags can lag reality (formed tanks report Moving after they stop): prefer positions.
- Find the first observable divergence. Inspect the relevant OSC path and retail or FAF callers.
  Use Ghidra when the remaining behavior is unclear; runtime captures decide disagreements.
