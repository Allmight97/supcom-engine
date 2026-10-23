"""The HTML view: one self-contained page, text labels first and colour second."""
import html
import os

import judge
import labels
import views

CSS = """
:root { --bg:#fafaf7; --fg:#1d1d1b; --muted:#5d5d57; --line:#d9d8d0; --card:#fff; --ok:#1d6b3a; --wait:#8a5a00;
  --bad:#a6261c; --needs:#fff4d6; --needs-line:#b07a00; --link:#14527a; }
@media (prefers-color-scheme: dark) { :root { --bg:#141413; --fg:#ecebe4; --muted:#a3a29a; --line:#3a3a36;
  --card:#1d1d1b; --ok:#6fcf8d; --wait:#e8b64c; --bad:#ff8a80; --needs:#2e2410; --needs-line:#e8b64c; --link:#7ec0ee; } }
body { background:var(--bg); color:var(--fg); font:16px/1.55 -apple-system, system-ui, sans-serif; margin:0; }
main { max-width:68rem; margin:0 auto; padding:2rem 1.25rem 4rem; }
h1 { font-size:1.6rem; margin:0 0 .25rem; } h2 { font-size:1.15rem; margin:0 0 .75rem; }
section { margin:0 0 2.25rem; } a { color:var(--link); }
.code { display:inline-block; min-width:1.6rem; text-align:center; border:1px solid var(--line); border-radius:4px;
  font-weight:700; margin-right:.5rem; padding:0 .3rem; }
.muted { color:var(--muted); } .legend span { display:inline-block; margin-right:1.25rem; }
.needs { background:var(--needs); border:2px solid var(--needs-line); border-radius:8px; padding:1rem 1.25rem; }
.needs li { margin:.6rem 0; } .needs .why { color:var(--muted); display:block; }
table { border-collapse:collapse; width:100%; background:var(--card); } th, td { text-align:left; vertical-align:top;
  border-bottom:1px solid var(--line); padding:.45rem .6rem; } th { color:var(--muted); font-weight:600; }
.st { font-weight:700; } .ok { color:var(--ok); } .wait { color:var(--wait); } .bad { color:var(--bad); }
ul.plain { padding-left:1.2rem; } ul.plain li { margin:.35rem 0; } code { font-size:.9em; }
"""

SCRIPT = """
for (const t of document.querySelectorAll('time[data-ago]')) {
  const m = Math.max(0, Math.round((Date.now() - Date.parse(t.dateTime)) / 60000));
  t.textContent = m < 60 ? m + ' min ago' : Math.round(m / 60) + ' h ago';
}
"""

TONE = {'passed': 'ok', 'failed': 'bad', 'running': 'wait'}


def e(value):
    return html.escape(str(value))


def status(text, tone):
    return f'<span class="st {tone}">{e(text)}</span>'


def anchor(url, text):
    return f'<a href="{e(url)}">{e(text)}</a>' if url else e(text)


def table(heads, rows):
    if not rows:
        return '<p class="muted">none</p>'
    body = ''.join('<tr>' + ''.join(f'<td>{cell}</td>' for cell in row) + '</tr>' for row in rows)
    return f'<table><thead><tr>{"".join(f"<th>{h}</th>" for h in heads)}</tr></thead><tbody>{body}</tbody></table>'


def section(code, title, body, css=''):
    return (f'<section id="{code}" class="{css}"><h2><span class="code">{code}</span>{e(title)}</h2>{body}</section>')


def needs_block(snap):
    items = snap['needs_you']
    if not items:
        return section('N', 'Needs you', '<p>Nothing needs you.</p>', 'needs')
    rows = ''.join(f'<li>{status("needs your word" if i["code"] == "delete-branches" else "needs you", "bad")} '
                   f'{anchor(i["link"], i["text"])}<span class="why">{e(i["why"])}</span></li>' for i in items)
    return section('N', f'Needs you ({len(items)})', f'<ul class="plain">{rows}</ul>', 'needs')


def since_block(changes, before):
    body = ''.join(f'<li>{e(c)}</li>' for c in changes) if changes else '<li>Nothing changed.</li>'
    return (f'<section id="since"><h2>Since your last look ({e(labels.clock(before))})</h2><ul class="plain">{body}</ul></section>')


def pr_block(snap):
    rows = []
    for p in snap['prs']:
        c = p['checks']
        rows.append([anchor(p['url'], f'#{p["number"]}'), e(p['title']), f'<code>{e(p["head"])}</code>',
                     status(labels.checks(c), labels.checks_tone(c)),
                     status(labels.review(p['review']), 'bad' if p['review'] == 'CHANGES_REQUESTED' else 'wait' if p['review'] != 'APPROVED' else 'ok'),
                     status(labels.merge(p['merge']), 'bad' if p['merge'] == 'DIRTY' else 'wait' if p['merge'] == 'BLOCKED' else 'ok')
                     + (' (draft)' if p['draft'] else ''), e(f'#{p["builds_on"]}') if p['builds_on'] else ''])
    return section('U', 'Our upstream PRs', table(['PR', 'Title', 'Branch', 'Checks', 'Review', 'Merge state', 'Builds on'], rows))


