-- SETUP|TICK|n every 100 sim ticks, so the launcher knows how far a run got and can check per-kind checkpoints.
assert(BeginSession, 'simInit.lua has no BeginSession')
local CaptureBeginSession = BeginSession

function BeginSession()
    CaptureBeginSession()
    ForkThread(function()
        while true do
            LOG('SETUP|TICK|' .. GetGameTick())
            WaitTicks(100)
        end
    end)
end

LOG('HOOKCHECK|/capturehook/lua/simInit.lua|ok')
