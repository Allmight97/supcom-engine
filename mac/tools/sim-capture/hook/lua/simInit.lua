-- Appended to /lua/simInit.lua: from the start of the session, logs every live unit every N ticks (/siminterval,
-- default 5; with /simvel also "VEL tick entity vx vy vz" from GetVelocity), runs /simscript NAME's SimScript()
-- and each AI brain's threat queries every /simthreat N ticks (default 600), then "SIMCAP|END|<tick>" at the end tick
-- (ScenarioInfo.Options.SimCaptureEndTick from /simticks, default 3000).
--   MOTION tick entity blueprint army x y z heading layer moving     (heading = Entity:GetHeading(), moving 0/1;
--                                                                    the format of sim_probe --motion-log)
--   THREAT tick army threatType (x,z,threat),(x,z,threat),...       (GetThreatsAroundPosition(start, 16, true, type); every key)
--   HIGHEST tick army (x,y,z) threat                                  (GetHighestThreatPosition(16, true, 'Overall'))
--   ECON tick army mass income requested stored ratio energy income requested stored ratio units bp=n,...  (/simecon N)
--   INTEL tick army entity blueprint radar sonar omni seen seenever fake [blip x,y,z]  (/simintel N; AI armies,
--                                                                    each enemy unit they hold a blip for)
--   FIRE, DAMAGE, DEATH (/simcombat; hook/lua/globalInit.lua and hook/lua/sim/Unit.lua)
local THREAT_TYPES = { 'Overall', 'Land', 'Structures', 'Commander', 'Unknown' }
local format, concat, tostring = string.format, table.concat, tostring

local function num(v)
    return v and format('%.6g', v) or 'nil'
end

local function list(t)
    if type(t) ~= 'table' then
        return type(t) == 'number' and num(t) or tostring(t)
    end
    local keys = {}
    for k in t do
        table.insert(keys, k)
    end
    table.sort(keys, function(a, b)
        if type(a) == type(b) then return a < b end
        return type(a) == 'number'
    end)
    local parts = {}
    for _, k in keys do
        local v = t[k]
        local text = type(v) == 'table' and ('(' .. list(v) .. ')') or (type(v) == 'number' and num(v) or tostring(v))
        table.insert(parts, type(k) == 'number' and text or (tostring(k) .. '=' .. text))
    end
    return concat(parts, ',')
end

local function LogUnits(tick)
    local units = {}
    for _, brain in ArmyBrains do
        for _, unit in brain:GetListOfUnits(categories.ALLUNITS, false) or {} do
            if not unit:IsDead() then
                table.insert(units, unit)
            end
        end
    end
    table.sort(units, function(a, b) return a:GetEntityId() < b:GetEntityId() end)
    for _, unit in units do
        local pos = unit:GetPosition()
        LOG(format('MOTION %d %s %s %d %s %s %s %s %s %d',
            tick, tostring(unit:GetEntityId()), unit:GetBlueprint().BlueprintId, unit:GetArmy(),
            num(pos[1]), num(pos[2]), num(pos[3]), num(unit:GetHeading()),
            tostring(unit:GetCurrentLayer()), unit:IsUnitState('Moving') and 1 or 0))
        if ScenarioInfo.Options.SimCaptureVelocity then
            local vx, vy, vz = unit:GetVelocity()
            LOG(format('VEL %d %s %s %s %s', tick, tostring(unit:GetEntityId()), num(vx), num(vy), num(vz)))
        end
    end
end

local function LogThreats(tick)
    for index, brain in ArmyBrains do
        if brain.BrainType == 'AI' then
            local x, z = brain:GetArmyStartPos()
            local start = { x, GetSurfaceHeight(x, z), z }
            for _, threatType in THREAT_TYPES do
                local ok, threats = pcall(brain.GetThreatsAroundPosition, brain, start, 16, true, threatType)
                LOG(format('THREAT %d %d %s %s', tick, index, threatType, ok and list(threats) or ('error:' .. tostring(threats))))
            end
            local ok, pos, threat = pcall(brain.GetHighestThreatPosition, brain, 16, true, 'Overall')
            if ok then
                LOG(format('HIGHEST %d %d %s %s', tick, index, type(pos) == 'table' and list({ pos }) or tostring(pos), num(threat)))
            else
                LOG(format('HIGHEST %d %d error:%s', tick, index, tostring(pos)))
            end
        end
    end
