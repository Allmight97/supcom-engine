---
description: Two models (Sonnet medium, Haiku high) audit the docs agents read for stale or misleading guidance; you compare and adjudicate
allowed-tools: Read, Write, Bash(mac/scripts/doc-hygiene:*), Bash(git -C:*), Agent
---

Read ${CLAUDE_PLUGIN_ROOT}/skills/doc-audit-practice/SKILL.md first and follow it.

1. Run `mac/scripts/doc-hygiene` (dead terms) and fix or note its hits before auditing.
2. Write the brief to `mac/work/logs/doc-audit-YYYY-MM-DD-brief.md` from the skill's template, with
   the current direction taken from the roadmap issue's Destination and Decisions settled
   (`gh issue view 12`).
3. Start two background agents on that brief, in one message: Sonnet at medium effort writing
   `doc-audit-YYYY-MM-DD-sonnet.md`, Haiku at high effort writing `doc-audit-YYYY-MM-DD-haiku.md`
   (both in `mac/work/logs/`, read only otherwise).
4. When both finish, write `doc-audit-YYYY-MM-DD-adjudication.md`: a table of findings found by
   both, by Sonnet only, by Haiku only; your verdict per finding (apply, reject with reason, ask
   JStar); and the exact edits. Ask JStar about anything outside the repo or anything that changes a
   decision.
5. Apply the accepted edits, add newly dropped terms to `mac/agents/dead-terms.txt`, run
   `mac/scripts/check`, then commit.
6. Report to JStar: the comparison table's counts, what changed, what waits on him.
