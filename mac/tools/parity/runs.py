"""Runs: a capture of the original becomes a stored run, an OpenSupCom run becomes a record, and both are judged on read.

A stored run is trusted only through open_run/load_run: its files match the refs manifest, its source package
(init.lua and probe/) matches the hashes recorded when it ran, and its log is a complete run of the probe (done
marker, every expected row, no Lua error). The baseline and the gate are consequences: capture records the
baseline when two distinct valid captures of one experiment MATCH; check gates a probe on its first MATCH.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field

import core
import store

TREE = os.path.dirname(store.TOOLKIT)
SOURCES = os.path.join(TREE, 'tools', 'moho_probes')
MAP = '/maps/SCMP_009/SCMP_009_scenario.lua'
OSC_ERRORS = re.compile(r'\[(error|critical)\]|\[warning\].*(error|failed|exception)|stack traceback|Unknown unit type', re.I)
UNSTAGED = ('init_probes.lua', '.DS_Store', '__pycache__')

sys.path.insert(0, os.path.join(store.TOOLKIT, 'tools', 'lib'))
import capture  # noqa: E402


def osc_errors(text):
    return [line.strip() for line in text.splitlines() if OSC_ERRORS.search(line)]


def original_errors(text):
    return capture.lua_errors(text, ['Unable to reset selection sets'])


def read(path, encoding='latin-1'):
    with open(path, encoding=encoding, errors='replace') as f:
        return f.read()


def git(*args, cwd=TREE):
    return subprocess.run(('git',) + args, cwd=cwd, capture_output=True, text=True).stdout.strip()


def run_id():
    return time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())


def probe_files(folder):
    return sorted(os.path.relpath(os.path.join(r, n), folder) for r, _, ns in os.walk(folder)
                  for n in ns if n != '.DS_Store' and '__pycache__' not in r)


def staged(rel):
    return os.path.basename(rel) not in UNSTAGED and not rel.endswith('.py')


def lua_string(text):
    return "'" + text.replace('\\', '\\\\').replace("'", "\\'") + "'"


def wine_path(native):
    """A folder of the bottle as the game sees it (C:\\...)."""
    rel = os.path.relpath(native, store.BOTTLE)
    if rel.startswith('..'):
        raise SystemExit(f'parity: {native} is not inside the bottle {store.BOTTLE}')
    return 'C:\\' + rel.replace('/', '\\')


def generate_init(text, native_root, wine_root):
    """The probe's own init with both game roots replaced."""
    for name, value in (('FA_ROOT_LINUX', native_root), ('FA_ROOT_WINE', wine_root)):
        text, n = re.subn(rf'(?m)^local {name} = .*$', lambda m: f'local {name} = {lua_string(value)}', text)
        if n != 1:
            raise SystemExit(f'parity: the probe init has no single "local {name} = ..." line')
    return text


def stage(probe_dir, init_text, dest):
    """dest/init.lua (init_text) and the probe's hooks and other shipped files from probe_dir."""
    os.makedirs(dest)
    with open(os.path.join(dest, 'init.lua'), 'w') as f:
        f.write(init_text)
    for rel in probe_files(probe_dir):
        if staged(rel):
            os.makedirs(os.path.dirname(os.path.join(dest, rel)), exist_ok=True)
            shutil.copyfile(os.path.join(probe_dir, rel), os.path.join(dest, rel))


def freeze(probe, package):
    """Copy the probe's committed sources into package/probe and generate package/init.lua from that copy.
    Returns the pin: the revision and every frozen file's git blob id. Staging derives from the package."""
    folder = os.path.join(SOURCES, probe)
    if not os.path.isdir(folder):
        raise SystemExit(f'parity: no probe folder {folder}')
    rel = os.path.relpath(folder, TREE)
    if git('status', '--porcelain', '--', rel):
        raise SystemExit(f'parity: {rel} has uncommitted changes; pin sources only from a committed tree')
    frozen = os.path.join(package, 'probe')
    os.makedirs(package)
    shutil.copytree(folder, frozen, ignore=shutil.ignore_patterns('.DS_Store', '__pycache__'))
    with open(os.path.join(package, 'init.lua'), 'w') as f:
        f.write(generate_init(read(os.path.join(frozen, 'init_probes.lua')), store.NATIVE_GAME, wine_path(store.ORIGINAL_GAME)))
    return {'git_head': git('rev-parse', 'HEAD'), 'last_change': git('log', '-1', '--format=%H', '--', rel), 'folder': rel,
            'blobs': {f: store.git_blob(os.path.join(frozen, f)) for f in probe_files(frozen)}}


