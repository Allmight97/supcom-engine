# 2026-10-18: one repository, the toolkit moves into mac/

## Decisions (JStar)

- The Mac toolkit leaves Allmight97/SupCom and lives in the fork's public `mac/`
  folder, relicensed MIT (JStar is its only author). The old repository is archived
  afterwards by the main session.
- `mac/scripts/play` passes `--fps-cap -2` by default; an `--fps-cap` after `--` replaces it.
- The plan and GPT 6.1 Sol's review of it (eight changes, all accepted) are in
  `mac/work/logs/consolidation-plan.md` and `mac/work/logs/review-consolidation-gpt.md`.

## What was done

- Secret scan of SupCom's 124 tracked files before publishing: no tokens, keys or
  private paths. The only email is the vcpkg patch author's, in Microsoft's port patches.
- Copied the tracked files (no history) into `mac/`: `osc/` to `recipe/`, `.agents/` to
  `agents/`, `notes/roadmap.md` to `roadmap.md`, `scripts/osc-setup` to `scripts/setup`.
  Paths rewritten in the scripts, tools, plugin, README, AGENTS, STATUS, roadmap and
  docs; notes and logs keep their dated text.
- Guards outside the tree: `setup` copies `pre-commit` and the new `pre-push` to
  `.git/mac-hooks/` and the Claude hooks to `.git/mac-hooks/claude/`, excludes
  `/mac/work/`, and no longer generates the root AGENTS.md and CLAUDE.md. The old
  exclude lines for those two files were removed by hand before staging.
- `tree-snapshot` writes paths from the checkout root. The new nested-toolkit case in
  `check` fails with the old `tree-snapshot` (six receipt cases rejected) and passes now.
- Data: `~/Projects/SupCom/work` moved to `mac/work/` and `downloads/` to
  `mac/work/downloads/` (same disk, `mv`; 22 GB). Nothing deleted.
- Rebuild with `OSC_FA_PATH`, `VULKAN_SDK` and `VK_DRIVER_FILES` unset. The CMake
  cache named the old SDK and overlay paths, so it was deleted first; afterwards it
  names no SupCom path.
- Plugin: uninstalled the SupCom-scoped `supcom-capture`, re-registered the `supcom`
  marketplace at `mac/agents/mods`, installed 0.1.2 at local scope for OpenSupCom.
  `/supcom-capture:compare` answers in a headless session started in the checkout.

## Checks (2026-10-18, rebuilt tree, engine identical to main 7d39ac25)

- `mac/scripts/check`: all checks passed.
- Unit tests: 1,594 cases (3 skipped), 169,643 assertions pass.
- `ctest -L mp`: 4/4. `ctest -L gate`: 269/269 (7 golden tests skipped: their images
  live outside the repository).
- `mac/scripts/osc-smoke`: SMOKE_OK. `mac/scripts/osc-render-check`: RENDER_CHECK_OK,
  driver KosmicKrisp.
- Pre-push in a scratch repository refused an `up/` branch carrying a `mac/` commit.

## Open

- JStar: `mac/scripts/play --hud` after the move; the overnight changes by eye.
- FAF client's game command (`~/.faforever/client.prefs`) still names
  `~/Projects/SupCom/.agents/faf-crossover`; repoint it to
  `~/Projects/OpenSupCom/mac/agents/faf-crossover game %s` before the old folder goes.
- Not run: `tools/check_format.sh` and clang-tidy (no engine code changed).
