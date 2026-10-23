"""One pass over the live state: git refs and worktrees, GitHub through gh, upstream-news and the parity store.
Every command goes through the runner given to gather(), so the self-test feeds fixtures. A failed command is
recorded in errors and its facts stay empty; nothing here prints."""
import concurrent.futures as futures
import importlib.machinery
import importlib.util
import json
import os
import re
import subprocess
import sys
from collections import namedtuple
from datetime import datetime

import judge

Result = namedtuple('Result', 'rc out err')
REMOTES = ('upstream', 'origin')
OPEN_FIELDS = ('number,title,url,headRefName,isDraft,reviewDecision,mergeStateStatus,statusCheckRollup,body,'
               'files,updatedAt')
ALL_OPEN_FIELDS = 'number,title,author,files,url,isDraft'
OUR_FIELDS = 'number,title,url,headRefName,state,closedAt,mergedAt'
BUILDS_ON = re.compile(r'(?:builds|stacked|based|depends) on #(\d+)', re.I)
PASSED = {'SUCCESS', 'NEUTRAL', 'SKIPPED'}
PARITY_LINE = re.compile(r'^(\S+): runs (\d+), baseline (\S+), (gated|not gated)$')
DAMAGED_LINE = re.compile(r'^(\S+): DAMAGED (.*)$')


def system(args, timeout=30):
    try:
        done = subprocess.run(args, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
    except FileNotFoundError:
        return Result(127, '', f'{args[0]} not found')
    except subprocess.TimeoutExpired:
        return Result(124, '', f'{args[0]} timed out after {timeout} s')
    return Result(done.returncode, done.stdout, done.stderr.strip())


def load_news(root):
    path = os.path.join(root, 'mac/scripts/upstream-news')
    loader = importlib.machinery.SourceFileLoader('upstream_news', path)
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader('upstream_news', loader))
    loader.exec_module(module)
    return module


def check_outcome(entry):
    """(name, passed|failed|running) for one statusCheckRollup entry, a CheckRun or a StatusContext."""
    if entry.get('__typename') == 'StatusContext':
        state = entry.get('state', '')
        return entry.get('context', ''), 'passed' if state == 'SUCCESS' else 'running' if state in ('PENDING', 'EXPECTED', '') else 'failed'
    if entry.get('status') != 'COMPLETED':
        return entry.get('name', ''), 'running'
    return entry.get('name', ''), 'passed' if entry.get('conclusion') in PASSED else 'failed'


def latest_checks(rollup):
    latest = {}
    for entry in rollup or []:
        key = (entry.get('workflowName', ''), entry.get('name') or entry.get('context', ''))
        if key not in latest or (entry.get('startedAt') or '') >= (latest[key].get('startedAt') or ''):
            latest[key] = entry
    return latest.values()


def checks_summary(rollup):
    outcomes = [check_outcome(e) for e in latest_checks(rollup)]
    return {'passed': sum(o == 'passed' for _, o in outcomes), 'failed': sorted(n for n, o in outcomes if o == 'failed'),
            'running': sum(o == 'running' for _, o in outcomes)}


def parse_worktrees(text):
    out = []
    for block in text.strip().split('\n\n'):
        fields = dict(line.split(' ', 1) if ' ' in line else (line, '') for line in block.splitlines())
        if 'worktree' in fields:
            branch = fields.get('branch', '')
            out.append({'path': fields['worktree'], 'head': fields.get('HEAD', '')[:8],
                        'branch': branch[len('refs/heads/'):] if branch.startswith('refs/heads/') else None})
    return out


def parse_parity(text):
    probes, damaged = [], []
    for line in text.splitlines():
        found = PARITY_LINE.match(line)
        if found:
            probes.append({'name': found[1], 'runs': int(found[2]), 'baseline': found[3] if found[3] != 'none' else None,
                           'gated': found[4] == 'gated'})
        elif DAMAGED_LINE.match(line):
            damaged.append(line)
    return {'probes': probes, 'damaged': damaged}


