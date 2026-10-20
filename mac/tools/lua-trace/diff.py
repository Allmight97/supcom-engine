#!/usr/bin/env python3
"""Compare the engine calls of two Lua call traces (mac/tools/lua-trace logs).

Usage: diff.py ORIGINAL.log OURS.log [--bindings mac/work/lua-bindings.json] [--kind user]
       diff.py --self-test

ORIGINAL is a trace of the original game (mac/tools/lua-trace/capture); OURS is a
trace in the same format (OpenSupCom has no producer yet). Reports the functions only the
original called, the functions only we called, the first point where the
first-call order differs, and the call counts side by side. Counts depend on how
long each run lasted, so compare them as orders of magnitude. Exits 1 when the two traces call no function
in common: a report with nothing compared proves nothing.
"""
import argparse
import importlib.util
import json
import pathlib
import sys

spec = importlib.util.spec_from_file_location("summarize", pathlib.Path(__file__).with_name("summarize.py"))
summarize = importlib.util.module_from_spec(spec)
spec.loader.exec_module(summarize)


def calls(path, kind, bindings):
    """(first-call order, counts) of one trace, merged over its states of this kind, by binding label."""
    states = summarize.parse(path)
    mapping = summarize.class_map(states, bindings)
    known = {k: {(b["class"], b["name"]) for b in bindings if b["list_head"] in heads}
             for k, heads in summarize.SIDE_LISTS.items()}
    first, counts = [], {}
    for state in states.values():
        if state.kind != kind:
            continue
        for name, (seq, _, _) in sorted(state.calls.items(), key=lambda item: item[1][0]):
            label = summarize.resolve(kind, name, mapping, known)[0]
            if label not in first:
                first.append(label)
        for name, count in state.counts().items():
            label = summarize.resolve(kind, name, mapping, known)[0]
            counts[label] = counts.get(label, 0) + count
    return first, counts


def shared_prefix(first_a, first_b, shared):
    """How many of the shared functions are first called in the same order."""
    a = [n for n in first_a if n in shared]
    b = [n for n in first_b if n in shared]
    same = 0
    while same < min(len(a), len(b)) and a[same] == b[same]:
        same += 1
    return same, a, b


def report(original_path, ours_path, kind, bindings):
    original_first, original = calls(original_path, kind, bindings)
    ours_first, ours = calls(ours_path, kind, bindings)
    only_original = sorted(set(original) - set(ours), key=lambda n: (-original[n], n))
    only_ours = sorted(set(ours) - set(original), key=lambda n: (-ours[n], n))
    both = set(original) & set(ours)
    if not both:
        sys.exit(f"diff.py: {original_path} and {ours_path} call no function in common ({len(original)} and {len(ours)} distinct)")
    same, common_original, common_ours = shared_prefix(original_first, ours_first, both)

    out = [f"# Lua call trace diff ({kind} side)", "",
           f"- Original: `{original_path}`, {len(original)} distinct functions called",
           f"- Ours: `{ours_path}`, {len(ours)} distinct functions called",
           f"- Called by both: {len(both)}; only by the original: {len(only_original)}; only by ours: {len(only_ours)}",
           f"- First-call order of the shared functions agrees for the first {same} of {len(both)}"]
    if same < len(both):
        out.append(f"  (original next: `{common_original[same]}`, ours next: `{common_ours[same]}`)")
    out += ["", "## Only the original called", ""]
    out += [f"- `{n}` ({original[n]})" for n in only_original] or ["- none"]
    out += ["", "## Only ours called", ""]
    out += [f"- `{n}` ({ours[n]})" for n in only_ours] or ["- none"]
    out += ["", "## Call counts of shared functions", "", "| Function | Original | Ours |", "| --- | --- | --- |"]
    for n in sorted(both, key=lambda n: (-abs(original[n] - ours[n]), n)):
        out.append(f"| `{n}` | {original[n]} | {ours[n]} |")
    return "\n".join(out) + "\n"


def self_test():
    traces = {}
    stub = lambda path, kind, bindings: traces[path]
    globals()["calls"] = stub
    traces["a"] = (["f", "g"], {"f": 2, "g": 1})
    traces["b"] = (["g"], {"g": 5})
    traces["c"] = (["h"], {"h": 1})
    traces["empty"] = ([], {})
    assert "agrees for the first 1 of 1" in report("a", "b", "user", [])
    for other in ("c", "empty"):
        try:
            report("a", other, "user", [])
        except SystemExit as stop:
            assert "no function in common" in str(stop), stop
        else:
            raise AssertionError(f"a diff with no shared calls ({other}) reported success")
    print("diff.py self-test ok")


def main():
    if sys.argv[1:] == ["--self-test"]:
        return self_test()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("original")
    parser.add_argument("ours")
    parser.add_argument("--bindings", default="work/lua-bindings.json")
    parser.add_argument("--kind", default="user", choices=sorted(summarize.SIDE_LISTS))
    parser.add_argument("-o", "--output")
    args = parser.parse_args()
    with open(args.bindings) as f:
        bindings = json.load(f)["bindings"]
    text = report(args.original, args.ours, args.kind, bindings)
    if args.output:
        with open(args.output, "w") as f:
            f.write(text)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
