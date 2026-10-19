-- build-progress's power generator, framed the same, one frame /refat S seconds after building starts.
-- The original ignores resumes as short as 0.2 s, so a sweep is one run per moment, for example
-- /refat 3.0, 3.2, ... 5.0 (about 31% to 52% built at 10.4% a second); REFSHOT|BUILD gives each frame's fraction.
-- Run after the ACU's warp-in: /reffactions 1 /refwait 20 /nofog /refclean /refat S.
local acu = { 74.5, 17.7188, 62.5 }
local hpr = { 0.785, 0.9, 0 }
local at = tonumber((GetCommandLineArg('/refat', 1) or { '3' })[1])
RefShots = {
    { name = 'start', pos = acu, hpr = hpr, zoom = 30, sim = { action = 'build', blueprint = 'ueb1101', dx = -6, dz = 6 }, resume = 0.3 },
    { name = string.format('t%02d', math.floor(at * 10 + 0.5)), pos = acu, hpr = hpr, zoom = 30, resume = at - 0.3 },
}
