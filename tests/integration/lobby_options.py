"""The skirmish lobby's Game Speed and Unit Cap, and the speed keys rebound.

CTest: data.lobby_options. Each run clicks through retail's front end and
single-player skirmish lobby (Skirmish, Launch), offscreen, with the lobby's
options as the player last chose them (the profile's Lobby_Gen_* entries,
which the lobby reads as it opens). --lobby-options-test notes the game speed
at tick 10, counts the speed actions the key map runs, and at tick 160 logs
the speed, that count and the HUD's readouts (units "count/cap", the clock).
From tick 100, once retail's opening input lock (worldview.LockInput) has
let go even at +4, the run presses keys through the window's input (--mouse).
Each run must exit 0: a script error fails it.

1. Normal: NumPlus runs the speed action, and the speed stays +0; the cap
   is 250.
2. Fast: the speed is +4 and stays there, though NumPlus runs the action.
3. Fast's own recording, watched (a launch no lobby made): +0, and NumPlus
   raises it to +1. In the same process as a Fast lobby game, a game then
   launched as a campaign operation is (its options Fast too): +0, and a
   request for +1 is taken.
4. Adjustable: NumPlus raises it to +1, and the clock shows "(+1)".
5. Rebound: retail's keymapper.SetUserKeyMapping (what its Key Bindings
   dialog would call: retail's own dialog has its Assign button commented
   out) binds Equals and Minus to the speed actions in place of NumPlus and
   NumMinus, in the profile's UserKeyMap. The key map loads as the game
   starts, so the binding takes effect from the next launch; a scripted run
   writes no preferences file, so the driver copies the UserKeyMap the run
   logs into the next run's. That run presses Equals three times, Minus
   once and NumPlus once: four actions and +2 (NumPlus unbound), where the
   default keys give one action and +1.

6. The mode fails, not passes, when the renderer cannot start (the Vulkan
   loader given no driver) or when asked to run headless (--ticks).

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
from dataclasses import dataclass
from pathlib import Path

TIMEOUT_SECONDS = 300
SKIPPED = 77

# Indices into retail's lobbyOptions.lua values, as the lobby stores them
NORMAL, FAST, ADJUSTABLE = 1, 2, 3
CAP_250 = 1
SANDBOX = 4  # a lone player may launch


@dataclass
class Report:
    start: int
    end: int
    actions: int
    units: str
    time: str


def write_prefs(prefs: Path, speed: int, key_map: str = "") -> None:
    """The player's preferences: the lobby's last choices."""
    user_key_map = f"        UserKeyMap = {key_map},\n" if key_map else ""
    prefs.write_text(
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


def run(
    exe: str, name: str, args: list[str], env: dict[str, str] | None = None
) -> tuple[Report | None, str, int]:
    """The run's report (None: none), its output and its exit status."""
    game = subprocess.run(
        [exe, "--lobby-options-test", *args],
        capture_output=True,
        text=True,
        errors="replace",
        timeout=TIMEOUT_SECONDS,
        check=False,
        env=env,
    )
    output = game.stdout + game.stderr
    for line in output.splitlines():
        if "lobby-options:" in line or "FAIL" in line:
            print(f"{name}: {line}")
    start = re.search(r"lobby-options: start=(-?\d+)", output)
    end = re.search(r"lobby-options: end=(-?\d+) actions=(\d+) units=(\S+) time=(\S+)", output)
    report = None
    if start and end:
        report = Report(int(start[1]), int(end[1]), int(end[2]), end[3], end[4])
    return report, output, game.returncode


def lobby_args(tmp: Path, presses: list[str]) -> list[str]:
    return [
        "--prefs",
        str(tmp / "Game.prefs"),
        "--user-dir",
        str(tmp / "user"),
        "--click",
        "Skirmish",
        "--click",
        "Launch",
        *presses,
    ]


def check(name: str, report: Report | None, status: int, want: dict) -> list[str]:
    """What is wrong with a run (each problem named for the run)."""
    problems = [f"exit {status}"] if status != 0 else []
    if report is None:
        return [f"{name}: {p}" for p in [*problems, "no report"]]
    got = {"start": report.start, "end": report.end, "actions": report.actions}
    problems += [
        f"{key} {got[key]}, expected {value}"
        for key, value in want.items()
        if key in got and got[key] != value
    ]
    if "cap" in want and not report.units.endswith(f"/{want['cap']}"):
        problems.append(f"units {report.units}, expected a cap of {want['cap']}")
    clock = want.get("clock")
    if clock and not report.time.endswith(clock):
        problems.append(f"clock {report.time}, expected it to end {clock}")
    if clock is None and "(" in report.time:
        problems.append(f"clock {report.time} shows a speed, as only Adjustable's does")
    return [f"{name}: {p}" for p in problems]


