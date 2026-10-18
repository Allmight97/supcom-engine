#!/usr/bin/env python3
"""Compare the recon state of our sim with a capture of the original.

Usage: intel_compare.py ORIGINAL.log OURS.log [--check]

Both logs hold tools/sim-capture INTEL lines (`INTEL tick army entity blueprint radar R sonar S omni O seen N
seenever E fake F [blip x,y,z]`; a leading "info: " is ignored). The report gives the first contact of each log and,
per logged tick, how many blips the armies hold by kind. With --check the run fails (exit 1) unless the first
contact is the same army seeing the same unit within 60 ticks, and at the last common tick the counts of blips seen
now and seen ever are each within 25% of the original's.
"""
import collections
import sys

KINDS = ('radar', 'seen', 'seenever')


def load(path):
    first, counts = None, collections.defaultdict(collections.Counter)
    for line in open(path, errors='replace'):
        at = line.find('INTEL ')
        if at < 0:
            continue
        fields = line[at:].split()
        tick, army, entity = int(fields[1]), fields[2], fields[3]
        flags = {fields[i]: fields[i + 1] == '1' for i in range(5, 17, 2)}
        if first is None:
            first = (tick, army, entity, fields[4])
        for kind in KINDS:
            counts[tick][kind] += flags[kind]
        counts[tick]['blips'] += 1
    return first, counts


def main():
    arguments = [a for a in sys.argv[1:] if a != '--check']
    if len(arguments) != 2:
        sys.exit(__doc__)
    (first_o, counts_o), (first_u, counts_u) = load(arguments[0]), load(arguments[1])
    print('# Recon: original vs ours\n')
    print(f'- First contact: original {first_o}, ours {first_u}\n')
    print('| Tick | Blips (orig, ours) | Radar | Seen now | Seen ever |\n| --- | --- | --- | --- | --- |')
    common = sorted(set(counts_o) & set(counts_u))
    for tick in common[::50] + common[-1:]:
        o, u = counts_o[tick], counts_u[tick]
        print(f'| {tick} | {o["blips"]}, {u["blips"]} | ' + ' | '.join(f'{o[k]}, {u[k]}' for k in KINDS) + ' |')
    if '--check' not in sys.argv:
        return
    failures = []
    if not first_o or not first_u or first_o[1:] != first_u[1:] or abs(first_o[0] - first_u[0]) > 60:
        failures.append(f'first contact {first_u} differs from the original {first_o}')
    if common:
        o, u = counts_o[common[-1]], counts_u[common[-1]]
        for kind in ('seen', 'seenever'):
            if abs(u[kind] - o[kind]) > 0.25 * max(o[kind], 1):
                failures.append(f'{kind} at tick {common[-1]}: {u[kind]} against {o[kind]}')
    for failure in failures:
        print(f'FAIL {failure}', file=sys.stderr)
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    main()
