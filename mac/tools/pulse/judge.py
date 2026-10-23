"""From the raw facts to the snapshot: which branches are done, which PRs overlap, what needs JStar, and what
changed since the last look. Pure functions: no command runs here."""
from datetime import datetime, timedelta

import labels

SCHEMA = 1
REPO = 'bwiemz/supcom-engine'
LANDED_DAYS = 14
NOISE_PREFIXES = ('docs/', 'mac/', '.github/')
NOISE_FILES = {'AGENTS.md', 'CLAUDE.md', 'README.md'}
KINDS = ('up', 'mac', 'scratch', 'claude')


def kind_of(name):
    return next((k for k in KINDS if name.startswith(k + '/')), 'other')


def pr_url(number):
    return f'https://github.com/{REPO}/pull/{number}'


def meaningful(paths):
    return {p for p in paths if not p.startswith(NOISE_PREFIXES) and p not in NOISE_FILES}


def local_iso(timestamp):
    return datetime.fromtimestamp(timestamp).astimezone().isoformat(timespec='seconds') if timestamp else ''


def heads(raw):
    """Branch name -> its newest PR {number, state, url}; an open PR wins."""
    index = {}
    landings = raw['landings']
    for pr in sorted(raw['closed'], key=lambda p: p['number']):
        state = 'merged' if pr['merged'] else 'landed' if landings.get(pr['number']) else 'closed'
        index[pr['head']] = {'number': pr['number'], 'state': state, 'url': pr['url']}
    for pr in raw['open']:
        index[pr['head']] = {'number': pr['number'], 'state': 'open', 'url': pr['url']}
    return index


def judge_up(b, pr):
    if pr:
        extra = f'; {b["ahead"]} commits not in main' if b['ahead'] and pr['state'] == 'closed' else ''
        return True, f'PR #{pr["number"]} {labels.pr_state(pr)}{extra}'
    return (True, 'every commit is in upstream/main') if b['ahead_up'] == 0 else (False, '')


def judge_scratch(b):
    if b['own_commits'] != 0:
        return False, ''
    inside = b['contained_in']
    return True, f'every commit is in {", ".join(inside[:3])}' if inside else 'only merge commits of other branches'


def judge_branch(b, kind, pr):
    """(deletable, reason) for one local branch."""
    if pr and pr['state'] == 'open':
        return False, f'open PR #{pr["number"]}'
    if kind == 'up':
        return judge_up(b, pr)
    if b['ahead'] == 0:
        return True, 'merged into main'
    return judge_scratch(b) if kind == 'scratch' else (False, '')


def branch_entries(raw, index, held):
    out = []
    for b in raw['branches']:
        kind, pr = kind_of(b['name']), index.get(b['name'])
        deletable, reason = judge_branch(b, kind, pr)
        noteworthy = deletable or (b['unpushed'] > 0 and b['ahead'] > 0) or (kind == 'up' and pr is None and b['ahead_up'] > 0)
        out.append({'name': b['name'], 'kind': kind, 'sha': b['sha'], 'last_commit_at': local_iso(b['ts']),
                    'ahead': b['ahead'], 'behind': b['behind'], 'ahead_upstream': b['ahead_up'],
                    'pushed': b['pushed'], 'unpushed': b['unpushed'], 'pr': pr, 'worktree': held.get(b['name']),
                    'deletable': deletable, 'reason': reason, 'noteworthy': noteworthy,
                    'files': sorted(b['files'])})
    return sorted(out, key=lambda e: (not e['deletable'], e['kind'], e['name']))


def our_files(raw, branch_list):
    """Label -> files of our live work: each open PR (with its local branch's files) and each up/* branch not done."""
    mine = {f'#{pr["number"]}': meaningful(pr['files']) for pr in raw['open']}
    by_head = {pr['head']: f'#{pr["number"]}' for pr in raw['open']}
    for b in branch_list:
        if b['kind'] == 'up' and not b['deletable'] or b['name'] in by_head:
            mine.setdefault(by_head.get(b['name'], b['name']), set()).update(meaningful(b['files']))
    return mine


