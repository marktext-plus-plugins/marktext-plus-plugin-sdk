-- A complete Lua plugin. Two files: this one and manifest.json.
--
-- Nothing is compiled and nothing is installed: the editor interprets this
-- file, so the same two files run on Windows, macOS and Linux.

function on_command(ctx)
  if ctx.selection == "" then
    return { notify = t("error.empty") }
  end

  -- Asking is an action, not a call: the script cannot block while the reader
  -- thinks, so it hands the question back and is called again with the answer.
  if ctx.answer == nil then
    return {
      ask = t("ask.style"),
      default = storage.get("style") or "LOUD",
      choices = { "LOUD", "louder", "LOUDEST" },
    }
  end
  storage.set("style", ctx.answer)

  local shouted = string.upper(ctx.selection)
  if ctx.answer == "LOUDEST" then
    shouted = shouted .. "!!!"
  end

  return { show = shouted, title = ctx.answer }
end
