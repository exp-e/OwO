# -*- coding: utf-8 -*-
"""Publish 'Quantum Expander笔记.md' (X:\\md4obsd) as note-quantum-expander.html.
- Body is converted by the same rules as _gen_articles.py (text kept verbatim).
- Cover: pics/aixyx.jpg ; body image: pics/expander.png -> assets/
- Category: math (数学), date 2026-11-06, no zhihu link.
- Also inserts the note card into index.html (top of #noteList) and updates
  the category filter counts.
Run _build_search_index.py afterwards to refresh search-index.js.
"""
import io, os, re, shutil

folder = r'X:\md4obsd'
pics = os.path.join(folder, 'pics')
out_dir = os.path.dirname(os.path.abspath(__file__))
assets_dir = os.path.join(out_dir, 'assets')

SRC_MD = os.path.join(folder, 'Quantum Expander笔记.md')
TEMPLATE = os.path.join(out_dir, 'note-qecc.html')
OUT_PAGE = os.path.join(out_dir, 'note-quantum-expander.html')
INDEX_HTML = os.path.join(out_dir, 'index.html')

TITLE = 'Quantum Expander笔记'
DATE = '2026-11-06'
SLUG = 'note-quantum-expander'
CAT_LABEL = '数学'
COVER = 'aixyx.jpg'
EXCERPT = ('Quantum Expander 读书笔记：量子扩展器定义与谱隙、16 个酉矩阵的深度-1 构造、'
           'SU(2^n) 上的 k-design 及其在多体物理中的关联与纠缠熵应用。')

# ---------------------------------------------------------------- md -> html
headings = []  # (id, level, title)

def md_to_html(text):
    lines = text.split('\n')
    html = []
    i = 0
    in_list = False
    list_tag = ''

    def close_list():
        nonlocal in_list, list_tag
        if in_list:
            html.append('</' + list_tag + '>')

    while i < len(lines):
        stripped = lines[i].strip()

        if stripped == '':
            close_list()
            in_list = False
            i += 1
            continue
        if re.match(r'^-{3,}$', stripped):
            close_list()
            in_list = False
            html.append('<hr>')
            i += 1
            continue

        m = re.match(r'^(#{1,3})\s+(.*)', stripped)
        if m:
            close_list()
            in_list = False
            level = len(m.group(1))
            ttl = m.group(2).strip()
            sec_id = 'sec-' + str(len(headings))
            headings.append((sec_id, level, ttl))
            html.append('<h{0} id="{1}">{2}</h{0}>'.format(level + 2, sec_id, ttl))
            i += 1
            continue

        if stripped.startswith('>'):
            close_list()
            in_list = False
            bq_lines = []
            balance = 0
            # Obsidian-style lazy continuation: keep absorbing lines while a
            # $$...$$ display block opened inside the quote is unclosed.
            while i < len(lines):
                s = lines[i].strip()
                if s.startswith('>'):
                    content = re.sub(r'^>\s?', '', s)
                    balance += content.count('$$')
                    bq_lines.append(content)
                    i += 1
                elif balance % 2 == 1:
                    balance += s.count('$$')
                    bq_lines.append(s)
                    i += 1
                else:
                    break
            html.append('<blockquote>' + '<br>'.join(bq_lines) + '</blockquote>')
            continue

        m = re.match(r'^!\[\[([^\]]+)\]\]$', stripped)
        if m:
            close_list()
            in_list = False
            name = m.group(1)
            base = name.split('|')[0].strip()
            src = os.path.join(pics, base)
            if os.path.exists(src):
                dst = os.path.join(assets_dir, base)
                if not os.path.exists(dst):
                    shutil.copy2(src, dst)
                html.append('<img class="note-img" src="assets/' + base + '" alt="' + base + '">')
            else:
                print('  [warn] image missing:', base)
            i += 1
            continue

        m = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)$', stripped)
        if m:
            close_list()
            in_list = False
            base = os.path.basename(m.group(2))
            src = os.path.join(pics, base)
            if os.path.exists(src):
                dst = os.path.join(assets_dir, base)
                if not os.path.exists(dst):
                    shutil.copy2(src, dst)
                html.append('<img class="note-img" src="assets/' + base + '" alt="' + m.group(1) + '">')
            i += 1
            continue

        m = re.match(r'^(\d+)\.\s+(.*)', stripped)
        if m:
            if not in_list or list_tag != 'ol':
                close_list()
                html.append('<ol>')
                in_list = True
                list_tag = 'ol'
            html.append('<li>' + m.group(2) + '</li>')
            i += 1
            continue

        m = re.match(r'^[-*]\s+(.*)', stripped)
        if m:
            if not in_list or list_tag != 'ul':
                close_list()
                html.append('<ul>')
                in_list = True
                list_tag = 'ul'
            html.append('<li>' + m.group(1) + '</li>')
            i += 1
            continue

        close_list()
        in_list = False
        # Paragraph with multi-line $$...$$ display block continuation:
        # while a $$ remains unclosed, absorb following lines into the same <p>.
        parts = [stripped]
        parity = stripped.count('$$')
        while parity % 2 == 1 and i + 1 < len(lines):
            i += 1
            nxt = lines[i].strip()
            parity += nxt.count('$$')
            parts.append(nxt)
        html.append('<p>' + '\n'.join(parts) + '</p>')
        i += 1

    if in_list:
        html.append('</' + list_tag + '>')
    return '\n'.join(html).rstrip('\n')

# ---------------------------------------------------------------- read md
with io.open(SRC_MD, 'r', encoding='utf-8') as f:
    raw = f.read()
