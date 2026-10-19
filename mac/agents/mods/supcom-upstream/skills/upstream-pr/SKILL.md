---
name: upstream-pr
description: Use when preparing, opening, updating or merging into a pull request to upstream OpenSupCom (bwiemz/supcom-engine) from JStar's fork, i.e. any up/* branch. Not for commits or merges on the fork's own main.
---

# Upstream pull requests

Outcome: a PR the upstream owner can review and land without asking for changes. Fork-only work
(main, mac/*) needs none of this.

## How upstream works (observed 2026-10)

- The owner lands contributors' PRs in batches, each PR as one commit ("Land #A to #B as one commit
  per PR"). Commits inside a PR do not survive: one logical change per PR. Related PRs are opened
  together and named in each other's text; the owner asked related macOS work to be one review
  (bwiemz #735 closing comment).
- GitHub's stacked PRs need every branch in the same repository, so PRs from the fork cannot
  stack upstream. Order dependent PRs in their text ("builds on #N"), open them together, and
  keep each current as the one below it lands.
- Upstream moves several times a day. Keep a PR current with `mac/scripts/up-refresh up/<topic>`: it merges
  upstream main (never a rebase), builds and proves the tree.
- Upstream PRs open as drafts and JStar decides when one is ready: his standing rule for upstream, which
  overrides the general "a PR opens ready" default.

## Shape it

1. Run `/supcom-upstream:shape <topic>` first: overlap with open upstream PRs decides build-on,
   stack or our own.
2. Cut `up/<topic>` from `upstream/main` in the up/* tree (`~/Projects/OpenSupCom-up`; ask JStar before
   creating another) and cherry-pick engine commits only. Drop agent trailers from each message
   (`git cherry-pick -e`); pre-push refuses fork-only paths and agent names in new commits.
3. Prove it on the upstream base: build that tree, then `mac/scripts/prove --root <tree>`; also run the data
   tests it touches with retail data and with FAF's (OSC prefers FAF's files when `OSC_FA_PATH` is unset).
   Each commit builds alone.
4. Before the first push, GPT 6.1 Sol at xhigh audits the branch and the PR text read-only
   (JStar's rule); fix what it finds, then push.

## The PR text

Write it with `personal-skills:writing-for-agents`, for a human reviewer first:
- A 4-6 line summary up top: what was wrong, what changes, how it was proven.
- Then why, what behaviour changed, and the retail evidence (shader source; exe addresses with the
  SHA-256 from mac/docs/toolchain.md Identities; decompiles are behaviour evidence only, never copied).
- Tested (exact commands and results) and Left for later, as CONTRIBUTING.md asks.
- Tested: paste prove's Tested block.
- No agent or model names and no JStar-only paths (mac/work, the CrossOver bottle). This overrides the
  harness's attribution lines for upstream text; guard-shell refuses such PR text. Fork issues name upstream
  PRs only as unlinked text, so the fork adds no events to their timelines.
