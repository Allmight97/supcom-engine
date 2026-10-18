-- HUD with the ACU selected, a Lua move order ~20 u away, then the walk 3 s later. Run with /refui.
RefShots = {
    { name = 'move-order', select = 'COMMAND', sim = { action = 'move', dx = 14, dz = 14 }, resume = 0.3 },
    { name = 'move-walking', select = 'COMMAND', resume = 3 },
}
