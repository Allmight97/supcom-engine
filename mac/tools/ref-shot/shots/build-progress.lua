-- The ACU builds a power generator about 8 u from it; one frame per second of building. Run with /reffactions 1
-- (UEF, so ueb1101 matches the ACU), /nofog /refclean; REFSHOT|BUILD lines log the fraction complete per tick.
local acu = { 74.5, 17.7188, 62.5 }
local hpr = { 0.785, 0.9, 0 }
RefShots = {
    { name = 'build-00', pos = acu, hpr = hpr, zoom = 30, sim = { action = 'build', blueprint = 'ueb1101', dx = -6, dz = 6 }, resume = 0.3 },
    { name = 'build-01', pos = acu, hpr = hpr, zoom = 30, resume = 1 },
    { name = 'build-02', pos = acu, hpr = hpr, zoom = 30, resume = 1 },
    { name = 'build-03', pos = acu, hpr = hpr, zoom = 30, resume = 1 },
    { name = 'build-04', pos = acu, hpr = hpr, zoom = 30, resume = 1 },
    { name = 'build-05', pos = acu, hpr = hpr, zoom = 30, resume = 1 },
    { name = 'build-06', pos = acu, hpr = hpr, zoom = 30, resume = 1 },
    { name = 'build-07', pos = acu, hpr = hpr, zoom = 30, resume = 1 },
    { name = 'build-08', pos = acu, hpr = hpr, zoom = 30, resume = 1 },
    { name = 'build-09', pos = acu, hpr = hpr, zoom = 30, resume = 1 },
    { name = 'build-10', pos = acu, hpr = hpr, zoom = 30, resume = 1 },
    { name = 'build-11', pos = acu, hpr = hpr, zoom = 30, resume = 1 },
    { name = 'build-12', pos = acu, hpr = hpr, zoom = 30, resume = 1 },
}
