-- /simcombat: DEATH lines (FIRE and DAMAGE come from globalInit.lua, on the engine methods).
--   DEATH tick unit blueprint killer
local SimCaptureOnKilled = Unit.OnKilled

local function SimCaptureId(entity)
    return entity and entity.GetEntityId and tostring(entity:GetEntityId()) or 'none'
end

Unit.OnKilled = function(self, instigator, type, overkillRatio)
    if ScenarioInfo.Options.SimCaptureCombat then
        LOG(string.format('DEATH %d %s %s %s', GetGameTick(), SimCaptureId(self), self:GetBlueprint().BlueprintId, SimCaptureId(instigator)))
    end
    return SimCaptureOnKilled(self, instigator, type, overkillRatio)
end

LOG('HOOKCHECK|/simcapturehook/lua/sim/Unit.lua|ok')
