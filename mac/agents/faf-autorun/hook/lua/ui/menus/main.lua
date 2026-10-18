local AutorunCreateUI = CreateUI
local autorunLoaded = false

function CreateUI()
    AutorunCreateUI()
    local load = GetCommandLineArg('/autoload', 1)
    if load and not autorunLoaded then
        autorunLoaded = true
        ForkThread(function()
            WaitSeconds(2)
            local path = GetSpecialFilePath(Prefs.GetCurrentProfile().Name, load[1], 'SaveGame')
            LOG('faf-autorun: loading ' .. path)
            local worked, errmsg, detail = LoadSavedGame(path)
            if not worked then
                LOG('faf-autorun: load failed ' .. tostring(errmsg) .. ' ' .. tostring(detail))
            end
        end)
    end
end

LOG('HOOKCHECK|/autorunhook/lua/ui/menus/main.lua|ok')
