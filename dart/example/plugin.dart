import 'dart:io';

import 'package:marktext_plus_plugin_sdk/marktext_plus_plugin_sdk.dart';

/// The whole of a compiled plugin. Build it with:
///
///     dart compile exe example/plugin.dart -o bin/linux-x64/plugin
///
/// `exe` is the only shape a Dart plugin can take: `dart compile` produces
/// executables, snapshots, JavaScript and Wasm, and nothing that a host can
/// load as a `.so` or `.dll`.
Future<void> main(List<String> args) async {
  exit(await serve(args, {
    'shout': (request) =>
        (request.params['text'] as String? ?? '').toUpperCase(),
  }, name: 'plugin'));
}
