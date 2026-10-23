"""pulse --self-test: fixture facts and a fake command runner, no network and no repository."""
import copy
import json
import re
import sys

import gather
import judge
import views
import webview

ROOT = '/repo'
NOW = '2026-10-23T12:00:00+00:00'
KEYS = {'schema', 'checked_at', 'fork', 'prs', 'overlap', 'landed', 'branches', 'worktrees', 'parity', 'needs_you',
        'errors'}
GOOD = {'passed': 3, 'failed': [], 'running': 0}


def pr(number, head, **kw):
    return {'number': number, 'title': f'title {number}', 'url': judge.pr_url(number), 'head': head, 'draft': False,
            'review': 'REVIEW_REQUIRED', 'merge': 'BLOCKED', 'checks': GOOD, 'updated_at': NOW, 'builds_on': None,
            'files': [], **kw}


def other(number, files, author='zoo'):
    return {'number': number, 'author': author, 'title': f'other {number}', 'url': judge.pr_url(number), 'draft': False,
            'files': files}


def branch(name, ahead=0, ahead_up=0, unpushed=0, pushed=False, own=None, inside=(), files=()):
    return {'name': name, 'sha': name[:8], 'ts': 1_760_000_000, 'ahead': ahead, 'behind': 0, 'ahead_up': ahead_up,
            'unpushed': unpushed, 'pushed': pushed, 'contained_in': list(inside), 'own_commits': own, 'files': list(files)}


def closed(number, head, closed_at, merged=False):
    return {'number': number, 'title': f'old {number}', 'url': judge.pr_url(number), 'head': head, 'closed_at': closed_at,
            'merged': merged}


def raw_fixture():
    return {
        'now': NOW, 'errors': [], 'parity': {'probes': [{'name': 'crowd', 'runs': 3, 'baseline': 'r1', 'gated': True},
                                                         {'name': 'economy', 'runs': 2, 'baseline': None, 'gated': False}],
                                             'damaged': []},
        'fork': {'main': 'a' * 40, 'upstream': 'b' * 40, 'behind': 3, 'ahead_of_upstream': 10, 'unpushed': 1},
        'open': [pr(10, 'up/open', checks={'passed': 1, 'failed': ['linux-gcc'], 'running': 1}, files=['src/sim/a.cpp', 'docs/x.md']),
                 pr(11, 'up/stack', draft=True, merge='DIRTY', review='CHANGES_REQUESTED', builds_on=10, files=['src/sim/b.cpp'])],
        'others': [other(10, ['src/sim/a.cpp'], 'me'), other(50, ['src/sim/a.cpp']), other(51, ['docs/x.md']),
                   other(52, ['src/other.cpp']), other(53, ['src/sim/b.cpp', 'src/zzz.cpp'])],
        'matters': [{'number': 52, 'author': 'zoo', 'title': 'other 52', 'mac': True, 'overlap': [], 'draft': False},
                    {'number': 10, 'author': 'me', 'title': 'title 10', 'mac': False, 'overlap': ['src/sim/a.cpp'], 'draft': False}],
        'closed': [closed(5, 'up/landed', '2026-10-20T00:00:00Z'), closed(6, 'up/dropped', '2026-10-21T00:00:00Z'),
                   closed(7, 'mac/merged', '2026-10-22T00:00:00Z', True), closed(4, 'up/ancient', '2026-09-01T00:00:00Z')],
        'landings': {5: 'abc1234 2026-10-20'},
        'branches': [branch('up/open', ahead_up=3, unpushed=2, pushed=True, files=['src/sim/a.cpp']),
                     branch('up/stack', ahead=1, ahead_up=4, pushed=True),
                     branch('up/landed', ahead=2, ahead_up=2, pushed=True), branch('up/dropped', ahead=2, ahead_up=2, pushed=True),
                     branch('up/nopr', ahead=3, ahead_up=2, pushed=True, files=['src/nopr.cpp']),
                     branch('up/atup'), branch('mac/merged'), branch('mac/work', ahead=2, unpushed=2),
                     branch('scratch/merges', ahead=3, own=0), branch('scratch/inside', ahead=2, own=0, inside=['scratch/merges']),
                     branch('scratch/own', ahead=2, own=2), branch('claude/held'), branch('claude/sess'), branch('claude/free')],
        'worktrees': [{'path': ROOT, 'head': 'a' * 8, 'branch': 'main', 'changes': 0, 'ts': 1_760_000_000, 'primary': True},
                      {'path': '/w/held', 'head': 'c' * 8, 'branch': 'claude/held', 'changes': 3, 'ts': 1_760_000_000, 'primary': False},
                      {'path': '/w/sess', 'head': 'd' * 8, 'branch': 'mac/work', 'changes': 0, 'ts': 1_760_000_000, 'primary': False}]}


