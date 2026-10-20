#include "core/test_status.hpp"

#include <atomic>
#include <cstdlib>
#include <mutex>

namespace osc::test_status {

namespace {

constexpr size_t kMaxKeptMessages = 50;

std::mutex g_mutex;
int g_count = 0;
int g_passes = 0;
std::vector<std::string> g_messages;
std::atomic<bool> g_count_lua{false};

} // namespace

void record_failure(std::string message) {
    std::lock_guard lock(g_mutex);
    ++g_count;
    if (g_messages.size() < kMaxKeptMessages) g_messages.push_back(std::move(message));
}

int failure_count() {
    std::lock_guard lock(g_mutex);
    return g_count;
}

void record_pass() {
    std::lock_guard lock(g_mutex);
    ++g_passes;
}

int pass_count() {
    std::lock_guard lock(g_mutex);
    return g_passes;
}

void skip(const std::string& reason) {
    if (const int failures = failure_count(); failures > 0) {
        spdlog::error("=== FAIL ({} failed check(s)) before a skip: {} ===", failures, reason);
        for (const auto& message : failure_messages()) spdlog::error("  - {}", message);
        spdlog::default_logger()->flush();
        std::exit(1);
    }
    spdlog::warn("=== SKIPPED: {} ===", reason);
    spdlog::default_logger()->flush();
    std::exit(kExitSkipped);
}

std::vector<std::string> failure_messages() {
    std::lock_guard lock(g_mutex);
    return g_messages;
}

void reset() {
    std::lock_guard lock(g_mutex);
    g_count = 0;
    g_passes = 0;
    g_messages.clear();
}

void set_count_lua_failures(bool enabled) { g_count_lua.store(enabled); }
bool count_lua_failures() { return g_count_lua.load(); }

} // namespace osc::test_status
