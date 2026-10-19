---
name: doc-audit-practice
description: Use with /supcom-docs:doc-audit, or when the roadmap issue's Decisions settled changed or a thread is about to retire, to audit the docs agents read for stale or misleading guidance.
---

# Doc audit practice

Why: after a change of direction, old docs and worklogs teach agents dropped patterns. Two
independent auditors on one brief found different things (2026-10-18): Sonnet medium found the
judgement risks (what an agent would wrongly do), Haiku high found more mechanical slips (dead
links, wrong paths, failing commands). Keep both until the comparison tables show one adds nothing.

When: after a decision in the roadmap issue changes a direction, before the thread that made the
change retires. Not for routine edits.

What is mechanical goes in `mac/agents/dead-terms.txt` (enforced on every check), not in prose.

Brief template (fill the direction from the roadmap issue; keep the rest):

> Audit the docs agents read in this fork for anything that could make an agent assume something
> false or repeat a pattern we dropped. Current direction: <Destination and Decisions settled
> from the roadmap issue>. Scope: mac/README.md, mac/AGENTS.md, mac/docs/,
> mac/agents/ (skills, commands, hook comments), mac/tools/ and mac/scripts/
> headers and help, root AGENTS.md and CLAUDE.md, and today's local logs in mac/work/logs/ (not the
> archive folders). Flag text that describes the past instead of current guidance. Per finding: file and line, the current fact it contradicts, and an action
> (delete, or rewrite with replacement text). Rank by how likely it is
> to cause a wrong action. Say what you checked and skipped. Read only; write your report to the
> file named in your task.

Adjudication: apply what both found unless it is wrong; check single-model findings against the
files before applying; anything outside
the repo (issues, app settings, other folders) waits for JStar.
