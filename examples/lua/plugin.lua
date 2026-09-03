--- A complete Lua plugin. Every capability the editor offers is used once.
---
--- Two files ship: this one and lib/marktext-plus.lua, which `require` loads
--- from this plugin's own directory. A plugin is not limited to those two —
--- `require` will load any file you put beside them.
local sdk = require("lib.marktext-plus")

local LANGUAGES = { "English", "简体中文", "日本語", "Deutsch", "Français" }

--- @param ctx table  command, selection, document, answer
function on_command(ctx)
  -- sdk.t(): your own strings, in the reader's language, from `locales`.
  if ctx.selection == "" and ctx.command == "summarise.selection" then
    return sdk.notify(sdk.t("error.empty"))            -- needs ui.notifications
  end

  -- sdk.ask(): the usual answers to press, and anything typed is taken as it
  -- stands. sdk.storage: your own settings, in your own directory.
  if ctx.answer == nil then
    return sdk.ask(sdk.t("ask.language"), {
      default = sdk.storage.get("language") or "English", -- needs storage.local
      choices = LANGUAGES,
    })
  end
  sdk.storage.set("language", ctx.answer)

  local text = ctx.command == "summarise.document"
      and ctx.document                                  -- needs document.read
      or ctx.selection

  -- sdk.ai(): the editor calls the model the reader configured and comes back
  -- to on_result. Your prompt, unedited; the API key never reaches this script.
  return sdk.ai(
    "Summarise the Markdown below in " .. ctx.answer .. ", in three bullet "
      .. "points. Return only the bullets.\n\n" .. text
  )                                                     -- needs ai.chat
end

--- @param ctx table
--- @param result string  what the model replied
function on_result(ctx, result)
  -- show for something small, panel for something document-sized: a whole
  -- document in a dialog covers the thing the reader wants to compare it to.
  if ctx.command == "summarise.document" then
    return sdk.panel(result, ctx.answer)
  end
  return sdk.show(result, ctx.answer)
end
