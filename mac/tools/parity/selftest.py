"""Self-tests on synthetic fixtures: no game data, no game, no build needed."""
import contextlib
import importlib.machinery
import importlib.util
import io
import os
import stat
import subprocess
import sys
import tempfile

import adapters
import core
import runs
import store


def timing_log(mutate=None):
    lines = []
    for t in adapters.Timing.factory_clocks:
        lines.append(f'info: PROBE timing factory t={t} state=Bu progress={t / 100:.4f} consumed=1.000 focus=uel0201 focus-frac=0.0000')
    for t in range(41):
        lines.append(f'PROBE timing engineer t={t} state=- progress=0.0000 consumed=0.000 focus=none focus-frac=-1.0000 at=260.00,790.00')
    lines.append('PROBE timing done')
    return '\n'.join(mutate(lines) if mutate else lines) + '\n'


def economy_log():
    lines = ['PROBE econ start energy=4000.0/0.00/0.00 mass=650.0/0.00/0.00',
             'PROBE econ stall-start monkeylord-use=250.00 energy=0.0/0.00/0.00 mass=650.0/0.00/0.00',
             'PROBE econ ample-start energy=1.0/2.00/3.00 mass=650.0/0.00/0.00']
    for label in adapters.Economy.labels:
        for t in adapters.Economy.ticks:
            lines.append(f'PROBE econ {label} tick={t} progress=0.100 engineer-focus=none factory-use=1.00 '
                         'energy=1.0/2.00/3.00 mass=1.0/2.00/3.00')
    return '\n'.join(lines + ['PROBE econ done']) + '\n'


def engineer_log():
    lines = ['PROBE eng-build engineer at=260.000,10.000,790.000 turret-bone at=260.000,11.000,790.000']
    for t in range(21):
        lines.append(f'PROBE eng-build t={t} tick=-1 state=- progress=0.0000 consumed=0.000 focus=none heading=0.0000 turret=0.000,1.000 anim=-1.0000')
        if t == 2:
            lines += ['PROBE eng-build event OnStartBuild tick=-1', 'PROBE eng-build event OnStartBuild-done tick=-1',
                      'PROBE eng-build frame at=262.500,10.000,784.500']
    return '\n'.join(lines + ['PROBE eng-build done']) + '\n'


def guardassist_log():
    lines = []
    for scene in adapters.GuardAssist.scenes:
        for t in adapters.GuardAssist.steps:
            focus = 'uel0201#1' if t >= 10 else 'none'
            lines.append(f'PROBE assist {scene} t={t} at=306.00,808.00 gap=14.14 ugap=-1.00 state=Guarding focus={focus} '
                         f'eprog=0.100 fprog=0.200 ftarget=uel0201#1 req=100.00/50.00')
            if t == 9:
                lines += [f'PROBE assist {scene} event OnStartBuild t=9']
    return '\n'.join(lines + ['PROBE assist done']) + '\n'


def buildbots_log():
    lines = []
    for scene, n in adapters.BuildBots.scenes.items():
        for t in range(n):
            lines.append(f'PROBE bots {scene} t={t} estate=Building eprog=0.100 frac=0.100 hp=60.0 bots=1 state=Guarding '
                         'focus=urb1101 bprog=0.000 at=301.66,798.99')
            if t == 9:
                lines.append(f'PROBE bots {scene} event OnStartBuild t=9 bot=1 order=Repair')
    return '\n'.join(lines + ['PROBE bots done']) + '\n'


def crowd_log(short=0):
    lines = []
    for v in range(6):
        for t in range(2, 401, 2):
            lines.append(f'PROBE tr v={v} t={t} 700.00,150.00,1;704.00,150.00,1;')
        lines += [f'PROBE tr-short v={v} i={i} x=1.00 z=2.00 q=0' for i in range(short)]
        lines.append(f'PROBE tr-done v={v} short={short}')
    return '\n'.join(lines + ['PROBE tr-all-done']) + '\n'


