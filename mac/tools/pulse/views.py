"""The text, brief and JSON views of a snapshot."""
import json
import textwrap

import labels

LEGEND = 'N needs you   U our upstream PRs   O overlap   L landed   F fork   B branches   W worktrees   P parity'
ORDER = 'NUOLFPBW'
CAP = 40


def as_json(snapshot):
    return json.dumps(snapshot, indent=2)


def sha(value, detail):
    return (value or '?')[:12 if detail else 8]


def fork_summary(snap):
    fork = snap['fork']
    ahead, behind = fork.get('ahead_of_upstream'), fork.get('behind')
    return (f'fork main {sha(fork.get("main"), False)} vs upstream {sha(fork.get("upstream"), False)} '
            f'(+{"?" if ahead is None else ahead}/-{"?" if behind is None else behind})')


def header(snap, now=None):
    checked = snap['checked_at']
    return f'pulse  checked {labels.clock(checked)} ({labels.age(checked, now or checked)} ago)  {fork_summary(snap)}'


def error_lines(snap):
    seen = {}
    for error in snap['errors']:
        seen.setdefault(error['source'], error['message'])
    return [f'pulse: {source} failed ({message}); what it feeds is missing or stale' for source, message in seen.items()]


def link(url, detail):
    return f' <{url}>' if detail and url else ''


def needs_lines(snap, detail):
    items = snap['needs_you']
    if not items:
        return ['nothing needs you']
    return [f'{i["code"]}: {i["text"]} -- {i["why"]}{link(i["link"], detail)}' for i in items]


def pr_lines(snap, detail):
    out = []
    for p in snap['prs']:
        parts = [f'#{p["number"]} {labels.short(p["title"], 45 if not detail else 120)}', f'checks: {labels.checks(p["checks"])}',
                 labels.review(p['review']), labels.merge(p['merge'])]
        if p['draft']:
            parts.append('draft')
        if p['builds_on']:
            parts.append(f'builds on #{p["builds_on"]}')
        out.append('  '.join(parts[:1]) + '  ' + ' | '.join(parts[1:]) + link(p['url'], detail))
    return out or ['no open upstream PRs']


def overlap_lines(snap, detail):
    out = []
    for e in snap['overlap']:
        what = f'shares {labels.files_label(e["files"], 8 if detail else 3)} with {", ".join(e["with"])}' if e['with'] \
            else ' '.join(e['tags']) + (f' {labels.files_label(e["files"])}' if e['files'] else '')
        out.append(f'#{e["number"]} {e["author"]}: {labels.short(e["title"], 50)}  {what}{link(e["url"], detail)}')
    return out or ['no overlapping upstream PRs']


def landed_lines(snap, detail):
    return [f'#{p["number"]} {labels.pr_state(p)} {p["closed_at"][5:10]}'
            f'{" " + p["landing"] if p["landing"] and detail else ""}: {labels.short(p["title"], 60)}{link(p["url"], detail)}'
            for p in snap['landed']] or ['none in the last 14 days']


def fork_lines(snap, detail):
    f = snap['fork']
    return [f'main {sha(f.get("main"), detail)}: {f.get("ahead_of_upstream")} ahead of upstream, {f.get("behind")} behind, '
            f'{f.get("unpushed")} not on origin; upstream main {sha(f.get("upstream"), detail)}']


def parity_lines(snap, detail):
    probes = snap['parity']['probes']
    if detail:
        out = [f'{p["name"]}: {"gated" if p["gated"] else "not gated"}, {p["runs"]} runs, baseline {p["baseline"] or "none"}'
               for p in probes]
    else:
        names = lambda gated: ', '.join(p['name'] for p in probes if p['gated'] == gated) or 'none'
        out = textwrap.wrap(f'gated: {names(True)}; not gated: {names(False)}', 100)
    return out + [f'DAMAGED {d}' for d in snap['parity']['damaged']] or ['no probes stored']


def branch_state(b):
    notes = [f'deletable: {b["reason"]}' if b['deletable'] else b['reason']]
    notes.append(f'{b["unpushed"]} not on origin' if b['unpushed'] and b['ahead'] else '')
    notes.append('no PR' if b['kind'] == 'up' and b['pr'] is None and b['ahead_upstream'] and not b['deletable'] else '')
    return '; '.join(n for n in notes if n)


