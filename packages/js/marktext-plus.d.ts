/**
 * Type declarations for a MarkText Plus JavaScript plugin.
 *
 * **Not shipped with your plugin, and not imported by it.** The editor injects
 * `storage`, `t` and the context; there is nothing to require at runtime. This
 * file exists so your editor can complete those names and tell you when you
 * have misspelled one — `sotrage.get` is otherwise a mistake you find when a
 * reader clicks the menu entry.
 *
 * Point your editor at it, for example with a jsconfig.json beside plugin.js:
 *
 *     { "compilerOptions": { "checkJs": true }, "include": ["plugin.js", "marktext-plus.d.ts"] }
 */

/** What the editor tells a plugin about the moment its command fired. */
interface PluginContext {
  /** The `id` of the menu entry or command the reader chose. */
  readonly command: string;
  /** The selected text; `""` when nothing is selected. */
  readonly selection: string;
  /** The whole document. */
  readonly document: string;
  /** What the reader typed last time you asked, otherwise null. */
  readonly answer: string | null;
}

/** Ask the reader something, then run the command again with the answer. */
interface AskAction {
  ask: string;
  default?: string;
  /** Answers offered as chips. Anything typed instead is used as it stands. */
  choices?: string[];
}

/** Send a prompt to the model the reader configured. Needs `ai.chat`. */
interface AiAction {
  ai: string;
}

/** One answer, in a small window with a copy button. */
interface ShowAction {
  show: string;
  title?: string;
}

/** One answer, in a panel beside the document. For document-sized results. */
interface PanelAction {
  panel: string;
  title?: string;
}

/** Say something to the reader and stop. */
interface NotifyAction {
  notify: string;
}

/** Show two texts side by side. Nothing is written to the document. */
interface DiffAction {
  diff: { original: string; result: string };
}

/** Replace the selection. Needs `document.write`. */
interface ReplaceAction {
  replace: string;
}

type PluginAction =
  | AskAction
  | AiAction
  | ShowAction
  | PanelAction
  | NotifyAction
  | DiffAction
  | ReplaceAction
  | null;

/**
 * Your own settings, in your own directory. Strings only.
 * Needs the `storage.local` permission.
 */
declare const storage: {
  get(key: string): string | null;
  set(key: string, value: string | null): void;
};

/**
 * Your own string in the reader's language, from `locales` in the manifest.
 * An unknown key comes back as itself, so a missing translation shows a key
 * rather than an empty menu entry.
 */
declare function t(key: string): string;

/** Called when one of your menu entries or commands fires. */
declare function on_command(ctx: PluginContext): PluginAction;

/** Called with the model's reply, after you returned an `ai` action. */
declare function on_result(ctx: PluginContext, result: string): PluginAction;
