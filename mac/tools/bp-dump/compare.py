#!/usr/bin/env python3
"""Compare two blueprint dumps (tools/bp-dump): the original's and our engine's.

Usage: compare.py ORIGINAL.log OURS.log
       compare.py --self-test

Reports blueprints only one side has, and per field path (list indices shown as [*]) how often the original has
a value we lack ("added"), we have a value the original lacks ("removed"), or the values differ ("changed"), with
the most common original values. Fails when the dumps share no blueprint. The original merges its C++ blueprint defaults into every spec, so "added"
fields with one constant value are those defaults.
"""
import argparse
import collections
import re
import sys


def entries(path):
    out = {}
    for line in open(path, encoding='latin-1'):
        at = line.find('BPDUMP|')
        if at < 0:
            continue
        _, key, value = line[at:].rstrip('\r\n').split('|', 2)
        if key != 'END':
            out[key] = value
    return out


class Parser:
    def __init__(self, text):
        self.text, self.at = text, 0

    def value(self):
        c = self.text[self.at]
        if c == '{':
            return self.table()
        if c == '"':
            return self.string()
        if c == '<':
            end = self.text.index('>', self.at)
            token = self.text[self.at:end + 1]
            self.at = end + 1
            return token
        m = re.compile(r'true|false|-?1\.#INF|-?1\.#IND|[-+0-9.eEinfa]+').match(self.text, self.at)
        self.at = m.end()
        token = m.group(0)
        if token in ('true', 'false'):
            return token == 'true'
        if '#' in token:
            return float('-inf') if token.startswith('-') else float('inf')
        return float(token)

    def string(self):
        self.at += 1
        out = []
        while True:
            c = self.text[self.at]
            if c == '"':
                self.at += 1
                return ''.join(out)
            if c == '\\':
                self.at += 1
                c = self.text[self.at]
                if c.isdigit():
                    m = re.compile(r'\d{1,3}').match(self.text, self.at)
                    out.append(chr(int(m.group(0))))
                    self.at = m.end()
                    continue
                out.append({'n': '\n', 'r': '\r', 't': '\t'}.get(c, c))
                self.at += 1
                continue
            out.append(c)
            self.at += 1

    def table(self):
        self.at += 1
        out = {}
        while self.text[self.at] != '}':
            if self.text[self.at] == '[':
                self.at += 1
                key = self.value()
                self.at += 1  # ]
            else:
                m = re.compile(r'[^=]+').match(self.text, self.at)
                key = m.group(0)
                self.at = m.end()
            self.at += 1  # =
            out[key] = self.value()
            if self.text[self.at] == ',':
                self.at += 1
        self.at += 1
        return out


def parse(text):
    return Parser(text).value()


def flatten(value, prefix, out):
    if isinstance(value, dict):
        for key, item in value.items():
            part = '[*]' if isinstance(key, float) else key
            flatten(item, f'{prefix}.{part}' if prefix else part, out)
    else:
        out.append((prefix, value))


def kind(key):
    if key.endswith('_mesh') or key.endswith('_wreck') or key.endswith('_build'):
        return 'Mesh'
    if '/' not in key:
        return 'Unit'
    if key.endswith('_prop.bp'):
        return 'Prop'
    if key.endswith('_proj.bp'):
        return 'Projectile'
    return 'Other'


def main():
    if sys.argv[1:] == ['--self-test']:
        return self_test()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('original')
    parser.add_argument('ours')
    args = parser.parse_args()
    original, ours = entries(args.original), entries(args.ours)
    only_original = sorted(set(original) - set(ours))
    only_ours = sorted(set(ours) - set(original))
    if not set(original) & set(ours):
        sys.exit('FAIL no blueprint is in both dumps; nothing to compare')
    print(f'# Blueprint dump comparison\n\n- Original: {len(original)} blueprints; ours: {len(ours)}')
    print(f'- Only the original: {len(only_original)} {only_original[:10]}')
    by_kind = collections.Counter(kind(k) for k in only_ours)
    print(f'- Only ours: {len(only_ours)} by kind {dict(by_kind)} {only_ours[:5]}\n')

    stats = collections.defaultdict(lambda: {'added': collections.Counter(), 'removed': 0, 'changed': collections.Counter(), 'kinds': set()})
    for key in sorted(set(original) & set(ours)):
        a, b = parse(original[key]), parse(ours[key])
        fa, fb = [], []
        flatten(a, '', fa)
        flatten(b, '', fb)
        da = collections.defaultdict(list)
        db = collections.defaultdict(list)
        for p, v in fa:
            da[p].append(v)
        for p, v in fb:
            db[p].append(v)
        for p in set(da) | set(db):
            entry = stats[p]
            entry['kinds'].add(kind(key))
            if p not in db:
                entry['added'][repr(da[p][0])] += 1
            elif p not in da:
                entry['removed'] += 1
            elif sorted(map(repr, da[p])) != sorted(map(repr, db[p])):
                entry['changed'][f'{da[p][0]!r} vs {db[p][0]!r}'] += 1

    print('## Fields the original has and we lack\n')
    print('| Path | Kinds | Blueprints | Original values |\n| --- | --- | --- | --- |')
    for p in sorted(stats):
        e = stats[p]
        if e['added']:
            total = sum(e['added'].values())
            values = ', '.join(f'{v} ×{n}' for v, n in e['added'].most_common(3))
            print(f'| `{p}` | {",".join(sorted(e["kinds"]))} | {total} | {values} |')
    print('\n## Fields we have and the original lacks\n')
    for p in sorted(stats):
        if stats[p]['removed']:
            print(f'- `{p}`: {stats[p]["removed"]}')
    print('\n## Values that differ\n')
    for p in sorted(stats):
        e = stats[p]
        if e['changed']:
            total = sum(e['changed'].values())
            print(f'- `{p}`: {total}, e.g. {e["changed"].most_common(2)}')


B1 = "BPDUMP|uel0001|{a=1}\n"
B2 = "BPDUMP|uel0002|{a=1}\n"
B3 = B1.replace("a=1", "a=2")


def self_test():
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        def run(a, b):
            for name, text in (('a.log', a), ('b.log', b)):
                with open(f'{tmp}/{name}', 'w') as f:
                    f.write(text)
            return subprocess.run([sys.executable, '-I', __file__, f'{tmp}/a.log', f'{tmp}/b.log'],
                                  capture_output=True, text=True)
        empty = run('', '')
        assert empty.returncode == 1 and len(empty.stderr.splitlines()) == 1, empty
        disjoint = run(B1, B2)
        assert disjoint.returncode == 1 and len(disjoint.stderr.splitlines()) == 1, disjoint
        same = run(B1, B1)
        assert same.returncode == 0, same
        changed = run(B1, B3)
        assert changed.returncode == 0 and '`a`: 1' in changed.stdout, changed
    print('compare.py self-test ok')


if __name__ == '__main__':
    sys.exit(main())
