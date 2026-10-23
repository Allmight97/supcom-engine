"""One adapter per probe: the shape of its lines, what its clock means, its fields with types and tolerance.

Each adapter parses the payload of one `PROBE ` line (parse), lists the rows a complete run holds (expected)
and names the one line that ends the run (marker). Nothing here is shared grammar: a line that does not have
exactly the declared words and keys is malformed.
"""
import re

from core import Float, Int, Malformed, Recorded, Row, Text, Value, tokens, typed

F, I, T = Float(), Int(), Text()
UNSET = 'not set by the probe: the map\'s own and the engine default'
TRIPLE = re.compile(r'(-?[\d.]+)/(-?[\d.]+)/(-?[\d.]+)')


def split(raw, name, parts, types, join=','):
    """Replace raw[name] by raw['name.part'] for each part, from a value like 'a,b'."""
    pieces = raw.pop(name).split(join)
    if len(pieces) != len(parts):
        raise Malformed(f'{name} should have {len(parts)} values')
    for part, piece in zip(parts, pieces):
        raw[f'{name}.{part}'] = piece


class Adapter:
    name = ''
    clock = ''
    marker = ''
    types = {}
    variable_scenes = ()
    original_args = ('/map', 'SCMP_009')
    original_timeout = 600
    osc_ticks = 400
    osc_timeout = 300
    osc_args = ()

    def type_of(self, name):
        return self.types[name]

    def expected(self):
        raise NotImplementedError

    def expected_set(self):
        return set(self.expected())

    def variable(self, identity):
        return identity[0] in self.variable_scenes

    def count_key(self, identity):
        return f'{identity[0]}/{identity[1]}' if identity[1] else identity[0]

    def extra_counts(self, parsed):
        return {}

    def check(self, parsed):
        return []

    def contract(self):
        """The experiment a run is part of: what two runs must share to count as repeats of each other."""
        return {'probe': self.name, 'clock': self.clock, 'marker': self.marker, 'map': self.original_args[-1],
                'seed': UNSET, 'factions': UNSET, 'options': UNSET, 'pathing': UNSET,
                'execution': 'the original: windowed UI game, 640x480, under CrossOver',
                'original_args': list(self.original_args), 'osc_ticks': self.osc_ticks, 'osc_args': list(self.osc_args)}


class Timing(Adapter):
    name = 'timing'
    clock = 't is the loop index of a WaitTicks(1) loop: one sim tick a step, from the order'
    marker = 'timing done'
    osc_ticks = 300
    original_timeout = 420
    common = ('state', 'progress', 'consumed', 'focus', 'focus-frac')
    types = {'state': T, 'progress': F, 'consumed': F, 'focus': T, 'focus-frac': F,
             'at.x': F, 'at.z': F}
    factory_clocks = list(range(0, 13)) + list(range(130, 161))

    def parse(self, payload, state):
        if payload == self.marker:
            return Row('done')
        parts = payload.split()
        if len(parts) < 4 or parts[0] != 'timing' or parts[1] not in ('factory', 'engineer') or not parts[2].startswith('t='):
            raise Malformed('not a timing row')
        scene = parts[1]
        keys = self.common + (('at',) if scene == 'engineer' else ())
        raw = tokens(' '.join(parts[:2] + parts[3:]), ('timing', scene), keys)
        if scene == 'engineer':
            split(raw, 'at', ('x', 'z'), self.types)
        t = Int().parse(parts[2][2:])
        phase = 'build' if scene == 'engineer' else ('start' if t <= 12 else 'finish')
        return Row(scene, phase, '', t, typed(self.types, raw))

    def expected(self):
        rows = [('factory', 'start' if t <= 12 else 'finish', '', t) for t in self.factory_clocks]
        rows += [('engineer', 'build', '', t) for t in range(41)]
        return rows + [('done', '', '', None)]


