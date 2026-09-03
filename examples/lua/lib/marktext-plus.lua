--- The MarkText Plus API, as a module you require.
---
--- The editor injects `storage`, `t` and `require` as globals before your
--- plugin is read. This wraps them in one named thing, and adds a constructor
--- for each action the editor understands, so a plugin reads as calls rather
--- than as table literals whose spelling nothing checks.
---
--- Ships with your plugin: it is ordinary Lua and `require` loads it from your
--- own directory.

local M = {}

--- Your own settings, in your own directory. Strings only.
--- Needs the `storage.local` permission.
M.storage = storage

--- Your own string in the reader's language, from `locales` in the manifest.
--- An unknown key comes back as itself.
---@param key string
---@return string
function M.t(key) return t(key) end

--- Ask the reader something. The command runs again with `ctx.answer` set.
---@param label string
---@param options table|nil  { default = string, choices = { string } }
function M.ask(label, options)
  options = options or {}
  return {
    ask = label,
    default = options.default,
    choices = options.choices,
  }
end

--- Send a prompt to the model the reader configured. Needs `ai.chat`.
--- The reply arrives in `on_result`. Your API key never reaches this script.
---@param prompt string
function M.ai(prompt) return { ai = prompt } end

--- One answer, in a small window with a copy button.
---@param text string
---@param title string|nil
function M.show(text, title) return { show = text, title = title } end

--- One answer, in a panel beside the document. For document-sized results.
---@param text string
---@param title string|nil
function M.panel(text, title) return { panel = text, title = title } end

--- Fill one of the panes around the document. The editor lays the document
--- and up to three panes out as a two by two grid.
---
--- `as` draws it: "text" as it stands, "source" as Markdown source, "preview"
--- rendered. Pass `ctx.view` to answer the way the reader is reading.
---
--- `append` adds to the pane instead of replacing it, and `ai` asks the model
--- one more thing once this has been shown — together they are how a plugin
--- works through a document a block at a time, showing each as it arrives.
---@param text string
---@param options table|nil  { title, slot, as, append, ai }
function M.pane(text, options)
  options = options or {}
  return {
    pane = text,
    title = options.title,
    slot = options.slot,
    as = options.as,
    append = options.append,
    ai = options.ai,
  }
end

--- Say one line to the reader and stop. Needs `ui.notifications`.
---@param message string
function M.notify(message) return { notify = message } end

--- Show two texts side by side. Nothing is written to the document.
---@param original string
---@param result string
function M.diff(original, result)
  return { diff = { original = original, result = result } }
end

--- Replace the selection. Needs `document.write`.
---@param text string
function M.replace(text) return { replace = text } end

--- Do nothing.
function M.nothing() return {} end

return M
