// A complete JavaScript plugin. Every capability the editor offers is used
// once. The same plugin as ../lua — same manifest, same behaviour; pick the
// language you would rather write.
//
// Two files ship: this one and lib/marktext-plus.js, which `require` loads
// from this plugin's own directory. A plugin is not limited to those two —
// `require` will load any file you put beside them.
const sdk = require("lib/marktext-plus");

const LANGUAGES = ["English", "简体中文", "日本語", "Deutsch", "Français"];

/** @param ctx {{command: string, selection: string, document: string, answer: string|null}} */
function on_command(ctx) {
  // sdk.t(): your own strings, in the reader's language, from `locales`.
  if (!ctx.selection && ctx.command === "summarise.selection") {
    return sdk.notify(sdk.t("error.empty"));         // needs ui.notifications
  }

  // sdk.ask(): the usual answers to press, and anything typed is taken as it
  // stands. sdk.storage: your own settings, in your own directory.
  if (ctx.answer == null) {
    return sdk.ask(sdk.t("ask.language"), {
      default: sdk.storage.get("language") || "English", // needs storage.local
      choices: LANGUAGES,
    });
  }
  sdk.storage.set("language", ctx.answer);

  const text =
    ctx.command === "summarise.document"
      ? ctx.document                                    // needs document.read
      : ctx.selection;

  // sdk.ai(): the editor calls the model the reader configured and comes back
  // to on_result. Your prompt, unedited; the API key never reaches this script.
  return sdk.ai(
    `Summarise the Markdown below in ${ctx.answer}, in three bullet points. ` +
      `Return only the bullets.\n\n${text}`
  );                                                    // needs ai.chat
}

/** @param ctx {object} @param result {string} what the model replied */
function on_result(ctx, result) {
  // show for something small, panel for something document-sized.
  if (ctx.command === "summarise.document") {
    return sdk.panel(result, ctx.answer);
  }
  return sdk.show(result, ctx.answer);
}
