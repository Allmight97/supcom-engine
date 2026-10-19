-- The UEF ACU's warp-in at about 1 s and 2 s after the game starts (no /refwait), framed as build-progress.
-- Run with /reffactions 1 /nofog /refclean.
local acu = { 74.5, 17.7188, 62.5 }
local hpr = { 0.785, 0.9, 0 }
RefShots = {
    { name = 'warpin-1s', pos = acu, hpr = hpr, zoom = 30, resume = 1 },
    { name = 'warpin-2s', pos = acu, hpr = hpr, zoom = 30, resume = 1 },
}
