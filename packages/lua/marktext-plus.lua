---@meta
--- Type definitions for a MarkText Plus Lua plugin.
---
--- **Not shipped with your plugin, and not required by it.** The editor
--- injects `storage`, `t` and the context; there is nothing to `require` at
--- runtime — and a Lua plugin could not require it anyway, since the sandbox
--- has no `require`. This file exists so your editor can complete those names
--- and tell you when you have misspelled one.
---
--- With the Lua Language Server, keep it anywhere in the workspace, or add it
--- explicitly:
---
---     ---@module 'marktext-plus'
---
--- It is a definitions file: nothing in it runs.

---@class PluginContext
---@field command string   The `id` of the menu entry or command that fired.
---@field selection string The selected text; empty when nothing is selected.
---@field document string  The whole document.
---@field answer string|nil What the reader typed last time you asked.

--- An action is a plain table. Return exactly one shape:
---
---   { ask = "...", default = "...", choices = { "..." } }  ask the reader
---   { ai = "..." }                                          call the model
---   { show = "...", title = "..." }                         a small window
---   { panel = "...", title = "..." }                        a panel beside the text
---   { notify = "..." }                                      one line to the reader
---   { diff = { original = "...", result = "..." } }         side by side
---   { replace = "..." }                                     replace the selection
---
---@alias PluginAction table

--- Your own settings, in your own directory. Strings only.
--- Needs the `storage.local` permission.
---@class Storage
---@field get fun(key: string): string|nil
---@field set fun(key: string, value: string|nil)
storage = {}

--- Your own string in the reader's language, from `locales` in the manifest.
--- An unknown key comes back as itself.
---@param key string
---@return string
function t(key) end

--- Called when one of your menu entries or commands fires.
---@param ctx PluginContext
---@return PluginAction
function on_command(ctx) end

--- Called with the model's reply, after you returned an `ai` action.
---@param ctx PluginContext
---@param result string
---@return PluginAction
function on_result(ctx, result) end