@dataclass
class Run:
    probe: str
    run: str
    files: dict = field(default_factory=dict)
    record: dict = field(default_factory=dict)
    setup: dict = field(default_factory=dict)
    text: str = ''
    problems: list = field(default_factory=list)

    def log(self, name):
        return core.Log(name, self.text, original_errors)

    def package(self):
        """The source package as {rel: sha256}: the generated init and every shipped probe file."""
        return {r: e['sha256'] for r, e in self.files.items() if r == 'init.lua' or r.startswith('probe/')}

    def experiment(self):
        """What two runs must share to be repeats of each other."""
        return (self.record.get('executable_sha256'), self.record.get('game_data_scd_sha256'), self.record.get('contract'),
                self.package())


def package_problems(run):
    """Why the stored source package is not the one that ran, from the hashes recorded at capture time."""
    sha = lambda rel: run.files.get(rel, {}).get('sha256')
    record, bad = run.record, []
    for what, rel, key in (('log', record['log'], 'log_sha256'), ('init.lua', 'init.lua', 'init_sha256')):
        if sha(rel) != record[key]:
            bad.append(f'{what} does not match the checksum in record.json')
    if os.path.basename(run.setup.get('log', '')) != record['log']:
        bad.append('.setup names another log than record.json')
    shipped = {r[len('probe/'):] for r in run.files if r.startswith('probe/')}
    pinned = record['sources']['blobs']
    for rel in sorted(shipped | set(pinned)):
        if rel not in shipped:
            bad.append(f'probe/{rel} is missing from the package')
        elif rel not in pinned:
            bad.append(f'probe/{rel} is not in the pinned sources')
        elif store.git_blob(os.path.join(store.run_dir(run.probe, run.run), 'probe', rel)) != pinned[rel]:
            bad.append(f'probe/{rel} differs from the pinned source')
    ran = {k[len('stage/'):]: v for k, v in run.setup.get('hashes', {}).items() if k.startswith('stage/')}
    here = {'init.lua': sha('init.lua'), **{rel: sha(f'probe/{rel}') for rel in shipped if staged(rel)}}
    bad += [f'{rel}: the package holds {"nothing" if not here.get(rel) else "other content"} than what ran (.setup)'
            for rel in sorted(set(ran) | set(here)) if ran.get(rel) != here.get(rel)]
    return bad


def open_run(probe, run):
    """A stored run with its files, record and source package checked. .problems says what is wrong with it."""
    problems, files = store.verify_run(probe, run)
    out = Run(probe, run, files=files, problems=problems)
    folder = store.run_dir(probe, run)
    try:
        out.record = store.read_json(os.path.join(folder, 'record.json'))
        out.setup = store.read_json(os.path.join(folder, os.path.basename(out.record['log'])[:-len('.log')] + '.setup'))
        out.text = read(os.path.join(folder, out.record['log']))
        out.problems += package_problems(out)
    except (OSError, ValueError, KeyError) as e:
        out.problems.append(f'cannot be read: {type(e).__name__}: {e}')
    return out


def load_run(adapter, probe, run):
    """open_run plus completeness: the log is a whole run of the probe with no Lua error."""
    out = open_run(probe, run)
    if out.text:
        out.problems += core.inspect(adapter, out.log('original')).problems
    return out


def baseline_problems(chosen, get):
    """Why a baseline decision no longer holds: its two runs must be distinct and of one experiment."""
    if chosen['run'] == chosen['repeat']:
        return ['the baseline and its repeat are the same run']
    first, second = get(chosen['run']), get(chosen['repeat'])
    if first.experiment() != second.experiment():
        return [f'baseline runs {first.run} and {second.run} are not of one experiment']
    return []


def reference(adapter, probe):
    """(baseline Run, problems). (None, []) when the probe has no baseline; otherwise the run is complete and verified."""
    chosen = store.baseline(probe)
    if not chosen:
        return None, []
    base = load_run(adapter, probe, chosen['run'])
    opened = {chosen['run']: base, chosen['repeat']: open_run(probe, chosen['repeat'])}
    problems = [f'run {r.run}: {p}' for r in opened.values() for p in r.problems]
    return base, problems or baseline_problems(chosen, opened.__getitem__)


