# SDK per estensioni di MarkText Plus

Applicazione principale: [MarkText Plus](https://github.com/SugarFatFree/marktext-plus)

[English](../../README.md) | [简体中文](README_zh-CN.md) | [日本語](README_ja-JP.md) | [한국어](README_ko-KR.md) | [Deutsch](README_de-DE.md) | [Français](README_fr-FR.md) | Italiano | [Русский](README_ru-RU.md) | [Español](README_es-ES.md) | [Português](README_pt-PT.md) | [العربية](README_ar-SA.md) | [Português (Brasil)](README_pt-BR.md)

Come si scrive un'estensione per MarkText Plus, e che cosa l'editor le lascia e non le lascia fare.

**Prerelease.** Questo SDK resta a 0.x finché il sistema di estensioni non si assesta, e il manifest e il protocollo descritti qui possono ancora cambiare fra una versione e l'altra. Che cosa significhi oggi, e che cosa significherà poi, sta in [Compatibilità](#compatibilità) più sotto.

## Prima si sceglie il runtime

Un'estensione gira su macchine dove c'è l'editor e nient'altro — niente SDK di Dart, niente Node, niente Python. Questo solo fatto decide quasi tutto ciò che segue.

| `runtime` | Che cosa distribuite | Gira su | Quando usarlo |
|---|---|---|---|
| `lua` | un file `.lua` | ogni piattaforma, senza build | il caso normale: comandi di menu, domande, lavoro sul testo |
| `js` | un file `.js` | ogni piattaforma, senza build | lo stesso, se preferite scrivere JavaScript |
| `process` | **un eseguibile per piattaforma** | solo quelle per cui avete compilato | vi serve una vera toolchain, delle librerie, o lavoro che dura ‡ |
| `data` | nessun codice | ovunque | temi, snippet, dizionari |

`‡` — l'editor **non avvia ancora** un plugin compilato. Si installa, e lanciare
uno dei suoi comandi lo dice chiaramente:
*«has no script to run: its runtime is process»*. Il protocollo qui sotto è quello
che parlerà, e la parte che lo parla dentro l'editor è scritta e testata; solo che
nulla le passa un comando. Scritto qui perché la serata spesa a compilare sia una
decisione e non una sorpresa.

Cominciate da `lua` o `js`. Un'estensione così è **un file di script e un `manifest.json`, nient'altro** — nessuna build, nessun compilatore, nessuna seconda lingua, e quei due file girano tali e quali su Windows, macOS e Linux. Uno script non può nemmeno far cadere l'editor.

Prendete `process` solo se uno script davvero non basta.

L'estensione di traduzione IA pubblicata accanto a questo SDK è tutto ciò che un'estensione Lua è sul disco:

```
manifest.json
plugin.lua
README.md
CHANGELOG.md
LICENSE
```

Uno script, un manifest, e tre file di documentazione. **Di Dart, nemmeno l'ombra.**

## Che cosa c'è in questo repository

Una directory per linguaggio, ciascuna un'estensione completa da copiare:

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

Prendono il nome dal **linguaggio**, perché è quello che scegliete. `runtime` nel manifest dice come gira — `lua`, `js`, `process` — e `packages/dart` è un'estensione `process`: Dart è soltanto il linguaggio in cui è scritto il suo esempio.

**Un'estensione `process` può essere scritta in qualunque cosa si compili in un eseguibile.** L'editor avvia un programma e ci parla in JSON-RPC su stdin e stdout; non viene mai a sapere che cosa abbia prodotto quel programma. Go, Rust, C++, C#, un Python collegato staticamente — vanno tutti bene, e nessuno ha bisogno di questo repository oltre al protocollo:

- un oggetto JSON per riga, su stdin e stdout;
- le risposte restituiscono l'`id` numerico;
- terminare quando stdin arriva alla fine;
- terminare se `MARKTEXT_PLUS_PLUGIN_TOKEN` non è nell'ambiente, così che un eseguibile aperto con un doppio clic dica che cos'è invece di aspettare.

Questo è tutto il contratto. Eccolo in Python, senza nulla preso da questo repository — risponde all'editor e si rifiuta di girare se nessuno l'ha avviato:

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

[`packages/dart/lib`](../../packages/dart/lib) sono le stesse quattro regole con i bordi curati: input malformato, un metodo sconosciuto, un errore dentro un gestore che non fa finire l'estensione intera. Dart sta qui perché l'editor è scritto in Dart e `dart compile exe` era la strada più corta per avere un esempio funzionante. Non è un requisito e non è una raccomandazione: riscrivere quattro regole nel linguaggio che già conoscete è di solito più semplice che aggiungere una toolchain Dart alla vostra build.

I tre punti d'ingresso fanno la stessa cosa: caricano l'API e la chiamano.

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

`lua` e `js` sono deliberatamente **la stessa estensione scritta due volte** — stesso manifest, stessi permessi, stesso comportamento — così che le due si possano leggere una accanto all'altra. **Copiatene una.** Un'estensione dichiara un `runtime` e un punto d'ingresso; una directory che le contiene tutte e tre sono tre estensioni che indossano un manifest solo.

### Perché il modulo API sta dentro un esempio

Perché viene distribuito con la vostra estensione. `lib/marktext-plus.lua` non è una dipendenza da indicare — è un file che copiate insieme al resto e che poi è vostro. Copiare `packages/lua` per intero vi dà un'estensione funzionante, API compresa; non c'è un altro posto da cui prenderla, né un numero di versione da inseguire.

### Che cos'è il modulo API

Per uno script è comune Lua o JavaScript, **distribuito con la vostra estensione**. L'editor inietta `storage`, `t` e `require` come globali prima che il vostro file venga letto; il modulo li raccoglie sotto un nome solo e aggiunge un costruttore per ogni azione, così che un'estensione si legga `sdk.show(text, title)` e non come una tabella di cui nessuno controlla l'ortografia. Potete modificarlo, o non usarlo affatto — restituire la tabella nuda funziona esattamente allo stesso modo.

Per `packages/dart` è una libreria vera, compilata dentro il vostro eseguibile, e porta ciò di cui uno script non ha bisogno: il ciclo JSON-RPC, il controllo all'avvio, la chiusura. Un'estensione a processo sta dall'altra parte di una pipe.

## Un'estensione può stare in più file

`require` carica uno dei **vostri** file — il modulo API qui sopra viene caricato esattamente così, e lo stesso vale per qualunque altra cosa mettiate accanto:

```lua
local helpers = require("lib.helpers")   -- lib/helpers.lua, returns its table
```

```js
const helpers = require("lib/helpers");  // lib/helpers.js, sets module.exports
```

Caricato una volta sola, per quante volte lo si richieda. Il nome è un nome, non un percorso: si risolve dentro la directory della vostra estensione e da nessun'altra parte. Spezzare un'estensione grande — o distribuirla con una libreria scritta da qualcun altro — non vi costa quindi alcun accesso in più al resto del disco. Un nome con un separatore, un `..` o un punto iniziale viene rifiutato prima che si legga alcunché, e il file risolto viene poi ricontrollato per accertare che stia dentro la vostra directory: è così che si prende un collegamento simbolico che punta fuori.

## Provare un'estensione prima di distribuirla

Un'estensione Lua o JavaScript la interpreta l'editor, quindi la prova onesta è installarla — **Estensioni → Installa da ZIP**. Una compilata si può controllare prima:

```
cd packages/dart && dart compile exe plugin.dart -o bin/linux/plugin
echo | ./bin/linux/plugin       # should refuse: it was not started by the editor
```

è tutta la verifica di un'estensione compilata: si compila, e si rifiuta di girare quando nessuno le ha dato un token di avvio.

### È stata installata e non compare

Un'estensione il cui `manifest.json` non può essere letto non compare nell'elenco, e ciò che manca dall'elenco somiglia esattamente a ciò che non è mai stato installato — quindi la mossa successiva è installarla di nuovo, e di nuovo non compare nulla.

L'editor la elenca a parte, sotto quelle che si sono caricate, **con il motivo**: la chiave che non ha saputo leggere e che cosa si aspettava di trovarci. Quella riga ha un proprio pulsante di eliminazione, perché un'estensione che non si carica non ha una pagina da cui disinstallarla.

Il motivo è quasi sempre uno di questi:

- `runtime` deve essere `lua`, `js`, `process` o `data`
- `lua` e `js` richiedono `entrypoint`; `process` richiede `entrypoints`, un percorso per ogni sistema operativo
- nessun punto d'ingresso può essere un file `.dart`. L'editor non include un SDK Dart e non può presumere che il lettore ne abbia uno: compilala e distribuisci l'eseguibile con `runtime: "process"`

## Manifest

`manifest.json` sta nella radice dell'estensione. L'editor lo legge **senza eseguire nulla**. Vedete [`schema/manifest.schema.json`](../../schema/manifest.schema.json).

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

### Eseguibili per piattaforma

Un'estensione `process` non usa `entrypoint`. Nomina i suoi eseguibili **per sistema operativo**, con l'architettura sotto e soltanto dove conta:

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

Il sistema è la parte a cui dovete sempre rispondere — una build Windows è un file diverso da una build Linux. L'architettura spesso no, perciò è facoltativa:

- **Un percorso per l'intero sistema.** `macos` qui sopra è un binario universale: un file che contiene entrambe le architetture, come le build macOS si distribuiscono di solito. Scrivere due volte lo stesso percorso per dirlo sarebbe peggio.
- **Una tabella di architetture.** `windows` qui sopra distribuisce una build separata per ciascuna e non supporta altro.
- **Un `default` condiviso più una specializzazione.** `linux` qui sopra esegue `bin/linux/plugin` dappertutto tranne su arm64, che ha la sua. Vince quella specializzata.

I sistemi sono `windows`, `macos` e `linux`; le architetture, `x64` e `arm64`. **Qualsiasi altro nome viene rifiutato all'installazione anziché saltato** — altrimenti un `windwos` scritto male diventerebbe, nel momento del clic, «questa estensione non supporta la vostra piattaforma», e non ci sarebbe modo di spiegarlo.

Una piattaforma per cui non avete compilato viene nominata invece che indovinata — «nessuna build per `linux-arm64`; ci sono `macos-x64`, `macos-arm64`, `windows-x64`». Dichiarare `runtime: "process"` senza `entrypoints`, o nominare un sistema senza nulla sotto, viene rifiutato.

## Come viene chiamata un'estensione script

Entrambi i runtime di script sono sincroni — l'interprete Lua non ha coroutine, e il motore JS non ha un proprio ciclo di eventi. Tutto ciò che richiede tempo (chiedere a chi legge, chiamare un modello) bloccherebbe l'editor. Perciò uno script non aspetta mai: **restituisce un'azione** che descrive che cosa vuole sia fatto, l'editor lo fa, e richiama lo script con la risposta.

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

La stessa forma in JavaScript:

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

### Un pannello può essere interrogato di nuovo

Un comando avviato da un pannello può essere eseguito una seconda volta: chi
legge chiede di cambiare la risposta invece di ridescrivere tutto. L'editor lo
dice nei campi che il vostro script già conosce:

- `ctx.selection` è **la vostra ultima risposta**, perché una richiesta
  successiva riguarda la bozza che si ha davanti, non il documento.
- `ctx.answer` è ciò che è stato chiesto stavolta — lo stesso campo in cui
  arriva la risposta al vostro `ask`.

Un comando che legge la selezione come «la parte su cui lavorare» non ha
bisogno di nulla di nuovo. Uno che ignora `ctx.selection` riscriverà ogni volta
il documento da capo, che non è ciò che è stato chiesto.

Il riquadro compare solo se il comando ha chiesto qualcosa all'inizio, perché è
lì che arriva la richiesta successiva; un comando che non chiede nulla viene
eseguito una volta. Ciò che `apply` sostituisce resta quanto indicato dalla
prima risposta: una seconda bozza più breve sostituisce comunque il paragrafo
da cui è nata la prima, non la bozza da cui proviene, che nel documento non
c'è.

### Le azioni

| Ritorno | Che cosa fa l'editor | Poi |
|---|---|---|
| `{ ask = "…", default = "…", choices = {…} }` | chiede a chi legge; le `choices` compaiono come pastiglie da premere, e ciò che viene digitato al loro posto è preso così com'è | richiama `on_command` con `ctx.answer` valorizzato |
| `{ ai = "…" }` | manda il vostro prompt al modello che chi legge ha configurato | chiama `on_result(ctx, reply)` |
| `{ show = "…", title = "…" }` | mostra una risposta in una finestrella, con un pulsante per copiare | finisce; non scrive nulla |
| `{ panel = "…", title = "…" }` | la mostra in un pannello accanto al documento | finisce; non scrive nulla |
| `{ pane = "…", title = "…", slot = "right"\|"bottom"\|"corner", apply = true, replaces = "…" }` | riempie uno dei riquadri attorno al documento | finisce; non scrive nulla |
| `{ pane = "<html>…", title = "…", as = "web" }` | disegna una tua pagina HTML in quel riquadro, con il motore web del sistema. Richiede `ui.webview` | stops |
| `{ notify = "…" }` | dice una riga a chi legge | finisce |
| `{ diff = { original = "…", result = "…" } }` | mostra i due testi affiancati | finisce; non scrive nulla |
| `{ replace = "…" }` | sostituisce la selezione | finisce |
| `{ ui = <nodo>, title = "…" }` | disegna la vostra interfaccia — vedi sotto | chiama `on_event(ctx, id, values)` quando chi legge la usa |
| qualunque altra cosa | niente | finisce |

### Disegnare la propria interfaccia

`ui` porta un albero che l'editor disegna con i propri componenti. I nodi sono tabelle con una sola chiave:

```lua
return sdk.ui({ column = {
  { text = sdk.t("ask.instruction"), emphasis = true },
  { input = { id = "brief", multiline = true, placeholder = "…" } },
  { chips = { id = "idea", options = prompts.writing_ideas(sdk.t) } },
  { row = {
    { spacer = true },
    { button = { id = "go", label = sdk.t("action.write"), primary = true } },
  }},
}}, sdk.t("menu.write"))
```

| Nodo | Campi |
|---|---|
| `text` | la stringa stessa; `emphasis = true` la disegna come titolo |
| `input` | `id` (obbligatorio), `value`, `placeholder`, `multiline` |
| `chips` | `id` (obbligatorio), `options` — un elenco di stringhe |
| `button` | `id` (obbligatorio), `label`, `primary` |
| `row` / `column` | un elenco di nodi |
| `select` | `id` (obbligatorio), `options`, `value` — un menù a tendina, quando sono troppe per i chip |
| `checkbox` | `id` (obbligatorio), `label`, `value`; il valore arriva come `"true"` o `"false"` |
| `markdown` | Markdown, disegnato dal renderer dell'editor: la vostra risposta somiglia al documento di cui parla |
| `image` | `source` (obbligatorio), `height` — vedi sotto |
| `spacer` | spazio vuoto; in una riga spinge il seguito all'estremità |

Premere un pulsante o scegliere un chip chiama `on_event(ctx, id, values)`, dove `id` è quello di quel nodo e `values` contiene **tutti gli input dell'albero** per id. Non dovete ricordare il modulo disegnato un passo prima: ce l'ha l'editor.

Non è HTML, ed è proprio questo il punto: sono i componenti dell'editor stesso. Non costano nulla all'avvio, seguono il tema di chi legge senza che l'estensione sappia quale sia, e non possono disegnare fuori dal contenitore che hanno ricevuto.

**Immagini.** `source` è una di tre cose:

- una URI `data:` — decodificata sul posto, nulla lascia la macchina;
- un percorso relativo alla cartella della vostra estensione — uno assoluto viene rifiutato, perché leggere file dal disco di chi legge è compito di `workspace.read`;
- un URL `http(s)` — **lo prende l'editor**, non la vostra estensione: così segue il proxy di sistema e finisce nel registro della vostra estensione con host, stato, dimensione e tempo. Richiede `network.request`.

Quest'ultima riga è voluta. Potete uscire in rete; chi legge può sapere dove. **Un permesso che nessuno può verificare dopo è una promessa, non un permesso.**

**Un nodo scritto male fa rifiutare l'intero albero**, con un errore che vedrete, invece di non disegnare nulla in silenzio. Lo stesso per un albero più profondo di 12 livelli o più grande di 500 nodi: mezzo modulo è peggio di nessuno, perché chi legge compila quello che vede e poi preme un pulsante mai disegnato.

**Cosa va chiesto.** Questi quattro vengono rifiutati se il manifesto non
dichiara il permesso:

| Restituisce | Richiede |
|---|---|
| `ai` | `ai.chat` |
| `replace` | `document.write` |
| `notify` | `ui.notifications` |
| `pane`, `panel` | `ui.sidebar` |
| `pane` + `as = "web"` | `ui.webview`, che porta con sé `ui.sidebar` e `network.request` |

`ask`, `show` e `diff` non chiedono nulla. Rispondere a chi ha appena lanciato il
comando è ciò per cui esiste un'estensione; richiedere un permesso significherebbe
che ogni estensione lo dichiara — e uno che hanno tutti non dice nulla al lettore.

**La tua pagina.** `as = "web"` disegna il testo del riquadro come una pagina HTML
invece che come parole. È l'unica via a un'interfaccia che l'editor non ha
progettato, ed è quella costosa: tutto il resto di ciò che puoi restituire viene
*descritto* all'editor — nodi con un nome, o testo — e disegnato con i suoi
widget. Per questo non costa nulla all'avvio e segue il tema di chi legge senza
che tu sappia quale sia.

Il motore è quello del sistema — WebView2 su Windows, WKWebView su macOS — e
**non un browser distribuito con l'editor**. Il download e la memoria restano
dov'erano, e le impostazioni proxy del lettore valgono senza che nessuno le
sistemi. E **nulla viene creato finché un plugin non lo chiede**: chi non apre mai
un plugin così non paga mai un motore.

Dove va la pagina finisce nel log del plugin, che è ciò che `ui.webview` promette.
**Manda HTML, non un indirizzo**: quello che disegni è tuo, e una pagina che vuole
qualcosa da un server può chiederlo da sé.

**Non tutte le macchine ne hanno uno.** Un Linux senza un motore web utilizzabile
riceve una frase che nomina il tuo plugin — non un riquadro vuoto, che sembrerebbe
un plugin rotto. Non fare della pagina web l'unico modo di usare il tuo plugin, a
meno di voler lasciare fuori quei lettori.

**I riquadri.** L'editor divide già una scheda fra sorgente e anteprima; `pane` è quella divisione, messa a tua disposizione. Al massimo quattro celle, e **le due metà della vista divisa sono due di esse** — è da lì che viene tutto questo, quindi un documento in vista divisa è già due celle prima che tu riempia qualcosa.

La forma segue quante celle ci sono, ed è simmetrica a ogni passo:

| Celle | Disposizione |
|---|---|
| una | il documento ha l'intera scheda |
| due | affiancate, metà ciascuna |
| tre | una metà divisa, l'altra intera |
| quattro | in alto a sinistra, in alto a destra, in basso a sinistra, in basso a destra |

Con tre celle e un documento non diviso, **scegli tu quale metà viene divisa**: riempire `right` mette un riquadro accanto al documento, così la parte alta si divide e l'altro riquadro prende tutta la riga bassa; riempire solo `bottom` e `corner` lascia al documento tutta la riga alta e divide la bassa fra i due. Chi legge può poi spostarlo dalla barra del titolo del riquadro — quale metà è divisa è una vista degli stessi riquadri, non una decisione che continui a prendere tu.

I divisori si trascinano, come quello fra sorgente e anteprima.

I nomi `right`, `bottom`, `corner` sono anche l'indirizzo con cui ritrovi un riquadro più tardi, per aggiungervi o sostituirne il contenuto. Un riquadro resta un riquadro: riempire solo `corner` ti dà un riquadro accanto al documento, non un angolo con due celle vuote davanti. Il verso, però, lo decide il nome — riempire solo `bottom` mette il riquadro sotto il documento, qualsiasi altra casella lo mette accanto —, perché una riscrittura del paragrafo che stai leggendo si legge meglio sotto: stessa larghezza di riga, e l'occhio scende invece di attraversare. Il lettore può ribaltarlo dalla barra del titolo del riquadro. Un nome che l'editor non conosce viene rifiutato anziché indovinato: un riquadro che compare dove non l'hai chiesto, senza modo di sapere perché, è peggio di un rifiuto.

**Un riquadro appartiene alla scheda in cui è stato aperto.** Cambiare scheda lo toglie dallo schermo, chiudere la scheda lo chiude con essa, e tornando indietro ricompare.

**Offrirsi di riscriverlo nel documento.** `apply` mette sul riquadro un pulsante Applica, che scrive ciò che contiene nel documento; `replaces` dice che cosa sostituisce — vuoto significa l'intero documento. Ciò che un modello restituisce merita di essere letto prima di finire in quello che chi legge stava scrivendo: una riscrittura viene quindi mostrata prima e scritta quando lo dice, passando per la cronologia dell'editor, così un annulla la riporta indietro. Che cosa viene sostituito è fissato quando il tuo comando è stato eseguito, non quando si preme il pulsante: una selezione che nel frattempo si è spostata non manda il testo in un posto qualsiasi. Richiede `document.write`, che l'editor verifica al pulsante e non sulla tua parola.

**Dì che stai lavorando prima di cominciare.** Un'azione di riquadro viene letta prima di una `ai`, quindi restituirle entrambe significa «metti su questo, poi vai a chiedere» — e un riquadro dal testo vuoto con una richiesta dietro è esattamente ciò che l'editor disegna come «in corso». Finché non arriva il primo blocco lo dice dove andrà il testo; dopo si sposta nella barra del titolo, così l'avanzamento non sta mai sopra ciò che è arrivato. Restituire il solo `ai` lascia lo schermo immutato per i secondi che il modello impiega, e si legge come una voce di menu che non ha fatto nulla.

Chiudere un riquadro è il modo in cui chi legge ti ferma. Aggiungere a uno che ha chiuso viene rifiutato, anziché rimetterlo lì un blocco alla volta.

**`show` o `panel`.** Poche righe sono una risposta: una finestrella va bene, e un pannello per quelle è più mobilio che contenuto. Un risultato grande quanto un documento è ciò che chi legge tiene accanto a quello che ha sullo schermo, e una finestra sopra lo schermo è l'unico posto dove non può stare.

Un'esecuzione è limitata a otto domande, così uno script che risponde a ogni domanda con un'altra non può trattenere chi legge.

**Il prompt è vostro.** L'editor tiene le credenziali e fa la richiesta; non riscrive il vostro prompt, e il vostro script non vede mai la chiave API. Al modello viene sottoposta esattamente la stringa che avete restituito in `ai`.

### Che cosa può raggiungere uno script

Solo questo. Niente `os`, niente `package`, niente `dofile`, niente `loadfile`, nessun file system e nessuna rete — un'estensione script viene dal repository di uno sconosciuto, e riceve ciò che ha dichiarato e nient'altro.

| | |
|---|---|
| `storage.get(key)` / `storage.set(key, value)` | le vostre impostazioni, nella vostra directory. Solo stringhe. Richiede `storage.local` |
| `t(key)` | la vostra stringa nella lingua di chi legge; una chiave sconosciuta torna com'è |
| `require(name)` | uno dei vostri file, risolto solo dentro la directory della vostra estensione |
| `ctx.command` | l'`id` della voce di menu o del comando che è scattato |
| `ctx.selection` | il testo selezionato, `""` quando non c'è nulla di selezionato |
| `ctx.document` | l'intero documento |
| `ctx.answer` | ciò che chi legge ha digitato l'ultima volta che avete chiesto, altrimenti nil/undefined |
| `ctx.view` | come chi legge sta guardando il documento: `source`, `preview` o `split` |

### Che cosa questo Lua non fa

L'interprete è un Lua scritto interamente in Dart — è proprio per questo che un'estensione script non richiede nulla di installato — e non è completo. Questi quattro punti falliscono tutti **in silenzio**, ed è lì che si perde tempo: un pattern che non trova nulla è identico a un documento che non contiene nulla.

| Invece di | Usate | Perché |
|---|---|---|
| `#someString` | `string.len(s)` | solleva `length error`. `#` su una *tabella* funziona, quindi le due non si distinguono a naso |
| `s:match("%S")`, `%s` | confrontare i caratteri: `s:sub(i, i) == " "` | le classi non trovano nulla, e ogni riga sembra vuota |
| `for l in s:gmatch("(.-)\n")` | `s:find("\n", pos, true)` e `s:sub` | non restituisce proprio niente |
| `s:gmatch("[^\n]*")` | lo stesso | non supera mai una corrispondenza vuota |

| un `return` senza valore dentro una funzione annidata | `return nil` | viene ignorato, e le righe successive vengono eseguite |

**L'ultimo merita più di una riga.** `if not ok then return end` è il modo in cui ogni programmatore Lua scrive una guardia, e dentro una funzione annidata non protegge nulla: le righe che doveva saltare vengono eseguite lo stesso. La validazione passa, il caso vuoto è «gestito», e la gestione non avviene.

Dentro `while true do ... end` è peggio. Il ciclo non ha via d'uscita, e quello che il lettore vede è un editor che ha smesso di rispondere.

La correzione è una parola — scrivi `return nil`. È Lua ordinario, e continuerà a funzionare il giorno in cui l'interprete sarà corretto.

La suite di test dell'editor fissa questi punti: se l'interprete viene sostituito, questa tabella verrà corretta invece di restare a trarre in inganno. Il comportamento del `return` senza valore è fissato da un test che afferma che è **rotto**: il giorno in cui quel test fallirà sarà il giorno in cui l'aggiramento potrà sparire.

Il runtime JavaScript è QuickJS e non ha lacune paragonabili che valga la pena elencare.

## Permessi

Dichiarati nel manifest, mostrati a chi legge, e **applicati**. VS Code e IntelliJ mostrano un elenco di permessi e poi si fidano dell'estensione; qui nessuno controlla niente, quindi controlla l'editor. Restituire `{ ai = ... }` senza `ai.chat` non chiama alcun modello — a chi legge viene detto che l'estensione non l'ha chiesto.

| Permesso | Consente all'estensione di |
|---|---|
| `document.read` | leggere il documento aperto e la selezione |
| `document.write` | modificare il documento aperto |
| `ui.contextMenu` | aggiungere voci al menu contestuale |
| `ui.menuBar` | aggiungere voci alla barra dei menu |
| `ui.toolbar` | aggiungere un pulsante alla barra strumenti † |
| `ui.sidebar` | aggiungere un pannello alla barra laterale |
| `ui.statusBar` | aggiungere una voce alla barra di stato † |
| `ui.settings` | avere una propria pagina di impostazioni |
| `ui.commandPalette` | aggiungere comandi alla palette † |
| `ui.notifications` | dire qualcosa a chi legge |
| `ai.chat` | interrogare il modello configurato (la chiave non passa mai) |
| `storage.local` | tenere il proprio file di impostazioni nella propria directory |
| `clipboard.read` / `clipboard.write` | gli appunti † |
| `workspace.read` / `workspace.write` | i file sotto la cartella aperta da chi legge † |
| `network.request` | fare richieste HTTP proprie. **La più ampia che si possa chiedere**: tutto ciò che può leggere, può mandarlo ovunque |
| `ui.webview` | aprire la propria pagina web dentro l'editor. **Si porta dietro `network.request`**, e chi legge lo viene a sapere: una pagina in una vista web va a prendersi quel che vuole |

`†` — il permesso esiste davvero ed è mostrato al lettore, ma **dietro non c'è
ancora nulla**: non esiste una barra degli strumenti, una barra di stato o una
tavolozza dei comandi a cui un plugin possa aggiungere qualcosa, né appunti o
spazio di lavoro che uno script possa raggiungere. Dichiararlo oggi non dà nulla
al plugin. Restano elencati perché fanno parte del manifest, e saranno onorati
quando la capacità arriverà.

Chiedete quello che usate. Un'estensione che chiede `network.request` per aggiungere una voce di menu è un'estensione che chi legge dovrebbe rifiutare.

## Punti di contributo

```json
"menus":    [{"id": "…", "title": "…", "location": "editor.contextMenu", "when": "selection"}],
"commands": [{"id": "…", "title": "…"}],
"panels":   [{"id": "…", "title": "…", "icon": "…"}],
"toolbar":  [{"id": "…", "title": "…", "icon": "…"}],
"pages":    [{"id": "…", "title": "…"}]
```

**`toolbar` e `pages` sono gli ultimi due di proposito: nulla li disegna ancora.**
Un pulsante della barra strumenti dichiarato qui non compare, e `pages` viene letto
e poi mai più guardato — la pagina di impostazioni di un plugin viene da `settings`
più sotto, e quella viene disegnata. Entrambi restano nel manifest perché ne fanno
parte e saranno onorati quando la capacità arriverà, come i permessi `†` sopra.
I tre che li precedono sono disegnati oggi.

`title` può essere una chiave di traduzione. `location` è un posto che definisce l'editor — un'estensione mette cose in posti con un nome, mai a coordinate in pixel, e non consegna mai all'editor widget propri.

`panels` mette un'icona nella barra laterale di destra; premerla apre un cassetto riempito eseguendo il vostro comando con lo stesso `id`. Richiede `ui.sidebar`, e richiede un'`icon`, perché la barra è una fila di icone e una voce senza nulla da disegnare sarebbe un vuoto che apre qualcosa. Se nessuna estensione contribuisce un pannello, la fila non c'è affatto — una striscia di icone senza icone è larghezza tolta al documento per niente.

Un pannello chiede nel proprio cassetto: un comando che restituisce `ask` mette lì la domanda — il testo, le `choices` che hai indicato e una casella che contiene già la risposta della volta scorsa — e la risposta arriva nello stesso cassetto. Prima la domanda veniva posta nella scheda fluttuante mentre la risposta atterrava nel cassetto: un solo scambio in due posti. Chiudere il cassetto è il modo in cui il lettore rifiuta. Un comando avviato da un menu continua a chiedere nella scheda, non avendo un posto proprio.

`when` dice quando una voce di menu vale la pena di essere offerta: `selection` solo con una selezione, `noSelection` solo senza, e la sua assenza significa sempre. Senza, tutte le voci vengono offerte insieme — «Traduci la selezione» senza nulla di selezionato, e «Traduci il documento» mentre chi legge sta indicando un paragrafo. Un valore che l'editor non conosce viene rifiutato all'installazione invece di essere letto in silenzio come «sempre».

## Impostazioni

Ogni campo in `settings` diventa un vero controllo nella pagina di impostazioni dell'estensione, disegnato dall'editor:

| `type` | Controllo |
|---|---|
| `text` | una casella di testo |
| `password` | una casella di testo che non mostra il contenuto |
| `number` | una casella di testo numerica |
| `boolean` | un interruttore; salvato come le stringhe `"true"` / `"false"` |

I valori stanno in `settings.json` nella directory propria dell'estensione, quindi nessuna estensione può leggere o scrivere le impostazioni di un'altra. Ciò che chi legge salva raggiunge uno script già in esecuzione al comando successivo, non al prossimo avvio.

## Traduzioni

`locales` associa a una lingua le vostre stringhe; `defaultLocale` dice su che cosa ripiegare. Chi legge in `zh_CN` ottiene `zh_CN` se l'avete fornito, poi `zh`, poi la vostra lingua predefinita. Fornite le lingue che volete — è la vostra tabella, non quella dell'editor.

## Estensioni compilate (`runtime: "process"`)

**L'editor non ne avvia ancora nessuno** — vedi `‡` più in alto. Quel che segue è
il protocollo che parlerà, e la metà che sta nell'editor è scritta: un plugin
compilato si installa, e lanciare un suo comando dice che non ha script da eseguire.
Tutto in questa sezione descrive il lato del plugin.

L'eseguibile viene avviato come processo figlio e parla JSON-RPC 2.0, un oggetto JSON per riga, su stdin/stdout. Le risposte restituiscono l'`id` numerico. [`packages/dart/lib`](../../packages/dart/lib), in questo repository, lo implementa per estensioni scritte in Dart e compilate con `dart compile exe`.

### Non potete distribuire sorgenti che per girare richiedono una toolchain

Riguarda solo le estensioni compilate, e Dart in particolare, perché l'editor è scritto in Dart: `entrypoint: "bin/plugin.dart"` viene rifiutato all'installazione. Eseguirlo richiederebbe un SDK di Dart sulla macchina di chi legge, che l'editor non installa e non può dare per scontato — e una build di release non ha alcun interprete a cui consegnarlo. Compilatelo (`dart compile exe`) e distribuite l'eseguibile.

Niente di tutto questo vale per un'estensione Lua o JavaScript. Quelle le interpreta l'editor stesso, ed è tutto il loro senso: niente Dart, niente toolchain, niente build.

**Perché un processo e non una libreria che l'editor carica.** Le estensioni Lua e JS girano già dentro il processo dell'editor, sul suo stesso thread — è il caso normale, e regge perché sono interpretate: uno script sbagliato solleva un errore che l'editor intercetta, così una svista finisce in un messaggio e non in un crash. Ciò che non copre è uno script che non torna mai; quello congela la finestra allo stesso modo, ed è per questo che la regola qui sopra vi chiede di porre voi stessi un limite al lavoro.

Il codice nativo toglie anche il resto del confine. Un thread condivide lo spazio di indirizzamento, quindi un errore di segmentazione, un overflow dello stack o un `abort()` in un qualsiasi punto di un `.so` caricato si porta via l'editor, insieme al documento non salvato di chi legge e senza alcun modo di riferire che cosa sia successo; e lo scaricamento non è affidabile, quindi disabilitare un'estensione non la fermerebbe davvero. Un processo separato restituisce tutto questo — può andare in crash, bloccarsi, essere ucciso a scadenza, e l'editor sopravvive e sa dire di quale estensione si trattava. (Per Dart, del resto, non c'è nulla da scegliere: `dart compile` conosce `exe`, `aot-snapshot`, `js`, `wasm` e i formati snapshot. Non esiste alcun sottocomando che produca un `.so` o una `.dll` richiamabile da C.)

