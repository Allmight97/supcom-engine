local AutorunLaunchSinglePlayerSession = LaunchSinglePlayerSession

local function AutorunAddLobbyOptions(sessionInfo)
    local options = sessionInfo.scenarioInfo.Options
    options.Ratings = options.Ratings or {}
    options.ClanTags = options.ClanTags or {}
    for _, info in sessionInfo.teamInfo do
        if info.PlayerName and not info.Civilian then
            options.Ratings[info.PlayerName] = options.Ratings[info.PlayerName] or 0
        end
    end
    for _, mod in import('/lua/mods.lua').GetGameMods() do
        local file = mod.location .. '/lua/AI/LobbyOptions/lobbyoptions.lua'
        if exists(file) then
            for _, option in import(file).AIOpts do
                if options[option.key] == nil then
                    local value = option.values[option.default]
                    options[option.key] = type(value) == 'table' and value.key or value
                end
            end
        end
    end
end

function LaunchSinglePlayerSession(sessionInfo)
    local ai = GetCommandLineArg('/autoai', 1)
    local count = GetCommandLineArg('/autoais', 1)
    if ai or count then
        local limit = count and tonumber(count[1])
        local kept, ais = {}, 0
        for _, info in sessionInfo.teamInfo do
            if info.Human or info.Civilian then
                table.insert(kept, info)
            else
                ais = ais + 1
                if not limit or ais <= limit then
                    if ai then
                        info.AIPersonality = ai[1]
                        info.PlayerName = GetRandomName(info.Faction, ai[1])
                    end
                    table.insert(kept, info)
                end
            end
        end
        sessionInfo.teamInfo = kept
    end
    AutorunAddLobbyOptions(sessionInfo)
    for _, info in sessionInfo.teamInfo do
        if not info.Human and not info.Civilian then
            LOG('faf-autorun: army ' .. tostring(info.ArmyName) .. ' AI ' .. tostring(info.AIPersonality) .. ' named ' .. tostring(info.PlayerName))
        end
    end
    return AutorunLaunchSinglePlayerSession(sessionInfo)
end

LOG('HOOKCHECK|/autorunhook/lua/SinglePlayerLaunch.lua|ok')
