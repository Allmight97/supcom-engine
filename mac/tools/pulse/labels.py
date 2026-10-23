"""Words for statuses and ages, shared by the text view, the HTML view and the since-last-look list."""
from datetime import datetime

REVIEW = {'APPROVED': 'approved', 'CHANGES_REQUESTED': 'changes requested', 'REVIEW_REQUIRED': 'awaiting review',
          '': 'no review yet'}
MERGE = {'CLEAN': 'ready to merge', 'BLOCKED': 'blocked', 'DIRTY': 'merge conflict', 'BEHIND': 'behind its base',
         'UNSTABLE': 'checks unstable', 'DRAFT': 'draft', 'HAS_HOOKS': 'ready to merge', 'UNKNOWN': 'unknown', '': 'unknown'}
PR_STATE = {'open': 'open', 'landed': 'landed', 'merged': 'merged', 'closed': 'closed unlanded'}


def when(iso):
    return datetime.fromisoformat(iso.replace('Z', '+00:00'))


def age(then, now):
    minutes = max(0, int((when(now) - when(then)).total_seconds() // 60))
    if minutes < 60:
        return f'{minutes}m'
    if minutes < 60 * 48:
        return f'{minutes // 60}h'
    return f'{minutes // 1440}d'


def clock(iso):
    return when(iso).strftime('%H:%M')


def short(text, limit):
    return text if len(text) <= limit else text[:limit - 3].rstrip() + '...'


def checks(c):
    parts = [f'{c["passed"]} passed'] if c['passed'] else []
    if c['failed']:
        parts.append(f'{len(c["failed"])} failed ({", ".join(c["failed"])})')
    if c['running']:
        parts.append(f'{c["running"]} running')
    return ', '.join(parts) or 'no checks'


def checks_tone(c):
    return 'bad' if c['failed'] else 'wait' if c['running'] or not c['passed'] else 'ok'


def review(code):
    return REVIEW.get(code or '', (code or '').lower())


def merge(code):
    return MERGE.get(code or '', (code or '').lower())


def pr_state(pr):
    return PR_STATE.get(pr['state'], pr['state'])


def files_label(files, limit=3):
    names = [f.rsplit('/', 1)[-1] for f in files]
    return ', '.join(names[:limit]) + (f' +{len(names) - limit}' if len(names) > limit else '')
