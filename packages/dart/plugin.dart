import 'dart:io';

// A real import, unlike the script plugins: a process plugin sits on the other
// side of a pipe, and this is the library that implements it. `sdk/` beside
// this file is that library; `pubspec.yaml` points at it.
import 'package:marktext_plus_plugin_sdk/marktext_plus_plugin_sdk.dart';

/// The compiled form of the same plugin as ../lua and ../js.
///
/// **Reach for this last.** It needs a toolchain, it is built once per
/// platform, and it runs as a separate process. A script needs none of that.
///
/// Build:
///
///     dart pub get
///     dart compile exe plugin.dart -o bin/linux/plugin
///
/// `exe` is the only shape a Dart plugin can take: `dart compile` produces
/// executables, snapshots, JavaScript and Wasm, and nothing a host can load as
/// a `.so` or `.dll`.
Future<void> main(List<String> args) async {
  // serve() refuses to run unless the editor started it, so double-clicking
  // this executable prints a line saying what it is and exits. It also returns
  // when stdin closes, which is what happens if the editor goes away.
  exit(await serve(args, {
    'summarise': (request) {
      final text = request.params['text'] as String? ?? '';
      final language = request.params['language'] as String? ?? 'English';
      return {
        'prompt': 'Summarise the Markdown below in $language, in three '
            'bullet points. Return only the bullets.\n\n$text',
      };
    },
  }, name: 'plugin'));
}