def branch_line(b, snap, detail):
    held = f' [worktree {b["worktree"].rsplit("/", 1)[-1]}]' if b['worktree'] else ''
    age = labels.age(b['last_commit_at'], snap['checked_at'])
    extra = f'  +{b["ahead"]}/-{b["behind"]} {age}' if detail else f'  {age}'
    return f'{b["name"]}{extra}  {branch_state(b)}{held}'.rstrip()


def branch_lines(snap, detail):
    shown = [b for b in snap['branches'] if detail or b['noteworthy']]
    out = [branch_line(b, snap, detail) for b in shown]
    hidden = len(snap['branches']) - len(shown)
    return out + ([f'{hidden} other branches in step with their work: pulse --detail'] if hidden else []) or ['no other branches']


def worktree_lines(snap, detail):
    out = []
    for w in snap['worktrees']:
        state = 'unknown' if w['dirty'] is None else f'{w["changes"]} uncommitted' if w['dirty'] else 'clean'
        name = w['path'] if detail else w['path'].rstrip('/').rsplit('/', 1)[-1]
        pr = f'  PR #{w["pr"]["number"]} {labels.pr_state(w["pr"])}' if w['pr'] else ''
        done = '  branch done' if w['branch_done'] else ''
        age = labels.age(w['last_commit_at'], snap['checked_at']) if w['last_commit_at'] else '?'
        out.append(f'{name}  {w["branch"] or "detached " + w["head"]}  {state}  last commit {age} ago{pr}{done}')
    return out


SECTIONS = {'N': ('NEEDS YOU', needs_lines), 'U': ('OUR UPSTREAM PRS', pr_lines), 'O': ('OVERLAP', overlap_lines),
            'L': ('LANDED', landed_lines), 'F': ('FORK', fork_lines), 'P': ('PARITY', parity_lines),
            'B': ('BRANCHES', branch_lines), 'W': ('WORKTREES', worktree_lines)}
MINIMUM = {'N': 8, 'U': 6, 'O': 3, 'L': 2, 'F': 1, 'P': 2, 'B': 4, 'W': 3}
WIDTH = 120


def entries(snap, detail):
    return {code: [textwrap.wrap(line, WIDTH, initial_indent='  ', subsequent_indent='      ') or ['  ']
                   for line in render(snap, detail)] for code, (_, render) in SECTIONS.items()}


def fit(bodies, room):
    """How many entries of each section to show so the text fits ROOM lines: every section gets its minimum
    first, then the sections fill in priority order. A cut section ends with a line that says so."""
    take = dict.fromkeys(ORDER, 0)

    def used():
        return len(ORDER) + sum(sum(len(e) for e in bodies[c][:take[c]]) + (take[c] < len(bodies[c])) for c in ORDER)

    def grow(code, limit):
        while take[code] < len(bodies[code]):
            take[code] += 1
            shown = sum(len(e) for e in bodies[code][:take[code]])
            if used() > room or (limit and take[code] > 1 and shown > limit[code]):
                take[code] -= 1
                return

    for limit in (MINIMUM, None):
        for code in ORDER:
            grow(code, limit)
    return take


def section_lines(snap, code, body, shown):
    count = len(snap['needs_you']) if code == 'N' else 0
    out = [f'{code}  {SECTIONS[code][0]}' + (f' ({count})' if count else '')]
    out += [line for entry in body[:shown] for line in entry]
    return out + ([f'  ... {len(body) - shown} more: pulse --detail'] if shown < len(body) else [])


def text(snap, detail=False, cap=CAP):
    bodies = entries(snap, detail)
    head = [header(snap), LEGEND] + error_lines(snap)
    take = {c: len(bodies[c]) for c in ORDER} if detail else fit(bodies, cap - len(head))
    return '\n'.join(head + [line for code in ORDER for line in section_lines(snap, code, bodies[code], take[code])])


def brief(snap):
    out = [header(snap)] if snap['fork'].get('main') else []
    out += error_lines(snap)
    if not snap['errors'] or snap['fork'].get('main'):
        out.append(f'N  NEEDS YOU ({len(snap["needs_you"])})' if snap['needs_you'] else 'N  nothing needs you')
        out += [f'  {line}' for line in needs_lines(snap, False)] if snap['needs_you'] else []
    return '\n'.join(out)
