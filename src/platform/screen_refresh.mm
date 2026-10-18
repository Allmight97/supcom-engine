#include "platform/screen_refresh.hpp"

#import <AppKit/AppKit.h>
#define GLFW_EXPOSE_NATIVE_COCOA
#include <GLFW/glfw3.h>
#include <GLFW/glfw3native.h>

namespace osc::platform {

double screen_refresh_rate(GLFWwindow* glfw_window) {
    NSScreen* screen = [glfwGetCocoaWindow(glfw_window) screen];
    if (!screen) screen = [NSScreen screens].firstObject;
    return screen ? static_cast<double>(screen.maximumFramesPerSecond) : 0.0;
}

} // namespace osc::platform
