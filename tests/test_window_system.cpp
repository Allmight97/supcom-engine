#include <catch2/catch_test_macros.hpp>

#include "renderer/renderer.hpp"
#include "renderer/window.hpp"

#include <GLFW/glfw3.h>

using osc::renderer::open_window;

namespace {

struct NullPlatform {
    NullPlatform() { glfwInitHint(GLFW_PLATFORM, GLFW_PLATFORM_NULL); }
    ~NullPlatform() { glfwInitHint(GLFW_PLATFORM, GLFW_ANY_PLATFORM); }
};

} // namespace

TEST_CASE("Shutting down one renderer leaves another's window open", "[renderer][window]") {
    osc::renderer::Renderer outer;
    osc::renderer::Renderer inner;
    if (!outer.init(64, 64, "outer", /*offscreen=*/true) ||
        !inner.init(64, 64, "inner", /*offscreen=*/true))
        SKIP("no Vulkan device");

    inner.shutdown();
    glfwGetError(nullptr);
    outer.set_window_title("still open");

    REQUIRE(glfwGetError(nullptr) == GLFW_NO_ERROR);
}

TEST_CASE("GLFW runs while any window is open", "[window]") {
    if (!glfwPlatformSupported(GLFW_PLATFORM_NULL)) SKIP("GLFW is built without its null platform");
    const NullPlatform null_platform;
    glfwGetError(nullptr);

    SECTION("closing one window leaves another") {
        const auto first = open_window(64, 48, "first", /*offscreen=*/true);
        REQUIRE(first);
        REQUIRE(glfwGetPlatform() == GLFW_PLATFORM_NULL);
        {
            const auto second = open_window(32, 24, "second", /*offscreen=*/true);
            REQUIRE(second);
        }

        int width = 0;
        int height = 0;
        glfwGetWindowSize(first.get(), &width, &height);
        CHECK(glfwGetError(nullptr) == GLFW_NO_ERROR);
        CHECK(width == 64);
        CHECK(height == 48);
    }

    SECTION("a window that cannot be made leaves GLFW to the open ones") {
        const auto open = open_window(64, 48, "open", /*offscreen=*/true);
        REQUIRE(open);
        REQUIRE(glfwGetPlatform() == GLFW_PLATFORM_NULL);

        CHECK_FALSE(open_window(0, 0, "empty", /*offscreen=*/true));
        glfwGetError(nullptr);

        int width = 0;
        int height = 0;
        glfwGetWindowSize(open.get(), &width, &height);
        CHECK(glfwGetError(nullptr) == GLFW_NO_ERROR);
        CHECK(width == 64);
        CHECK(height == 48);
    }

    SECTION("GLFW ends with the last window and starts again with the next") {
        {
            const auto only = open_window(64, 48, "only", /*offscreen=*/true);
            REQUIRE(only);
            REQUIRE(glfwGetPlatform() == GLFW_PLATFORM_NULL);
        }
        glfwGetError(nullptr);
        CHECK(glfwGetPlatform() == 0);
        CHECK(glfwGetError(nullptr) == GLFW_NOT_INITIALIZED);

        const auto next = open_window(64, 48, "next", /*offscreen=*/true);
        REQUIRE(next);
        CHECK(glfwGetPlatform() == GLFW_PLATFORM_NULL);
    }

    SECTION("a window that cannot be made as the first leaves GLFW stopped") {
        CHECK_FALSE(open_window(0, 0, "empty", /*offscreen=*/true));
        glfwGetError(nullptr);
        CHECK(glfwGetPlatform() == 0);
        CHECK(glfwGetError(nullptr) == GLFW_NOT_INITIALIZED);
    }
}