- **Usate `serve()` e i due punti seguenti sono già a posto.** Un'intera estensione compilata:

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

- **Non girate se non è stato l'editor ad avviarvi.** L'editor genera un token a ogni avvio e lo passa nella variabile d'ambiente `MARKTEXT_PLUS_PLUGIN_TOKEN`; senza, `serve()` stampa una riga che dice che cos'è questo programma ed esce con 1. Un token fatto per un avvio non può essere digitato da chi non l'ha ricevuto, e viaggia nell'ambiente e non in argv, che può leggere qualunque cosa sappia eseguire `ps`.

  **Che cosa fa e che cosa non fa.** Nessun programma può impedire l'esecuzione di un file che sta sul disco di chi legge — un doppio clic sul vostro eseguibile avvierà sempre un processo. Ciò che il token rende non falsificabile è la vostra risposta a «è stato l'editor ad avviarmi», così che il processo parta, dica che cos'è, e finisca, invece di restare seduto su stdin somigliando a un programma bloccato. Un'estensione che salta il controllo è un'estensione che nessuno ha protetto; per questo il controllo sta in `serve()` dell'SDK e non soltanto in questo paragrafo. Le estensioni script lo ottengono gratis: un file `.lua` o `.js` lo interpreta l'editor, e un doppio clic al massimo apre un editor di testo.

