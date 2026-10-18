-- /simspeed N: run the session at game speed N (the launch hook makes speed adjustable) and log
-- SETUP|SPEED|requested|simrate; SETUP|RATE|gametime|simrate every 10 s of game time after that.
assert(OnFirstUpdate, 'gamemain.lua has no OnFirstUpdate')
local CaptureOnFirstUpdate = OnFirstUpdate

function OnFirstUpdate()
    CaptureOnFirstUpdate()
    local speed = GetCommandLineArg('/simspeed', 1)
    if speed then
        SetGameSpeed(tonumber(speed[1]))
        ForkThread(function()
            WaitSeconds(1)
            LOG('SETUP|SPEED|' .. speed[1] .. '|' .. tostring(GetSimRate()))
            while true do
                WaitSeconds(10)
                LOG(string.format('SETUP|RATE|%.1f|%s', GameTime(), tostring(GetSimRate())))
            end
        end)
    end
end

LOG('HOOKCHECK|/capturehook/lua/ui/game/gamemain.lua|ok')
