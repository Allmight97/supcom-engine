local RefShotOnFirstUpdate = OnFirstUpdate

function OnFirstUpdate()
    RefShotOnFirstUpdate()
    ForkThread(RefShotRun)
end

local function RefShotFields(value, prefix)
    if type(value) ~= 'table' then
        return prefix .. '=' .. tostring(value)
    end
    local parts = {}
    for k, v in value do
        table.insert(parts, RefShotFields(v, prefix .. (prefix == '' and '' or '.') .. tostring(k)))
    end
    table.sort(parts)
    return table.concat(parts, ' ')
end

function RefShotRun()
    local set = GetCommandLineArg('/refshots', 1)
    if not set then
        return
    end
    doscript('/ref-shot/shots/' .. set[1] .. '.lua')
    WaitSeconds(2)
    local shadows = GetCommandLineArg('/refshadows', 1)
    if shadows then
        ConExecute('shadow_Fidelity ' .. shadows[1])
        LOG('REFSHOT|SHADOWS|' .. shadows[1])
    end
    if HasCommandLineArg('/refclean') then
        for _, command in { 'ren_Ranges false', 'ui_RenderIcons false', 'ren_MapBorderClear', 'ren_PlayableBoundary false' } do
            ConExecute(command)
        end
        for _, view in import('/lua/ui/game/worldview.lua').GetWorldViews() do
            view:EnableResourceRendering(false)
        end
        LOG('REFSHOT|CLEAN')
    end
    if not HasCommandLineArg('/refui') then
        HideGameUI('on')
    end
    local wait = GetCommandLineArg('/refwait', 1)
    if wait then
        WaitSeconds(tonumber(wait[1]))
    end
    SessionRequestPause()
    WaitSeconds(2)
    for _, command in rawget(_G, 'RefConsole') or {} do
        ConExecute(command)
        LOG('REFSHOT|CONSOLE|' .. command)
    end
    for _, shot in RefShots do
        if HasCommandLineArg('/refbare') then
            ConExecute('ren_Decals false')
            ConExecute('ren_MeshStatic false')
            LOG('REFSHOT|BARE')
        end
        if shot.select then
            UISelectionByCategory(shot.select, false, false, false, false)
        elseif shot.select == false then
            SelectUnits({})
        end
        if shot.sim then
            SimCallback({ Func = 'RefShot', Args = shot.sim })
        end
        if shot.resume then
            SessionResume()
            WaitSeconds(shot.resume)
            SessionRequestPause()
            WaitSeconds(0.5)
        end
        for _, command in shot.console or {} do
            ConExecute(command)
            LOG('REFSHOT|CONSOLE|' .. command)
        end
        local camera = GetCamera('WorldCamera')
        if shot.pos then
            camera:SnapTo(Vector(shot.pos[1], shot.pos[2], shot.pos[3]), shot.hpr, shot.zoom)
        end
        WaitSeconds(3)
        LOG('REFSHOT|SETTINGS|' .. shot.name .. '|' .. RefShotFields(camera:SaveSettings(), '')
            .. ' MaxZoom=' .. tostring(camera:GetMaxZoom()) .. ' MinZoom=' .. tostring(camera:GetMinZoom())
            .. ' GameTime=' .. tostring(GameTime()))
        LOG('REFSHOT|READY|' .. shot.name)
        WaitSeconds(4)
    end
    LOG('REFSHOT|END')
end

-- /refui: pause without the "Game Paused" banner (tabs.OnPause), so UI shots show the normal HUD.
local RefShotOnPause = OnPause
function OnPause(pausedBy, timeoutsRemaining)
    if not HasCommandLineArg('/refui') then
        return RefShotOnPause(pausedBy, timeoutsRemaining)
    end
    PauseSound("World", true)
    PauseSound("Music", true)
    PauseVoice("VO", true)
end

LOG('HOOKCHECK|/refshothook/lua/ui/game/gamemain.lua|ok')
