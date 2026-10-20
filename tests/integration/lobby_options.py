"""The skirmish lobby's Game Speed and Unit Cap, and the speed keys rebound.

CTest: data.lobby_options. Each run clicks through retail's front end and
single-player skirmish lobby (Skirmish, Launch), offscreen, with the lobby's
options as the player last chose them (the profile's Lobby_Gen_* entries,
which the lobby reads as it opens). A UI mod in a temporary Documents folder
hooks retail's score.lua: at tick 10 it notes the game speed, and at tick 160
it logs the speed and the HUD's readouts (units "count/cap", the clock).
From tick 100, once retail's opening input lock (worldview.LockInput) has
let go even at +4, the run presses keys through the window's input (--mouse).

1. Normal: the speed stays +0 though NumPlus is pressed; the cap is 250.
2. Fast: the speed is +4 and stays there.
3. Adjustable: NumPlus raises it to +1, and the clock shows "(+1)".
4. Rebound: retail's keymapper.SetUserKeyMapping (what its Key Bindings
   dialog would call: retail's own dialog has its Assign button commented
   out) binds Equals and Minus to the speed actions in place of NumPlus and
   NumMinus, in the profile's UserKeyMap. The key map loads as the game
   starts, so the binding takes effect from the next launch; a scripted run
   writes no preferences file, so the driver copies the UserKeyMap the run
   logs into the next run's. That run presses Equals three times, Minus
   once and NumPlus once: +2 (NumPlus unbound), where the default keys give +1.

Any script error fails a run.

Usage:
    lobby_options.py <opensupcom>

Exits 77 (skipped) when the game has no data.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

TIMEOUT_SECONDS = 300
SKIPPED = 77

PROBE = "osc-lobby-options-probe"
MODS_DIR = Path("My Games/Gas Powered Games/Supreme Commander Forged Alliance/mods")

# Indices into retail's lobbyOptions.lua values, as the lobby stores them
NORMAL, FAST, ADJUSTABLE = 1, 2, 3
CAP_250 = 1
SANDBOX = 4  # a lone player may launch

SCORE_HOOK = """
local oscBeat = _OnBeat
local oscStart = nil
local oscDone = false
function _OnBeat()
    oscBeat()
    local tick = GameTick()
    if tick >= 10 and not oscStart then
        oscStart = GetGameSpeed()
        if oscRebind then
            local keymapper = import('/lua/keymap/keymapper.lua')
            keymapper.SetUserKeyMapping('Equals', 'NumPlus', 'increase_game_speed')
            keymapper.SetUserKeyMapping('Minus', 'NumMinus', 'decrease_game_speed')
            SavePreferences()
            local entries = {}
            for key, action in import('/lua/user/prefs.lua').GetFromCurrentProfile('UserKeyMap') do
                table.insert(entries, string.format('[%q]=%q,', key, action))
            end
            LOG('lobby-options: keymap={' .. table.concat(entries) .. '}')
        end
    end
    if tick >= 160 and not oscDone then
        oscDone = true
        LOG(string.format('lobby-options: start=%d end=%d units=%s time=%s',
            oscStart, GetGameSpeed(), controls.units:GetText(),
            string.gsub(controls.time:GetText(), ' ', '_')))
        ExitApplication()
    end