def blueprints_log(count=120):
    lines = []
    for n in range(count):
        lines += [f'PROBE bp uel{n:04d} Categories[0]=LAND', f'PROBE bp uel{n:04d} Physics.MaxSpeed={n / 10:g}',
                  f'PROBE bp uel{n:04d} General.UpgradesTo=']
    return '\n'.join(lines + ['PROBE bp done']) + '\n'


def change(text, old, new):
    assert old in text
    return text.replace(old, new, 1)


def expect(cond, message):
    if not cond:
        raise AssertionError(message)


def logs(ref, new):
    return core.Log('ref', ref, runs.osc_errors), core.Log('new', new, runs.osc_errors)


def compare(name, ref, new):
    return core.compare(adapters.ADAPTERS[name], *logs(ref, new))


def problems_of(name, text, errors=runs.osc_errors):
    return core.inspect(adapters.ADAPTERS[name], core.Log('x', text, errors)).problems


def test_core():
    ref = timing_log()
    expect(compare('timing', ref, ref).status == 'MATCH', 'identical logs match')
    expect(compare('timing', ref, ref).fields_compared == 44 * 5 + 41 * 7, 'every declared field is compared')
    changed = compare('timing', ref, change(ref, 'factory t=3 state=Bu progress=0.0300', 'factory t=3 state=Bu progress=0.0301'))
    expect(changed.status == 'DIFFERS' and 'scene=factory phase=start tick=3 field=progress ref=0.03 new=0.0301' in changed.summary,
           changed.summary)
    expect(changed.divergences == 1, 'one divergence counted')
    expect(compare('timing', ref, ref.replace('timing done', 'timing finished')).status == 'INVALID', 'malformed line')
    expect(compare('timing', ref, ref + 'PROBE timing done\n').status == 'INVALID', 'duplicate row')
    for bad in ('nan', 'inf', '-nan(ind)', '1.#QNAN'):
        expect(compare('timing', ref, change(ref, 'progress=0.0300', f'progress={bad}')).status == 'INVALID', f'non-finite {bad}')
    expect(compare('timing', 'nothing\n', 'nothing\n').status == 'INVALID', 'zero comparisons')
    short = '\n'.join(l for l in ref.splitlines() if 'engineer t=7 ' not in l) + '\n'
    expect(compare('timing', ref, short).status == 'INVALID', 'a log missing an expected row is not a complete run')
    expect(compare('timing', ref, change(ref, ' focus-frac=-1.0000 at=260.00,790.00', ' focus-frac=-1.0000', )).status == 'INVALID',
           'a line missing a key is malformed')


def test_compare_demands_a_complete_run():
    """The reproduced false MATCHes: the same incomplete log on both sides used to compare equal."""
    ref = timing_log()
    one_row = next(l for l in ref.splitlines() if 'factory t=0 ' in l) + '\n'
    no_marker = '\n'.join(l for l in ref.splitlines() if 'timing done' not in l) + '\n'
    lua_error = ref + 'warning: Error running lua script: boom\n'
    for what, text, errors in (('one row', one_row, runs.osc_errors), ('no done marker', no_marker, runs.osc_errors),
                               ('a Lua error', lua_error, runs.original_errors)):
        for side in (0, 1):
            pair = [core.Log('ref', ref, errors), core.Log('new', ref, errors)]
            pair[side] = core.Log('ref' if side == 0 else 'new', text, errors)
            result = core.compare(adapters.ADAPTERS['timing'], *pair)
            expect(result.status == 'INVALID', f'{what} on side {side}: {result.status} {result.summary}')
        same = core.compare(adapters.ADAPTERS['timing'], core.Log('a', text, errors), core.Log('b', text, errors))
        expect(same.status == 'INVALID', f'{what} on both sides: {same.status}')
    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for name, text in (('one.log', one_row), ('full.log', ref)):
            paths.append(os.path.join(tmp, name))
            with open(paths[-1], 'w') as f:
                f.write(text)
        done = subprocess.run([sys.executable, '-I', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'parity'),
                               'compare', 'timing', paths[0], paths[0]], capture_output=True, text=True)
        expect(done.returncode == 2 and done.stdout.startswith('INVALID'), f'parity compare of one row: {done.stdout}')


