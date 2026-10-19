---
description: Before shaping an upstream PR, a Sonnet agent (high effort) maps open upstream PRs against the fork's work; you decide build-on, stack, or send our own
argument-hint: "[topic or branch, e.g. effect-shaders]"
allowed-tools: Read, Bash(mac/scripts/upstream-news:*), Bash(git -C:*), Bash(gh pr view:*), Bash(gh pr diff:*), Agent
---

Topic: $ARGUMENTS (empty: every fork engine change not yet upstream). The upstream-pr skill holds the rest of the upstream PR process.

1. Run `mac/scripts/upstream-news` (fetches upstream; lists landings, then open PRs tagged MAC or
   OVERLAP with the fork's files).
2. Start one agent, Sonnet at high effort, read-only, with this brief and that output pasted in:
   for the topic's fork commits (`git -C . log --no-merges upstream/main..main -- src tests cmake
   CMakeLists.txt`, filtered to the topic) and each listed PR that touches the same files or
   subject (`gh pr view N --repo bwiemz/supcom-engine`, `gh pr diff`), say per PR: duplicate,
   conflicts, prerequisite, or independent, with the files and one line of evidence. Then
   recommend one of: build on their PR (and how to rebase ours), a PR stacked on theirs, or our own
   PR; and the commit grouping (coherent vertical slices) for it. Under 30 lines; label inferences.
3. Check the agent's claims you will act on against the diffs, then give JStar the recommendation
   and the one decision it needs. Never comment on, open or edit an upstream PR without his word;
   an upstream PR is a draft, cut as `up/<topic>` from `upstream/main` (root AGENTS.md).
