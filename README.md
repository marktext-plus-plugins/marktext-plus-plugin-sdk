# MarkText Plus Plugin SDK
Main application: [MarkText Plus](https://github.com/SugarFatFree/marktext-plus)


SDK and protocol reference for MarkText Plus plugins.

Plugins run as separate processes and communicate with the editor over JSON-RPC 2.0 messages on stdin/stdout. A plugin must never assume that the editor process shares its memory or event loop.

## Lifecycle

1. MarkText Plus reads `manifest.json` without starting the plugin.
2. The host starts the declared `entrypoint` only when the plugin is needed.
3. The host sends `initialize` with protocol and app information.
4. The host sends capability-specific `execute` requests.
5. The host may send `shutdown`; a timeout or crash terminates only the plugin process.

Every request is one JSON object per line. Responses must echo the numeric request `id`.

## Manifest

See [`schema/manifest.schema.json`](schema/manifest.schema.json). A minimal plugin contains:

```json
{
  "id": "com.example.my-plugin",
  "name": "My Plugin",
  "version": "1.0.0",
  "entrypoint": "bin/plugin",
  "minAppVersion": "1.6.0",
  "capabilities": ["command"]
}
```

## Safety rules

- Do not execute Dart code inside the editor process.
- Keep stdout for protocol responses; write diagnostics to stderr.
- Treat all host input as untrusted and validate it before use.
- Keep operations bounded; the host enforces request timeouts.
- Never persist API keys in the plugin directory or manifest.

The SDK is MIT licensed.