class Economy(Adapter):
    name = 'economy'
    clock = 'tick is the elapsed ticks since the scene\'s factory order (WaitTicks totals from the order)'
    marker = 'econ done'
    osc_ticks = 1300
    original_timeout = 600
    ticks = (30, 60, 100, 150, 200, 300)
    labels = ('alone', 'stalled', 'ample')
    types = {'progress': F, 'engineer-focus': T, 'factory-use': F, 'monkeylord-use': F,
             **{f'{r}.{k}': F for r in ('energy', 'mass') for k in ('stored', 'income', 'requested')}}

    def parse(self, payload, state):
        if payload == self.marker:
            return Row('done')
        parts = payload.split()
        if len(parts) < 2 or parts[0] != 'econ':
            raise Malformed('not an econ row')
        label = parts[1]
        if label in self.labels:
            raw = tokens(payload, ('econ', label), ('tick', 'progress', 'engineer-focus', 'factory-use', 'energy', 'mass'))
            clock, row = Int().parse(raw.pop('tick')), Row(label, 'sample')
        elif label == 'start' or label == 'ample-start':
            raw, clock, row = tokens(payload, ('econ', label), ('energy', 'mass')), None, Row(label)
        elif label == 'stall-start':
            raw, clock, row = tokens(payload, ('econ', label), ('monkeylord-use', 'energy', 'mass')), None, Row(label)
        else:
            raise Malformed('unknown econ row')
        for resource in ('energy', 'mass'):
            if resource in raw:
                match = TRIPLE.fullmatch(raw.pop(resource))
                if not match:
                    raise Malformed(f'{resource} should be stored/income/requested')
                for part, value in zip(('stored', 'income', 'requested'), match.groups()):
                    raw[f'{resource}.{part}'] = value
        row.clock, row.fields = clock, typed(self.types, raw)
        return row

    def expected(self):
        rows = [('start', '', '', None), ('stall-start', '', '', None), ('ample-start', '', '', None)]
        rows += [(label, 'sample', '', t) for label in self.labels for t in self.ticks]
        return rows + [('done', '', '', None)]


class Engineer(Adapter):
    name = 'engineer'
    clock = ('t is the loop index of a WaitTicks(1) loop from the build order (one sim tick a step); a callback\'s '
             'after_t is the last t logged before it. The original\'s sim has no GetGameTick and no GetAnimationFraction: '
             'it logs tick=-1 and anim=-1, so those fields are recorded, not compared')
    marker = 'eng-build done'
    osc_ticks = 200
    original_timeout = 420
    variable_scenes = ('callback',)
    step_keys = ('tick', 'state', 'progress', 'consumed', 'focus', 'heading', 'turret', 'anim')
    types = {'tick': Recorded(I), 'after_t': I, 'kind': T, 'name': T, 'state': T, 'progress': F, 'consumed': F, 'focus': T,
             'heading': F, 'turret.x': F, 'turret.z': F, 'anim': Recorded(F),
             **{f'{k}.{a}': F for k in ('at', 'turret-bone', 'frame') for a in 'xyz'}}

    def parse(self, payload, state):
        if payload == self.marker:
            return Row('done')
        if payload.startswith('eng-build engineer '):
            match = re.fullmatch(r'eng-build engineer at=([^,\s]+),([^,\s]+),([^,\s]+) turret-bone at=([^,\s]+),([^,\s]+),([^,\s]+)', payload)
            if not match:
                raise Malformed('engineer position row')
            raw = {f'{k}.{a}': v for k, group in (('at', match.groups()[:3]), ('turret-bone', match.groups()[3:]))
                   for a, v in zip('xyz', group)}
            return Row('engineer-position', fields=typed(self.types, raw))
        if payload.startswith('eng-build frame '):
            raw = tokens(payload, ('eng-build', 'frame'), ('at',))
            split(raw, 'at', 'xyz', self.types)
            return Row('frame', fields=typed(self.types, {k.replace('at.', 'frame.'): v for k, v in raw.items()}))
        if payload.startswith(('eng-build event ', 'eng-build no ')):
            parts = payload.split()
            kind = parts[1]
            if len(parts) != (4 if kind == 'event' else 3) or (kind == 'event' and not parts[3].startswith('tick=')):
                raise Malformed(f'{kind} row')
            state['calls'] = state.get('calls', 0) + 1
            fields = {'kind': kind, 'name': parts[2], 'after_t': state.get('t', -1)}
            if kind == 'event':
                fields['tick'] = I.parse(parts[3][5:])
            return Row('callback', '', f'{state["calls"]:03d}', fields=fields)
        parts = payload.split()
        if len(parts) < 2 or parts[0] != 'eng-build' or not parts[1].startswith('t='):
            raise Malformed('not an eng-build row')
        raw = tokens(' '.join(parts[:1] + parts[2:]), ('eng-build',), self.step_keys)
        split(raw, 'turret', 'xz', self.types)
        t = Int().parse(parts[1][2:])
        state['t'] = t
        return Row('step', '', '', t, typed(self.types, raw))

    def expected(self):
        return ([('engineer-position', '', '', None)] + [('step', '', '', t) for t in range(21)]
                + [('frame', '', '', None), ('done', '', '', None)])