def survey(probe):
    """(problems, baseline run id, gated): every stored run opened and the probe's decisions checked."""
    opened = {i: open_run(probe, i) for i in store.run_ids(probe)}
    problems = [f'run {r.run}: {p}' for r in opened.values() for p in r.problems]
    chosen = store.baseline(probe)
    if chosen:
        if {chosen['run'], chosen['repeat']} <= set(opened):
            problems += baseline_problems(chosen, opened.__getitem__)
        else:
            problems.append('the baseline names a run that is not stored')
    return problems, chosen['run'] if chosen else None, bool(store.gate(probe)), len(opened)


def settle(adapter, probe):
    """Record the baseline when two distinct valid runs of one experiment MATCH. Returns the decision file or None."""
    if store.baseline(probe):
        return None
    valid = [r for r in (load_run(adapter, probe, i) for i in store.run_ids(probe)) if not r.problems]
    for i, first in enumerate(valid):
        for second in valid[i + 1:]:
            if first.experiment() == second.experiment():
                result = core.compare(adapter, first.log('run'), second.log('repeat'))
                if result.status == 'MATCH':
                    return store.add_decision(probe, 'baseline', {'run': first.run, 'repeat': second.run,
                                                                   'repeatability': result.summary})[0]
    return None


def store_capture(adapter, probe, run, work, pin, game):
    """Move a finished capture (work/package plus work/PROBE-RUN.log and .setup) into the store.
    Returns (run folder, problems); a log with a Lua error is not stored and stays in work."""
    name = f'{probe}-{run}'
    text = read(os.path.join(work, f'{name}.log'))
    if errors := original_errors(text):
        return None, [f'Lua error: {errors[0][:160]}']
    package = os.path.join(work, 'package')
    for kept in (f'{name}.log', f'{name}.setup'):
        shutil.move(os.path.join(work, kept), package)
    record = {'run': run, 'probe': probe, 'kind': 'original', 'captured': store.now(), 'contract': adapter.contract(),
              'log': f'{name}.log', 'log_sha256': store.sha256(os.path.join(package, f'{name}.log')),
              'executable_sha256': game['exe'], 'game_data_scd_sha256': game['scd'],
              'init_sha256': store.sha256(os.path.join(package, 'init.lua')), 'sources': pin,
              'toolkit_head': git('rev-parse', 'HEAD'),
              'completion': {'marker': 'PROBE ' + adapter.marker, 'expected_rows': len(adapter.expected()),
                             'counts': core.counts(adapter, core.parse_log(adapter, text))}}
    store.write_json(os.path.join(package, 'record.json'), record)
    target, problems = store.commit_run(probe, package, run)
    return target, problems


def capture_original(adapter, probe):
    """Run the probe on the original and store it. Returns (run folder or None, problems, work folder)."""
    run = run_id()
    work = os.path.join(store.PARITY, 'staging', f'{probe}-{run}')
    pin = freeze(probe, os.path.join(work, 'package'))
    scratch = tempfile.mkdtemp(prefix='parity-stage-')
    log = os.path.join(work, f'{probe}-{run}.log')
    stage(os.path.join(work, 'package', 'probe'), read(os.path.join(work, 'package', 'init.lua')), os.path.join(scratch, 'stage'))
    watch = os.path.join(work, 'watch.log')
    print(f'watch: {watch}', flush=True)
    cmd = [os.path.join(os.path.dirname(os.path.abspath(__file__)), 'capture'), os.path.join(scratch, 'stage'), log,
           'PROBE ' + adapter.marker, str(adapter.original_timeout), *adapter.original_args]
    code = subprocess.run(cmd, cwd=store.TOOLKIT, env={**os.environ, 'GAME_RUN_WATCH': watch}).returncode
    shutil.rmtree(scratch)
    if code or not os.path.exists(log):
        return None, [f'the capture script exited {code} and left {log}.partial'], work
    target, problems = store_capture(adapter, probe, run, work, pin, store.identity(store.ORIGINAL_GAME))
    return target, problems, work


def osc_env(root):
    out = subprocess.run(['bash', '-c', f'source {store.TOOLKIT}/recipe/env.sh && env -0'], cwd=root,
                         capture_output=True, text=True).stdout
    return {**dict(line.split('=', 1) for line in out.split('\0') if '=' in line), 'OSC_ROOT': root}


