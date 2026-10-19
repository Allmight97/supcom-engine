# JStar's fork of OpenSupCom

This checkout is Allmight97/supcom-engine, a fork of bwiemz/supcom-engine (`upstream`; pushes disabled).
Outside `mac/` it holds upstream's engine plus Mac engine changes, under upstream's rules: read
`CONTRIBUTING.md` and `docs/provenance-and-compatibility.md` before engine edits. `mac/` holds the Mac toolkit;
`mac/AGENTS.md` routes its work. The plan and all work in flight: fork issue #12 and its sub-issues.

Rules for every agent here (guards named in brackets refuse the fixed patterns):
- Mac engine work goes on `mac/<topic>` branches into `main` with a merge commit. An upstream PR is an `up/<topic>`
  branch cut from `upstream/main` with engine commits only, no fork files and no agent names [pre-push]. Shape and
  prove it locally, then open it ready, as upstream lands them. Any write to upstream needs JStar's word [guard-shell].
- Never commit game files, captures, game screenshots, saves or replays [pre-commit]. `mac/work/` (ignored) holds
  them, including the only captures of the original; never delete there without JStar [guard-shell].
- JStar's mouse, keyboard and windows are his: no real input unless he granted it [guard-input].
- A rule learned from a decompile is re-expressed and tested, never copied. faf-re has no licence: behaviour
  reference only.
- Never bypass a guard. If one refuses something JStar asked for, tell him; he decides.
