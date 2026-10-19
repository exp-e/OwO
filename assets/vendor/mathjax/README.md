MathJax 3.2.2, `es5/tex-svg-full.js`, distributed under the Apache 2.0 license (see LICENSE).

Source: https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-svg-full.js

The full TeX/SVG bundle includes TeX extensions so ordinary formula rendering does not require a third-party CDN. Keep the version pinned when updating it.

After exporting notes, run `node tools/repair-note-math.mjs` to join formulas split across paragraph or quote boundaries and escape HTML-sensitive TeX. Run `node tools/repair-note-math.mjs --check` and `node --test tools/repair-note-math.test.mjs` to validate the exports.
