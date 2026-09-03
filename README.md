# MarkText Plus Plugin SDK

Main application: [MarkText Plus](https://github.com/SugarFatFree/marktext-plus)

How to write a plugin for MarkText Plus, and what the editor will and will not
let one do.

## Pick a runtime first

A plugin runs on machines that have the editor and nothing else — no Dart SDK,
no Node, no Python. That single fact decides most of what follows.

| `runtime` | What you ship | Runs on | Use it when |
|---|---|---|---|
| `lua` | one `.lua` file | every platform, no build | the default: menu commands, prompts, text work |
| `js` | one `.js` file | every platform, no build | same, if you would rather write JavaScript |
| `process` | one executable **per platform** | only the platforms you built for | you need a real toolchain, libraries, or long-running work |
| `data` | no code at all | everywhere | themes, snippets, dictionaries |

Start with `lua` or `js`. They need no build step, they cannot crash the
editor, and one file works on Windows, macOS and Linux at once.

**A plugin may not ship Dart source.** `entrypoint: "bin/plugin.dart"` is
rejected at install time. Running it would need a Dart SDK the reader has no
reason to have, and the editor cannot supply one. Dart compiles to a real
executable — `dart compile exe` — and that is what a `process` plugin ships.

## Manifest

`manifest.json` sits at the root of the plugin. The editor reads it without
running anything. See [`schema/manifest.schema.json`](schema/manifest.schema.json).

```json
{
  "id": "com.example.my-plugin",
  "name": "My Plugin",
  "version": "1.0.0",
  "minAppVersion": "1.7.0",
  "runtime": "lua",
  "entrypoint": "plugin.lua",

  "permissions": ["document.read", "ui.contextMenu", "ai.chat", "storage.local"],

  "menus": [
    {"id": "translate.selection", "title": "menu.selection", "location": "editor.contextMenu"}
  ],

  "settings": [
    {"key": "target", "title": "settings.target", "type": "text", "default": "English"}
  ],

  "defaultLocale": "en",
  "locales": {
    "en": {"menu.selection": "Translate selection", "settings.target": "Target language"},
    "zh": {"menu.selection": "翻译选中内容", "settings.target": "目标语言"}
  }
}
```

### Per-platform executables

A `process` plugin does not use `entrypoint`. It names one executable for each
platform it was built for, keyed `os-arch`:

```json
{
  "runtime": "process",
  "entrypoints": {
    "linux-x64":   "bin/linux-x64/plugin",
    "linux-arm64": "bin/linux-arm64/plugin",
    "windows-x64": "bin\\windows-x64\\plugin.exe",
    "macos-arm64": "bin/macos-arm64/plugin"
  }
}
```

The `os` is `windows`, `macos` or `linux`; the `arch` is `x64` or `arm64`. A
platform you did not build for is named to the reader — "no build for
`linux-arm64`; it ships `windows-x64`, `macos-arm64`" — rather than guessed at.
Declaring `runtime: "process"` with no `entrypoints` is rejected.

## How a script plugin is called

Both script runtimes are synchronous — the Lua interpreter has no coroutines,
and the JS engine has no event loop of its own. Anything that takes time
(asking the reader something, calling a model) would therefore block the
editor. So a script never waits: it **returns an action** describing what it
wants done, the editor does it, and the editor calls the script again with the
answer.

```lua
function on_command(ctx)
  -- ctx.command, ctx.selection, ctx.document, ctx.answer
  if ctx.selection == "" then
    return { notify = t("nothing.selected") }
  end
  if ctx.answer == nil then
    return { ask = t("which.language"), default = storage.get("target") or "English" }
  end
  storage.set("target", ctx.answer)
  return { ai = "Translate into " .. ctx.answer .. ":\n\n" .. ctx.selection }
end

function on_result(ctx, result)
  return { diff = true, original = ctx.selection, result = result }
end
```

The same shape in JavaScript:

```js
function on_command(ctx) {
  if (!ctx.selection) return { notify: t("nothing.selected") };
  if (ctx.answer == null) {
    return { ask: t("which.language"), default: storage.get("target") || "English" };
  }
  storage.set("target", ctx.answer);
  return { ai: `Translate into ${ctx.answer}:\n\n${ctx.selection}` };
}

function on_result(ctx, result) {
  return { diff: true, original: ctx.selection, result: result };
}
```

### The actions

| Return | The editor does | Then |
|---|---|---|
| `{ ask = "…", default = "…" }` | asks the reader | calls `on_command` again with `ctx.answer` set |
| `{ ai = "…" }` | sends your prompt to the model the reader configured | calls `on_result(ctx, reply)` |
| `{ notify = "…" }` | tells the reader | stops |
| `{ diff = true, original = "…", result = "…" }` | shows both side by side | stops; nothing is written |
| `{ replace = "…" }` | replaces the selection | stops |
| anything else | nothing | stops |

A run is capped at 8 steps, so a script that keeps returning `ask` cannot trap
the reader in a loop.

**The prompt is yours.** The editor holds the credentials and makes the
request; it never writes or edits your prompt, and your script never sees the
API key. What the model is asked is exactly the string you returned in `ai`.

### What a script can reach

Only these. There is no `os`, no `package`, no `require`, no `dofile`, no
`loadfile`, no file system and no network — a script plugin comes from a
stranger's repository, so it gets what it declared and nothing else.

| | |
|---|---|
| `storage.get(key)` / `storage.set(key, value)` | your own settings, in your own directory. Strings only. Needs `storage.local`. |
| `t(key)` | your own string in the reader's language; returns the key itself if you have no translation for it |
| `ctx.command` | the `id` of the menu entry or command that fired |
| `ctx.selection` | the selected text, `""` when nothing is selected |
| `ctx.document` | the whole document |
| `ctx.answer` | what the reader typed last time you asked, otherwise nil/undefined |

## Permissions

Declared in the manifest, shown to the reader, and **enforced**. VS Code and
IntelliJ show a permission list and then trust the extension; here nothing is
reviewed by anybody, so the editor checks. Returning `{ ai = ... }` without
`ai.chat` does not call the model — the reader is told the plugin did not ask
for it.

| Permission | Lets the plugin |
|---|---|
| `document.read` | read the open document and the selection |
| `document.write` | change the open document |
| `ui.contextMenu` | add entries to the right-click menu |
| `ui.menuBar` | add entries to the menu bar |
| `ui.toolbar` | add a toolbar button |
| `ui.sidebar` | add a side-bar panel |
| `ui.statusBar` | add a status-bar item |
| `ui.settings` | have a settings page |
| `ui.commandPalette` | add commands to the palette |
| `ui.notifications` | tell the reader things |
| `ai.chat` | ask the model the reader configured (never the key) |
| `storage.local` | keep its own settings file in its own directory |
| `clipboard.read` / `clipboard.write` | the clipboard |
| `workspace.read` / `workspace.write` | files under the folder the reader opened |
| `network.request` | make HTTP requests of its own. The widest thing to ask for: anything it can read, it can send anywhere. |

Ask for what you use. A plugin asking for `network.request` to add a menu entry
is one the reader should decline.

## Contribution points

```json
"menus":    [{"id": "…", "title": "…", "location": "editor.contextMenu"}],
"commands": [{"id": "…", "title": "…"}],
"toolbar":  [{"id": "…", "title": "…", "icon": "…"}],
"pages":    [{"id": "…", "title": "…"}]
```

`title` may be a translation key. `location` is a slot the editor defines —
a plugin places things in named slots, never at pixel coordinates, and never
by handing the editor widgets of its own.

## Settings

Each field in `settings` becomes a real control on the plugin's own settings
page, which the editor draws:

| `type` | Control |
|---|---|
| `text` | a text box |
| `password` | a text box that does not show what is in it |
| `number` | a numeric text box |
| `boolean` | a switch; saved as the strings `"true"` / `"false"` |

Values live in `settings.json` inside the plugin's own directory, so no plugin
can read or write another's. What the reader saves reaches an already-running
script on its next command, not at the next launch.

## Translations

`locales` maps a language to your own strings; `defaultLocale` says which to
fall back on. A reader on `zh_CN` gets `zh_CN` if you shipped it, then `zh`,
then your default. Ship whichever languages you like — this is your table, not
the editor's.

## Compiled plugins (`runtime: "process"`)

The executable is started as a child process and speaks JSON-RPC 2.0, one JSON
object per line, on stdin/stdout. Responses echo the numeric request `id`. The
[`dart/`](dart) package in this repository implements that protocol for plugins
written in Dart and compiled with `dart compile exe`.

- **Exit when stdin reaches end of file.** That is how you are told to shut
  down, and it is what happens on its own if the editor dies. The editor also
  writes down the processes it started and kills any it finds still running the
  next time it starts — but only ones it started. Processes *you* spawn are
  yours to clean up.
- Keep stdout for protocol responses; write diagnostics to stderr.
- Requests are bounded by a timeout, and a timeout kills only your process.
- Treat everything the host sends as untrusted and validate it.

## Safety rules

- Never write an API key into the plugin directory or the manifest.
- Do not put anything in `stdout` other than protocol messages.
- Keep work bounded; the editor enforces timeouts and step limits.
- A plugin ZIP with a path-traversing entry is rejected at install time.

The SDK is MIT licensed.
