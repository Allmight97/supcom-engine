#pragma once

// --lobby-options-test: a game launched through retail's front end and
// skirmish lobby by --click, offscreen, its speed keys pressed by --mouse.
// At kStartTick it notes the game speed and starts counting the speed
// actions the key map runs (uimain's IncreaseGameSpeed and
// DecreaseGameSpeed); with --lobby-options-rebind it binds Equals and Minus
// to them with retail's keymapper.SetUserKeyMapping and logs the profile's
// UserKeyMap. At kReportTick it logs the speed, the actions run and the
// HUD's readouts (units, clock). With --lobby-options-relaunch it then
// launches a game as a campaign operation does (LaunchSinglePlayerSession,
// its options Fast), and there logs its speed at kStartTick and again after
// asking for +1. tests/integration/lobby_options.py sets the
// lobby's options and reads the report. A script error fails it.

#include "core/types.hpp"

#include <string>

struct lua_State;

namespace osc::lua {
class LuaState;
}
namespace osc::sim {
class SimState;
}

namespace osc::app {

class LobbyOptionsTest {
public:
    static constexpr u32 kStartTick = 10;
    static constexpr u32 kReportTick = 160;

    LobbyOptionsTest(bool rebind, bool relaunch) : rebind_(rebind), relaunch_(relaunch) {}

    /// Each frame: the start at kStartTick, the report at kReportTick.
    void frame(lua::LuaState& ui, const sim::SimState* sim);
    bool done() const { return done_; }
    /// The result, as test_status failures or a [PASS] line.
    void finish() const;

private:
    /// Run `code` in the UI state; its string result, or "" (failed).
    std::string run(lua::LuaState& ui, const char* code);
    void fail(const std::string& why);

    bool rebind_;
    bool relaunch_;
    bool started_ = false;
    bool reported_ = false;
    bool relaunch_asked_ = false;
    bool relaunch_began_ = false; ///< its tick count started again
    bool relaunched_ = false;
    bool done_ = false;
    u32 frames_ = 0;
};

} // namespace osc::app
