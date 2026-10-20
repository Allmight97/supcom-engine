# Supreme Commander: Forged Alliance and FAF in CrossOver

Guidance for running the original game (and FAF's) in a CrossOver bottle, to make reference captures for
OpenSupCom. CrossOver is not the product's target; the Mac target is OpenSupCom itself. Checked on an Apple
silicon Mac (macOS 27.2) with CrossOver 26.3, the GOG release of Forged Alliance (1.5.3599) and FAF game
version 3839, in October 2026. You need your own copy of the game.

## What works

- The original game: main menu, a skirmish against the built-in AI with the mouse, save, reload, exit
  through the menu.
- FAF's game: the same, run offline from its own Skirmish menu, and a skirmish against the M28AI mod.
- The FAF client (signed in, chat, mod vault), and a private game hosted from it with the M28AI mod in
  fullscreen at 2560×1440 (120 Hz) on a 5K display: mouse on target, normal exit (October 2026, two
  3-minute sessions). Section 5 has the setup.

## 1. Make the bottle

1. In CrossOver, create a bottle (Windows 10, 64-bit) and install the GOG
   Forged Alliance installer into it.
2. Install Microsoft XACT into the bottle (CrossOver: Install Software →
   search "XACT", or winetricks `xact`). Wine's built-in XACT crashed the
   game at startup.
3. Use graphics backend Auto with MSync on (bottle settings → Advanced). In
   `cxbottle.conf`: `"CX_GRAPHICS_BACKEND" = ""`, `"WINEMSYNC" = "1"`.
   `wined3d` also ran the game.

## 2. Settings in Game.prefs

The game keeps its settings in the bottle at
`drive_c/users/crossover/AppData/Local/Gas Powered Games/Supreme Commander Forged Alliance/Game.prefs`.
Edit it only while the game is closed (the game rewrites it when it exits),
and keep a copy first.

- **Skip the black splash screen.** Without this, the game waits at a black
  screen for a key press. Add at the end of the file:

  ```lua
  movie = {
      nologo = true
  }
  ```

- **Fullscreen size.** `primary_adapter = 'W,H,60'` must be a mode of your
  Mac's *main* display (the one with the menu bar), in points (for example
  `'2880,1620,60'` for a 5K display set to "looks like 2880×1620", or
  `'1728,1117,60'` for a 16-inch MacBook Pro screen). After one fullscreen
  start the game lists the modes it found under
  `options_overrides.primary_adapter`. A size the main display lacks logs
  "unable to create device" and falls back to 1024×768. If you plug in or
  remove an external display, check this again.

## 3. Window or fullscreen

- **Fullscreen (recommended for play):** start without `/windowed`, with
  `primary_adapter` (or Options → Video) set to a main-display size such as
  2560×1440. The FAF client always starts the game this way. The game
  minimizes when another app takes focus; click its Dock icon to return.
  To fill the screen with the mouse on target, follow "What keeps the mouse
  on target" in section 5.
- **Windowed:** start the game with `/windowed 1680 1050` (or another size).
  Choose the size at launch: resizing the window afterwards breaks clicking
  on the 3D world (moving it is fine). In some windows FAF's clicks landed
  off target (see Known problems).

## 4. FAF (Forged Alliance Forever)

FAF's own Mac instructions are in the FAF client repository:
[downlords-faf-client scripts/mac/README.md](https://github.com/FAForever/downlords-faf-client/blob/develop/scripts/mac/README.md).
Point the client's game path at your bottle's Forged Alliance folder. Two
fixes were needed on top of that recipe in CrossOver:

- **The y: drive.** FAF writes the game path as a Unix path
  (`/Users/you/...`). CrossOver bottles map `y:` to your home folder, so the
  game looked for its files on `Y:\Users\you\...`, found nothing, and showed
  no textures; the game log said "does not match any files", "Global Settings
  not loaded" and "Error initializing 3D audio". Fix: delete the bottle's
  `dosdevices/y:` link before starting the game, so the path resolves on `Z:`.
- **Mods: the in-game Mods Manager's OK button does not work** (Escape
  discards the selection), so a mod from FAF's vault never becomes active and
  its AIs are missing from the lobby. Workaround: with the game closed, set
  the mod in `Game.prefs`:

  ```lua
  active_mods = { ['fnewm028-v326-55b4-92b6-64398e7ge43f'] = true }
  ```

  The uid is in the mod's `mod_info.lua` (this one is M28AI version 326);
  mods live in `~/My Games/Gas Powered Games/Supreme Commander Forged Alliance/mods`.
  The lobby then lists the mod's AIs (for example "AI: M28 Easy"). Set it
  back to `active_mods = { }` when you want to play without mods.

