---
name: doc-audit-practice
description: Use with /supcom-docs:doc-audit, or when STATUS.md's Decisions changed or a thread is about to retire, to audit the docs agents read for stale or misleading guidance.
---

# Doc audit practice

Why: after a change of direction, old docs and worklogs teach agents dropped patterns. Two
independent auditors on one brief found different things (2026-10-18): Sonnet medium found the
judgement risks (what an agent would wrongly do), Haiku high found more mechanical slips (dead
links, wrong paths, failing commands). Keep both until the comparison tables show one adds nothing.

When: `mac/scripts/check` prints a note when Decisions changed since the last recorded audit; run
the audit before the thread that made the change retires. Not for routine edits.

What is mechanical goes in `mac/agents/dead-terms.txt` (enforced on every check), not in prose.

Brief template (fill the direction from STATUS; keep the rest):

> Audit the docs agents read in this fork for anything that could make an agent assume something
> false or repeat a pattern we dropped. Current direction: <Decisions and key Facts from
> mac/STATUS.md>. Scope: mac/README.md, mac/AGENTS.md, mac/STATUS.md, mac/roadmap.md, mac/docs/,
> mac/notes/, mac/log/, mac/agents/ (skills, commands, hook comments), mac/tools/ and mac/scripts/
> headers and help, root AGENTS.md and CLAUDE.md, and today's local logs in mac/work/logs/ (not the
> archive folders). Dated history may describe the past; flag it only when an agent could read it
> as current guidance. Per finding: file and line, the current fact it contradicts, and an action
> (delete, rewrite with replacement text, or a one-line superseded note). Rank by how likely it is
> to cause a wrong action. Say what you checked and skipped. Read only; write your report to the
> file named in your task.

Adjudication: apply what both found unless it is wrong; check single-model findings against the
files before applying; dated history gets a superseded line, not a silent rewrite; anything outside
the repo (issues, app settings, other folders) waits for JStar.
