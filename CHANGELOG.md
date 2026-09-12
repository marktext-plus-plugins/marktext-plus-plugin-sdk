# Changelog

## [Unreleased]

### Changed

- **The README says what happens to a third pane beside a document being read
  in split view: it is not drawn.** Source and preview are already a division
  and take a cell each, so only two of the three slots have a cell beside them.
  This repository told authors how three cells divide "with a document that is
  **not split**" and then said nothing about the case where it is — while
  arguing, two paragraphs down, that a slot the editor does not know is
  "refused rather than guessed at" because a pane appearing where you did not
  ask for it, with no way to find out why, is worse than being told. A pane not
  appearing at all is worse still.

  The sentence carries a `◆` in all twelve documents, and the editor's
  `the_sdk_says_what_the_editor_does_not_do_test` counts them — the editor is
  the side that knows whether it is still true. `†` and `‡` already mark the
  other two things this repository promises and the editor does not do.

- **The README says which contribution points the editor does not draw yet, and
  that it does not start a compiled plugin.** Three promises this repository made
  and the editor does not keep:

  - `toolbar` — a button declared here does not appear. The `†` that means "the
    permission is real and there is nothing behind it" was on `ui.toolbar` in the
    permissions table two sections away; the Contribution points block, which is
    the part an author copies, listed five points with nothing to tell three from
    two.
  - `pages` — read by the editor and then never looked at again, and explained
    nowhere at all. A plugin's own settings page comes from `settings`, which is
    drawn.
  - `runtime: "process"` — the whole section was in the present tense, and this
    repository ships `packages/dart` for it. A compiled plugin installs; running
    one of its commands says *"has no script to run: its runtime is process"*.
    The host that speaks the protocol is written and tested inside the editor,
    and nothing dispatches a command to it.

  Marked with `‡` in the runtime table, in a footnote under it, and at the head
  of the compiled-plugins section, in the English README and all eleven
  translations. `toolbar` and `pages` now sit last in the block with a paragraph
  under it saying so. Nothing is removed: the fields stay part of the manifest
  and will be honoured when the capability arrives, as the `†` permissions do.

  The cost of not saying it is an author's evening — the field is accepted, the
  plugin installs, and nothing happens.

- **`check.py` reconciles the contribution points three ways.** The block
  against the schema in both directions: a field the schema has and the block
  does not is one an author copying the block will never learn about, and a field
  the block has and the schema refuses produces a manifest that will not install.
  The eleven translations against the English one for the same keys in the same
  order — the action table beside it has had that guard since a row went missing
  in translation, and the contribution points had not. And the count of `‡`
  marks, because a translation that loses one costs the evening above.

  The editor's repository carries the other half: it knows which fields it draws,
  so it checks that these READMEs mark the ones it does not.

- **`check.py` refuses a valueless `return` in any example.** On `lua_dardo` a
  `return` with no value inside a nested function is not a return: execution
  carries on to the next statement, so `if not ok then return end` — how every
  Lua programmer writes a guard — does not guard, and inside `while true` it is
  a loop with no exit that reaches the reader as an editor which has stopped
  answering. The README's own table says this; nothing here held the examples
  beside it to it. The only check that did lives in the editor's repository and
  runs when the editor is pushed, so an example broken here stayed broken until
  then. Every spelling is refused now: alone, before `end`, before `else`,
  closed with a semicolon, or followed by a comment.

- **`check.py` compares each example's declared commands with the ones its
  script names.** Both examples are correct today and name both of theirs.
  What the check prevents is the way an example stops working without anyone
  noticing: a menu entry added to the manifest and not to the script, so the
  reader clicks it and the plugin does whatever its last branch happens to do.
  The official plugin had exactly that shape. The reverse is checked too — a
  branch for a command the manifest does not declare can never run, because
  the editor refuses a command a plugin never declared.

## [0.1.3] - 2026-09-11

### Added