def by(items, key, value):
    return next(i for i in items if i[key] == value)


def test_checks():
    run = {'__typename': 'CheckRun', 'status': 'COMPLETED', 'conclusion': 'SUCCESS', 'name': 'a', 'startedAt': '1'}
    assert gather.checks_summary([]) == {'passed': 0, 'failed': [], 'running': 0}
    mixed = [run, {**run, 'name': 'b', 'conclusion': 'FAILURE'}, {**run, 'name': 'c', 'status': 'IN_PROGRESS', 'conclusion': ''},
             {'__typename': 'StatusContext', 'context': 'ctx', 'state': 'PENDING'}]
    assert gather.checks_summary(mixed) == {'passed': 1, 'failed': ['b'], 'running': 2}
    rerun = [{**run, 'conclusion': 'FAILURE', 'startedAt': '1'}, {**run, 'startedAt': '2'}]
    assert gather.checks_summary(rerun)['failed'] == [], 'a rerun replaces the earlier run of the same check'


def test_parsers():
    found = gather.parse_worktrees('worktree /a\nHEAD abcdef0123\nbranch refs/heads/main\n\nworktree /b\nHEAD 1234567890\ndetached\n')
    assert [(w['path'], w['branch']) for w in found] == [('/a', 'main'), ('/b', None)]
    parity = gather.parse_parity('crowd: runs 3, baseline r1, gated\nx: runs 0, baseline none, not gated\nx: DAMAGED run r: bad\n')
    assert [p['gated'] for p in parity['probes']] == [True, False] and parity['probes'][1]['baseline'] is None
    assert parity['damaged'] == ['x: DAMAGED run r: bad']


def test_branches(snap):
    verdict = {b['name']: (b['deletable'], b['reason']) for b in snap['branches']}
    for name in ('up/landed', 'up/dropped', 'up/atup', 'mac/merged', 'scratch/merges', 'scratch/inside', 'claude/free'):
        assert verdict[name][0], f'{name} is done: {verdict[name]}'
    for name in ('up/open', 'up/stack', 'up/nopr', 'mac/work', 'scratch/own', 'claude/held', 'claude/sess'):
        assert not verdict[name][0], f'{name} holds work: {verdict[name]}'
    assert 'open PR #10' in verdict['up/open'][1], 'an open PR blocks deletion even at 0 commits ahead of main'
    assert 'commits not in main' in verdict['up/dropped'][1] and 'landed' in verdict['up/landed'][1]
    held = by(snap['branches'], 'name', 'claude/held')
    assert held['worktree'] == '/w/held' and 'worktree held' in held['reason'], 'a merged branch checked out in a worktree is never deletable'


def test_overlap(snap):
    numbers = [o['number'] for o in snap['overlap']]
    assert 10 not in numbers and 11 not in numbers, 'our own PRs are not overlap'
    assert 51 not in numbers, 'a shared docs file is not an overlap'
    assert by(snap['overlap'], 'number', 50)['with'] == ['#10']
    assert by(snap['overlap'], 'number', 53)['with'] == ['#11'] and by(snap['overlap'], 'number', 53)['files'] == ['src/sim/b.cpp']
    news_only = by(snap['overlap'], 'number', 52)
    assert news_only['with'] == [] and news_only['tags'] == ['MAC']
    assert numbers == [53, 50, 52], 'overlap with our work first, newest first'


