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

Start with `lua` or `js`. Such a plugin is **one script file and a
`manifest.json`, and nothing else** — no build step, no compiler, no second
language, and the same two files work on Windows, macOS and Linux at once. A
script cannot crash the editor either.

Only reach for `process` when a script genuinely will not do.

The AI translate plugin published alongside this SDK is the whole of what a
Lua plugin looks like on disk:

```
manifest.json
plugin.lua
README.md
CHANGELOG.md
LICENSE
```

One script, one manifest, and three files that are documentation. No Dart
anywhere.

## Manifest

`manifest.json` sits at the root of the plugin. The editor reads it without
running anything. See [`schema/manifest.schema.json`](schema/manifest.schema.json).

```json
{
  "id": "com.example.my-plugin",
  "name": "My Plugin",
  "version": "1.0.0",
  "minAppVersion": "1.6.1",
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

A `process` plugin does not use `entrypoint`. It names its executables by
operating system, and by architecture underneath where that matters:

```json
{
  "runtime": "process",
  "entrypoints": {
    "macos": "bin/macos/plugin",
    "windows": {
      "x64":   "bin\\windows-x64\\plugin.exe",
      "arm64": "bin\\windows-arm64\\plugin.exe"
    },
    "linux": {
      "default": "bin/linux/plugin",
      "arm64":   "bin/linux-arm64/plugin"
    }
  }
}
```

The system is the part you always have to answer — a Windows build is a
different file from a Linux one. The architecture often is not, so it is
optional:

- **One path for the whole system.** `macos` above is a universal binary: one
  file holding both architectures, which is how macOS builds normally ship.
  Writing the same path under `x64` and `arm64` to say so would be worse.
- **A table of architectures.** `windows` above ships a separate build for each
  and supports nothing else.
- **A shared `default` plus a specialisation.** `linux` above runs
  `bin/linux/plugin` everywhere except arm64, which gets its own. The
  specialised build wins.

Systems are `windows`, `macos` and `linux`; architectures are `x64` and
`arm64`. Anything else is refused when the plugin is installed rather than
skipped — a misspelt `windwos` would otherwise turn into "this plugin does not
support your platform" at the moment the reader clicks, with nothing to explain
it.

A platform you did not build for is named to the reader — "no build for
`linux-arm64`; it ships `macos-x64`, `macos-arm64`, `windows-x64`" — rather
than guessed at. Declaring `runtime: "process"` with no `entrypoints`, or
naming a system with nothing under it, is rejected.

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
    return {
      ask = t("which.language"),
      default = storage.get("target") or "English",
      choices = { "English", "简体中文", "日本語" },
    }
  end
  storage.set("target", ctx.answer)
  return { ai = "Translate into " .. ctx.answer .. ":\n\n" .. ctx.selection }
end

function on_result(ctx, result)
  return { show = result, title = ctx.answer }
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
  return { show: result, title: ctx.answer };
}
```

### The actions

| Return | The editor does | Then |
|---|---|---|
| `{ ask = "…", default = "…", choices = {…} }` | asks the reader; `choices` appear as chips to press, and anything typed instead is taken as it stands | calls `on_command` again with `ctx.answer` set |
| `{ ai = "…" }` | sends your prompt to the model the reader configured | calls `on_result(ctx, reply)` |
| `{ show = "…", title = "…" }` | shows one answer in a small window, with a copy button | stops; nothing is written |
| `{ panel = "…", title = "…" }` | shows it in a panel beside the document | stops; nothing is written |
| `{ notify = "…" }` | tells the reader | stops |
| `{ diff = { original = "…", result = "…" } }` | shows both side by side | stops; nothing is written |
| `{ replace = "…" }` | replaces the selection | stops |
| anything else | nothing | stops |

**`show` or `panel`.** A few lines are an answer: a small window is right, and
a panel for them is more furniture than content. A document-sized result is
something the reader compares against what is on screen, and a window over the
screen is the one place it cannot go.

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
"menus":    [{"id": "…", "title": "…", "location": "editor.contextMenu", "when": "selection"}],
"commands": [{"id": "…", "title": "…"}],
"toolbar":  [{"id": "…", "title": "…", "icon": "…"}],
"pages":    [{"id": "…", "title": "…"}]
```

`title` may be a translation key. `location` is a slot the editor defines —
a plugin places things in named slots, never at pixel coordinates, and never
by handing the editor widgets of its own.

`when` says when a menu entry is worth offering: `selection` only with
something selected, `noSelection` only without, and absent means always.
Without it every entry is offered at once — "translate the selection" with
nothing selected, and "translate the document" while the reader is pointing at
a paragraph. A value the editor does not know is refused when the plugin is
installed rather than quietly treated as "always".

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

### You may not ship source that needs a toolchain to run

This is about compiled plugins only, and about Dart in particular because the
editor is written in it: `entrypoint: "bin/plugin.dart"` is rejected when the
plugin is installed. Running it would need a Dart SDK on the reader's machine,
which the editor does not install and cannot assume — and a release build has
no interpreter to hand it to. Compile it (`dart compile exe`) and ship the
executable.

Nothing here applies to a Lua or JavaScript plugin. Those are interpreted by
the editor itself, which is the whole point of them: no Dart, no toolchain, no
build.

**Why a process and not a library the editor loads.** Lua and JS plugins
already run inside the editor, on its own thread — that is the normal case, and
it is safe because both are interpreted: a bad script raises an error the
editor catches. Native code has no such boundary. A thread shares the address
space, so a segfault, a stack overflow or an `abort()` anywhere in a loaded
`.so` takes the editor down with the reader's unsaved document and no way to
report what happened; a loop with no exit freezes the window with no way to
interrupt it; and unloading is unreliable, so disabling a plugin would not
actually stop it. A separate process gives all three back — it can crash, hang
or be killed on a timeout, and the editor survives and says which plugin did
it. (For Dart specifically there is also no choice to make: `dart compile` has
`exe`, `aot-snapshot`, `js`, `wasm` and the snapshot formats. There is no
subcommand that produces a C-callable `.so` or `.dll`.)

- **Use `serve()` and both of the next two points are already handled.** The
  whole of a compiled plugin:

  ```dart
  import 'dart:io';
  import 'package:marktext_plus_plugin_sdk/marktext_plus_plugin_sdk.dart';

  Future<void> main(List<String> args) async {
    exit(await serve(args, {
      'shout': (request) =>
          (request.params['text'] as String? ?? '').toUpperCase(),
    }, name: 'plugin'));
  }
  ```

  ```
  dart compile exe example/plugin.dart -o bin/linux-x64/plugin
  ```

- **Say what you are when someone runs you directly.** Your executable sits in
  a folder the reader can open, so sooner or later one gets double-clicked, and
  a plugin that just waits on stdin looks like a program that has hung. The
  editor passes `--marktext-plus-plugin-host` to everything it starts; without
  it, `serve()` prints a line saying what this is and exits 1.

- **Exit when stdin reaches end of file.** That is how you are told to shut
  down, and it is what happens on its own if the editor dies — `serve()`
  returns when that happens. The editor also
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