- **`as = "web"` — a plugin can draw its own HTML page.** `ui.webview` had been
  declared, described to the reader, listed here in twelve languages and given a
  proxy of its own, and there was no way for a plugin to open a page. There is
  now: a pane whose text is an HTML document, drawn by the operating system's
  web engine rather than a browser packaged with the editor, and created only
  when a plugin asks so a reader who never opens one never pays for an engine.
  Where the page goes is written to the plugin log. Windows and macOS have an
  engine the editor can use; a Linux box without one gets a line saying so,
  naming the plugin, rather than an empty pane.

  Declaring `ui.webview` now carries `ui.sidebar` as well as `network.request`:
  a page arrives as a pane, and taking room beside the document is not something
  to get for free alongside the engine.


- **What a panel is asked on a second round.** A command run from a panel can
  now be run again, with the reader asking for its answer to be changed rather
  than describing the whole thing afresh. The editor says so in fields the
  script already knows: `ctx.selection` is the script's own last answer,
  because a follow-up is about the draft in front of the reader rather than
  the document, and `ctx.answer` is what was asked for this time.

  A command that reads the selection as "the part to work on" needs no change.
  One that ignores `ctx.selection` will rewrite the whole document every
  round, which is not what was asked. The box is only offered when the command
  asked something to begin with, since that is where a follow-up arrives.

- **`sdk.ui` — a plugin can draw its own interface.** It returns a tree of
  nodes (`text`, `input`, `chips`, `button`, `row`, `column`, `spacer`) and the
  editor renders them as its own widgets; pressing a button calls
  `on_event(ctx, id, values)` with every input in the tree by id, so a plugin
  never has to remember the form it drew a step ago.

  Not HTML, and deliberately: these are the editor's own widgets, so they cost
  nothing at startup, follow the reader's theme without the plugin knowing what
  the theme is, and cannot draw outside the container they were given. A
  WebView escape hatch is planned separately for what this cannot express.

  A misspelled node refuses the whole tree with an error rather than quietly
  drawing nothing, and so does a tree deeper than 12 or larger than 500 nodes —
  half a form is worse than none.
- Three more nodes: `select` (a dropdown, for when there are too many options
  for chips), `checkbox` (its value arrives as `"true"` or `"false"`, because
  everything a plugin is told is a string), and `markdown` — drawn by the
  editor's own renderer, so an answer that is a document looks like one
  instead of showing its own `##` and `**`.
- An `image` node. `source` is a `data:` URI, a path inside your own plugin
  directory, or an `http(s)` URL — and that last one is fetched **by the
  editor**, so it follows the reader's system proxy and lands in your plugin's
  log with the host, status, size and time. You may reach the network; the
  reader may find out where you went. A permission nobody can check up on
  afterwards is a promise rather than a permission.
- `ui.webview` joins the permission list, and **carries `network.request` with
  it** — the reader is shown both, because a permission list that understates
  what it grants is worse than none. The web view itself lands in a later
  release; the permission and the logging are here first.

Nothing here changes how a plugin behaves. One of them changes what the
documentation tells you to do, which for someone starting a plugin is the
same thing.

- The safety rules now state the limits an installed ZIP has to fit: 64 MB for
  the archive, 10000 entries, 256 MB unpacked. They were added to the editor
  today (a ZIP was free to claim it unpacked to gigabytes, and to mean it), and
  an author who packages three platforms' executables should hear the number
  from here rather than from a failed install.

- **The icon names a panel may use are in the schema.** It asked only for a
  non-empty string, so the forty names the editor can draw were something to
  guess at — and a name it does not know draws a generic plugin square with
  nothing said, which reads as the editor ignoring your icon rather than as a
  typo. An editor writing your manifest now completes them and refuses the
  rest.
- **Where to look when a plugin installs and does not appear.** The editor
  lists a plugin whose manifest it could not read below the ones that loaded,
  with the key it could not read and what it expected there, and a delete
  button on that row. "Trying a plugin before you ship it" only covered trying
  one before shipping; it now covers the case where it is installed and
  invisible, with the three reasons that account for most of it.