end
"""


def write_probe(documents: Path, rebind: bool) -> None:
    mods = documents / MODS_DIR
    mods.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(mods / "OscLobbyOptions.zip", "w") as probe:
        probe.writestr(
            "mod_info.lua",
            f'name = "OSC lobby options probe"\nuid = "{PROBE}"\nversion = 1\n'
            'description = "Logs the game speed and the HUD"\nauthor = "OpenSupCom"\n'
            "ui_only = true\n",
        )
        rebind_line = f"local oscRebind = {'true' if rebind else 'false'}\n"
        probe.writestr("hook/lua/ui/game/score.lua", rebind_line + SCORE_HOOK)


def write_prefs(prefs: Path, speed: int, key_map: str = "") -> None:
    """The player's preferences: the probe selected, and the lobby's choices."""
    user_key_map = f"        UserKeyMap = {key_map},\n" if key_map else ""
    prefs.write_text(
        f"active_mods = {{ ['{PROBE}'] = true }}\n"
        "profile = {\n"
        "    current = 1,\n"
        "    profiles = { {\n"
        "        Name = 'Player',\n"
        "        MenuTutorialPrompt = true,\n"
        "        LastScenario = '/maps/SCMP_009/SCMP_009_scenario.lua',\n"
        f"        Lobby_Gen_GameSpeed = {speed},\n"
        f"        Lobby_Gen_Cap = {CAP_250},\n"
        f"        Lobby_Gen_Victory = {SANDBOX},\n"
        f"{user_key_map}"
        "    } },\n"
        "}\n"
    )


def keys(*presses: tuple[int, str]) -> list[str]:
    """--mouse steps: each key pressed and let go at its tick."""
    args: list[str] = []
    for tick, key in presses:
        args += ["--mouse", f"t{tick} press {key}", "--mouse", f"t{tick} release {key}"]
    return args


def run(exe: str, tmp: Path, name: str, presses: list[str], env: dict[str, str]):
    """The run's report (start, end, units, time), or None (SKIPPED: no data); and its output."""
    game = subprocess.run(
        [
            exe,
            "--prefs",
            str(tmp / "Game.prefs"),
            "--user-dir",
            str(tmp / "user"),
            "--click",
            "Skirmish",
            "--click",
            "Launch",
            *presses,
        ],
        capture_output=True,
        text=True,
        errors="replace",
        timeout=TIMEOUT_SECONDS,
        check=False,
        env=env,
    )
    output = game.stdout + game.stderr
    if game.returncode == SKIPPED:
        return SKIPPED, output
    for line in output.splitlines():
        if "lobby-options:" in line or "FAIL" in line or "SetGameOption" in line:
            print(f"{name}: {line}")
    match = re.search(r"lobby-options: start=(-?\d+) end=(-?\d+) units=(\S+) time=(\S+)", output)
    report = match.groups() if match else None
    if game.returncode != 0:
        print(f"{name}: exit {game.returncode}")
    return report, output


def main(argv: list[str]) -> int:
    if len(argv) < 1:
        print(__doc__, file=sys.stderr)
        return 2
    exe = argv[0]
    problems: list[str] = []
    # name, speed option, rebind, presses, start, end, clock ends with
    cases = [
        ("normal", NORMAL, False, keys((100, "numplus")), 0, 0, None),
        ("fast", FAST, False, keys((100, "numplus")), 4, 4, None),
        ("adjustable", ADJUSTABLE, False, keys((100, "numplus")), 0, 1, "(+1)"),
        ("rebind", ADJUSTABLE, True, [], 0, 0, "(+0)"),
    ]
    outputs: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="osc-lobby-options-") as root:
        for name, speed, rebind, presses, start, end, clock in cases:
            tmp = Path(root) / name
            documents = tmp / "Documents"
            write_probe(documents, rebind)
            write_prefs(tmp / "Game.prefs", speed)
            env = {**os.environ, "XDG_DOCUMENTS_DIR": str(documents)}
            report, outputs[name] = run(exe, tmp, name, presses, env)
            if report == SKIPPED:
                print("no game data: skipped")
                return SKIPPED
            if report is None:
                problems.append(f"{name}: no report")
                continue
            got_start, got_end, units, time = report
            if (int(got_start), int(got_end)) != (start, end):
                problems.append(f"{name}: speed {got_start} then {got_end}, expected {start} then {end}")
            if not units.endswith("/250"):
                problems.append(f"{name}: units {units}, expected a cap of 250")
            if clock is not None and not time.endswith(clock):
                problems.append(f"{name}: clock {time}, expected it to end {clock}")
            if clock is None and "(" in time:
                problems.append(f"{name}: clock {time} shows a speed, as only Adjustable's does")

        # The rebound keys, in the next launch's preferences
        tmp = Path(root) / "rebound"
        key_map = re.search(r"lobby-options: keymap=(\{.*\})", outputs.get("rebind", ""))
        if not key_map or '["Equals"]="increase_game_speed"' not in key_map.group(1):
            problems.append("rebind: the profile's UserKeyMap binds no Equals to the speed")
        else:
            write_probe(tmp / "Documents", rebind=False)
            write_prefs(tmp / "Game.prefs", ADJUSTABLE, key_map.group(1))
            presses = keys(
                (100, "equals"), (105, "equals"), (110, "equals"), (115, "minus"), (120, "numplus")
            )
            env = {**os.environ, "XDG_DOCUMENTS_DIR": str(tmp / "Documents")}
            report, _ = run(exe, tmp, "rebound", presses, env)
            if report is None or report == SKIPPED:
                problems.append("rebound: no report")
            elif int(report[1]) != 2 or not report[3].endswith("(+2)"):
                problems.append(
                    f"rebound: speed {report[1]}, clock {report[3]}: expected +2 from Equals "
                    "three times and Minus once, NumPlus unbound"
                )
    for problem in problems:
        print(f"FAIL: {problem}")
    if problems:
        return 1
    print("lobby options: Game Speed, Unit Cap and the rebound speed keys hold")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
