---
description: Compare the original with OpenSupCom (parity PROBE|--all, or motion | intel | bp ORIGINAL.log OSC.log, image REF.png OSC.png)
argument-hint: <kind> <original> <opensupcom> [--check] | parity <probe>|--all
allowed-tools: Bash(python3 -I mac/tools/parity/parity:*), Bash(python3 -I mac/tools/motion-compare/motion_compare.py:*), Bash(python3 -I mac/tools/intel-compare/intel_compare.py:*), Bash(python3 -I mac/tools/bp-dump/compare.py:*), Bash(uv run -q mac/tools/image-compare/compare.py:*), Read
---

Arguments: `$ARGUMENTS`

Read `${CLAUDE_PLUGIN_ROOT}/skills/capture-practice/SKILL.md` and its section on reading a divergence before drawing conclusions.

1. `parity` is the way to compare tick by tick. `parity PROBE` or `parity --all` runs
   `python3 -I mac/tools/parity/parity check PROBE|--all` (it runs OpenSupCom, from this checkout's build, and compares
   with the stored baseline of the original; `NO-REF` means no capture). `parity PROBE ORIGINAL.log OSC.log` runs
   `python3 -I mac/tools/parity/parity compare PROBE ORIGINAL.log OSC.log -v` (each log must be a complete run first). The status is MATCH, DIFFERS (first
   divergence: scene, phase, tick, field, both values) or INVALID (a run or log that cannot be used: report why).
   Capturing the original is `parity capture PROBE`, which opens a game window (mac/docs/toolchain.md, Comparisons).
2. The other kinds expect a kind and two files: the original's capture first, the OpenSupCom file second. Only `intel`
   allows an optional `--check` after the files. Anything else: reply with the usage in the description above. Run
   nothing. Run the comparator for the kind from the checkout root, with the two files (and the optional `--check` for intel):
   - `motion`: `python3 -I mac/tools/motion-compare/motion_compare.py ORIGINAL.log OSC.log`
   - `intel`: `python3 -I mac/tools/intel-compare/intel_compare.py ORIGINAL.log OSC.log [--check]`
   - `bp`: `python3 -I mac/tools/bp-dump/compare.py ORIGINAL.log OSC.log`
   - `image`: `uv run -q mac/tools/image-compare/compare.py REF.png OSC.png`
3. If the comparator reports no comparable lines (parity: INVALID), report that and stop.
4. Report the comparator's result and the files compared.