### Fixed

- **The API module still listed seven kinds of interface node; there are
  eleven.** `select`, `checkbox`, `markdown` and `image` were added to the
  editor and written into the README's table, and the one-line list inside both
  API modules stayed where it was. That list is what an author reads in an
  editor's hover, which is where "what can I put in a tree?" is actually asked
  — and a tree is refused whole over one unknown node, so not knowing a kind
  exists costs a whole interface rather than one node.

  `scripts/check.py` now holds the two modules to the README's table, and the
  editor's own test suite holds that table to the nodes it draws. Between them
  a kind cannot be added in one place and missed in the other two.

- **Five rows of the permissions table promised things the editor has never
  built.** "add a toolbar button", "add a status-bar item", "add commands to
  the palette", the clipboard and the workspace: seven permissions in all, and
  behind each of them nothing. There is no toolbar or status bar a plugin can
  add to, nothing registers a plugin's commands in the palette, and neither
  script runtime mentions a clipboard or a workspace anywhere. An author who
  read a row, declared the permission, wrote the manifest entry and saw nothing
  happen had lost an evening to a sentence.

  They are marked `†` now, in all twelve languages, with a note under the table
  saying what the dagger means: the permission is real and the reader is shown
  it, and there is nothing behind it yet. The rows stay, because they are part
  of the manifest and will be honoured when the capability arrives. The
  editor's own test suite decides which rows carry the dagger — the day one of
  these is implemented, the dagger has to come out or that test fails.

- **The examples said they showed all of it, and showed seven of twelve.**
  "Every capability the editor offers is used once" opened both scripts, and
  the five they leave out include `pane` — the grid the editor lays results out
  in, the one that takes a slot, a way of drawing and an Apply button, and the
  one the shipped AI plugin lives in. An example is the first thing an author
  copies, so a claim on top of it is read as a map of the API. They now say
  which seven, point at the actions table for the rest, and name `pane` as the
  one to read next; `scripts/check.py` counts both numbers and fails when
  either drifts.

- **Nothing compared the eleven translated actions tables with the English
  one.** An eleventh action added to the English table would have left the
  other eleven at ten, and an author reading in their own language would never
  have learned it existed. Compared by the action name rather than the whole
  cell, since the metavariables inside it — `<node>` and the ellipses — are
  English words and are translated on purpose.

- **`nothing()` had lost its comment to `ui()`.** When `ui` was added between
  `replace` and `nothing`, the one-line description stayed where it was — so
  `Do nothing.` ended up on top of the interface-drawing documentation, and the
  function that does nothing said nothing at all. In both languages, because
  they were edited together. Nobody reads this module top to bottom; it is read
  one function at a time in an editor's hover, where a comment one function out
  describes the wrong thing with the same authority as a right one.

  `scripts/check.py` now requires every exported name to have a doc comment
  immediately above it, in both languages, so the next insertion cannot take
  one with it.

- **The English README said there is no `require`, five paragraphs after
  explaining how to use it.** The sandbox list — "no `os`, no `package`, no
  `require`, no `dofile`, no `loadfile`" — was written before a plugin could be
  more than one file. Lua's own `require` is indeed removed; the editor then
  installs one that cannot leave the plugin's own directory, which is what
  loads `lib/marktext-plus.lua`. So the document told an author their `require`
  would fail while shipping a library file that needs it. All eleven
  translations had been corrected and the English had not, which is the
  opposite of the usual direction.
- **`ctx.view` was documented in seven languages and missing from five.**
  A script is told whether the reader is in `source`, `preview` or `split`;
  English, German, Japanese, Korean and Chinese never said so. The same four
  translations once lost the side panel.

  Both were found by comparing the backticked identifiers across the twelve —
  the one part of a document in eleven languages that does not change with the
  language. The editor's `sdk_schema_agrees_test` now holds all twelve to the
  same set of 108, with no exceptions.
