// A test-mode run's exit code (finish_test_run): a run that counted no check
// fails, so a mode whose checks never ran cannot pass.

#include <catch2/catch_test_macros.hpp>

#include "app/support.hpp"
#include "core/test_status.hpp"

#include <cstdlib>

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

TEST_CASE("finish_test_run: a run with no check fails; one passed check passes", "[app][test-status]") {
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
