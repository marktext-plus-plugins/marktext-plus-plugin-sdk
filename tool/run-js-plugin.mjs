// Runs a JavaScript plugin the way the editor does, without the editor.
//
//     node tool/run-js-plugin.mjs packages/js
//
// The editor interprets a JS plugin with QuickJS, which only exists inside a
// built application — so this stands in: the same injected globals, the same
// require that reaches only inside the plugin directory, and the same two
// entry points. It is how the example in packages/js is checked, and it works
// on any plugin of your own.
import { readFileSync } from 'node:fs';
import { join, sep } from 'node:path';
import vm from 'node:vm';

const dir = process.argv[2];
const store = { language: 'English' };
const strings = JSON.parse(readFileSync(join(dir, 'manifest.json'), 'utf8'))
  .locales['zh'];

const loaded = {};
function makeRequire(context) {
  return function require(name) {
    if (name.includes('..') || name.startsWith('.')) throw new Error('refused');
    if (loaded[name]) return loaded[name];
    const file = join(dir, name.split('/').join(sep) + '.js');
    const module = { exports: {} };
    vm.runInContext(
      `(function (module, exports, require) {${readFileSync(file, 'utf8')}})`,
      context,
    )(module, module.exports, require);
    loaded[name] = module.exports;
    return module.exports;
  };
}

const sandbox = {
  storage: {
    get: (k) => (k in store ? store[k] : null),
    set: (k, v) => { store[k] = String(v); },
  },
  t: (k) => (k in strings ? strings[k] : k),
};
const context = vm.createContext(sandbox);
sandbox.require = makeRequire(context);
vm.runInContext(readFileSync(join(dir, 'plugin.js'), 'utf8'), context);

const call = (fn, ...args) =>
  vm.runInContext(`(${fn})`, context)(...args);

const check = (label, got, want) => {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  console.log(`  ${ok ? 'OK ' : 'XX '} ${label}`);
  if (!ok) console.log(`      got  ${JSON.stringify(got)}\n      want ${JSON.stringify(want)}`);
  return ok;
};

let pass = true;
// Anything the plugin throws is a failure of the plugin, not of this script:
// reported as such rather than as a Node stack trace.
const guard = (label, fn) => {
  try {
    return fn();
  } catch (error) {
    console.log(`  XX  ${label}: ${error.message}`);
    pass = false;
    return undefined;
  }
};

pass &= check('nothing selected -> notify, in the reader language',
  guard('on_command', () => call('on_command',
    { command: 'summarise.selection', selection: '', document: '', answer: null })),
  { notify: '请先选中一些文本' });

const ask = guard('ask', () => call('on_command',
  { command: 'summarise.selection', selection: 'hi', document: '', answer: null })) ?? {};
pass &= check('asks with the stored default and the offered choices',
  { ask: ask.ask, default: ask.default,
    first: (ask.choices ?? [])[0], n: (ask.choices ?? []).length },
  { ask: '用哪种语言总结？', default: 'English', first: 'English', n: 5 });

const ai = guard('ai', () => call('on_command',
  { command: 'summarise.selection', selection: 'hello', document: '', answer: '日本語' })) ?? {};
pass &= check('builds the prompt and remembers the language',
  { hasLang: (ai.ai ?? '').includes('日本語'),
    hasText: (ai.ai ?? '').includes('hello'), stored: store.language },
  { hasLang: true, hasText: true, stored: '日本語' });

pass &= check('a selection comes back small',
  guard('show', () => call('on_result',
    { command: 'summarise.selection', answer: '日本語' }, '- a')),
  { show: '- a', title: '日本語' });
pass &= check('a document comes back beside the text',
  guard('panel', () => call('on_result',
    { command: 'summarise.document', answer: '日本語' }, '- a')),
  { panel: '- a', title: '日本語' });

if (!pass) console.log('\nThe plugin did not behave as the editor expects.');
process.exit(pass ? 0 : 1);