- **All twelve READMEs still described the rule the editor stopped following.**
  A lone pane used to sit beside the document whatever slot it claimed — "one
  pane is one pane whichever slot it claimed" — and since 2026-09-07 the name
  decides: only `bottom` puts it under the document, any other slot beside it.
  The editor was changed after manual testing, its own layout test was changed
  with it, and the SDK was not. An author filling only `bottom` was told they
  would get a pane beside the document and got one below it, while the official
  writing and proofreading commands were already relying on the new behaviour.

  The direction sentence is now in all twelve, and the editor's
  `sdk_schema_agrees_test` counts `bottom` in that paragraph: it is named once
  as a slot and a second time saying which way that slot goes, so a language
  that keeps only the list fails. The identifier does not translate, which is
  what makes the count work in eleven languages the guard cannot read.
- **The German, Japanese, Korean and Chinese docs had no `panels` in them at
  all** — no line in the manifest field list, neither paragraph explaining
  what a panel is. Anyone reading those four did not know a plugin could put
  anything in the right side bar. Eight of twelve described one more
  capability than the rest, and the guard comparing the translations counts
  headings and fenced blocks, which that section has neither of.
- **A panel asks in its own drawer now, and the docs said otherwise.** They
  said a command returning `ask` is reported there as text "because a drawer is
  not a conversation". The question goes in the drawer — its text, the
  `choices` you named, a box holding last time's answer — and the reply comes
  back to the same drawer. A command started from a menu still asks in the
  floating card, having no room of its own.
- **`return` on its own inside a nested function does nothing in the editor's
  Lua.** `if not ok then return end` continues into the failure it was
  checking for, and `while true do return end` is an infinite loop. Write
  `return nil`. Every guard an experienced Lua programmer writes by reflex is
  the shape that does not work here.

- **The safety rules promised a protection that does not exist.** "Keep work
  bounded; the editor enforces timeouts and step limits" — it does not, for
  Lua or JavaScript. Both run on the editor's own thread, synchronously, with
  no interrupt available: `lua_dardo` exposes no debug hook and `flutter_js`
  does not surface QuickJS's interrupt handler. A loop with no exit freezes
  the window until the process is killed. Only compiled plugins are timed out,
  because only they are a separate process. The rule now says that, in all
  twelve languages.
- The same paragraph that argues for compiled plugins being a separate process
  listed "a loop with no exit freezes the window" among the things native code
  costs you — and called scripts safe "because both are interpreted". The
  interpreting boundary is real and it catches errors; it does nothing about a
  script that never returns. That sentence has been corrected rather than
  removed: knowing which half of the boundary holds is the point of the
  paragraph.
- The README and all eleven translations pointed at `examples/`, a directory
  renamed to `packages/` before 0.1.2, and taught a `tool/run-js-plugin.mjs`
  that was deleted at the same time. Both had been corrected; the 0.1.2 release
  commit rewrote those twelve files from an older copy and put them back, so
  0.1.2 shipped telling a new plugin author to open a directory that is not
  there. The check below now refuses any documented path this repository does
  not have.

### Internal

- The repository checks itself on every push: that the Lua and JavaScript
  modules expose the same names, that the published schema is a valid JSON
  Schema, and that each example manifest satisfies it. All three were true
  and none of them was enforced — a plugin written in one language and ported
  to the other would have been the first to find out otherwise.
  `scripts/check.py` runs the same checks locally, with no arguments.
- It also refuses a README, in any language, that names a path this repository
  does not have.

## [0.1.2] - 2026-09-05

The first release rather than a pre-release. Still 0.x: the manifest and the
protocol are settling but not settled, and a deliberate breaking change
remains possible while that is true — it will be in this file with what to do
about it.

### Added

