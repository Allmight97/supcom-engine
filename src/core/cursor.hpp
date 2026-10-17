#pragma once

#include "core/types.hpp"

#include <algorithm>
#include <array>
#include <cmath>

namespace osc::core {

/// Framebuffer pixels per interface unit. FA's Lua lays its screens out in
/// interface units, so on a dense display they keep the size they have on a
/// 96-dpi one: the display's content scale (2 on Retina, 1.5 at Windows'
/// 150%) times the player's zoom. The 3D world keeps the framebuffer's pixels.
inline f64 interface_scale(f64 content_scale, f64 zoom) {
    return (content_scale > 0 ? content_scale : 1.0) * (zoom > 0 ? zoom : 1.0);
}

/// The interface's width or height in its units for a framebuffer's in pixels
inline u32 interface_size(u32 framebuffer, f64 scale) {
    return std::max<u32>(1, static_cast<u32>(std::lround(framebuffer / scale)));
}

/// A cursor position from the window's units to the interface's. The window's
/// units are the framebuffer's pixels on Windows and X11 and points on macOS
/// and Wayland; everything the cursor is compared with -- the UI's rects, the
/// camera's view, its pan and spin -- is in the interface's units.
inline std::array<f64, 2> to_interface(f64 x, f64 y, i32 window_w, i32 window_h,
                                       i32 framebuffer_w, i32 framebuffer_h, f64 scale) {
    const f64 sx = window_w > 0 ? static_cast<f64>(framebuffer_w) / window_w : 1.0;
    const f64 sy = window_h > 0 ? static_cast<f64>(framebuffer_h) / window_h : 1.0;
    return {x * sx / scale, y * sy / scale};
}

/// `buttons`: a bit per GLFW mouse button held; `mods`: the GLFW_MOD_* keys held
struct ScriptedPointer {
    f64 x = 0;
    f64 y = 0;
    u32 buttons = 0;
    i32 mods = 0;
};

} // namespace osc::core