def test_blueprint_values():
    bp = blueprints_log()
    speed = compare('blueprints', bp, change(bp, 'uel0007 Physics.MaxSpeed=0.7', 'uel0007 Physics.MaxSpeed=0.8'))
    expect(speed.status == 'DIFFERS' and 'scene=uel0007 phase=field leg=Physics.MaxSpeed field=value ref=0.7 new=0.8' in speed.summary, speed.summary)
    wide = compare('blueprints', bp, change(bp, 'uel0007 Physics.MaxSpeed=0.7', 'uel0007 Physics.MaxSpeed=0.70000000149012'))
    expect(wide.status == 'MATCH', 'a 32-bit float printed in 14 digits is the same value')
    for old, new, what in (('uel0000 Physics.MaxSpeed=0', 'uel0000 Physics.MaxSpeed=0.0000009', '0 -> 0.0000009'),
                           ('uel0007 Physics.MaxSpeed=0.7', 'uel0007 Physics.MaxSpeed=0.7000009', '0.7 -> 0.7000009')):
        expect(compare('blueprints', bp, change(bp, old, new)).status == 'DIFFERS', what)
    for a, b in (('1000000', '1000001'), ('16777216', '16777217')):
        big = change(bp, 'uel0007 Physics.MaxSpeed=0.7', f'uel0007 Economy.BuildTime={a}')
        expect(compare('blueprints', big, big.replace(a, b)).status == 'DIFFERS', f'integer {a} -> {b} is exact')
    expect(compare('blueprints', bp, change(bp, 'MaxSpeed=0.7', 'MaxSpeed=0.7e0')).status == 'MATCH', 'the same float spelled another way')
    word = compare('blueprints', bp, change(bp, 'uel0007 Categories[0]=LAND', 'uel0007 Categories[0]=AIR'))
    expect(word.status == 'DIFFERS' and 'ref=LAND new=AIR' in word.summary, word.summary)
    expect(compare('blueprints', bp, change(bp, 'MaxSpeed=0.7', 'MaxSpeed=nan')).status == 'INVALID', 'nan in a number')
    expect(compare('blueprints', bp, bp.replace('uel0007 Categories[0]=LAND\n', '')).status == 'DIFFERS', 'a missing field')
    expect(problems_of('blueprints', blueprints_log(5)), 'too few blueprints')


def test_engineer_and_crowd():
    events = engineer_log()
    live = events.replace('tick=-1 state', 'tick=7 state').replace('anim=-1.0000', 'anim=0.5000')
    for ref, new in ((events, live), (live, events)):
        seen = compare('engineer', ref, new)
        expect(seen.status == 'MATCH' and seen.recorded > 0 and 'recorded fields' in seen.summary, seen.summary)
    swapped = change(events, 'event OnStartBuild tick=-1\nPROBE eng-build event OnStartBuild-done tick=-1',
                     'event OnStartBuild-done tick=-1\nPROBE eng-build event OnStartBuild tick=-1')
    expect(compare('engineer', events, swapped).status == 'DIFFERS', 'swapped callbacks are a different sequence')
    late = change(events, 'PROBE eng-build event OnStartBuild tick=-1\n', '')
    late = change(late, 'PROBE eng-build t=5 ', 'PROBE eng-build event OnStartBuild tick=-1\nPROBE eng-build t=5 ')
    expect(compare('engineer', events, late).status == 'DIFFERS', 'a callback at another step differs')
    steps = change(events, 'PROBE eng-build t=3 ', 'PROBE eng-build event OnExtra tick=-1\nPROBE eng-build t=3 ')
    expect('field=name' in compare('engineer', events, steps).summary or compare('engineer', events, steps).status == 'DIFFERS', 'an extra callback')
    dropped = compare('engineer', events, change(events, 'PROBE eng-build event OnStartBuild-done tick=-1\n', ''))
    expect(dropped.status == 'DIFFERS', dropped.summary)
    expect(problems_of('crowd', change(crowd_log(2), 'short=2', 'short=3')), 'tr-done must agree with tr-short rows')
    moved = compare('crowd', crowd_log(), change(crowd_log(), 'v=3 t=100 700.00,150.00', 'v=3 t=100 700.01,150.00'))
    expect(moved.status == 'MATCH' and moved.recorded > 0, 'positions are recorded, not judged')
    fewer = compare('crowd', crowd_log(), change(crowd_log(), 'v=3 t=100 700.00,150.00,1;704.00,150.00,1;', 'v=3 t=100 700.00,150.00,1;'))
    expect(fewer.status == 'DIFFERS' and 'scene=v3 phase=trace tick=100 field=n' in fewer.summary, fewer.summary)
    stopped = compare('crowd', crowd_log(1), crowd_log(1).replace('tr-short v=2 i=0', 'tr-short v=2 i=1'))
    expect(stopped.status == 'DIFFERS' and 'phase=short' in stopped.summary, stopped.summary)


