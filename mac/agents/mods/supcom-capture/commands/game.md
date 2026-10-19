---
description: Screenshot or drive the original game's window in CrossOver (for OpenSupCom, use mac/scripts/play) (shot [name] | click X Y | key CODE | wait [SECONDS]) [--owner java|ForgedAlliance]
argument-hint: shot [name] | click X Y | key CODE | wait [SECONDS] [--owner java|ForgedAlliance]
allowed-tools: Bash(mac/scripts/game-window:*), Bash(GAME_WINDOW_OWNER=* mac/scripts/game-window:*), Read
---

Arguments: `$ARGUMENTS`

Drive the game window through `mac/scripts/game-window` from the checkout root. Do nothing else.

1. Owner. Default: the GOG game (`SupremeCommander`); run the script with no `GAME_WINDOW_OWNER`. If the arguments hold `--owner java` or `--owner ForgedAlliance`, remove that pair and prefix the command with `GAME_WINDOW_OWNER=<value> `. Refuse any other owner value.
2. Action, from the remaining arguments:
   - `shot [name]`: run `mac/scripts/game-window shot <name>` (name default `game`). On success, Read the PNG path it prints (relative to `mac/`), then reply with the path and one line that describes what the window shows.
   - `click X Y [right]`, `key CODE`, `wait [SECONDS]`: run `mac/scripts/game-window <action> <args>` unchanged. For `wait`, give the Bash call a timeout above SECONDS (default 120 s).
   - Anything else: reply with the usage in the description above. Run nothing.
3. Exit status. 0: report the output in one line. 1: report the script's message (for example `No SupremeCommander window.`). 2: report the usage. 3: report "Input refused: the game window is not in front." 4: report "Real input is off; JStar grants it with mac/scripts/input-grant MINUTES." Never grant it, retry, change focus another way, or bypass the frontmost guard.
