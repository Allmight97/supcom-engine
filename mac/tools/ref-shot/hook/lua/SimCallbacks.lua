-- Sim side of a shot's sim = { action = ... } (sent with SimCallback): orders for army 1's ACU, offsets from it.
--   { action = 'move', dx = 14, dz = 14 }   { action = 'build', blueprint = 'ueb1101', dx = 10, dz = 0 }
--   { action = 'kill' }: the ACU dies at once, as Ctrl-K's self-destruct does when its countdown ends
--   { action = 'emitters', list = { { bp = PATH, x = 0, y = 2, z = 0, lifetime = 20, scale = 2 }, ... } }: emitters at
--   the ACU, offset; lifetime (ticks) replaces the blueprint's lifetime curve, scale calls ScaleEmitter
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
    elseif data.action == 'kill' then
        acu:Kill()
    elseif data.action == 'emitters' then
        for _, e in data.list do
            local effect = CreateEmitterAtEntity(acu, acu:GetArmy(), e.bp):OffsetEmitter(e.x or 0, e.y or 0, e.z or 0)
            if e.lifetime then
                effect:SetEmitterCurveParam('LIFETIME_CURVE', e.lifetime, 0)
            end
            if e.scale then
                effect:ScaleEmitter(e.scale)
            end
            LOG(string.format('REFSHOT|PROBE|%s|%g,%g,%g|lifetime %s|scale %s', e.bp, e.x or 0, e.y or 0, e.z or 0,
                tostring(e.lifetime), tostring(e.scale)))
        end
    end
    LOG(string.format('REFSHOT|SIM|%d|%s|%s|%g,%g', GetGameTick(), data.action, tostring(data.blueprint), x, z))
end

LOG('HOOKCHECK|/refshothook/lua/SimCallbacks.lua|ok')
