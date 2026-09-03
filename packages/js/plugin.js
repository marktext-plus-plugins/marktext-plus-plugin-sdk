/// <reference path="./sdk/marktext-plus.d.ts" />
//
// The reference above is for your editor, not for the runtime: it is what
// makes `storage`, `t` and `ctx` complete and typo-check. Those are injected
// by the editor before this file is read, so there is nothing to load them
// from. `require` below is a different thing: it loads this plugin's own files.
//
// The same plugin as ../lua, in JavaScript. Same manifest, same behaviour;
// pick the language you would rather write.

// require(): one of this plugin's own files. A plugin is not limited to one.
const prompt = require("lib/prompt");

const LANGUAGES = ["English", "简体中文", "日本語", "Deutsch", "Français"];

/** @param {PluginContext} ctx @returns {PluginAction} */
function on_command(ctx) {
  // t(): your own strings, in the reader's language. Declared in `locales`.
  if (!ctx.selection && ctx.command === "summarise.selection") {
    return { notify: t("error.empty") };              // needs ui.notifications
  }

  // ask + choices: the usual answers to press, and anything typed is taken as
  // it stands. storage: your own settings, in your own directory.
  if (ctx.answer == null) {
    return {
      ask: t("ask.language"),
      default: storage.get("language") || "English",  // needs storage.local
      choices: LANGUAGES,
    };
  }
  storage.set("language", ctx.answer);

  const text =
    ctx.command === "summarise.document"
      ? ctx.document                                   // needs document.read
      : ctx.selection;

  // ai: the editor calls the model the reader configured and comes back to
  // on_result. Your prompt, unedited; the API key never reaches this script.
  return { ai: prompt.summarise(text, ctx.answer) };   // needs ai.chat
}

/** @param {PluginContext} ctx @param {string} result @returns {PluginAction} */
function on_result(ctx, result) {
  // show for something small, panel for something document-sized.
  if (ctx.command === "summarise.document") {
    return { panel: result, title: ctx.answer };
  }
  return { show: result, title: ctx.answer };
}
