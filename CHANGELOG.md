# Changelog

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
