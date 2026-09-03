# SDK de complementos de MarkText Plus

Aplicación principal: [MarkText Plus](https://github.com/SugarFatFree/marktext-plus)

[English](../../README.md) | [简体中文](README_zh-CN.md) | [日本語](README_ja-JP.md) | [한국어](README_ko-KR.md) | [Deutsch](README_de-DE.md) | [Français](README_fr-FR.md) | [Italiano](README_it-IT.md) | [Русский](README_ru-RU.md) | Español | [Português](README_pt-PT.md) | [العربية](README_ar-SA.md) | [Português (Brasil)](README_pt-BR.md)

Cómo escribir un complemento para MarkText Plus, y qué le deja hacer el editor y qué no.

**Versión preliminar.** Este SDK se queda en 0.x mientras el sistema de complementos se asienta, y el manifiesto y el protocolo que aquí se describen todavía pueden cambiar de una versión a otra. Qué significa eso ahora, y qué significará después, está en [Compatibilidad](#compatibilidad), más abajo.

## Primero, elija el motor de ejecución

Un complemento se ejecuta en máquinas donde solo está el editor: ni SDK de Dart, ni Node, ni Python. Ese único hecho decide casi todo lo que sigue.

| `runtime` | Qué distribuye | Se ejecuta en | Cuándo usarlo |
|---|---|---|---|
| `lua` | un archivo `.lua` | todas las plataformas, sin compilar | el caso normal: órdenes de menú, preguntas, trabajo con texto |
| `js` | un archivo `.js` | todas las plataformas, sin compilar | lo mismo, si prefiere escribir JavaScript |
| `process` | **un ejecutable por plataforma** | solo aquellas para las que compiló | necesita una cadena de herramientas real, bibliotecas o trabajo prolongado |
| `data` | ningún código | en todas partes | temas, fragmentos, diccionarios |

Empiece por `lua` o `js`. Un complemento así es **un archivo de script y un `manifest.json`, y nada más**: sin compilación, sin compilador, sin un segundo lenguaje, y esos dos archivos funcionan tal cual en Windows, macOS y Linux. Un script tampoco puede tumbar el editor.

Recurra a `process` solo cuando un script de verdad no baste.

El complemento de traducción con IA publicado junto a este SDK es todo lo que un complemento en Lua es en el disco:

```
manifest.json
plugin.lua
README.md
CHANGELOG.md
LICENSE
```

Un script, un manifiesto y tres archivos de documentación. **Ni rastro de Dart.**

## Qué hay en este repositorio

Un directorio por lenguaje, cada uno un complemento completo para copiar:

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

Llevan el nombre del **lenguaje**, porque es lo que usted elige. `runtime` en el manifiesto dice cómo se ejecuta —`lua`, `js`, `process`— y `examples/dart` es un complemento `process`: Dart es simplemente el lenguaje en que está escrito su ejemplo.

**Un complemento `process` puede escribirse en cualquier cosa que compile a un ejecutable.** El editor arranca un programa y le habla en JSON-RPC por stdin y stdout; nunca llega a saber qué produjo ese programa. Go, Rust, C++, C#, un Python enlazado estáticamente: todos sirven, y ninguno necesita de este repositorio nada más que el protocolo:

- un objeto JSON por línea, en stdin y stdout;
- las respuestas devuelven el `id` numérico;
- terminar cuando stdin llegue al final;
- terminar si `MARKTEXT_PLUS_PLUGIN_TOKEN` no está en el entorno, para que un ejecutable abierto con doble clic diga qué es en lugar de quedarse esperando.

Ese es todo el contrato. Aquí está en Python, sin nada tomado de este repositorio: responde al editor y se niega a ejecutarse si nadie lo ha lanzado:

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

[`examples/dart/lib`](../../examples/dart/lib) son esas mismas cuatro reglas con los bordes atendidos: entrada mal formada, un método desconocido, un error dentro de un manejador que no termina el complemento entero. Dart está aquí porque el editor está escrito en Dart y `dart compile exe` era el camino más corto a un ejemplo que funcionara. No es un requisito ni una recomendación: reescribir cuatro reglas en el lenguaje que ya conoce suele ser más fácil que añadir una cadena de herramientas de Dart a su compilación.

Los tres puntos de entrada hacen lo mismo: cargan la API y la llaman.

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

`lua` y `js` son deliberadamente **el mismo complemento escrito dos veces** —mismo manifiesto, mismos permisos, mismo comportamiento— para poder leer ambos uno junto a otro. **Copie uno.** Un complemento declara un `runtime` y un punto de entrada; un directorio con los tres son tres complementos con un solo manifiesto puesto.

### Por qué el módulo de API vive dentro de un ejemplo

Porque se distribuye con su complemento. `lib/marktext-plus.lua` no es una dependencia a la que se apunta: es un archivo que copia junto con lo demás y que a partir de ahí es suyo. Copiar `examples/lua` entero le da un complemento que funciona, API incluida; no hay otro sitio del que traerla ni número de versión al que seguir el paso.

### Qué es el módulo de API

Para un script es Lua o JavaScript corriente, **distribuido con su complemento**. El editor inyecta `storage`, `t` y `require` como variables globales antes de que se lea su archivo; el módulo las reúne bajo un solo nombre y añade un constructor por acción, de modo que un complemento se lee como `sdk.show(text, title)` y no como una tabla cuya ortografía nadie comprueba. Puede modificarlo, o no usarlo en absoluto: devolver la tabla desnuda funciona exactamente igual.

Para `examples/dart` es una biblioteca de verdad, compilada dentro de su ejecutable, y lleva lo que un script no necesita: el bucle JSON-RPC, la comprobación de arranque y el cierre. Un complemento de proceso está al otro lado de una tubería.

## Un complemento puede tener varios archivos

`require` carga uno de **sus propios** archivos; el módulo de API de arriba se carga exactamente así, y cualquier otra cosa que ponga al lado también:

```lua
local helpers = require("lib.helpers")   -- lib/helpers.lua, returns its table
```

```js
const helpers = require("lib/helpers");  // lib/helpers.js, sets module.exports
```

Se carga una sola vez, por muchas veces que se pida. El nombre es un nombre, no una ruta: se resuelve dentro del directorio de su complemento y en ningún otro sitio. Partir un complemento grande —o distribuir con él una biblioteca escrita por otra persona— no le cuesta, por tanto, ningún acceso adicional al resto del disco. Un nombre con un separador, con `..` o con un punto inicial se rechaza antes de leer nada, y el archivo resuelto se comprueba después para asegurar que está dentro de su directorio: eso es lo que atrapa un enlace simbólico que apunta afuera.

## Probar un complemento antes de distribuirlo

Un complemento en Lua o JavaScript lo interpreta el editor, así que la prueba honesta es instalarlo: **Complementos → Instalar desde ZIP**. Dos cosas pueden comprobarse antes:

```
node tool/run-js-plugin.mjs examples/js      # or your own plugin directory
```

ejecuta un complemento de JavaScript como lo hace el editor —las mismas variables globales inyectadas, el mismo `require` que solo alcanza el directorio del complemento, los mismos dos puntos de entrada— y le dice cuál de sus respuestas no tiene la forma que el editor espera. El editor usa QuickJS, que solo existe dentro de una aplicación compilada; esto hace sus veces.

```
cd examples/dart && dart compile exe plugin.dart -o bin/linux/plugin
echo | ./bin/linux/plugin       # should refuse: it was not started by the editor
```

es toda la comprobación de un complemento compilado: compila, y se niega a ejecutarse cuando nadie le ha dado un testigo de arranque.

## Manifiesto

`manifest.json` está en la raíz del complemento. El editor lo lee **sin ejecutar nada**. Véase [`schema/manifest.schema.json`](../../schema/manifest.schema.json).

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

### Ejecutables por plataforma

Un complemento `process` no usa `entrypoint`. Nombra sus ejecutables **por sistema operativo**, con la arquitectura debajo y solo donde importa:

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

El sistema es la parte que siempre hay que responder: una compilación de Windows es un archivo distinto de una de Linux. La arquitectura a menudo no, así que es opcional:

- **Una ruta para todo el sistema.** `macos` arriba es un binario universal: un archivo que contiene ambas arquitecturas, como se distribuyen de ordinario las compilaciones de macOS. Escribir dos veces la misma ruta para decirlo sería peor.
- **Una tabla de arquitecturas.** `windows` arriba distribuye una compilación distinta para cada una y no admite ninguna otra.
- **Un `default` compartido más una especialización.** `linux` arriba ejecuta `bin/linux/plugin` en todas partes salvo en arm64, que tiene la suya. Gana la especializada.

Los sistemas son `windows`, `macos` y `linux`; las arquitecturas, `x64` y `arm64`. **Cualquier otro nombre se rechaza al instalar en vez de saltarse** —de otro modo un `windwos` mal escrito se convertiría, en el momento del clic, en «este complemento no admite su plataforma», sin nada con que explicarlo.

Una plataforma para la que no compiló se nombra en vez de adivinarse: «no hay compilación para `linux-arm64`; se distribuyen `macos-x64`, `macos-arm64`, `windows-x64`». Declarar `runtime: "process"` sin `entrypoints`, o nombrar un sistema y no poner nada debajo, se rechaza.

## Cómo se llama a un complemento de script

Ambos motores de script son síncronos: el intérprete de Lua no tiene corrutinas y el motor de JS no tiene bucle de eventos propio. Todo lo que lleva tiempo (preguntar a quien lee, llamar a un modelo) bloquearía el editor. Por eso un script nunca espera: **devuelve una acción** que describe qué quiere que se haga, el editor lo hace y vuelve a llamar al script con la respuesta.

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

La misma forma en JavaScript:

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

### Las acciones

| Devuelve | Qué hace el editor | Después |
|---|---|---|
| `{ ask = "…", default = "…", choices = {…} }` | pregunta a quien lee; `choices` aparecen como fichas que pulsar, y lo que se escriba en su lugar se toma tal cual | vuelve a llamar a `on_command` con `ctx.answer` puesto |
| `{ ai = "…" }` | envía su indicación al modelo que quien lee haya configurado | llama a `on_result(ctx, reply)` |
| `{ show = "…", title = "…" }` | muestra una respuesta en una ventana pequeña, con un botón para copiar | termina; no se escribe nada |
| `{ panel = "…", title = "…" }` | la muestra en un panel junto al documento | termina; no se escribe nada |
| `{ pane = "…", title = "…", slot = "right"\|"bottom"\|"corner" }` | rellena uno de los cuadros alrededor del documento | termina; no se escribe nada |
| `{ notify = "…" }` | dice una línea a quien lee | termina |
| `{ diff = { original = "…", result = "…" } }` | muestra los dos textos uno al lado del otro | termina; no se escribe nada |
| `{ replace = "…" }` | sustituye la selección | termina |
| cualquier otra cosa | nada | termina |

**Los cuadros.** El editor ya divide una pestaña entre fuente y vista previa; `pane` es esa división puesta a su disposición. El documento se queda con la primera celda de una cuadrícula de dos por dos y usted puede rellenar las otras tres: `right` al lado, `bottom` debajo, `corner` abajo a la derecha. **Una celda que nadie ha pedido no se dibuja**, así que rellenar solo `corner` no deja dos franjas vacías. Un nombre de hueco que el editor no conoce se rechaza en vez de adivinarse: un cuadro que aparece donde usted no lo pidió, sin manera de saber por qué, es peor que una negativa.

**`show` o `panel`.** Unas pocas líneas son una respuesta: una ventana pequeña está bien, y un panel para eso es más mueble que contenido. Un resultado del tamaño de un documento es lo que quien lee sostiene contra lo que tiene en pantalla, y una ventana encima de la pantalla es el único sitio donde no puede estar.

Una ejecución está limitada a ocho preguntas, así que un script que responda a cada pregunta con otra no puede retener a quien lee.

**La indicación es suya.** El editor guarda las credenciales y hace la petición; no reescribe su indicación, y su script nunca ve la clave de API. Al modelo se le presenta exactamente la cadena que devolvió en `ai`.

### A qué puede llegar un script

Solo a esto. Sin `os`, sin `package`, sin `dofile`, sin `loadfile`, sin sistema de archivos y sin red: un complemento de script viene del repositorio de un desconocido, así que recibe lo que declaró y nada más.

| | |
|---|---|
| `storage.get(key)` / `storage.set(key, value)` | sus propios ajustes, en su propio directorio. Solo cadenas. Necesita `storage.local` |
| `t(key)` | su propia cadena en el idioma de quien lee; una clave desconocida vuelve tal cual |
| `require(name)` | uno de sus propios archivos, resuelto solo dentro del directorio de su complemento |
| `ctx.command` | el `id` de la entrada de menú o la orden que se disparó |
| `ctx.selection` | el texto seleccionado, `""` cuando no hay nada seleccionado |
| `ctx.document` | el documento entero |
| `ctx.answer` | lo que quien lee escribió la última vez que preguntó, si no nil/undefined |
| `ctx.view` | cómo está mirando el documento: `source`, `preview` o `split` |

### Lo que este Lua no hace

El intérprete es un Lua escrito enteramente en Dart —precisamente por eso un complemento de script no exige nada instalado— y no está completo. Los cuatro puntos siguientes fallan todos **en silencio**, y ahí es donde se pierde el tiempo: un patrón que no encuentra nada se ve exactamente igual que un documento que no contiene nada.

| En lugar de | Use | Porque |
|---|---|---|
| `#someString` | `string.len(s)` | lanza `length error`. `#` sobre una *tabla* funciona, así que no se distinguen al tacto |
| `s:match("%S")`, `%s` | comparar caracteres: `s:sub(i, i) == " "` | las clases no encuentran nada, y toda línea parece vacía |
| `for l in s:gmatch("(.-)\n")` | `s:find("\n", pos, true)` y `s:sub` | no devuelve absolutamente nada |
| `s:gmatch("[^\n]*")` | lo mismo | nunca avanza más allá de una coincidencia vacía |

El conjunto de pruebas del propio editor fija estos cuatro puntos, así que si se sustituye el intérprete esta tabla se corregirá en vez de quedarse induciendo a error.

El motor de JavaScript es QuickJS y no tiene lagunas comparables que merezca la pena enumerar.

## Permisos

Declarados en el manifiesto, mostrados a quien lee y **aplicados**. VS Code e IntelliJ muestran una lista de permisos y luego confían en la extensión; aquí nadie revisa nada, así que comprueba el editor. Devolver `{ ai = ... }` sin `ai.chat` no llama a ningún modelo: a quien lee se le dice que el complemento no lo pidió.

| Permiso | Permite al complemento |
|---|---|
| `document.read` | leer el documento abierto y la selección |
| `document.write` | modificar el documento abierto |
| `ui.contextMenu` | añadir entradas al menú contextual |
| `ui.menuBar` | añadir entradas a la barra de menús |
| `ui.toolbar` | añadir un botón a la barra de herramientas |
| `ui.sidebar` | añadir un panel a la barra lateral |
| `ui.statusBar` | añadir un elemento a la barra de estado |
| `ui.settings` | tener su propia página de ajustes |
| `ui.commandPalette` | añadir órdenes a la paleta |
| `ui.notifications` | decirle algo a quien lee |
| `ai.chat` | consultar el modelo configurado (la clave nunca se entrega) |
| `storage.local` | guardar su propio archivo de ajustes en su propio directorio |
| `clipboard.read` / `clipboard.write` | el portapapeles |
| `workspace.read` / `workspace.write` | los archivos bajo la carpeta que quien lee abrió |
| `network.request` | hacer sus propias peticiones HTTP. **Lo más amplio que se puede pedir**: todo lo que pueda leer, puede enviarlo a cualquier sitio |

Pida lo que use. Un complemento que pide `network.request` para añadir una entrada de menú es uno que quien lee debería rechazar.

## Puntos de contribución

```json
"menus":    [{"id": "…", "title": "…", "location": "editor.contextMenu", "when": "selection"}],
"commands": [{"id": "…", "title": "…"}],
"toolbar":  [{"id": "…", "title": "…", "icon": "…"}],
"panels":   [{"id": "…", "title": "…", "icon": "…"}],
"pages":    [{"id": "…", "title": "…"}]
```

`title` puede ser una clave de traducción. `location` es un hueco que define el editor: un complemento pone cosas en huecos con nombre, nunca en coordenadas de píxeles, y nunca le entrega al editor widgets propios.

`panels` pone un icono en la barra lateral derecha; pulsarlo abre un cajón que se rellena ejecutando su orden con el mismo `id`. Necesita `ui.sidebar`, y necesita un `icon`, porque la barra es una fila de iconos y una entrada sin nada que dibujar sería un hueco que abre algo. Si ningún complemento aporta un panel, no hay barra en absoluto: una franja de iconos sin iconos es anchura quitada al documento para nada.

Un panel se abre y responde: una orden que devuelve `ask` o `ai` se informa allí como texto en vez de detenerse a preguntar, porque un cajón no es una conversación.

`when` dice cuándo merece la pena ofrecer una entrada de menú: `selection` solo con una selección, `noSelection` solo sin ella, y su ausencia significa siempre. Sin eso se ofrecen todas a la vez: «Traducir la selección» sin nada seleccionado y «Traducir el documento» mientras quien lee señala un párrafo. Un valor que el editor no conoce se rechaza al instalar en lugar de leerse en silencio como «siempre».

## Ajustes

Cada campo de `settings` se convierte en un control real en la página de ajustes del complemento, dibujado por el editor:

| `type` | Control |
|---|---|
| `text` | una caja de texto |
| `password` | una caja de texto que no muestra su contenido |
| `number` | una caja de texto numérica |
| `boolean` | un interruptor; guardado como las cadenas `"true"` / `"false"` |

Los valores viven en `settings.json`, dentro del directorio propio del complemento, así que ningún complemento puede leer ni escribir los ajustes de otro. Lo que quien lee guarda llega a un script ya en marcha en su siguiente orden, no en el siguiente arranque.

## Traducciones

`locales` asocia a un idioma sus propias cadenas; `defaultLocale` dice a qué recurrir. Quien lee en `zh_CN` obtiene `zh_CN` si usted lo incluyó, luego `zh`, luego su idioma predeterminado. Incluya los idiomas que quiera: es su tabla, no la del editor.

## Complementos compilados (`runtime: "process"`)

El ejecutable se arranca como proceso hijo y habla JSON-RPC 2.0, un objeto JSON por línea, por stdin/stdout. Las respuestas devuelven el `id` numérico. [`examples/dart/lib`](../../examples/dart/lib), en este repositorio, lo implementa para complementos escritos en Dart y compilados con `dart compile exe`.

### No puede distribuir código fuente que necesite una cadena de herramientas para ejecutarse

Esto atañe solo a los complementos compilados, y a Dart en particular, porque el editor está escrito en Dart: `entrypoint: "bin/plugin.dart"` se rechaza al instalar. Ejecutarlo exigiría un SDK de Dart en la máquina de quien lee, que el editor ni instala ni puede dar por supuesto, y una compilación de publicación no tiene intérprete al que entregárselo. Compílelo (`dart compile exe`) y distribuya el ejecutable.

Nada de esto se aplica a un complemento en Lua o JavaScript. Esos los interpreta el propio editor, que es todo su sentido: sin Dart, sin cadena de herramientas, sin compilación.

**Por qué un proceso y no una biblioteca que el editor cargue.** Los complementos en Lua y JS ya se ejecutan dentro del proceso del editor, en su mismo hilo: ese es el caso normal, y es seguro porque son interpretados: un script malo lanza un error que el editor atrapa. El código nativo no tiene esa frontera. Un hilo comparte el espacio de direcciones, así que un fallo de segmentación, un desbordamiento de pila o un `abort()` en cualquier punto de un `.so` cargado se lleva al editor, junto con el documento sin guardar de quien lee y sin manera alguna de informar de lo ocurrido; un bucle sin salida congela la ventana sin que se pueda interrumpir; y la descarga no es fiable, así que desactivar un complemento no lo detendría de verdad. Un proceso aparte devuelve esas tres cosas: puede caerse, colgarse, ser terminado por tiempo de espera, y el editor sobrevive y sabe decir de qué complemento se trataba. (Para Dart, además, no hay nada que elegir: `dart compile` conoce `exe`, `aot-snapshot`, `js`, `wasm` y los formatos de instantánea. No existe ninguna subinstrucción que produzca un `.so` o una `.dll` invocable desde C.)

- **Use `serve()` y los dos puntos siguientes ya están resueltos.** Un complemento compilado entero:

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

- **No se ejecute si no le arrancó el editor.** El editor genera un testigo en cada arranque y lo pasa en la variable de entorno `MARKTEXT_PLUS_PLUGIN_TOKEN`; sin él, `serve()` imprime una línea diciendo qué es este programa y termina con 1. Un testigo hecho para un arranque no lo puede teclear quien no lo recibió, y viaja en el entorno y no en argv, que puede leer cualquier cosa capaz de ejecutar `ps`.

  **Qué hace esto y qué no.** Ningún programa puede impedir que se ejecute un archivo que está en el disco de quien lee: hacer doble clic en su ejecutable siempre arrancará un proceso. Lo que el testigo vuelve infalsificable es su respuesta a «¿me arrancó el editor?», de modo que el proceso arranca, dice qué es y termina, en lugar de quedarse sentado en stdin pareciendo un programa colgado. Un complemento que se salta la comprobación es un complemento que nadie protegió; por eso la comprobación está en `serve()` del SDK y no solo en este párrafo. Los complementos de script lo obtienen gratis: un archivo `.lua` o `.js` lo interpreta el editor, y un doble clic abre, como mucho, un editor de texto.

- **Termine cuando stdin llegue al final.** Así se le dice que pare, y así ocurre solo si el editor desaparece: `serve()` devuelve el control en ese momento. El editor además anota los procesos que arrancó y en el siguiente inicio limpia los que sigan vivos, pero solo los que arrancó él. **Los procesos que arranca *usted* los limpia usted.**
- Deje stdout para las respuestas del protocolo; los diagnósticos van a stderr.
- Las peticiones tienen un tiempo de espera, y agotarlo mata solo su proceso.
- Trate todo lo que envía el anfitrión como no fiable y valídelo.

## Compatibilidad

Un complemento es un archivo en la máquina de otra persona, que este editor lee. Romperlo no es un fallo de compilación que alguien de aquí vaya a ver: es un complemento que deja de funcionar para quienes lo usan. Por eso:

**`minAppVersion` se aplica.** Diga cuál es el editor más antiguo con el que su complemento funciona y el editor lo respeta: uno más antiguo se niega a instalarlo y se niega también a ejecutar uno ya instalado, nombrando la versión que se pide y la que hay. Antes se leía y se ignoraba, lo cual es peor que no tener el campo.

**Lo que el editor no quitará sin avisar.** Cada nombre de permiso, cada valor de `runtime`, cada acción que un script puede devolver, cada campo de `ctx`, y `storage`, `t` y `require`, están fijados por una prueba en el código del editor. **Añadir** a esas listas es libre; **quitar o renombrar** hace fallar esa prueba, y por tanto no puede ocurrir por descuido.

**Mientras esto sea 0.x**, un cambio incompatible deliberado sigue siendo posible, y entonces constará en el registro de cambios junto con qué hacer al respecto. Cuando el manifiesto y el protocolo lleven intactos el tiempo suficiente para merecer confianza, esto pasará a 1.0 y eso terminará: a partir de ahí, lo que un complemento puede escribir hoy seguirá funcionando, y las cosas solo desaparecerán tras haberse declarado obsoletas en una versión que aún las admitía.

**Dónde un complemento está solo.** El editor no puede prometer el comportamiento de su indicación, ni el modelo que quien lee haya configurado, ni los procesos hijos que un complemento `process` arranque por su cuenta. Tampoco puede impedir que quien lee ejecute su ejecutable a mano: lo que hace en su lugar está más arriba, en el testigo de arranque.

## Reglas de seguridad

- No escriba nunca una clave de API en el directorio del complemento ni en el manifiesto.
- A stdout no va nada que no sean mensajes del protocolo.
- Mantenga el trabajo acotado; el editor impone tiempos de espera y límites de pasos.
- Un ZIP con una entrada que sale del directorio se rechaza al instalar.

El SDK se distribuye bajo licencia MIT.
