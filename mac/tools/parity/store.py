"""The reference store: stored runs of the original, their decisions, manifests and the identities they tie to.

mac/work/parity/refs/PROBE/RUN_ID/ holds one immutable capture: log, .setup manifest, the frozen source package
(init.lua and probe/), record.json. Decisions about a probe (its baseline, its gate) are append-only files in
refs/PROBE/decisions/, so a run's files never change. A manifest (work/parity/manifests/AREA.json) lists the
sha256 of every file of an area (`refs`, and the older corpus `traces`). Nothing here overwrites a stored file.
"""
import fcntl
import hashlib
import json
import os
import shutil
import stat
import time

TOOLKIT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PARITY = os.path.join(TOOLKIT, 'work', 'parity')
REFS = os.path.join(PARITY, 'refs')
AREAS = {'refs': REFS, 'traces': os.path.join(TOOLKIT, 'work', 'traces')}
BOTTLE = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'CrossOver', 'Bottles',
                      os.environ.get('FAF_BOTTLE', 'SupCom'), 'drive_c')
NATIVE_GAME = os.environ.get('OSC_FA_PATH') or os.path.join(TOOLKIT, 'work', 'game')
ORIGINAL_GAME = os.path.join(BOTTLE, 'GOG Games', 'Supreme Commander Forged Alliance')


def now():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def git_blob(path):
    """The id git gives a file's content."""
    with open(path, 'rb') as f:
        data = f.read()
    return hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest()


def write_json(path, data, new=False):
    with open(path, 'x' if new else 'w') as f:
        json.dump(data, f, indent=1, sort_keys=True)
        f.write('\n')


def read_json(path):
    with open(path) as f:
        return json.load(f)


def lock_down(tree):
    for root, _, files in os.walk(tree):
        for name in files:
            path = os.path.join(root, name)
            os.chmod(path, os.stat(path).st_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))


def identity(game_dir, cache_path=os.path.join(PARITY, 'identity-cache.json')):
    """The executable's sha256 and the .scd hashes of a game folder; hashes are cached by size and mtime."""
    try:
        cache = read_json(cache_path)
    except (OSError, ValueError):
        cache = {}
    files = [os.path.join('bin', 'SupremeCommander.exe')]
    scd = os.path.join(game_dir, 'gamedata')
    files += sorted(os.path.join('gamedata', n) for n in os.listdir(scd) if n.lower().endswith('.scd'))
    out = {}
    for rel in files:
        path = os.path.join(game_dir, rel)
        st = os.stat(path)
        key = f'{os.path.realpath(path)}|{st.st_size}|{int(st.st_mtime)}'
        if key not in cache:
            cache[key] = sha256(path)
        out[rel] = cache[key]
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    write_json(cache_path, cache)
    return {'exe': out.pop(files[0]), 'scd': out}


def manifest_path(area):
    return os.path.join(PARITY, 'manifests', f'{area}.json')


def scan(tree):
    """{relative path: {sha256, bytes}} of every file under tree, and the entries that are not plain files."""
    files, odd = {}, []
    for root, dirs, names in os.walk(tree):
        dirs.sort()
        for name in sorted(names):
            path = os.path.join(root, name)
            rel = os.path.relpath(path, tree)
            if os.path.islink(path) or not os.path.isfile(path):
                odd.append(rel)
            else:
                files[rel] = {'sha256': sha256(path), 'bytes': os.path.getsize(path)}
    return files, odd