def test_guardassist():
    log = guardassist_log()
    expect(problems_of('guardassist', log) == [], problems_of('guardassist', log))
    expect(compare('guardassist', log, log).status == 'MATCH', 'a log matches itself')
    refocused = compare('guardassist', log, change(log, 'far t=40 at=306.00,808.00 gap=14.14 ugap=-1.00 state=Guarding focus=uel0201#1',
                                                   'far t=40 at=306.00,808.00 gap=14.14 ugap=-1.00 state=Guarding focus=none'))
    expect(refocused.status == 'DIFFERS' and 'scene=far phase=step tick=40 field=focus' in refocused.summary, refocused.summary)
    missing = '\n'.join(l for l in log.splitlines() if 'near t=100 ' not in l) + '\n'
    expect(compare('guardassist', log, missing).status == 'INVALID', 'a missing row is invalid')
    moved = compare('guardassist', log, change(log, 'far t=40 at=306.00,808.00 gap=14.14 ugap=-1.00', 'far t=40 at=307.25,809.50 gap=15.00 ugap=3.00'))
    expect(moved.status == 'MATCH' and moved.recorded > 0, 'position, gap and ugap are recorded, not judged')
    late = change(change(log, 'PROBE assist near event OnStartBuild t=9\n', ''), 'PROBE assist near t=11 ',
                  'PROBE assist near event OnStartBuild t=10\nPROBE assist near t=11 ')
    expect(compare('guardassist', log, late).status == 'DIFFERS', 'an event at another step differs')
    expect(compare('guardassist', log, change(log, 'PROBE assist far event OnStartBuild t=9\n', '')).status == 'DIFFERS', 'a missing event')


def test_buildbots():
    log = buildbots_log()
    expect(problems_of('buildbots', log) == [], problems_of('buildbots', log))
    unfocused = compare('buildbots', log, change(log, 'frame t=40 estate=Building eprog=0.100 frac=0.100 hp=60.0 bots=1 state=Guarding focus=urb1101',
                                                 'frame t=40 estate=Building eprog=0.100 frac=0.100 hp=60.0 bots=1 state=Guarding focus=none'))
    expect(unfocused.status == 'DIFFERS' and 'scene=frame phase=step tick=40 field=focus' in unfocused.summary, unfocused.summary)
    moved = compare('buildbots', log, change(log, 'cybran t=40 estate=Building eprog=0.100 frac=0.100 hp=60.0 bots=1 state=Guarding focus=urb1101 bprog=0.000 at=301.66,798.99',
                                             'cybran t=40 estate=Building eprog=0.100 frac=0.100 hp=60.0 bots=1 state=Guarding focus=urb1101 bprog=0.000 at=305.00,790.00'))
    expect(moved.status == 'MATCH' and moved.recorded > 0, 'the bot\'s position is recorded, not judged')
    reordered = change(log, 'PROBE bots repair event OnStartBuild t=9 bot=1 order=Repair', 'PROBE bots repair event OnStartBuild t=9 bot=1 order=MobileBuild')
    expect(compare('buildbots', log, reordered).status == 'DIFFERS', 'another order named by a start differs')
    expect(compare('buildbots', log, change(log, 'PROBE bots reclaim event OnStartBuild t=9 bot=1 order=Repair\n', '')).status == 'DIFFERS',
           'a missing event')
    missing = '\n'.join(l for l in log.splitlines() if 'builder t=100 ' not in l) + '\n'
    expect(compare('buildbots', log, missing).status == 'INVALID', 'a missing row is invalid')


