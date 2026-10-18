-- In-game UI reference (run with /refui so the UI stays visible, and /refwait so the ACU has warped in).
-- select = a category expression for UISelectionByCategory; false clears the selection.
local acu = { 74.5, 17.7188, 62.5 }
RefShots = {
    { name = 'bottom-bar', pos = acu, hpr = { 0, 1.0, 0 }, zoom = 80, select = false },
    { name = 'acu-selected', pos = acu, hpr = { 0, 1.0, 0 }, zoom = 80, select = 'COMMAND' },
    { name = 'acu-selected-close', pos = acu, hpr = { 0.785, 0.9, 0 }, zoom = 40, select = 'COMMAND' },
}
