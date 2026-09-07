# Changelog

## [Unreleased]

### Added

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

### Added

- The safety rules now state the limits an installed ZIP has to fit: 64 MB for
  the archive, 10000 entries, 256 MB unpacked. They were added to the editor
  today (a ZIP was free to claim it unpacked to gigabytes, and to mean it), and
  an author who packages three platforms' executables should hear the number
  from here rather than from a failed install.

### Fixed

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
