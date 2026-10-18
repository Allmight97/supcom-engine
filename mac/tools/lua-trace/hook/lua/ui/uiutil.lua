-- /tracemenuskirmish: keep the lobby's Launch button (a local of lobby.lua) where the menu hook can press it.
if HasCommandLineArg('/tracemenuskirmish') then
    local TraceMenuCreateButtonStd = CreateButtonStd
    function CreateButtonStd(parent, filename, label, pointSize, textOffsetVert, textOffsetHorz, clickCue, rolloverCue)
        local button = TraceMenuCreateButtonStd(parent, filename, label, pointSize, textOffsetVert, textOffsetHorz, clickCue, rolloverCue)
        if label == '<LOC lobui_0212>Launch' then
            rawset(_G, 'TraceMenuLaunchButton', button)
        end
        return button
    end
end

LOG('HOOKCHECK|/tracehook/lua/ui/uiutil.lua|ok')
