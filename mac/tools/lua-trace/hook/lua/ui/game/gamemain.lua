-- /autosave SECONDS NAME saves at that game time; /autoexit SECONDS exits normally at that game time.
local TraceAutoOnFirstUpdate = OnFirstUpdate

function OnFirstUpdate()
    TraceAutoOnFirstUpdate()
    if HasCommandLineArg('/autosave') or HasCommandLineArg('/autoexit') then
        ForkThread(TraceAutoPilot)
    end
end

function TraceAutoPilot()
    local save = GetCommandLineArg('/autosave', 2)
    local exit = GetCommandLineArg('/autoexit', 1)
    local saving = false
    while true do
        local now = GameTime()
        if save and now >= tonumber(save[1]) then
            local name = save[2]
            save = nil
            local path = GetSpecialFilePath(import('/lua/user/prefs.lua').GetCurrentProfile().Name, name, 'SaveGame')
            saving = true
            InternalSaveGame(path, name, function(worked, errmsg)
                saving = false
                LOG('autorun: ' .. (worked and 'saved ' .. path or 'save failed ' .. tostring(errmsg)))
            end)
        end
        if exit and not saving and now >= tonumber(exit[1]) then
            LOG(string.format('autorun: exiting at game time %d s', now))
            ExitApplication()
            return
        end
        WaitSeconds(1)
    end
end

LOG('HOOKCHECK|/tracehook/lua/ui/game/gamemain.lua|ok')
