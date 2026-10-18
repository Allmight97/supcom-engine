-- /simbots makes every army an AI (as the original's unused SetupBotSession does), with /ai KEY (default rush);
-- /simfactions 3,1,1,1 sets the armies' factions; /simticks N, /siminterval N, /simthreat N, /simecon N,
-- /simintel N, /simscript NAME, /simvel and /simcombat
-- reach the sim as ScenarioInfo.Options.SimCapture* fields.
local SimCaptureLaunchSinglePlayerSession = LaunchSinglePlayerSession

function LaunchSinglePlayerSession(sessionInfo)
    if HasCommandLineArg('/simbots') then
        local ai = GetCommandLineArg('/ai', 1)
        for _, info in sessionInfo.teamInfo do
            if not info.Civilian then
                info.Human = false
                info.AIPersonality = ai and ai[1] or 'rush'
            end
        end
    end
    local factions = GetCommandLineArg('/simfactions', 1)
    if factions then
        local index = 1
        for value in string.gfind(factions[1], '[^,]+') do
            if sessionInfo.teamInfo[index] then
                sessionInfo.teamInfo[index].Faction = tonumber(value)
            end
            index = index + 1
        end
    end
    local options = sessionInfo.scenarioInfo.Options
    for arg, key in { ['/simticks'] = 'SimCaptureEndTick', ['/siminterval'] = 'SimCaptureInterval',
            ['/simthreat'] = 'SimCaptureThreat', ['/simecon'] = 'SimCaptureEconomy', ['/simintel'] = 'SimCaptureIntel' } do
        local value = GetCommandLineArg(arg, 1)
        if value then
            options[key] = tonumber(value[1])
        end
    end
    local script = GetCommandLineArg('/simscript', 1)
    options.SimCaptureScript = script and script[1]
    options.SimCaptureVelocity = HasCommandLineArg('/simvel')
    options.SimCaptureCombat = HasCommandLineArg('/simcombat')
    for index, info in sessionInfo.teamInfo do
        LOG('SIMCAP|ARMY|' .. index .. '|' .. tostring(info.ArmyName) .. '|human ' .. tostring(info.Human) .. '|ai ' .. tostring(info.AIPersonality) .. '|faction ' .. tostring(info.Faction) .. '|civilian ' .. tostring(info.Civilian or false))
    end
    return SimCaptureLaunchSinglePlayerSession(sessionInfo)
end

LOG('HOOKCHECK|/simcapturehook/lua/SinglePlayerLaunch.lua|ok')