def test_valid_logs():
    cases = {'timing': timing_log(), 'economy': economy_log(), 'engineer': engineer_log(), 'crowd': crowd_log(2),
             'guardassist': guardassist_log(), 'buildbots': buildbots_log(), 'blueprints': blueprints_log()}
    for name, log in cases.items():
        marker = adapters.ADAPTERS[name].marker
        expect(problems_of(name, log) == [], f'{name}: a complete log is valid: {problems_of(name, log)}')
        expect(compare(name, log, log).status == 'MATCH', f'{name} matches itself')
        expect(problems_of(name, '\n'.join(l for l in log.splitlines() if marker not in l) + '\n'), f'{name}: no done marker')
        expect(problems_of(name, log + 'warning: Error running lua script: boom\n', runs.original_errors), f'{name}: Lua error')
        expect(problems_of(name, log + '[2026-10-22] [error] boom\n'), f'{name}: OpenSupCom error line')
        expect(problems_of(name, '\n'.join(log.splitlines()[:-3]) + '\n'), f'{name}: truncated log')


def test_init():
    text = "local FA_ROOT_LINUX = '/a'\nlocal FA_ROOT_WINE = 'Z:\\\\b'\nx = 1\n"
    out = runs.generate_init(text, "/native/it's", 'C:\\GOG')
    expect("local FA_ROOT_LINUX = '/native/it\\'s'" in out and "local FA_ROOT_WINE = 'C:\\\\GOG'" in out and 'x = 1' in out, out)
    try:
        runs.generate_init('x = 1\n', '/a', 'b')
        raise AssertionError('an init without root lines must be refused')
    except SystemExit:
        pass


@contextlib.contextmanager
def scratch_store():
    saved = (store.PARITY, store.REFS, dict(store.AREAS))
    with tempfile.TemporaryDirectory() as tmp:
        store.PARITY, store.REFS = os.path.join(tmp, 'parity'), os.path.join(tmp, 'parity', 'refs')
        store.AREAS.update({'refs': store.REFS, 'traces': os.path.join(tmp, 'corpus')})
        try:
            yield tmp
        finally:
            store.PARITY, store.REFS = saved[0], saved[1]
            store.AREAS.clear()
            store.AREAS.update(saved[2])


def test_manifests_and_backup():
    with scratch_store() as tmp:
        corpus = store.AREAS['traces']
        os.makedirs(os.path.join(corpus, 'sub'))
        for name, text in (('a.log', 'one'), ('sub/b.log', 'two')):
            with open(os.path.join(corpus, name), 'w') as f:
                f.write(text)
        expect(store.update_manifest('traces') == (['a.log', 'sub/b.log'], []), 'manifest lists the files')
        expect(store.verify_area('traces') == (2, []), 'fresh manifest verifies')
        dest = os.path.join(tmp, 'backup')
        expect(store.backup('traces', dest) == (2, []), 'backup copies and verifies')
        expect(store.verify_area('traces', dest) == (2, []), 'the backup verifies')
        expect(store.backup('traces', dest) == (0, []), 'a second backup copies nothing')
        with open(os.path.join(corpus, 'new.log'), 'w') as f:
            f.write('three')
        expect(store.verify_area('traces')[1] == ['not in the manifest: new.log'], 'an unlisted file is reported')
        expect(store.backup('traces', dest) == (1, []), 'a new file is added then copied')
        os.chmod(os.path.join(dest, 'traces', 'a.log'), 0o644)
        with open(os.path.join(dest, 'traces', 'a.log'), 'w') as f:
            f.write('tampered')
        expect(store.verify_area('traces', dest)[1] == ['changed: a.log'], 'a damaged backup fails verify')
        expect(store.backup('traces', dest)[1][0].startswith('refusing to overwrite'), 'backup never overwrites')
        with open(os.path.join(corpus, 'a.log'), 'w') as f:
            f.write('edited')
        expect(store.update_manifest('traces')[1] == ['changed: a.log'], 'a changed original is a problem, not a new entry')


