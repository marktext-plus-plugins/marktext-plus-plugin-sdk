# SDK de extensões do MarkText Plus

Aplicação principal: [MarkText Plus](https://github.com/SugarFatFree/marktext-plus)

[English](../../README.md) | [简体中文](README_zh-CN.md) | [日本語](README_ja-JP.md) | [한국어](README_ko-KR.md) | [Deutsch](README_de-DE.md) | [Français](README_fr-FR.md) | [Italiano](README_it-IT.md) | [Русский](README_ru-RU.md) | [Español](README_es-ES.md) | [Português](README_pt-PT.md) | [العربية](README_ar-SA.md) | Português (Brasil)

Como escrever uma extensão para o MarkText Plus, e o que o editor lhe deixa e não lhe deixa fazer.

**Pré-lançamento.** Este SDK fica em 0.x enquanto o sistema de extensões não assentar, e o manifesto e o protocolo aqui descritos ainda podem mudar entre versões. O que isso significa agora, e o que significará depois, está em [Compatibilidade](#compatibilidade), mais abaixo.

## Primeiro, escolha o motor de execução

Uma extensão corre em máquinas onde só está o editor — nem SDK do Dart, nem Node, nem Python. Este único fato decide quase tudo o que se segue.

| `runtime` | O que distribui | Corre em | Quando usar |
|---|---|---|---|
| `lua` | um arquivo `.lua` | todas as plataformas, sem compilar | o caso normal: comandos de menu, perguntas, trabalho com texto |
| `js` | um arquivo `.js` | todas as plataformas, sem compilar | o mesmo, se preferir escrever JavaScript |
| `process` | **um executável por plataforma** | só aquelas para que compilou | precisa de uma cadeia de ferramentas a sério, bibliotecas, ou trabalho demorado |
| `data` | nenhum código | em toda a parte | temas, excertos, dicionários |

Comece por `lua` ou `js`. Uma extensão dessas é **um arquivo de script e um `manifest.json`, e mais nada** — sem compilação, sem compilador, sem uma segunda linguagem, e esses dois arquivos correm tal e qual no Windows, no macOS e no Linux. Um script também não consegue deitar o editor abaixo.

Recorra a `process` apenas quando um script realmente não chegar.

A extensão de tradução por IA publicada ao lado deste SDK é tudo aquilo que uma extensão em Lua é no disco:

```
manifest.json
plugin.lua
README.md
CHANGELOG.md
LICENSE
```

Um script, um manifesto e três arquivos de documentação. **Nem sinal de Dart.**

## O que está neste repositório

Um diretório por linguagem, cada um uma extensão completa para copiar:

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

Têm o nome da **linguagem**, porque é isso que escolhe. O `runtime` no manifesto diz como corre — `lua`, `js`, `process` — e `examples/dart` é uma extensão `process`: Dart é apenas a linguagem em que o exemplo está escrito.

**Uma extensão `process` pode ser escrita em qualquer coisa que compile para um executável.** O editor arranca um programa e fala com ele em JSON-RPC por stdin e stdout; nunca fica a saber o que produziu esse programa. Go, Rust, C++, C#, um Python ligado estaticamente — servem todos, e nenhum precisa deste repositório para além do protocolo:

- um objeto JSON por linha, em stdin e stdout;
- as respostas devolvem o `id` numérico;
- terminar quando stdin chegar ao fim;
- terminar se `MARKTEXT_PLUS_PLUGIN_TOKEN` não estiver no ambiente, para que um executável aberto com clique duplo diga o que é em vez de ficar à espera.

É este o contmouse todo. Aqui está em Python, sem nada tirado deste repositório — responde ao editor e recusa-se em execução se ninguém o arrancou:

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

[`examples/dart/lib`](../../examples/dart/lib) são as mesmas quatro regras com as arestas tratadas: entrada malformada, um método desconhecido, um erro dentro de um manipulador que não termina a extensão inteira. Dart está aqui porque o editor é escrito em Dart e `dart compile exe` era o caminho mais curto para um exemplo funcionando. Não é um requisito nem uma recomendação: reescrever quatro regras na linguagem que já conhece é normalmente mais fácil do que juntar uma cadeia de ferramentas do Dart à sua compilação.

Os três pontos de entrada fazem a mesma coisa: carregam a API e chamam-na.

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

`lua` e `js` são deliberadamente **a mesma extensão escrita duas vezes** — mesmo manifesto, mesmas permissões, mesmo comportamento — para que se possam ler lado a lado. **Copie uma.** Uma extensão declara um `runtime` e um ponto de entrada; um diretório com as três são três extensões a vestir um só manifesto.

### Porque é que o módulo de API vive dentro de um exemplo

Porque é distribuído com a sua extensão. `lib/marktext-plus.lua` não é uma dependência para a qual se aponta — é um arquivo que copia com o resto e que a partir daí é seu. Copiar `examples/lua` por inteiro dá-lhe uma extensão funcionando, API incluída; não há outro sítio de onde a ir buscar, nem número de versão a acompanhar.

### O que é o módulo de API

Para um script é Lua ou JavaScript vulgar, **distribuído com a sua extensão**. O editor injeta `storage`, `t` e `require` como variáveis globais antes de o seu arquivo ser lido; o módulo junta-as sob um só nome e acrescenta um construtor por ação, de modo que uma extensão se lê como `sdk.show(text, title)` e não como uma tabela cuja ortografia ninguém verifica. Pode alterá-lo, ou não o usar de todo — devolver a tabela nua funciona exatamente da mesma maneira.

Para `examples/dart` é uma biblioteca a sério, compilada para dentro do seu executável, e traz o que um script não precisa: o ciclo JSON-RPC, a verificação de arranque e o encerramento. Uma extensão em processo está do outro lado de um tubo.

## Uma extensão pode ter vários arquivos

`require` carrega um dos **seus próprios** arquivos — o módulo de API acima é carregado exatamente assim, e o mesmo vale para tudo o que puser ao lado:

```lua
local helpers = require("lib.helpers")   -- lib/helpers.lua, returns its table
```

```js
const helpers = require("lib/helpers");  // lib/helpers.js, sets module.exports
```

Carregado uma só vez, por mais vezes que seja pedido. O nome é um nome, não um caminho: resolve-se dentro do diretório da sua extensão e em mais lado nenhum. Partir uma extensão grande — ou distribuir com ela uma biblioteca escrita por outra pessoa — não lhe custa, portanto, qualquer acesso adicional ao resto do disco. Um nome com um aba, com `..` ou com um ponto inicial é recusado antes de se ler seja o que for, e o arquivo resolvido é depois verificado como estando dentro do seu diretório — é isso que apanha uma ligação simbólica que aponta para fora.

## Experimentar uma extensão antes de a distribuir

Uma extensão em Lua ou JavaScript é interpretada pelo editor, por isso a prova honesta é instalá-la — **Extensões → Instalar a partir de ZIP**. Duas coisas podem ser verificadas mais cedo:

```
node tool/run-js-plugin.mjs examples/js      # or your own plugin diretory
```

corre uma extensão de JavaScript como o editor a corre — as mesmas variáveis globais injetadas, o mesmo `require` que só alcança o diretório da extensão, os mesmos dois pontos de entrada — e diz-lhe qual das suas respostas não tem a forma que o editor espera. O editor usa QuickJS, que só existe dentro de uma aplicação compilada; isto faz as vezes dele.

```
cd examples/dart && dart compile exe plugin.dart -o bin/linux/plugin
echo | ./bin/linux/plugin       # should refuse: it was not started by the editor
```

é toda a verificação de uma extensão compilada: compila, e recusa-se em execução quando ninguém lhe deu uma senha de arranque.

## Manifesto

`manifest.json` está na raiz da extensão. O editor lê-o **sem executar nada**. Veja [`schema/manifest.schema.json`](../../schema/manifest.schema.json).

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

### Executáveis por plataforma

Uma extensão `process` não usa `entrypoint`. Nomeia os seus executáveis **por sistema operativo**, com a arquitetura por baixo e só onde importa:

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

O sistema é a parte a que tem sempre de responder — uma compilação para Windows é um arquivo diferente de uma para Linux. A arquitetura muitas vezes não, por isso é opcional:

- **Um caminho para o sistema inteiro.** O `macos` acima é um binário universal: um arquivo que contém ambas as arquiteturas, como as compilações de macOS costumam ser distribuídas. Escrever o mesmo caminho duas vezes para o dizer seria pior.
- **Uma tabela de arquiteturas.** O `windows` acima distribui uma compilação separada para cada uma e não suporta mais nada.
- **Um `default` partilhado mais uma especialização.** O `linux` acima corre `bin/linux/plugin` em toda a parte exceto em arm64, que tem a sua. Ganha a especializada.

Os sistemas são `windows`, `macos` e `linux`; as arquiteturas, `x64` e `arm64`. **Qualquer outro nome é recusado ao instalar em vez de ser saltado** — de outro modo um `windwos` mal escrito transformar-se-ia, no momento do clique, em «esta extensão não suporta a sua plataforma», sem nada com que o explicar.

Uma plataforma para a qual não compilou é nomeada em vez de adivinhada — «não há compilação para `linux-arm64`; o que vem são `macos-x64`, `macos-arm64`, `windows-x64`». Declarar `runtime: "process"` sem `entrypoints`, ou nomear um sistema e não pôr nada por baixo, é recusado.

## Como é chamada uma extensão em script

Ambos os motores de script são síncronos — o interpretador de Lua não tem co-rotinas, e o motor de JS não tem ciclo de eventos próprio. Tudo o que leva tempo (perguntar a quem lê, chamar um modelo) bloquearia o editor. Por isso um script nunca espera: **devolve uma ação** que descreve o que quer que seja feito, o editor fá-lo, e volta a chamar o script com a resposta.

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

A mesma forma em JavaScript:

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

### As ações

| Devolve | O que o editor faz | Depois |
|---|---|---|
| `{ ask = "…", default = "…", choices = {…} }` | pergunta a quem lê; as `choices` aparecem como fichas para pressionar, e o que for escrito em vez delas é tomado tal como está | volta a chamar `on_command` com `ctx.answer` preenchido |
| `{ ai = "…" }` | envia a sua instrução ao modelo que quem lê configurou | chama `on_result(ctx, reply)` |
| `{ show = "…", title = "…" }` | mostra uma resposta numa janela pequena, com um botão para copiar | termina; nada é escrito |
| `{ panel = "…", title = "…" }` | mostra-a num painel ao lado do documento | termina; nada é escrito |
| `{ pane = "…", title = "…", slot = "right"\|"bottom"\|"corner", apply = true, replaces = "…" }` | preenche um dos quadros à volta do documento | termina; nada é escrito |
| `{ notify = "…" }` | diz uma linha a quem lê | termina |
| `{ diff = { original = "…", result = "…" } }` | mostra os dois textos lado a lado | termina; nada é escrito |
| `{ replace = "…" }` | substitui a seleção | termina |
| qualquer outra coisa | nada | termina |

**Os quadros.** O editor já divide uma aba entre código-fonte e pré-visualização; `pane` é essa divisão posta à sua disposição. No máximo quatro células, e **as duas metades da vista dividida são duas delas** — foi daí que isto nasceu, por isso um documento em vista dividida já são duas células antes de você preencher o que quer que seja.

A forma segue quantas células há, e é simétrica em cada passo:

| Células | Disposição |
|---|---|
| uma | o documento tem a aba inteira |
| duas | lado a lado, metade cada |
| três | uma metade dividida, a outra inteira |
| quatro | em cima à esquerda, em cima à direita, em baixo à esquerda, em baixo à direita |

Com três células e um documento que não está dividido, **você escolhe qual metade é dividida**: preencher `right` põe um quadro ao lado do documento, por isso a metade de cima divide-se e o outro quadro fica com a linha de baixo inteira; preencher apenas `bottom` e `corner` deixa ao documento a linha de cima inteira e divide a de baixo entre os dois. Quem lê pode depois mudá-lo a partir da barra de título do quadro — que metade está dividida é uma vista dos mesmos quadros, não uma decisão que você continua a tomar.

Os separadores arrastam-se, como o que há entre código-fonte e pré-visualização.

Os nomes `right`, `bottom`, `corner` são também a morada por onde você volta a um quadro mais tarde, para lhe acrescentar ou substituir o que ele tem. Um quadro é um quadro, seja qual for o nome que usou: preencher apenas `corner` dá-lhe um quadro ao lado do documento, e não um canto com duas células vazias à frente. Um nome que o editor não conhece é recusado em vez de adivinhado: um quadro que aparece onde não o pediu, sem maneira de saber porquê, é pior do que uma recusa.

**Um quadro pertence à aba em que foi aberto.** Mudar de aba tira-o do ecrã, fechar a aba fecha-o com ela, e voltar traz-a de novo.

**Oferecer-se para o escrever de volta.** O `apply` põe no quadro um botão Aplicar, que escreve o que ele tem no documento; o `replaces` diz o que isso substitui — vazio significando o documento inteiro. O que um modelo devolve merece ser lido antes de aterrar naquilo que quem lê estava a escrever: por isso uma reescrita é mostrada primeiro e escrita quando essa pessoa o disser, passando pelo histórico do editor, de modo que um desfazer a traz de volta. O que é substituído fica fixado quando o seu comando correu, e não quando o botão é premido: uma seleção que se moveu entretanto não manda o texto para um sítio qualquer. Precisa de `document.write`, que o editor verifica no botão e não por palavra sua.

**Diga que está trabalhando antes de começar.** Uma ação de quadro é lida antes de uma `ai`, então devolver ambas quer dizer «ponha isto e depois vá perguntar» — e um quadro de texto vazio com um pedido por trás é precisamente o que o editor desenha como «trabalhando». Até chegar o primeiro bloco ele o diz onde o texto vai ficar; depois passa para a barra do título, para que o andamento nunca fique por cima do que chegou. Devolver só o `ai` deixa a tela na mesma durante os segundos que o modelo leva, e se lê como um item de menu que não fez nada.

Fechar um quadro é como quem lê para você. Acrescentar a um que ele fechou é recusado, em vez de trazê-lo de volta um bloco de cada vez.

**`show` ou `panel`.** Umas quantas linhas são uma resposta: uma janela pequena serve, e um painel para isso é mais mobília do que conteúdo. Um resultado do tamanho de um documento é o que quem lê põe ao lado do que tem no tela, e uma janela por cima do tela é o único sítio onde não pode estar.

Uma execução está limitada a oito perguntas, portanto um script que responda a cada pergunta com outra não consegue prender quem lê.

**A instrução é sua.** O editor guarda as credenciais e faz o pedido; não reescreve a sua instrução, e o seu script nunca vê a chave da API. Ao modelo é apresentada exatamente a cadeia que devolveu em `ai`.

### A que é que um script consegue chegar

Só a isto. Sem `os`, sem `package`, sem `dofile`, sem `loadfile`, sem sistema de arquivos e sem rede — uma extensão em script vem do repositório de um desconhecido, por isso recebe o que declarou e mais nada.

| | |
|---|---|
| `storage.get(key)` / `storage.set(key, value)` | as suas definições, no seu diretório. Só cadeias. Precisa de `storage.local` |
| `t(key)` | a sua cadeia na língua de quem lê; uma chave desconhecida volta como ela própria |
| `require(name)` | um dos seus arquivos, resolvido só dentro do diretório da sua extensão |
| `ctx.command` | o `id` da entrada de menu ou do comando que disparou |
| `ctx.selection` | o texto selecionado, `""` quando nada está selecionado |
| `ctx.document` | o documento inteiro |
| `ctx.answer` | o que quem lê escreveu da última vez que perguntou, senão nil/undefined |
| `ctx.view` | como quem lê está vendo o documento: `source`, `preview` ou `split` |

### O que este Lua não faz

O interpretador é um Lua escrito inteiramente em Dart — é precisamente por isso que uma extensão em script não exige nada instalado — e não está completo. Os quatro pontos seguintes falham todos **em silêncio**, e é aí que se perde tempo: um padrão que não encontra nada é igualzinho a um documento que não contém nada.

| Em vez de | Use | Porque |
|---|---|---|
| `#someString` | `string.len(s)` | lança `length error`. `#` sobre uma *tabela* funciona, por isso não se distinguem ao toque |
| `s:match("%S")`, `%s` | comparar caracteres: `s:sub(i, i) == " "` | as classes não encontram nada, e toda a linha parece vazia |
| `for l in s:gmatch("(.-)\n")` | `s:find("\n", pos, true)` e `s:sub` | não devolve absolutamente nada |
| `s:gmatch("[^\n]*")` | o mesmo | nunca passa além de uma correspondência vazia |

O conjunto de testes do próprio editor fixa estes quatro pontos, por isso se o interpretador for substituído esta tabela será corrigida em vez de ficar induzindo em erro.

O motor de JavaScript é QuickJS e não tem lacunas comparáveis que valha a pena enumerar.

## Permissões

Declaradas no manifesto, mostradas a quem lê e **impostas**. O VS Code e o IntelliJ mostram uma lista de permissões e depois confiam na extensão; aqui ninguém revê nada, por isso é o editor que verifica. Devolver `{ ai = ... }` sem `ai.chat` não chama modelo nenhum — a quem lê é dito que a extensão não o pediu.

| Permissão | Permite à extensão |
|---|---|
| `document.read` | ler o documento aberto e a seleção |
| `document.write` | alterar o documento aberto |
| `ui.contextMenu` | acrescentar entradas ao menu de contexto |
| `ui.menuBar` | acrescentar entradas à barra de menus |
| `ui.toolbar` | acrescentar um botão à barra de ferramentas |
| `ui.sidebar` | acrescentar um painel à barra lateral |
| `ui.statusBar` | acrescentar um item à barra de estado |
| `ui.settings` | ter a sua própria página de definições |
| `ui.commandPalette` | acrescentar comandos à paleta |
| `ui.notifications` | dizer algo a quem lê |
| `ai.chat` | consultar o modelo configurado (a chave nunca é entregue) |
| `storage.local` | guardar o seu arquivo de definições no seu diretório |
| `clipboard.read` / `clipboard.write` | a área de transferência |
| `workspace.read` / `workspace.write` | os arquivos sob a pasta que quem lê abriu |
| `network.request` | fazer pedidos HTTP próprios. **O mais amplo que se pode pedir**: tudo o que conseguir ler, consegue enviar para qualquer lado |

Peça o que usa. Uma extensão que pede `network.request` para acrescentar uma entrada de menu é uma que quem lê deve recusar.

## Pontos de contribuição

```json
"menus":    [{"id": "…", "title": "…", "location": "editor.contextMenu", "when": "selection"}],
"commands": [{"id": "…", "title": "…"}],
"toolbar":  [{"id": "…", "title": "…", "icon": "…"}],
"panels":   [{"id": "…", "title": "…", "icon": "…"}],
"pages":    [{"id": "…", "title": "…"}]
```

`title` pode ser uma chave de tradução. `location` é um lugar que o editor define — uma extensão põe coisas em lugares com nome, nunca em coordenadas de pixels, e nunca entrega ao editor widgets seus.

`panels` põe um ícone na barra lateral direita; clicar nele abre uma gaveta preenchida ao executar o seu comando com o mesmo `id`. Precisa de `ui.sidebar`, e precisa de um `icon`, porque a barra é uma fila de ícones e uma entrada sem nada para desenhar seria um vazio que abre alguma coisa. Se nenhuma extensão contribuir com um painel, não há barra nenhuma — uma faixa de ícones sem ícones é largura tirada ao documento para nada.

Um painel abre-se e responde: um comando que devolva `ask` ou `ai` é ali relatado como texto em vez de parar para perguntar, porque uma gaveta não é uma conversa.

`when` diz quando uma entrada de menu vale a pena ser oferecida: `selection` só com uma seleção, `noSelection` só sem ela, e a ausência significa sempre. Sem isso são oferecidas todas ao mesmo tempo — «Traduzir a seleção» sem nada selecionado, e «Traduzir o documento» enquanto quem lê aponta para um parágrafo. Um valor que o editor não conhece é recusado ao instalar em vez de ser lido em silêncio como «sempre».

## Definições

Cada campo de `settings` torna-se um controlo a sério na página de definições da extensão, desenhado pelo editor:

| `type` | Controlo |
|---|---|
| `text` | uma caixa de texto |
| `password` | uma caixa de texto que não mostra o conteúdo |
| `number` | uma caixa de texto numérica |
| `boolean` | um interruptor; guardado como as cadeias `"true"` / `"false"` |

Os valores estão em `settings.json`, no diretório da própria extensão, por isso nenhuma extensão consegue ler nem escrever as definições de outra. O que quem lê guarda chega a um script já em execução no comando seguinte, e não no próximo arranque.

## Traduções

`locales` associa a uma língua as suas cadeias; `defaultLocale` diz para onde recuar. Quem lê em `zh_CN` recebe `zh_CN` se o tiver incluído, depois `zh`, depois a sua língua predefinida. Inclua as línguas que quiser — a tabela é sua, não do editor.

## Extensões compiladas (`runtime: "process"`)

O executável é arrancado como processo filho e fala JSON-RPC 2.0, um objeto JSON por linha, em stdin/stdout. As respostas devolvem o `id` numérico. [`examples/dart/lib`](../../examples/dart/lib), neste repositório, implementa isso para extensões escritas em Dart e compiladas com `dart compile exe`.

### Não pode distribuir código-fonte que precise de uma cadeia de ferramentas parem execução

Isto diz respeito só às extensões compiladas, e ao Dart em particular, porque o editor é escrito em Dart: `entrypoint: "bin/plugin.dart"` é recusado ao instalar. Executá-lo exigiria um SDK do Dart na máquina de quem lê, que o editor não instala e não pode pressupor — e uma compilação de lançamento não tem interpretador a quem o entregar. Compile-o (`dart compile exe`) e distribua o executável.

Nada disto se aplica a uma extensão em Lua ou JavaScript. Essas são interpretadas pelo próprio editor, que é todo o seu sentido: sem Dart, sem cadeia de ferramentas, sem compilação.

**Porquê um processo e não uma biblioteca que o editor carrega.** As extensões em Lua e JS já correm dentro do processo do editor, no mesmo thread — é o caso normal, e é seguro porque são interpretadas: um script mau lança um erro que o editor apanha. O código nativo não tem essa fronteira. Um fio partilha o espaço de endereçamento, por isso uma falha de segmentação, um estouro de pilha ou um `abort()` em qualquer ponto de um `.so` carregado leva o editor consigo, juntamente com o documento não guardado de quem lê e sem maneira nenhuma de relatar o que aconteceu; um ciclo sem saída congela a janela sem que se possa interrompê-lo; e o descarregamento não é fiável, por isso desativar uma extensão não a pararia de fato. Um processo à parte devolve as três coisas — pode ir abaixo, pode bloquear, pode ser morto por tempo esgotado, e o editor sobrevive e sabe dizer de que extensão se tratava. (Para o Dart, de resto, não há nada a escolher: `dart compile` conhece `exe`, `aot-snapshot`, `js`, `wasm` e os formatos de instantâneo. Não existe subcomando que produza um `.so` ou uma `.dll` que se possa chamar a partir de C.)

- **Use `serve()` e os dois pontos seguintes já estão tratados.** Uma extensão compilada inteira:

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

- **Não corra se não foi o editor a arrancá-lo.** O editor gera uma senha em cada arranque e passa-a na variável de ambiente `MARKTEXT_PLUS_PLUGIN_TOKEN`; sem ela, `serve()` imprime uma linha dizendo o que é este programa e termina com 1. Uma senha feita para um arranque não pode ser escrita por quem não a recebeu, e viaja no ambiente e não em argv, que pode ser lido por tudo o que saiba executar `ps`.

  **O que isto faz e o que não faz.** Nenhum programa consegue impedir que um arquivo no disco de quem lê seja executado — um clique duplo no seu executável arranca sempre um processo. O que a senha torna infalsificável é a sua resposta a «foi o editor que me arrancou?», de modo que o processo arranca, diz o que é, e termina, em vez de ficar sentado no stdin parecendo um programa encravado. Uma extensão que salta esta verificação é uma extensão que ninguém protegeu; é por isso que a verificação está no `serve()` do SDK e não apenas neste parágrafo. As extensões em script recebem isto de graça: um arquivo `.lua` ou `.js` é interpretado pelo editor, e um clique duplo abre, quando muito, um editor de texto.

- **Termine quando stdin chegar ao fim.** É assim que lhe é dito para parar, e é o que acontece por si se o editor desaparecer — `serve()` devolve o controlo nesse momento. O editor também anota os processos que arrancou e no arranque seguinte limpa os que ainda estejam vivos — mas só os que arrancou. **Os processos que *você* arranca é a si que compete limpá-los.**
- Deixe o stdout para as respostas do protocolo; os diagnósticos vão para stderr.
- Os pedidos têm um tempo limite, e esgotá-lo mata apenas o seu processo.
- Trate tudo o que o anfitrião envia como não fiável e verifique-o.

## Compatibilidade

Uma extensão é um arquivo na máquina de outra pessoa, que este editor lê. Parti-la não é uma falha de compilação que alguém aqui veja — é uma extensão que deixa de funcionar para quem a usa. Por isso:

**`minAppVersion` é imposto.** Diga qual é o editor mais antigo com que a sua extensão funciona e o editor cumpre-o: um mais antigo recusa instalá-la e recusa também executar uma já instalada, nomeando a versão pedida e a que existe. Antes este campo era lido e ignorado, o que é pior do que não o ter.

**O que o editor não tira sem avisar.** Cada nome de permissão, cada valor de `runtime`, cada ação que um script pode devolver, cada campo de `ctx`, e ainda `storage`, `t` e `require`, estão fixados por um teste no código do editor. **Acrescentar** a essas listas é livre; **retirar ou mudar o nome** faz esse teste falhar, e por isso não pode acontecer por descuido.

**Enquanto isto for 0.x**, uma alteração incompatível deliberada continua possível, e então constará do registo de alterações juntamente com o que fazer quanto a ela. Quando o manifesto e o protocolo tiverem ficado intactos tempo suficiente para merecerem confiança, isto passará a 1.0 e isso acaba: a partir daí, o que uma extensão pode escrever hoje continuará funcionando, e as coisas só desaparecerão depois de terem sido declaradas obsoletas numa versão que ainda as suportava.

**Onde uma extensão está por sua conta.** O editor não pode prometer o comportamento da sua instrução, nem o modelo que quem lê configurou, nem os processos filhos que uma extensão `process` arranque por si. Também não pode impedir quem lê de executar o seu executável à mão — o que faz em vez disso está acima, na senha de arranque.

## Regras de segurança

- Nunca escreva uma chave de API no diretório da extensão nem no manifesto.
- Para o stdout não vai nada que não sejam mensagens do protocolo.
- Mantenha o trabalho dentro de limites; o editor impõe tempos limite e limites de passos.
- Um ZIP com uma entrada que saia do diretório é recusado ao instalar.

O SDK é distribuído sob a licença MIT.