- `apply` on a pane action puts an Apply button on it, which writes what the
  pane holds into the document; `replaces` says what that replaces, and an
  empty one means the whole document. What a model returns is worth reading
  before it lands in what the reader was writing, so a rewrite is shown first
  and written when they say so. Needs `document.write`, which the editor
  checks when the button is pressed rather than trusting the flag.
- `description` in the manifest: one line saying what the plugin does, for the
  plugin list. Like every other string a plugin shows, it may be a key into
  its own `locales`.

### Changed

- The three example plugins are back under `packages/`, where they were before
  they were briefly `examples/`.

### Removed

- `tool/run-js-plugin.mjs`. It ran a JavaScript plugin under Node to stand in
  for the editor, but the editor uses QuickJS and Node is V8 — so what it
  proved was an approximation, and only for one of the three runtimes: Lua has
  no equivalent, because `lua_dardo` likewise exists only inside a built
  application. The honest test was always installing the plugin, which is what
  the README said next to it.
- `tool/check-translations.mjs`. It compared the translated READMEs against the
  English one — a tool for maintaining this repository, of no use to anyone
  writing a plugin, and it had no business shipping in an SDK.

## [0.1.1] - 2026-09-03

Pre-release. The SDK stays at 0.x while the plugin system is still settling.

The first release described one kind of plugin: a separate process speaking
JSON-RPC. That is now one of four, and no longer the one to reach for.

### Added

- `runtime`: `lua` and `js` plugins, which are a single file that runs inside
  the editor on every platform with nothing to build.
- The action protocol — `on_command` returns what it wants done, the editor
  does it, `on_result` gets the answer — so a script never blocks the editor
  while the reader is asked something or a model is called.
- `storage` and `t()`: a plugin's own settings, and its own strings in the
  reader's language.
- `permissions`: seventeen of them, declared in the manifest, shown to the
  reader, and enforced rather than merely displayed.
- `settings`: fields the editor draws as real controls on the plugin's own
  settings page.
- `locales` and `defaultLocale`: a plugin ships translations for whichever
  languages its author wants.
- `entrypoints`: a compiled plugin's executables for `runtime: "process"`, by
  operating system and then, only where it matters, by architecture. A single
  path covers every architecture of a system — a macOS universal binary is one
  file holding both — and a system may pair a shared `default` with a build
  specialised for one architecture. A platform with no build is named to the
  reader; an unknown system or architecture is refused at install time rather
  than silently skipped.

- `serve()`: the request loop, the handshake and the shutdown, so a plugin is
  its handlers and nothing else. Both of the things an author previously had to
  remember produce a program that looks hung rather than one that reports an
  error — a double-clicked executable waiting on stdin, and a plugin that
  outlives the editor because it ignored end of file — so neither is left to be
  remembered.

- `when` on a menu entry: `selection`, `noSelection`, or absent for always.
  Without it every entry a plugin declared was offered at once, including the
  ones that made no sense for what the reader had in front of them.
- `show` and `panel` actions. A few lines are an answer and belong in a small
  window; a document-sized result belongs beside the document, because a window
  over the screen is the one place the reader cannot compare it against
  anything.
- `choices` on `ask`, drawn as chips to press. The box stays, so an answer that
  is not on the list costs nothing but typing it.
- `repository` in the manifest, so an installed plugin's detail page can still
  say where the plugin came from.

- `examples/lua`, `examples/js` and `examples/process`: one complete, runnable
  plugin per runtime, named after the `runtime` value each one declares. The
  only example before was Dart — the runtime an author should reach for last —
  and it sat at the repository root rather than with the others.
- One directory per language under `examples/`, each a complete plugin you copy
  wholesale — including its API module, which ships with your plugin rather
  than being fetched from anywhere:
  `examples/lua`, `examples/js`, `examples/dart`. Named after the language
  because that is what an author chooses; `runtime` in the manifest still names
  how a plugin runs, and the Dart one is a `process` plugin. Before this
  the Dart library sat at the repository root holding a library and an example
  at once, while the scripts were `examples/*-plugin` — three runtimes, three
  namings, and the one to reach for last in the most prominent place.
