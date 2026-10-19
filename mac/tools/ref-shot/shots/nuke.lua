-- A UEF ACU's death explosion (the nuke's dome): before, then 1.5 s and 5 s of game time after the kill.
-- Run with /reffactions 1 /refwait 20 /nofog /refclean and GAME_RUN_WINDOW="1600 900" (OSC's capture size); the
-- frames are paused, so effects hold still. OSC: tools/ref-shot/osc-shot nuke NAME FRAME X1MP_006 /refwait 20 /nofog
-- /refclean with FRAME alive 1730, kill-1500ms 2270, kill-5000ms 2930.
local acu = { 74.5, 17.7188, 62.5 }
local hpr = { 0.785, 0.7, 0 }
RefShots = {
    { name = 'alive', pos = acu, hpr = hpr, zoom = 90 },
    { name = 'kill-1500ms', pos = acu, hpr = hpr, zoom = 90, sim = { action = 'kill' }, resume = 1.5 },
    { name = 'kill-5000ms', pos = acu, hpr = hpr, zoom = 90, resume = 3.5 },
}
