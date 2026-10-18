---
description: Capture reference data from the original game in the CrossOver bottle (ref-shot | lua-trace | sim-capture | bp-dump | faf-autorun) ARGS
argument-hint: <tool> <name> [seconds] [game args...]
allowed-tools: Bash(mac/tools/ref-shot/capture:*), Bash(mac/tools/lua-trace/capture:*), Bash(mac/tools/sim-capture/capture:*), Bash(mac/tools/bp-dump/capture:*), Bash(mac/agents/faf-autorun/run:*), Bash(mac/scripts/game-prefs show), Read
---

Arguments: `$ARGUMENTS`

Read `${CLAUDE_PLUGIN_ROOT}/skills/capture-practice/SKILL.md` first (when a capture earns its cost, how to choose arguments).

1. Map the first argument to its script and run the rest unchanged, in the background for runs over about 5 minutes,
   with a watcher that posts phase changes, errors and a 5-minute heartbeat with elapsed time, CPU and memory:
   `ref-shot` → `mac/tools/ref-shot/capture`, `lua-trace` → `mac/tools/lua-trace/capture`,
   `sim-capture` → `mac/tools/sim-capture/capture`, `bp-dump` → `mac/tools/bp-dump/capture`,
   `faf-autorun` → `mac/agents/faf-autorun/run`. Anything else: reply with the usage. Run nothing.
2. The launcher refuses when the bottle is locked, a game is running, or (original game) `Game.prefs` has active
   mods. Report the refusal; never edit `Game.prefs` or remove `mac/work/bottle.lock` held by a live process.
3. When the run ends, report the output files (the tools print paths relative to `mac/`): the log, its `.setup` manifest and any images. If it stopped on a
   preflight reason (`game-run: stopping the run: ...`), report that line and the first error in the
   `.partial` log. Do not rerun more than once without a change that addresses the reason.