def overlap_entry(pr, mine, news):
    files = meaningful(pr['files'])
    with_ = [label for label, theirs in mine.items() if files & theirs]
    shared = sorted(set().union(*(files & mine[label] for label in with_)) if with_ else ())
    return {'number': pr['number'], 'author': pr['author'], 'title': pr['title'], 'url': pr['url'],
            'files': shared or news.get('overlap', []), 'with': with_, 'tags': news_tags(news), 'draft': pr['draft']}


def overlap_entries(raw, branch_list, ours):
    """Other authors' open PRs that share files with our open PRs or live up/* branches, then the rest of
    upstream-news's MAC/OVERLAP list."""
    mine = our_files(raw, branch_list)
    tags = {p['number']: p for p in raw['matters']}
    entries = {}
    for pr in (p for p in raw['others'] if p['number'] not in ours):
        entry = overlap_entry(pr, mine, tags.get(pr['number'], {}))
        if entry['with'] or pr['number'] in tags:
            entries[pr['number']] = entry
    for number, news in tags.items():
        if number not in entries and number not in ours:
            entries[number] = {'number': number, 'author': news['author'], 'title': news['title'], 'url': pr_url(number),
                               'files': news['overlap'], 'with': [], 'tags': news_tags(news), 'draft': news['draft']}
    return sorted(entries.values(), key=lambda e: (not e['with'], -e['number']))


def news_tags(news):
    return [t for t, on in (('MAC', news.get('mac')), ('OVERLAP', news.get('overlap'))) if on]


def landed_entries(raw):
    cutoff = labels.when(raw['now']) - timedelta(days=LANDED_DAYS)
    landings = raw['landings']
    out = []
    for pr in sorted(raw['closed'], key=lambda p: -p['number']):
        if pr['closed_at'] and labels.when(pr['closed_at']) >= cutoff:
            landing = landings.get(pr['number'], '')
            state = 'merged' if pr['merged'] else 'landed' if landing else 'closed'
            out.append({'number': pr['number'], 'title': pr['title'], 'url': pr['url'], 'head': pr['head'],
                        'state': state, 'closed_at': pr['closed_at'], 'landing': landing})
    return out


def pr_entries(raw, branch_list):
    local = {b['name']: b for b in branch_list}
    return [{'number': pr['number'], 'title': pr['title'], 'url': pr['url'], 'head': pr['head'],
             'draft': pr['draft'], 'checks': pr['checks'], 'review': pr['review'], 'merge': pr['merge'],
             'builds_on': pr['builds_on'], 'updated_at': pr['updated_at'],
             'unpushed': local[pr['head']]['unpushed'] if pr['head'] in local else None}
            for pr in sorted(raw['open'], key=lambda p: p['number'])]


def worktree_entries(raw, index, by_name):
    out = []
    for w in raw['worktrees']:
        branch = by_name.get(w['branch'])
        out.append({'path': w['path'], 'branch': w['branch'], 'head': w['head'], 'primary': w['primary'],
                    'dirty': w['changes'] > 0 if w['changes'] is not None else None, 'changes': w['changes'],
                    'last_commit_at': local_iso(w['ts']), 'pr': index.get(w['branch']),
                    'branch_done': bool(branch and branch['deletable'])})
    return out


def assemble(raw):
    index = heads(raw)
    held = {w['branch']: w['path'] for w in raw['worktrees'] if w['branch']}
    branch_list = branch_entries(raw, index, held)
    by_name = {b['name']: b for b in branch_list}
    ours = {pr['number'] for pr in raw['open']}
    parity = raw['parity'] or {'probes': [], 'damaged': []}
    snapshot = {'schema': SCHEMA, 'checked_at': raw['now'], 'fork': raw['fork'],
                'prs': pr_entries(raw, branch_list), 'overlap': overlap_entries(raw, branch_list, ours),
                'landed': landed_entries(raw), 'branches': branch_list,
                'worktrees': worktree_entries(raw, index, by_name), 'parity': parity,
                'needs_you': [], 'errors': raw['errors']}
    snapshot['needs_you'] = needs_you(snapshot)
    return snapshot


def item(code, text, why, link=None):
    return {'code': code, 'text': text, 'why': why, 'link': link}