def test_needs_you(snap):
    codes = [i['code'] for i in snap['needs_you']]
    for wanted in ('checks-failed', 'changes-requested', 'merge-conflict', 'draft', 'unpushed', 'sync-due', 'pushed-no-pr',
                   'delete-branches', 'overlap'):
        assert wanted in codes, f'missing {wanted}: {codes}'
    assert codes.index('checks-failed') < codes.index('sync-due') < codes.index('delete-branches') < codes.index('overlap')
    assert 'linux-gcc' in by(snap['needs_you'], 'code', 'checks-failed')['text']
    delete = by(snap['needs_you'], 'code', 'delete-branches')
    assert 'up/landed' in delete['text'] and 'claude/free' in delete['text'] and 'claude/held' not in delete['text'] and 'claude/sess' not in delete['text'] and 'git branch -D' in delete['why']
    assert all(set(i) == {'code', 'text', 'why', 'link'} for i in snap['needs_you'])
    quiet = copy.deepcopy(raw_fixture())
    quiet.update(open=[pr(10, 'up/open')], fork={**quiet['fork'], 'behind': 0}, branches=[], others=[], matters=[], worktrees=[])
    assert judge.assemble(quiet)['needs_you'] == []


def test_landed(snap):
    assert [(p['number'], p['state']) for p in snap['landed']] == [(7, 'merged'), (6, 'closed'), (5, 'landed')]


def many_branches(snap, count=30):
    wide = copy.deepcopy(snap)
    wide['branches'] = [{**snap['branches'][0], 'name': f'scratch/s{i}', 'noteworthy': True} for i in range(count)]
    wide['needs_you'] = snap['needs_you'] * 3
    wide['worktrees'] = snap['worktrees'] * 5
    return wide


def test_text(snap):
    out = views.text(snap)
    titles = [line[:1] for line in out.splitlines() if re.match(r'^[NUOLFPBW]  [A-Z]', line)]
    assert ''.join(titles) == 'NUOLFPBW', titles
    assert out.index('NEEDS YOU') < out.index('OUR UPSTREAM PRS') and 'http' not in out
    wide = views.text(many_branches(snap))
    assert len(wide.splitlines()) <= views.CAP and 'more: pulse --detail' in wide
    assert all(f'{c}  ' in wide for c in 'NUOLFPBW'), 'every section keeps a title and a line under the cap'
    long = views.text(many_branches(snap), detail=True)
    assert len(long.splitlines()) > views.CAP and 'http' in long and 'more:' not in long
    test_brief(snap)


def test_brief(snap):
    short = views.brief(snap).splitlines()
    assert short[0].startswith('pulse  checked') and short[1].startswith('N  NEEDS YOU') and 'OUR UPSTREAM' not in '\n'.join(short)
    failed = {**snap, 'errors': [{'source': 'gh', 'message': 'no network'}], 'fork': {}}
    assert views.brief(failed).count('\n') == 0 and 'pulse: gh failed (no network)' in views.brief(failed)
    assert 'pulse: gh failed' in views.text(failed)


def test_json(snap):
    loaded = json.loads(views.as_json(snap))
    assert set(loaded) == KEYS and loaded['schema'] == 1
    assert set(loaded['fork']) == {'main', 'upstream', 'behind', 'ahead_of_upstream', 'unpushed'}
    assert set(loaded['prs'][0]) >= {'number', 'title', 'url', 'head', 'checks', 'review', 'merge', 'builds_on'}
    assert set(loaded['prs'][0]['checks']) == {'passed', 'failed', 'running'}
    assert set(loaded['overlap'][0]) >= {'number', 'author', 'title', 'url', 'files', 'with'}
    assert set(loaded['branches'][0]) >= {'name', 'kind', 'last_commit_at', 'ahead', 'behind', 'pushed', 'pr', 'deletable', 'reason'}
    assert set(loaded['worktrees'][0]) >= {'path', 'branch', 'head', 'dirty', 'last_commit_at', 'pr'}


