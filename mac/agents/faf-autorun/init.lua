InitFileDir = FafBinDir
dofile(FafBinDir .. '/init.lua')
table.insert(path, 1, { dir = AutorunDir .. '/hook', mountpoint = '/autorunhook' })
table.insert(path, 1, { dir = AutorunDir .. '/../../tools/lib/capture-hook', mountpoint = '/capturehook' })
table.insert(hook, 1, '/autorunhook')
table.insert(hook, 1, '/capturehook')
LOG('faf-autorun: hooks mounted from ' .. AutorunDir)
