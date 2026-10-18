-- /simcombat (ScenarioInfo.Options.SimCaptureCombat): FIRE and DAMAGE lines from the engine methods every weapon
-- and entity class inherits; sim state only (it alone has moho.weapon_methods). Wrapped here,
-- before any Lua class copies them, in both the moho class table and its __spec table (as tools/lua-trace does).
--   FIRE tick unit weaponLabel target projectileBlueprint muzzleBone   (target = entity id, "x,y,z" or "none")
--   DAMAGE tick target instigator healthChange
if rawget(moho, 'weapon_methods') then
    local function wrapMethod(class, name, make)
        for _, t in { class, rawget(class, '__spec') or {} } do
            local original = rawget(t, name)
            if original then
                rawset(t, name, make(original))
            end
        end
    end
    local function id(entity)
        return entity and entity.GetEntityId and tostring(entity:GetEntityId()) or 'none'
    end
    wrapMethod(moho.weapon_methods, 'CreateProjectile', function(original)
        return function(self, muzzle)
            local proj = original(self, muzzle)
            if not ScenarioInfo.Options.SimCaptureCombat then
                return proj
            end
            local unit, target, where = self.unit, self:GetCurrentTarget(), nil
            if target and target.GetEntityId then
                where = id(target)
            else
                local p = self:GetCurrentTargetPos()
                where = p and string.format('%.3f,%.3f,%.3f', p[1], p[2], p[3]) or 'none'
            end
            LOG(string.format('FIRE %d %s %s %s %s %s', GetGameTick(), id(unit), tostring(self:GetBlueprint().Label),
                where, proj and tostring(proj:GetBlueprint().BlueprintId) or 'none', tostring(muzzle)))
            return proj
        end
    end)
    wrapMethod(moho.entity_methods, 'AdjustHealth', function(original)
        return function(self, instigator, delta)
            if ScenarioInfo.Options.SimCaptureCombat then
                LOG(string.format('DAMAGE %d %s %s %.4f', GetGameTick(), id(self), id(instigator), delta))
            end
            return original(self, instigator, delta)
        end
    end)
end

LOG('HOOKCHECK|/simcapturehook/lua/globalInit.lua|ok')
