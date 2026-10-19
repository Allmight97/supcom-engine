# 2026-10-19: issue audit, root causes, roadmap decisions

Main session (Opus medium) with JStar. Helpers: Haiku high (fact check), Sonnet high (dispositions),
GPT 6.1 Sol xhigh (technical depth), Fable 5.1 (advisor), Opus medium (architecture scan, PR fixes),
a separate FAF session. Evidence on the dev Mac: `mac/work/logs/issue-audit-2026-10-19/`,
`mac/work/logs/faf-native-2026-10-19/`.

## Decisions (JStar)

Recorded in STATUS Decisions, with the [decision page](https://claude.ai/artifact/SZwjqSDf98x1Rq5YLrj4Mr):
delete upstream's installed-SDK driver discovery in the fork; Apple Silicon only (macOS 14+);
keep "without upscaling"; one logical change per upstream PR (stacked PRs do not work across
forks); try DXVK or D3DMetal on the capture bottle after the sync; rewrite #1, #6, #7, #8 and file
two issues; the focus-army desync: prove, then leave script threads out of the compared checksum.
Standing direction: design bugs away at their source; patch only when unavoidable. FAF goes in #9.

## Done

- PR bwiemz #750 kept current: upstream merged in three times (#749, #756, #764), all checks rerun
  each time; a pre-push audit and a re-audit by GPT 6.1 Sol (xhigh) found the effect clock's
  one-hour wrap and three weak tests, fixed on the branch and on fork main (`86f6d8dd`).
- `mac/scripts/format` (clang-format 22, as CI pins); the refresh-rate menu keeps only even
  divisors of the panel's rate (`5fba72c0`); play defers to the Video options with the Metal HUD on.
- The upstream-pr skill in the supcom-upstream plugin.
- Issue audit of #1, #2, #4-#8 against fork main and upstream main; the roadmap proposal.
- Architecture scan (`improve-codebase-architecture`): four families. F4 focus army reaches the
  checksum (the strongest), F2 one rule many holders (41 raw blueprint lookups; #4), F1 silent
  fallback (18 retail ShaderNames reach the Unit fallback), F3 platform drift (8-bit targets,
  emitter LOD).
- Fork issue #9 (FAF): OSC-versus-OSC through FAF's client needs no FAF change; mixing with
  Windows FA.exe is not practical now; Linux joins the same way.

## Findings moved here from STATUS

- Build sparks (2026-10-18): OSC creates and draws them as retail's rules say; 1-3 px at zoom 30-60
  (1600x900 frames), gone past zoom ~115 (LODCutoff 100), never created for a build ordered while
  zoomed out (CreateIfVisible). Retail CanSeeCam (GOG exe 0x0065C3A0) compares LODCutoff with the
  view's width at the point's depth times a per-fidelity scale (0.9/1.0/1.2/1.0, .data 0xF57E30).
- JStar's evening play, 2026-10-18 (before the dome and 8-bit fixes): smooth; the nuke clipped with
  zoom; a glow around lights; fans at 118 fps; the original in CrossOver at /windowed 2560 1440
  looked soft. All but the fans were fixed the same evening; at 60 Hz he heard no fans.
- Render cost (2026-10-18, upstream's --render-bench, battle scene, M4 Max, before the 8-bit
  targets): GPU p50 4.69 ms at 1920x1080, 5.35 at 2560x1440, 9.59 at 5120x2880; about 3.9 ms that no
  size changes; three whole-map terrain draws of 1,572,864 indices each (normal pass, main pass,
  shadow casters). Two read-only opinions: `mac/work/logs/perf-opinions-2026-10-18.md`.
- The headless replay of JStar's 2026-10-18 game on fork main diverges at tick 3875 of 4341: the
  nuke's damage to his self-destructed ACU. Ctrl-K is recorded (SimCallback); the likely cause is
  the client-local focus army reaching sim scripts that fork threads the checksum counts.

## Failures, causes, fixes

- A merge resolution by a regex script mangled a conflict block in `renderer.cpp`; the build caught
  it before any push. Redone with a line-by-line resolver.
- Issue #5's "0 commits behind" was stale because the daily schedule has never fired (only manual
  runs); check that it fires.
- `mac/STATUS.md` passed the check's 170-line limit; run details moved here.

## Open

The roadmap in STATUS Next actions, from the upstream sync on.
