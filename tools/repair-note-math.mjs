// Run after exporting notes: node tools/repair-note-math.mjs
// Verify committed exports: node tools/repair-note-math.mjs --check
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const localMathJax = 'assets/vendor/mathjax/tex-svg-full-3.2.2.js';

function escapeMath(text) {
  // Keep existing HTML entities; protect TeX comparisons and matrix separators
  // from the browser's HTML parser. This also makes repeated repairs harmless.
  return text.replace(/&(?!#\d+;|#x[\da-f]+;|[a-z][a-z\d]+;)/gi, '&amp;')
    .replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

export function repairContent(content) {
  // The exporter wrapped each source line in <p>, including lines in $$...$$.
  // MathJax requires both delimiters to have the same HTML parent.
  const displayFixed = content.replace(/(?<!\\)\$\$([\s\S]*?)(?<!\\)\$\$/g,
    (match, display) => {
      const closesQuote = /<\/blockquote>/.test(display);
      const tex = display.replace(/<\/?p\s*>|<br\s*\/?>|<\/blockquote>/gi, '\n')
        .replace(/\r?\n(?:[ \t]*\r?\n)+/g, '\n');
      // A quote can end just after the opening $$ in legacy exports. Close it
      // before the formula and reuse the closing </p> following the final $$.
      const prefix = closesQuote ? '</blockquote>\n<p>' : '';
      return prefix + '$$' + escapeMath(tex) + '$$';
    });
  // Inline math must never pair dollar signs across HTML elements. In
  // particular, currency such as "$100" must not consume the next paragraph.
  return displayFixed.split(/(<\/?(?:p|blockquote|br|h[1-6]|div|span|mark|u|b|strong|em|i|a|ul|ol|li|pre|code|img|hr)(?=[\s/>])[^>]*>)/gi)
    .map((part, index) => index % 2 ? part : part.replace(
      /(?<![\\$])\$(?!\$)([^$\r\n]*?)(?<!\\)\$(?!\$)/g,
      (match, tex) => '$' + escapeMath(tex) + '$'))
    .join('');
}

export function repairPage(page) {
  const start = page.indexOf('<div class="article-content">');
  if (start === -1) return page;
  const end = page.indexOf('\n    </div>', start);
  if (end === -1) throw new Error('Cannot find end of article-content');
  page = page.slice(0, start) + repairContent(page.slice(start, end)) + page.slice(end);
  return page.replace(
    /<script src="https:\/\/cdn\.jsdelivr\.net\/npm\/mathjax@[^" ]+" async><\/script>/g,
    `<script src="${localMathJax}" defer></script>`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const check = process.argv.includes('--check');
  let changed = 0;
  for (const file of fs.readdirSync(root).filter(name => /^note-.*\.html$/.test(name))) {
    const target = path.join(root, file);
    const before = fs.readFileSync(target, 'utf8');
    const after = repairPage(before);
    if (before !== after) {
      changed++;
      console.log(`${check ? 'Needs repair' : 'Repaired'}: ${file}`);
      if (!check) fs.writeFileSync(target, after);
    }
  }
  console.log(`${changed} note pages ${check ? 'need repair' : 'updated'}.`);
  if (check && changed) process.exitCode = 1;
}
