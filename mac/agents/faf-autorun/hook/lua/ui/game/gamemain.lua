local AutorunOnFirstUpdate = OnFirstUpdate

function OnFirstUpdate()
    AutorunOnFirstUpdate()
    ForkThread(AutorunPilot)
end

function AutorunPilot()
    local save = GetCommandLineArg('/autosave', 2)
    local exit = GetCommandLineArg('/autoexit', 1)
    local beat = 0
    local saving = false
    LOG('faf-autorun: session started')
    while true do
        local now = GameTime()
        if now >= beat then
            LOG(string.format('faf-autorun: game time %d s', now))
            beat = (math.floor(now / 60) + 1) * 60
        end
        if save and now >= tonumber(save[1]) then
            local name = save[2]
            save = nil
            local path = GetSpecialFilePath(Prefs.GetCurrentProfile().Name, name, 'SaveGame')
            saving = true
            InternalSaveGame(path, name, function(worked, errmsg)
                saving = false
                if worked then
                    LOG('faf-autorun: saved ' .. path)
                else
                    LOG('faf-autorun: save failed ' .. tostring(errmsg))
                end
            end)
        end
        if exit and not saving and now >= tonumber(exit[1]) then
            LOG(string.format('faf-autorun: exiting at game time %d s', now))
            ExitApplication()
            return
        end
        WaitSeconds(1)
    end
end

LOG('HOOKCHECK|/autorunhook/lua/ui/game/gamemain.lua|ok')
