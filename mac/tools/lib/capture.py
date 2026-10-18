#!/usr/bin/env python3
"""Preflight checks and setup manifests for tools/lib/game-run.sh.

  capture.py watch LOG STATE [--checkpoint 'TEXT@TICK']... [--allow TEXT]...
      Reads LOG from the offset saved in STATE (JSON) and exits 3 with a reason when the run must stop:
      a Lua error or unknown unit type, a hook the game loaded ("Hooked X with /mount/...") that has not
      logged HOOKCHECK|/mount/...|ok within 90 s, or a checkpoint TEXT not seen once SETUP|TICK reached TICK.
  capture.py setup LOG SNAPSHOT_DIR END -- ARGS...
      Writes LOG's manifest to <LOG without .partial>.setup (JSON): arguments, git HEAD and dirty flag, the
      sha256 of every hook and script in SNAPSHOT_DIR, resolved armies, options, seed, last tick and how the run
      ended.
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


def setup(log, snapshot, end, args):
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
                hashes[os.path.relpath(path, snapshot)] = hashlib.sha256(open(path, 'rb').read()).hexdigest()
    git = lambda *a: subprocess.run(('git',) + a, capture_output=True, text=True).stdout.strip()
    manifest = {
        'log': log.removesuffix('.partial'), 'args': args, 'end': end,
        'git_head': git('rev-parse', 'HEAD'), 'git_dirty': bool(git('status', '--porcelain', '--', 'tools', 'agents')),
        'armies': armies, 'seed': seed, 'options': options, 'last_tick': tick, 'hashes': dict(sorted(hashes.items())),
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
    m = json.load(open(setup(log, d, 'marker', ['/map', 'X'])))
    assert m['armies'][0]['faction'] == '3' and m['seed'] == '7' and m['options'] == {'A': '1', 'B': 'x'}
    assert m['last_tick'] == 2500 and m['end'] == 'marker'
    os.makedirs(os.path.join(d, 'mods', 'm'))
    open(os.path.join(d, 'mods', 'm', 'mod_info.lua'), 'w').write('name = "Mine"\nuid = "u-1"\n')
    open(os.path.join(d, 'prefs'), 'w').write("a = 1\nactive_mods = {\n    ['u-1'] = true,\n    ['faf-only'] = true\n}\n")
    assert active_mods(os.path.join(d, 'prefs')) == ['u-1', 'faf-only']
    assert loadable_mods(os.path.join(d, 'mods'), os.path.join(d, 'none.scd')) == {'u-1': 'Mine'}
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
    if a[:1] == ['setup'] and len(a) >= 5 and a[4] == '--':
        print(setup(a[1], a[2], a[3], a[5:]))
        return
    sys.exit(__doc__.strip())


main()
