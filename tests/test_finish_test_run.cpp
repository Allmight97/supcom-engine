// A test-mode run's exit code (finish_test_run): a run that counted no check
// fails, so a mode whose checks never ran cannot pass.

#include <catch2/catch_test_macros.hpp>

#include "app/support.hpp"
#include "core/log.hpp"
#include "core/test_status.hpp"
#include "lua/lua_state.hpp"

#include <spdlog/sinks/ostream_sink.h>
#include <spdlog/spdlog.h>

#include <cstdlib>
#include <memory>
#include <sstream>

extern "C" {
#include <lua.h>
}

namespace {
void set_listed(bool listed) {
#ifdef _WIN32
    _putenv_s("OSC_NO_CHECK_BASELINE", listed ? "1" : "");
#else
    if (listed) setenv("OSC_NO_CHECK_BASELINE", "1", 1);
    else unsetenv("OSC_NO_CHECK_BASELINE");
#endif
}
} // namespace

TEST_CASE("finish_test_run: a run with no check fails; one passed check passes",
          "[app][test-status]") {
    osc::test_status::reset();
    CHECK(osc::app::finish_test_run("no-check") == 1);
    osc::test_status::record_pass();
    CHECK(osc::app::finish_test_run("one-check") == 0);
    osc::test_status::fail("a failed check");
    CHECK(osc::app::finish_test_run("one-failure") == 1);
    osc::test_status::reset();
}

TEST_CASE("finish_test_run: a listed run passes with no check; a failure still fails it",
          "[app][test-status]") {
    osc::test_status::reset();
    set_listed(true);
    CHECK(osc::app::finish_test_run("listed, no check") == 0);
    osc::test_status::fail("a failed check");
    CHECK(osc::app::finish_test_run("listed, one failure") == 1);
    set_listed(false);
    osc::test_status::reset();
}

TEST_CASE("finish_test_run: an AI game its caller judges needs no check", "[app][test-status]") {
    osc::test_status::reset();
    CHECK(osc::app::finish_test_run("ai game", 0, false) == 0);
    osc::test_status::fail("a script error");
    CHECK(osc::app::finish_test_run("ai game", 0, false) == 1);
    osc::test_status::reset();
}

TEST_CASE("A test mode's Lua LOG line naming PASS counts as a check", "[app][test-status]") {
    osc::test_status::reset();
    osc::test_status::set_count_lua_failures(true);
    osc::lua::LuaState lua;
    lua_pushstring(lua.raw(), "Bone test 1: PASS");
    osc::log::l_LOG(lua.raw());
    osc::test_status::set_count_lua_failures(false);
    CHECK(osc::test_status::check_count() == 1);
    CHECK(osc::test_status::failure_count() == 0);
    osc::test_status::reset();
}

TEST_CASE(
    "finish_test_run: a run whose only check failed reports the failure, not \"no check ran\"",
    "[app][test-status]") {
    osc::test_status::reset();
    osc::test_status::fail("the one check failed");
    CHECK(osc::test_status::check_count() == 1);
    std::ostringstream log;
    const auto previous = spdlog::default_logger();
    spdlog::set_default_logger(std::make_shared<spdlog::logger>(
        "capture", std::make_shared<spdlog::sinks::ostream_sink_st>(log)));
    const int code = osc::app::finish_test_run("one failure");
    spdlog::set_default_logger(previous);
    CHECK(code == 1);
    CHECK(log.str().find("one failure: FAIL (1 failed check(s))") != std::string::npos);
    CHECK(log.str().find("the one check failed") != std::string::npos);
    CHECK(log.str().find("no check ran") == std::string::npos);
    osc::test_status::reset();
}
