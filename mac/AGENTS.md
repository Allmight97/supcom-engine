# mac/: the Mac-developer toolkit for OpenSupCom

## Outcome

Supreme Commander: Forged Alliance runs natively on JStar's Mac through
OpenSupCom (OSC, [bwiemz/supcom-engine](https://github.com/bwiemz/supcom-engine),
MIT, C++20, Vulkan through KosmicKrisp on Metal 4), faithful to the original,
with FAF and its improvements. JStar is OSC's macOS developer; Mac work lands on the
fork's main first and is offered upstream as pull requests where upstream can take it.

One checkout, `~/Projects/OpenSupCom`, JStar's fork
([Allmight97/supcom-engine](https://github.com/Allmight97/supcom-engine)):

- Outside `mac/`: upstream's engine plus Mac engine changes. Upstream's own rules
  apply there (`CONTRIBUTING.md`, `docs/provenance-and-compatibility.md`); its tests
  prove engine changes.
- `mac/` (this folder, MIT): everything else. The play command and build recipe,
  capture and comparison tools for the original game, guards, status and plans,
  Claude plugins. It came from Allmight97/SupCom (history there and in its tag
  `native-engine-final`).
- Fork-only files outside `mac/`: `AGENTS.md`, `CLAUDE.md` and the banner at the top
  of `README.md`.
- Branches: `main` is the fork. Mac engine work goes on `mac/<topic>` branches and
  merges into `main`. An upstream pull request goes on an `up/<topic>` branch cut
  from `upstream/main`, with only the engine commits cherry-picked; it never carries
  `mac/`, the root `AGENTS.md` or `CLAUDE.md`, or the README banner. The pre-push
  hook refuses an `up/*` branch whose commits touch the first three.

Read [STATUS.md](STATUS.md) when joining or resuming: it owns current facts,
decisions, open questions and next actions, and nothing else. The plan is
[roadmap.md](roadmap.md). Procedures are in
[docs/toolchain.md](docs/toolchain.md). Unsettled notes go in
`mac/notes/scratchpad.md` (dated entries). At the end of a session, add one
`mac/log/YYYY-MM-DD-TOPIC.md`: decisions, what was done, failures with causes and
fixes, what is open. Never edit an earlier log.

## How we judge work

- Start from what a player feels and an observed failure: interface scale, frame
  pacing (the worst frames, not the average), input latency, first-use shader
  hitches. Go narrow and deep; widen only when a measurement points somewhere.
- Measure before tuning: `mac/scripts/play --hud` today; `xctrace` and frame-capture
  procedures are M2 deliverables (roadmap.md).
- Every human observation becomes a command that reproduces it: a replay plus a
  screenshot at a tick, or a capture of the original plus a comparator. Agents then
  check it without a person.
- Faithful to the original: when OSC and the original disagree, a capture of the
  original decides, not a decompiler reading or a guess.
- A Mac build must pass OSC's cross-platform lockstep checks before anyone plays
  online (floating-point contraction on arm64 can change results).
- Prefer the simplest change that serves the outcome. Upstream's maintainer reviews
  every PR: small, one logical change per commit, messages that say why.

## Evidence and game files

- Contributors supply their own game. Never commit game files, captures, game
  screenshots, saves or replays. Guards: `mac/agents/githooks/pre-commit` and
  `pre-push`, which `mac/scripts/setup` copies to `.git/mac-hooks/` so they run on
  every branch. Never bypass a hook (`--no-verify`, `add -f`);
  `mac/agents/hooks/block-git-bypass.sh` blocks those commands, even inside a heredoc,
  so put such text in a file.
- `mac/work/` (ignored; never committed) holds the player's game (`mac/work/game`,
  which OSC reads), the reference corpus of the original (`mac/work/traces`,
  `mac/work/logs`, including reference screenshots), the Ghidra project
  (`mac/work/ghidra`), the Vulkan SDK, and play-test evidence (`mac/work/playtests`).
  `mac/work/downloads/` holds acquired originals; never patch the only copy. Record
  byte sizes and SHA-256 identities of new originals.
- The original runs only in CrossOver under Rosetta, which macOS 28 removes.
  CrossOver serves only reference captures; capture what we need while it runs.
- OSC's provenance policy: a rule learned from a decompile is re-expressed and
  tested; decompiled code is never copied. faf-re (Draiget/faf-re) has no licence:
  read it as a behaviour reference only.
- Label observations, inferences and unknowns. Static analysis does not establish
  runtime behaviour. Tie findings about the original to the executable's SHA-256 and
  function addresses.
- The Ghidra project allows one opener at a time: run pyghidra scripts through
  `mac/scripts/ghidra-py`. Bound tool output; write long results to `mac/work/logs/`.

## Verification

- Run `mac/scripts/check` before a commit that touches `mac/`, `AGENTS.md`,
  `CLAUDE.md` or `README.md`. It proves the toolkit only. The commit hook refuses
  unless the last check passed on exactly the staged content: `git add` every file
  first, edit nothing after.
- Engine changes: the tests CONTRIBUTING.md names (unit, `ctest -L mp`, and
  `ctest -L gate` before every PR), `mac/scripts/osc-smoke` and `mac/scripts/osc-render-check`, as in
  [docs/toolchain.md](docs/toolchain.md); a nontrivial bug fix shows its test failing first.
- Report checks run, checks not run, failures and deletions.
- Docs stay true to the current direction: `mac/scripts/check` fails on a term from
  `mac/agents/dead-terms.txt` in live guidance (add dropped terms there when a direction
  changes) and notes when STATUS's Decisions changed since the last `/supcom-docs:doc-audit`.

## Collaboration

- JStar's mouse, keyboard and window focus are his. Agents never send real input
  or raise windows unless JStar created `~/.supcom-input-ok`; agents never create
  it (`mac/agents/hooks/block-real-input.sh`). Validate with scripted, hidden runs and
  offscreen screenshots; JStar does the visual play tests (`mac/scripts/play`).
- Work in the existing checkout. Ask JStar before creating a worktree, deleting a
  database or resetting user data. `origin` is JStar's fork
  (Allmight97/supcom-engine) and `upstream` is bwiemz's (push disabled by
  `mac/scripts/setup`). Mac work lands on the fork; a PR to upstream needs JStar's word.
- Audits: Haiku at high effort for mechanical sweeps (paths, links, consistency);
  Sonnet at medium or better when the question is what could mislead an agent.
- One session at a time owns the checkout; STATUS.md "Tracks" names it.
  Another session that needs it asks JStar for a worktree instead of switching branches.
- Main session: Opus at medium; judgement and adjudication stay there with JStar.
  Delegate bounded labour to Haiku at high, judgement-heavy subtasks to Opus at
  medium, and coding tasks or second opinions to GPT 6.1 Sol at high through
  `codex exec` (stdin closed: `</dev/null`). Give Codex a narrow brief that names the files to touch. Stop a
  run that has edited no file after 20 minutes. Prefer Codex for review over open-ended
  implementation.
- Commit with `git commit -m … -- <paths>`; one logical change per commit, as
  CONTRIBUTING.md asks; merge branches into `main` with a merge commit; push at
  milestones and pauses. Git command restrictions are enforced by
  `mac/agents/hooks/block-git-bypass.sh`.
- The CrossOver bottle and the Ghidra project are shared; check running processes
  before changing either.
