"""The typed comparison core: parse a probe log through an adapter, validate it, compare two logs.

An adapter (adapters.py) declares, for one probe, the shape of each of its lines and gives every line a
Row: identity (scene, phase, leg, clock) plus typed fields. Everything strict lives here, once.
"""
import math
import re
import struct
from dataclasses import dataclass, field

NUMBER = re.compile(r'[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?')
NON_FINITE = re.compile(r'(?i)nan|inf|#')


class Malformed(ValueError):
    pass


class NonFinite(ValueError):
    pass


@dataclass(frozen=True)
class Float:
    def parse(self, text):
        if NON_FINITE.search(text):
            raise NonFinite(text)
        if not NUMBER.fullmatch(text):
            raise Malformed(f'{text!r} is not a number')
        value = float(text)
        if not math.isfinite(value):
            raise NonFinite(text)
        return value

    def same(self, a, b):
        return a == b


@dataclass(frozen=True)
class Int:
    def parse(self, text):
        if not re.fullmatch(r'[+-]?\d+', text):
            raise Malformed(f'{text!r} is not an integer')
        return int(text)

    def same(self, a, b):
        return a == b


@dataclass(frozen=True)
class Text:
    def parse(self, text):
        if text == '':
            raise Malformed('empty value')
        return text

    def same(self, a, b):
        return a == b


@dataclass(frozen=True)
class Value:
    """A Lua tostring value. An integer literal is exact. Any other number is a 32-bit float, compared after
    rounding both sides to float32 (the original prints one widened to 14 digits). Text is exact."""

    def parse(self, text):
        if re.fullmatch(r'(?i)[+-]?(nan|inf|infinity|1\.#\w+)(\(\w+\))?', text):
            raise NonFinite(text)
        if re.fullmatch(r'[+-]?\d+', text):
            return int(text)
        if NUMBER.fullmatch(text):
            value = float(text)
            if not math.isfinite(value):
                raise NonFinite(text)
            try:
                float32(value)
            except OverflowError:
                raise Malformed(f'{text} is beyond a 32-bit float') from None
            return value
        return text

    def same(self, a, b):
        if isinstance(a, str) or isinstance(b, str) or (isinstance(a, int) and isinstance(b, int)):
            return type(a) is type(b) and a == b
        return float32(a) == float32(b)


@dataclass(frozen=True)
class Recorded:
    """A field the log keeps but the comparison never judges (what one side cannot say, or only records)."""
    kind: object

    def parse(self, text):
        return self.kind.parse(text)

    def same(self, a, b):
        return True


def float32(value):
    return struct.unpack('f', struct.pack('f', value))[0]


@dataclass
class Row:
    scene: str
    phase: str = ''
    leg: str = ''
    clock: int | None = None
    fields: dict = field(default_factory=dict)

    @property
    def identity(self):
        return (self.scene, self.phase, self.leg, self.clock)


def describe(identity):
    scene, phase, leg, clock = identity
    parts = [f'scene={scene}']
    if phase:
        parts.append(f'phase={phase}')
    if leg:
        parts.append(f'leg={leg}')
    if clock is not None:
        parts.append(f'tick={clock}')
    return ' '.join(parts)


def tokens(payload, words, keys):
    """The key=value tokens of a line that starts with exactly `words` and carries exactly `keys`, in order."""
    parts = payload.split()
    n = len(words)
    if tuple(parts[:n]) != tuple(words):
        raise Malformed(f'expected {" ".join(words)}')
    pairs = [p.partition('=') for p in parts[n:]]
    if any(sep == '' for _, sep, _ in pairs) or tuple(k for k, _, _ in pairs) != tuple(keys):
        raise Malformed(f'expected keys {" ".join(keys)}')
    return {k: v for k, _, v in pairs}


def typed(types, raw):
    """Convert raw strings to values with types[name]; a NonFinite or Malformed value propagates."""
    return {name: types[name].parse(value) for name, value in raw.items()}


@dataclass
class Log:
    """One side's log text, its name in messages, and `errors(text)`: the log's Lua error lines."""
    name: str
    text: str
    errors: object


@dataclass
class Parsed:
    rows: dict = field(default_factory=dict)
    order: list = field(default_factory=list)
    problems: list = field(default_factory=list)


