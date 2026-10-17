# The interface's scale on a dense display

## Why

FA's Lua lays its screens out in the root frame's units, and M217h made
those the framebuffer's pixels. On a Retina display a window's framebuffer
is twice its size in points, so retail's menus and HUD drew at half size.
On a 5K panel they were too small to use. The same holds on Wayland at
200%, and on Windows and X11 at a high DPI.

Drawing the whole window at its points (letting macOS double it) fixes the
size but halves the world's resolution. The world should keep the panel's
pixels; only the interface should scale.

## The rule

- **Two units.** The framebuffer's pixels, and the interface's units:
  pixels over the interface's scale.
- **The interface's scale** is the display's content scale times the
  player's zoom (`--ui-scale`, default 1).
  - The content scale is GLFW's `glfwGetWindowContentScale`: 2 on Retina,
    the compositor's scale on Wayland, the monitor's DPI over 96 on Windows
    and X11.
  - It is not the framebuffer's size over the window's: that is 1 on
    Windows and X11 whatever their DPI.
  - A change of display (`glfwSetWindowContentScaleCallback`) rebuilds the
    swapchain, and the root frame follows as on a resize.
- **In pixels:** the 3D world, and everything Vulkan sizes: viewports,
  scissors, render areas, images, captures.
- **In interface units:** everything in screen space.
  - The root frame (`GetFrame(0)`).
  - The cursor, wherever it is read (UI dispatch, the camera, world
    clicks).
  - The camera's view (`Camera::set_viewport`): picking, projection, the
    middle-drag pan and the spin.
  - The world views' `Project` and `UnProject`, and `GetMouseWorldPos`.
  - The strategic, resource and projectile icons, the overlays, FAF's
    world drawing's thickness, the minimap, and the C++ HUD.
- **The conversions:**
  - The screen's renderers push the interface's size to their shaders,
    which turn positions into clip space.
  - The interface's clip rects are scaled to pixels for the scissor.
- **Text:** glyphs are rasterized at the scale's pixels (`FontCache`'s
  density). Advances and metrics stay those of the point size, so
  retail's layouts measure text as before and it is drawn sharp.

## Offscreen

A capture's hidden window has an unscaled framebuffer, so its display
scale is 1 whatever the machine's display. `--ui-scale` keeps a capture's
1600×900 interface and multiplies its pixels. That is how a 2× display is
checked without one:

- A 3200×1800 capture shrunk to 1600×900 differs from the 1× capture in
  0.04% of pixels (SCMP_009's game interface) and 0.01% (the Video
  options), by more than 10%.
- Clicks by label and a pointer moved to a ground point land at 2× as at
  1×.

## FAF's UI Scale

FAF's options have UI Scale (`ui_scale`, 80% to 200%). FAF's own Lua
applies it (`lua/maui/layouthelpers.lua`), on top of the root frame's
size, so it multiplies with the display's scale as it does on a PC's
1440p screen. The engine never reads that preference. `--ui-scale` is
for retail, which has no such option; a FAF player uses one or the other.

## What changes for whom

- **macOS:**
  - "Looks like" 2560×1440 on a 5K panel: the world at 5120×2880, the
    interface at 2560×1440.
  - At the panel's native 1× mode the content scale is 1, so the
    interface is the panel's pixels; `--ui-scale 2` enlarges it.
- **Wayland** at 125–200%: the interface takes the compositor's scale.
- **Windows and X11:** the interface takes the monitor's DPI.
  - At 150% a 2560×1440 framebuffer has a 1707×960 interface, where it
    was 2560×1440.
  - A FAF player who set UI Scale to make up for that gets both.

## Left

- The cartographic minimap's frame is drawn at the view's interface units
  and magnified on a dense display (a shortcut in `renderer.cpp`). Drawing
  it at the scale's pixels needs its lines checked at that density.
- A small window on a 2× laptop gives retail an interface under its
  1024×768 minimum.
- `--ui-scale` lives on the command line only, not in the preferences.

## Tests

- **Unit:**
  - the cursor from the window's units to the interface's (Retina,
    Wayland, Windows);
  - the scale and the interface's size.
- **Captures:** the 1× and 2× comparisons above. No test drives the real
  cursor at a scale other than 1; a player's click is the check.
