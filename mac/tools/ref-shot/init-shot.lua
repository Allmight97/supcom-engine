-- Init file for `SupremeCommander.exe /init <this file>`: the stock mounts plus a
-- hook directory whose gamemain.lua hook poses the camera for reference screenshots.
local game_root = 'C:\\GOG Games\\Supreme Commander Forged Alliance'
local documents = SHGetFolderPath('PERSONAL') .. 'My Games\\Gas Powered Games\\Supreme Commander Forged Alliance'

path = {}

local function mount(dir, mountpoint)
    table.insert(path, { dir = dir, mountpoint = mountpoint })
end

local function mount_each(dir, mountpoint)
    for _, entry in io.dir(dir .. '\\*') do
        if entry ~= '.' and entry ~= '..' then
            local name = string.gsub(string.gsub(string.lower(entry), '[.]scd$', ''), '[.]zip$', '')
            mount(dir .. '\\' .. entry, mountpoint .. '/' .. name)
        end
    end
end

mount_each(documents .. '\\mods', '/mods')
mount_each(documents .. '\\maps', '/maps')
mount(InitFileDir, '/ref-shot')
mount(InitFileDir .. '\\hook', '/refshothook')
mount(string.gsub(InitFileDir, '[^\\]+$', '') .. 'lib\\capture-hook', '/capturehook')
mount(game_root .. '\\gamedata\\*.scd', '/')
mount(game_root, '/')

hook = { '/capturehook', '/refshothook', '/schook' }

protocols = { 'http', 'https', 'mailto', 'ventrilo', 'teamspeak', 'daap', 'im' }

LOG('ref-shot: init file mounted ' .. InitFileDir)