- All three entrypoints now load their API and call it — `require` for the
  scripts, `import` for the compiled one — and use every capability the editor
  offers once, so the example is the documentation. The scripts previously had
  an editor directive in a comment where the compiled one had a real import,
  which read as three different things rather than one.

- A per-launch token in `MARKTEXT_PLUS_PLUGIN_TOKEN`, replacing the fixed
  `--marktext-plus-plugin-host` argument. The old one could be typed by anyone
  wanting to run a plugin as though the editor had; this one cannot, and it is
  not in argv where `ps` would show it. `serve()` exits 1 without it.

- An API module for each script runtime, `lib/marktext-plus.lua` and
  `lib/marktext-plus.js`, loaded with `require` and shipped with the plugin. It
  wraps the injected `storage` and `t` under one name and adds a constructor
  per action, so a plugin reads as `sdk.show(text, title)` rather than as a
  table literal whose spelling nothing checks. Using it is optional: returning
  the plain table works exactly as well.
- The editor's own test suite checks both modules against what the runtimes
  read, and against each other — an author choosing a language must not be
  choosing what the editor will let them say.

- `require`, in both script runtimes: a plugin may be several files. It
  resolves inside the plugin's own directory and nowhere else, so splitting a
  large plugin up — or shipping a library someone else wrote alongside it —
  costs no access to the rest of the disk.

- `tool/run-js-plugin.mjs`: runs a JavaScript plugin the way the editor does,
  without the editor. The editor's QuickJS only exists inside a built
  application, so a JS plugin could not be tried at all until it was installed.

- The README now says outright that a `process` plugin can be written in
  anything that compiles to an executable — Go, Rust, C++, C#, Python — and
  shows the whole protocol as twenty lines of Python that use nothing from this
  repository. The Dart library was reading as a requirement when it is one
  implementation of four rules.

- `minAppVersion` is enforced. The editor refuses to install a plugin that
  needs a newer one, and refuses to run one already installed, naming both
  versions. It was read and ignored before, which is worse than not having the
  field.
- A Compatibility section saying what the editor will not take away without
  notice, and what happens at 1.0. Every permission name, runtime value, action
  and capability is pinned by a test in the editor's own source: adding to
  those lists is free, removing or renaming one fails.

- `tool/check-translations.mjs`: the translated READMEs are checked against the
  English one for shape — same outline, same code blocks. Eleven copies of a
  document that changes weekly drift by losing a section, not by rewording one,
  and headings are translated so their text cannot be compared.

- `pane`: fill one of the panes around the document. The editor lays the
  document and up to three panes out as a two by two grid — the split it
  already had between source and preview, offered out. `as` draws it the way
  the reader is reading, and `ctx.view` says which that is.
- `append` and a following `ai` on a pane, so a plugin can work through a
  document a block at a time and show each block as it arrives instead of
  sending the whole thing at once and waiting.
- `panels`: contribute a panel to the right-hand side bar. Needs `ui.sidebar`,
  which until now was a permission with nothing behind it. With nothing
  contributed there is no bar at all.
- A section on what this Lua does not do. Four gaps found by one plugin
  splitting a document into paragraphs — `#` on a string, `%s`/`%S`, and two
  forms of `gmatch` — every one of which fails silently.

### Changed

- The manifest schema now validates runtimes, per-platform entrypoints, the
  permission vocabulary, settings fields and contribution points, instead of
  accepting any string.

### Removed

- Dart source as an entrypoint. It needed a Dart SDK on the reader's machine
  that the editor does not install and cannot assume; in a release build it
  launched the editor's own binary and waited for it to speak JSON-RPC.
  Compile it with `dart compile exe` and ship it as `runtime: "process"`.

## [0.1.0] - 2026-09-02

### Added

- Initial MarkText Plus plugin manifest schema.
- JSON-RPC request and response helpers for Dart plugins.
- Protocol and process-isolation documentation.
