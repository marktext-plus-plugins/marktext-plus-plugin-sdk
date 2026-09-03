# Changelog

## [0.2.0] - 2026-09-03

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

- `examples/lua-plugin` and `examples/js-plugin`: complete, runnable plugins,
  the same one written in each language. The only example before was Dart —
  the one runtime an author should reach for last.

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
