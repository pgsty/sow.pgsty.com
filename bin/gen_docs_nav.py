#!/usr/bin/env python3
"""Generate data/docs_nav.json from the content/docs tree.

The sidebar partial (layouts/_partials/docs-sidebar-tree.html) renders
navigation exclusively from this file, and errors out on any node whose
page cannot be resolved, so this generator must be re-run whenever a doc
page is added, removed, or re-weighted:

    python3 bin/gen_docs_nav.py

Layout contract (mirrors the original silo scaffold):
  - sections:            ordered top-level nodes: the docs root itself
                         (flat entry) followed by each docs subsection
                         with its nested children.
  - page_by_url:         "/docs/start/install/" -> "docs/start/install"
  - children_by_url:     section url -> ordered direct child page paths
                         (drives the section-index cards on _index pages)
  - active_path_by_url:  url -> ancestor urls including self (sidebar
                         expansion state)

English files are canonical for structure and weight; the zh translation
only contributes title_zh. A missing zh counterpart is reported but does
not fail the build.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, 'content', 'docs')
OUT = os.path.join(ROOT, 'data', 'docs_nav.json')

FM_RE = re.compile(r'\A---\n(.*?)\n---\n', re.S)


def front_matter(path):
    with open(path, encoding='utf-8') as f:
        m = FM_RE.match(f.read())
    if not m:
        raise SystemExit(f'{path}: missing front matter')
    fm = {}
    for line in m.group(1).splitlines():
        if ':' not in line or line.startswith((' ', '\t', '#')):
            continue
        key, _, val = line.partition(':')
        fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm


def scan(directory, page_prefix):
    """Return ordered [(page_path, fm_en, title_zh, children)] for one dir."""
    entries = []
    for name in sorted(os.listdir(directory)):
        full = os.path.join(directory, name)
        if os.path.isdir(full):
            index = os.path.join(full, '_index.md')
            if not os.path.exists(index):
                raise SystemExit(f'{full}: subdirectory without _index.md')
            fm = front_matter(index)
            zh = zh_title(os.path.join(full, '_index.zh.md'), index)
            children = scan(full, f'{page_prefix}/{name}')
            entries.append((f'{page_prefix}/{name}', fm, zh, children))
        elif name.endswith('.md') and not name.endswith('.zh.md') and name != '_index.md':
            fm = front_matter(full)
            zh = zh_title(full[:-3] + '.zh.md', full)
            page = f'{page_prefix}/{name[:-3]}'
            entries.append((page, fm, zh, []))
    entries.sort(key=lambda e: (int(e[1].get('weight', 9999)), e[0]))
    return entries


def zh_title(zh_path, en_path):
    if not os.path.exists(zh_path):
        print(f'  [warn] missing zh translation: {os.path.relpath(zh_path, ROOT)}',
              file=sys.stderr)
        return None
    fm = front_matter(zh_path)
    return fm.get('linkTitle') or fm.get('title')


def to_node(page, fm, zh, children):
    url = fm.get('url')
    if not url:
        raise SystemExit(f'{page}: front matter must set url')
    return {
        'page': page,
        'url': url if url.endswith('/') else url + '/',
        'title_en': fm.get('linkTitle') or fm.get('title') or page,
        'title_zh': zh or fm.get('linkTitle') or fm.get('title') or page,
        'children': [to_node(*c) for c in children],
    }


def main():
    root_fm = front_matter(os.path.join(DOCS, '_index.md'))
    root_zh = zh_title(os.path.join(DOCS, '_index.zh.md'),
                       os.path.join(DOCS, '_index.md'))
    tree = scan(DOCS, 'docs')

    sections = [to_node('docs', root_fm, root_zh, [])]
    sections += [to_node(*entry) for entry in tree]

    page_by_url = {}
    children_by_url = {}
    active_path_by_url = {}

    def walk(node, ancestors):
        url, page = node['url'], node['page']
        page_by_url[url] = page
        active_path_by_url[url] = ancestors + [url]
        if node['children']:
            children_by_url[url] = [c['page'] for c in node['children']]
            for child in node['children']:
                walk(child, ancestors + [url])

    docs_url = sections[0]['url']
    page_by_url[docs_url] = 'docs'
    active_path_by_url[docs_url] = [docs_url]
    children_by_url[docs_url] = [entry[0] for entry in tree]
    for section in sections[1:]:
        walk(section, [docs_url])

    data = {
        'meta': {'generated_by': 'bin/gen_docs_nav.py',
                 'page_count': len(page_by_url)},
        'page_by_url': page_by_url,
        'children_by_url': children_by_url,
        'active_path_by_url': active_path_by_url,
        'sections': sections,
    }
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(f'wrote {os.path.relpath(OUT, ROOT)}: {len(page_by_url)} pages')


if __name__ == '__main__':
    main()