To play offline without the client, run FAF's `ForgedAlliance.exe` from
`~/.faforever/bin` with `/init init.lua /windowed 1680 1050`, then use
Skirmish in its main menu.

## 5. Fullscreen size and mouse on target

Measured findings for reference captures. Only one game can run in the bottle at a time; close any running copy
first (`pgrep -fl 'ForgedAlliance[.]exe|SupremeCommander[.]exe'` prints nothing when none runs).

### Choose the fullscreen size

The size must be a mode of the main display (section 2). Example: 2560×1440
on a 5K display.

- **In the game (works):** start a game, press F10 → Options → Video, set
  the resolution to 2560×1440 (120 or 60) instead of Windowed, apply, then
  exit the game. The game keeps it for the next start.
- **In the file (if the menu fights you):** with the game closed, change
  `primary_adapter` in `Game.prefs` to `'2560,1440,60'`.

What keeps the mouse on target (5K Studio Display, October 2026):

1. Mac display: System Settings → Displays → "looks like" 2560×1440.
2. Game: 2560×1440 fullscreen (`primary_adapter = '2560,1440,120'`).
3. Bottle: let a fullscreen game take over the display. With the game closed,
   in Terminal:

   ```sh
   "/Applications/CrossOver.app/Contents/SharedSupport/CrossOver/bin/wine" --bottle SupCom \
       reg add 'HKCU\Software\Wine\Mac Driver' /v CaptureDisplaysForFullscreen /t REG_SZ /d y /f
   ```

   Use your bottle's name in place of `SupCom`. This is part of the measured
   setup; it is not yet shown to be necessary. It takes over every display,
   not only the game's: other displays go black while the fullscreen game is
   in front (CrossOver's Mac driver calls only `CGCaptureAllDisplays`).
4. FAF's game only: when it first opens, press Cmd-Tab to another app, then
   click the game's Dock icon to return. The mouse is on target from then on.
   (Measured with FAF's executable started directly; the client-started game
   shows the same 31-point offset.)

| Mac display ("looks like") | Game | Takes over the display | Fills the screen | Mouse |
| --- | --- | --- | --- | --- |
| 2560×1440 | GOG game, 2560×1440 fullscreen | yes, about 2 s after start | yes | on target (measured 0 points) |
| 2560×1440 | FAF game 3839, 2560×1440 fullscreen | only later, not at start | yes | 31 points too high until you switch away and back once, then on target (measured 0 points) |
| 2880×1620 | 2560×1440 fullscreen | not measured | no, large centred area | on target |
| any | windowed | no | no, small window | far off |

Why FAF's game is off: both games first open a 2048×1152 window just below
the menu bar (31 points down), then grow it to fill the screen. The GOG game
then takes over the display and the mouse lines up. FAF's game keeps the old
31-point origin, so every pointer position it reads is 31 points too high:
over the third lobby slot it highlights the second. Taking over the display
later does not fix that; hiding the window and showing it again (Cmd-Tab
away and back, or another desktop and back) does. Measured with
`mac/tools/mouse-probe/run` (GOG) and `mac/tools/mouse-probe/run faf` (FAF's
executable started directly, LAN lobby), offsets read while the pointer was
still. Not yet measured: the same runs without the
CaptureDisplaysForFullscreen setting.
These runs used CrossOver's Auto graphics backend with MSync on, and High
Resolution mode off.

## Known problems and untested parts

- FAF's Campaign stops with a Lua error and a black screen.
- Mouse off target in a window: when the game started in a smaller window,
  clicks landed away from the pointer (also seen in the Mods Manager's bottom
  row). Use fullscreen at 2560×1440 instead (section 5).
- FAF's game in fullscreen reads the mouse 31 points too high until you
  Cmd-Tab away and back once (section 5).
- Escape on the game's main screen closes open dialogs and then offers to
  quit the game; that is the game's normal behavior.
- Typing into the save-name field can drop letters while the game runs.
- Untested: long sessions, online
  multiplayer, CrossOver's High Resolution mode (it shows the game the full
  pixel size, for example 5120×2880, so the game's mode list changes and its
  interface gets very small).
