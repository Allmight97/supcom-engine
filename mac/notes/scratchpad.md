# Scratchpad

Working notes that are not yet facts for STATUS.md: hypotheses, half-finished
reasoning, questions to check, ideas worth keeping across context compaction.
Any agent may add a dated entry at the top. Move settled facts to STATUS.md,
procedures to docs/toolchain.md, history to log/; delete entries once moved
or abandoned.

## 2026-10-17 (main: draft note to zooldoo, for JStar to post; not sent)

Where: upstream's GitHub Discussions (enabled), or a comment on #729. JStar posts it.

> Hi zooldoo, I'm JStar, working on OpenSupCom on macOS (M4 Max, macOS 27, a 5K
> 120 Hz display). I've seen your Mac PRs (#240, #485, #687) and want to avoid
> duplicating you: I rebuilt the HiDPI interface scale before seeing #687.
> What I have that may help, all on my fork (Allmight97/supcom-engine): OSC runs
> unmodified on KosmicKrisp (LunarG's Mesa driver on Metal 4, in Vulkan SDK
> 1.4.363) with zero validation errors; vk-bootstrap now gets the linked loader's
> vkGetInstanceProcAddr, so it no longer opens libMoltenVK.dylib by name; the build
> ships the loader and both drivers beside the game and prefers KosmicKrisp;
> GetAntiAliasingOptions was a nil stub that broke retail's Video options, fixed.
> Which driver and loader do you run, and on which macOS? If useful, I could take
> driver, packaging (a .app with the loader and driver inside) and macOS CI, and
> leave renderer and interface work to you. Happy to coordinate however suits you.
