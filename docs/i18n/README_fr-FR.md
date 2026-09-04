# SDK d'extensions pour MarkText Plus

Application principale : [MarkText Plus](https://github.com/SugarFatFree/marktext-plus)

[English](../../README.md) | [简体中文](README_zh-CN.md) | [日本語](README_ja-JP.md) | [한국어](README_ko-KR.md) | [Deutsch](README_de-DE.md) | Français | [Italiano](README_it-IT.md) | [Русский](README_ru-RU.md) | [Español](README_es-ES.md) | [Português](README_pt-PT.md) | [العربية](README_ar-SA.md) | [Português (Brasil)](README_pt-BR.md)

Comment écrire une extension pour MarkText Plus, et ce que l'éditeur lui permet ou non de faire.

**Préversion.** Ce SDK reste en 0.x tant que le système d'extensions n'est pas stabilisé ; le manifeste et le protocole décrits ici peuvent encore changer d'une version à l'autre. Ce que cela signifie aujourd'hui, et ce que cela signifiera plus tard, se trouve dans [Compatibilité](#compatibilité) plus bas.

## Choisissez d'abord un moteur d'exécution

Une extension tourne sur des machines où il n'y a que l'éditeur — pas de SDK Dart, pas de Node, pas de Python. Ce seul fait décide de l'essentiel de ce qui suit.

| `runtime` | Ce que vous livrez | Tourne sur | Quand l'utiliser |
|---|---|---|---|
| `lua` | un fichier `.lua` | toutes les plateformes, sans compilation | le cas normal : commandes de menu, questions, travail sur le texte |
| `js` | un fichier `.js` | toutes les plateformes, sans compilation | idem, si vous préférez écrire du JavaScript |
| `process` | **un exécutable par plateforme** | seulement celles pour lesquelles vous avez compilé | il vous faut une vraie chaîne d'outils, des bibliothèques, ou un traitement long |
| `data` | aucun code | partout | thèmes, extraits, dictionnaires |

Commencez par `lua` ou `js`. Une telle extension, c'est **un fichier de script et un `manifest.json`, rien d'autre** — pas de compilation, pas de compilateur, pas de seconde langue, et ces deux fichiers tournent tels quels sous Windows, macOS et Linux. Un script ne peut pas non plus faire tomber l'éditeur.

Ne prenez `process` que si un script ne suffit vraiment pas.

L'extension de traduction IA publiée à côté de ce SDK est tout ce qu'est une extension Lua sur le disque :

```
manifest.json
plugin.lua
README.md
CHANGELOG.md
LICENSE
```

Un script, un manifeste, et trois fichiers de documentation. **Pas la moindre trace de Dart.**

## Ce que contient ce dépôt

Un répertoire par langage, chacun une extension complète à copier :

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

Nommés d'après le **langage**, puisque c'est ce que vous choisissez. `runtime` dans le manifeste dit comment cela s'exécute — `lua`, `js`, `process` — et `examples/dart` est une extension `process` : Dart n'est que le langage dans lequel son exemple est écrit.

**Une extension `process` peut être écrite dans tout ce qui se compile en exécutable.** L'éditeur lance un programme et lui parle en JSON-RPC sur stdin et stdout ; il n'apprend jamais ce qui a produit ce programme. Go, Rust, C++, C#, un Python lié statiquement — tous conviennent, et aucun n'a besoin de ce dépôt au-delà du protocole :

- un objet JSON par ligne, sur stdin et stdout ;
- les réponses renvoient l'`id` numérique ;
- terminer quand stdin atteint la fin ;
- terminer si `MARKTEXT_PLUS_PLUGIN_TOKEN` n'est pas dans l'environnement, pour qu'un exécutable double-cliqué dise ce qu'il est au lieu d'attendre.

Voilà tout le contrat. Le voici en Python, sans rien tirer de ce dépôt — il répond à l'éditeur et refuse de tourner si personne ne l'a lancé :

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

[`examples/dart/lib`](../../examples/dart/lib), ce sont les mêmes quatre règles avec les bords traités : entrée mal formée, méthode inconnue, erreur dans un gestionnaire qui ne met pas fin à l'extension entière. Dart est ici parce que l'éditeur est écrit en Dart, et que `dart compile exe` était le chemin le plus court vers un exemple qui marche. Ce n'est ni une exigence ni une recommandation : réécrire quatre règles dans le langage que vous connaissez déjà est en général plus simple que d'ajouter une chaîne d'outils Dart à votre build.

Les trois points d'entrée font la même chose : charger l'API et l'appeler.

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

`lua` et `js` sont délibérément **la même extension écrite deux fois** — même manifeste, mêmes permissions, même comportement — pour qu'on puisse lire les deux côte à côte. **N'en copiez qu'une.** Une extension déclare un `runtime` et un point d'entrée ; un répertoire qui contient les trois, ce sont trois extensions portant un seul manifeste.

### Pourquoi le module d'API vit à l'intérieur d'un exemple

Parce qu'il est livré avec votre extension. `lib/marktext-plus.lua` n'est pas une dépendance que l'on désigne — c'est un fichier que vous copiez avec le reste et qui devient le vôtre. Copier `examples/lua` en entier vous donne une extension qui marche, API comprise ; il n'y a pas d'autre endroit où aller la chercher, ni de numéro de version à suivre.

### Ce qu'est le module d'API

Pour un script, c'est du Lua ou du JavaScript ordinaire, **livré avec votre extension**. L'éditeur injecte `storage`, `t` et `require` comme variables globales avant que votre fichier ne soit lu ; le module les rassemble sous un seul nom et ajoute un constructeur par action, si bien qu'une extension se lit `sdk.show(text, title)` plutôt que sous forme de table dont personne ne vérifie l'orthographe. Vous pouvez le modifier, ou ne pas l'utiliser du tout — renvoyer la table brute fonctionne exactement pareil.

Pour `examples/dart`, c'est une vraie bibliothèque, compilée dans votre exécutable, et elle porte ce dont un script n'a pas besoin : la boucle JSON-RPC, la vérification du lancement, l'arrêt. Une extension processus se tient de l'autre côté d'un tube.

## Une extension peut tenir en plusieurs fichiers

`require` charge un de **vos propres** fichiers — le module d'API ci-dessus est chargé exactement ainsi, et tout ce que vous placez à côté également :

```lua
local helpers = require("lib.helpers")   -- lib/helpers.lua, returns its table
```

```js
const helpers = require("lib/helpers");  // lib/helpers.js, sets module.exports
```

Chargé une seule fois, quel que soit le nombre d'appels. Le nom est un nom, pas un chemin : il se résout à l'intérieur du répertoire de votre extension et nulle part ailleurs. Découper une grosse extension — ou livrer avec elle une bibliothèque écrite par quelqu'un d'autre — ne vous donne donc aucun accès supplémentaire au reste du disque. Un nom contenant un séparateur, un `..` ou un point initial est refusé avant toute lecture, et le fichier résolu est ensuite vérifié comme se trouvant bien dans votre répertoire — c'est ce qui attrape un lien symbolique pointant vers l'extérieur.

## Essayer une extension avant de la livrer

Une extension Lua ou JavaScript est interprétée par l'éditeur ; l'épreuve honnête est donc de l'installer — **Extensions → Installer depuis un ZIP**. Deux choses peuvent être vérifiées plus tôt :

```
node tool/run-js-plugin.mjs examples/js      # or your own plugin directory
```

exécute une extension JavaScript comme le fait l'éditeur — mêmes variables globales injectées, même `require` qui n'atteint que le répertoire de l'extension, mêmes deux points d'entrée — et vous dit laquelle de vos réponses n'a pas la forme attendue. L'éditeur utilise QuickJS, qui n'existe que dans une application compilée ; ceci en tient lieu.

```
cd examples/dart && dart compile exe plugin.dart -o bin/linux/plugin
echo | ./bin/linux/plugin       # should refuse: it was not started by the editor
```

c'est toute la vérification d'une extension compilée : elle se compile, et elle refuse de tourner quand personne ne lui a donné de jeton de lancement.

## Manifeste

`manifest.json` est à la racine de l'extension. L'éditeur le lit **sans rien exécuter**. Voir [`schema/manifest.schema.json`](../../schema/manifest.schema.json).

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

### Exécutables par plateforme

Une extension `process` n'utilise pas `entrypoint`. Elle nomme ses exécutables **par système d'exploitation**, l'architecture en dessous et seulement là où elle compte :

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

Le système est la partie à laquelle vous devez toujours répondre — une compilation Windows est un autre fichier qu'une compilation Linux. L'architecture souvent non, elle est donc facultative :

- **Un chemin pour tout le système.** `macos` ci-dessus est un binaire universel : un fichier qui contient les deux architectures, comme les compilations macOS se livrent d'ordinaire. Écrire deux fois le même chemin pour le dire serait pire.
- **Une table d'architectures.** `windows` ci-dessus livre une compilation distincte pour chacune et ne prend rien d'autre en charge.
- **Un `default` commun plus une spécialisation.** `linux` ci-dessus exécute `bin/linux/plugin` partout sauf sur arm64, qui a la sienne. La spécialisée l'emporte.

Les systèmes sont `windows`, `macos` et `linux` ; les architectures, `x64` et `arm64`. **Tout autre nom est refusé à l'installation plutôt qu'ignoré** — sans quoi un `windwos` mal orthographié se transformerait, au moment du clic, en « cette extension ne prend pas votre plateforme en charge », sans rien pour l'expliquer.

Une plateforme pour laquelle vous n'avez pas compilé est nommée plutôt que devinée — « pas de compilation pour `linux-arm64` ; ce qui est livré, c'est `macos-x64`, `macos-arm64`, `windows-x64` ». Déclarer `runtime: "process"` sans `entrypoints`, ou nommer un système sans rien mettre dessous, est refusé.

## Comment une extension script est appelée

Les deux moteurs de script sont synchrones — l'interpréteur Lua n'a pas de coroutines, et le moteur JS n'a pas de boucle d'événements propre. Tout ce qui prend du temps (interroger le lecteur, appeler un modèle) bloquerait l'éditeur. Un script n'attend donc jamais : il **renvoie une action** décrivant ce qu'il veut voir fait, l'éditeur le fait, puis rappelle le script avec la réponse.

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

La même forme en JavaScript :

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

### Les actions

| Retour | Ce que fait l'éditeur | Ensuite |
|---|---|---|
| `{ ask = "…", default = "…", choices = {…} }` | interroge le lecteur ; `choices` apparaissent en pastilles à presser, et ce qui est saisi à la place est repris tel quel | rappelle `on_command` avec `ctx.answer` renseigné |
| `{ ai = "…" }` | envoie votre invite au modèle configuré par le lecteur | appelle `on_result(ctx, reply)` |
| `{ show = "…", title = "…" }` | montre une réponse dans une petite fenêtre, avec un bouton de copie | s'arrête ; rien n'est écrit |
| `{ panel = "…", title = "…" }` | la montre dans un panneau à côté du document | s'arrête ; rien n'est écrit |
| `{ pane = "…", title = "…", slot = "right"\|"bottom"\|"corner" }` | remplit l'un des volets autour du document | s'arrête ; rien n'est écrit |
| `{ notify = "…" }` | dit une ligne au lecteur | s'arrête |
| `{ diff = { original = "…", result = "…" } }` | montre les deux textes côte à côte | s'arrête ; rien n'est écrit |
| `{ replace = "…" }` | remplace la sélection | s'arrête |
| n'importe quoi d'autre | rien | s'arrête |

**Les volets.** L'éditeur partage déjà un onglet entre source et aperçu ; `pane` est ce partage, mis à votre disposition. Le document garde la première case, et vous pouvez en remplir jusqu'à trois autres.

La forme suit le nombre de volets remplis, et reste symétrique à chaque étape :

| Remplis | Disposition |
|---|---|
| aucun | le document occupe tout l'onglet |
| un | le document et votre volet côte à côte, moitié chacun |
| deux | la moitié haute partagée par le milieu, votre deuxième volet prenant toute la moitié basse |
| trois | les deux moitiés partagées, quatre cases égales |

Les séparateurs se déplacent, comme celui entre source et aperçu.

Les noms `right`, `bottom`, `corner` disent **quel volet**, non où il se pose : ce sont les adresses par lesquelles vous le retrouverez plus tard — pour y ajouter, ou pour remplacer ce qu'il contient. Ne remplir que `corner` vous donne un volet à côté du document, pas un coin précédé de deux cases vides. Un nom que l'éditeur ne connaît pas est refusé plutôt que deviné : un volet qui paraît là où vous ne l'avez pas demandé, sans moyen de savoir pourquoi, est pire qu'un refus.

**Dites que vous travaillez avant de commencer.** Une action de volet est lue avant une action `ai` : renvoyer les deux signifie « affiche ceci, puis va demander » — et un volet au texte vide avec une requête derrière lui est précisément ce que l'éditeur dessine comme « en cours ». Tant que le premier bloc n'est pas arrivé, il le dit là où le texte ira ; ensuite cela passe dans la barre de titre, pour que l'avancement ne recouvre jamais ce qui est arrivé. Ne renvoyer que le `ai` laisse l'écran inchangé pendant les secondes que prend le modèle, ce qui se lit comme une entrée de menu sans effet.

Fermer un volet, c'est ainsi que la personne qui lit vous arrête. Ajouter à un volet qu'elle a fermé est refusé, plutôt que de le ramener un bloc à la fois.

**`show` ou `panel`.** Quelques lignes sont une réponse : une petite fenêtre convient, et un panneau pour cela fait plus de meuble que de contenu. Un résultat de la taille d'un document est ce que le lecteur tient contre ce qui est à l'écran, et une fenêtre par-dessus l'écran est le seul endroit où il ne peut pas aller.

Une exécution est bornée à huit questions ; un script qui répond à chaque question par une autre ne peut donc pas retenir le lecteur.

**L'invite est la vôtre.** L'éditeur détient les identifiants et effectue la requête ; il ne réécrit pas votre invite, et votre script ne voit jamais la clé d'API. Ce qui est soumis au modèle, c'est exactement la chaîne que vous avez renvoyée dans `ai`.

### Ce qu'un script peut atteindre

Ceci seulement. Pas d'`os`, pas de `package`, pas de `dofile`, pas de `loadfile`, pas de système de fichiers et pas de réseau — une extension script vient du dépôt d'un inconnu : elle obtient ce qu'elle a déclaré, et rien d'autre.

| | |
|---|---|
| `storage.get(key)` / `storage.set(key, value)` | vos propres réglages, dans votre propre répertoire. Chaînes uniquement. Nécessite `storage.local` |
| `t(key)` | votre propre chaîne dans la langue du lecteur ; une clé inconnue revient telle quelle |
| `require(name)` | un de vos propres fichiers, résolu seulement dans le répertoire de votre extension |
| `ctx.command` | l'`id` de l'entrée de menu ou de la commande déclenchée |
| `ctx.selection` | le texte sélectionné, `""` quand rien ne l'est |
| `ctx.document` | le document entier |
| `ctx.answer` | ce que le lecteur a saisi la dernière fois que vous avez demandé, sinon nil/undefined |
| `ctx.view` | comment le lecteur regarde le document : `source`, `preview` ou `split` |

### Ce que ce Lua ne fait pas

L'interpréteur est un Lua écrit entièrement en Dart — c'est précisément pour cela qu'une extension script n'exige rien d'installé — et il est incomplet. Les quatre points suivants échouent tous **silencieusement**, et c'est là que le temps se perd : un motif qui ne trouve rien ressemble exactement à un document qui ne contient rien.

| Au lieu de | Utilisez | Parce que |
|---|---|---|
| `#someString` | `string.len(s)` | lève `length error`. `#` sur une *table* fonctionne : impossible de les distinguer au ressenti |
| `s:match("%S")`, `%s` | comparer les caractères : `s:sub(i, i) == " "` | les classes ne trouvent rien, chaque ligne paraît donc vide |
| `for l in s:gmatch("(.-)\n")` | `s:find("\n", pos, true)` et `s:sub` | ne renvoie absolument rien |
| `s:gmatch("[^\n]*")` | idem | n'avance jamais au-delà d'une correspondance vide |

La suite de tests de l'éditeur fixe ces quatre points : si l'interpréteur est remplacé, ce tableau sera corrigé plutôt que laissé à induire en erreur.

Le moteur JavaScript est QuickJS et ne présente pas de lacunes comparables qui mériteraient d'être listées.

## Permissions

Déclarées dans le manifeste, montrées au lecteur, et **appliquées**. VS Code et IntelliJ montrent une liste de permissions puis font confiance à l'extension ; ici, personne ne relit quoi que ce soit, c'est donc l'éditeur qui vérifie. Renvoyer `{ ai = ... }` sans `ai.chat` n'appelle aucun modèle — il est dit au lecteur que l'extension ne l'a pas demandé.

| Permission | Permet à l'extension de |
|---|---|
| `document.read` | lire le document ouvert et la sélection |
| `document.write` | modifier le document ouvert |
| `ui.contextMenu` | ajouter des entrées au menu contextuel |
| `ui.menuBar` | ajouter des entrées à la barre de menus |
| `ui.toolbar` | ajouter un bouton de barre d'outils |
| `ui.sidebar` | ajouter un panneau à la barre latérale |
| `ui.statusBar` | ajouter un élément à la barre d'état |
| `ui.settings` | avoir sa propre page de réglages |
| `ui.commandPalette` | ajouter des commandes à la palette |
| `ui.notifications` | dire quelque chose au lecteur |
| `ai.chat` | interroger le modèle configuré (la clé n'est jamais transmise) |
| `storage.local` | garder son propre fichier de réglages dans son propre répertoire |
| `clipboard.read` / `clipboard.write` | le presse-papiers |
| `workspace.read` / `workspace.write` | les fichiers sous le dossier ouvert par le lecteur |
| `network.request` | émettre ses propres requêtes HTTP. **La plus large que l'on puisse demander** : tout ce qu'elle peut lire, elle peut l'envoyer n'importe où |

Ne demandez que ce que vous utilisez. Une extension qui demande `network.request` pour ajouter une entrée de menu est une extension que le lecteur devrait refuser.

## Points de contribution

```json
"menus":    [{"id": "…", "title": "…", "location": "editor.contextMenu", "when": "selection"}],
"commands": [{"id": "…", "title": "…"}],
"toolbar":  [{"id": "…", "title": "…", "icon": "…"}],
"panels":   [{"id": "…", "title": "…", "icon": "…"}],
"pages":    [{"id": "…", "title": "…"}]
```

`title` peut être une clé de traduction. `location` est un emplacement défini par l'éditeur — une extension pose des choses à des emplacements nommés, jamais à des coordonnées en pixels, et ne remet jamais ses propres widgets à l'éditeur.

`panels` place une icône dans la barre latérale de droite ; la presser ouvre un tiroir rempli en exécutant votre commande du même `id`. Cela nécessite `ui.sidebar`, et une `icon`, car la barre est un rail d'icônes et une entrée sans rien à dessiner serait un vide qui ouvre quelque chose. Si aucune extension ne contribue de panneau, il n'y a pas de rail du tout — une bande d'icônes sans icônes, c'est de la largeur prise au document pour rien.

Un panneau s'ouvre et répond : une commande qui renvoie `ask` ou `ai` y est rapportée sous forme de texte plutôt que de s'arrêter pour demander, car un tiroir n'est pas une conversation.

`when` dit quand une entrée de menu mérite d'être proposée : `selection` seulement s'il y a une sélection, `noSelection` seulement s'il n'y en a pas, et son absence signifie toujours. Sans cela, toutes les entrées sont proposées en même temps — « Traduire la sélection » sans rien de sélectionné, et « Traduire le document » alors que le lecteur pointe un paragraphe. Une valeur que l'éditeur ne connaît pas est refusée à l'installation au lieu d'être lue en silence comme « toujours ».

## Réglages

Chaque champ de `settings` devient un vrai contrôle sur la page de réglages de l'extension, dessiné par l'éditeur :

| `type` | Contrôle |
|---|---|
| `text` | une zone de texte |
| `password` | une zone de texte qui ne montre pas son contenu |
| `number` | une zone de texte numérique |
| `boolean` | un interrupteur ; enregistré sous forme des chaînes `"true"` / `"false"` |

Les valeurs vivent dans `settings.json`, dans le répertoire propre de l'extension : aucune extension ne peut donc lire ni écrire les réglages d'une autre. Ce que le lecteur enregistre parvient à un script déjà en cours à sa commande suivante, et non au prochain démarrage.

## Traductions

`locales` associe à une langue vos propres chaînes ; `defaultLocale` dit sur quoi se rabattre. Un lecteur en `zh_CN` obtient `zh_CN` si vous l'avez fourni, puis `zh`, puis votre langue par défaut. Fournissez les langues que vous voulez — c'est votre table, pas celle de l'éditeur.

## Extensions compilées (`runtime: "process"`)

L'exécutable est lancé comme processus enfant et parle JSON-RPC 2.0, un objet JSON par ligne, sur stdin/stdout. Les réponses renvoient l'`id` numérique. [`examples/dart/lib`](../../examples/dart/lib), dans ce dépôt, met cela en œuvre pour les extensions écrites en Dart et compilées avec `dart compile exe`.

### Vous ne pouvez pas livrer un source qui exige une chaîne d'outils pour tourner

Cela ne concerne que les extensions compilées, et Dart en particulier, parce que l'éditeur est écrit en Dart : `entrypoint: "bin/plugin.dart"` est refusé à l'installation. L'exécuter exigerait un SDK Dart sur la machine du lecteur, que l'éditeur n'installe pas et ne peut pas présumer — et une compilation de production n'a aucun interpréteur à lui remettre. Compilez-le (`dart compile exe`) et livrez l'exécutable.

Rien de tout cela ne s'applique à une extension Lua ou JavaScript. Celles-là sont interprétées par l'éditeur lui-même, ce qui est tout leur intérêt : pas de Dart, pas de chaîne d'outils, pas de compilation.

**Pourquoi un processus et non une bibliothèque que l'éditeur charge.** Les extensions Lua et JS tournent déjà dans le processus de l'éditeur, sur son propre fil — c'est le cas normal, et c'est sûr parce qu'elles sont interprétées : un mauvais script lève une erreur que l'éditeur rattrape. Le code natif n'a pas cette frontière. Un fil partage l'espace d'adressage : une erreur de segmentation, un débordement de pile ou un `abort()` n'importe où dans un `.so` chargé emporte l'éditeur, avec le document non enregistré du lecteur et sans aucun moyen de rapporter ce qui s'est passé ; une boucle sans issue gèle la fenêtre sans qu'on puisse l'interrompre ; et le déchargement n'est pas fiable, désactiver une extension ne l'arrêterait donc pas vraiment. Un processus distinct rend ces trois choses — il peut planter, se bloquer, être tué après un délai, et l'éditeur survit et peut dire de quelle extension il s'agissait. (Pour Dart, il n'y a de toute façon rien à choisir : `dart compile` connaît `exe`, `aot-snapshot`, `js`, `wasm` et les formats d'instantané. Aucune sous-commande ne produit un `.so` ou une `.dll` appelable depuis C.)

- **Utilisez `serve()` et les deux points suivants sont déjà réglés.** Une extension compilée entière :

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

- **Ne tournez pas si l'éditeur ne vous a pas lancé.** L'éditeur engendre un jeton à chaque lancement et le passe dans la variable d'environnement `MARKTEXT_PLUS_PLUGIN_TOKEN` ; sans lui, `serve()` affiche une ligne disant ce qu'est ce programme et se termine avec le code 1. Un jeton fabriqué pour un lancement ne peut pas être saisi par qui ne l'a pas reçu, et il voyage dans l'environnement plutôt que dans argv, que peut lire tout ce qui sait exécuter `ps`.

  **Ce que cela fait et ne fait pas.** Aucun programme ne peut empêcher l'exécution d'un fichier situé sur le disque du lecteur — double-cliquer votre exécutable démarrera toujours un processus. Ce que le jeton rend infalsifiable, c'est votre réponse à « est-ce l'éditeur qui m'a lancé », de sorte que le processus démarre, dit ce qu'il est, et se termine, au lieu de rester assis sur stdin à ressembler à un programme bloqué. Une extension qui saute cette vérification est une extension que personne n'a protégée ; c'est pourquoi la vérification est dans `serve()` du SDK et pas seulement dans ce paragraphe. Les extensions script l'obtiennent gratuitement : un fichier `.lua` ou `.js` est interprété par l'éditeur, le double-cliquer ouvre au pire un éditeur de texte.

- **Terminez quand stdin atteint la fin.** C'est ainsi qu'on vous dit de vous arrêter, et c'est ce qui arrive de soi-même si l'éditeur disparaît — `serve()` rend la main à ce moment-là. L'éditeur note aussi les processus qu'il a lancés et nettoie au démarrage suivant ceux qui tournent encore — mais seulement ceux qu'il a lancés. **Les processus que *vous* lancez, c'est à vous de les nettoyer.**
- Laissez stdout aux réponses du protocole ; les diagnostics vont sur stderr.
- Les requêtes sont bornées par un délai, et un dépassement ne tue que votre processus.
- Traitez tout ce qu'envoie l'hôte comme non fiable et vérifiez-le.

## Compatibilité

Une extension est un fichier sur la machine de quelqu'un d'autre, que cet éditeur lit. La casser n'est pas un échec de compilation que quelqu'un ici verra — c'est une extension qui cesse de fonctionner pour ses lecteurs. Donc :

**`minAppVersion` est appliqué.** Nommez le plus ancien éditeur avec lequel votre extension fonctionne et l'éditeur s'y tient : un éditeur plus ancien refuse de l'installer, refuse aussi d'exécuter une extension déjà installée, et nomme la version demandée et la version présente. Ce champ était auparavant lu puis ignoré, ce qui est pire que de ne pas l'avoir.

**Ce que l'éditeur ne retirera pas sans prévenir.** Chaque nom de permission, chaque valeur de `runtime`, chaque action qu'un script peut renvoyer, chaque champ de `ctx`, ainsi que `storage`, `t` et `require`, sont fixés par un test dans le source de l'éditeur. **Ajouter** à ces listes est libre ; **retirer ou renommer** fait échouer ce test, et ne peut donc pas arriver par inadvertance.

**Tant que ceci est en 0.x**, un changement incompatible délibéré reste possible, et il figurera alors au journal des modifications avec ce qu'il faut faire. Quand le manifeste et le protocole seront restés assez longtemps intacts pour mériter confiance, ceci deviendra 1.0 et cela cessera : ensuite, ce qu'une extension peut écrire aujourd'hui continuera de fonctionner, et rien ne disparaîtra sans avoir été annoncé comme obsolète dans une version qui le prenait encore en charge.

**Là où une extension est seule.** L'éditeur ne peut garantir ni le comportement de votre invite, ni le modèle configuré par le lecteur, ni les processus enfants qu'une extension `process` lance elle-même. Il ne peut pas non plus empêcher un lecteur de lancer votre exécutable à la main — ce qu'il fait à la place figure plus haut, au jeton de lancement.

## Règles de sûreté

- N'écrivez jamais une clé d'API dans le répertoire de l'extension ni dans le manifeste.
- Rien d'autre que les messages du protocole ne va sur stdout.
- Bornez le travail ; l'éditeur impose des délais et des limites de pas.
- Un ZIP d'extension contenant une entrée qui remonte hors du répertoire est refusé à l'installation.

Le SDK est sous licence MIT.
