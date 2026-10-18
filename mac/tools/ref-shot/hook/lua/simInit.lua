-- Appended to /lua/simInit.lua: every tick logs each commander's pose and what it is building; the game is
-- paused during the shots, so the last lines before REFSHOT|READY give the state in the images.
--   REFSHOT|ACU|tick|army|entity|blueprint|x,y,z|qx,qy,qz,qw
--   REFSHOT|BUILD|tick|army|entity|blueprint|fraction
local function RefShotLogCommanders()
    while true do
        for index, brain in ArmyBrains do
            for _, unit in brain:GetListOfUnits(categories.COMMAND, false) or {} do
                local p = unit:GetPosition()
                local q = unit:GetOrientation()
                LOG(string.format('REFSHOT|ACU|%d|%d|%s|%s|%.6g,%.6g,%.6g|%.6g,%.6g,%.6g,%.6g', GetGameTick(), index,
                    tostring(unit:GetEntityId()), unit:GetBlueprint().BlueprintId, p[1], p[2], p[3], q[1], q[2], q[3], q[4]))
                local built = unit:GetFocusUnit()
                if built then
                    LOG(string.format('REFSHOT|BUILD|%d|%d|%s|%s|%.4f', GetGameTick(), index, tostring(built:GetEntityId()),
                        built:GetBlueprint().BlueprintId, built:GetFractionComplete()))
                end
            end
        end
        WaitTicks(1)
    end
end

local RefShotBeginSession = BeginSession
function BeginSession()
    RefShotBeginSession()
    ForkThread(RefShotLogCommanders)
end

LOG('HOOKCHECK|/refshothook/lua/simInit.lua|ok')
