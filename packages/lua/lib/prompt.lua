--- A second file, to show that a plugin need not be one.
---
--- Loaded with `require("lib.prompt")`: the name is a name, not a path, and it
--- resolves inside this plugin's directory and nowhere else.

local M = {}

--- The prompt this plugin sends. Kept here so it can be read on its own.
---@param text string
---@param language string
---@return string
function M.summarise(text, language)
  return "Summarise the Markdown below in " .. language .. ", in three "
    .. "bullet points. Return only the bullets.\n\n" .. text
end

return M