GAME = {'exe': 'e' * 64, 'scd': {'gamedata/a.scd': 'a' * 64}}
INIT = "local FA_ROOT_LINUX = '/x'\nlocal FA_ROOT_WINE = 'Z:\\\\x'\n"
HOOK = 'probe hook\n'


def make_run(tmp, probe, run, text, game=GAME, hook=HOOK, setup_hook=None, setup_dir=''):
    """A finished capture as parity capture leaves it, stored through the same store_capture."""
    work = os.path.join(tmp, 'work', f'{probe}-{run}')
    package = os.path.join(work, 'package')
    hook_path = os.path.join(package, 'probe', 'hooks', 'h.lua')
    os.makedirs(os.path.dirname(hook_path))
    files = {'probe/init_probes.lua': INIT, 'probe/hooks/h.lua': hook, 'init.lua': INIT + '-- generated\n'}
    for rel, body in files.items():
        with open(os.path.join(package, rel), 'w') as f:
            f.write(body)
    blobs = {rel[6:]: store.git_blob(os.path.join(package, rel)) for rel in files if rel.startswith('probe/')}
    name = f'{probe}-{run}'
    with open(os.path.join(work, f'{name}.log'), 'w') as f:
        f.write(text)
    stage = {'stage/init.lua': store.sha256(os.path.join(package, 'init.lua')),
             'stage/hooks/h.lua': store.sha256(hook_path) if setup_hook is None else setup_hook}
    store.write_json(os.path.join(work, f'{name}.setup'), {'log': f'{setup_dir}{name}.log', 'hashes': stage})
    pin = {'git_head': 'h', 'last_change': 'c', 'folder': f'tools/moho_probes/{probe}', 'blobs': blobs}
    return runs.store_capture(adapters.ADAPTERS[probe], probe, run, work, pin, game)


def damage(path, text='damaged'):
    if os.path.exists(path):
        os.chmod(path, 0o644)
    with open(path, 'w') as f:
        f.write(text)