class Crowd(Adapter):
    name = 'crowd'
    clock = 't counts the ticks since the variant\'s move order (WaitTicks(1) each, logged every 2nd); '\
            'units are listed in creation order, dead ones left out. The probe asks how many units are alive each tick '\
            'and which stopped short: those are compared; positions are recorded, not judged'
    marker = 'tr-all-done'
    osc_ticks = 2800
    original_timeout = 900
    variants = range(6)
    types = {'n': I, 'x': Recorded(F), 'z': Recorded(F), 'q': Recorded(I), 'short': I}

    def type_of(self, name):
        return self.types[name.rpartition('.')[2]] if '.' in name else self.types[name]

    def parse(self, payload, state):
        if payload == self.marker:
            return Row('all-done')
        parts = payload.split(' ', 3)
        if parts[0] == 'tr':
            if len(parts) < 3 or not parts[1].startswith('v=') or not parts[2].startswith('t='):
                raise Malformed('tr row')
            entries = [e for e in (parts[3].strip().split(';') if len(parts) > 3 else []) if e != '']
            fields = {'n': len(entries)}
            for i, entry in enumerate(entries):
                pieces = entry.split(',')
                if len(pieces) != 3:
                    raise Malformed(f'unit {i} should be x,z,q')
                for name, piece in zip('xzq', pieces):
                    fields[f'u{i}.{name}'] = self.type_of(name).parse(piece)
            return Row('v' + str(Int().parse(parts[1][2:])), 'trace', '', Int().parse(parts[2][2:]), fields)
        if parts[0] == 'tr-short':
            raw = tokens(payload, ('tr-short',), ('v', 'i', 'x', 'z', 'q'))
            return Row('v' + raw['v'], 'short', raw['i'], None, typed(self.types, {k: raw[k] for k in 'xzq'}))
        if parts[0] == 'tr-done':
            raw = tokens(payload, ('tr-done',), ('v', 'short'))
            return Row('v' + raw['v'], 'done', '', None, typed(self.types, {'short': raw['short']}))
        raise Malformed('not a crowd row')

    def variable(self, identity):
        return identity[1] == 'short'

    def expected(self):
        rows = [(f'v{v}', 'trace', '', t) for v in self.variants for t in range(2, 401, 2)]
        rows += [(f'v{v}', 'done', '', None) for v in self.variants]
        return rows + [('all-done', '', '', None)]

    def check(self, parsed):
        problems = []
        for v in self.variants:
            done = parsed.rows.get((f'v{v}', 'done', '', None))
            short = sum(1 for i in parsed.order if i[0] == f'v{v}' and i[1] == 'short')
            if done and done.fields['short'] != short:
                problems.append(f'v{v}: tr-done says {done.fields["short"]} short but {short} tr-short rows')
        return problems


class Blueprints(Adapter):
    name = 'blueprints'
    clock = 'none: every blueprint as the sim\'s scripts see it once, at the start; a row is one field of one blueprint'
    marker = 'bp done'
    osc_ticks = 10
    original_timeout = 420
    min_blueprints = 100
    types = {'value': Value()}
    infinite_fields = ('MaxHeightDiff',)
    INFINITY = re.compile(r'(?i)([+-]?)(1\.#INF|inf|infinity)')

    def parse(self, payload, state):
        if payload == self.marker:
            return Row('done')
        parts = payload.split(' ', 2)
        if len(parts) != 3 or parts[0] != 'bp' or '=' not in parts[2]:
            raise Malformed('not a bp field row')
        path, _, value = parts[2].partition('=')
        row = Row(parts[1], 'field', path, None)
        infinite = self.INFINITY.fullmatch(value)
        if infinite and path.rpartition('.')[2] in self.infinite_fields:
            row.fields = {'value': infinite.group(1).replace('+', '') + 'inf'}
        else:
            row.fields = typed(self.types, {'value': value})
        return row

    def expected(self):
        return [('done', '', '', None)]

    def variable(self, identity):
        return identity[1] == 'field'

    def count_key(self, identity):
        return 'fields' if identity[1] == 'field' else identity[0]

    def extra_counts(self, parsed):
        return {'blueprints': len({i[0] for i in parsed.order if i[1] == 'field'})}

    def check(self, parsed):
        n = self.extra_counts(parsed)['blueprints']
        return [] if n >= self.min_blueprints else [f'only {n} blueprints logged']


ADAPTERS = {a.name: a for a in (Timing(), Economy(), Engineer(), Crowd(), Blueprints())}
