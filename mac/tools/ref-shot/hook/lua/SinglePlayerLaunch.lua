local RefShotLaunchSinglePlayerSession = LaunchSinglePlayerSession

-- /refemitters TEXT passes TEXT to the sim hook (simInit.lua).
-- /reffactions 1,4,1,2 sets the faction of armies 1, 2, 3, 4 (1 UEF, 2 Aeon, 3 Cybran, 4 Seraphim).
function LaunchSinglePlayerSession(sessionInfo)
    local factions = GetCommandLineArg('/reffactions', 1)
    if factions then
        local index = 1
        for value in string.gfind(factions[1], '[^,]+') do
            local info = sessionInfo.teamInfo[index]
            if info and not info.Civilian then
                info.Faction = tonumber(value)
            end
            index = index + 1
        end
    end
    local emitters = GetCommandLineArg('/refemitters', 1)
    sessionInfo.scenarioInfo.Options.RefShotEmitters = emitters and emitters[1]
    for index, info in sessionInfo.teamInfo do
        LOG('REFSHOT|ARMY|' .. index .. '|' .. tostring(info.ArmyName) .. '|faction ' .. tostring(info.Faction))
    end
    return RefShotLaunchSinglePlayerSession(sessionInfo)
end

LOG('HOOKCHECK|/refshothook/lua/SinglePlayerLaunch.lua|ok')