def test_repeat_rule():
    """One run twice, or two runs of different experiments, never make a baseline; a damaged run never serves."""
    adapter = adapters.ADAPTERS['timing']
    with scratch_store() as tmp:
        folder, problems = make_run(tmp, 'timing', 'r1', timing_log())
        expect(folder and not problems, (folder, problems))
        expect(runs.open_run('timing', 'r1').problems == [] and runs.load_run(adapter, 'timing', 'r1').problems == [], 'a stored run loads')
        expect(runs.settle(adapter, 'timing') is None and store.baseline('timing') is None, 'one run cannot repeat itself')
        make_run(tmp, 'timing', 'old', timing_log(), setup_dir='/gone/staging/timing-old/')
        expect(runs.open_run('timing', 'old').problems == [], 'a .setup naming the deleted staging folder still resolves in its package')
        store.add_decision('timing', 'baseline', {'run': 'r1', 'repeat': 'r1'})
        expect(runs.reference(adapter, 'timing')[1] == ['the baseline and its repeat are the same run'], 'a forged self-repeat')
    with scratch_store() as tmp:
        make_run(tmp, 'timing', 'r1', timing_log())
        make_run(tmp, 'timing', 'r2', timing_log(), game={**GAME, 'exe': 'f' * 64})
        make_run(tmp, 'timing', 'r3', timing_log(), hook='another hook\n')
        make_run(tmp, 'timing', 'r4', timing_log().replace('timing done', ''))
        expect(runs.settle(adapter, 'timing') is None, 'another executable, another source package or an incomplete log: no repeat')
        make_run(tmp, 'timing', 'r5', timing_log())
        decision = runs.settle(adapter, 'timing')
        expect(decision and store.baseline('timing')['run'] == 'r1' and store.baseline('timing')['repeat'] == 'r5', 'two matching captures')
        base, problems = runs.reference(adapter, 'timing')
        expect(base.run == 'r1' and not problems, problems)
        expect(runs.survey('timing')[:2] == ([], 'r1'), 'list sees undamaged runs, an incomplete one among them, and the baseline')
    with scratch_store() as tmp:
        make_run(tmp, 'timing', 'r1', timing_log())
        make_run(tmp, 'timing', 'r2', timing_log().replace('progress=0.0300', 'progress=0.0301'))
        expect(runs.settle(adapter, 'timing') is None, 'two captures that differ make no baseline')
        expect(make_run(tmp, 'timing', 'r3', timing_log(), game=GAME)[0] and runs.settle(adapter, 'timing'), 'the third matches the first')
        expect(make_run(tmp, 'timing', 'r9', timing_log() + 'warning: Error running lua script: boom\n')[0] is None,
               'a capture with a Lua error is not stored')


def test_damaged_reference():
    """A stored log, source file, init or record that changed, or a package that is not what ran, fails on read."""
    adapter = adapters.ADAPTERS['timing']
    for what in ('log', 'hook', 'init', 'record', 'setup', 'extra source', 'setup hashes'):
        with scratch_store() as tmp:
            make_run(tmp, 'timing', 'r1', timing_log(), setup_hook='0' * 64 if what == 'setup hashes' else None)
            make_run(tmp, 'timing', 'r2', timing_log())
            if what == 'setup hashes':
                expect(runs.settle(adapter, 'timing') is None, 'setup hashes: the package is not what ran')
                expect(any('differs' in p or 'than what ran' in p for p in runs.open_run('timing', 'r1').problems), 'setup hashes')
                continue
            expect(runs.settle(adapter, 'timing'), 'baseline')
            folder = store.run_dir('timing', 'r1')
            target = {'log': 'timing-r1.log', 'hook': 'probe/hooks/h.lua', 'init': 'init.lua', 'record': 'record.json',
                      'setup': 'timing-r1.setup', 'extra source': 'probe/extra.lua'}[what]
            damage(os.path.join(folder, target), HOOK if what == 'extra source' else 'damaged')
            status, summary = runs.check(adapter, 'timing', os.path.join(tmp, 'no-such-tree'))
            expect(status == 'INVALID' and 'stored reference cannot be used' in summary, f'{what}: {status} {summary}')
            expect(runs.survey('timing')[0], f'{what}: list reports it')


