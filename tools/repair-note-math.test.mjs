import { test } from 'node:test';
import assert from 'node:assert/strict';
import { repairContent } from './repair-note-math.mjs';

test('rejoins display delimiters and preserves TeX matrix row breaks', () => {
  const broken = '<p>$$</p>\n<p>\\begin{matrix}a & b \\\\</p>\n<p>c & d\\end{matrix}</p>\n<p>$$</p>';
  const fixed = repairContent(broken);
  assert.equal((fixed.match(/<p>/g) || []).length, 1);
  assert.match(fixed, /a &amp; b \\\\/);
  assert.match(fixed, /c &amp; d\\end\{matrix\}/);
  assert.equal(repairContent(fixed), fixed);
});

test('moves an intervening quote boundary before the complete formula', () => {
  const fixed = repairContent('<blockquote>Proof<br>$$</blockquote>\n<p>x < y</p>\n<p>$$</p>');
  assert.match(fixed, /Proof<br><\/blockquote>\n<p>\$\$/);
  assert.match(fixed, /x &lt; y/);
  assert.doesNotMatch(fixed.match(/\$\$([\s\S]*?)\$\$/)[1], /<\/?(?:p|blockquote)>/);
  assert.equal(repairContent(fixed), fixed);
});

test('protects inline comparisons without changing prose or escaped dollars', () => {
  const fixed = repairContent('<p>Use $x<y$ and $a &amp; b$, price \\$5.</p>');
  assert.equal(fixed, '<p>Use $x&lt;y$ and $a &amp; b$, price \\$5.</p>');
});

test('currency cannot escape markup or consume math in the following paragraph', () => {
  const source = '<blockquote>Lend $100.<br>Return 108.</blockquote>\n<h5>Interest</h5>\n<p>Rate $i>0$.</p>';
  assert.equal(repairContent(source), '<blockquote>Lend $100.<br>Return 108.</blockquote>\n<h5>Interest</h5>\n<p>Rate $i&gt;0$.</p>');
});

test('comparison variables that share HTML tag names remain math', () => {
  assert.equal(repairContent('<p>$x<a$ and $a<b$</p>'), '<p>$x&lt;a$ and $a&lt;b$</p>');
});
