# -*- coding: utf-8 -*-
"""Post-process every note-*.html: convert leftover markdown inline format
into <strong>/<em>, in place, without touching the source .md files.

Rules:
- Operate only inside <div class="article-content"> ... </article>.
- Protect math ($...$, $$...$$) so asterisks inside formulas stay verbatim.
- **bold** -> <strong>, *italic* -> <em> (never a '<p>/<li>/<blockquote>'
  boundary inside one match; <br> crossing is allowed).
- Idempotent; safe to re-run after regenerating pages.
Run _build_search_index.py afterwards.
"""
import io, os, re, glob

OUT = os.path.dirname(os.path.abspath(__file__))
_tokens = []

def protect_math(s):
    def repl(m):
        _tokens.append(m.group(0))
        return '\x00%d\x00' % (len(_tokens) - 1)
    return re.sub(r'\$\$[\s\S]*?\$\$|\$[^$\n]+?\$', repl, s)

BOUND = re.compile(r'<(?:/p|\s*p[\s>]|/h[1-6]|[hb]1|<h[1-6][\s>]|/li|/blockquote|blockquote[\s>]|/ol|/ul|ol[\s>]|ul[\s>])', re.I)

def unbound(m):
    seg = m.group(1)
    if re.search(r'<(?:/?p[\s>]|/?h[1-6]|/?li|/?blockquote|/?ol|/?ul|[a-z]+ )', seg, re.I):
        return m.group(0)
    return '<strong>' + seg + '</strong>'

def make_italic(m):
    seg = m.group(1)
    if re.search(r'<(?:/?p[\s>]|/?h[1-6]|/?li|/?blockquote|/?ol|/?ul|[a-z]+ )', seg, re.I):
        return m.group(0)
    return '<em>' + seg + '</em>'

def format_region(region):
    _tokens.clear()
    region = protect_math(region)
    before = region
    while re.search(r'\*\*[^<]*(?:<(?!/p|/h[1-6]|/li|/blockquote|/ol|/ul|p[\s>]|h[1-6][\s>]|li[\s>]|blockquote[\s>]|ol[\s>]|ul[\s>])[^<]*)*?\*\*', region):
        twice = re.sub(r'\*\*(.+?)\*\*', unbound, region, flags=re.S, count=1)
        if twice == region:
            break
        region = twice
    region = re.sub(r'(?<![\w*$_])\*(?![\s*])([^*\n]+?)(?<![\s$_])\*(?!\*)', make_italic, region, flags=re.S)
    region = re.sub(r'\x00(\d+)\x00', lambda m: _tokens[int(m.group(1))], region)
    return region if region != before else None

body_span = re.compile(r'(<div class="article-content">\n[\s\S]*?\n    </div>\n  </article>)', re.S)

changed_files, report = [], {}
for path in glob.glob(os.path.join(OUT, 'note-*.html')):
    with io.open(path, 'r', encoding='utf-8') as f:
        page = f.read()
    m = body_span.search(page)
    if not m:
        continue
    new_region = format_region(m.group(0))
    if new_region:
        page = page[:m.start()] + new_region + page[m.end():]
        with io.open(path, 'w', encoding='utf-8') as f:
            f.write(page)
        changed_files.append(os.path.basename(path))
        report[os.path.basename(path)] = (
            len(re.findall(r'<strong>', new_region)) - len(re.findall(r'<strong>', m.group(0))),
            len(re.findall(r'<em>', new_region)) - len(re.findall(r'<em>', m.group(0))))

for k in sorted(report):
    s, e = report[k]
    print('%-32s +strong=%-3s +em=%s' % (k, s, e))
print('changed %d files' % len(changed_files))
