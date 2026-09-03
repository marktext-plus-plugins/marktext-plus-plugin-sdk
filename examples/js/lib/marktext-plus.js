// The MarkText Plus API, as a module you require.
//
// The editor injects `storage`, `t` and `require` as globals before your
// plugin is read. This wraps them in one named thing, and adds a constructor
// for each action the editor understands, so a plugin reads as calls rather
// than as object literals whose spelling nothing checks.
//
// Ships with your plugin: it is ordinary JavaScript and `require` loads it
// from your own directory.

module.exports = {
  /**
   * Your own settings, in your own directory. Strings only.
   * Needs the `storage.local` permission.
   */
  storage: storage,

  /**
   * Your own string in the reader's language, from `locales` in the manifest.
   * An unknown key comes back as itself.
   * @param {string} key @returns {string}
   */
  t: function (key) {
    return t(key);
  },

  /**
   * Ask the reader something. The command runs again with `ctx.answer` set.
   * @param {string} label
   * @param {{ default?: string, choices?: string[] }} [options]
   */
  ask: function (label, options) {
    options = options || {};
    return { ask: label, default: options.default, choices: options.choices };
  },

  /**
   * Send a prompt to the model the reader configured. Needs `ai.chat`.
   * The reply arrives in `on_result`. Your API key never reaches this script.
   * @param {string} prompt
   */
  ai: function (prompt) {
    return { ai: prompt };
  },

  /** One answer, in a small window with a copy button.
   * @param {string} text @param {string} [title] */
  show: function (text, title) {
    return { show: text, title: title };
  },

  /** One answer, in a panel beside the document, for document-sized results.
   * @param {string} text @param {string} [title] */
  panel: function (text, title) {
    return { panel: text, title: title };
  },

  /** Say one line to the reader and stop. Needs `ui.notifications`.
   * @param {string} message */
  notify: function (message) {
    return { notify: message };
  },

  /** Show two texts side by side. Nothing is written to the document.
   * @param {string} original @param {string} result */
  diff: function (original, result) {
    return { diff: { original: original, result: result } };
  },

  /** Replace the selection. Needs `document.write`. @param {string} text */
  replace: function (text) {
    return { replace: text };
  },

  /** Do nothing. */
  nothing: function () {
    return {};
  },
};
