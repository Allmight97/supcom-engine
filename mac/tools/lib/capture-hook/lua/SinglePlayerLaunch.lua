-- Drops repeated army names (FAF's command-line launch adds NEUTRAL_CIVILIAN itself as well as from the map),
-- then logs the session the game will start, after every other hook changed it (this hook is mounted first, so
-- its wrapper runs last): SETUP|ARMY|index|name|human|ai|faction|civilian, SETUP|SEED|n, SETUP|OPTIONS|key=value,...
assert(LaunchSinglePlayerSession, 'SinglePlayerLaunch.lua has no LaunchSinglePlayerSession')
local CaptureLaunchSinglePlayerSession = LaunchSinglePlayerSession

function LaunchSinglePlayerSession(sessionInfo)
    local armies, names = {}, {}
    for _, info in sessionInfo.teamInfo do
        if not names[info.ArmyName] then
            names[info.ArmyName] = true
            table.insert(armies, info)
        end
    end
    sessionInfo.teamInfo = armies
    if HasCommandLineArg('/simspeed') then
        sessionInfo.scenarioInfo.Options.GameSpeed = 'adjustable'
    end
    for index, info in sessionInfo.teamInfo do
        LOG(string.format('SETUP|ARMY|%d|%s|%s|%s|%s|%s', index, tostring(info.ArmyName), tostring(info.Human or false),
            tostring(info.AIPersonality or ''), tostring(info.Faction), tostring(info.Civilian or false)))
    end
    LOG('SETUP|SEED|' .. tostring(sessionInfo.RandomSeed))
    local options = {}
    for key, value in sessionInfo.scenarioInfo.Options or {} do
        if type(value) ~= 'table' then
            table.insert(options, tostring(key) .. '=' .. tostring(value))
        end
    end
    table.sort(options)
    LOG('SETUP|OPTIONS|' .. table.concat(options, ','))
    return CaptureLaunchSinglePlayerSession(sessionInfo)
end

LOG('HOOKCHECK|/capturehook/lua/SinglePlayerLaunch.lua|ok')
