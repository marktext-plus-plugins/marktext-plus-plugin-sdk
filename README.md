# MarkText Plus Plugin SDK

Main application: [MarkText Plus](https://github.com/SugarFatFree/marktext-plus)

[简体中文](docs/i18n/README_zh-CN.md) | [日本語](docs/i18n/README_ja-JP.md) | [한국어](docs/i18n/README_ko-KR.md) | [Deutsch](docs/i18n/README_de-DE.md) | [Français](docs/i18n/README_fr-FR.md) | [Italiano](docs/i18n/README_it-IT.md) | [Русский](docs/i18n/README_ru-RU.md) | [Español](docs/i18n/README_es-ES.md) | [Português](docs/i18n/README_pt-PT.md) | [العربية](docs/i18n/README_ar-SA.md) | [Português (Brasil)](docs/i18n/README_pt-BR.md)

How to write a plugin for MarkText Plus, and what the editor will and will not
let one do.

**Pre-release.** This SDK stays at 0.x while the plugin system settles, and the
manifest and protocol described here can still change between versions. What
that means in practice, and what it will mean later, is in
[Compatibility](#compatibility) below.

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

## What is in this repository

One directory per language, each a complete plugin you can copy:

```
packages/lua/       ← start here
  manifest.json
  plugin.lua              the entrypoint
  lib/marktext-plus.lua   the API, loaded with require("lib.marktext-plus")

packages/js/        ← or here
  manifest.json
  plugin.js
  lib/marktext-plus.js    the API, loaded with require("lib/marktext-plus")

packages/dart/      ← only if a script will not do; any compiled language works
  manifest.json
  plugin.dart             the entrypoint, compiled to an executable
  lib/                    the library it imports
  pubspec.yaml

schema/manifest.schema.json
```

Named after the **language**, because that is what you choose. `runtime` in the
manifest names how it runs — `lua`, `js`, `process` — and `packages/dart` is a
`process` plugin: Dart is simply the language its example happens to be written
in.

**A `process` plugin can be written in anything that compiles to an
executable.** The editor starts a program and talks JSON-RPC to it over
stdin and stdout; it never learns what produced that program. Go, Rust, C++,
C#, a statically linked Python — all of them work, and none of them needs
anything from this repository beyond the protocol:

- one JSON object per line, on stdin and stdout;
- responses echo the numeric request `id`;
- exit when stdin reaches end of file;
- exit when `MARKTEXT_PLUS_PLUGIN_TOKEN` is not in the environment, so a
  double-clicked executable says what it is instead of waiting.

That is the whole contract. Here it is in Python, with nothing from this
repository — it answers the editor, and refuses to run when nobody started it:

```python
#!/usr/bin/env python3
import json, os, sys

if not os.environ.get("MARKTEXT_PLUS_PLUGIN_TOKEN"):
    print("This is a MarkText Plus plugin.", file=sys.stderr)
    sys.exit(1)

for line in sys.stdin:                       # ends at EOF: the editor went away
    line = line.strip()
    if not line:
        continue
    request = json.loads(line)
    if request.get("method") == "shutdown":
        break
    result = {"echoed": request.get("params", {}).get("text", "")}
    print(json.dumps({"jsonrpc": "2.0", "id": request["id"], "result": result}),
          flush=True)
```

[`packages/dart/lib`](packages/dart/lib) is the same four rules with the edges
handled — malformed input, an unknown method, an error inside one handler not
ending the plugin. Dart is here because the editor is written in it, so
`dart compile exe` was the shortest way to have a working example. It is not a
requirement and not a recommendation: writing those rules again in the language
you already know is usually easier than adding a Dart toolchain to your build.

All three entrypoints do the same thing: load the API and call it.

```lua
local sdk = require("lib.marktext-plus")
return sdk.ask(sdk.t("ask.language"), { default = ..., choices = ... })
```
```js
const sdk = require("lib/marktext-plus");
return sdk.ask(sdk.t("ask.language"), { default: ..., choices: [...] });
```
```dart
import 'package:marktext_plus_plugin_sdk/marktext_plus_plugin_sdk.dart';
exit(await serve(args, { 'summarise': (request) => ... }));
```

`lua` and `js` are deliberately the *same* plugin written twice — same
manifest, same permissions, same behaviour — so the two can be read against
each other. **Copy one.** A plugin declares one `runtime` and one entrypoint;
a directory holding all three is three plugins wearing one manifest.

### Why the API module lives inside an example

Because it ships with your plugin. `lib/marktext-plus.lua` is not a dependency
you point at — it is a file you copy along with the rest, and then own. Copying
`packages/lua` wholesale gives you a working plugin including the API; there is
no separate place to fetch it from, and nothing to keep in step with a version
number.

### What the API module is

For a script, it is ordinary Lua or JavaScript that **ships with your plugin**.
The editor injects `storage`, `t` and `require` as globals before your file is
read; the module wraps them under one name and adds a constructor for each
action, so a plugin reads as `sdk.show(text, title)` rather than as a table
literal whose spelling nothing checks. You can edit it, or not use it at all —
returning the plain table works exactly as well.

For `packages/dart` it is a real library, compiled into your executable, and it
carries something a script does not need: the JSON-RPC loop, the launch check
and the shutdown. A process plugin is on the other side of a pipe.

## A plugin can be several files

`require` loads one of **your own** files — the API module above is loaded
exactly this way, and anything else you put beside it works the same:

```lua
local helpers = require("lib.helpers")   -- lib/helpers.lua, returns its table
```
```js
const helpers = require("lib/helpers");  // lib/helpers.js, sets module.exports
```

Loaded once however often it is required. The name is a name, not a path: it
resolves inside your plugin's directory and nowhere else, so splitting a large
plugin up — or using a library someone else wrote and you shipped alongside —
costs you no access to the rest of the disk. A name with a separator in it, a
`..`, or a leading dot is refused before anything is read, and the resolved
file is checked to be inside your directory afterwards as well, which is what
catches a symbolic link pointing out.

Each example directory is named after the `runtime` it declares, and each is a
complete plugin: a manifest and the code, nothing else needed. `lua` and `js`
are deliberately the *same* plugin written twice — same manifest, same
permissions, same behaviour — so the two can be read side by side to see what
changes and what does not.

**Copy one.** A plugin declares one `runtime` and one entrypoint; a directory
holding a `.lua`, a `.js` and an executable is three plugins wearing one
manifest, and only whichever the manifest names would ever run. Take the
example whose language you want and leave the others here.

## Trying a plugin before you ship it

A Lua or JavaScript plugin is interpreted by the editor, so the honest test is
installing it — **Plugins → Install from ZIP**. A compiled plugin can be
checked sooner:

```
cd packages/dart && dart compile exe plugin.dart -o bin/linux/plugin
echo | ./bin/linux/plugin       # should refuse: it was not started by the editor
```

is the whole check for a compiled plugin: it builds, and it declines to run
when nothing gave it a launch token.

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
| `{ pane = "…", title = "…", slot = "right"\|"bottom"\|"corner" }` | fills one of the panes around the document | stops; nothing is written |
| `{ notify = "…" }` | tells the reader | stops |
| `{ diff = { original = "…", result = "…" } }` | shows both side by side | stops; nothing is written |
| `{ replace = "…" }` | replaces the selection | stops |
| anything else | nothing | stops |

**Panes.** The editor already splits a tab between source and preview; `pane`
is that split offered to you. The document keeps the first cell of a two by two
grid and you may fill the other three — `right` beside it, `bottom` under it,
`corner` under the right-hand one. A slot nobody asked for is not drawn, so
filling only `corner` does not leave two empty strips. A slot name the editor
does not know is refused rather than guessed at: a pane appearing somewhere you
did not ask for, with no way to find out why, is worse than being told.

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

### What this Lua does not do

The interpreter is a pure-Dart Lua, which is why a script plugin needs nothing
installed — and it is not complete. These four all fail **silently**, which is
the part that costs time: a pattern that matches nothing looks exactly like a
document with nothing in it.

| Instead of | Use | Because |
|---|---|---|
| `#someString` | `string.len(s)` | raises `length error`. `#` on a *table* works, so the two cannot be told apart by feel |
| `s:match("%S")`, `%s` | compare characters: `s:sub(i, i) == " "` | the classes match nothing, so every line looks blank |
| `for l in s:gmatch("(.-)\n")` | `s:find("\n", pos, true)` and `s:sub` | returns nothing at all |
| `s:gmatch("[^\n]*")` | the same | never advances past an empty match |

The editor's own test suite pins these, so if the interpreter is replaced this
table is corrected rather than left to mislead.

The JavaScript runtime is QuickJS and has no equivalent gaps worth listing.

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
"panels":   [{"id": "…", "title": "…", "icon": "…"}],
"pages":    [{"id": "…", "title": "…"}]
```

`title` may be a translation key. `location` is a slot the editor defines —
a plugin places things in named slots, never at pixel coordinates, and never
by handing the editor widgets of its own.

`panels` puts an icon in the right-hand side bar; pressing it opens a drawer
filled by running your command of the same `id`. It needs `ui.sidebar`, and it
needs an `icon`, because the bar is a rail of icons and one with nothing to
draw would be a gap that opens something. With no plugin contributing a panel
there is no rail at all — a strip of icons with no icons in it is width taken
from the document for nothing.

A panel is opened and answers: a command that returns `ask` or `ai` is reported
as text there rather than stopping to ask, because a drawer is not a
conversation.

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
[`packages/dart`](packages/dart) library in this repository implements that protocol for plugins
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
  dart compile exe plugin.dart -o bin/linux/plugin
  ```

- **Refuse to run unless the editor started you.** The editor generates a
  token for each launch and hands it over in the `MARKTEXT_PLUS_PLUGIN_TOKEN`
  environment variable; without it, `serve()` prints a line saying what this is
  and exits 1. A token made for one launch cannot be typed by someone who was
  not given it, and it travels in the environment rather than in argv, which
  anything that can run `ps` may read.

  **What this does and does not do.** No program can stop a file on the
  reader's own disk from being executed — double-clicking your executable will
  always start a process. What the token makes unforgeable is your answer to
  "did the editor start me", so the process starts, says what it is, and ends,
  instead of sitting on stdin looking like a program that has hung. A plugin
  that skips the check is a plugin nobody protected; the check is the SDK's,
  which is why it is in `serve()` rather than in this paragraph.

  Script plugins get this for nothing: a `.lua` or `.js` file is interpreted by
  the editor, so double-clicking it opens a text editor at worst.

- **Exit when stdin reaches end of file.** That is how you are told to shut
  down, and it is what happens on its own if the editor dies — `serve()`
  returns when that happens. The editor also
  writes down the processes it started and kills any it finds still running the
  next time it starts — but only ones it started. Processes *you* spawn are
  yours to clean up.
- Keep stdout for protocol responses; write diagnostics to stderr.
- Requests are bounded by a timeout, and a timeout kills only your process.
- Treat everything the host sends as untrusted and validate it.

## Compatibility

A plugin is a file on someone else's machine that this editor reads. Breaking
it is not a build failure anybody here sees — it is a plugin that stops working
for its readers. So:

**`minAppVersion` is enforced.** Say the oldest editor your plugin works with
and the editor holds to it: an editor older than that refuses to install the
plugin, and refuses to run one already installed, saying which version is
wanted and which is present. It used to be read and ignored, which was worse
than not having the field.

**What the editor will not take away without notice.** Every permission name,
every `runtime` value, every action a script can return, every field in `ctx`,
and `storage` and `t` and `require` are pinned by a test in the editor's own
source. Adding to any of those lists is free; removing or renaming one fails
that test, so it cannot happen by accident.

**While this is 0.x**, a deliberate breaking change is still possible, and it
will be in the changelog with what to do about it. When the manifest and the
protocol have been left alone for long enough to be worth trusting, this
becomes 1.0 and that stops: after it, anything a plugin can write today keeps
working, and things go away only after being deprecated in a release that still
supports them.

**Where a plugin is on its own.** The editor cannot promise the behaviour of
your prompt, the model a reader configured, or a `process` plugin's own child
processes. Nor can it stop a reader from running your executable by hand — see
the launch token above for what it does instead.

## Safety rules

- Never write an API key into the plugin directory or the manifest.
- Do not put anything in `stdout` other than protocol messages.
- Keep work bounded; the editor enforces timeouts and step limits.
- A plugin ZIP with a path-traversing entry is rejected at install time.

The SDK is MIT licensed.
