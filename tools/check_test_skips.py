#!/usr/bin/env python3
"""Fail on an integration mode that skips without saying so.

A mode skips through osc::test_status::skip(reason): it exits 77, which ctest
counts as skipped, unless a check failed first. Three older shapes read as a
pass instead, so this check fails on them in tests/integration/runner and
src/app/*_test.cpp:

- std::exit(77) (or kExitSkippedNoData) outside test_status::skip: a failure
  recorded before it is lost;
- `pass++` on a line that says it skips (a comment or log naming "skip", no
  "[PASS]"): the skip counts as a passed check;
- a bare `return;` right after a log line that says it skips: the mode ends
  as a pass with the rest of its checks unrun.

tools/test_skips_baseline.txt lists the ones found when the check landed, as
"<path>: <the line>"; a listed one that is gone fails until it is taken off.

Usage: check_test_skips.py <repo root>    (exit 1 on a problem)
       check_test_skips.py --self-test
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

import scan_guard

RAW_EXIT = re.compile(r"\bstd::exit\s*\(\s*(77|(app::)?kExitSkippedNoData)\s*\)")
PASS_BUMP = re.compile(r"\bpass\s*\+\+|\+\+\s*pass\b|\bpass\s*\+=")
SKIP_WORD = re.compile(r"(?i)skip")
SKIP_LOG = re.compile(r"(?i)spdlog::\w+\s*\(.*skip")
BARE_RETURN = re.compile(r"^\s*return\s*;")
BASELINE = "tools/test_skips_baseline.txt"


def problems_in(rel: str, text: str) -> list[str]:
    lines = text.splitlines()
    out = []
    for i, line in enumerate(lines):
        if RAW_EXIT.search(line):
            out.append(f"{rel}:{i + 1}: exits 77 itself; skip with osc::test_status::skip(reason)")
        if PASS_BUMP.search(line) and SKIP_WORD.search(line) and "[PASS]" not in line:
            out.append(f"{rel}:{i + 1}: a skip counted as a pass; skip with osc::test_status::skip(reason)")
        if SKIP_LOG.search(line):
            after = [n for n in lines[i + 1:i + 3] if n.strip()]
            if after and BARE_RETURN.match(after[0]):
                out.append(f"{rel}:{i + 1}: logs a skip and returns as a pass; "
                           "skip with osc::test_status::skip(reason)")
    return out


def sources(root: Path) -> list[Path]:
    return sorted((root / "tests/integration/runner").glob("*.cpp")) + \
        sorted((root / "src/app").glob("*_test.cpp"))


def check(root: Path) -> list[str]:
    files = sources(root)
    guard = scan_guard.unscanned(root, [f.relative_to(root).as_posix() for f in files],
                                 "tests/integration/runner/integration_tests.cpp")
    if guard:
        return guard
    found = {}
    for path in files:
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for problem in problems_in(rel, text):
            where, _, _ = problem.partition(": ")
            line = text.splitlines()[int(where.rsplit(":", 1)[1]) - 1].strip()
            found[f"{rel}: {line}"] = problem
    listed = [entry for entry in (root / BASELINE).read_text().splitlines()
              if entry.strip() and not entry.startswith("#")]
    out = [p for key, p in found.items() if key not in listed]
    out += [f"{BASELINE}: {entry!r} is gone; take it off" for entry in listed if entry not in found]
    return out


def self_test() -> int:
    cases = [
        ("a raw exit", "if (!ok) std::exit(app::kExitSkippedNoData);\n", [1]),
        ("a raw 77", "std::exit(77);\n", [1]),
        ("the helper", 'osc::test_status::skip("no timestamps");\n', []),
        ("a skip counted", "pass++; // skip if no live projectiles\n", [1]),
        ("a pass about skipping", 'pass++; spdlog::info("[PASS] Test 5: the renderer skips it");\n', []),
        ("a skip returned", 'spdlog::warn("[SKIP] Test 8: no sound data");\n\n  return;\n', [1]),
        ("a skip then more", 'spdlog::warn("skipping Test 8");\n  t.check(x, "y");\n  return;\n', []),
        ("a return elsewhere", "if (done) {\n  return;\n}\n", []),
    ]
    failed = 0
    for what, text, want in cases:
        got = [int(p.split(":")[1]) for p in problems_in("tests/integration/runner/x.cpp", text)]
        if got != want:
            print(f"self-test: {what}: lines {got}, want {want}")
            failed += 1
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        if not check(root) or "was not scanned" not in check(root)[0]:
            print("self-test: a tree without the runner fails")
            failed += 1
        (root / "tools").mkdir()
        (root / BASELINE).write_text("# none\n")
        runner = root / "tests/integration/runner"
        runner.mkdir(parents=True)
        (runner / "integration_tests.cpp").write_text("void f() {\n  std::exit(77);\n}\n")
        if [p.split(":")[:2] for p in check(root)] != [["tests/integration/runner/integration_tests.cpp", "2"]]:
            print(f"self-test: the scan of a tree finds its raw exit: {check(root)}")
            failed += 1
        (root / BASELINE).write_text("tests/integration/runner/integration_tests.cpp: std::exit(77);\n"
                                     "tests/integration/runner/integration_tests.cpp: gone();\n")
        if [p.split(":")[0] for p in check(root)] != [BASELINE]:
            print(f"self-test: a listed one is allowed and a gone one fails: {check(root)}")
            failed += 1
    if failed:
        return 1
    print("self-test: ok")
    return 0


def main(argv: list[str]) -> int:
    if argv == ["--self-test"]:
        return self_test()
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    problems = check(Path(argv[0]))
    for p in problems:
        print(p)
    if problems:
        return 1
    print("test_skips: every mode skips through osc::test_status::skip")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
