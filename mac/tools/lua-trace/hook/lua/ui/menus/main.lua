-- /tracemenuskirmish: once the main menu is up, run the menu's own ButtonSkirmish (CreateUI defines it
-- at module level; it hides the menu and hosts a lobby on LastScenario), add easy AIs (/tracemenuais N,
-- default 1) in slots 2.., log
-- REFSHOT|READY|lobby for a screenshot, then press the lobby's Launch button.
-- /autoload NAME loads save NAME from the main menu instead.
local TraceMenuCreateUI = CreateUI
local traceMenuStarted = false

function CreateUI()
    TraceMenuCreateUI()
    local load = GetCommandLineArg('/autoload', 1)
    if load and not traceMenuStarted then
        traceMenuStarted = true
        ForkThread(function()
            WaitSeconds(2)
            local path = GetSpecialFilePath(import('/lua/user/prefs.lua').GetCurrentProfile().Name, load[1], 'SaveGame')
            LOG('autorun: loading ' .. path)
            local worked, errmsg, detail = LoadSavedGame(path)
            if not worked then
                LOG('autorun: load failed ' .. tostring(errmsg) .. ' ' .. tostring(detail))
            end
        end)
    end
    if not HasCommandLineArg('/tracemenuskirmish') or traceMenuStarted then
        return
    end
    traceMenuStarted = true
    ForkThread(function()
        WaitSeconds(3)
        local Prefs = import('/lua/user/prefs.lua')
        local name = Prefs.GetCurrentProfile().Name or 'Unknown'
        LOG('TRACEMENU|skirmish|' .. tostring(Prefs.GetFromCurrentProfile('LastScenario')))
        ButtonSkirmish()
        WaitSeconds(4)
        LOG('TRACEMENU|add-ai')
        local lobby = import('/lua/ui/lobby/lobby.lua')
        local ais = GetCommandLineArg('/tracemenuais', 1)
        for slot = 2, 1 + (ais and tonumber(ais[1]) or 1) do
            lobby.HostTryAddPlayer(lobby.FindIDForName(name), slot, 'AI: Easy', false, 'easy', false, false, false)
        end
        WaitSeconds(3)
        LOG('REFSHOT|READY|lobby')
        WaitSeconds(4)
        LOG('TRACEMENU|launch')
        local button = rawget(_G, 'TraceMenuLaunchButton')
        button.OnClick(button)
    end)
end

LOG('HOOKCHECK|/tracehook/lua/ui/menus/main.lua|ok')
