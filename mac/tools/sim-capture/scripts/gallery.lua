-- Tier gallery: every buildable tech 2, tech 3 and experimental unit and structure, one faction per army.
-- Run with /simfactions 1,2,3,4 (army N gets faction N: UEF, Aeon, Cybran, Seraphim) and /nocivilians.
--   tick 1:   each army gets 1e6 mass and energy storage and income
--   tick 2:   structures in a grid at the army's start, mobile units in a grid 70 u toward the map centre
--   tick 60:  every structure with General.UpgradesTo is ordered to upgrade
--   tick 200: every mobile unit attack-moves to the map centre, so the four galleries fight
--   every 10 ticks: SHIELD tick unit health max for each unit with a shield
-- Logs "SIMSCRIPT tick spawn entity blueprint x z", "SIMSCRIPT tick spawnfail blueprint reason",
-- "SIMSCRIPT tick upgrade entity from to" and "SIMSCRIPT tick attackmove army count".
local FACTIONS = { 'UEF', 'AEON', 'CYBRAN', 'SERAPHIM' }
local TIERS = { TECH2 = true, TECH3 = true, EXPERIMENTAL = true }
local EXCLUDED = { CIVILIAN = true, OPERATION = true, INSIGNIFICANTUNIT = true, UNTARGETABLE = true,
    SATELLITE = true, POD = true, DUMMYUNIT = true }

local function galleryBlueprints(faction)
    local mobile, structure = {}, {}
    for id, bp in __blueprints do
        if type(id) == 'string' and not string.find(id, '/') and bp.Categories then
            local cats, tier, built, excluded = {}, false, false, false
            for _, c in bp.Categories do
                cats[c] = true
                tier = tier or TIERS[c]
                built = built or string.find(c, '^BUILTBY') ~= nil
                excluded = excluded or EXCLUDED[c]
            end
            if tier and built and not excluded and cats[faction] then
                if cats.MOBILE then
                    table.insert(mobile, id)
                elseif cats.STRUCTURE then
                    table.insert(structure, id)
                end
            end
        end
    end
    table.sort(mobile)
    table.sort(structure)
    return mobile, structure
end

local function waitUntil(tick)
    while GetGameTick() < tick do
        WaitTicks(1)
    end
end

function SimScript()
    local centre = { 256, 256 }
    local galleries = {}
    waitUntil(1)
    for index = 1, 4 do
        local brain = ArmyBrains[index]
        for _, kind in { 'MASS', 'ENERGY' } do
            brain:GiveStorage(kind, 1000000)
            brain:GiveResource(kind, 1000000)
        end
    end
    waitUntil(2)
    for index = 1, 4 do
        local brain = ArmyBrains[index]
        local x, z = brain:GetArmyStartPos()
        local dx, dz = centre[1] - x, centre[2] - z
        local length = math.sqrt(dx * dx + dz * dz)
        dx, dz = dx / length, dz / length
        local mobile, structure = galleryBlueprints(FACTIONS[index])
        local units = { mobile = {}, structure = {} }
        local function place(list, kind, originX, originZ, spacing)
            for i, bp in list do
                local column, row = math.mod(i - 1, 8) - 3.5, math.floor((i - 1) / 8)
                local px = originX + column * spacing * dz + row * spacing * dx
                local pz = originZ - column * spacing * dx + row * spacing * dz
                local ok, unit = pcall(CreateUnitHPR, bp, index, px, GetSurfaceHeight(px, pz), pz, 0, 0, 0)
                if ok and unit then
                    table.insert(units[kind], unit)
                    LOG(string.format('SIMSCRIPT %d spawn %s %s %g %g', GetGameTick(), tostring(unit:GetEntityId()), bp, px, pz))
                else
                    LOG(string.format('SIMSCRIPT %d spawnfail %s %s', GetGameTick(), bp, tostring(unit)))
                end
            end
        end
        place(structure, 'structure', x - dx * 20, z - dz * 20, 18)
        place(mobile, 'mobile', x + dx * 70, z + dz * 70, 14)
        galleries[index] = units
    end

    ForkThread(function()
        while true do
            for _, brain in ArmyBrains do
                for _, unit in brain:GetListOfUnits(categories.ALLUNITS, false) or {} do
                    local shield = unit.MyShield
                    if shield and not unit:IsDead() and shield.GetHealth then
                        LOG(string.format('SHIELD %d %s %g %g', GetGameTick(), tostring(unit:GetEntityId()),
                            shield:GetHealth(), shield:GetMaxHealth()))
                    end
                end
            end
            WaitTicks(10)
        end
    end)

    waitUntil(60)
    for _, units in galleries do
        for _, unit in units.structure do
            local target = not unit:IsDead() and unit:GetBlueprint().General.UpgradesTo
            if target and target ~= '' then
                local ok = pcall(IssueUpgrade, { unit }, target)
                LOG(string.format('SIMSCRIPT %d upgrade %s %s %s%s', GetGameTick(), tostring(unit:GetEntityId()),
                    unit:GetBlueprint().BlueprintId, target, ok and '' or ' failed'))
            end
        end
    end

    waitUntil(200)
    for index, units in galleries do
        local alive = {}
        for _, unit in units.mobile do
            if not unit:IsDead() then
                table.insert(alive, unit)
            end
        end
        if table.getn(alive) > 0 then
            pcall(IssueAggressiveMove, alive, { centre[1], GetSurfaceHeight(centre[1], centre[2]), centre[2] })
        end
        LOG(string.format('SIMSCRIPT %d attackmove %d %d', GetGameTick(), index, table.getn(alive)))
    end
end
