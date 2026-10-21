# Forged Alliance natively on the Mac

```bash
osc                                  # the menu: pick options, then play
osc --go                             # play again with the last menu choices
# Once, to run osc from any folder:
ln -s ~/Projects/OpenSupCom/mac/scripts/osc ~/.local/bin/osc
# Direct play, for scripts and advanced use (run from ~/Projects/OpenSupCom). KosmicKrisp (Metal 4) is chosen automatically.
mac/scripts/play                     # Video options decide; full screen at 60 Hz caps at 60; Metal HUD on
mac/scripts/play --build             # rebuild the current branch first
mac/scripts/play --full              # force full screen 2560x1440 (overrides the Video option)
mac/scripts/play --no-hud            # without Apple's Metal HUD (fps and frame times)
mac/scripts/play -- --fps-cap -2     # extra game args after --; a cap (-2 = refresh - 2, 0 = none)
grep -m1 driver ~/Library/Application\ Support/opensupcom/logs/opensupcom.log   # confirm: "driver KosmicKrisp"
# Nuke test: skirmish as UEF, victory "Sandbox", select your ACU, Ctrl-K.
```

This folder contains the modernization of [OpenSupCom](https://github.com/bwiemz/supcom-engine) on modern Apple silicon with a focus on Apple's software stack released with macOS 27.

[Allmight97/supcom-engine](https://github.com/Allmight97/supcom-engine) (upstream:
[bwiemz/supcom-engine](https://github.com/bwiemz/supcom-engine)): the build recipe, the
play command, checks, and tools that compare against the original game. Mac engine work lands on the fork and is offered upstream where
upstream can take it.

Graphics run Vulkan on Metal 4 through **KosmicKrisp** (LunarG's conformant driver) on Apple
Silicon with macOS 26+, and the bundled **MoltenVK** on macOS 14-25. Plan, decisions, known
issues and work in flight: the [roadmap issue](https://github.com/Allmight97/supcom-engine/issues/12).

## Use it

You need your own copy of the game (GOG or Steam) and this Mac setup:
[docs/toolchain.md, "Fresh setup"](docs/toolchain.md). Run the commands below from the
checkout root (`~/Projects/OpenSupCom`).

`osc` is the everyday way to play. Its menu sets the window, Metal HUD, frame cap, UI scale,
rebuild, and extra game options, shows the `play` command it runs, and remembers your choices.
`osc --go` plays with the last choices. Its choices are the lists at the top of [scripts/osc](scripts/osc).

Maintainers: when `play` gains an option or a play test needs a new game flag, add it to the osc
menu (those lists and the menu's lines) in the same change.

The table lists the `play` flags that osc drives, and the other scripts:

| Command | What it does |
| --- | --- |
| `mac/scripts/play` | Play as the game's Video options say (full screen at 60 Hz caps the frame rate at 60), with the Metal HUD |
| `mac/scripts/play --build` | Rebuild the current branch first |
| `mac/scripts/play --full` | Full screen 2560x1440, overriding the Video option |
| `mac/scripts/play --size W H` | Windowed at W x H |
| `mac/scripts/play --no-hud` | Without Apple's Metal HUD (frame rate, GPU time, frame interval) |
| `mac/scripts/play ... -- --ui-scale 1.25` | Pass any game option after `--` (here: a larger interface) |
| `mac/scripts/play -- --fps-cap -2` | A frame-rate cap (`-2`: 2 below the refresh rate; `0`: none) |
| `mac/scripts/osc-smoke` | Headless AI skirmish; fails on any error |
| `mac/scripts/osc-render-check` | Hidden rendered capture; fails unless the driver is KosmicKrisp and there are no errors |
| `mac/scripts/upstream-news` | What upstream landed or is working on that touches the Mac; run before any Mac change |
| `mac/scripts/check` | The toolkit's own checks (required before every commit that touches `mac/`) |
| `mac/scripts/setup` | Install the commit and push guards and the Claude settings (after a clone or a hook change) |

The game's log is `~/Library/Application Support/opensupcom/logs/opensupcom.log` (settings stay in `~/.config/opensupcom` when that folder exists).

## Constraints

- Bring your own game. Game files, screenshots of game art, saves and replays are
  never committed; git hooks enforce it.
- The original game is the reference for faithfulness. It runs only in CrossOver
  under Rosetta, which macOS 28 removes, so reference captures are made while it lasts
  ([docs/crossover-recipe.md](docs/crossover-recipe.md)).
- Agents working here follow [AGENTS.md](AGENTS.md). They never use the player's
  mouse, keyboard or window focus; they test with hidden runs.

## Licence

MIT, like OpenSupCom ([LICENSE](LICENSE)).
