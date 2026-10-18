-- Sim side of a shot's sim = { action = ... } (sent with SimCallback): orders for army 1's ACU, offsets from it.
--   { action = 'move', dx = 14, dz = 14 }   { action = 'build', blueprint = 'ueb1101', dx = 10, dz = 0 }
local RefShotDoCallback = DoCallback

function DoCallback(name, data, units)
    if name ~= 'RefShot' then
        return RefShotDoCallback(name, data, units)
    end
    local acu = ArmyBrains[1]:GetListOfUnits(categories.COMMAND, false)[1]
    local p = acu:GetPosition()
    local x, z = p[1] + (data.dx or 0), p[3] + (data.dz or 0)
    local target = { x, GetSurfaceHeight(x, z), z }
    if data.action == 'move' then
        IssueMove({ acu }, target)
    elseif data.action == 'build' then
        IssueBuildMobile({ acu }, target, data.blueprint, {})
    end
    LOG(string.format('REFSHOT|SIM|%d|%s|%s|%g,%g', GetGameTick(), data.action, tostring(data.blueprint), x, z))
end

LOG('HOOKCHECK|/refshothook/lua/SimCallbacks.lua|ok')
