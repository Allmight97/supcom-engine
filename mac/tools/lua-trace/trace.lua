-- Lua-to-engine call tracer for the original game. Loaded once per Lua state by
-- the /tracehook/lua/globalInit.lua hook, after globalInit has turned the moho.*
-- tables into classes and before any game module derives from them.
--
-- Output, through the game's own LOG (which expands tabs), one line each with
-- fields separated by '|'; values escape control characters and '|' as \ddd:
--   TRACE|START|<state>|<functions wrapped>
--   TRACE|CALL|<state>|<seq>|<name>|<caller file:line>|<args>
--   TRACE|RET|<state>|<seq>|<name>|<results>
--   TRACE|COUNTS|<state>|<seq>|<name>=<calls> ...
-- CALL/RET lines cover the first DETAIL calls of each name; COUNTS lines cover
-- every call and repeat about every COUNT_PERIOD seconds.

if rawget(_G, '__lua_trace') then return end

local DETAIL = 20
local COUNT_PERIOD = 10
local VALUE_CHARS = 80
local FIELDS = 6

local log = LOG
local fork = ForkThread
local yield = coroutine.yield
local getinfo = debug.getinfo
local format = string.format
local gsub = string.gsub
local sub = string.sub
local concat = table.concat
local getn = table.getn
local clock = rawget(_G, 'GetSystemTimeSeconds') or rawget(_G, 'CurrentTime')
    or rawget(_G, 'GetGameTimeSeconds')

local kind = rawget(_G, 'GetPreference') and 'user' or 'sim'
local state = kind .. '-' .. gsub(sub(tostring({}), 8), '^0x', '')
    .. (clock and format('-%d', clock() * 1000) or '')

local counts = {}
local order = {}
local seq = 0
local busy = false
local last_dump = clock and clock() or 0
local dumper = not (fork and clock)

local function emit(fields)
    for i = 1, getn(fields) do fields[i] = tostring(fields[i]) end
    log('TRACE|' .. concat(fields, '|'))
end

local function clean(s)
    s = gsub(s, '[%c|]', function(c) return format('\\%03d', string.byte(c)) end)
    if string.len(s) > VALUE_CHARS then s = sub(s, 1, VALUE_CHARS) .. '...' end
    return s
end

local function scalar(v)
    local t = type(v)
    if t == 'string' then return '"' .. clean(v) .. '"' end
    if t == 'number' then return format('%.6g', v) end
    if t == 'nil' or t == 'boolean' then return tostring(v) end
    return t
end

local function value(v)
    if type(v) ~= 'table' then return scalar(v) end
    if rawget(v, '_c_object') then return 'object' end
    local parts, shown = {}, 0
    local k, x = next(v)
    while k ~= nil and shown < FIELDS do
        shown = shown + 1
        if type(k) == 'number' then
            parts[shown] = scalar(x)
        else
            parts[shown] = clean(tostring(k)) .. '=' .. scalar(x)
        end
        k, x = next(v, k)
    end
    if k ~= nil then parts[shown + 1] = '...' end
    return '{' .. concat(parts, ',') .. '}'
end

local function values(list)
    local parts = {}
    for i = 1, list.n do parts[i] = value(list[i]) end
    return concat(parts, ', ')
end

local function pack(...) return arg end

local function dump_counts()
    local parts = {}
    for i = 1, getn(order) do
        local name = order[i]
        if counts[name] > 0 then table.insert(parts, name .. '=' .. tostring(counts[name])) end
        if getn(parts) == 60 or (i == getn(order) and getn(parts) > 0) then
            emit({ 'COUNTS', state, seq, concat(parts, ' ') })
            parts = {}
        end
    end
end

local function caller()
    local info = getinfo(5, 'Sl')
    if not info then return '?' end
    local source = gsub(string.lower(info.source or '?'), '\\', '/')
    source = gsub(gsub(source, '^@.*%.scd/', '/'), '^@.*/tools/lua%-trace/', '/lua-trace/')
    return clean(source) .. ':' .. tostring(info.currentline or -1)
end

local function dump_periodically()
    while true do
        local now = clock()
        if now - last_dump >= COUNT_PERIOD then
            last_dump = now
            busy = true
            pcall(dump_counts)
            busy = false
        end
        yield(1)
    end
end

-- ForkThread fails until the state's thread manager exists, which in the
-- session user state is after globalInit.
local function start_dumper()
    dumper = pcall(fork, dump_periodically)
end

local function wrap(name, f)
    counts[name] = 0
    table.insert(order, name)
    return function(...)
        local n = counts[name] + 1
        counts[name] = n
        seq = seq + 1
        if not dumper and math.mod(seq, 64) == 0 then start_dumper() end
        if busy or n > DETAIL then return f(unpack(arg)) end
        local id = seq
        busy = true
        pcall(function() emit({ 'CALL', state, id, name, caller(), values(arg) }) end)
        busy = false
        local results = pack(f(unpack(arg)))
        busy = true
        pcall(function() emit({ 'RET', state, id, name, values(results) }) end)
        busy = false
        return unpack(results)
    end
end

local function is_native(v)
    local t = type(v)
    return t == 'cfunction' or (t == 'function' and getinfo(v, 'S').what == 'C')
end

local lua_library = {
    assert = true, collectgarbage = true, dofile = true, error = true, gcinfo = true,
    getfenv = true, getmetatable = true, ipairs = true, loadfile = true, loadlib = true,
    loadstring = true, newproxy = true, next = true, pairs = true, pcall = true,
    rawequal = true, rawget = true, rawset = true, require = true, setfenv = true,
    setmetatable = true, tonumber = true, tostring = true, type = true, unpack = true,
    xpcall = true, _ALERT = true, _ERRORMESSAGE = true,
}

-- A method inherited by derived classes appears in each class table; name it by
-- the class with the fewest methods that holds it, which is the base that
-- registered it.
local function method_owners()
    local size, owner = {}, {}
    for class_name, class in moho do
        if type(class) ~= 'table' then class = {} end
        local count = 0
        for _, v in class do if is_native(v) then count = count + 1 end end
        size[class_name] = count
    end
    for class_name, class in moho do
        if type(class) ~= 'table' then class = {} end
        for method, v in class do
            if type(method) == 'string' and is_native(v) then
                local current = owner[v]
                if not current or size[class_name] < size[current] then
                    owner[v] = class_name
                end
            end
        end
    end
    return owner
end

local function install()
    local globals = {}
    for k, v in _G do
        if type(k) == 'string' and not lua_library[k] and is_native(v) then
            globals[k] = v
        end
    end
    for k, v in globals do rawset(_G, k, wrap(k, v)) end

    -- Lua classes derived from a moho class copy methods from its __spec table,
    -- so wrap both the class table and its spec.
    local wrapped = {}
    local owner = method_owners()
    for _, class in moho do
        if type(class) == 'table' then
            for _, t in { class, rawget(class, '__spec') or {} } do
                local methods = {}
                for method, v in t do
                    if type(method) == 'string' and is_native(v) then methods[method] = v end
                end
                for method, v in methods do
                    if not wrapped[v] then wrapped[v] = wrap((owner[v] or '?') .. ':' .. method, v) end
                    rawset(t, method, wrapped[v])
                end
            end
        end
    end
    return getn(order)
end

rawset(_G, '__lua_trace', state)
emit({ 'START', state, install() })
if not dumper then start_dumper() end
