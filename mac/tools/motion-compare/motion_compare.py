#!/usr/bin/env python3
"""Compare unit motion of our sim with a capture of the original.

Usage: motion_compare.py ORIGINAL.log OURS.log [--max-drift ID=LIMIT]... > report.md

Both logs hold `MOTION tick id blueprint army x y z heading layer moving` lines (mac/tools/sim-capture for the
original, an OpenSupCom log in the same format for ours, none yet; other lines and a leading "info: " are ignored). Units are matched by
entity id and blueprint (the original reuses ids). The report gives, per blueprint, the speed, acceleration and turn rate each run shows, and per unit how
far its path drifts from the original's. AI choices make the games diverge after a while, so the per-blueprint
movement figures are the main comparison. Each --max-drift fails the run (exit 1) when the unit with that entity id
is missing from either log or its worst drift exceeds LIMIT world units.
"""
import collections
import math
import sys

TICK_SECONDS = 0.1


def load(path):
    samples = collections.defaultdict(dict)  # id -> tick -> record
    for line in open(path, errors='replace'):
        at = line.find('MOTION ')
        if at < 0:
            continue
        fields = line[at:].split()
        if len(fields) != 11:
            continue
        _, tick, entity, blueprint, army, x, y, z, heading, layer, moving = fields
        try:
            samples[f'{entity}/{blueprint}'][int(tick)] = (blueprint, int(army), float(x), float(y), float(z), float(heading), layer,
                                          moving == '1')
        except ValueError:
            continue
    return samples


def angle(delta):
    return abs((delta + math.pi) % (2 * math.pi) - math.pi)


def kinematics(samples):
    """Per blueprint: speeds (units/s) between consecutive samples, speed changes (units/s²), turn rates (rad/s)."""
    stats = collections.defaultdict(lambda: {'speed': [], 'accel': [], 'turn': []})
    for ticks in samples.values():
        ordered = sorted(ticks.items())
        previous_speed = None
        for (t0, a), (t1, b) in zip(ordered, ordered[1:]):
            seconds = (t1 - t0) * TICK_SECONDS
            if seconds <= 0:
                continue
            speed = math.hypot(b[2] - a[2], b[4] - a[4]) / seconds
            entry = stats[b[0]]
            entry['speed'].append(speed)
            if previous_speed is not None:
                entry['accel'].append((speed - previous_speed) / seconds)
            entry['turn'].append(angle(b[5] - a[5]) / seconds)
            previous_speed = speed
    return stats


def summary(values, moving_only=False):
    values = [v for v in values if not moving_only or v > 0.05]
    if not values:
        return '-'
    values.sort()
    return f'{values[len(values) // 2]:.2f} / {values[-1]:.2f}'


def main():
    arguments = sys.argv[1:]
    limits = {}
    while '--max-drift' in arguments:
        at = arguments.index('--max-drift')
        unit, _, limit = arguments[at + 1].partition('=')
        limits[unit] = float(limit)
        del arguments[at:at + 2]
    if len(arguments) != 2:
        sys.exit(__doc__)
    original, ours = load(arguments[0]), load(arguments[1])  # keyed by id/blueprint: the original reuses ids
    print('# Unit motion: original vs ours\n')
    shared = sorted(set(original) & set(ours), key=lambda e: (int(e.split('/')[0]), e))
    print(f'- Units: original {len(original)}, ours {len(ours)}, same id in both {len(shared)}')
    ticks_o = {t for ticks in original.values() for t in ticks}
    ticks_u = {t for ticks in ours.values() for t in ticks}
    if ticks_o and ticks_u:
        print(f'- Ticks: original {min(ticks_o)}-{max(ticks_o)}, ours {min(ticks_u)}-{max(ticks_u)}, '
              f'common {len(ticks_o & ticks_u)}')
    print()

    print('## Movement by blueprint\n')
    print('Median / maximum over 5-tick samples. Speed counts moving samples only (above 0.05 units/s).\n')
    print('| Blueprint | Samples (orig, ours) | Speed orig | Speed ours | Accel orig | Accel ours | Turn orig | Turn ours |')
    print('| --- | --- | --- | --- | --- | --- | --- | --- |')
    stats_o, stats_u = kinematics(original), kinematics(ours)
    for blueprint in sorted(set(stats_o) | set(stats_u)):
        o, u = stats_o.get(blueprint), stats_u.get(blueprint)
        if not (o and any(v > 0.05 for v in o['speed'])) and not (u and any(v > 0.05 for v in u['speed'])):
            continue
        empty = {'speed': [], 'accel': [], 'turn': []}
        o, u = o or empty, u or empty
        print(f'| `{blueprint}` | {len(o["speed"])}, {len(u["speed"])} '
              f'| {summary(o["speed"], True)} | {summary(u["speed"], True)} '
              f'| {summary([abs(v) for v in o["accel"]], True)} | {summary([abs(v) for v in u["accel"]], True)} '
              f'| {summary(o["turn"], True)} | {summary(u["turn"], True)} |')
    print()

    print('## Drift of matched units\n')
    print('Distance between the two runs\' positions of the same unit; "first > 1" is the first common tick where it '
          'exceeds 1 world unit.\n')
    print('| Unit | Blueprint | Common samples | First > 1 | Worst | Distance at end |\n| --- | --- | --- | --- | --- | --- |')
    worst_by_id = {}
    for entity in shared:
        common = sorted(set(original[entity]) & set(ours[entity]))
        if not common:
            continue
        first = next((t for t in common
                      if math.hypot(original[entity][t][2] - ours[entity][t][2],
                                    original[entity][t][4] - ours[entity][t][4]) > 1), None)
        last = common[-1]
        end = math.hypot(original[entity][last][2] - ours[entity][last][2],
                         original[entity][last][4] - ours[entity][last][4])
        worst = max(math.hypot(original[entity][t][2] - ours[entity][t][2],
                               original[entity][t][4] - ours[entity][t][4]) for t in common)
        worst_by_id[entity.split('/')[0]] = worst
        print(f'| {entity.split("/")[0]} | `{original[entity][common[0]][0]}` | {len(common)} | {first if first is not None else "-"} '
              f'| {worst:.1f} | {end:.1f} |')

    failed = [f'unit {unit}: ' + ('missing' if unit not in worst_by_id else f'worst drift {worst_by_id[unit]:.2f} > {limit}')
              for unit, limit in limits.items() if worst_by_id.get(unit, math.inf) > limit]
    for line in failed:
        print(f'FAIL {line}', file=sys.stderr)
    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