def update_manifest(area):
    """List the area's new files in its manifest; report listed files that changed or vanished. Never edits an entry."""
    os.makedirs(PARITY, exist_ok=True)
    with open(os.path.join(PARITY, '.manifest.lock'), 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        path = manifest_path(area)
        manifest = read_json(path) if os.path.exists(path) else {'area': area, 'created': now(), 'files': {}}
        files, odd = scan(AREAS[area])
        problems = [f'not a plain file: {r}' for r in odd]
        problems += [f'changed: {r}' for r in manifest['files'] if r in files and files[r] != manifest['files'][r]]
        problems += [f'missing: {r}' for r in manifest['files'] if r not in files]
        added = sorted(set(files) - set(manifest['files']))
        if not problems and added:
            manifest['files'].update({r: files[r] for r in added})
            manifest['updated'] = now()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            write_json(path, manifest)
        return added, problems


def verify(tree, listed):
    """Problems of tree against listed ({rel: entry}): changed, missing, unlisted and not plain files; and the scan."""
    files, odd = scan(tree)
    problems = [f'not a plain file: {r}' for r in odd]
    problems += [f'missing: {r}' if r not in files else f'changed: {r}' for r, e in listed.items() if files.get(r) != e]
    problems += [f'not in the manifest: {r}' for r in sorted(set(files) - set(listed))]
    return problems, files


def verify_area(area, root=None):
    """Verify an area in place, or its backup under root (root/AREA with root/AREA.manifest.json)."""
    tree, path = (os.path.join(root, area), os.path.join(root, f'{area}.manifest.json')) if root \
        else (AREAS[area], manifest_path(area))
    if not os.path.exists(path):
        return None, [f'no manifest for {area} ({path})']
    listed = read_json(path)['files']
    return len(listed), verify(tree, listed)[0]


def backup(area, dest):
    """Copy an area's files to dest/AREA (never over a different file), then verify the copy by checksum."""
    _, problems = update_manifest(area)
    if problems:
        return 0, problems
    listed = read_json(manifest_path(area))['files']
    copied = 0
    for rel, entry in listed.items():
        src, out = os.path.join(AREAS[area], rel), os.path.join(dest, area, rel)
        if os.path.exists(out):
            if sha256(out) != entry['sha256']:
                return copied, [f'refusing to overwrite a different file: {out}']
            continue
        os.makedirs(os.path.dirname(out), exist_ok=True)
        shutil.copy2(src, out + '.partial')
        os.replace(out + '.partial', out)
        copied += 1
    shutil.copyfile(manifest_path(area), os.path.join(dest, f'{area}.manifest.json'))
    return copied, verify_area(area, dest)[1]


def probes():
    return sorted(d for d in os.listdir(REFS) if os.path.isdir(os.path.join(REFS, d))) if os.path.isdir(REFS) else []


def run_dir(probe, run):
    return os.path.join(REFS, probe, run)


def run_ids(probe):
    base = os.path.join(REFS, probe)
    return sorted(d for d in os.listdir(base) if d != 'decisions' and os.path.isdir(os.path.join(base, d)))


def verify_run(probe, run):
    """(problems, {rel: entry}) of a stored run's files against the refs manifest: every file listed and unchanged."""
    path = manifest_path('refs')
    if not os.path.exists(path):
        return [f'no refs manifest ({path})'], {}
    prefix = f'{probe}/{run}/'
    listed = {r[len(prefix):]: e for r, e in read_json(path)['files'].items() if r.startswith(prefix)}
    if not listed:
        return [f'run {run} of {probe} is not in the refs manifest'], {}
    return verify(run_dir(probe, run), listed)


def commit_run(probe, package, run):
    """Move a finished package into the store, read-only and listed in the manifest."""
    target = run_dir(probe, run)
    if os.path.exists(target):
        raise SystemExit(f'parity: {target} exists; a stored run is never replaced')
    os.makedirs(os.path.dirname(target), exist_ok=True)
    shutil.move(package, target)
    lock_down(target)
    return target, update_manifest('refs')[1]


def add_decision(probe, kind, data):
    folder = os.path.join(REFS, probe, 'decisions')
    os.makedirs(folder, exist_ok=True)
    stamp = time.time_ns()
    path = os.path.join(folder, f'{time.strftime("%Y%m%dT%H%M%S", time.gmtime(stamp // 10**9))}{stamp % 10**9:09d}Z-{kind}.json')
    write_json(path, {'kind': kind, 'at': now(), **data}, new=True)
    lock_down(folder)
    return path, update_manifest('refs')[1]


def decisions(probe, kind):
    folder = os.path.join(REFS, probe, 'decisions')
    names = sorted(n for n in os.listdir(folder) if n.endswith(f'-{kind}.json')) if os.path.isdir(folder) else []
    return [read_json(os.path.join(folder, n)) for n in names]


def baseline(probe):
    found = decisions(probe, 'baseline')
    return found[-1] if found else None


def gate(probe):
    """The latest gate if it names the current baseline."""
    chosen, gates = baseline(probe), decisions(probe, 'gate')
    return gates[-1] if chosen and gates and gates[-1]['baseline'] == chosen['run'] else None
