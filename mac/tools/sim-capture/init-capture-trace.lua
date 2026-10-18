-- init-capture.lua plus tools/lua-trace's call tracer in the same run (used for /simtrace).
dofile(InitFileDir .. '\\init-capture.lua')
local trace_dir = string.gsub(InitFileDir, '[\\/]sim%-capture$', '\\lua-trace')
table.insert(path, { dir = trace_dir, mountpoint = '/lua-trace' })
table.insert(path, { dir = trace_dir .. '\\hook', mountpoint = '/tracehook' })
table.insert(hook, 2, '/tracehook')
LOG('sim-capture: lua-trace mounted from ' .. trace_dir)
