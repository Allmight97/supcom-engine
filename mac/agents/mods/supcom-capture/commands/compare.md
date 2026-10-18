---
description: Compare a capture of the original with an OpenSupCom run (motion | intel | bp ORIGINAL.log OSC.log, image REF.png OSC.png)
argument-hint: <kind> <original> <opensupcom> [--check]
allowed-tools: Bash(python3 -I mac/tools/motion-compare/motion_compare.py:*), Bash(python3 -I mac/tools/intel-compare/intel_compare.py:*), Bash(python3 -I mac/tools/bp-dump/compare.py:*), Bash(uv run -q mac/tools/image-compare/compare.py:*), Read
---

Arguments: `$ARGUMENTS`

Read `${CLAUDE_PLUGIN_ROOT}/skills/capture-practice/SKILL.md` and its section on reading a divergence before drawing conclusions.

1. Expect a kind and two files: the original's capture first, the OpenSupCom file second. Only `intel` allows
   an optional `--check` after the files. Anything else:
   reply with the usage in the description above. Run nothing.
2. Run the comparator for the kind from the checkout root, with the two files (and the optional `--check` for intel):
   - `motion`: `python3 -I mac/tools/motion-compare/motion_compare.py ORIGINAL.log OSC.log`
   - `intel`: `python3 -I mac/tools/intel-compare/intel_compare.py ORIGINAL.log OSC.log [--check]`
   - `bp`: `python3 -I mac/tools/bp-dump/compare.py ORIGINAL.log OSC.log`
   - `image`: `uv run -q mac/tools/image-compare/compare.py REF.png OSC.png`
3. If the comparator reports no comparable lines, report that and stop.
4. Report the comparator's result and the files compared.
