# The lobby's Game Speed and Unit Cap in every lobby game

Retail's skirmish lobby launches a single-player game through the same
`LaunchGame` as a network game (`lobby.lua`), and sends every option as a
string (`lobbyOptions.lua`: UnitCap '250' to '1000', GameSpeed 'normal',
'fast', 'adjustable'). The engine read GameSpeed only for network games, from
the sim's `ScenarioInfo`, and UnitCap only when it was a number. So a
single-player skirmish played Fast at +0, let the keys change Normal and Fast,
and kept a cap of 1000.

## Where each rule comes from

Retail's scripts are the reference where they say something. Where they
don't, the rule comes from the decompiled engine of the GOG release of
Forged Alliance: `bin/SupremeCommander.exe`, file version 1.5.0.1, linked
2008-02-19, SHA-256
`79074e294ea72fb179914cc393525720c523b65d6c9e300f11d31edceccdb887`. That is
not the Steam FA 3599 this project measures against, and no capture of the
original has checked these rules yet. The code states them in its own words.

Read from the scripts:
- The option's values and its default: Normal is the first and the default,
  so a skirmish with untouched settings is Normal. The lobby's help text
  describes Normal and Fast as fixed speeds (+0 and +4) and Adjustable as
  one the players change.
- The clock shows the speed (`00:16 (+1)`) only in an Adjustable game, and
  learns it from `uimain.NoteGameSpeedChanged` (`score.lua`).
- Retail's Key Bindings dialog cannot rebind: its Assign and Reset buttons
  are commented out. A rebind is the profile's `UserKeyMap`
  (`keymapper.SetUserKeyMapping`), which the key map loads as the game
  starts.

Read from the decompiled engine (GOG build above):
- `CLobby::LaunchGame` (0x7c37a0) reads GameSpeed and creates the session's
  client manager (`CLIENT_CreateClientManager`, 0x53fa30) with a starting
  rate and an adjustable flag: +4 for 'fast', +0 otherwise; adjustable only
  for 'adjustable'.
- The other callers create it adjustable at +0, whatever the options say:
  the single-player session a campaign operation uses (0x88b6bb), a loaded
  saved game (0x88058f) and a replay (0x876616).
- The client manager's `SetSimRate` (0x53e4d0) does nothing when the speed
  is not adjustable. `SetGameSpeed` and the `WLD_*SimRate` commands all go
  through it, so in a fixed game none of them changes the speed.
- `WLD_IncreaseSimRate` (0x88cbb0) stops at +10. The engine allows +50.
  Left as it is until a capture says which.

Chosen here, where neither source decides:
- The value is matched without regard to case ('Adjustable' counts). The
  engine's network path already did this.
- A GameSpeed that is absent, or not a string, fixes the speed at +0. This
  follows from the decompiled branch (only the string 'adjustable' sets the
  flag), but nothing has tested it.
- A peer's speed message is ignored where the speed is fixed, or when the
  peer plays no army. It applies the same rule as a local request. The
  decompile has not been read for this.

## The engine's shape

- `GameOptionsConfig::number` and `string` read an option as Lua does (a
  number, or a string of one). Every option the session reads goes through
  them: UnitCap, NoRushOption, CheatMult, BuildMult, Victory and the rest.
- `sim::lobby_game_speed(options)` turns GameSpeed into a rate and an
  adjustable flag.
- A lobby's `LaunchGame` marks its launch (`__osc_launch_lobby`), and the
  launch takes `lobby_game_speed`: the lockstep session for a network game,
  `GameStateManager::set_speed_option` for a single-player one. A replay or
  saved game asked for in its place (by the lobby's `GameLaunched`, say)
  does not. Any other launch, and every new game until then, is adjustable
  at +0: `transition_to(GAME)` resets it as the reload enters the game.
- A single-player game's accepted speed change reaches
  `uimain.NoteGameSpeedChanged`, as a network game's does.

## Tests

- `data.lobby_options` (gate, `tests/integration/lobby_options.py`): lobby
  launches with each Game Speed and a Unit Cap of 250, NumPlus pressed
  through the window's input. It counts that the key ran the speed action
  in every case. Fast's recording, watched, is adjustable at +0, and so is
  a game launched as a campaign operation in the same process after a Fast
  lobby game. A rebind to Equals and Minus takes effect at the next launch.
  The mode fails when the renderer cannot start, and refuses to run headless.
- `osc_tests`: the option readers and `lobby_game_speed`; a string UnitCap
  reaching every army; a fixed speed refusing requests until a new game; a
  peer's speed message ignored in a fixed game and from an observer.
