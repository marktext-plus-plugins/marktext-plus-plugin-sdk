# MarkText Plus Plug-in-SDK

Hauptanwendung: [MarkText Plus](https://github.com/SugarFatFree/marktext-plus)

[English](../../README.md) | [简体中文](README_zh-CN.md) | [日本語](README_ja-JP.md) | [한국어](README_ko-KR.md) | Deutsch | [Français](README_fr-FR.md) | [Italiano](README_it-IT.md) | [Русский](README_ru-RU.md) | [Español](README_es-ES.md) | [Português](README_pt-PT.md) | [العربية](README_ar-SA.md) | [Português (Brasil)](README_pt-BR.md)

Wie man ein Plug-in für MarkText Plus schreibt, und was der Editor einem erlaubt und was nicht.

**Vorabversion.** Dieses SDK bleibt bei 0.x, solange sich das Plug-in-System noch setzt; das hier beschriebene Manifest und Protokoll können sich zwischen Versionen ändern. Was das jetzt heißt und was es später heißen wird, steht unten unter [Kompatibilität](#kompatibilität).

## Zuerst die Laufzeit wählen

Ein Plug-in läuft auf Maschinen, auf denen nur der Editor ist — kein Dart-SDK, kein Node, kein Python. Diese eine Tatsache entscheidet das meiste, was folgt.

| `runtime` | Was Sie ausliefern | Läuft auf | Wann |
|---|---|---|---|
| `lua` | eine `.lua`-Datei | jeder Plattform, ohne Build | der Normalfall: Menübefehle, Rückfragen, Textarbeit |
| `js` | eine `.js`-Datei | jeder Plattform, ohne Build | dasselbe, falls Sie lieber JavaScript schreiben |
| `process` | **eine ausführbare Datei je Plattform** | nur den Plattformen, für die Sie gebaut haben | Sie brauchen eine echte Toolchain, Bibliotheken oder lange laufende Arbeit |
| `data` | gar keinen Code | überall | Themes, Snippets, Wörterbücher |

Fangen Sie mit `lua` oder `js` an. So ein Plug-in ist **eine Skriptdatei und eine `manifest.json`, sonst nichts** — kein Build, kein Compiler, keine zweite Sprache, und dieselben zwei Dateien laufen unter Windows, macOS und Linux. Ein Skript kann den Editor auch nicht zum Absturz bringen.

Greifen Sie erst dann zu `process`, wenn ein Skript wirklich nicht reicht.

Das AI-Übersetzungs-Plug-in, das neben diesem SDK veröffentlicht ist, ist alles, was ein Lua-Plug-in auf der Platte ausmacht:

```
manifest.json
plugin.lua
README.md
CHANGELOG.md
LICENSE
```

Ein Skript, ein Manifest und drei Dateien Dokumentation. **Nirgends Dart.**

## Was in diesem Repository liegt

Ein Verzeichnis je Sprache, jedes ein vollständiges Plug-in zum Kopieren:

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

Benannt nach der **Sprache**, denn die wählen Sie. `runtime` im Manifest benennt, wie es läuft — `lua`, `js`, `process` — und `packages/dart` ist ein `process`-Plug-in: Dart ist bloß die Sprache, in der sein Beispiel geschrieben ist.

**Ein `process`-Plug-in darf in allem geschrieben sein, was sich zu einer ausführbaren Datei kompilieren lässt.** Der Editor startet ein Programm und spricht JSON-RPC mit ihm über stdin und stdout; er erfährt nie, was dieses Programm hervorgebracht hat. Go, Rust, C++, C#, ein statisch gelinktes Python — alle funktionieren, und keines braucht aus diesem Repository mehr als das Protokoll:

- ein JSON-Objekt je Zeile, auf stdin und stdout;
- Antworten geben die numerische `id` zurück;
- beenden, wenn stdin das Ende erreicht;
- beenden, wenn `MARKTEXT_PLUS_PLUGIN_TOKEN` nicht in der Umgebung steht, damit eine doppelgeklickte Datei sagt, was sie ist, statt zu warten.

Das ist der ganze Vertrag. Hier ist er in Python, ohne irgendetwas aus diesem Repository — es antwortet dem Editor und weigert sich zu laufen, wenn es niemand gestartet hat:

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

[`packages/dart/lib`](../../packages/dart/lib) sind dieselben vier Regeln mit den Rändern versorgt: fehlerhafte Eingaben, eine unbekannte Methode, ein Fehler in einem Handler, der nicht das ganze Plug-in beendet. Dart steht hier, weil der Editor darin geschrieben ist und `dart compile exe` der kürzeste Weg zu einem lauffähigen Beispiel war. Es ist weder Bedingung noch Empfehlung: vier Regeln in der Sprache neu zu schreiben, die Sie ohnehin können, ist meist leichter, als Ihrem Build eine Dart-Toolchain hinzuzufügen.

Alle drei Einstiegspunkte tun dasselbe: die API laden und sie aufrufen.

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

`lua` und `js` sind mit Absicht **dasselbe Plug-in, zweimal geschrieben** — gleiches Manifest, gleiche Berechtigungen, gleiches Verhalten — damit man beide nebeneinander lesen kann. **Kopieren Sie eines.** Ein Plug-in erklärt eine `runtime` und einen Einstiegspunkt; ein Verzeichnis mit allen dreien sind drei Plug-ins in einem Manifest.

### Warum das API-Modul in einem Beispiel liegt

Weil es mit Ihrem Plug-in ausgeliefert wird. `lib/marktext-plus.lua` ist keine Abhängigkeit, auf die Sie zeigen — es ist eine Datei, die Sie mitkopieren und dann besitzen. `packages/lua` im Ganzen zu kopieren gibt Ihnen ein lauffähiges Plug-in samt API; es gibt keinen zweiten Ort, von dem man es holt, und keine Versionsnummer, mit der man Schritt halten muss.

### Was das API-Modul ist

Für ein Skript ist es gewöhnliches Lua oder JavaScript, das **mit Ihrem Plug-in ausgeliefert wird**. Der Editor spritzt `storage`, `t` und `require` als Globals ein, bevor Ihre Datei gelesen wird; das Modul fasst sie unter einem Namen zusammen und fügt je Aktion einen Konstruktor hinzu, sodass ein Plug-in sich als `sdk.show(text, title)` liest statt als Tabellenliteral, dessen Schreibweise niemand prüft. Sie dürfen es ändern oder gar nicht benutzen — die schlichte Tabelle zurückzugeben funktioniert genauso.

Für `packages/dart` ist es eine echte Bibliothek, in Ihre ausführbare Datei kompiliert, und sie trägt etwas, das ein Skript nicht braucht: die JSON-RPC-Schleife, die Startprüfung und das Herunterfahren. Ein Prozess-Plug-in sitzt auf der anderen Seite einer Pipe.

## Ein Plug-in darf aus mehreren Dateien bestehen

`require` lädt eine **Ihrer eigenen** Dateien — das API-Modul oben wird genau so geladen, und alles andere, was Sie danebenlegen, ebenso:

```lua
local helpers = require("lib.helpers")   -- lib/helpers.lua, returns its table
```

```js
const helpers = require("lib/helpers");  // lib/helpers.js, sets module.exports
```

Einmal geladen, so oft es auch verlangt wird. Der Name ist ein Name, kein Pfad: er wird innerhalb des Verzeichnisses Ihres Plug-ins aufgelöst und sonst nirgends. Ein großes Plug-in aufzuteilen — oder eine fremde Bibliothek mitzuliefern — kostet Sie also keinerlei Zugriff auf den Rest der Platte. Ein Name mit einem Trennzeichen, einem `..` oder einem führenden Punkt wird abgelehnt, bevor irgendetwas gelesen wird, und die aufgelöste Datei wird danach noch daraufhin geprüft, ob sie in Ihrem Verzeichnis liegt — das fängt einen symbolischen Link, der hinauszeigt.

## Ein Plug-in ausprobieren, bevor Sie es ausliefern

Ein Lua- oder JavaScript-Plug-in wird vom Editor interpretiert, die ehrliche Probe ist also, es zu installieren — **Plug-ins → Aus ZIP installieren**. Ein kompiliertes lässt sich früher prüfen:

```
cd packages/dart && dart compile exe plugin.dart -o bin/linux/plugin
echo | ./bin/linux/plugin       # should refuse: it was not started by the editor
```

ist die ganze Prüfung für ein kompiliertes Plug-in: es baut, und es weigert sich zu laufen, wenn ihm niemand ein Start-Token gegeben hat.

## Manifest

`manifest.json` liegt im Wurzelverzeichnis des Plug-ins. Der Editor liest es, **ohne irgendetwas auszuführen**. Siehe [`schema/manifest.schema.json`](../../schema/manifest.schema.json).

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

### Ausführbare Dateien je Plattform

Ein `process`-Plug-in benutzt kein `entrypoint`. Es benennt seine ausführbaren Dateien **nach Betriebssystem**, die Architektur darunter und nur wo sie zählt:

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

Das System ist der Teil, den Sie immer beantworten müssen — ein Windows-Build ist eine andere Datei als ein Linux-Build. Die Architektur oft nicht, deshalb ist sie optional:

- **Ein Pfad für das ganze System.** `macos` oben ist ein Universal Binary: eine Datei, die beide Architekturen enthält, wie macOS-Builds gewöhnlich ausgeliefert werden. Denselben Pfad zweimal zu schreiben, um das zu sagen, wäre schlechter.
- **Eine Tabelle von Architekturen.** `windows` oben liefert für jede einen eigenen Build und unterstützt sonst nichts.
- **Ein gemeinsames `default` plus eine Spezialisierung.** `linux` oben führt überall `bin/linux/plugin` aus, außer auf arm64, das seinen eigenen bekommt. Der spezialisierte gewinnt.

Systeme sind `windows`, `macos` und `linux`; Architekturen sind `x64` und `arm64`. **Alles andere wird beim Installieren abgelehnt statt übersprungen** — ein verschriebenes `windwos` würde sonst im Moment des Klickens zu „dieses Plug-in unterstützt Ihre Plattform nicht" und ließe sich durch nichts erklären.

Eine Plattform, für die Sie nicht gebaut haben, wird beim Namen genannt statt geraten — „kein Build für `linux-arm64`; ausgeliefert sind `macos-x64`, `macos-arm64`, `windows-x64`". `runtime: "process"` ohne `entrypoints` zu erklären, oder ein System zu nennen und nichts darunter zu setzen, wird abgelehnt.

## Wie ein Skript-Plug-in aufgerufen wird

Beide Skriptlaufzeiten sind synchron — der Lua-Interpreter hat keine Coroutinen, und die JS-Engine hat keine eigene Ereignisschleife. Alles, was Zeit braucht (den Lesenden fragen, ein Modell aufrufen), würde den Editor blockieren. Ein Skript wartet daher nie: es **gibt eine Aktion zurück**, die beschreibt, was geschehen soll, der Editor tut es, und der Editor ruft das Skript mit der Antwort erneut auf.

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

Dieselbe Form in JavaScript:

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

### Die Aktionen

| Rückgabe | Was der Editor tut | Danach |
|---|---|---|
| `{ ask = "…", default = "…", choices = {…} }` | fragt die Lesenden; `choices` erscheinen als Chips zum Antippen, und was stattdessen getippt wird, gilt so, wie es dasteht | ruft `on_command` erneut auf, mit gesetztem `ctx.answer` |
| `{ ai = "…" }` | schickt Ihren Prompt an das Modell, das die Lesenden eingerichtet haben | ruft `on_result(ctx, reply)` auf |
| `{ show = "…", title = "…" }` | zeigt eine Antwort in einem kleinen Fenster, mit Kopierschaltfläche | endet; nichts wird geschrieben |
| `{ panel = "…", title = "…" }` | zeigt sie in einem Bereich neben dem Dokument | endet; nichts wird geschrieben |
| `{ pane = "…", title = "…", slot = "right"\|"bottom"\|"corner" }` | füllt einen der Bereiche um das Dokument | endet; nichts wird geschrieben |
| `{ notify = "…" }` | sagt den Lesenden eine Zeile | endet |
| `{ diff = { original = "…", result = "…" } }` | zeigt beide Texte nebeneinander | endet; nichts wird geschrieben |
| `{ replace = "…" }` | ersetzt die Auswahl | endet |
| irgendetwas anderes | nichts | endet |

**Bereiche.** Der Editor teilt einen Tab ohnehin zwischen Quelltext und Vorschau; `pane` ist das nach außen gegeben. Das Dokument behält die erste Zelle eines Zwei-mal-zwei-Rasters, die anderen drei dürfen Sie füllen — `right` daneben, `bottom` darunter, `corner` rechts unten. **Eine Zelle, um die niemand gebeten hat, wird nicht gezeichnet**, nur `corner` zu füllen hinterlässt also keine zwei leeren Streifen. Ein Platzname, den der Editor nicht kennt, wird abgelehnt statt geraten: ein Bereich, der irgendwo auftaucht, worum Sie nicht gebeten haben, und für den es keine Erklärung gibt, ist schlechter, als es gesagt zu bekommen.

**`show` oder `panel`.** Ein paar Zeilen sind eine Antwort: ein kleines Fenster ist richtig, ein Bereich dafür ist mehr Möbel als Inhalt. Ein dokumentgroßes Ergebnis ist etwas, das die Lesenden gegen das halten, was auf dem Bildschirm steht, und ein Fenster über dem Bildschirm ist der eine Ort, an den es nicht kann.

Ein Lauf ist auf acht Schritte begrenzt, ein Skript, das jede Frage mit einer weiteren beantwortet, kann die Lesenden also nicht festhalten.

**Der Prompt gehört Ihnen.** Der Editor hält die Zugangsdaten und stellt die Anfrage; er schreibt Ihren Prompt nicht um, und Ihr Skript sieht den API-Schlüssel nie. Dem Modell wird genau die Zeichenkette vorgelegt, die Sie in `ai` zurückgegeben haben.

### Was ein Skript erreichen kann

Nur dies. Kein `os`, kein `package`, kein `dofile`, kein `loadfile`, kein Dateisystem und kein Netz — ein Skript-Plug-in kommt aus dem Repository einer fremden Person und bekommt daher, was es erklärt hat, und sonst nichts.

| | |
|---|---|
| `storage.get(key)` / `storage.set(key, value)` | Ihre eigenen Einstellungen, in Ihrem eigenen Verzeichnis. Nur Zeichenketten. Braucht `storage.local` |
| `t(key)` | Ihre eigene Zeichenkette in der Sprache der Lesenden; ein unbekannter Schlüssel kommt als er selbst zurück |
| `require(name)` | eine Ihrer eigenen Dateien, aufgelöst nur innerhalb Ihres Plug-in-Verzeichnisses |
| `ctx.command` | die `id` des Menüeintrags oder Befehls, der ausgelöst hat |
| `ctx.selection` | der markierte Text, `""` wenn nichts markiert ist |
| `ctx.document` | das ganze Dokument |
| `ctx.answer` | was die Lesenden beim letzten Fragen eingegeben haben, sonst nil/undefined |

### Was dieses Lua nicht kann

Der Interpreter ist ein Lua in reinem Dart — genau deshalb braucht ein Skript-Plug-in nichts Installiertes — und er ist nicht vollständig. Diese vier scheitern alle **stillschweigend**, und das ist der teure Teil: ein Muster, das nichts findet, sieht genauso aus wie ein Dokument, in dem nichts steht.

| Statt | Nehmen Sie | Weil |
|---|---|---|
| `#someString` | `string.len(s)` | wirft `length error`. `#` auf einer *Tabelle* funktioniert, die beiden lassen sich also nicht am Gefühl unterscheiden |
| `s:match("%S")`, `%s` | Zeichen vergleichen: `s:sub(i, i) == " "` | die Klassen finden nichts, also sieht jede Zeile leer aus |
| `for l in s:gmatch("(.-)\n")` | `s:find("\n", pos, true)` und `s:sub` | gibt überhaupt nichts zurück |
| `s:gmatch("[^\n]*")` | dasselbe | kommt über eine leere Fundstelle nie hinaus |

Die Testsuite des Editors hält diese vier fest, wird der Interpreter also ersetzt, wird diese Tabelle korrigiert statt weiter in die Irre zu führen.

Die JavaScript-Laufzeit ist QuickJS und hat keine vergleichbaren Lücken, die aufzuzählen wären.

## Berechtigungen

Im Manifest erklärt, den Lesenden gezeigt und **durchgesetzt**. VS Code und IntelliJ zeigen eine Liste und vertrauen der Erweiterung dann; hier prüft niemand etwas nach, also prüft der Editor. `{ ai = ... }` ohne `ai.chat` ruft kein Modell auf — den Lesenden wird gesagt, dass das Plug-in darum nicht gebeten hat.

| Berechtigung | Erlaubt dem Plug-in |
|---|---|
| `document.read` | das offene Dokument und die Auswahl zu lesen |
| `document.write` | das offene Dokument zu ändern |
| `ui.contextMenu` | Einträge im Kontextmenü |
| `ui.menuBar` | Einträge in der Menüleiste |
| `ui.toolbar` | eine Schaltfläche in der Werkzeugleiste |
| `ui.sidebar` | einen eigenen Bereich in der Seitenleiste |
| `ui.statusBar` | einen Eintrag in der Statusleiste |
| `ui.settings` | eine eigene Einstellungsseite |
| `ui.commandPalette` | Befehle in der Befehlspalette |
| `ui.notifications` | den Lesenden etwas zu sagen |
| `ai.chat` | das eingerichtete Modell zu fragen (der Schlüssel wird nie übergeben) |
| `storage.local` | eine eigene Einstellungsdatei im eigenen Verzeichnis |
| `clipboard.read` / `clipboard.write` | die Zwischenablage |
| `workspace.read` / `workspace.write` | Dateien unter dem geöffneten Ordner |
| `network.request` | eigene HTTP-Anfragen. **Das Weiteste, worum man bitten kann**: was es lesen kann, kann es überallhin senden |

Bitten Sie um das, was Sie benutzen. Ein Plug-in, das für einen Menüeintrag um `network.request` bittet, sollten die Lesenden ablehnen.

## Beitragspunkte

```json
"menus":    [{"id": "…", "title": "…", "location": "editor.contextMenu", "when": "selection"}],
"commands": [{"id": "…", "title": "…"}],
"toolbar":  [{"id": "…", "title": "…", "icon": "…"}],
"pages":    [{"id": "…", "title": "…"}]
```

`title` darf ein Übersetzungsschlüssel sein. `location` ist ein Platz, den der Editor definiert — ein Plug-in stellt Dinge an benannte Plätze, nie an Pixelkoordinaten, und reicht dem Editor nie eigene Widgets.

`when` sagt, wann ein Menüeintrag es wert ist, angeboten zu werden: `selection` nur mit einer Auswahl, `noSelection` nur ohne, und fehlt es, dann immer. Ohne das werden alle Einträge auf einmal angeboten — „Auswahl übersetzen" ohne Auswahl und „Dokument übersetzen", während die Lesenden auf einen Absatz zeigen. Ein Wert, den der Editor nicht kennt, wird beim Installieren abgelehnt, statt still als „immer" gelesen zu werden.

## Einstellungen

Jedes Feld in `settings` wird auf der eigenen Einstellungsseite des Plug-ins zu einem echten Bedienelement, das der Editor zeichnet:

| `type` | Bedienelement |
|---|---|
| `text` | ein Textfeld |
| `password` | ein Textfeld, das seinen Inhalt nicht zeigt |
| `number` | ein numerisches Textfeld |
| `boolean` | ein Schalter; gespeichert als die Zeichenketten `"true"` / `"false"` |

Die Werte liegen in `settings.json` im eigenen Verzeichnis des Plug-ins, kein Plug-in kann also die Einstellungen eines anderen lesen oder schreiben. Was die Lesenden speichern, erreicht ein bereits laufendes Skript beim nächsten Befehl, nicht erst beim nächsten Start.

## Übersetzungen

`locales` ordnet einer Sprache Ihre eigenen Zeichenketten zu; `defaultLocale` sagt, worauf zurückgefallen wird. Lesende mit `zh_CN` bekommen `zh_CN`, falls Sie es mitgeliefert haben, dann `zh`, dann Ihre Vorgabe. Liefern Sie mit, welche Sprachen Sie wollen — das ist Ihre Tabelle, nicht die des Editors.

## Kompilierte Plug-ins (`runtime: "process"`)

Die ausführbare Datei wird als Kindprozess gestartet und spricht JSON-RPC 2.0, ein JSON-Objekt je Zeile, auf stdin/stdout. Antworten geben die numerische `id` zurück. [`packages/dart/lib`](../../packages/dart/lib) in diesem Repository setzt das für Plug-ins um, die in Dart geschrieben und mit `dart compile exe` kompiliert werden.

### Sie dürfen keinen Quelltext ausliefern, der eine Toolchain zum Laufen braucht

Das betrifft nur kompilierte Plug-ins, und besonders Dart, weil der Editor darin geschrieben ist: `entrypoint: "bin/plugin.dart"` wird beim Installieren abgelehnt. Es auszuführen bräuchte ein Dart-SDK auf der Maschine der Lesenden, das der Editor nicht installiert und nicht voraussetzen kann — und ein Release-Build hat keinen Interpreter, dem er es reichen könnte. Kompilieren Sie es (`dart compile exe`) und liefern Sie die ausführbare Datei aus.

Nichts davon gilt für ein Lua- oder JavaScript-Plug-in. Die interpretiert der Editor selbst, was ihr ganzer Sinn ist: kein Dart, keine Toolchain, kein Build.

**Warum ein Prozess und keine Bibliothek, die der Editor lädt.** Lua- und JS-Plug-ins laufen bereits im Prozess des Editors, in seinem eigenen Thread — das ist der Normalfall, und es ist sicher, weil beide interpretiert werden: ein schlechtes Skript wirft einen Fehler, den der Editor auffängt. Nativer Code hat diese Grenze nicht. Ein Thread teilt den Adressraum, also nimmt ein Speicherzugriffsfehler, ein Stapelüberlauf oder ein `abort()` irgendwo in einer geladenen `.so` den Editor mit, samt dem ungesicherten Dokument der Lesenden und ohne jede Möglichkeit zu berichten, was geschah; eine Schleife ohne Ausgang friert das Fenster ein, ohne dass man sie unterbrechen könnte; und Entladen ist unzuverlässig, ein Plug-in zu deaktivieren würde es also nicht wirklich anhalten. Ein eigener Prozess gibt alle drei zurück — er darf abstürzen, hängen oder nach einer Zeitüberschreitung getötet werden, und der Editor überlebt und sagt, welches Plug-in es war. (Für Dart gibt es ohnehin nichts zu wählen: `dart compile` kennt `exe`, `aot-snapshot`, `js`, `wasm` und die Snapshot-Formate. Einen Unterbefehl, der eine von C aufrufbare `.so` oder `.dll` erzeugt, gibt es **nicht**.)

- **Benutzen Sie `serve()`, dann sind die nächsten zwei Punkte bereits erledigt.** Ein ganzes kompiliertes Plug-in:

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

- **Laufen Sie nicht, wenn der Editor Sie nicht gestartet hat.** Der Editor erzeugt für jeden Start ein Token und übergibt es in der Umgebungsvariablen `MARKTEXT_PLUS_PLUGIN_TOKEN`; ohne es gibt `serve()` eine Zeile aus, die sagt, was das hier ist, und endet mit 1. Ein Token für einen Start lässt sich von niemandem tippen, dem es nicht gegeben wurde, und es reist in der Umgebung statt in argv, das alles lesen kann, was `ps` ausführen darf.

  **Was das tut und was nicht.** Kein Programm kann verhindern, dass eine Datei auf der eigenen Platte ausgeführt wird — ein Doppelklick auf Ihre ausführbare Datei startet immer einen Prozess. Was das Token unfälschbar macht, ist Ihre Antwort auf „hat der Editor mich gestartet", damit der Prozess startet, sagt was er ist und endet, statt auf stdin zu sitzen und wie ein hängendes Programm auszusehen. Ein Plug-in, das die Prüfung auslässt, ist ein Plug-in, das niemand geschützt hat; deshalb steht die Prüfung in `serve()` des SDK und nicht bloß in diesem Absatz. Skript-Plug-ins bekommen das umsonst: eine `.lua`- oder `.js`-Datei interpretiert der Editor, ein Doppelklick öffnet schlimmstenfalls einen Texteditor.

- **Beenden Sie, wenn stdin das Ende erreicht.** So wird Ihnen gesagt, dass Sie aufhören sollen, und so geschieht es von selbst, wenn der Editor stirbt — `serve()` kehrt dann zurück. Der Editor schreibt außerdem auf, welche Prozesse er gestartet hat, und räumt beim nächsten Start alle noch laufenden weg — aber nur die, die er gestartet hat. **Prozesse, die *Sie* starten, müssen Sie selbst aufräumen.**
- Lassen Sie stdout den Protokollantworten; Diagnosen gehören auf stderr.
- Anfragen sind durch eine Zeitüberschreitung begrenzt, und eine Zeitüberschreitung tötet nur Ihren Prozess.
- Behandeln Sie alles, was der Host schickt, als nicht vertrauenswürdig, und prüfen Sie es.

## Kompatibilität

Ein Plug-in ist eine Datei auf der Maschine einer anderen Person, die dieser Editor liest. Sie kaputtzumachen ist kein Build-Fehler, den hier jemand sieht — es ist ein Plug-in, das für seine Lesenden aufhört zu funktionieren. Deshalb:

**`minAppVersion` wird durchgesetzt.** Nennen Sie den ältesten Editor, mit dem Ihr Plug-in läuft, und der Editor hält sich daran: ein älterer verweigert die Installation und verweigert auch, ein bereits installiertes auszuführen, und nennt dabei die gewünschte und die vorhandene Version. Früher wurde das Feld gelesen und ignoriert, was schlechter ist, als es gar nicht zu haben.

**Was der Editor nicht ohne Ankündigung wegnimmt.** Jeder Berechtigungsname, jeder `runtime`-Wert, jede Aktion, die ein Skript zurückgeben kann, jedes Feld in `ctx` sowie `storage`, `t` und `require` sind durch einen Test im Quelltext des Editors festgehalten. Zu diesen Listen etwas **hinzuzufügen** ist frei; etwas **zu entfernen oder umzubenennen** lässt jenen Test fehlschlagen und kann daher nicht aus Versehen geschehen.

**Solange dies 0.x ist**, bleibt eine absichtliche brechende Änderung möglich, und sie steht dann im Änderungsprotokoll, mitsamt dem, was zu tun ist. Wenn Manifest und Protokoll lange genug unangetastet geblieben sind, um Vertrauen zu verdienen, wird dies 1.0, und damit hört das auf: danach funktioniert weiter, was ein Plug-in heute schreiben kann, und Dinge verschwinden erst, nachdem sie in einer Version, die sie noch unterstützt, als veraltet angekündigt wurden.

**Wo ein Plug-in auf sich gestellt ist.** Der Editor kann weder das Verhalten Ihres Prompts zusagen noch das Modell, das die Lesenden eingerichtet haben, noch die eigenen Kindprozesse eines `process`-Plug-ins. Er kann auch niemanden davon abhalten, Ihre ausführbare Datei von Hand zu starten — was er stattdessen tut, steht oben beim Start-Token.

## Sicherheitsregeln

- Schreiben Sie nie einen API-Schlüssel in das Plug-in-Verzeichnis oder das Manifest.
- Auf stdout gehört nichts außer Protokollnachrichten.
- Halten Sie die Arbeit begrenzt; der Editor erzwingt Zeitüberschreitungen und Schrittgrenzen.
- Ein Plug-in-ZIP mit einem Eintrag, der aus dem Verzeichnis hinausführt, wird beim Installieren abgelehnt.

Das SDK steht unter der MIT-Lizenz.