def parse_log(adapter, text):
    """Every `PROBE ` line through the adapter; malformed, non-finite and duplicate rows become problems."""
    out, state = Parsed(), {}
    for number, line in enumerate(text.splitlines(), 1):
        at = line.find('PROBE ')
        if at < 0:
            continue
        payload = line[at + 6:].strip()
        try:
            row = adapter.parse(payload, state)
        except Malformed as e:
            out.problems.append(f'line {number}: malformed ({e}): {payload[:120]}')
            continue
        except NonFinite as e:
            out.problems.append(f'line {number}: non-finite value {e}: {payload[:120]}')
            continue
        if row.identity in out.rows:
            out.problems.append(f'line {number}: duplicate row {describe(row.identity)}')
            continue
        out.rows[row.identity] = row
        out.order.append(row.identity)
    return out


def inspect(adapter, log):
    """The log parsed, with every reason it is not a complete run of the probe in .problems."""
    parsed = parse_log(adapter, log.text)
    parsed.problems += [f'Lua error: {line[:160]}' for line in log.errors(log.text)[:3]]
    expected = adapter.expected_set()
    missing = [i for i in adapter.expected() if i not in parsed.rows]
    if missing:
        parsed.problems.append(f'{len(missing)} expected rows missing, first {describe(missing[0])}')
    unexpected = [i for i in parsed.order if i not in expected and not adapter.variable(i)]
    if unexpected:
        parsed.problems.append(f'{len(unexpected)} unexpected rows, first {describe(unexpected[0])}')
    parsed.problems += adapter.check(parsed)
    return parsed


def counts(adapter, parsed):
    """Rows by scene and phase, as evidence of what a log holds."""
    out = {}
    for identity in parsed.order:
        key = adapter.count_key(identity)
        out[key] = out.get(key, 0) + 1
    return {**out, **adapter.extra_counts(parsed)}


@dataclass
class Result:
    status: str
    summary: str
    divergences: int = 0
    recorded: int = 0
    rows_compared: int = 0
    fields_compared: int = 0
    detail: list = field(default_factory=list)

    @property
    def code(self):
        return {'MATCH': 0, 'DIFFERS': 1}.get(self.status, 2)


def compare(adapter, ref, new):
    """MATCH, DIFFERS or INVALID for two Logs. Each log must be a complete run first: no comparison skips that."""
    parsed = [inspect(adapter, log) for log in (ref, new)]
    problems = [f'{log.name}: {p}' for log, one in zip((ref, new), parsed) for p in one.problems[:3]]
    if problems:
        return Result('INVALID', f'{adapter.name}: {sum(len(one.problems) for one in parsed)} problems; {problems[0]}',
                      detail=problems)
    a_log, b_log = parsed
    found, rows, fields, recorded = [], 0, 0, 0
    for identity in a_log.order:
        if identity not in b_log.rows:
            found.append((identity, '(row)', 'present', 'missing'))
            continue
        a, b = a_log.rows[identity], b_log.rows[identity]
        rows += 1
        for name in a.fields:
            if name not in b.fields:
                found.append((identity, name, a.fields[name], 'missing'))
            elif isinstance(adapter.type_of(name), Recorded):
                recorded += 1
            else:
                fields += 1
                if not adapter.type_of(name).same(a.fields[name], b.fields[name]):
                    found.append((identity, name, a.fields[name], b.fields[name]))
        found += [(identity, name, 'missing', b.fields[name]) for name in b.fields if name not in a.fields]
    found += [(identity, '(row)', 'missing', 'present') for identity in b_log.order if identity not in a_log.rows]
    if not rows or not fields:
        return Result('INVALID', f'{adapter.name}: nothing was compared ({len(a_log.rows)} {ref.name} rows, '
                      f'{len(b_log.rows)} {new.name} rows share {rows})')
    note = f'; {recorded} recorded fields not judged' if recorded else ''
    if not found:
        return Result('MATCH', f'{adapter.name}: {rows} rows, {fields} fields compared{note}', 0, recorded, rows, fields)
    identity, name, a, b = found[0]
    return Result('DIFFERS', f'{adapter.name}: first divergence {describe(identity)} field={name} '
                  f'{ref.name}={a} {new.name}={b}; {len(found)} field divergences in {len({f[0] for f in found})} rows '
                  f'({rows} rows, {fields} fields compared{note})', len(found), recorded, rows, fields,
                  [f'{describe(i)} field={n} {ref.name}={x} {new.name}={y}' for i, n, x, y in found[:20]])
