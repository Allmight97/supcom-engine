-- Emitter blueprints set down beside army 1's ACU, unchanged and altered, one live frame at zoom 30: which of them
-- the original draws. Run after the warp-in with /refdump DIR: /reffactions 1 /refwait 20 /nofog /refclean /refdump DIR.
local acu = { 74.5, 17.7188, 62.5 }
local hpr = { 0.785, 0.9, 0 }
local glow = '/effects/emitters/flashing_blue_glow_01_emit.bp'
local cube = '/effects/emitters/build_terran_glow_01_emit.bp'
RefShots = {
    { name = 'probe', pos = acu, hpr = hpr, zoom = 30, resume = 1, pause = false, sim = { action = 'emitters', list = {
        { bp = glow, x = -6, y = 2 },
        { bp = glow, x = -3, y = 2, lifetime = 20 },
        { bp = glow, x = 3, y = 2, scale = 4 },
        { bp = cube, x = 6, y = 2 },
        { bp = cube, x = 0, y = 2, z = 5, lifetime = 20 },
        { bp = '/effects/emitters/teleport_commander_mist_01_emit.bp', x = 0, y = 2, z = -5 },
    } } },
}
