"""Publish the public cold-boson note using the established note converter."""
import ast
import html
import json
import os
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path(r'X:\md4obsd\玻色冷原子笔记.md')
PICS = SOURCE.parent / 'pics'
SLUG = 'note-cold-bosons'
TITLE = '玻色冷原子笔记'
DATE = '2026-11-24'
EXCERPT = '光学晶格中的超冷玻色原子读书笔记：玻色–哈伯德模型、Wannier 函数、跃迁耦合强度，以及超流态与莫特绝缘态的量子相变。'

# Load converter definitions without running the encrypted-note publisher.
tree = ast.parse((ROOT / '_gen_quantum_expander.py').read_text(encoding='utf-8'))
definitions = ast.Module(body=[node for node in tree.body if isinstance(node, ast.FunctionDef)], type_ignores=[])
scope = dict(io=None, os=os, re=re, shutil=shutil, pics=str(PICS),
             assets_dir=str(ROOT / 'assets'), headings=[], _mtokens=[])
exec(compile(definitions, '<note converter>', 'exec'), scope)
raw = SOURCE.read_text(encoding='utf-8')

# Preserve the Markdown comparison table; the older converter handles prose,
# headings, lists, images and complete math blocks.
tables = []
def table(match):
    rows = [line.strip().strip('|').split('|') for line in match.group().strip().splitlines()]
    cells = lambda row, tag: ''.join('<{0}>{1}</{0}>'.format(tag, scope['format_inline'](html.escape(c.strip()))) for c in row)
    rendered = '<div class="table-scroll"><table><thead><tr>' + cells(rows[0], 'th') + '</tr></thead><tbody>'
    rendered += ''.join('<tr>' + cells(row, 'td') + '</tr>' for row in rows[2:])
    tables.append(rendered + '</tbody></table></div>')
    return 'COLD_BOSON_TABLE_' + str(len(tables) - 1) + '\n'
raw = re.sub(r'(?m)^\|[^\n]+\n\|[-:| ]+\n(?:\|[^\n]+\n?)+', table, raw)
body = scope['md_to_html'](raw)
for i, rendered in enumerate(tables):
    body = body.replace('<p>COLD_BOSON_TABLE_' + str(i) + '</p>', rendered)
body = body.replace('&lt;u&gt;', '<u>').replace('&lt;/u&gt;', '</u>')

images = re.findall(r'!\[\[([^\]|]+)', raw)
for image in images:
    assert (PICS / image).is_file(), image
    shutil.copy2(PICS / image, ROOT / 'assets' / image)
cover = 'figure_2.png'
page = (ROOT / 'note-qecc.html').read_text(encoding='utf-8')
page = re.sub(r'<title>.*?</title>', '<title>' + TITLE + '</title>', page, count=1)
page = page.replace('2026-04-15', DATE)
page = page.replace('<span class="cat-tag">数学</span>', '<span class="cat-tag">物理</span>')
page = re.sub(r'<img class="article-cover"[^>]+>', '<img class="article-cover" src="assets/' + cover + '" alt="' + TITLE + '">', page, count=1)
page = re.sub(r'(<h1 class="article-title" id="article-title">).*?(</h1>)', lambda m: m[1] + TITLE + m[2], page, count=1)
page = re.sub(r'\n *<a href="https://[^"]*zhihu\.com[^"]*"[^>]*>.*?</a>', '', page, count=1)
page = re.sub(r'(<div class="article-content">\n).*?(\n    </div>\n  </article>)', lambda m: m[1] + body + m[2], page, count=1, flags=re.S)
toc = '<li class="toc-main"><a href="#article-title">' + TITLE + '</a></li>\n'
toc += '\n'.join('<li' + (' class="sub"' if level > 1 else '') + '><a href="#' + sid + '">' + title + '</a></li>' for sid, level, title in scope['headings'])
page = re.sub(r'(<ul class="toc-list(?: mobile-toc-list)?">).*?(</ul>)', lambda m: m[1] + '\n' + toc + '\n' + m[2], page, flags=re.S)
page = page.replace('</style>', '.table-scroll{overflow-x:auto;margin:18px 0} .article-content table{border-collapse:collapse;width:100%;min-width:480px} .article-content th,.article-content td{border:1px solid var(--border-soft);padding:8px;text-align:left}\n</style>', 1)
(ROOT / (SLUG + '.html')).write_text(page, encoding='utf-8')

index_path = ROOT / 'index.html'
index = index_path.read_text(encoding='utf-8')
card = '<a class="note-card" data-cat="physics" href="' + SLUG + '.html">\n'
card += '<img class="note-card-cover" src="assets/' + cover + '" alt="' + TITLE + '">\n<div class="note-card-body">\n'
card += '<div class="note-card-title">' + TITLE + '</div>\n'
card += '<div class="note-card-meta"><span class="cat-tag">物理</span><span><i class="far fa-calendar"></i> ' + DATE + '</span></div>\n'
card += '<div class="note-card-excerpt">' + EXCERPT + '</div>\n</div>\n</a>'
if 'href="' + SLUG + '.html"' not in index:
    index = index.replace('<div class="note-list" id="noteList">', '<div class="note-list" id="noteList">\n' + card, 1)
cats = re.findall(r'<a class="note-card" data-cat="([^"]+)"', index)
for cat in ['all', 'math', 'physics', 'other', 'locked']:
    count = sum(c != 'locked' for c in cats) if cat == 'all' else cats.count(cat)
    index = re.sub(r'(data-cat="' + cat + r'">[^<]*<span class="count">)\d+', lambda m: m[1] + str(count), index, count=1)
index_path.write_text(index, encoding='utf-8')

# Update only this public record, leaving locked-note metadata untouched.
search_path = ROOT / 'search-index.js'
search = search_path.read_text(encoding='utf-8')
prefix, data = search.split('window.NOTE_INDEX = ', 1)
records = json.loads(data.strip().rstrip(';'))
record = dict(t=TITLE, u=SLUG + '.html', c='物理', d=DATE, x=EXCERPT,
              k='cold bosons', b=re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', body))).strip())
records = [record] + [r for r in records if r['u'] != record['u']]
search_path.write_text(prefix + 'window.NOTE_INDEX = ' + json.dumps(records, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')
print('Published:', SLUG, '| images:', len(images), '| tables:', len(tables), '| sections:', len(scope['headings']))