def pr_items(pr):
    n, link = pr['number'], pr['url']
    items = []
    if pr['checks']['failed']:
        items.append(item('checks-failed', f'#{n} fails {", ".join(pr["checks"]["failed"])}',
                          'CI must pass before upstream reviews it', link))
    if pr['review'] == 'CHANGES_REQUESTED':
        items.append(item('changes-requested', f'#{n} has changes requested', 'the reviewer waits on a new push', link))
    if pr['merge'] == 'DIRTY':
        items.append(item('merge-conflict', f'#{n} has a merge conflict with upstream main',
                          'rebase it on upstream/main', link))
    if pr['draft']:
        items.append(item('draft', f'#{n} is a draft', 'upstream does not review a draft', link))
    if pr['unpushed']:
        items.append(item('unpushed', f'#{n} ({pr["head"]}) has {pr["unpushed"]} commits not on origin',
                          'the PR shows the pushed branch, not your local work', link))
    return items


def overlap_items(entries):
    return [item('overlap', f'#{e["number"]} ({e["author"]}) shares {labels.files_label(e["files"])} with '
                 + ', '.join(e['with']), 'may conflict, or do the same work', e['url'])
            for e in entries if e['with']]


def pushed_without_pr(b):
    return b['kind'] == 'up' and b['pushed'] and b['pr'] is None and b['ahead_upstream'] and not b['deletable']


def delete_item(branch_list):
    free = [b['name'] for b in branch_list if b['deletable'] and not b['worktree']]
    held = [f'{b["name"]} (worktree {b["worktree"].rsplit("/", 1)[-1]})' for b in branch_list
            if b['deletable'] and b['worktree']]
    parts = ([f'safe to delete: {", ".join(free)}'] if free else []) + \
            ([f'done, but a worktree holds them (remove it first): {", ".join(held)}'] if held else [])
    why = 'needs your word: git branch -D' if free else 'needs your word: remove the worktree, then git branch -D'
    return [item('delete-branches', '; '.join(parts), why)] if parts else []


def branch_items(branch_list, pr_facts):
    items = [item('pushed-no-pr', f'{b["name"]} is pushed to origin with no PR',
                  f'{b["ahead_upstream"]} commits could go upstream') for b in branch_list if pr_facts and pushed_without_pr(b)]
    return items + delete_item(branch_list)


def needs_you(snapshot):
    items = [i for pr in snapshot['prs'] for i in pr_items(pr)]
    behind = snapshot['fork'].get('behind')
    if behind:
        items.append(item('sync-due', f'fork main is {behind} commits behind upstream', 'run mac/scripts/sync-upstream'))
    gh_ok = not any(e['source'] == 'gh' for e in snapshot['errors'])
    return items + branch_items(snapshot['branches'], gh_ok) + overlap_items(snapshot['overlap'])


def label_map(entries, key='number'):
    return {e[key]: e for e in entries}


PR_FACETS = (('checks', lambda p: labels.checks(p['checks'])), ('review', lambda p: labels.review(p['review'])),
             ('merge state', lambda p: labels.merge(p['merge'])))


def pr_changes(old, new):
    before, after, ended = label_map(old['prs']), label_map(new['prs']), label_map(new['landed'])
    changes = [f'new PR #{n}: {p["title"]}' for n, p in after.items() if n not in before]
    changes += [f'#{n} {what}: {fmt(before[n])} -> {fmt(p)}' for n, p in after.items() if n in before
                for what, fmt in PR_FACETS if fmt(before[n]) != fmt(p)]
    changes += [f'#{n} is no longer open: {labels.pr_state(ended[n]) if n in ended else "gone"}' for n in before if n not in after]
    return changes


def overlap_changes(old, new):
    before, after = label_map(old['overlap']), label_map(new['overlap'])
    return ([f'new overlap: #{n} ({e["author"]}) {e["title"]}' for n, e in after.items() if n not in before]
            + [f'overlap gone: #{n}' for n in before if n not in after])


def branch_changes(old, new):
    before, after = {b['name'] for b in old['branches']}, {b['name'] for b in new['branches']}
    return [f'branch added: {n}' for n in sorted(after - before)] + [f'branch removed: {n}' for n in sorted(before - after)]


def since(old, new):
    """Plain sentences for what differs between two snapshots."""
    moved = old['fork'].get('upstream') != new['fork'].get('upstream')
    fork = [f'upstream main moved: {old["fork"].get("behind")} -> {new["fork"].get("behind")} commits behind'] if moved else []
    return pr_changes(old, new) + overlap_changes(old, new) + branch_changes(old, new) + fork
