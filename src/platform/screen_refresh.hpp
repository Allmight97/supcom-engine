#pragma once

struct GLFWwindow;

namespace osc::platform {

/// The refresh rate of the screen holding the window (the main screen when
/// macOS places it on none), in Hz; 0 when unknown.
double screen_refresh_rate(GLFWwindow* window);

} // namespace osc::platform
