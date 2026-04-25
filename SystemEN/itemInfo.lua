-- Robust loader: catches errors at each level so translation degrades gracefully.

local ok_f, err_f = pcall(require, "SystemEN/LuaFiles514/itemInfo_f")
local ok_d, err_d = pcall(dofile, "SystemEN/LuaFiles514/itemInfo.lua")

DisplayServer = 1
TagStart = '('
TagEnd = ')'
ServerColour = ''

-- Override main() with per-item pcall: one bad item won't kill all translations.
local original_main = main
main = function()
    if type(tbl) ~= "table" then return false, "tbl missing" end
    local count, fail = 0, 0
    for ItemID, DESC in pairs(tbl) do
        local ok = pcall(function()
            local idName = DESC.identifiedDisplayName or ""
            if DisplayServer == 1 and DESC.Server ~= nil and DESC.Custom == nil then
                idName = idName .. ' ' .. TagStart .. DESC.Server .. TagEnd
            end
            AddItem(ItemID, DESC.unidentifiedDisplayName or "", DESC.unidentifiedResourceName or "",
                    idName, DESC.identifiedResourceName or "", DESC.slotCount or 0, DESC.ClassNum or 0)
            local descSrc = (DESC.unidentifiedDescriptionName and DESC.unidentifiedDescriptionName[1] ~= "")
                            and DESC.unidentifiedDescriptionName or DESC.identifiedDescriptionName
            if type(descSrc) == "table" then
                for _, line in ipairs(descSrc) do AddItemUnidentifiedDesc(ItemID, line) end
            end
            if type(DESC.identifiedDescriptionName) == "table" then
                for _, line in ipairs(DESC.identifiedDescriptionName) do AddItemIdentifiedDesc(ItemID, line) end
            end
        end)
        if ok then count = count + 1 else fail = fail + 1 end
    end
    return true, string.format("loaded %d items, %d failed", count, fail)
end
