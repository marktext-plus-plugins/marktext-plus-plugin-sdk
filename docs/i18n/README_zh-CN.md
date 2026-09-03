# MarkText Plus 插件 SDK

主应用：[MarkText Plus](https://github.com/SugarFatFree/marktext-plus)

[English](../../README.md) | 简体中文 | [日本語](README_ja-JP.md) | [한국어](README_ko-KR.md) | [Deutsch](README_de-DE.md) | [Français](README_fr-FR.md) | [Italiano](README_it-IT.md) | [Русский](README_ru-RU.md) | [Español](README_es-ES.md) | [Português](README_pt-PT.md) | [العربية](README_ar-SA.md) | [Português (Brasil)](README_pt-BR.md)

怎么给 MarkText Plus 写插件，以及编辑器允许和不允许插件做什么。

**预发布。** 本 SDK 在插件系统定型之前停留在 0.x，这里描述的 manifest 和协议仍可能在版本之间变动。具体现在意味着什么、将来意味着什么，见下面的[兼容性](#兼容性)。

## 先选运行时

插件运行的机器上只有编辑器，没有别的——没有 Dart SDK，没有 Node，没有 Python。后面大部分内容都由这一条决定。

| `runtime` | 你要发布什么 | 能跑在哪 | 什么时候用 |
|---|---|---|---|
| `lua` | 一个 `.lua` 文件 | 所有平台，不用编译 | 默认选它：菜单命令、提问、文本处理 |
| `js` | 一个 `.js` 文件 | 所有平台，不用编译 | 同上，如果你更想写 JavaScript |
| `process` | **每个平台一个**可执行文件 | 只有你构建过的平台 | 确实需要真正的工具链、第三方库或长时间运行的工作 |
| `data` | 完全没有代码 | 所有平台 | 主题、代码片段、词典 |

从 `lua` 或 `js` 开始。这样的插件就是**一个脚本文件加一个 `manifest.json`，没有别的**——不用编译，不需要编译器，不需要第二种语言，同样这两个文件在 Windows、macOS、Linux 上都能跑。脚本也不可能把编辑器搞崩。

只有在脚本确实不够用时才考虑 `process`。

随 SDK 发布的 AI 翻译插件，就是一个 Lua 插件在磁盘上的全部样子：

```
manifest.json
plugin.lua
README.md
CHANGELOG.md
LICENSE
```

一个脚本、一个清单，外加三个纯文档文件。**没有任何 Dart 文件。**

## 这个仓库里有什么

按**语言**各一个目录，每个都是可以整份复制走的完整插件：

```
examples/lua/       ← start here
  manifest.json
  plugin.lua              the entrypoint
  lib/marktext-plus.lua   the API, loaded with require("lib.marktext-plus")

examples/js/        ← or here
  manifest.json
  plugin.js
  lib/marktext-plus.js    the API, loaded with require("lib/marktext-plus")

examples/dart/      ← only if a script will not do; any compiled language works
  manifest.json
  plugin.dart             the entrypoint, compiled to an executable
  lib/                    the library it imports
  pubspec.yaml

schema/manifest.schema.json
```

按语言命名，因为那才是你要选的东西。manifest 里的 `runtime` 说的是"怎么跑"——`lua`、`js`、`process`——而 `examples/dart` 是个 `process` 插件，Dart 只是它示例用的语言。

**`process` 插件可以用任何能编译成可执行文件的语言写。** 编辑器只是启动一个程序、通过 stdin/stdout 跟它说 JSON-RPC，它**永远不知道那个程序是什么编出来的**。Go、Rust、C++、C#、静态链接的 Python 都行，而且除了协议本身，都不需要本仓库的任何东西：

- 每行一个 JSON 对象，走 stdin 和 stdout；
- 响应回显数字 `id`；
- stdin 读到文件结束就退出；
- 环境变量里没有 `MARKTEXT_PLUS_PLUGIN_TOKEN` 就退出，这样被双击的可执行文件会说明自己是什么，而不是干等。

这就是全部约定。下面是它的 Python 版本，不依赖本仓库任何东西——它能回应编辑器，也会在没人启动它时拒绝运行：

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

[`examples/dart/lib`](../../examples/dart/lib) 是同样四条规则加上边界处理：畸形输入、未知方法、单个 handler 出错不会终结整个插件。Dart 出现在这里只是因为编辑器本身用它写的，`dart compile exe` 是最快拿出一个能跑的示例的办法。它**不是要求，也不是推荐**：用你已经会的语言把那四条规则再写一遍，通常比给你的构建加一套 Dart 工具链容易。

三个入口做的是同一件事：加载 API，然后调用它。

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

`lua` 和 `js` 是**故意写成同一个插件的两个版本**——清单一样、权限一样、行为一样——好让你对照着看清哪些会变、哪些不会。**只留一个。** 一个插件只声明一个 `runtime` 和一个入口；同时放着三种的目录，是三个插件共用一份清单。

### 为什么 API 模块放在示例里面

因为它**随你的插件一起分发**。`lib/marktext-plus.lua` 不是一个你去指向的依赖——它是你连同其余部分一起复制、然后归你所有的一个文件。把 `examples/lua` 整份复制走，你就得到一个能用的插件，API 也在里面；没有另一个地方需要去取它，也没有版本号需要跟着对。

### API 模块是什么

对脚本来说，它就是普通的 Lua 或 JavaScript，**随你的插件分发**。编辑器在读你的文件之前就注入了 `storage`、`t` 和 `require`；这个模块把它们收在一个名字下面，并为每个动作提供构造函数，于是插件读起来是 `sdk.show(text, title)`，而不是拼写没人检查的字面量表。你可以改它，也可以完全不用——直接返回原始的表一样有效。

对 `examples/dart` 来说它是真正的库，会被编译进你的可执行文件，而且带着脚本不需要的东西：JSON-RPC 循环、启动检查、关闭处理。进程插件在管道的另一端。

## 插件可以是多个文件

`require` 加载的是**你自己的**文件——上面那个 API 模块正是这样被加载的，你放在旁边的任何别的文件也一样：

```lua
local helpers = require("lib.helpers")   -- lib/helpers.lua, returns its table
```

```js
const helpers = require("lib/helpers");  // lib/helpers.js, sets module.exports
```

无论 `require` 多少次都只加载一次。名字是**名字不是路径**：它只在你的插件目录里解析，别处都不行，所以把一个大插件拆开——或者带上别人写的库一起发布——不会让你多拿到磁盘上任何别的东西。名字里带分隔符、带 `..` 或以点开头，在读任何东西之前就被拒绝；解析出来的文件之后还会再检查一次是否在你的目录内，这道检查抓的是指向外面的符号链接。

## 发布前怎么试

Lua 或 JS 插件由编辑器解释执行，所以最实在的检验就是装上它——**插件 → 安装 ZIP**。有两件事可以更早做：

```
node tool/run-js-plugin.mjs examples/js      # or your own plugin directory
```

会像编辑器那样运行一个 JavaScript 插件——同样的注入全局、同样只能在插件目录内解析的 `require`、同样的两个入口——并告诉你哪一条回答不是编辑器期待的形状。编辑器用的是 QuickJS，它只存在于构建产物里；这个脚本替它站台。

```
cd examples/dart && dart compile exe plugin.dart -o bin/linux/plugin
echo | ./bin/linux/plugin       # should refuse: it was not started by the editor
```

这就是编译型插件的全部检查：它能编译，而且在没人给它启动令牌时拒绝运行。

## 清单

`manifest.json` 放在插件根目录。编辑器**不运行任何代码**就能读它。见 [`schema/manifest.schema.json`](../../schema/manifest.schema.json)。

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

### 按平台的可执行文件

`process` 插件不用 `entrypoint`，而是**先按操作系统**声明可执行文件，架构在其下、可以省略：

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

操作系统是你**总得**回答的部分——Windows 的构建和 Linux 的必然是两个文件。架构往往不是，所以它可选：

- **整个系统一个路径。** 上面的 `macos` 是通用二进制：一个文件装着两种架构，这也是 macOS 构建通常的形态。为了表达这件事而把同一个路径在 `x64` 和 `arm64` 下各写一遍，只会更糟。
- **一张架构表。** 上面的 `windows` 为每种架构各发一个构建，别的架构就是不支持。
- **共用的 `default` 加一个专门构建。** 上面的 `linux` 在 arm64 之外都跑 `bin/linux/plugin`，arm64 有自己的。专门的优先。

系统名只有 `windows`、`macos`、`linux`，架构只有 `x64` 和 `arm64`。**写错的名字在安装时报错，不会被跳过**——否则一个拼错的 `windwos` 会在用户点击的那一刻变成"这个插件不支持你的平台"，而且无从解释。

没有为某个平台构建时，会明确告诉用户是哪个平台——"没有 `linux-arm64` 的构建，它带了 `macos-x64`、`macos-arm64`、`windows-x64`"——而不是瞎猜一个去跑。声明 `runtime: "process"` 却没有 `entrypoints`，或者声明了某个系统却在下面留空，都会被拒绝。

## 脚本插件是怎么被调用的

两种脚本运行时都是同步的——Lua 解释器没有协程，JS 引擎也没有自己的事件循环。凡是耗时的事（问用户、调模型）都会卡住编辑器。所以脚本从不等待：它**返回一个动作**说明自己想做什么，编辑器去做，做完再带着结果调用脚本。

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

同样的形状，用 JavaScript 写：

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

### 动作一览

| 返回 | 编辑器做什么 | 然后 |
|---|---|---|
| `{ ask = "…", default = "…", choices = {…} }` | 问用户；`choices` 显示成可点的标签，输入别的照样按原样采纳 | 带着 `ctx.answer` 再次调用 `on_command` |
| `{ ai = "…" }` | 把你的提示词发给用户配置的模型 | 调用 `on_result(ctx, reply)` |
| `{ show = "…", title = "…" }` | 用小窗口显示一条结果，带复制按钮 | 结束；不写入文档 |
| `{ panel = "…", title = "…" }` | 在正文旁边的面板里显示 | 结束；不写入文档 |
| `{ notify = "…" }` | 告诉用户一句话 | 结束 |
| `{ diff = { original = "…", result = "…" } }` | 左右对照显示两段文本 | 结束；不写入文档 |
| `{ replace = "…" }` | 替换当前选区 | 结束 |
| 其它任何东西 | 什么都不做 | 结束 |

**`show` 还是 `panel`。** 几行文字是一个答案：小窗口才对，给它开一整栏是家具多过内容。整篇文档大小的结果，是用户要拿来跟屏幕上的东西对照的，而盖住屏幕的窗口恰恰是它唯一不能待的地方。

单次运行上限 8 步，所以一个不停返回 `ask` 的脚本困不住用户。

**提示词是你的。** 编辑器保管凭据、发出请求；它不会改写你的提示词，你的脚本也永远看不到 API key。发给模型的，就是你在 `ai` 里返回的那个字符串。

### 脚本能碰到什么

只有下面这些。没有 `os`、没有 `package`、没有 `dofile`、没有 `loadfile`，没有文件系统，也没有网络——脚本插件来自陌生人的仓库，所以它只拿到自己声明过的东西，别的一概没有。

| | |
|---|---|
| `storage.get(key)` / `storage.set(key, value)` | 你自己的设置，存在你自己的目录里。只能是字符串。需要 `storage.local` |
| `t(key)` | 你自己的字符串，按用户的语言取；没有对应翻译时返回键名本身 |
| `require(name)` | 你自己的文件，只在你的插件目录内解析 |
| `ctx.command` | 触发的那个菜单项或命令的 `id` |
| `ctx.selection` | 选中的文本，没有选中时为 `""` |
| `ctx.document` | 整篇文档 |
| `ctx.answer` | 上一次你提问时用户输入的内容，否则为 nil/undefined |

## 权限

在清单里声明，展示给用户，**并且强制执行**。VS Code 和 IntelliJ 会展示权限清单然后信任扩展；这里没有任何人做审核，所以由编辑器来检查。没有 `ai.chat` 却返回 `{ ai = ... }` 不会调用模型——用户会被告知这个插件没有申请这项权限。

| 权限 | 允许插件 |
|---|---|
| `document.read` | 读取打开的文档和选区 |
| `document.write` | 修改打开的文档 |
| `ui.contextMenu` | 往右键菜单加条目 |
| `ui.menuBar` | 往菜单栏加条目 |
| `ui.toolbar` | 加一个工具栏按钮 |
| `ui.sidebar` | 加一个侧边栏面板 |
| `ui.statusBar` | 加一个状态栏项 |
| `ui.settings` | 拥有自己的设置页 |
| `ui.commandPalette` | 往命令面板加命令 |
| `ui.notifications` | 向用户提示信息 |
| `ai.chat` | 调用用户配置的模型（永远拿不到 key） |
| `storage.local` | 在自己目录里保存自己的设置文件 |
| `clipboard.read` / `clipboard.write` | 剪贴板 |
| `workspace.read` / `workspace.write` | 用户打开的文件夹下的文件 |
| `network.request` | 自行发起 HTTP 请求。**能申请的最宽的一项**：凡是它能读到的，它都能发出去 |

用到什么就申请什么。一个只为加个菜单项却申请 `network.request` 的插件，用户应该拒绝。

## 贡献点

```json
"menus":    [{"id": "…", "title": "…", "location": "editor.contextMenu", "when": "selection"}],
"commands": [{"id": "…", "title": "…"}],
"toolbar":  [{"id": "…", "title": "…", "icon": "…"}],
"pages":    [{"id": "…", "title": "…"}]
```

`title` 可以是翻译键。`location` 是编辑器定义的槽位——插件只能把东西放进有名字的槽位，不能指定像素坐标，也不能把自己的控件交给编辑器。

`when` 说明一个菜单项什么时候值得出现：`selection` 只在有选区时，`noSelection` 只在没选区时，省略表示总是出现。没有它的话，所有条目会同时出现——"翻译选中内容"在没选中任何东西时也在，"翻译全文"在用户正指着一个段落时也在。编辑器不认识的值会在安装时被拒绝，而不是悄悄当成"总是"。

## 设置

`settings` 里的每个字段，都会在插件自己的设置页上变成一个真实控件，由编辑器绘制：

| `type` | 控件 |
|---|---|
| `text` | 文本框 |
| `password` | 不显示内容的文本框 |
| `number` | 数字文本框 |
| `boolean` | 开关；保存为 `"true"` / `"false"` 字符串 |

值存在插件自己目录下的 `settings.json` 里，所以任何插件都读不到、也写不了别人的设置。用户保存后，**已经在运行的脚本在下一条命令时就会读到新值**，不用等下次启动。

## 翻译

`locales` 把语言映射到你自己的字符串表，`defaultLocale` 是兜底。用户在 `zh_CN` 时，先找 `zh_CN`（如果你提供了），再找 `zh`，最后用你的默认语言。想支持哪些语言完全由你决定——这是你的表，不是编辑器的。

## 编译型插件（`runtime: "process"`）

可执行文件作为子进程启动，通过 stdin/stdout 用 JSON-RPC 2.0 通信，每行一个 JSON 对象，响应回显数字 `id`。本仓库的 [`examples/dart/lib`](../../examples/dart/lib) 为用 Dart 编写、用 `dart compile exe` 编译的插件实现了这套协议。

### 不许分发需要工具链才能运行的源码

这一条只针对编译型插件，而且特别针对 Dart，因为编辑器本身就是用它写的：`entrypoint: "bin/plugin.dart"` 会在插件安装时被拒绝。运行它需要用户机器上有 Dart SDK，而编辑器既不安装它、也不能假定它存在——release 构建里更没有解释器可以交给它。编译它（`dart compile exe`），然后分发那个可执行文件。

这里说的和 Lua 或 JavaScript 插件无关。那两种由编辑器自己解释执行，这正是它们存在的意义：不需要 Dart，不需要工具链，不需要构建。

**为什么是进程，而不是编辑器加载的库。** Lua 和 JS 插件本来就在编辑器进程里、同一个线程上跑——那是常规情况，之所以安全是因为它们是被解释执行的：脚本出错抛的是编辑器能接住的异常。原生代码没有这道边界。线程共享地址空间，所以一个 `.so` 里任何位置的段错误、栈溢出或 `abort()`，都会带走编辑器和用户未保存的文档，而且无从上报；死循环会冻结窗口且无法打断；卸载也不可靠，"禁用插件"其实并没有真的停掉它。独立进程把这三样都拿回来了——它可以崩、可以超时被杀，编辑器活着并且说得清是哪个插件干的。（对 Dart 而言另外没有选择：`dart compile` 的子命令只有 `exe`、`aot-snapshot`、`js`、`wasm` 和几种快照格式，**不存在**产出 C 可调用的 `.so` 或 `.dll` 的子命令。）

- **使用 `serve()`，下面两条就已经替你处理好了。** 一个编译型插件的全部：

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

- **不是编辑器启动的就别运行。** 编辑器为每次启动生成一个令牌，通过 `MARKTEXT_PLUS_PLUGIN_TOKEN` 环境变量传入；拿不到它，`serve()` 就打印一句说明并以 1 退出。为一次启动生成的令牌，没拿到它的人打不出来；它走环境变量而不是 argv，因为凡是能跑 `ps` 的东西都能读到 argv。

  **这能做到什么、不能做到什么。** 没有任何程序能阻止用户运行自己磁盘上的文件——双击你的可执行文件一定会起一个进程。令牌让**"是不是编辑器启动的"这个答案无法伪造**，于是进程起来、说明自己是什么、然后结束，而不是干等 stdin 像个卡死的程序。跳过这个检查的插件就是没人替它做防护；检查在 SDK 的 `serve()` 里，而不是只写在这段话里，正是这个原因。脚本插件天然就有这层保证：`.lua` 或 `.js` 文件由编辑器解释执行，双击它最多打开一个文本编辑器。

- **stdin 读到文件结束就退出。** 这是通知你关闭的方式，也是编辑器意外死亡时自然发生的事——`serve()` 在这时会返回。编辑器同时会记下自己启动过的进程，下次启动时清理还活着的——但只限它自己启动的那些。**你自己再启动的进程，得你自己负责收拾。**
- stdout 只留给协议响应，诊断信息写 stderr。
- 请求有超时限制，超时只会杀掉你的进程。
- 把宿主发来的一切都当作不可信的输入，先校验再用。

## 兼容性

插件是别人机器上的一个文件，由这个编辑器去读。把它弄坏，不是这里任何人能看到的构建失败——而是它的用户那边不能用了。所以：

**`minAppVersion` 是强制执行的。** 写清你的插件最低需要哪个版本的编辑器，编辑器会遵守：比它旧的编辑器拒绝安装这个插件，也拒绝运行已经装上的，并说清要的是哪个版本、有的是哪个版本。这个字段以前被读取然后忽略，那比没有它更糟。

**编辑器不会不打招呼就拿走的东西。** 每一个权限名、每一个 `runtime` 值、脚本能返回的每一种动作、`ctx` 里的每个字段，以及 `storage`、`t`、`require`，都由编辑器源码里的一个测试钉住。往这些清单里**加**东西是自由的；**删掉或改名**会让那个测试失败，所以那不可能是不小心发生的。

**在 0.x 期间**，有意为之的破坏性变更仍然可能发生，但会写进 changelog 并说明该怎么改。等 manifest 和协议被搁置足够久、久到值得信任时，这里会转 1.0，届时这条就结束了：此后今天插件能写的东西继续有效，要移除什么，必须先在一个仍然支持它的版本里标记废弃。

**插件自己负责的部分。** 编辑器无法为你的提示词、用户配置的模型、或者 `process` 插件自己再启动的子进程的行为做任何承诺。它也拦不住用户手动运行你的可执行文件——上面的启动令牌说明了它转而做了什么。

## 安全须知

- 永远不要把 API key 写进插件目录或清单。
- 除了协议消息，不要往 stdout 写任何东西。
- 工作要有边界；编辑器有超时和步数上限。
- 带有路径穿越条目的插件 ZIP 会在安装时被拒绝。

本 SDK 采用 MIT 协议。
