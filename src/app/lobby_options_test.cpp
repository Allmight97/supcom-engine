#include "app/lobby_options_test.hpp"

#include "core/test_status.hpp"
#include "lua/lua_state.hpp"
#include "sim/sim_state.hpp"

#include <fmt/format.h>
#include <spdlog/spdlog.h>

#include <cstring>

extern "C" {
#include <lauxlib.h>
#include <lua.h>
}

namespace osc::app {

namespace {

/// Frames to reach the report before the run counts as stuck.
constexpr u32 kMaxFrames = 30000;

/// The speed now, and a count of the speed actions the key map runs from here.
constexpr const char* kStart = R"(
    local uimain = import('/lua/ui/uimain.lua')
    rawset(_G, '__osc_speed_actions', 0)
    for _, name in {'IncreaseGameSpeed', 'DecreaseGameSpeed'} do
        local action = uimain[name]
        uimain[name] = function()
            rawset(_G, '__osc_speed_actions', rawget(_G, '__osc_speed_actions') + 1)
            action()
        end
    end
    return tostring(GetGameSpeed())
)";

/// Equals and Minus in place of NumPlus and NumMinus, as retail's Key Bindings
/// dialog would bind them; the profile's UserKeyMap after.
constexpr const char* kRebind = R"(
    local keymapper = import('/lua/keymap/keymapper.lua')
    keymapper.SetUserKeyMapping('Equals', 'NumPlus', 'increase_game_speed')
    keymapper.SetUserKeyMapping('Minus', 'NumMinus', 'decrease_game_speed')
    SavePreferences()
    local entries = {}
    for key, action in import('/lua/user/prefs.lua').GetFromCurrentProfile('UserKeyMap') do
        table.insert(entries, string.format('[%q]=%q,', key, action))
    end
    return '{' .. table.concat(entries) .. '}'
)";

constexpr const char* kReport = R"(
    local score = import('/lua/ui/game/score.lua')
    return string.format('end=%d actions=%d units=%s time=%s', GetGameSpeed(),
        rawget(_G, '__osc_speed_actions'), score.controls.units:GetText(),
        string.gsub(score.controls.time:GetText(), ' ', '_'))
)";

} // namespace

void LobbyOptionsTest::frame(lua::LuaState& ui, const sim::SimState* sim) {
    if (done_) return;
    if (++frames_ > kMaxFrames) {
        done_ = true; // stuck: reported by finish
        return;
    }
    if (!sim) return;
    const u32 tick = sim->tick_count();
    if (!started_ && tick >= kStartTick) {
        started_ = true;
        const std::string speed = run(ui, kStart);
        if (speed.empty()) return;
        spdlog::info("lobby-options: start={}", speed);
        if (rebind_) {
            const std::string key_map = run(ui, kRebind);
            if (key_map.empty()) return;
            spdlog::info("lobby-options: keymap={}", key_map);
        }
    }
    if (started_ && tick >= kReportTick) {
        const std::string report = run(ui, kReport);
        if (report.empty()) return;
        spdlog::info("lobby-options: {}", report);
        reported_ = true;
        done_ = true;
    }
}

std::string LobbyOptionsTest::run(lua::LuaState& ui, const char* code) {
    lua_State* L = ui.raw();
    const int top = lua_gettop(L);
    std::string out;
    if (luaL_loadbuffer(L, code, std::strlen(code), "=lobby-options") != 0 ||
        lua_pcall(L, 0, 1, 0) != 0 || lua_type(L, -1) != LUA_TSTRING) {
        fail(lua_isstring(L, -1) ? lua_tostring(L, -1) : "a probe returned no string");
    } else {
        out = lua_tostring(L, -1);
    }
    lua_settop(L, top);
    return out;
}

void LobbyOptionsTest::fail(const std::string& why) {
    test_status::fail("[FAIL] lobby-options: {}", why);
    done_ = true;
}

void LobbyOptionsTest::finish() const {
    if (reported_) {
        spdlog::info("[PASS] lobby-options: reported at tick {}", kReportTick);
    } else if (test_status::failure_count() == 0) {
        test_status::fail("[FAIL] lobby-options: the game never reached tick {} ({} frames)",
                          kReportTick, frames_);
    }
}

} // namespace osc::app
