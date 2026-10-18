-- S2 motion checks for army 1 (the idle human), relative to its start position (x, z):
--   tick 40: a T1 land factory and four power generators (a small base), a T1 tank and an engineer
--   tick 50: tank moves 60 u straight ahead (+z); tick 300: back to its start (180 degree turn);
--            tick 500: a point 3 u to its side
--   tick 60: engineer crosses the base to its far side
--   tick 650: twelve tanks; tick 700: six get IssueFormMove, six a plain IssueMove, to the same point
-- Every spawn and order is logged as "SIMSCRIPT tick event entity|count blueprint|x z".
function SimScript()
    local brain = ArmyBrains[1]
    local x, z = brain:GetArmyStartPos()
    local function point(dx, dz)
        return { x + dx, GetSurfaceHeight(x + dx, z + dz), z + dz }
    end
    local function spawn(bp, dx, dz)
        local p = point(dx, dz)
        local unit = CreateUnitHPR(bp, brain:GetArmyIndex(), p[1], p[2], p[3], 0, 0, 0)
        LOG(string.format('SIMSCRIPT %d spawn %s %s %g %g', GetGameTick(), tostring(unit:GetEntityId()), bp, p[1], p[3]))
        return unit
    end
    local function move(kind, units, dx, dz)
        local p = point(dx, dz)
        local ok, err
        if kind == 'formmove' then
            ok, err = pcall(IssueFormMove, units, p, 'AttackFormation', 0)
        else
            ok, err = pcall(IssueMove, units, p)
        end
        if not ok then
            LOG('SIMSCRIPT ' .. GetGameTick() .. ' error ' .. kind .. ' ' .. tostring(err))
        end
        LOG(string.format('SIMSCRIPT %d %s %d units %g %g', GetGameTick(), kind, table.getn(units), p[1], p[3]))
    end
    local function waitUntil(tick)
        while GetGameTick() < tick do
            WaitTicks(1)
        end
    end

    waitUntil(40)
    spawn('ueb0101', -20, 40)
    for _, offset in { { -27, 34 }, { -13, 34 }, { -27, 46 }, { -13, 46 } } do
        spawn('ueb1101', offset[1], offset[2])
    end
    local tank = spawn('uel0201', 20, 10)
    local engineer = spawn('uel0105', -20, 20)

    waitUntil(50)
    move('move', { tank }, 20, 70)
    waitUntil(60)
    move('move', { engineer }, -20, 62)
    waitUntil(300)
    move('move', { tank }, 20, 10)
    waitUntil(500)
    move('move', { tank }, 23, 10)

    waitUntil(650)
    local formed, plain = {}, {}
    for i = 0, 5 do
        table.insert(formed, spawn('uel0201', 40 + math.mod(i, 3) * 4, 20 + math.floor(i / 3) * 4))
        table.insert(plain, spawn('uel0201', 60 + math.mod(i, 3) * 4, 20 + math.floor(i / 3) * 4))
    end
    waitUntil(700)
    move('formmove', formed, 55, 100)
    move('move', plain, 55, 100)
end
