#include "core/frame_limiter.hpp"

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include <chrono>

using osc::core::FrameCap;
using osc::core::FrameIntervals;
using osc::core::FrameLimiter;
using Clock = FrameLimiter::Clock;
using namespace std::chrono_literals;

namespace {

double ms(Clock::duration d) {
    return std::chrono::duration<double, std::milli>(d).count();
}

} // namespace

TEST_CASE("An absolute frame cap is its setting, whatever the display", "[frame_cap]") {
    FrameCap cap(117.5);
    CHECK(cap.update(120));
    CHECK(cap.fps() == 117.5);
    CHECK_FALSE(cap.update(60));
    CHECK(cap.fps() == 117.5);
}

TEST_CASE("A relative frame cap follows the display's refresh rate", "[frame_cap]") {
    FrameCap cap(-2);
    CHECK(cap.update(120));
    CHECK(cap.fps() == 118);
    CHECK_FALSE(cap.update(120));
    // The window moves to a 60 Hz display, then a 144 Hz one
    CHECK(cap.update(60));
    CHECK(cap.fps() == 58);
    CHECK(cap.update(144));
    CHECK(cap.fps() == 142);
    // Decimals, and a rate it can't go below
    FrameCap half(-2.5);
    half.update(120);
    CHECK(half.fps() == 117.5);
    FrameCap deep(-115);
    deep.update(120);
    CHECK(deep.fps() == 0);
}

TEST_CASE("Without a setting, a full screen mode's lower rate is the cap", "[frame_cap]") {
    // The Video option's 60 Hz on a 120 Hz display: 60; its 120 Hz, or 60 Hz
    // on a 60 Hz display: none beyond vsync
    FrameCap cap(0);
    CHECK(cap.update(120, 60));
    CHECK(cap.fps() == 60);
    CHECK_FALSE(cap.update(120, 60));
    CHECK(cap.update(120, 120));
    CHECK(cap.fps() == 0);
    CHECK(cap.update(60, 60));
    CHECK(cap.fps() == 0);
    // No mode (windowed), or the display's rate unknown: none
    CHECK(cap.update(120, 0));
    CHECK(cap.fps() == 0);
    CHECK(cap.update(0, 60));
    CHECK(cap.fps() == 0);
    // A setting wins over the mode
    FrameCap absolute(90);
    absolute.update(120, 60);
    CHECK(absolute.fps() == 90);
    FrameCap relative(-2);
    relative.update(120, 60);
    CHECK(relative.fps() == 118);
}

TEST_CASE("A frame cap under the lowest is none", "[frame_cap]") {
    FrameCap slow(9.5);
    slow.update(0);
    CHECK(slow.fps() == 0);
    FrameCap lowest(FrameCap::kMinFps);
    lowest.update(0);
    CHECK(lowest.fps() == FrameCap::kMinFps);
}

TEST_CASE("A relative frame cap is none while the display's rate is unknown", "[frame_cap]") {
    FrameCap cap(-2);
    CHECK(cap.update(0));
    CHECK(cap.fps() == 0);
    CHECK(cap.update(120));
    CHECK(cap.fps() == 118);
}

TEST_CASE("No frame cap never waits", "[frame_cap]") {
    FrameLimiter limiter;
    limiter.set_fps(0);
    const Clock::time_point t0{};
    CHECK(limiter.next(t0) == t0);
    CHECK(limiter.next(t0 + 1ms) == t0 + 1ms);
}

TEST_CASE("Fast frames start a period apart", "[frame_cap]") {
    FrameLimiter limiter;
    limiter.set_fps(60);
    Clock::time_point now{};
    Clock::time_point last = limiter.next(now);
    FrameIntervals intervals;
    for (int i = 0; i < 600; ++i) {
        now = last + 2ms; // each frame's work takes 2 ms
        const Clock::time_point start = limiter.next(now);
        intervals.add(ms(start - last));
        last = start;
    }
    CHECK(intervals.mean() == Catch::Approx(1000.0 / 60).margin(1e-5));
    CHECK(intervals.sd() < 1e-3);
}

TEST_CASE("A late frame keeps the cadence; one a whole period late restarts it", "[frame_cap]") {
    FrameLimiter limiter;
    limiter.set_fps(100); // 10 ms
    const Clock::time_point t0{};
    CHECK(limiter.next(t0) == t0);
    // 3 ms past its deadline: no wait, and the next deadline stays on the grid
    CHECK(limiter.next(t0 + 13ms) == t0 + 13ms);
    CHECK(limiter.next(t0 + 15ms) == t0 + 20ms);
    // 25 ms past: start the count again from there
    CHECK(limiter.next(t0 + 55ms) == t0 + 55ms);
    CHECK(limiter.next(t0 + 56ms) == t0 + 65ms);
}

TEST_CASE("Frame intervals give their mean and spread", "[frame_cap]") {
    FrameIntervals intervals;
    for (double v : {8.0, 9.0, 10.0}) intervals.add(v);
    CHECK(intervals.mean() == Catch::Approx(9.0));
    CHECK(intervals.sd() == Catch::Approx(0.816497).epsilon(1e-5));
    CHECK(intervals.min == 8.0);
    CHECK(intervals.max == 10.0);
}

TEST_CASE("Waiting for a frame's start ends on time", "[frame_cap]") {
    const auto t = Clock::now() + 5ms;
    osc::core::wait_until(t);
    const auto late = Clock::now() - t;
    CHECK(late >= 0ns);
    CHECK(late < 2ms); // the spin ends it; a loaded machine may still preempt
}
