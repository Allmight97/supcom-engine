-- Started from the hooked front-end and in-game modules; logs the game cursor for tools/mouse-probe/run.
local function logpos(x, y) LOG(string.format('MOUSEPROBE|pos|%d|%d', x, y)) end
if not rawget(_G, 'MouseProbeStarted') then
    rawset(_G, 'MouseProbeStarted', true)
    ForkThread(function()
        local frame, rootHooked
        while true do
            local root = GetFrame(0)
            if root then
                local size = root.Width() .. 'x' .. root.Height()
                if size ~= frame then frame = size; LOG('MOUSEPROBE|frame|' .. size) end
                if rootHooked ~= root then
                    rootHooked = root
                    local old = root.HandleEvent
                    root.HandleEvent = function(self, event)
                        if event.Type == 'MouseMotion' then logpos(event.MouseX, event.MouseY) end
                        if old then return old(self, event) end
                        return false
                    end
                end
            end
            local ok, p = pcall(GetMouseScreenPos)
            if ok and p then logpos(p[1], p[2]) end
            WaitSeconds(0.2)
        end
    end)
end
