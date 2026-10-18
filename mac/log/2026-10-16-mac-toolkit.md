# 2026-10-16 (main): first play test, the toolkit trim, review rounds

## Decisions (JStar)

- All effort goes to OpenSupCom (OSC); the native engine and further CrossOver work stop.
  CrossOver serves only reference captures of the original.
- JStar is OSC's macOS developer. First contribution: a formal Mac build, opened as a PR
  without asking the maintainer first; JStar says when it is ready.
- This repo becomes the Mac-developer toolkit; the OSC checkout holds only upstream plus
  Mac changes (chosen over carrying tooling inside a fork).
- Interface scale: keep the full Retina framebuffer and scale only the interface (not the
  half-resolution fix the `mac-ui-scale` session first committed).
- Delegation: Opus 5.5 medium for judgement-heavy subtasks, Haiku high for bounded labour,
  GPT 6.1 Sol high for coding and second opinions; adjudication stays in the main thread.

## Done

- Synced the OSC checkout to upstream `df11a927` (fast-forward), rebuilt, unit tests
  1,540/1,543, headless SCMP_009 smoke clean. JStar's first play test: playable, 120 fps
  title bar, audio perfect; tiny interface on 5K, anti-aliasing options error, a pink
  tint on moving units (notes/play-test-2026-10-16.md).
- Consults on 5K UI and rendering (work/logs/consult-5k-{gpt,fable}.md). Verified leads:
  the game rendered 5760x3240 targets ("looks like" 2880x1620); the pink is OSC's
  selection highlight (team colour blended halfway to white in `unit_renderer.cpp`).
- Toolkit plan reviewed by GPT 6.1 Sol and Fable, then carried out by an Opus agent:
  tag `native-engine-final` pushed; `~/Projects/SupCom-archive-2026-10-16.tar.gz`
  (95 MB, git bundle of every branch, worktree leftovers, trial evidence); 283 tracked
  files and about 9 GB of rebuildable output removed; build recipe moved to `osc/`;
  `scripts/osc-setup` guards the OSC checkout (commit 8fd4fa8).
- Docs and plugin reviewed with writing-for-agents by Sonnet, Opus, Haiku and GPT 6.1 Sol;
  adjudicated in work/logs/docs-adjudication.md and implemented by GPT 6.1 Sol: one rule
  for upstream PRs, an OSC AGENTS.md for Codex and Claude, push to upstream disabled,
  git rules enforced by hooks, `scripts/osc-smoke`, build-script and lock fixes, Apple's
  game-porting skills moved to the OSC checkout.
- Uninstalled the retired plugins `supcom-metal` and `supcom-session`.

## Failures and fixes

- My first smoke run gave the map's short name; OSC needs the full scenario path.
- My first build watcher matched the wrong process and ended early; re-armed on the
  build script's own output.
- Codex's write sandbox blocked edits under `.agents/` and the OSC `.git`; it left a
  patch, which the main session applied, and the main session ran `scripts/osc-setup`.
- A review claimed plugins run from a stale cache; `claude plugin list` and the refreshed
  skill list showed they load from `.agents/mods`, so the check only flags installed
  plugins whose source is gone.

## Open

- `mac-ui-scale`: rework to full-resolution world plus scaled interface; then JStar's
  play test at "looks like" 2560x1440, 2880x1620 and native.
- Where the second copy of the reference corpus goes.
- The Mac build PR set (notes/roadmap.md M1).
