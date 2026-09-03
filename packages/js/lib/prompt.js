// A second file, to show that a plugin need not be one.
//
// Loaded with `require("lib/prompt")`: the name is a name, not a path, and it
// resolves inside this plugin's directory and nowhere else.

/**
 * The prompt this plugin sends. Kept here so it can be read on its own.
 * @param {string} text @param {string} language @returns {string}
 */
function summarise(text, language) {
  return (
    `Summarise the Markdown below in ${language}, in three bullet points. ` +
    `Return only the bullets.\n\n${text}`
  );
}

module.exports = { summarise };
