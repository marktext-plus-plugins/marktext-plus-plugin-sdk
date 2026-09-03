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
- `entrypoints`: one executable per platform for `runtime: "process"`, keyed
  `os-arch`. A platform with no build is named to the reader.

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