- **Terminate quando stdin arriva alla fine.** È così che vi si dice di fermarvi, ed è ciò che accade da sé se l'editor sparisce — `serve()` in quel momento ritorna. L'editor annota anche i processi che ha avviato e all'avvio successivo ripulisce quelli ancora in vita — ma solo quelli che ha avviato lui. **I processi che avviate *voi* tocca a voi ripulirli.**
- Lasciate stdout alle risposte del protocollo; le diagnostiche vanno su stderr.
- Le richieste hanno una scadenza, e uno scadere uccide solo il vostro processo.
- Trattate tutto ciò che manda l'host come non affidabile, e verificatelo.

## Compatibilità

Un'estensione è un file sulla macchina di qualcun altro, che questo editor legge. Romperla non è un errore di build che qualcuno qui vedrà — è un'estensione che smette di funzionare per chi la legge. Quindi:

**`minAppVersion` viene applicato.** Dite qual è l'editor più vecchio con cui la vostra estensione funziona e l'editor lo rispetta: uno più vecchio rifiuta di installarla, rifiuta anche di eseguirne una già installata, e dice quale versione è richiesta e quale è presente. Prima veniva letto e ignorato, il che è peggio che non avere il campo.

**Ciò che l'editor non toglierà senza preavviso.** Ogni nome di permesso, ogni valore di `runtime`, ogni azione che uno script può restituire, ogni campo di `ctx`, e `storage`, `t` e `require`, sono fissati da un test nel sorgente dell'editor. **Aggiungere** a quegli elenchi è libero; **togliere o rinominare** fa fallire quel test, e non può quindi succedere per sbaglio.

