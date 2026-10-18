import re, sys, time
mac_log, game_log = sys.argv[1], sys.argv[2]
out = open(mac_log.replace('mac-', 'pairs-'), 'a')
def last(path, pat, tail=400):
    try:
        with open(path, errors='replace') as f: lines = f.readlines()[-tail:] if tail else f.readlines()
    except FileNotFoundError: return None
    for l in reversed(lines):
        m = re.search(pat, l)
        if m: return m
    return None
prev = None
while True:
    mac = last(mac_log, r'cursor (-?\d+),(-?\d+) mode (\d+)x(\d+) px (\d+)x(\d+) (?:win (-?[\d.]+),(-?[\d.]+) ([\d.]+)x([\d.]+) layer (-?\d+)|.*)')
    game = last(game_log, r'MOUSEPROBE\|pos\|(-?\d+)\|(-?\d+)')
    frame = last(game_log, r'MOUSEPROBE\|frame\|([\d.]+)x([\d.]+)', 0)
    if mac and mac.group(7) and game and frame:
        cx, cy = int(mac.group(1)), int(mac.group(2))
        wx, wy, ww, wh = (float(mac.group(i)) for i in (7, 8, 9, 10))
        fw, fh = float(frame.group(1)), float(frame.group(2))
        sx, sy = fw / ww, fh / wh
        ex, ey = (cx - wx) * sx, (cy - wy) * sy
        gx, gy = int(game.group(1)), int(game.group(2))
        line = (f"Mac pointer {cx},{cy} pt | window {wx:.0f},{wy:.0f} {ww:.0f}x{wh:.0f} pt layer {mac.group(11)}{' (captured)' if int(mac.group(11)) > 1000000 else ' (NOT captured)'} | "
                f"game frame {fw:.0f}x{fh:.0f} | game cursor {gx},{gy} | expected {ex:.0f},{ey:.0f} | "
                f"OFFSET game px dx {gx-ex:+.0f} dy {gy-ey:+.0f}  (= {(gx-ex)/sx:+.1f}, {(gy-ey)/sy:+.1f} pt)")
    else:
        line = "waiting: " + ("mac ok " if mac and mac.group(7) else "no game window yet ") + ("game ok" if game else "no MOUSEPROBE lines yet")
    if line != prev: stamp = time.strftime('%H:%M:%S'); print(stamp, line, flush=True); out.write(f'{stamp} {line}\n'); out.flush(); prev = line
    time.sleep(0.5)
