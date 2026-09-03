# Compiled plugin example

The same plugin as [`../lua`](../lua) and [`../js`](../js), as a compiled
executable. **Reach for this last**: it needs a toolchain, it has to be built
once per platform you support, and it runs as a separate process. A script does
not.

**Dart is not required.** The editor starts a program and speaks JSON-RPC to it
over stdin and stdout; it never learns what produced the program. Go, Rust,
C++, C#, a statically linked Python — anything that compiles to an executable
works, and the whole contract is four rules, written out in the main
[README](../../README.md#what-is-in-this-repository). This example is in Dart
because the editor is, so `dart compile exe` was the shortest way to have a
working one.

## Build

```
dart pub get
dart compile exe plugin.dart -o bin/linux/plugin
```

`exe` is the only shape a Dart plugin can take. `dart compile` produces
executables, snapshots, JavaScript and Wasm — there is no subcommand that
produces a `.so` or `.dll` a host could load.

Repeat on each platform you want to support, into the paths the manifest names:

| Platform | Output |
|---|---|
| Linux | `bin/linux/plugin` |
| macOS | `bin/macos/plugin` |
| Windows x64 | `bin\windows-x64\plugin.exe` |
| Windows arm64 | `bin\windows-arm64\plugin.exe` |

A platform with no build there is named to the reader rather than guessed at.

## Check it before you ship it

```
echo | ./bin/linux/plugin
```

should print what it is and exit 1: nothing gave it a launch token, so the
editor did not start it.

## Note on `manifest.json`

It names `entrypoints`, not `entrypoint`, and the architecture layer is
optional: `linux` and `macos` above are one path each — the same executable for
every architecture — while `windows` names one per architecture.