**Finché questo è 0.x**, un cambiamento incompatibile deliberato resta possibile, e finirà nel changelog insieme a che cosa fare. Quando manifest e protocollo saranno rimasti intatti abbastanza a lungo da meritare fiducia, questo diventerà 1.0 e la cosa finirà: da allora, quello che un'estensione può scrivere oggi continuerà a funzionare, e le cose spariranno solo dopo essere state dichiarate deprecate in una versione che le sosteneva ancora.

**Dove un'estensione è per conto suo.** L'editor non può garantire il comportamento del vostro prompt, né il modello che chi legge ha configurato, né i processi figli che un'estensione `process` avvia da sé. Né può impedire a chi legge di avviare a mano il vostro eseguibile — che cosa fa invece sta sopra, al token di avvio.

## Regole di sicurezza

- Non scrivete mai una chiave API nella directory dell'estensione o nel manifest.
- Su stdout non va nulla che non siano messaggi del protocollo.
- Ponete voi il limite al lavoro. Uno script gira sul thread dell'editor e
  niente lo interrompe: un ciclo senza uscita congela la finestra finché
  qualcuno non uccide il processo. Solo i plugin compilati hanno una scadenza,
  perché solo loro sono un processo separato da interrompere.
- Un ZIP di estensione con una voce che esce dalla cartella viene rifiutato
  all'installazione; così pure uno oltre i 64 MB, uno con più di 10000 voci, o
  uno che si scompatta oltre i 256 MB. Un eseguibile per tre piattaforme ci sta;
  una cartella di build versionata no.

L'SDK è sotto licenza MIT.
