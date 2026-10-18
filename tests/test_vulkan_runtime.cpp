#include "renderer/vk_types.hpp"

#include <catch2/catch_test_macros.hpp>

#include <array>
#include <cstring>

TEST_CASE("Vulkan startup identifies the loader and selected driver", "[renderer][vulkan]") {
    VkPhysicalDeviceDriverProperties driver{};
    driver.driverID = VK_DRIVER_ID_MESA_KOSMICKRISP;
    std::strcpy(driver.driverName, "KosmicKrisp");
    std::strcpy(driver.driverInfo, "Mesa 26.2.99 (test build)");
    CHECK(osc::renderer::vulkan_runtime_description(VK_MAKE_API_VERSION(0, 1, 4, 363), driver) ==
          "Vulkan loader 1.4.363, driver KosmicKrisp (Mesa 26.2.99 (test build)), driverID 28");
}

TEST_CASE("Vulkan startup labels unavailable driver properties", "[renderer][vulkan]") {
    const VkPhysicalDeviceDriverProperties driver{};
    CHECK(osc::renderer::vulkan_runtime_description(VK_API_VERSION_1_0, driver) ==
          "Vulkan loader 1.0.0, driver unavailable (unavailable), driverID 0");
}

TEST_CASE("Vulkan startup prefers a KosmicKrisp device", "[renderer][vulkan]") {
    using osc::renderer::preferred_device;
    const VkDriverId kosmickrisp = VK_DRIVER_ID_MESA_KOSMICKRISP;
    const VkDriverId moltenvk = VK_DRIVER_ID_MOLTENVK;
    CHECK(preferred_device(std::array{moltenvk, kosmickrisp}) == 1);
    CHECK(preferred_device(std::array{kosmickrisp, moltenvk}) == 0);
    CHECK(preferred_device(std::array{moltenvk}) == 0);
    CHECK(preferred_device(std::array{moltenvk, moltenvk}) == 0);
}