class Gatherer:
    def __init__(self, run, root, news):
        self.run, self.root, self.news, self.errors = run, root, news, []

    def fail(self, source, message):
        self.errors.append({'source': source, 'message': message})

    def git(self, *args, timeout=30):
        return self.run(['git', '-C', self.root, *args], timeout)

    def need(self, source, result):
        if result.rc:
            self.fail(source, (result.err.splitlines() or [f'exit {result.rc}'])[0])
            return None
        return result.out

    def count(self, *args):
        out = self.need('git', self.git('rev-list', '--count', *args))
        return int(out) if out and out.strip().isdigit() else 0

    def fetch(self):
        with futures.ThreadPoolExecutor(len(REMOTES)) as pool:
            for remote, result in zip(REMOTES, pool.map(lambda r: self.git('fetch', '-q', r, timeout=15), REMOTES)):
                if result.rc:
                    self.fail('fetch', f'git fetch {remote}: {(result.err.splitlines() or [result.rc])[0]}')

    def rev(self, ref):
        out = self.need('git', self.git('rev-parse', '--verify', '--quiet', ref))
        return out.strip() if out else ''

    def fork(self):
        return {'main': self.rev('main'), 'upstream': self.rev('upstream/main'),
                'behind': None, 'ahead_of_upstream': self.count('upstream/main..main'),
                'unpushed': self.count('origin/main..main')}

    def gh(self, *args):
        result = self.run(['gh', 'pr', 'list', '--repo', judge.REPO, *args], 40)
        out = self.need('gh', result)
        try:
            return json.loads(out) if out is not None else None
        except ValueError:
            self.fail('gh', 'gh returned unreadable JSON')
            return None

    def open_prs(self):
        found = self.gh('--author', '@me', '--state', 'open', '--limit', '50', '--json', OPEN_FIELDS)
        return [{'number': p['number'], 'title': p['title'], 'url': p['url'], 'head': p['headRefName'],
                 'draft': p['isDraft'], 'review': p['reviewDecision'] or '', 'merge': p['mergeStateStatus'] or '',
                 'checks': checks_summary(p['statusCheckRollup']), 'updated_at': p['updatedAt'],
                 'builds_on': int(m[1]) if (m := BUILDS_ON.search(p['body'] or '')) else None,
                 'files': [f['path'] for f in p['files']]} for p in found or []]

    def others(self):
        found = self.gh('--state', 'open', '--limit', '200', '--json', ALL_OPEN_FIELDS)
        return [{'number': p['number'], 'author': p['author']['login'], 'title': p['title'], 'url': p['url'],
                 'draft': p['isDraft'], 'files': [f['path'] for f in p['files']]} for p in found or []]

    def closed(self):
        found = self.gh('--author', '@me', '--state', 'all', '--limit', '60', '--json', OUR_FIELDS)
        return [{'number': p['number'], 'title': p['title'], 'url': p['url'], 'head': p['headRefName'],
                 'closed_at': p['closedAt'], 'merged': bool(p['mergedAt'])} for p in found or [] if p['state'] != 'OPEN']

    def upstream(self, full):
        """upstream-news's facts; FULL adds the commit that landed each PR."""
        facts = {'behind': None, 'matters': [], 'landings': {}}
        try:
            facts['behind'] = self.news.behind()
            matters = self.news.open_prs()
            facts['landings'] = self.news.landings() if full else {}
        except self.news.Fail as error:
            self.fail('git', str(error))
            return facts
        except OSError as error:
            self.fail(error.filename or 'gh', f'{error.filename or "gh"} not found')
            return facts
        if matters is None:
            self.fail('gh', 'upstream-news could not list the upstream PRs')
        facts['matters'] = [{'number': p['number'], 'author': p['author']['login'], 'title': p['title'],
                             'mac': p['mac'], 'overlap': p['overlap'], 'draft': p['isDraft']} for p in matters or []]
        return facts

    def scratch_facts(self, name, sha, tips):
        twins = {n for n in tips if n != name and judge.kind_of(n) == 'scratch' and tips[n] == sha}
        others = [n for n in tips if n != name and n not in twins]
        inside = self.need('git', self.git('for-each-ref', '--contains', name, '--format=%(refname:short)', 'refs/heads'))
        return {'own_commits': self.count('--no-merges', name, '--not', 'main', 'upstream/main', *others),
                'contained_in': [n for n in (inside or '').split() if n != name and n not in twins]}

    def branch(self, row, tips):
        name, sha, stamp = row
        counts = self.need('git', self.git('rev-list', '--left-right', '--count', f'main...{name}')) or '0\t0'
        behind, ahead = counts.split()
        entry = {'name': name, 'sha': sha[:8], 'ts': int(stamp), 'ahead': int(ahead), 'behind': int(behind),
                 'ahead_up': self.count(f'upstream/main..{name}'), 'unpushed': self.count(name, '--not', '--remotes=origin'),
                 'pushed': self.git('rev-parse', '--verify', '--quiet', f'refs/remotes/origin/{name}').rc == 0,
                 'contained_in': [], 'own_commits': None, 'files': []}
        kind = judge.kind_of(name)
        if kind == 'scratch':
            entry.update(self.scratch_facts(name, sha, tips))
        if kind == 'up':
            entry['files'] = (self.need('git', self.git('diff', '--name-only', f'upstream/main...{name}')) or '').split()
        return entry

    def branches(self):
        out = self.need('git', self.git('for-each-ref', '--format=%(refname:short)\t%(objectname)\t%(committerdate:unix)',
                                        'refs/heads')) or ''
        rows = [line.split('\t') for line in out.splitlines()]
        tips = {r[0]: r[1] for r in rows}
        with futures.ThreadPoolExecutor(8) as pool:
            return list(pool.map(lambda r: self.branch(r, tips), [r for r in rows if r[0] != 'main']))

    def worktree(self, entry):
        status = self.run(['git', '-C', entry['path'], 'status', '--porcelain'], 30)
        stamp = self.run(['git', '-C', entry['path'], 'log', '-1', '--format=%ct'], 30)
        return {**entry, 'changes': len(status.out.splitlines()) if status.rc == 0 else None,
                'ts': int(stamp.out) if stamp.rc == 0 and stamp.out.strip().isdigit() else 0}

    def worktrees(self):
        found = parse_worktrees(self.need('git', self.git('worktree', 'list', '--porcelain')) or '')
        with futures.ThreadPoolExecutor(6) as pool:
            done = list(pool.map(self.worktree, found))
        return [{**w, 'primary': i == 0} for i, w in enumerate(done)]

    def parity(self):
        result = self.run([sys.executable, '-I', os.path.join(self.root, 'mac/tools/parity/parity'), 'list'], 60)
        parsed = parse_parity(result.out)
        if result.rc and not parsed['probes'] and not parsed['damaged']:
            self.fail('parity', (result.err.splitlines() or [f'parity list exit {result.rc}'])[0])
        return parsed


def gather(run, root, news, fetch=True, full=True, now=None):
    """The raw facts; judge.assemble turns them into the snapshot. full=False skips what the brief view never uses."""
    g = Gatherer(run, root, news)
    if fetch:
        g.fetch()
    jobs = {'fork': g.fork, 'open': g.open_prs, 'others': g.others, 'branches': g.branches}
    if full:
        jobs.update(worktrees=g.worktrees, parity=g.parity)
    jobs.update(closed=g.closed, news=lambda: g.upstream(full))
    with futures.ThreadPoolExecutor(len(jobs)) as pool:
        done = {name: pool.submit(job) for name, job in jobs.items()}
        found = {name: future.result() for name, future in done.items()}
    fork, facts = found['fork'], found['news']
    fork['behind'] = facts['behind']
    return {'now': now or datetime.now().astimezone().isoformat(timespec='seconds'), 'fork': fork,
            'open': found['open'], 'others': found['others'], 'closed': found['closed'], 'matters': facts['matters'],
            'landings': facts['landings'], 'branches': found['branches'], 'worktrees': found.get('worktrees', []),
            'parity': found.get('parity'), 'errors': g.errors}
