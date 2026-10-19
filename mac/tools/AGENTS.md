# mac/tools: captures of the original and comparisons

- A capture answers one question. Look for a matching `.setup` manifest in `mac/work/traces/` and
  `mac/work/logs/` before running a new one; prefer a scripted scenario over a full game.
- Every capture goes through `lib/game-run.sh`: one game at a time under the bottle lock, hooks run from a copy,
  a final `NAME.log` only for a finished run (`.partial` means failed), and never over an existing capture.
- A new hook ends with its `HOOKCHECK` marker, or the run stops after 90 s.
- A comparator fails when the two sides share no samples; a pass with nothing compared proves nothing.
- Options live in each tool's header; docs point there instead of copying them.