def main(argv: list[str]) -> int:
    if len(argv) < 1:
        print(__doc__, file=sys.stderr)
        return 2
    exe = argv[0]
    problems: list[str] = []
    numplus = keys((100, "numplus"))
    # name, speed option, extra arguments, what the report must say
    cases = [
        ("normal", NORMAL, numplus, {"start": 0, "end": 0, "actions": 1, "cap": 250}),
        ("fast", FAST, numplus, {"start": 4, "end": 4, "actions": 1, "cap": 250}),
        ("adjustable", ADJUSTABLE, numplus, {"start": 0, "end": 1, "actions": 1, "clock": "(+1)"}),
        (
            "rebind",
            ADJUSTABLE,
            ["--lobby-options-rebind"],
            {"start": 0, "end": 0, "actions": 0, "clock": "(+0)"},
        ),
    ]
    outputs: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="osc-lobby-options-") as root:
        for name, speed, extra, want in cases:
            tmp = Path(root) / name
            tmp.mkdir()
            write_prefs(tmp / "Game.prefs", speed)
            report, outputs[name], status = run(exe, name, lobby_args(tmp, extra))
            if status == SKIPPED:
                print("no game data: skipped")
                return SKIPPED
            problems += check(name, report, status, want)

        # Fast's recording, watched: no lobby launched it, so its speed is adjustable
        recording = Path(root) / "fast" / "user" / "replays" / "Player" / "LastGame.oscreplay"
        if not recording.exists():
            problems.append("fast: left no recording")
        else:
            report, _, status = run(exe, "watched", ["--watch", str(recording), *numplus])
            problems += check(
                "watched", report, status, {"start": 0, "end": 1, "actions": 1, "clock": ""}
            )

        # A Fast lobby game, then a game no lobby launches, in one process
        tmp = Path(root) / "relaunch"
        tmp.mkdir()
        write_prefs(tmp / "Game.prefs", FAST)
        report, output, status = run(
            exe, "relaunch", lobby_args(tmp, [*numplus, "--lobby-options-relaunch"])
        )
        problems += check("relaunch", report, status, {"start": 4, "end": 4, "actions": 1})
        if not re.search(r"lobby-options: relaunched start=0 end=1\b", output):
            problems.append("relaunch: the next game isn't adjustable at +0")

        # Nothing checked is a failure: no renderer, or a headless run
        no_driver = {**os.environ, "VK_ICD_FILENAMES": str(tmp / "none.json")}
        no_driver["VK_DRIVER_FILES"] = no_driver["VK_ICD_FILENAMES"]
        for name, args, env in [
            ("no renderer", lobby_args(tmp, numplus), no_driver),
            ("headless", ["--user-dir", str(tmp / "user"), "--ticks", "30"], None),
        ]:
            _, _, status = run(exe, name, args, env)
            if status == 0:
                problems.append(f"{name}: exit 0, though nothing was checked")

        # The rebound keys, in the next launch's preferences
        tmp = Path(root) / "rebound"
        tmp.mkdir()
        key_map = re.search(r"lobby-options: keymap=(\{.*\})", outputs["rebind"])
        if not key_map or '["Equals"]="increase_game_speed"' not in key_map[1]:
            problems.append("rebind: the profile's UserKeyMap binds no Equals to the speed")
        else:
            write_prefs(tmp / "Game.prefs", ADJUSTABLE, key_map[1])
            presses = keys(
                (100, "equals"), (105, "equals"), (110, "equals"), (115, "minus"), (120, "numplus")
            )
            report, _, status = run(exe, "rebound", lobby_args(tmp, presses))
            problems += check(
                "rebound", report, status, {"start": 0, "end": 2, "actions": 4, "clock": "(+2)"}
            )
    for problem in problems:
        print(f"FAIL: {problem}")
    if problems:
        return 1
    print("lobby options: Game Speed, Unit Cap and the rebound speed keys hold")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