def run_osc(adapter, probe, probe_dir, root, out_dir):
    """Run the probe headless on root's build, with probe_dir's sources. Returns (log path or None, record, problems)."""
    binary = os.path.join(root, 'build', 'play', 'opensupcom')
    if not os.path.exists(binary):
        raise SystemExit(f'parity: {binary} is missing; build the tree first')
    env = osc_env(root)
    fa = env['OSC_FA_PATH']
    work = tempfile.mkdtemp(prefix='stage-', dir=out_dir)
    init = generate_init(read(os.path.join(probe_dir, 'init_probes.lua')), fa, wine_path(store.ORIGINAL_GAME))
    stage(probe_dir, init, os.path.join(work, 'stage'))
    log = os.path.join(out_dir, f'{probe}-osc.log')
    cmd = [binary, '--init', os.path.join(work, 'stage', 'init.lua'), '--fa-path', fa, '--map', MAP, '--ticks',
           str(adapter.osc_ticks), '--user-dir', os.path.join(work, 'user'), '--log', log, *adapter.osc_args]
    started = time.time()
    try:
        proc = subprocess.run(cmd, cwd=root, env=env, capture_output=True, text=True, timeout=adapter.osc_timeout)
        code, tail = proc.returncode, (proc.stdout + proc.stderr)[-300:]
    except subprocess.TimeoutExpired:
        code, tail = 'timeout', ''
    shutil.rmtree(work)
    if not os.path.exists(log):
        return None, {}, [f'OpenSupCom exited {code} and wrote no log: {tail}']
    text = read(log, 'utf-8')
    parsed = core.inspect(adapter, core.Log('opensupcom', text, osc_errors))
    problems = ([f'OpenSupCom exited {code}'] if code != 0 else []) + parsed.problems
    st = os.stat(binary)
    try:
        data = store.identity(fa)
    except OSError:
        data = None
    record = {'probe': probe, 'at': store.now(), 'root': root, 'git_head': git('rev-parse', 'HEAD', cwd=root),
              'src_dirty': bool(git('status', '--porcelain', '--', 'src', cwd=root)),
              'binary': {'bytes': st.st_size, 'mtime': int(st.st_mtime), 'sha256': store.sha256(binary)},
              'build_older_than_head': st.st_mtime < int(git('log', '-1', '--format=%ct', cwd=root) or 0),
              'fa_path': fa, 'game': data, 'args': cmd[1:], 'seconds': round(time.time() - started, 1),
              'log_sha256': store.sha256(log), 'counts': core.counts(adapter, parsed)}
    return log, record, problems


def keep(probe, out_dir):
    """Publish an OpenSupCom run's folder as the probe's one latest slot, replacing the previous one."""
    slot = os.path.join(store.PARITY, 'runs', probe, 'latest')
    os.makedirs(os.path.dirname(slot), exist_ok=True)
    shutil.rmtree(slot, ignore_errors=True)
    shutil.move(out_dir, slot)
    return slot


def sources_for(probe, base):
    """The probe folder to run: the baseline's frozen package, or the tree's own where there is no baseline."""
    return (os.path.join(store.run_dir(probe, base.run), 'probe'), f'frozen in run {base.run}') if base \
        else (os.path.join(SOURCES, probe), 'the tree (no baseline yet)')


def run_probe(adapter, probe, root, base, tree=False):
    """Run the probe on OpenSupCom with the baseline's frozen sources (or the tree's). Returns (log, record, problems,
    folder); the caller keeps or removes the folder."""
    folder, where = (os.path.join(SOURCES, probe), 'the tree') if tree else sources_for(probe, base)
    out = tempfile.mkdtemp(prefix=f'parity-{probe}-')
    log, record, problems = run_osc(adapter, probe, folder, root, out)
    record['sources'] = where
    if log:
        store.write_json(os.path.join(out, 'record.json'), record)
    return log, record, problems, out


def check(adapter, probe, root):
    """(status, summary) of OpenSupCom at root against the probe's baseline. A first MATCH gates the probe."""
    base, problems = reference(adapter, probe)
    if problems:
        return 'INVALID', f'{probe}: the stored reference cannot be used: {problems[0]}'
    if not base:
        return 'NO-REF', f'{probe}: no baseline'
    log, record, problems, out = run_probe(adapter, probe, root, base)
    if problems:
        return 'INVALID', f'{probe}: {problems[0]} (run kept in {keep(probe, out)})'
    result = core.compare(adapter, base.log('original'), core.Log('opensupcom', read(log, 'utf-8'), osc_errors))
    if result.status == 'MATCH':
        shutil.rmtree(out)
        if not store.gate(probe):
            store.add_decision(probe, 'gate', {'baseline': base.run, 'result': result.summary,
                                               'git_head': git('rev-parse', 'HEAD', cwd=root)})
        return 'MATCH', result.summary
    return result.status, f'{result.summary} (run kept in {keep(probe, out)})'
