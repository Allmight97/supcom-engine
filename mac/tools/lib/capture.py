#!/usr/bin/env python3
"""Preflight checks and setup manifests for tools/lib/game-run.sh.

  capture.py watch LOG STATE [--checkpoint 'TEXT@TICK']... [--allow TEXT]...
      Reads LOG from the offset saved in STATE (JSON) and exits 3 with a reason when the run must stop:
      a Lua error or unknown unit type, a hook the game loaded ("Hooked X with /mount/...") that has not
      logged HOOKCHECK|/mount/...|ok within 90 s, or a checkpoint TEXT not seen once SETUP|TICK reached TICK.
  capture.py setup LOG SNAPSHOT_DIR END EXE CXCONF PREFS WINDOW -- ARGS...
      Writes LOG's manifest to <LOG without .partial>.setup (JSON): arguments, git HEAD and dirty flag, the
      sha256 of every hook and script in SNAPSHOT_DIR, the game executable's path and sha256, the bottle's
      graphics backend (CX_GRAPHICS_BACKEND in CXCONF; "auto" when empty), the render setup (window size and
      the sha256 of PREFS), resolved armies, options, seed, last tick and how the run ended.
  capture.py mods PREFS DOCUMENTS_MODS GAME_MODS_SCD
      Exits 3 naming every mod in PREFS's active_mods that the original game can load (a mod folder in its
      Documents mods folder or in gamedata/mods.scd); mods only FAF has are ignored.
  capture.py --self-test
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import zipfile

HOOK_TIMEOUT = 90
ERRORS = re.compile(r'^warning: Error (running|in file)|Sim::Create\(\) crashed|Unknown unit type')
HOOKED = re.compile(r'Hooked \S+ with (/\w+hook/\S+)')
HOOKCHECK = re.compile(r'HOOKCHECK\|(/\w+hook/\S+?)\|ok')
TICK = re.compile(r'SETUP\|TICK\|(\d+)')


def watch(log, state_path, checkpoints, allows, now=None):
    now = time.time() if now is None else now
    try:
        state = json.load(open(state_path))
    except (OSError, ValueError):
        state = {'offset': 0, 'hooked': {}, 'checked': [], 'tick': 0, 'seen': []}
    with open(log, 'rb') as f:
        f.seek(state['offset'])
        chunk = f.read()
    complete = chunk.rfind(b'\n') + 1
    state['offset'] += complete
    reason = None
    for raw in chunk[:complete].decode('latin-1').splitlines():
        line = raw.strip()
        if ERRORS.search(line) and not any(a in line for a in allows) and reason is None:
            reason = 'error: ' + line[:200]
        m = HOOKED.search(line)
        if m and not m.group(1).lower().startswith('/schook/'):
            state['hooked'].setdefault(m.group(1).lower(), now)
        m = HOOKCHECK.search(line)
        if m and m.group(1).lower() not in state['checked']:
            state['checked'].append(m.group(1).lower())
        m = TICK.search(line)
        if m:
            state['tick'] = max(state['tick'], int(m.group(1)))
        for text, _ in checkpoints:
            if text in line and text not in state['seen']:
                state['seen'].append(text)
    for hook, since in state['hooked'].items():
        if hook not in state['checked'] and now - since > HOOK_TIMEOUT and reason is None:
            reason = 'hook %s loaded but sent no HOOKCHECK within %d s' % (hook, HOOK_TIMEOUT)
    for text, tick in checkpoints:
        if state['tick'] >= tick and text not in state['seen'] and reason is None:
            reason = 'checkpoint: no %r line by tick %d' % (text, tick)
    json.dump(state, open(state_path, 'w'))
    return reason


def sha256(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def backend(conf):
    m = re.search(r'(?m)^"CX_GRAPHICS_BACKEND"\s*=\s*"([^"]*)"', open(conf, encoding='latin-1').read())
    return (m.group(1) if m else '') or 'auto'


def setup(log, snapshot, end, exe, conf, prefs, window, args):
    lines = open(log, encoding='latin-1').read().splitlines()
    armies, options, seed, tick = [], {}, None, 0
    for line in lines:
        at = line.find('SETUP|')
        if at < 0:
            continue
        field = line[at:].strip().split('|')
        if field[1] == 'ARMY':
            armies.append(dict(zip(('index', 'name', 'human', 'ai', 'faction', 'civilian'), field[2:8])))
        elif field[1] == 'SEED':
            seed = field[2]
        elif field[1] == 'OPTIONS':
            options = dict(kv.split('=', 1) for kv in field[2].split(',') if '=' in kv) if len(field) > 2 else {}
        elif field[1] == 'TICK':
            tick = max(tick, int(field[2]))
    hashes = {}
    for root, _, files in os.walk(snapshot):
        for name in sorted(files):
            if name.endswith(('.lua', '.sh', '.py')) or os.access(os.path.join(root, name), os.X_OK):
                path = os.path.join(root, name)
                hashes[os.path.relpath(path, snapshot)] = sha256(path)
    git = lambda *a: subprocess.run(('git',) + a, capture_output=True, text=True).stdout.strip()
    manifest = {
        'log': log.removesuffix('.partial'), 'args': args, 'end': end,
        'git_head': git('rev-parse', 'HEAD'), 'git_dirty': bool(git('status', '--porcelain', '--', 'tools', 'agents')),
        'armies': armies, 'seed': seed, 'options': options, 'last_tick': tick, 'hashes': dict(sorted(hashes.items())),
        'exe': {'path': exe, 'sha256': sha256(exe)}, 'backend': backend(conf),
        'render': {'window': window, 'prefs_sha256': sha256(prefs)},
    }
    target = log.removesuffix('.partial').removesuffix('.log') + '.setup'
    json.dump(manifest, open(target, 'w'), indent=1)
    return target


def loadable_mods(documents, scd):
    uids = {}
    infos = []
    if os.path.isdir(documents):
        for entry in os.listdir(documents):
            path = os.path.join(documents, entry, 'mod_info.lua')
            if os.path.isfile(path):
                infos.append(open(path, encoding='latin-1').read())
    if os.path.isfile(scd):
        z = zipfile.ZipFile(scd)
        infos += [z.read(n).decode('latin-1') for n in z.namelist() if n.lower().endswith('mod_info.lua')]
    for text in infos:
        uid = re.search(r'(?m)^\s*uid\s*=\s*["\']([^"\']+)', text)
        name = re.search(r'(?m)^\s*name\s*=\s*["\']([^"\']+)', text)
        if uid:
            uids[uid.group(1)] = name.group(1) if name else uid.group(1)
    return uids


def active_mods(prefs):
    text = open(prefs, encoding='latin-1').read()
    m = re.search(r'(?m)^active_mods = \{(.*?)\}', text, re.S)
    return re.findall(r"\[\s*'([^']+)'\s*\]\s*=\s*true", m.group(1)) if m else []


def self_test():
    import subprocess
    import tempfile
    d = tempfile.mkdtemp()
    log, state = os.path.join(d, 'x.log'), os.path.join(d, 'state')
    open(log, 'w').write('info: Hooked /lua/a.lua with /refshothook/lua/a.lua\ninfo: SETUP|TICK|100\n')
    assert watch(log, state, [], [], now=0) is None
    assert 'HOOKCHECK' in watch(log, state, [], [], now=100)
    open(log, 'a').write('info: HOOKCHECK|/refshothook/lua/a.lua|ok\ninfo: SETUP|TICK|2500\n')
    assert watch(log, state, [], [], now=100) is None
    assert 'checkpoint' in watch(log, state, [('FIRE ', 2400)], [], now=100)
    open(log, 'a').write('warning: Error running lua script: Unable to reset selection sets\n')
    assert watch(log, state, [], ['Unable to reset selection sets'], now=100) is None
    open(log, 'a').write('warning: Error running lua script: Unknown unit type: uel1101\n')
    assert watch(log, state, [], [], now=100).startswith('error')
    open(log, 'a').write('info: SETUP|ARMY|1|ARMY_1|true||3|false\ninfo: SETUP|SEED|7\ninfo: SETUP|OPTIONS|A=1,B=x\n')
    exe, conf, prefs = (os.path.join(d, n) for n in ('game.exe', 'cxbottle.conf', 'Game.prefs'))
    open(exe, 'wb').write(b'MZ')
    open(conf, 'w').write('"CX_GRAPHICS_BACKEND" = ""\n')
    open(prefs, 'w').write('a = 1\n')
    m = json.load(open(setup(log, d, 'marker', exe, conf, prefs, '1680 1050', ['/map', 'X'])))
    assert m['exe'] == {'path': exe, 'sha256': hashlib.sha256(b'MZ').hexdigest()}
    assert m['backend'] == 'auto' and m['render'] == {'window': '1680 1050', 'prefs_sha256': hashlib.sha256(b'a = 1\n').hexdigest()}
    assert m['armies'][0]['faction'] == '3' and m['seed'] == '7' and m['options'] == {'A': '1', 'B': 'x'}
    assert m['last_tick'] == 2500 and m['end'] == 'marker'
    os.makedirs(os.path.join(d, 'mods', 'm'))
    open(os.path.join(d, 'mods', 'm', 'mod_info.lua'), 'w').write('name = "Mine"\nuid = "u-1"\n')
    open(os.path.join(d, 'prefs'), 'w').write("a = 1\nactive_mods = {\n    ['u-1'] = true,\n    ['faf-only'] = true\n}\n")
    assert active_mods(os.path.join(d, 'prefs')) == ['u-1', 'faf-only']
    assert loadable_mods(os.path.join(d, 'mods'), os.path.join(d, 'none.scd')) == {'u-1': 'Mine'}
    import shutil
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tree = os.path.join(d, 'tree')
    shutil.copytree(here, os.path.join(tree, 'tools'), ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(os.path.join(os.path.dirname(here), 'agents', 'faf-autorun'), os.path.join(tree, 'agents', 'faf-autorun'))
    evidence = os.path.join(tree, 'work', 'capture-run', 'done', 'hook')
    os.makedirs(os.path.dirname(evidence))
    os.makedirs(os.path.join(tree, 'work', 'logs'))
    open(evidence, 'w').write('original hook')
    open(os.path.join(tree, 'work', 'logs', 'done.log'), 'w').write('finished run')
    retry = subprocess.run([os.path.join(tree, 'agents', 'faf-autorun', 'run'), 'done', '5'], capture_output=True, text=True)
    assert retry.returncode == 1 and 'never overwritten' in retry.stderr, retry
    assert open(evidence).read() == 'original hook' and open(os.path.join(tree, 'work', 'logs', 'done.log')).read() == 'finished run'
    print('capture.py self-test ok')


def main():
    a = sys.argv[1:]
    if a[:1] == ['--self-test']:
        return self_test()
    if a[:1] == ['watch'] and len(a) >= 3:
        checkpoints, allows, rest = [], [], a[3:]
        while rest:
            flag, value, rest = rest[0], rest[1], rest[2:]
            if flag == '--checkpoint':
                text, tick = value.rsplit('@', 1)
                checkpoints.append((text, int(tick)))
            else:
                allows.append(value)
        reason = watch(a[1], a[2], checkpoints, allows)
        if reason:
            print(reason)
            sys.exit(3)
        return
    if a[:1] == ['mods'] and len(a) == 4:
        loadable = loadable_mods(a[2], a[3])
        hits = [loadable[u] for u in active_mods(a[1]) if u in loadable]
        if hits:
            print(', '.join(hits))
            sys.exit(3)
        return
    if a[:1] == ['setup'] and len(a) >= 9 and a[8] == '--':
        print(setup(*a[1:8], a[9:]))
        return
    sys.exit(__doc__.strip())


main()
