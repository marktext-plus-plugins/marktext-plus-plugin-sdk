# MarkText Plus 플러그인 SDK

메인 애플리케이션: [MarkText Plus](https://github.com/SugarFatFree/marktext-plus)

[English](../../README.md) | [简体中文](README_zh-CN.md) | [日本語](README_ja-JP.md) | 한국어 | [Deutsch](README_de-DE.md) | [Français](README_fr-FR.md) | [Italiano](README_it-IT.md) | [Русский](README_ru-RU.md) | [Español](README_es-ES.md) | [Português](README_pt-PT.md) | [العربية](README_ar-SA.md) | [Português (Brasil)](README_pt-BR.md)

MarkText Plus 플러그인을 어떻게 쓰는지, 그리고 에디터가 플러그인에 무엇을 허용하고 무엇을 허용하지 않는지.

**프리릴리스.** 이 SDK는 플러그인 체계가 자리 잡을 때까지 0.x에 머무르며, 여기 적힌 매니페스트와 프로토콜은 버전 사이에 달라질 수 있습니다. 그것이 지금 무엇을 뜻하고 앞으로 무엇을 뜻할지는 아래 [호환성](#호환성)에 있습니다.

## 먼저 런타임을 고르세요

플러그인이 도는 기계에는 에디터밖에 없습니다 — Dart SDK도, Node도, Python도 없습니다. 아래 대부분은 이 한 가지가 정합니다.

| `runtime` | 배포하는 것 | 도는 곳 | 언제 쓰나 |
|---|---|---|---|
| `lua` | `.lua` 파일 하나 | 모든 플랫폼, 빌드 없음 | 기본: 메뉴 명령, 질문, 텍스트 작업 |
| `js` | `.js` 파일 하나 | 모든 플랫폼, 빌드 없음 | 위와 같음, JavaScript가 더 편하다면 |
| `process` | **플랫폼마다 하나씩**의 실행 파일 | 빌드한 플랫폼에서만 | 진짜 툴체인, 라이브러리, 오래 도는 작업이 필요할 때 |
| `data` | 코드 없음 | 어디서나 | 테마, 스니펫, 사전 |

`lua`나 `js`로 시작하세요. 그런 플러그인은 **스크립트 파일 하나와 `manifest.json` 하나, 그게 전부입니다** — 빌드도, 컴파일러도, 두 번째 언어도 필요 없고, 그 두 파일이 Windows·macOS·Linux에서 그대로 돕니다. 스크립트가 에디터를 무너뜨릴 수도 없습니다.

스크립트로 정말 안 될 때만 `process`에 손을 뻗으세요.

이 SDK와 함께 공개된 AI 번역 플러그인이 Lua 플러그인이 디스크에서 갖는 모습의 전부입니다:

```
manifest.json
plugin.lua
README.md
CHANGELOG.md
LICENSE
```

스크립트 하나, 매니페스트 하나, 나머지 셋은 문서. **Dart는 하나도 없습니다.**

## 이 저장소에 있는 것

**언어**마다 디렉터리 하나, 각각 통째로 복사할 수 있는 완전한 플러그인입니다:

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

**언어**를 따서 이름 붙였습니다. 고르는 것이 그것이기 때문입니다. 매니페스트의 `runtime`은 "어떻게 도는지"를 말하며 — `lua`, `js`, `process` — `examples/dart`는 `process` 플러그인입니다. Dart는 그 예제가 마침 쓰인 언어일 뿐입니다.

**`process` 플러그인은 실행 파일로 컴파일되는 어떤 언어로도 쓸 수 있습니다.** 에디터는 프로그램을 시작하고 stdin/stdout으로 JSON-RPC를 말할 뿐, **그 프로그램이 무엇으로 만들어졌는지 결코 알지 못합니다**. Go, Rust, C++, C#, 정적 링크한 Python — 모두 됩니다. 프로토콜 말고는 이 저장소에서 필요한 것이 없습니다:

- 한 줄에 JSON 객체 하나, stdin과 stdout으로;
- 응답은 숫자 `id`를 그대로 돌려주고;
- stdin이 끝에 닿으면 종료하고;
- 환경에 `MARKTEXT_PLUS_PLUGIN_TOKEN`이 없으면 종료합니다. 더블클릭된 실행 파일이 기다리는 대신 자기가 무엇인지 말하도록.

이것이 계약의 전부입니다. 아래는 Python 판으로, 이 저장소의 것을 아무것도 쓰지 않습니다 — 에디터에 응답하고, 아무도 시작하지 않았을 때는 돌기를 거부합니다:

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

[`examples/dart/lib`](../../examples/dart/lib)는 같은 네 규칙에 가장자리 처리를 더한 것입니다: 잘못된 입력, 모르는 메서드, 핸들러 하나의 오류가 플러그인을 끝내지 않는 것. Dart가 여기 있는 것은 에디터가 그것으로 쓰였기 때문이고, `dart compile exe`가 도는 예제를 갖는 가장 짧은 길이었기 때문입니다. **요구 사항도 권장도 아닙니다**: 이미 아는 언어로 네 규칙을 다시 쓰는 편이, 빌드에 Dart 툴체인을 더하는 것보다 보통 쉽습니다.

세 진입점은 모두 같은 일을 합니다. API를 불러와 호출합니다.

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

`lua`와 `js`는 **일부러 같은 플러그인을 두 번 쓴 것**입니다 — 같은 매니페스트, 같은 권한, 같은 동작 — 그래서 둘을 나란히 놓고 무엇이 바뀌고 무엇이 그대로인지 읽을 수 있습니다. **하나만 복사하세요.** 플러그인은 `runtime` 하나와 진입점 하나를 선언합니다. 셋을 함께 둔 디렉터리는 매니페스트 하나를 걸친 플러그인 셋입니다.

### 왜 API 모듈이 예제 안에 있나

**플러그인과 함께 배포되기 때문입니다.** `lib/marktext-plus.lua`는 가리키는 의존이 아닙니다 — 나머지와 함께 복사해서 당신 것이 되는 파일입니다. `examples/lua`를 통째로 복사하면 API까지 들어 있는 도는 플러그인을 얻습니다. 따로 받아올 곳도, 맞춰야 할 버전 번호도 없습니다.

### API 모듈이란

스크립트에게 그것은 **플러그인과 함께 배포되는** 평범한 Lua나 JavaScript입니다. 에디터는 당신의 파일을 읽기 전에 `storage`, `t`, `require`를 전역으로 주입합니다. 이 모듈은 그것들을 한 이름 아래 묶고 액션마다 생성자를 더합니다. 덕분에 플러그인은 철자를 아무도 검사하지 않는 테이블 리터럴이 아니라 `sdk.show(text, title)`로 읽힙니다. 고쳐도 되고, 아예 쓰지 않아도 됩니다 — 맨 테이블을 돌려줘도 똑같이 동작합니다.

`examples/dart`에게 그것은 실행 파일에 컴파일되어 들어가는 진짜 라이브러리이고, 스크립트에는 필요 없는 것을 지고 있습니다: JSON-RPC 루프, 시작 확인, 종료 처리. 프로세스 플러그인은 파이프 반대편에 있습니다.

## 플러그인은 여러 파일이어도 됩니다

`require`가 불러오는 것은 **당신 자신의** 파일입니다 — 위의 API 모듈도 바로 이렇게 불러오며, 옆에 둔 다른 것도 마찬가지입니다:

```lua
local helpers = require("lib.helpers")   -- lib/helpers.lua, returns its table
```

```js
const helpers = require("lib/helpers");  // lib/helpers.js, sets module.exports
```

몇 번을 require하든 한 번만 불러옵니다. 이름은 **경로가 아니라 이름**입니다: 당신 플러그인의 디렉터리 안에서만 풀리고 다른 곳에서는 풀리지 않습니다. 그래서 큰 플러그인을 쪼개도 — 누군가 쓴 라이브러리를 함께 배포해도 — 디스크의 나머지에 대한 접근은 조금도 늘지 않습니다. 구분자가 든 이름, `..`, 앞에 붙은 점은 무엇을 읽기 전에 거부됩니다. 풀린 파일은 그 뒤에 당신 디렉터리 안에 있는지 다시 확인되며, 이것이 밖을 가리키는 심볼릭 링크를 잡습니다.

## 배포하기 전에 해보기

Lua나 JS 플러그인은 에디터가 해석하므로 정직한 시험은 설치해 보는 것입니다 — **플러그인 → ZIP에서 설치**. 두 가지는 더 일찍 확인할 수 있습니다:

```
node tool/run-js-plugin.mjs examples/js      # or your own plugin directory
```

는 JavaScript 플러그인을 에디터와 같은 방식으로 돌립니다 — 같은 주입 전역, 플러그인 디렉터리 안에만 닿는 같은 `require`, 같은 두 진입점 — 그리고 어느 답이 에디터가 기대하는 모양이 아닌지 말해 줍니다. 에디터는 QuickJS를 쓰는데 그것은 빌드된 애플리케이션 안에만 있으므로, 이것이 대신 섭니다.

```
cd examples/dart && dart compile exe plugin.dart -o bin/linux/plugin
echo | ./bin/linux/plugin       # should refuse: it was not started by the editor
```

는 컴파일된 플러그인 검사의 전부입니다: 빌드되고, 시작 토큰을 아무도 주지 않았을 때 돌기를 거부합니다.

## 매니페스트

`manifest.json`은 플러그인 루트에 놓입니다. 에디터는 **아무것도 실행하지 않고** 그것을 읽습니다. [`schema/manifest.schema.json`](../../schema/manifest.schema.json)을 보세요.

```json
{
  "id": "com.example.my-plugin",
  "name": "My Plugin",
  "description": "plugin.description",
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

### 플랫폼별 실행 파일

`process` 플러그인은 `entrypoint`를 쓰지 않습니다. **먼저 운영체제별로** 실행 파일을 밝히고, 아키텍처는 그 아래에서 생략할 수 있습니다:

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

시스템은 **언제나** 답해야 하는 부분입니다 — Windows 빌드와 Linux 빌드는 반드시 다른 파일입니다. 아키텍처는 흔히 그렇지 않으므로 선택입니다:

- **시스템 하나에 경로 하나.** 위의 `macos`는 유니버설 바이너리입니다: 한 파일이 두 아키텍처를 담으며, macOS 빌드는 보통 그렇게 나옵니다. 그것을 말하려고 같은 경로를 두 번 쓰게 하는 편이 더 나쁩니다.
- **아키텍처 표.** 위의 `windows`는 각각에 별도 빌드를 배포하고 그 밖은 지원하지 않습니다.
- **공유 `default`와 전용 빌드 하나.** 위의 `linux`는 arm64 말고는 `bin/linux/plugin`을 돌리고, arm64에는 전용이 있습니다. 전용이 이깁니다.

시스템 이름은 `windows`, `macos`, `linux`뿐이고 아키텍처는 `x64`와 `arm64`뿐입니다. **그 밖의 이름은 설치할 때 거부되며, 건너뛰어지지 않습니다** — 잘못 쓴 `windwos`는 그러지 않으면 읽는 사람이 누르는 그 순간 "이 플러그인은 당신 플랫폼을 지원하지 않습니다"로 바뀌고, 설명할 길이 없습니다.

빌드하지 않은 플랫폼은 짐작되는 대신 이름으로 알려집니다 — "`linux-arm64` 빌드는 없습니다. 들어 있는 것은 `macos-x64`, `macos-arm64`, `windows-x64`입니다". `runtime: "process"`라고 선언하고 `entrypoints`가 없거나, 시스템을 밝히고 그 아래를 비워두면 둘 다 거부됩니다.

## 스크립트 플러그인은 어떻게 불리나

두 스크립트 런타임 모두 동기입니다 — Lua 인터프리터에 코루틴이 없고, JS 엔진에도 자기 이벤트 루프가 없습니다. 시간이 걸리는 일(읽는 사람에게 묻기, 모델 부르기)은 에디터를 멈추게 합니다. 그래서 스크립트는 기다리지 않습니다. 무엇을 해 주기를 바라는지 적은 **액션을 돌려주고**, 에디터가 그것을 하고, 그 답을 들고 다시 스크립트를 부릅니다.

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

같은 모양을 JavaScript로:

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

### 액션 목록

| 돌려주는 것 | 에디터가 하는 일 | 그다음 |
|---|---|---|
| `{ ask = "…", default = "…", choices = {…} }` | 읽는 사람에게 묻습니다. `choices`는 누를 수 있는 칩이 되고, 대신 입력된 것은 그대로 받습니다 | `ctx.answer`를 넣어 `on_command`를 다시 부릅니다 |
| `{ ai = "…" }` | 당신의 프롬프트를 읽는 사람이 설정한 모델로 보냅니다 | `on_result(ctx, reply)`를 부릅니다 |
| `{ show = "…", title = "…" }` | 작은 창에 답 하나를, 복사 버튼과 함께 | 끝. 문서에는 아무것도 쓰지 않습니다 |
| `{ panel = "…", title = "…" }` | 본문 옆 패널에 보여 줍니다 | 끝. 문서에는 아무것도 쓰지 않습니다 |
| `{ pane = "…", title = "…", slot = "right"\|"bottom"\|"corner", apply = true, replaces = "…" }` | 문서 둘레의 창 하나를 채웁니다 | 끝. 문서에는 아무것도 쓰지 않습니다 |
| `{ notify = "…" }` | 읽는 사람에게 한 줄 전합니다 | 끝 |
| `{ diff = { original = "…", result = "…" } }` | 두 텍스트를 나란히 보여 줍니다 | 끝. 문서에는 아무것도 쓰지 않습니다 |
| `{ replace = "…" }` | 선택 영역을 바꿉니다 | 끝 |
| 그 밖의 것 | 아무것도 하지 않습니다 | 끝 |

**창.** 에디터는 원래 탭을 소스와 미리보기로 나눕니다. `pane`은 그것을 열어 준 것입니다. 칸은 최대 넷이고, **분할 보기의 두 절반이 그중 둘입니다** — 이 구조가 거기서 나왔으므로, 분할 보기 중인 문서는 당신이 무엇을 채우기 전에 이미 두 칸입니다.

모양은 칸이 몇인지가 정하며, 어느 단계에서나 좌우 대칭입니다:

| 칸 | 배치 |
|---|---|
| 하나 | 문서가 탭 전체를 차지 |
| 둘 | 나란히, 절반씩 |
| 셋 | 한쪽 절반이 나뉘고, 다른 쪽은 통째로 |
| 넷 | 왼쪽 위, 오른쪽 위, 왼쪽 아래, 오른쪽 아래 |

칸이 셋이고 문서가 분할 보기가 아닐 때, **어느 절반을 나눌지는 당신이 고릅니다**: `right`를 채우면 문서 옆에 창이 오므로 위가 나뉘고, 다른 창이 아래 줄을 통째로 가집니다. `bottom`과 `corner`만 채우면 문서가 위 줄을 통째로 갖고 두 창이 아래를 나눕니다. 읽는 사람은 나중에 창 제목줄에서 바꿀 수 있습니다 — 어느 절반이 나뉘는가는 같은 창들의 한 가지 모습이지, 당신이 계속 정할 일이 아닙니다.

구분선은 끌 수 있습니다. 소스와 미리보기 사이의 그것과 같습니다.

슬롯 이름 `right`, `bottom`, `corner`는 나중에 그 창을 다시 가리키는 주소이기도 합니다 — 덧붙이거나 내용을 바꾸기 위한. 창 하나는 창 하나이며, 무엇을 자칭하든 같습니다: `corner`만 채우면 문서 옆의 창 하나를 얻지, 구석의 한 칸과 빈 두 칸이 아닙니다. 에디터가 모르는 슬롯 이름은 짐작되지 않고 거절됩니다: 요청하지 않은 곳에 나타나고 그 이유를 알 길도 없는 창은 거절보다 나쁩니다.

**창은 그것이 열린 탭의 것입니다.** 탭을 바꾸면 화면에서 사라지고, 탭을 닫으면 함께 닫히며, 돌아오면 다시 있습니다.

**문서에 쓰겠다고 제안할 수 있습니다.** `apply`는 창에 「적용」 단추를 붙여 창이 담은 것을 문서에 씁니다. `replaces`는 그것이 무엇을 대신하는지 말하고, 비어 있으면 문서 전체입니다. 모델이 돌려준 것은 읽는 사람이 쓰던 글에 들어가기 전에 읽어 볼 값어치가 있으므로, 고쳐 쓴 것은 먼저 보이고 그가 말할 때 쓰입니다. 에디터의 기록을 거치므로 되돌리기 한 번이면 돌아옵니다. 무엇을 대신할지는 당신의 명령이 돌던 때에 정해지지, 단추를 누른 때가 아닙니다: 그 사이에 옮겨 간 선택 때문에 글이 엉뚱한 곳에 들어가지 않습니다. `document.write`가 필요하고, 에디터는 그것을 단추에서 확인합니다. 당신의 표시를 믿어서가 아닙니다.

**시작하기 전에, 하고 있다고 말할 것.** 창 동작은 `ai`보다 먼저 읽히므로, 둘을 함께 돌려주는 것은 "이것을 띄운 다음 물어보라"는 뜻입니다. 그리고 본문이 비어 있고 뒤에 요청이 있는 창이야말로 에디터가 "작업 중"으로 그리는 모습입니다. 첫 덩어리가 닿기 전에는 본문 자리에서 그렇게 말하고, 닿은 뒤에는 제목 줄로 옮겨가므로 진행 표시가 도착한 내용을 덮는 일이 없습니다. `ai`만 돌려주면 모델이 쓰는 몇 초 동안 화면은 그대로여서, 아무것도 하지 않는 메뉴 항목처럼 읽힙니다.

창을 닫는 것이 읽는 사람이 여러분을 멈추는 방법입니다. 닫힌 창에 덧붙이는 일은 한 덩어리씩 되돌려 놓는 대신 거절됩니다.

**`show`인가 `panel`인가.** 몇 줄은 답 하나입니다. 작은 창이 맞고, 그것을 위해 패널을 여는 것은 내용보다 가구가 많은 일입니다. 문서 크기의 결과는 읽는 사람이 화면 위의 것과 맞대어 보려는 것이고, 화면을 덮는 창은 그것이 놓일 수 없는 유일한 곳입니다.

한 번의 실행은 8단계까지이므로, `ask`만 계속 돌려주는 스크립트가 읽는 사람을 가둘 수 없습니다.

**프롬프트는 당신 것입니다.** 에디터는 자격 증명을 쥐고 요청을 보냅니다. 당신의 프롬프트를 고쳐 쓰지 않고, 당신의 스크립트가 API 키를 보는 일도 없습니다. 모델에 건네지는 것은 `ai`로 돌려준 그 문자열 그대로입니다.

### 스크립트가 닿을 수 있는 것

이것뿐입니다. `os`도, `package`도, `dofile`도, `loadfile`도 없고, 파일 시스템도 네트워크도 없습니다 — 스크립트 플러그인은 낯선 사람의 저장소에서 오므로, 선언한 것만 받고 그 밖에는 아무것도 받지 않습니다.

| | |
|---|---|
| `storage.get(key)` / `storage.set(key, value)` | 자기 설정을 자기 디렉터리에. 문자열만. `storage.local`이 필요합니다 |
| `t(key)` | 자기 문자열을 읽는 사람의 언어로. 번역이 없는 키는 그 키 자신이 돌아옵니다 |
| `require(name)` | 자기 파일. 플러그인 디렉터리 안에서만 풀립니다 |
| `ctx.command` | 눌린 메뉴 항목이나 명령의 `id` |
| `ctx.selection` | 선택된 텍스트. 아무것도 선택되지 않았으면 `""` |
| `ctx.document` | 문서 전체 |
| `ctx.answer` | 지난번에 물었을 때 읽는 사람이 입력한 것, 없으면 nil/undefined |

### 이 Lua가 하지 못하는 것

인터프리터는 순수 Dart로 된 Lua이고, 그래서 스크립트 플러그인은 아무것도 설치할 필요가 없습니다 — 그리고 완전하지 않습니다. 아래 넷은 모두 **조용히 실패합니다**. 시간을 잡아먹는 것이 바로 그 점입니다: 아무것에도 맞지 않는 패턴은, 아무것도 없는 문서와 똑같아 보입니다.

| 대신 | 쓸 것 | 이유 |
|---|---|---|
| `#someString` | `string.len(s)` | `length error`를 던집니다. `#`는 **테이블**에서는 되므로 감으로는 구별할 수 없습니다 |
| `s:match("%S")`, `%s` | 문자를 비교: `s:sub(i, i) == " "` | 클래스가 아무것에도 맞지 않아 모든 줄이 빈 줄로 보입니다 |
| `for l in s:gmatch("(.-)\n")` | `s:find("\n", pos, true)`와 `s:sub` | 아무것도 돌려주지 않습니다 |
| `s:gmatch("[^\n]*")` | 위와 같음 | 빈 일치에서 앞으로 나아가지 않습니다 |

에디터 자신의 테스트가 이 넷을 붙잡아 두므로, 인터프리터가 바뀌면 이 표는 고쳐집니다. 잘못된 채로 남지 않습니다.

JavaScript 쪽은 QuickJS이고, 따로 적을 만한 빈틈은 없습니다.

## 권한

매니페스트에 선언되고, 읽는 사람에게 보이며, **강제됩니다**. VS Code와 IntelliJ는 권한 목록을 보여 준 뒤 확장을 믿지만, 여기서는 아무도 심사하지 않으므로 에디터가 확인합니다. `ai.chat` 없이 `{ ai = ... }`를 돌려줘도 모델은 불리지 않고, 그 플러그인이 그것을 청하지 않았다고 읽는 사람에게 알립니다.

| 권한 | 플러그인이 할 수 있는 일 |
|---|---|
| `document.read` | 열린 문서와 선택 영역을 읽기 |
| `document.write` | 열린 문서를 바꾸기 |
| `ui.contextMenu` | 오른쪽 클릭 메뉴에 항목 더하기 |
| `ui.menuBar` | 메뉴 바에 항목 더하기 |
| `ui.toolbar` | 툴바 버튼 더하기 |
| `ui.sidebar` | 사이드바 패널 더하기 |
| `ui.statusBar` | 상태 표시줄 항목 더하기 |
| `ui.settings` | 자기 설정 페이지 갖기 |
| `ui.commandPalette` | 명령 팔레트에 명령 더하기 |
| `ui.notifications` | 읽는 사람에게 알리기 |
| `ai.chat` | 읽는 사람이 설정한 모델에 묻기(키는 결코 넘어가지 않음) |
| `storage.local` | 자기 디렉터리에 자기 설정 파일 두기 |
| `clipboard.read` / `clipboard.write` | 클립보드 |
| `workspace.read` / `workspace.write` | 읽는 사람이 연 폴더 아래의 파일 |
| `network.request` | 스스로 HTTP 요청 보내기. **청할 수 있는 가장 넓은 것**: 읽을 수 있는 것은 무엇이든 어디로든 보낼 수 있습니다 |

쓰는 것만 청하세요. 메뉴 항목 하나를 더하려고 `network.request`를 청하는 플러그인은 읽는 사람이 거절해야 할 것입니다.

## 기여 지점

```json
"menus":    [{"id": "…", "title": "…", "location": "editor.contextMenu", "when": "selection"}],
"commands": [{"id": "…", "title": "…"}],
"toolbar":  [{"id": "…", "title": "…", "icon": "…"}],
"pages":    [{"id": "…", "title": "…"}]
```

`title`은 번역 키여도 됩니다. `location`은 에디터가 정하는 자리입니다 — 플러그인은 이름 있는 자리에 물건을 놓을 뿐, 픽셀 좌표를 정하거나 자기 위젯을 에디터에 건넬 수 없습니다.

`when`은 메뉴 항목을 언제 내놓을 만한지 말합니다: `selection`은 선택이 있을 때만, `noSelection`은 없을 때만, 생략하면 언제나. 이것이 없으면 항목이 모두 한꺼번에 나옵니다 — 아무것도 선택하지 않았는데 "선택 영역 번역", 문단을 가리키는 중에 "문서 번역". 에디터가 모르는 값은 조용히 "언제나"로 읽히는 대신 설치할 때 거부됩니다.

## 설정

`settings`의 각 필드는 플러그인 자신의 설정 페이지에서 진짜 컨트롤이 됩니다. 그리는 것은 에디터입니다:

| `type` | 컨트롤 |
|---|---|
| `text` | 텍스트 상자 |
| `password` | 내용을 보이지 않는 텍스트 상자 |
| `number` | 숫자 텍스트 상자 |
| `boolean` | 스위치. `"true"` / `"false"` 문자열로 저장됩니다 |

값은 플러그인 자신의 디렉터리의 `settings.json`에 있으므로, 어떤 플러그인도 다른 플러그인의 설정을 읽거나 쓸 수 없습니다. 읽는 사람이 저장한 것은 **이미 돌고 있는 스크립트에도 다음 명령에서 닿습니다**. 다음 실행을 기다리지 않습니다.

## 번역

`locales`는 언어를 당신 자신의 문자열 표에 대응시키고, `defaultLocale`이 마지막 기댈 곳입니다. `zh_CN`의 읽는 사람은 먼저 `zh_CN`(준비했다면), 다음 `zh`, 마지막으로 당신의 기본 언어를 받습니다. 어떤 언어를 준비할지는 온전히 당신이 정합니다 — 이것은 당신의 표이지 에디터의 표가 아닙니다.

## 컴파일된 플러그인(`runtime: "process"`)

실행 파일은 자식 프로세스로 시작되고, stdin/stdout에서 JSON-RPC 2.0을 한 줄에 JSON 객체 하나로 말합니다. 응답은 숫자 `id`를 그대로 돌려줍니다. 이 저장소의 [`examples/dart/lib`](../../examples/dart/lib)가 Dart로 쓰고 `dart compile exe`로 컴파일하는 플러그인을 위해 그것을 구현합니다.

### 툴체인이 있어야 도는 소스는 배포할 수 없습니다

이것은 컴파일된 플러그인에 대한 것이고, 특히 Dart에 대한 것입니다. 에디터가 그것으로 쓰였기 때문입니다: `entrypoint: "bin/plugin.dart"`는 플러그인을 설치할 때 거부됩니다. 그것을 돌리려면 읽는 사람의 기계에 Dart SDK가 있어야 하는데, 에디터는 그것을 설치하지도, 있다고 가정하지도 못합니다 — 릴리스 빌드에는 건네줄 인터프리터도 없습니다. 컴파일해서(`dart compile exe`) 실행 파일을 배포하세요.

여기 쓴 것은 Lua나 JavaScript 플러그인과는 상관이 없습니다. 그것들은 에디터가 직접 해석하며, 그것이 바로 존재 이유입니다: Dart도, 툴체인도, 빌드도 없습니다.

**왜 에디터가 불러오는 라이브러리가 아니라 프로세스인가.** Lua와 JS 플러그인은 이미 에디터 프로세스 안에서, 같은 스레드에서 돕니다 — 그것이 보통의 모습이고, 안전한 것은 해석되기 때문입니다: 잘못된 스크립트는 에디터가 잡을 수 있는 예외를 던집니다. 네이티브 코드에는 그 경계가 없습니다. 스레드는 주소 공간을 공유하므로 불러온 `.so` 어디에서든 세그먼테이션 오류, 스택 넘침, `abort()`가 나면 읽는 사람의 저장하지 않은 문서와 함께 에디터를 가져가고, 보고할 방법도 없습니다. 출구 없는 루프는 창을 얼리고 끊을 수도 없습니다. 언로드는 믿을 수 없어서 "플러그인 끄기"가 실제로는 멈추지 않습니다. 별도 프로세스는 그 셋을 되찾아 줍니다 — 죽어도 되고, 시간 초과로 죽여도 되며, 에디터는 살아남아 어느 플러그인 탓인지 말할 수 있습니다. (Dart에 대해서는 애초에 고를 것이 없습니다: `dart compile`의 하위 명령은 `exe`, `aot-snapshot`, `js`, `wasm`과 스냅숏 형식뿐이고, C가 부를 수 있는 `.so`나 `.dll`을 만드는 것은 **없습니다**.)

- **`serve()`를 쓰면 아래 둘은 이미 처리되어 있습니다.** 컴파일된 플러그인의 전부:

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

- **에디터가 시작한 것이 아니면 돌지 마세요.** 에디터는 시작할 때마다 토큰을 만들어 `MARKTEXT_PLUS_PLUGIN_TOKEN` 환경 변수로 넘깁니다. 그것이 없으면 `serve()`는 이것이 무엇인지 한 줄 찍고 1로 끝냅니다. 한 번의 시작을 위해 만들어진 토큰은 받지 못한 사람이 칠 수 없습니다. argv가 아니라 환경으로 오는 것은, `ps`를 돌릴 수 있는 것이면 argv를 읽을 수 있기 때문입니다.

  **이것이 하는 일과 하지 못하는 일.** 읽는 사람 자신의 디스크에 있는 파일의 실행을 막을 수 있는 프로그램은 없습니다 — 실행 파일을 더블클릭하면 프로세스는 반드시 시작됩니다. 토큰이 위조 불가능하게 만드는 것은 **"에디터가 나를 시작했는가"에 대한 답**이고, 그래서 프로세스는 시작되어 자기가 무엇인지 말하고 끝납니다. stdin 앞에 앉아 멈춘 프로그램처럼 보이지 않습니다. 확인을 건너뛴 플러그인은 아무도 지켜 주지 않은 플러그인입니다. 확인이 이 문단이 아니라 SDK의 `serve()`에 있는 이유가 그것입니다. 스크립트 플러그인은 이것을 거저 얻습니다: `.lua`나 `.js`는 에디터가 해석하므로 더블클릭해도 기껏해야 텍스트 에디터가 열립니다.

- **stdin이 끝에 닿으면 종료하세요.** 그것이 종료를 알리는 방법이고, 에디터가 사라졌을 때 저절로 일어나는 일이기도 합니다 — `serve()`는 그때 돌아옵니다. 에디터는 자기가 시작한 프로세스를 적어 두고 다음 시작 때 아직 살아 있는 것을 치웁니다 — 다만 자기가 시작한 것만입니다. **당신이 시작한 프로세스는 당신이 치워야 합니다.**
- stdout은 프로토콜 응답에 남겨 두고, 진단은 stderr로 쓰세요.
- 요청에는 시간 제한이 있고, 시간 초과는 당신의 프로세스만 죽입니다.
- 호스트가 보내는 모든 것을 믿을 수 없는 입력으로 보고, 쓰기 전에 검사하세요.

## 호환성

플러그인은 다른 사람의 기계에 있는 파일이고, 이 에디터가 그것을 읽습니다. 그것을 망가뜨리는 일은 여기 있는 누구도 보는 빌드 실패가 아닙니다 — 그 읽는 사람에게 동작하지 않게 되는 일입니다. 그래서:

**`minAppVersion`은 강제됩니다.** 당신의 플러그인이 도는 가장 오래된 에디터를 밝히면 에디터가 그것을 지킵니다: 그보다 오래된 에디터는 설치를 거부하고, 이미 설치된 것의 실행도 거부하며, 어느 버전이 필요하고 어느 버전이 있는지 말합니다. 예전에는 읽히고 무시되었는데, 그것은 필드가 없는 것보다 나쁩니다.

**에디터가 알리지 않고 가져가지 않는 것.** 모든 권한 이름, 모든 `runtime` 값, 스크립트가 돌려줄 수 있는 모든 액션, `ctx`의 모든 필드, 그리고 `storage`, `t`, `require`는 에디터 자신의 소스에 있는 테스트로 고정되어 있습니다. 그 목록에 **더하는** 것은 자유입니다. **빼거나 이름을 바꾸면** 그 테스트가 실패하므로 실수로 그렇게 될 수 없습니다.

**0.x인 동안에는** 의도한 파괴적 변경이 여전히 있을 수 있고, 그때는 어떻게 해야 하는지와 함께 changelog에 실립니다. 매니페스트와 프로토콜이 충분히 오래 손대지 않은 채로 남아 믿을 만해지면 여기는 1.0이 되고, 그것은 끝납니다: 그 뒤로는 오늘 플러그인이 쓸 수 있는 것이 계속 동작하고, 무언가가 사라지는 것은 그것을 아직 지원하는 릴리스에서 폐기를 알린 다음입니다.

**플러그인이 스스로 지는 부분.** 에디터는 당신의 프롬프트의 동작도, 읽는 사람이 설정한 모델도, `process` 플러그인이 스스로 시작한 자식 프로세스도 보장하지 못합니다. 읽는 사람이 손으로 실행 파일을 돌리는 것을 막지도 못합니다 — 대신 무엇을 하는지는 위의 시작 토큰에 있습니다.

## 안전 수칙

- API 키를 플러그인 디렉터리나 매니페스트에 쓰지 마세요.
- 프로토콜 메시지 말고는 stdout에 아무것도 내보내지 마세요.
- 일에 끝을 두세요. 에디터에는 시간 제한과 단계 제한이 있습니다.
- 경로를 거슬러 올라가는 항목이 든 ZIP은 설치할 때 거부됩니다.

이 SDK는 MIT 라이선스입니다.