def test_html(snap):
    page = webview.page(snap)
    for code in 'NUOLFPBW':
        assert f'id="{code}"' in page, f'section {code} missing'
    assert 'Since your last look' not in page, 'no cache, no since section'
    assert page.index('id="N"') < page.index('id="U"') and 'prefers-color-scheme: dark' in page
    assert 'needs you' in page and 'failed' in page and 'awaiting review' in page and 'merge conflict' in page
    assert '<script src' not in page and 'http-equiv="refresh"' not in page
    test_since_page(snap)
    hostile = {**snap, 'prs': [{**snap['prs'][0], 'title': '<script>alert(1)</script>'}]}
    assert '<script>alert' not in webview.page(hostile)


def test_since_page(snap):
    before = copy.deepcopy(snap)
    after = copy.deepcopy(snap)
    after['prs'][0]['checks'] = GOOD
    after['prs'] = after['prs'][:1] + [{**after['prs'][0], 'number': 12, 'title': 'brand new'}]
    after['branches'] = after['branches'][1:] + [{**after['branches'][0], 'name': 'up/fresh'}]
    after['overlap'] = after['overlap'][1:]
    again = webview.page(after, before)
    assert 'Since your last look' in again and 'new PR #12: brand new' in again and '#10 checks: 1 passed, 1 failed (linux-gcc), 1 running -&gt; 3 passed' in again
    assert '#11 is no longer open' in again and 'branch added: up/fresh' in again and 'overlap gone: #53' in again


class Repo:
    """A fake runner for a repository with main, up/x and scratch/s."""

    def __init__(self, fail_gh=False):
        self.fail_gh, self.seen = fail_gh, []
        sha = 'f' * 40
        self.answers = [
            ('fetch -q', ''), ('for-each-ref --format', f'main\t{sha}\t1760000000\nup/x\t{sha[:-1]}0\t1760000100\nscratch/s\t{sha[:-1]}1\t1760000200\n'),
            ('rev-parse --verify --quiet main', sha), ('rev-parse --verify --quiet upstream/main', sha[:-1] + '2'),
            ('rev-parse --verify --quiet refs/remotes/origin/up/x', None), ('rev-parse --verify --quiet refs/remotes/origin/scratch/s', None),
            ('rev-list --count upstream/main..main', '5'), ('rev-list --count origin/main..main', '1'),
            ('rev-list --left-right --count main...up/x', '0\t2'), ('rev-list --left-right --count main...scratch/s', '0\t1'),
            ('rev-list --count upstream/main..up/x', '2'), ('rev-list --count upstream/main..scratch/s', '1'),
            ('rev-list --count up/x --not', '2'), ('rev-list --count scratch/s --not', '1'),
            ('rev-list --count --no-merges scratch/s --not main upstream/main', '0'),
            ('for-each-ref --contains scratch/s', 'scratch/s\nup/x\n'), ('diff --name-only upstream/main...up/x', 'src/a.cpp\n'),
            ('worktree list --porcelain', f'worktree {ROOT}\nHEAD {sha}\nbranch refs/heads/main\n\n'
                                          f'worktree /w/x\nHEAD {sha}\nbranch refs/heads/up/x\n'),
            ('status --porcelain', ' M a.cpp\n'), ('log -1 --format=%ct', '1760000100')]

    def __call__(self, args, timeout=30):
        text = ' '.join(args[3:] if args[:2] == ['git', '-C'] else args)
        self.seen.append(text)
        if args[0] == 'gh':
            return self.github(text)
        if args[0] == sys.executable:
            return gather.Result(0, 'crowd: runs 3, baseline r1, gated\n', '')
        for prefix, out in self.answers:
            if text.startswith(prefix):
                return gather.Result(0 if out is not None else 1, out or '', '')
        raise AssertionError(f'unexpected command: {text}')

    def github(self, text):
        if self.fail_gh:
            return gather.Result(1, '', 'gh: not logged in\nmore')
        file = {'path': 'src/a.cpp'}
        if '--author @me --state open' in text:
            return gather.Result(0, json.dumps([{'number': 20, 'title': 'mine', 'url': judge.pr_url(20), 'headRefName': 'up/x',
                                                 'isDraft': False, 'reviewDecision': '', 'mergeStateStatus': 'BLOCKED',
                                                 'statusCheckRollup': [], 'body': 'Builds on #19 (lands after it)',
                                                 'files': [file], 'updatedAt': NOW}]), '')
        if '--author @me --state all' in text:
            return gather.Result(0, json.dumps([{'number': 20, 'title': 'mine', 'url': '', 'headRefName': 'up/x', 'state': 'OPEN',
                                                 'closedAt': '', 'mergedAt': None},
                                                {'number': 19, 'title': 'old', 'url': judge.pr_url(19), 'headRefName': 'up/old',
                                                 'state': 'CLOSED', 'closedAt': '2026-10-22T00:00:00Z', 'mergedAt': None}]), '')
        return gather.Result(0, json.dumps([{'number': 30, 'title': 'theirs', 'url': judge.pr_url(30), 'isDraft': False,
                                             'author': {'login': 'zoo'}, 'files': [file]}]), '')


