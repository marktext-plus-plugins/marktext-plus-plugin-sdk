// The same plugin as examples/lua-plugin, in JavaScript.
//
// Same two files, same protocol, same result. The editor does not care which
// of the two languages an author picked — pick the one you would rather write.

function on_command(ctx) {
  if (!ctx.selection) {
    return { notify: t("error.empty") };
  }

  // Asking is an action, not a call: the script cannot block while the reader
  // thinks, so it hands the question back and is called again with the answer.
  if (ctx.answer == null) {
    return {
      ask: t("ask.style"),
      default: storage.get("style") || "LOUD",
      choices: ["LOUD", "louder", "LOUDEST"],
    };
  }
  storage.set("style", ctx.answer);

  let shouted = ctx.selection.toUpperCase();
  if (ctx.answer === "LOUDEST") shouted += "!!!";

  return { show: shouted, title: ctx.answer };
}
