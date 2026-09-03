---@meta
--- Type definitions for a MarkText Plus Lua plugin.
---
--- **Not shipped with your plugin, and not required by it.** The editor
--- injects `storage`, `t`, `require` and the context; this file is here so
--- your editor completes those names and tells you when you have misspelled
--- one. Nothing in it runs.
---
--- The sandbox leaves out `os`, `io`, `package`, `dofile` and `loadfile`: a
--- plugin gets what it declared in its manifest and nothing else.
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

--- One of your own files, by module name.
---
--- `require("lib.text")` loads `lib/text.lua` from your plugin's directory,
--- and loading it twice returns the same value. A module returns its table.
---
--- A name, not a path: it resolves inside your plugin's directory and nowhere
--- else, so a plugin is free to be several files without being able to read
--- the rest of the disk.
---@param name string
---@return any
function require(name) end

--- Called when one of your menu entries or commands fires.
---@param ctx PluginContext
---@return PluginAction
function on_command(ctx) end

--- Called with the model's reply, after you returned an `ai` action.
---@param ctx PluginContext
---@param result string
---@return PluginAction
function on_result(ctx, result) end