class News:
    class Fail(Exception):
        pass

    def behind(self):
        return 4

    def open_prs(self):
        return [{'number': 30, 'author': {'login': 'zoo'}, 'title': 'theirs', 'mac': False, 'overlap': ['src/a.cpp'], 'isDraft': False}]

    def landings(self):
        return {19: 'abc1234 2026-10-22'}


def test_gather():
    run = Repo()
    snap = judge.assemble(gather.gather(run, ROOT, News(), fetch=True, now=NOW))
    assert set(snap) == KEYS and snap['errors'] == [], snap['errors']
    assert snap['fork'] == {'main': 'f' * 40, 'upstream': 'f' * 39 + '2', 'behind': 4, 'ahead_of_upstream': 5, 'unpushed': 1}
    assert snap['prs'][0]['builds_on'] == 19 and snap['prs'][0]['unpushed'] == 2
    assert [o['number'] for o in snap['overlap']] == [30] and snap['overlap'][0]['with'] == ['#20']
    assert snap['landed'][0]['state'] == 'landed' and snap['landed'][0]['landing'] == 'abc1234 2026-10-22'
    x, s = by(snap['branches'], 'name', 'up/x'), by(snap['branches'], 'name', 'scratch/s')
    assert x['pr']['state'] == 'open' and not x['pushed'] and x['worktree'] == '/w/x' and not x['deletable']
    assert s['deletable'] and 'up/x' in s['reason']
    assert snap['worktrees'][1]['dirty'] and snap['worktrees'][0]['primary'] and snap['parity']['probes'][0]['gated']
    assert any(c.startswith('fetch -q upstream') for c in run.seen) and any(c.startswith('fetch -q origin') for c in run.seen)
    test_gather_options()


def test_brief_gather():
    quick = Repo()
    raw = gather.gather(quick, ROOT, News(), fetch=False, full=False, now=NOW)
    assert [w['branch'] for w in raw['worktrees']] == ['main', 'up/x'], 'the brief still knows which branches worktrees hold'
    assert not any(c.startswith('status') for c in quick.seen) and raw['parity'] is None


def test_gather_options():
    quick = Repo()
    gather.gather(quick, ROOT, News(), fetch=False, now=NOW)
    assert not any(c.startswith('fetch') for c in quick.seen), '--no-fetch must not fetch'
    class NoGh(News):
        def open_prs(self):
            raise FileNotFoundError(2, 'No such file', 'gh')

    missing = judge.assemble(gather.gather(Repo(), ROOT, NoGh(), fetch=False, now=NOW))
    assert missing['errors'] == [{'source': 'gh', 'message': 'gh not found'}] and missing['fork']['main']
    assert 'pushed-no-pr' not in [i['code'] for i in missing['needs_you']], 'without PR facts no branch is called unpublished'
    broken = judge.assemble(gather.gather(Repo(fail_gh=True), ROOT, News(), fetch=False, now=NOW))
    assert broken['errors'] and broken['errors'][0]['source'] == 'gh' and broken['prs'] == []


def run():
    snap = judge.assemble(raw_fixture())
    test_checks()
    test_parsers()
    test_branches(snap)
    test_overlap(snap)
    test_needs_you(snap)
    test_landed(snap)
    test_text(snap)
    test_json(snap)
    test_html(snap)
    test_gather()
    test_brief_gather()
    print('pulse self-test passed')
    return 0
