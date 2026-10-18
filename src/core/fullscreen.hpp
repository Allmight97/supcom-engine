#pragma once

#include <cstddef>
#include <optional>
#include <span>

namespace osc::core {

/// macOS's full screen is the window's own Space (the green button's): a
/// display mode change there re-lays out the whole desktop.
#ifdef __APPLE__
inline constexpr bool kNativeFullscreen = true;
#else
inline constexpr bool kNativeFullscreen = false;
#endif

struct NativeFullscreenStep {
    bool toggle = false;
    bool apply_windowed = false;
    bool settled = false;
    bool operator==(const NativeFullscreenStep&) const = default;
};

inline NativeFullscreenStep native_fullscreen_step(std::optional<bool> want, bool in_fullscreen,
                                                   bool moving, bool windowed_pending) {
    if (moving) {
        return {};
    }
    if (want && *want != in_fullscreen) {
        return {.toggle = true};
    }
    return {.apply_windowed = !in_fullscreen && windowed_pending, .settled = true};
}

/// A rectangle in the desktop's screen coordinates.
struct DisplayArea {
    int x = 0, y = 0, width = 0, height = 0;
};

/// The display holding the middle of `area`; the first display (GLFW's
/// primary: the main display, the one with the menu bar) when none does or
/// there is no area.
inline size_t display_at(std::span<const DisplayArea> displays, std::optional<DisplayArea> area) {
    if (!area) return 0;
    const int cx = area->x + area->width / 2;
    const int cy = area->y + area->height / 2;
    for (size_t i = 0; i < displays.size(); ++i) {
        const DisplayArea& d = displays[i];
        if (cx >= d.x && cx < d.x + d.width && cy >= d.y && cy < d.y + d.height) return i;
    }
    return 0;
}

} // namespace osc::core
