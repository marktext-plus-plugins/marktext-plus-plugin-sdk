import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'protocol.dart';

/// The environment variable MarkText Plus hands a plugin its launch token in.
///
/// The token is generated for one launch of one plugin, so it cannot be typed
/// by anyone who was not given it — unlike the fixed argument this replaced,
/// which anybody could pass. It travels in the environment rather than in
/// argv because argv is readable by anything that can run `ps`.
///
/// **This does not stop the executable from being run.** No program can stop a
/// file on the reader's own disk from being executed. What it makes
/// unforgeable is the answer to "did the editor start me".
const launchTokenVariable = 'MARKTEXT_PLUS_PLUGIN_TOKEN';

/// What a plugin does with one request.
///
/// Return the result to send back. Throwing turns into an error response for
/// that request and nothing else: one bad request does not end the plugin.
typedef PluginHandler = FutureOr<Object?> Function(PluginRequest request);

/// Runs a compiled plugin: the handshake, the request loop, and shutdown.
///
/// Written as a runner rather than a page of documentation because the two
/// things that go wrong here are both things an author has to remember to do,
/// and forgetting either produces a program that looks hung rather than one
/// that reports an error.
///
/// - **Started by hand.** The executable sits in a folder the reader can open,
///   so sooner or later it gets double-clicked. Without the handshake there is
///   nothing to notice that by, and the plugin sits waiting on stdin for a
///   request that is never coming.
/// - **The editor going away.** stdin reaching end of file is the only signal
///   there is — a crashed editor sends nothing else — and a plugin that
///   ignores it keeps running with nothing left that knows it exists.
///
/// Returns the exit code. Call it as `exit(await serve(args, handlers))`.
Future<int> serve(
  List<String> arguments,
  Map<String, PluginHandler> handlers, {
  Stream<List<int>>? input,
  IOSink? output,
  IOSink? diagnostics,
  String? name,
  Map<String, String>? environment,
}) async {
  final out = output ?? stdout;
  final err = diagnostics ?? stderr;

  final token = (environment ?? Platform.environment)[launchTokenVariable];
  if (token == null || token.isEmpty) {
    err.writeln(
      '${name ?? 'This program'} is a MarkText Plus plugin. It is started by '
      'the editor and does nothing on its own — install it and use it from '
      'there.',
    );
    return 1;
  }

  final lines = (input ?? stdin)
      .transform(utf8.decoder)
      .transform(const LineSplitter());

  await for (final line in lines) {
    if (line.trim().isEmpty) continue;

    final PluginRequest request;
    try {
      request = PluginRequest.fromLine(line);
    } catch (error) {
      // Not addressed to any id, so there is nothing to answer. Said out loud
      // rather than dropped, because a plugin that silently ignores malformed
      // input is indistinguishable from one that has stopped working.
      err.writeln('ignored an unreadable request: $error');
      continue;
    }

    if (request.method == 'shutdown') {
      out.writeln(successResponse(request.id, null));
      return 0;
    }

    final handler = handlers[request.method];
    if (handler == null) {
      out.writeln(errorResponse(request.id, 'unknown method: ${request.method}'));
      continue;
    }

    try {
      out.writeln(successResponse(request.id, await handler(request)));
    } catch (error) {
      out.writeln(errorResponse(request.id, '$error'));
    }
  }

  // stdin closed: the editor asked for shutdown, or stopped existing.
  return 0;
}
