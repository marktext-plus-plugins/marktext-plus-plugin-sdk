// Are the translated READMEs still the same document as the English one?
//
//     node tool/check-translations.mjs
//
// Headings are translated, so their text cannot be compared — but their
// *shape* can: eleven copies of a document that changes weekly drift by losing
// a section, not by rewording one. This compares the outline (how many
// headings, at which levels, in which order) and the fenced code blocks, which
// are not translated at all and so must match exactly.
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

const root = new URL('..', import.meta.url).pathname;
const outline = (text) =>
  text.split('\n').filter((l) => /^#{1,6} /.test(l)).map((l) => l.match(/^#+/)[0].length);
const fences = (text) => (text.match(/^ *```/gm) || []).length;

const english = readFileSync(join(root, 'README.md'), 'utf8');
const want = { outline: outline(english), fences: fences(english) };

const dir = join(root, 'docs/i18n');
const files = readdirSync(dir).filter((f) => f.endsWith('.md')).sort();

const expected = [
  'README_ar-SA.md', 'README_de-DE.md', 'README_es-ES.md', 'README_fr-FR.md',
  'README_it-IT.md', 'README_ja-JP.md', 'README_ko-KR.md', 'README_pt-BR.md',
  'README_pt-PT.md', 'README_ru-RU.md', 'README_zh-CN.md',
];

let ok = true;
for (const name of expected) {
  if (!files.includes(name)) {
    console.log(`  XX  ${name} is missing`);
    ok = false;
    continue;
  }
  const text = readFileSync(join(dir, name), 'utf8');
  const got = { outline: outline(text), fences: fences(text) };
  const problems = [];
  if (got.outline.length !== want.outline.length) {
    problems.push(
      `${got.outline.length} headings, English has ${want.outline.length}`);
  } else if (got.outline.join() !== want.outline.join()) {
    problems.push('headings are at different levels than the English ones');
  }
  if (got.fences !== want.fences) {
    problems.push(`${got.fences / 2} code blocks, English has ${want.fences / 2}`);
  }
  if (text.includes('](docs/i18n/')) {
    problems.push('links to docs/i18n as if it were the English README');
  }
  console.log(problems.length ? `  XX  ${name}: ${problems.join('; ')}`
                              : `  OK  ${name}`);
  if (problems.length) ok = false;
}

const extra = files.filter((f) => !expected.includes(f));
if (extra.length) {
  console.log(`  XX  not a language this project ships: ${extra.join(', ')}`);
  ok = false;
}

if (!ok) console.log('\nA translation is not the same document as README.md.');
process.exit(ok ? 0 : 1);
