-- Appended to /lua/simInit.lua by the doscript hook: logs every blueprint in __blueprints as
-- "BPDUMP|<id>|<value>", keys sorted, so a run of the original can be compared with our engine's blueprints
-- (tools/bp-dump/compare.py).
local format, sort, concat, tostring, type = string.format, table.sort, table.concat, tostring, type

local function serialize(value, seen)
    local kind = type(value)
    if kind == 'number' then return format('%.9g', value) end
    if kind == 'string' then return format('%q', value) end
    if kind == 'boolean' then return tostring(value) end
    if kind ~= 'table' then return '<' .. kind .. '>' end
    if seen[value] then return '<cycle>' end
    seen[value] = true
    local keys = {}
    for k in value do table.insert(keys, k) end
    sort(keys, function(a, b)
        if type(a) == type(b) and (type(a) == 'number' or type(a) == 'string') then return a < b end
        return type(a) < type(b)
    end)
    local parts = {}
    for _, k in keys do
        local key = type(k) == 'string' and k or ('[' .. serialize(k, seen) .. ']')
        table.insert(parts, key .. '=' .. serialize(value[k], seen))
    end
    seen[value] = nil
    return '{' .. concat(parts, ',') .. '}'
end

local ids = {}
for id, bp in __blueprints do
    if type(id) == 'string' then table.insert(ids, id) end
end
sort(ids)
for _, id in ids do
    LOG('BPDUMP|' .. id .. '|' .. serialize(__blueprints[id], {}))
end
LOG('BPDUMP|END|' .. table.getn(ids))

LOG('HOOKCHECK|/bpdumphook/lua/simInit.lua|ok')