body_html = md_to_html(raw)

wick = 'QECC讨论班：Stabilizer Codes'
with io.open(TEMPLATE, 'r', encoding='utf-8') as f:
    tpl = f.read()

# 1. <title>
tpl = tpl.replace('<title>' + wick + '</title>', '<title>' + TITLE + '</title>', 1)
tpl = tpl.replace('<title>' + wick + ' · 王凌潇</title>', '<title>' + TITLE + '</title>', 1)

# 2. dates (header meta + article meta)
tpl = tpl.replace('2026-04-15', DATE)

# 3. TOC lists (desktop sidebar + mobile dropdown)
toc_items = []
toc_items.append('<li class="toc-main"><a href="#article-title">' + TITLE + '</a></li>')
for sec_id, level, ttl in headings:
    cls = {1: '', 2: 'sub', 3: 'sub2'}[level]
    cls_attr = ' class="' + cls + '"' if cls else ''
    toc_items.append('<li{0}><a href="#{1}">{2}</a></li>'.format(cls_attr, sec_id, ttl))
toc_html = '\n'.join('      ' + x for x in toc_items)

m = re.search(r'(<ul class="toc-list">\n)(.*?)(\n    </ul>\n  </aside>)', tpl, re.S)
assert m, 'desktop toc not found'
tpl = tpl[:m.start(2)] + toc_html + tpl[m.end(2):]

m = re.search(r'(<ul class="toc-list mobile-toc-list">\n)(.*?)(\n    </ul>)', tpl, re.S)
assert m, 'mobile toc not found'
tpl = tpl[:m.start(2)] + toc_html + tpl[m.end(2):]

# 4. cover image
tpl = tpl.replace('<img class="article-cover" src="assets/nikomonesy.jpg" alt="' + wick + '">',
                  '<img class="article-cover" src="assets/' + COVER + '" alt="' + TITLE + '">')

# 4b. remove the zhihu link carried over from the template (this note has none)
tpl = re.sub(r'\n *<a href="https://[^"]*zhihu\.com[^"]*" target="_blank" rel="noopener"><i class="fab fa-zhihu"></i> 知乎原文</a>', '', tpl, count=1)

# 5. title h1
tpl = tpl.replace('<h1 class="article-title" id="article-title">' + wick + '</h1>',
                  '<h1 class="article-title" id="article-title">' + TITLE + '</h1>', 1)

# 6. article body
m = re.search(r'(<div class="article-content">\n)(.*?)(\n    </div>\n  </article>)', tpl, re.S)
assert m, 'article body not found'
tpl = tpl[:m.start(2)] + body_html + tpl[m.end(2):]

with io.open(OUT_PAGE, 'w', encoding='utf-8') as f:
    f.write(tpl)
print('wrote', SLUG + '.html', '| toc items:', len(toc_items) - 1)

# ---------------------------------------------------------------- assets
dst_cover = os.path.join(assets_dir, COVER)
if not os.path.exists(dst_cover):
    shutil.copy2(os.path.join(pics, COVER), dst_cover)
    print('copied cover -> assets/' + COVER)

# ---------------------------------------------------------------- index.html card
card = '''        <a class="note-card" data-cat="math" href="{slug}.html">
          <img class="note-card-cover" src="assets/{cover}" alt="{alt}">
          <div class="note-card-body">
            <div class="note-card-title">{title}</div>
            <div class="note-card-meta"><span class="cat-tag">{cat}</span><span><i class="far fa-calendar"></i> {date}</span></div>
            <div class="note-card-excerpt">{excerpt}</div>
          </div>
        </a>'''.format(slug=SLUG, cover=COVER, alt=TITLE, title=TITLE,
                       cat=CAT_LABEL, date=DATE, excerpt=EXCERPT)

with io.open(INDEX_HTML, 'r', encoding='utf-8') as f:
    idx = f.read()

# idempotent: drop any previously inserted card for this note
idx = re.sub(r'[ \t]*<a class="note-card" data-cat="math" href="' + SLUG +
             r'\.html">.*?</a>\n', '', idx, flags=re.S)

anchor = '<div class="note-list" id="noteList">\n'
assert anchor in idx, 'noteList anchor not found'
idx = idx.replace(anchor, anchor + card + '\n', 1)

# rebuild category counts from the actual cards present
cat_counts = {}
for mm in re.finditer(r'<a class="note-card" data-cat="([a-z]+)" href="', idx):
    cat_counts[mm.group(1)] = cat_counts.get(mm.group(1), 0) + 1

def set_count(s, cat):
    val = sum(cat_counts.values()) if cat == 'all' else cat_counts.get(cat, 0)
    return re.sub(r'(data-cat="' + cat + r'"[^>]*><span class="count">)\d+(</span>)' if cat != 'all'
                  else r'(data-cat="' + cat + r'"[^>]*>全部<span class="count">)\d+(</span>)',
                  r'\g<1>' + str(val) + r'\g<2>', s, count=1)

idx = set_count(idx, 'all')
for cat in ('math', 'physics', 'other'):
    idx = re.sub(r'(data-cat="' + cat + r'">[^>]*?<span class="count">)\d+(</span>)',
                 r'\g<1>' + str(cat_counts.get(cat, 0)) + r'\g<2>', idx, count=1)

with io.open(INDEX_HTML, 'w', encoding='utf-8') as f:
    f.write(idx)
print('inserted card into index.html (counts recomputed:', dict(cat_counts, all=sum(cat_counts.values())), ')')
