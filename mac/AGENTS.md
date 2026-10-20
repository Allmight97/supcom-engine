# mac/: the Mac toolkit for OpenSupCom

Supreme Commander: Forged Alliance runs natively on the Mac through OpenSupCom (OSC), faithful to the original,
with FAF. Mac work lands on the fork's `main` first and goes upstream as PRs where upstream can take it. The
root `AGENTS.md` holds the rules for every agent; this file routes toolkit work.

## Where things are

- Play and build: `mac/scripts/play`, `mac/recipe/build.sh`. Procedures: [docs/toolchain.md](docs/toolchain.md).
  The original game in CrossOver: [docs/crossover-recipe.md](docs/crossover-recipe.md).
- Guards, hooks and Claude plugins: `mac/agents/` (its own AGENTS.md). Capture and comparison tools for the
  original: `mac/tools/` (its own AGENTS.md).
- Upstream: `mac/scripts/upstream-news` (what upstream is doing), `mac/scripts/sync-upstream` (merge it into the
  fork), `mac/scripts/up-refresh` (keep an up/* PR current), `mac/scripts/prove` (the engine checks a change
  needs, with the Tested block for the PR text). The upstream-pr skill holds the PR practice.
- `mac/work/` (ignored): the player's game (`game`), the reference corpus of the original (`traces`, `logs`),
  the Ghidra project, the Vulkan SDK, play-test evidence, `downloads` (acquired originals: never patch the only
  copy; record new ones in toolchain.md Identities), and `notes` for unsettled agent notes.
- Fork-only files outside `mac/`: `AGENTS.md`, `CLAUDE.md`, the banner atop `README.md`, and
  `.github/workflows/mac-upstream-watch.yml`. pre-push keeps all but the banner out of up/* branches.

## How we judge work

- Start from what a player feels and an observed failure: frame pacing (the worst frames, not the average),
  interface scale, input latency, first-use hitches. Go narrow and deep; widen only when a measurement points.
- Measure before tuning: `mac/scripts/play` (Metal HUD on) and upstream's `--render-bench`.
- Upstream moves fast (tens of PRs a day). Before engine work, check overlap with its open PRs
  (`mac/scripts/upstream-news`, `/supcom-upstream:shape`) and build on theirs, not beside it.
- Design a bug's class away at its source (a deep module, an enforced boundary, a ratchet) before patching one
  case. A loop of narrow fix-and-test rounds is the sign to step back and redesign.
- A repeated procedure or a fixed rule becomes a script, hook or check that agents run; prose keeps judgement.
- Rendering work starts from the current KosmicKrisp, Metal 4 and Vulkan documentation and driver behaviour
  (they move fast), and aims at Retina displays, 2K to 5K at 120 Hz without upscaling (#6).
- Every human observation becomes a command that reproduces it (a replay plus a screenshot at a tick, or a
  capture of the original plus a comparator), so agents check it without a person.
- When OSC and the original disagree, a capture of the original decides, not a decompile or a guess. Tie
  findings about the original to the executable's SHA-256 and function addresses; label inferences.
- No online play until the Mac passes OSC's cross-OS lockstep check (#10).
- The original runs only in CrossOver under Rosetta, which macOS 28 removes: capture what the corpus needs (#15).

## Verification

- `mac/scripts/check` proves the toolkit; the commit hook requires it on exactly the staged content, so
  `git add` every file first and edit nothing after.
- Engine changes: `mac/scripts/prove`; a nontrivial bug fix shows its test failing first.
- After a decision changes a direction, add the dropped terms to `mac/agents/dead-terms.txt` and run
  `/supcom-docs:doc-audit`.

## Working here

- One session at a time works in this checkout; another that needs it asks JStar for a worktree.
- Commit with `git commit -m … -- <paths>`, one logical change per commit.
- The CrossOver bottle and the Ghidra project are shared: go through `mac/tools/lib/game-run.sh` and
  `mac/scripts/ghidra-py`, which lock them.
