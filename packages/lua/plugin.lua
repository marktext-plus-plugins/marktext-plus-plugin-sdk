---@module 'lib.marktext-plus'
--- The reference above is for your editor, not for the runtime: it is what
--- makes `storage`, `t` and `ctx` complete and typo-check against
--- lib/marktext-plus.lua. Those are injected by the editor before this file is
--- read, so there is nothing to load them from.
---
--- `require` below is a different thing: it loads this plugin's *own* files.

--- A complete Lua plugin. Every capability the editor offers is used once.

-- require(): one of this plugin's own files. A plugin is not limited to one.
local prompt = require("lib.prompt")

local LANGUAGES = { "English", "简体中文", "日本語", "Deutsch", "Français" }

---@param ctx PluginContext
---@return PluginAction
function on_command(ctx)
  -- t(): your own strings, in the reader's language. Declared in `locales`.
  if ctx.selection == "" and ctx.command == "summarise.selection" then
    return { notify = t("error.empty") }               -- needs ui.notifications
  end

  -- ask + choices: the usual answers to press, and anything typed is taken as
  -- it stands. storage: your own settings, in your own directory.
  if ctx.answer == nil then
    return {
      ask = t("ask.language"),
      default = storage.get("language") or "English",  -- needs storage.local
      choices = LANGUAGES,
    }
  end
  storage.set("language", ctx.answer)

  local text = ctx.command == "summarise.document"
      and ctx.document                                  -- needs document.read
      or ctx.selection

  -- ai: the editor calls the model the reader configured and comes back to
  -- on_result. Your prompt, unedited; the API key never reaches this script.
  return { ai = prompt.summarise(text, ctx.answer) }    -- needs ai.chat
end

---@param ctx PluginContext
---@param result string
---@return PluginAction
function on_result(ctx, result)
  -- show for something small, panel for something document-sized. A whole
  -- document in a dialog covers the thing the reader wants to compare it to.
  if ctx.command == "summarise.document" then
    return { panel = result, title = ctx.answer }
  end
  return { show = result, title = ctx.answer }
end
