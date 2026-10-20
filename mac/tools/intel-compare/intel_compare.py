#!/usr/bin/env python3
"""Compare the recon state of our sim with a capture of the original.

Usage: intel_compare.py ORIGINAL.log OURS.log [--check]
       intel_compare.py --self-test

Both logs hold tools/sim-capture INTEL lines (`INTEL tick army entity blueprint radar R sonar S omni O seen N
seenever E fake F [blip x,y,z]`; a leading "info: " is ignored). The report gives the first contact of each log and,
per logged tick, how many blips the armies hold by kind. With --check the run fails (exit 1) unless the first
contact is the same army seeing the same unit within 60 ticks, and at the last common tick the counts of blips seen
now and seen ever are each within 25% of the original's. Both modes fail when the logs share no logged tick.
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
    if sys.argv[1:] == ['--self-test']:
        return self_test()
    arguments = [a for a in sys.argv[1:] if a != '--check']
    if len(arguments) != 2:
        sys.exit(__doc__)
    (first_o, counts_o), (first_u, counts_u) = load(arguments[0]), load(arguments[1])
    common = sorted(set(counts_o) & set(counts_u))
    if not common:
        sys.exit('FAIL no logged tick is in both logs; nothing to compare')
    print('# Recon: original vs ours\n')
    print(f'- First contact: original {first_o}, ours {first_u}\n')
    print('| Tick | Blips (orig, ours) | Radar | Seen now | Seen ever |\n| --- | --- | --- | --- | --- |')
    for tick in common[::50] + common[-1:]:
        o, u = counts_o[tick], counts_u[tick]
        print(f'| {tick} | {o["blips"]}, {u["blips"]} | ' + ' | '.join(f'{o[k]}, {u[k]}' for k in KINDS) + ' |')
    if '--check' not in sys.argv:
        return
    failures = []
    if not first_o or not first_u or first_o[1:] != first_u[1:] or abs(first_o[0] - first_u[0]) > 60:
        failures.append(f'first contact {first_u} differs from the original {first_o}')
    o, u = counts_o[common[-1]], counts_u[common[-1]]
    for kind in ('seen', 'seenever'):
        if abs(u[kind] - o[kind]) > 0.25 * max(o[kind], 1):
            failures.append(f'{kind} at tick {common[-1]}: {u[kind]} against {o[kind]}')
    for failure in failures:
        print(f'FAIL {failure}', file=sys.stderr)
    sys.exit(1 if failures else 0)


I1 = "INTEL 10 1 e1 bp radar 1 sonar 0 omni 0 seen 1 seenever 1 fake 0\n"
I2 = I1.replace("INTEL 10", "INTEL 20")
I3 = I1.replace("seen 1 seenever 1", "seen 0 seenever 0")


def self_test():
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        def run(a, b, *extra):
            for name, text in (('a.log', a), ('b.log', b)):
                with open(f'{tmp}/{name}', 'w') as f:
                    f.write(text)
            return subprocess.run([sys.executable, '-I', __file__, f'{tmp}/a.log', f'{tmp}/b.log', *extra],
                                  capture_output=True, text=True)
        assert run(I1, I3, '--check').returncode == 1, 'blip counts that differ must fail --check'
        for extra in ((), ('--check',)):
            for a, b in (('', ''), (I1, I2)):
                bad = run(a, b, *extra)
                assert bad.returncode == 1 and len(bad.stderr.splitlines()) == 1, bad
            good = run(I1, I1, *extra)
            assert good.returncode == 0, good
    print('intel_compare self-test ok')


if __name__ == '__main__':
    main()
