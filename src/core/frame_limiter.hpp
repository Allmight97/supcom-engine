#pragma once

#include <algorithm>
#include <chrono>
#include <cmath>
#include <optional>
#include <thread>

namespace osc::core {

/// The fps_cap setting (--fps-cap, the fps_cap option): a positive value is
/// the cap in frames per second, a negative one that far below the refresh
/// rate of the window's display, 0 none.
class FrameCap {
public:
    /// The lowest cap: a frame's time for the game is clamped (to 0.25 s, and
    /// the sim's catch-up to 8 ticks), so slower frames would slow the game.
    static constexpr double kMinFps = 10;

    explicit FrameCap(double setting) : setting_(setting) {}

    bool relative() const { return setting_ < 0; }
    double setting() const { return setting_; }
    double refresh_hz() const { return refresh_hz_; }
    /// Frames per second; 0 is none (also a cap under kMinFps, as a relative
    /// one is while its display's rate is unknown).
    double fps() const { return fps_; }

    /// The refresh rate of the window's display now (0 unknown); true when
    /// the cap is first set or the rate it follows changed.
    bool update(double refresh_hz) {
        if (!relative()) refresh_hz = 0;
        if (set_ && refresh_hz == refresh_hz_) return false;
        set_ = true;
        refresh_hz_ = refresh_hz;
        fps_ = relative() ? refresh_hz + setting_ : setting_;
        if (fps_ < kMinFps) fps_ = 0;
        return true;
    }

private:
    double setting_;
    double refresh_hz_ = 0;
    double fps_ = 0;
    bool set_ = false;
};

/// Paces frame starts at a rate: each start's deadline is the last one's plus
/// a period, so the rate doesn't drift; a frame later than a whole period
/// starts the count again from its own start instead of rushing to catch up.
class FrameLimiter {
public:
    using Clock = std::chrono::steady_clock;

    void set_fps(double fps) {
        period_ = fps > 0 ? std::chrono::duration_cast<Clock::duration>(
                                std::chrono::duration<double>(1.0 / fps))
                          : Clock::duration::zero();
    }

    /// When the frame that could start at `now` starts.
    Clock::time_point next(Clock::time_point now) {
        if (period_ == Clock::duration::zero()) return now;
        if (!deadline_) {
            deadline_ = now;
            return now;
        }
        *deadline_ += period_;
        if (now - *deadline_ > period_) *deadline_ = now;
        return std::max(now, *deadline_);
    }

private:
    Clock::duration period_ = Clock::duration::zero();
    std::optional<Clock::time_point> deadline_;
};

/// Wait until `t` to within microseconds. Darwin's timers wake about half the
/// time asked for late (measured: 8 ms sleeps woke 2 to 4 ms late), so it
/// sleeps half of what is left until 0.5 ms is, then spins.
inline void wait_until(FrameLimiter::Clock::time_point t) {
    using namespace std::chrono_literals;
    using Clock = FrameLimiter::Clock;
    for (auto left = t - Clock::now(); left > 500us; left = t - Clock::now()) {
        std::this_thread::sleep_for(left / 2);
    }
    while (Clock::now() < t) std::this_thread::yield();
}

/// The spread of frame intervals, in milliseconds.
struct FrameIntervals {
    long count = 0;
    double sum = 0;
    double sum_sq = 0;
    double min = 0;
    double max = 0;

    void add(double ms) {
        min = count == 0 ? ms : std::min(min, ms);
        max = count == 0 ? ms : std::max(max, ms);
        ++count;
        sum += ms;
        sum_sq += ms * ms;
    }
    double mean() const { return count ? sum / static_cast<double>(count) : 0; }
    double sd() const {
        if (count < 2) return 0;
        const double m = mean();
        return std::sqrt(std::max(0.0, sum_sq / static_cast<double>(count) - m * m));
    }
};

} // namespace osc::core