def test_check_exit_codes():
    """check's exit status: a gated or named DIFFERS fails, an ungated one under --all does not, INVALID is 2."""
    here = os.path.dirname(os.path.abspath(__file__))
    loader = importlib.machinery.SourceFileLoader('parity_cli', os.path.join(here, 'parity'))
    cli = importlib.util.module_from_spec(importlib.util.spec_from_loader('parity_cli', loader))
    loader.exec_module(cli)
    saved = (runs.check, store.probes, store.gate)
    outcomes = {}
    runs.check = lambda adapter, probe, root: (outcomes[probe], probe)
    cli.adapter_for = lambda probe: None
    store.probes = lambda: sorted(outcomes)

    def code(args, gated=(), **states):
        outcomes.clear()
        outcomes.update(states)
        store.gate = lambda probe: {'baseline': 'r'} if probe in gated else None
        with contextlib.redirect_stdout(io.StringIO()):
            return cli.cmd_check(list(args))
    try:
        cases = ((['a'], (), {'a': 'MATCH'}, 0), (['a'], (), {'a': 'DIFFERS'}, 1), (['a'], (), {'a': 'INVALID'}, 2),
                 (['a'], (), {'a': 'NO-REF'}, 1), (['--all'], (), {'a': 'DIFFERS', 'b': 'NO-REF', 'c': 'MATCH'}, 0),
                 (['--all'], ('a',), {'a': 'DIFFERS', 'b': 'MATCH'}, 1), (['--all'], (), {'a': 'MATCH', 'b': 'INVALID'}, 2),
                 (['--ratchet'], ('a',), {'a': 'MATCH', 'b': 'DIFFERS'}, 0), (['--ratchet'], ('b',), {'a': 'MATCH', 'b': 'DIFFERS'}, 1),
                 (['--ratchet'], (), {'a': 'DIFFERS'}, 0))
        for args, gated, states, expected in cases:
            expect(code(args, gated, **states) == expected, f'check {args} gated {gated} {states}: expected {expected}')
    finally:
        runs.check, store.probes, store.gate = saved


def stub_tree(tmp, name):
    """A second tree root whose OpenSupCom prints the log named by $STUB_LOG."""
    root = os.path.join(tmp, name)
    binary = os.path.join(root, 'build', 'play', 'opensupcom')
    os.makedirs(os.path.dirname(binary))
    with open(binary, 'w') as f:
        f.write('#!/bin/sh\nwhile [ $# -gt 0 ]; do [ "$1" = --log ] && log=$2; shift; done\ncp "$STUB_LOG" "$log"\n')
    os.chmod(binary, os.stat(binary).st_mode | stat.S_IXUSR)
    return root


def test_check_against_another_root():
    """The step prove runs, against a tree other than this one: MATCH gates, a divergence fails, a missing build is refused."""
    adapter = adapters.ADAPTERS['timing']
    with scratch_store() as tmp:
        for run in ('r1', 'r2'):
            make_run(tmp, 'timing', run, timing_log())
        runs.settle(adapter, 'timing')
        root = stub_tree(tmp, 'other-tree')
        good, bad = os.path.join(tmp, 'good.log'), os.path.join(tmp, 'bad.log')
        for path, text in ((good, timing_log()), (bad, timing_log().replace('progress=0.0300', 'progress=0.0301'))):
            with open(path, 'w') as f:
                f.write(text)
        old = os.environ.get('STUB_LOG')
        try:
            expect(store.gate('timing') is None, 'not gated before the first MATCH')
            os.environ['STUB_LOG'] = good
            status, summary = runs.check(adapter, 'timing', root)
            expect(status == 'MATCH' and store.gate('timing'), f'{status} {summary}')
            os.environ['STUB_LOG'] = bad
            status, summary = runs.check(adapter, 'timing', root)
            expect(status == 'DIFFERS' and 'scene=factory phase=start tick=3 field=progress' in summary, f'{status} {summary}')
            expect(os.path.exists(os.path.join(store.PARITY, 'runs', 'timing', 'latest', 'record.json')), 'the divergent run is kept')
            try:
                runs.check(adapter, 'timing', os.path.join(tmp, 'unbuilt'))
                raise AssertionError('a tree without a build must be refused')
            except SystemExit:
                pass
        finally:
            if old is None:
                os.environ.pop('STUB_LOG', None)
            else:
                os.environ['STUB_LOG'] = old
        expect(runs.survey('timing')[0] == [], 'the store is untouched but for the gate')


def run():
    for test in (test_core, test_compare_demands_a_complete_run, test_blueprint_values, test_engineer_and_crowd,
                 test_guardassist, test_buildbots, test_valid_logs, test_init, test_manifests_and_backup, test_repeat_rule, test_damaged_reference,
                 test_check_exit_codes, test_check_against_another_root):
        test()
    print('parity self-test passed')
