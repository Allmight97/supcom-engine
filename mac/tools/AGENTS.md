# mac/tools: captures of the original and comparisons

- A capture answers one question. Look for a matching `.setup` manifest in `mac/work/traces/` and
  `mac/work/logs/` before running a new one; prefer a scripted scenario over a full game.
- Every capture goes through `lib/game-run.sh`: one game at a time under the bottle lock, hooks run from a copy,
  a final `NAME.log` only for a finished run (`.partial` means failed), and never over an existing capture.
- A new hook ends with its `HOOKCHECK` marker, or the run stops after 90 s.
- A comparator fails when the two sides share no samples; a pass with nothing compared proves nothing.
- Options live in each tool's header; docs point there instead of copying them.
- Tick-level comparison with the original goes through `parity/parity` (mac/docs/toolchain.md, Comparisons). A new
  probe gets an adapter and a synthetic fixture in its self-test before its first capture; its baseline is recorded
  by the second capture that compares equal. A negative control for an engine change goes through `mac/scripts/mutate`.
- `mac/work/parity/refs` is write-once: never edit, delete or overwrite a stored run; capture a new one. A backup
  never overwrites a different file. Stored runs are read only through `parity/runs.py`, which checks them.
- A capture or build that runs minutes goes in the background; follow its `watch:` file with Monitor
  (`tail -n +1 -F FILE | grep --line-buffered .`), so phases and errors reach the session.
- Toolkit code files stay under the 8,000-token budget: split a tool by concept (as `parity/` does), not by size.