end

local function LogEconomy(tick)
    for index, brain in ArmyBrains do
        local counts, units = {}, brain:GetListOfUnits(categories.ALLUNITS, false) or {}
        for _, unit in units do
            if not unit:IsDead() then
                local id = unit:GetBlueprint().BlueprintId
                counts[id] = (counts[id] or 0) + 1
            end
        end
        local parts = {}
        for id, n in counts do
            table.insert(parts, id .. '=' .. n)
        end
        table.sort(parts)
        LOG(format('ECON %d %d mass %s %s %s %s energy %s %s %s %s units %s', tick, index,
            num(brain:GetEconomyIncome('MASS')), num(brain:GetEconomyRequested('MASS')),
            num(brain:GetEconomyStored('MASS')), num(brain:GetEconomyStoredRatio('MASS')),
            num(brain:GetEconomyIncome('ENERGY')), num(brain:GetEconomyRequested('ENERGY')),
            num(brain:GetEconomyStored('ENERGY')), num(brain:GetEconomyStoredRatio('ENERGY')), concat(parts, ',')))
    end
end

local function LogIntel(tick)
    for index, brain in ArmyBrains do
        if brain.BrainType == 'AI' then
            for other, enemy in ArmyBrains do
                if other ~= index and IsEnemy(index, other) then
                    for _, unit in enemy:GetListOfUnits(categories.ALLUNITS, false) or {} do
                        if not unit:IsDead() then
                            local blip = unit:GetBlip(index)
                            if blip then
                                local up, bp = unit:GetPosition(), blip:GetPosition()
                                local moved = (math.abs(up[1] - bp[1]) + math.abs(up[3] - bp[3]) > 0.01)
                                    and format(' blip %s,%s,%s', num(bp[1]), num(bp[2]), num(bp[3])) or ''
                                LOG(format('INTEL %d %d %s %s radar %d sonar %d omni %d seen %d seenever %d fake %d%s',
                                    tick, index, tostring(unit:GetEntityId()), unit:GetBlueprint().BlueprintId,
                                    blip:IsOnRadar(index) and 1 or 0, blip:IsOnSonar(index) and 1 or 0,
                                    blip:IsOnOmni(index) and 1 or 0, blip:IsSeenNow(index) and 1 or 0,
                                    blip:IsSeenEver(index) and 1 or 0, blip:IsKnownFake(index) and 1 or 0, moved))
                            end
                        end
                    end
                end
            end
        end
    end
end

local function SimCapture()
    LOG('SIMCAP|START|' .. GetGameTick())
    local interval = ScenarioInfo.Options.SimCaptureInterval or 5
    local script = ScenarioInfo.Options.SimCaptureScript
    if script then
        doscript('/sim-capture/scripts/' .. script .. '.lua')
        ForkThread(SimScript)
    end
    while true do
        local tick = GetGameTick()
        if math.mod(tick, interval) == 0 then
            LogUnits(tick)
        end
        local options = ScenarioInfo.Options
        if options.SimCaptureEconomy and math.mod(tick, options.SimCaptureEconomy) == 0 then
            LogEconomy(tick)
        end
        if options.SimCaptureIntel and math.mod(tick, options.SimCaptureIntel) == 0 then
            LogIntel(tick)
        end
        if tick > 0 and math.mod(tick, ScenarioInfo.Options.SimCaptureThreat or 600) == 0 then
            LogThreats(tick)
        end
        if tick >= (ScenarioInfo.Options.SimCaptureEndTick or 3000) then
            LOG('SIMCAP|END|' .. tick)
            return
        end
        WaitTicks(1)
    end
end

local SimCaptureBeginSession = BeginSession
function BeginSession()
    SimCaptureBeginSession()
    ForkThread(SimCapture)
end

LOG('HOOKCHECK|/simcapturehook/lua/simInit.lua|ok')