def overlap_block(snap):
    rows = [[anchor(o['url'], f'#{o["number"]}'), e(o['author']), e(o['title']), e(', '.join(o['files'])) or '-',
             e(', '.join(o['with'])) or '-', status(' '.join(o['tags']) or 'shares files', 'wait' if o['with'] else 'muted')]
            for o in snap['overlap']]
    return section('O', 'Overlap', table(['PR', 'Author', 'Title', 'Shared files', 'With our work', 'Tags'], rows))


def landed_block(snap):
    rows = [[anchor(p['url'], f'#{p["number"]}'), status(labels.pr_state(p), 'ok' if p['state'] != 'closed' else 'wait'),
             e(p['closed_at'][:10]), e(p['landing']) or '-', f'<code>{e(p["head"])}</code>', e(p['title'])] for p in snap['landed']]
    return section('L', 'Landed in the last 14 days', table(['PR', 'Outcome', 'Closed', 'Landing commit', 'Branch', 'Title'], rows))


def fork_block(snap):
    f = snap['fork']
    items = [('main', f.get('main', '')[:12]), ('upstream main', f.get('upstream', '')[:12]),
             ('ahead of upstream', f.get('ahead_of_upstream')), ('behind upstream', f.get('behind')),
             ('not on origin', f.get('unpushed'))]
    rows = ''.join(f'<li>{e(k)}: <code>{e(v)}</code></li>' for k, v in items)
    return section('F', 'Fork', f'<ul class="plain">{rows}</ul>')


def parity_block(snap):
    rows = [[e(p['name']), status('gated', 'ok') if p['gated'] else status('not gated', 'wait'), e(p['runs']),
             e(p['baseline'] or 'none')] for p in snap['parity']['probes']]
    damaged = ''.join(f'<p>{status("damaged", "bad")} {e(d)}</p>' for d in snap['parity']['damaged'])
    return section('P', 'Parity', table(['Probe', 'Gate', 'Runs', 'Baseline'], rows) + damaged)


def branch_block(snap):
    rows = []
    for b in snap['branches']:
        pr = b['pr']
        rows.append([f'<code>{e(b["name"])}</code>', e(b['kind']), e(labels.age(b['last_commit_at'], snap['checked_at'])),
                     e(f'+{b["ahead"]}/-{b["behind"]}'), status('pushed', 'ok') if b['pushed'] else status('local only', 'wait'),
                     (anchor(pr['url'], f'#{pr["number"]} {labels.pr_state(pr)}') if pr else '-'),
                     (status('deletable', 'bad') + ' ' + e(b['reason']) if b['deletable'] else e(b['reason']) or '-')
                     + (f' <span class="muted">(worktree {e(os.path.basename(b["worktree"]))})</span>' if b['worktree'] else '')])
    return section('B', 'Branches', table(['Branch', 'Kind', 'Last commit', 'Ahead/behind main', 'Pushed', 'PR', 'Verdict'], rows))


def worktree_block(snap):
    rows = []
    for w in snap['worktrees']:
        state = status('unknown', 'wait') if w['dirty'] is None else status(f'{w["changes"]} uncommitted', 'bad') if w['dirty'] else status('clean', 'ok')
        pr = w['pr']
        rows.append([f'<code>{e(w["path"])}</code>', e(w['branch'] or 'detached ' + w['head']), state,
                     e(labels.age(w['last_commit_at'], snap['checked_at']) + ' ago') if w['last_commit_at'] else '?',
                     anchor(pr['url'], f'#{pr["number"]} {labels.pr_state(pr)}') if pr else '-',
                     status('branch done', 'wait') if w['branch_done'] else ''])
    return section('W', 'Worktrees', table(['Path', 'Branch', 'State', 'Last commit', 'PR', 'Note'], rows))


def legend():
    items = [(c, t) for c, (t, _) in views.SECTIONS.items()]
    return '<p class="legend">' + ''.join(f'<span><span class="code">{c}</span>{e(t.lower())}</span>' for c, t in items) + '</p>'


def page(snap, previous=None):
    checked = snap['checked_at']
    errors = ''.join(f'<p>{status("failed", "bad")} {e(line)}</p>' for line in views.error_lines(snap))
    since = since_block(judge.since(previous, snap), previous['checked_at']) if previous else ''
    blocks = {'N': needs_block(snap), 'U': pr_block(snap), 'O': overlap_block(snap), 'L': landed_block(snap),
              'F': fork_block(snap), 'P': parity_block(snap), 'B': branch_block(snap), 'W': worktree_block(snap)}
    top = (f'<h1>pulse</h1><p>Checked {e(checked.replace("T", " "))} (<time datetime="{e(checked)}" data-ago>just now</time>). '
           f'{e(views.fork_summary(snap))}</p>{legend()}{errors}')
    body = top + blocks['N'] + since + ''.join(blocks[c] for c in 'UOLFPBW')
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>pulse</title><style>{CSS}</style></head><body><main>{body}</main><script>{SCRIPT}</script></body></html>')
