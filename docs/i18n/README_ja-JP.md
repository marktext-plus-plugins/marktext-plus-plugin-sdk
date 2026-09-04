# MarkText Plus プラグイン SDK

メインアプリケーション：[MarkText Plus](https://github.com/SugarFatFree/marktext-plus)

[English](../../README.md) | [简体中文](README_zh-CN.md) | 日本語 | [한국어](README_ko-KR.md) | [Deutsch](README_de-DE.md) | [Français](README_fr-FR.md) | [Italiano](README_it-IT.md) | [Русский](README_ru-RU.md) | [Español](README_es-ES.md) | [Português](README_pt-PT.md) | [العربية](README_ar-SA.md) | [Português (Brasil)](README_pt-BR.md)

MarkText Plus のプラグインの書き方と、エディタがプラグインに何を許し何を許さないか。

**プレリリース。** この SDK はプラグイン機構が落ち着くまで 0.x のままで、ここに書かれたマニフェストとプロトコルはバージョン間で変わりうります。それが今なにを意味し、将来どうなるかは下の[互換性](#互換性)に。

## まずランタイムを選ぶ

プラグインが動く機械にはエディタしかありません——Dart SDK も Node も Python もない。以下の大半はこの一点で決まります。

| `runtime` | 配布するもの | 動く場所 | 使いどころ |
|---|---|---|---|
| `lua` | `.lua` 一つ | 全プラットフォーム、ビルド不要 | 既定：メニューコマンド、問いかけ、テキスト処理 |
| `js` | `.js` 一つ | 全プラットフォーム、ビルド不要 | 同上、JavaScript のほうが書きやすいなら |
| `process` | **プラットフォームごとに一つ**の実行ファイル | ビルドしたプラットフォームだけ | 本物のツールチェーン、ライブラリ、長時間の処理が要るとき |
| `data` | コードなし | どこでも | テーマ、スニペット、辞書 |

`lua` か `js` から始めてください。そのプラグインは**スクリプト一つと `manifest.json` 一つ、それだけ**——ビルドもコンパイラも第二の言語も要らず、その二つのファイルが Windows・macOS・Linux でそのまま動きます。スクリプトがエディタを落とすこともありません。

スクリプトでは本当に足りないときだけ `process` に手を伸ばしてください。

この SDK と共に公開されている AI 翻訳プラグインが、Lua プラグインのディスク上の姿のすべてです：

```
manifest.json
plugin.lua
README.md
CHANGELOG.md
LICENSE
```

スクリプト一つ、マニフェスト一つ、あとの三つはドキュメント。**Dart は一つもありません。**

## このリポジトリにあるもの

**言語**ごとに一つのディレクトリ。それぞれが丸ごとコピーできる完全なプラグインです：

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

言語で名付けてあります。選ぶのはそれだからです。マニフェストの `runtime` は「どう動くか」を言うもので——`lua`、`js`、`process`——`examples/dart` は `process` プラグインです。Dart はその例がたまたま書かれている言語にすぎません。

**`process` プラグインは実行ファイルにコンパイルできる言語なら何で書いてもかまいません。** エディタはプログラムを起動して stdin/stdout で JSON-RPC を話すだけで、**そのプログラムが何から作られたかを知ることはありません**。Go、Rust、C++、C#、静的リンクした Python——どれでも動き、プロトコル以外にこのリポジトリから必要なものはありません：

- 一行に一つの JSON オブジェクト、stdin と stdout で；
- レスポンスは数値の `id` をそのまま返す；
- stdin が終端に達したら終了する；
- 環境に `MARKTEXT_PLUS_PLUGIN_TOKEN` がなければ終了する。ダブルクリックされた実行ファイルが待ち続けるのではなく、自分が何かを告げるように。

これが約束のすべてです。以下は Python 版で、このリポジトリのものを何も使っていません——エディタに応答し、誰も起動していないときは動くことを拒みます：

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

[`examples/dart/lib`](../../examples/dart/lib) は同じ四つの規則に端の処理を足したものです：不正な入力、未知のメソッド、一つのハンドラの例外がプラグイン全体を終わらせないこと。Dart がここにあるのはエディタがそれで書かれているからで、`dart compile exe` が動く例を手にする最短路だったからにすぎません。**要件でも推奨でもありません**：すでに知っている言語で四つの規則を書き直すほうが、ビルドに Dart ツールチェーンを足すより普通は簡単です。

三つのエントリポイントはどれも同じことをします。API を読み込んで呼ぶ。

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

`lua` と `js` は**わざと同じプラグインを二度書いたもの**です——同じマニフェスト、同じ権限、同じ挙動——なので二つを並べて、何が変わり何が変わらないかを読み取れます。**一つだけコピーしてください。** プラグインは `runtime` 一つとエントリポイント一つを宣言します。三つを同居させたディレクトリは、一つのマニフェストを着た三つのプラグインです。

### なぜ API モジュールが例の中にあるのか

**プラグインと一緒に配布されるからです。** `lib/marktext-plus.lua` は指し示す依存ではありません——残りと一緒にコピーして、あなたのものになるファイルです。`examples/lua` を丸ごとコピーすれば API ごと動くプラグインが手に入ります。別途取りに行く場所も、追随すべきバージョン番号もありません。

### API モジュールとは

スクリプトにとっては、**プラグインと共に配布される**ただの Lua や JavaScript です。エディタはあなたのファイルを読む前に `storage`、`t`、`require` をグローバルとして注入します。このモジュールはそれらを一つの名前にまとめ、アクションごとのコンストラクタを足します。おかげでプラグインは、綴りを誰も検査しないテーブルリテラルではなく `sdk.show(text, title)` と読めます。書き換えても、まったく使わなくてもかまいません——素のテーブルを返しても同じように動きます。

`examples/dart` にとっては実行ファイルに組み込まれる本物のライブラリで、スクリプトには要らないものを担っています：JSON-RPC のループ、起動チェック、終了処理。プロセスプラグインはパイプの向こう側にいます。

## プラグインは複数ファイルでよい

`require` が読み込むのは**あなた自身の**ファイルです——上の API モジュールもまさにこの方法で読み込まれ、隣に置いた他のものも同じです：

```lua
local helpers = require("lib.helpers")   -- lib/helpers.lua, returns its table
```

```js
const helpers = require("lib/helpers");  // lib/helpers.js, sets module.exports
```

何度 require しても一度だけ読み込まれます。名前は**パスではなく名前**です：あなたのプラグインのディレクトリの中だけで解決され、他では解決されません。だから大きなプラグインを分割しても——あるいは誰かの書いたライブラリを同梱しても——ディスクの他の部分へのアクセスは一切増えません。区切り文字を含む名前、`..`、先頭のドットは、何かを読む前に拒否されます。解決されたファイルはそのあと、あなたのディレクトリの中にあるか改めて確認されます。これが外を指すシンボリックリンクを捕らえます。

## 配布する前に試す

Lua や JS のプラグインはエディタが解釈するので、正直な検査はインストールすることです——**プラグイン → ZIP からインストール**。二つはもっと早く確かめられます：

```
node tool/run-js-plugin.mjs examples/js      # or your own plugin directory
```

は JavaScript プラグインをエディタと同じように動かします——同じ注入グローバル、プラグインディレクトリの中だけに届く同じ `require`、同じ二つのエントリポイント——そして、どの答えがエディタの期待する形でないかを告げます。エディタは QuickJS を使い、それはビルド済みアプリケーションの中にしか存在しないので、これが代役を務めます。

```
cd examples/dart && dart compile exe plugin.dart -o bin/linux/plugin
echo | ./bin/linux/plugin       # should refuse: it was not started by the editor
```

はコンパイル済みプラグインの検査のすべてです：ビルドが通ること、そして起動トークンを誰も与えなかったときに動くことを拒むこと。

## マニフェスト

`manifest.json` はプラグインのルートに置きます。エディタは**何も実行せずに**それを読みます。[`schema/manifest.schema.json`](../../schema/manifest.schema.json) を参照。

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

### プラットフォームごとの実行ファイル

`process` プラグインは `entrypoint` を使いません。**まずオペレーティングシステム別に**実行ファイルを挙げ、アーキテクチャはその下、省略可能です：

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

システムは**必ず**答えなければならない部分です——Windows のビルドと Linux のビルドは必ず別のファイルです。アーキテクチャはしばしばそうではないので、省略できます：

- **システム全体に一つのパス。** 上の `macos` はユニバーサルバイナリ：一つのファイルが両方のアーキテクチャを持ち、macOS のビルドは通常そうなります。それを言うために同じパスを二度書かせるのはむしろ悪い。
- **アーキテクチャの表。** 上の `windows` はそれぞれに別のビルドを配り、それ以外は対応しません。
- **共有の `default` と一つの専用ビルド。** 上の `linux` は arm64 以外では `bin/linux/plugin` を走らせ、arm64 には専用のものがあります。専用のほうが勝ちます。

システム名は `windows`、`macos`、`linux` だけ、アーキテクチャは `x64` と `arm64` だけ。**それ以外の名前はインストール時に拒否され、読み飛ばされません**——綴りを誤った `windwos` は、さもなければ読者がクリックしたその瞬間に「このプラグインはあなたのプラットフォームに対応していません」に化け、説明のしようがなくなります。

ビルドしていないプラットフォームは、推測されるのではなく名指しで伝えられます——「`linux-arm64` のビルドはありません。同梱されているのは `macos-x64`、`macos-arm64`、`windows-x64` です」。`runtime: "process"` と宣言して `entrypoints` がない、あるいはシステムを挙げてその下が空、はどちらも拒否されます。

## スクリプトプラグインはどう呼ばれるか

どちらのスクリプトランタイムも同期です——Lua インタプリタにコルーチンはなく、JS エンジンにも自前のイベントループはありません。時間のかかること（読者に尋ねる、モデルを呼ぶ）はエディタを止めてしまいます。だからスクリプトは待ちません。何をしてほしいかを述べた**アクションを返し**、エディタがそれを行い、その答えを持って再びスクリプトを呼びます。

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

同じ形を JavaScript で：

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

### アクション一覧

| 返すもの | エディタがすること | そのあと |
|---|---|---|
| `{ ask = "…", default = "…", choices = {…} }` | 読者に尋ねる。`choices` は押せるチップになり、代わりに入力されたものはそのまま採られる | `ctx.answer` を入れて `on_command` を再び呼ぶ |
| `{ ai = "…" }` | あなたのプロンプトを、読者が設定したモデルへ送る | `on_result(ctx, reply)` を呼ぶ |
| `{ show = "…", title = "…" }` | 小さなウィンドウに一つの答えを、コピーボタン付きで | 終了。ドキュメントには何も書かない |
| `{ panel = "…", title = "…" }` | 本文の横のパネルに表示する | 終了。ドキュメントには何も書かない |
| `{ pane = "…", title = "…", slot = "right"\|"bottom"\|"corner" }` | ドキュメント周りのペインの一つを埋める | 終了。ドキュメントには何も書かない |
| `{ notify = "…" }` | 読者に一行伝える | 終了 |
| `{ diff = { original = "…", result = "…" } }` | 二つのテキストを並べて見せる | 終了。ドキュメントには何も書かない |
| `{ replace = "…" }` | 選択範囲を置き換える | 終了 |
| その他 | 何もしない | 終了 |

**ペイン。** エディタはもともとタブをソースとプレビューに分けています。`pane` はそれを開いたものです。ドキュメントが二かける二の格子の最初のセルを占め、残る三つをあなたが埋められます——`right` は横、`bottom` は下、`corner` は右下。**誰も求めていないセルは描かれない**ので、`corner` だけ埋めても空の帯が二つ残ることはありません。エディタの知らないスロット名は**推測されず拒否されます**：頼んでもいない場所にペインが現れ、その理由を知る術がないのは、告げられるより悪い。

**`show` か `panel` か。** 数行は一つの答えです。小さなウィンドウが正しく、そのためにパネルを開くのは中身より家具のほうが多い。ドキュメント大の結果は、読者が画面上のものと突き合わせるためのもので、画面を覆うウィンドウはそれが置けない唯一の場所です。

一回の実行は 8 手までなので、`ask` を返し続けるスクリプトが読者を閉じ込めることはできません。

**プロンプトはあなたのものです。** エディタは資格情報を持ち、リクエストを送ります。あなたのプロンプトを書き換えることはなく、あなたのスクリプトが API キーを見ることもありません。モデルに渡されるのは、`ai` で返した文字列そのものです。

### スクリプトが届くもの

これだけです。`os` も `package` も `dofile` も `loadfile` もなく、ファイルシステムもネットワークもありません——スクリプトプラグインは見知らぬ人のリポジトリから来るので、宣言したものだけを受け取り、それ以外は何も受け取りません。

| | |
|---|---|
| `storage.get(key)` / `storage.set(key, value)` | 自分の設定を、自分のディレクトリに。文字列のみ。`storage.local` が必要 |
| `t(key)` | 自分の文字列を読者の言語で。訳がない鍵はその鍵自身が返る |
| `require(name)` | 自分のファイル。プラグインのディレクトリの中だけで解決される |
| `ctx.command` | 発火したメニュー項目またはコマンドの `id` |
| `ctx.selection` | 選択されたテキスト。何も選択されていなければ `""` |
| `ctx.document` | ドキュメント全体 |
| `ctx.answer` | 前回尋ねたときに読者が入力したもの。なければ nil/undefined |

### この Lua ができないこと

インタプリタは純 Dart の Lua で、だからこそスクリプトプラグインは何もインストールせずに済みます——そして完全ではありません。次の四つはすべて**黙って失敗します**。時間を食うのはそこです：何にも一致しないパターンは、何も入っていないドキュメントとまったく同じに見えます。

| 代わりに | 使うもの | 理由 |
|---|---|---|
| `#someString` | `string.len(s)` | `length error` を投げます。`#` は**テーブル**では動くので、感覚では区別できません |
| `s:match("%S")`、`%s` | 文字を比べる：`s:sub(i, i) == " "` | クラスが何にも一致せず、どの行も空行に見えます |
| `for l in s:gmatch("(.-)\n")` | `s:find("\n", pos, true)` と `s:sub` | 何も返しません |
| `s:gmatch("[^\n]*")` | 同上 | 空一致から先へ進みません |

エディタ自身のテストがこの四つを留めているので、インタプリタが置き換わればこの表は訂正されます。誤解を招いたまま残ることはありません。

JavaScript 側は QuickJS で、並べて書くほどの欠落はありません。

## 権限

マニフェストで宣言し、読者に示され、**強制されます**。VS Code と IntelliJ は権限一覧を示したうえで拡張を信用しますが、ここでは誰も審査しないので、エディタが確かめます。`ai.chat` なしに `{ ai = ... }` を返してもモデルは呼ばれず、そのプラグインがそれを求めていないと読者に伝えられます。

| 権限 | プラグインにできること |
|---|---|
| `document.read` | 開いているドキュメントと選択範囲を読む |
| `document.write` | 開いているドキュメントを変更する |
| `ui.contextMenu` | 右クリックメニューに項目を足す |
| `ui.menuBar` | メニューバーに項目を足す |
| `ui.toolbar` | ツールバーのボタンを足す |
| `ui.sidebar` | サイドバーのパネルを足す |
| `ui.statusBar` | ステータスバーの項目を足す |
| `ui.settings` | 自分の設定ページを持つ |
| `ui.commandPalette` | コマンドパレットにコマンドを足す |
| `ui.notifications` | 読者に伝える |
| `ai.chat` | 読者が設定したモデルに尋ねる（鍵は決して渡らない） |
| `storage.local` | 自分のディレクトリに自分の設定ファイルを持つ |
| `clipboard.read` / `clipboard.write` | クリップボード |
| `workspace.read` / `workspace.write` | 読者が開いたフォルダ配下のファイル |
| `network.request` | 自分で HTTP リクエストを出す。**求めうる最も広いもの**：読めるものは何でもどこへでも送れます |

使うものだけを求めてください。メニュー項目を足すために `network.request` を求めるプラグインは、読者が断るべきものです。

## 貢献ポイント

```json
"menus":    [{"id": "…", "title": "…", "location": "editor.contextMenu", "when": "selection"}],
"commands": [{"id": "…", "title": "…"}],
"toolbar":  [{"id": "…", "title": "…", "icon": "…"}],
"pages":    [{"id": "…", "title": "…"}]
```

`title` は翻訳キーでもかまいません。`location` はエディタが定めるスロットです——プラグインは名前のあるスロットに物を置くだけで、ピクセル座標を指定することも、自前のウィジェットをエディタに渡すこともできません。

`when` はメニュー項目をいつ出す価値があるかを述べます：`selection` は選択があるときだけ、`noSelection` はないときだけ、省略すれば常に。これがないと項目はすべて同時に出ます——何も選択していないのに「選択範囲を翻訳」、段落を指しているのに「ドキュメントを翻訳」。エディタの知らない値は、黙って「常に」と読まれるのではなく、インストール時に拒否されます。

## 設定

`settings` の各フィールドは、プラグイン自身の設定ページで本物のコントロールになります。描くのはエディタです：

| `type` | コントロール |
|---|---|
| `text` | テキストボックス |
| `password` | 中身を見せないテキストボックス |
| `number` | 数値のテキストボックス |
| `boolean` | スイッチ。`"true"` / `"false"` の文字列として保存されます |

値はプラグイン自身のディレクトリの `settings.json` にあるので、どのプラグインも他のプラグインの設定を読むことも書くこともできません。読者が保存したものは、**すでに動いているスクリプトにも次のコマンドで届きます**。次回の起動を待ちません。

## 翻訳

`locales` は言語をあなた自身の文字列表に対応させ、`defaultLocale` が最後の拠りどころです。`zh_CN` の読者はまず `zh_CN`（用意していれば）、次に `zh`、最後にあなたの既定言語を得ます。どの言語を用意するかは完全にあなた次第です——これはあなたの表であって、エディタの表ではありません。

## コンパイル済みプラグイン（`runtime: "process"`）

実行ファイルは子プロセスとして起動され、stdin/stdout 上で JSON-RPC 2.0 を、一行に一つの JSON オブジェクトで話します。レスポンスは数値の `id` をそのまま返します。このリポジトリの [`examples/dart/lib`](../../examples/dart/lib) が、Dart で書き `dart compile exe` でコンパイルするプラグインのためにそれを実装しています。

### ツールチェーンがなければ動かないソースは配布できません

これはコンパイル済みプラグインだけの話で、とりわけ Dart の話です。エディタがそれで書かれているからです：`entrypoint: "bin/plugin.dart"` はプラグインのインストール時に拒否されます。それを動かすには読者の機械に Dart SDK が要りますが、エディタはそれを入れませんし、あることを前提にもできません——リリースビルドには渡せるインタプリタもありません。コンパイルして（`dart compile exe`）、実行ファイルを配布してください。

ここに書いたことは Lua や JavaScript のプラグインには当てはまりません。あれらはエディタ自身が解釈するもので、それこそが存在意義です：Dart も、ツールチェーンも、ビルドも要りません。

**なぜエディタが読み込むライブラリではなくプロセスなのか。** Lua と JS のプラグインはすでにエディタのプロセス内で、その同じスレッドで動いています——それが通常の姿で、安全なのは解釈実行だからです：まずいスクリプトはエディタが捕まえられる例外を投げます。ネイティブコードにその境界はありません。スレッドはアドレス空間を共有するので、読み込まれた `.so` のどこかでのセグメンテーション違反、スタックオーバーフロー、`abort()` は、読者の保存していないドキュメントごとエディタを持っていき、報告する術もありません。出口のないループはウィンドウを凍らせ、中断もできません。アンロードは信頼できないので、「プラグインを無効にする」が実際には止めていません。別プロセスはその三つを取り戻します——落ちてもよく、タイムアウトで殺してもよく、エディタは生き残り、どのプラグインの仕業かを言えます。（Dart に関してはそもそも選択肢がありません：`dart compile` のサブコマンドは `exe`、`aot-snapshot`、`js`、`wasm` とスナップショット形式だけで、C から呼べる `.so` や `.dll` を作るものは**存在しません**。）

- **`serve()` を使えば、次の二つはすでに面倒を見ています。** コンパイル済みプラグインの全体：

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

- **エディタが起動したのでなければ動かないこと。** エディタは起動ごとにトークンを生成し、`MARKTEXT_PLUS_PLUGIN_TOKEN` 環境変数で渡します。それがなければ `serve()` はこれが何かを一行印字して 1 で終了します。一回の起動のために作られたトークンは、渡されていない者には打てません。argv ではなく環境を通るのは、`ps` を動かせるものなら argv を読めるからです。

  **これができること、できないこと。** 読者自身のディスク上のファイルの実行を止められるプログラムはありません——あなたの実行ファイルをダブルクリックすれば必ずプロセスは起きます。トークンが偽造不能にするのは**「エディタが自分を起動したのか」への答え**であり、だからプロセスは起きて、自分が何かを言い、終わります。stdin の前に座って止まったプログラムに見えることはありません。チェックを飛ばしたプラグインは誰にも守られていないプラグインです。チェックがこの段落ではなく SDK の `serve()` にあるのはそのためです。スクリプトプラグインはこれをただで手にします：`.lua` や `.js` はエディタが解釈するので、ダブルクリックしてもせいぜいテキストエディタが開くだけです。

- **stdin が終端に達したら終了すること。** それが終了を告げる手段であり、エディタが消えたときに自然に起きることでもあります——`serve()` はそのとき戻ります。エディタは自分が起動したプロセスを書き留めておき、次の起動でまだ生きているものを片付けます——ただし自分が起動したものだけです。**あなたが起動したプロセスは、あなたが片付けてください。**
- stdout はプロトコルの応答のために取っておき、診断は stderr へ。
- リクエストにはタイムアウトがあり、タイムアウトはあなたのプロセスだけを殺します。
- ホストから来るものはすべて信用できない入力として、使う前に検証してください。

## 互換性

プラグインは他人の機械にあるファイルで、このエディタがそれを読みます。壊しても、ここにいる誰かが見るビルド失敗にはなりません——その読者にとって動かなくなるだけです。ですから：

**`minAppVersion` は強制されます。** あなたのプラグインが動く最も古いエディタを述べれば、エディタはそれを守ります：それより古いエディタはインストールを拒み、すでに入っているものの実行も拒み、求められている版と手元の版を告げます。以前は読まれて無視されていました。それはフィールドがないことより悪い。

**エディタが断りなく取り上げないもの。** すべての権限名、すべての `runtime` 値、スクリプトが返せるすべてのアクション、`ctx` のすべてのフィールド、そして `storage`、`t`、`require` は、エディタ自身のソースにあるテストで留められています。これらの一覧に**加える**のは自由です。**取り除く、綴りを変える**とそのテストが落ちるので、うっかりそうなることはありません。

**0.x のあいだは**、意図した破壊的変更はなお起こりえます。そのときは changelog に、どうすればよいかと共に載ります。マニフェストとプロトコルが十分に長く手を触れられず、信頼するに値するようになったとき、ここは 1.0 になり、それは終わります：以後、今日プラグインが書けるものは動き続け、何かがなくなるのは、それをまだ支えている版で非推奨と告げたあとです。

**プラグインが自分で背負う部分。** エディタはあなたのプロンプトの挙動も、読者が設定したモデルも、`process` プラグインが自分で起こした子プロセスも保証できません。読者が手で実行ファイルを動かすのを止めることもできません——代わりに何をしているかは上の起動トークンに。

## 安全のために

- API キーをプラグインのディレクトリやマニフェストに書かないこと。
- プロトコルのメッセージ以外を stdout に出さないこと。
- 仕事に区切りをつけること。エディタにはタイムアウトと手数の上限があります。
- パスをさかのぼるエントリを含む ZIP は、インストール時に拒否されます。

この SDK は MIT ライセンスです。
