-- A lobby launch creates the map's civilian armies (customprops.ExtraArmies, for example ARMY_9 and
-- NEUTRAL_CIVILIAN); the command-line launch the capture tools use reads only teams.ExtraArmies, so it
-- creates none. Read customprops too, unless /nocivilians.
assert(GetExtraArmies, 'maputil.lua has no GetExtraArmies')
local CaptureGetExtraArmies = GetExtraArmies

function GetExtraArmies(scenario)
    local armies = CaptureGetExtraArmies(scenario)
    local props = scenario.Configurations.standard and scenario.Configurations.standard.customprops
    if armies or HasCommandLineArg('/nocivilians') or not (props and props.ExtraArmies) then
        return armies
    end
    return STR_GetTokens(props.ExtraArmies, ' ')
end

LOG('HOOKCHECK|/capturehook/lua/ui/maputil.lua|ok')
