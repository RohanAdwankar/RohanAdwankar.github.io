#!/usr/bin/env python3
import os
import re
from pathlib import Path
import markdown

ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / 'posts'
OUT_INDEX = ROOT / 'index.html'

PAGE_CSS = '''
    <style>
    body { background: #1a1a1a; color: #e0e0e0; font-family: Georgia, serif; line-height: 1.6; max-width: 980px; margin: 60px auto; padding: 0 20px; }
    a { color: inherit; text-decoration: underline; text-decoration-thickness: 1px; }
    header { display:flex; justify-content:space-between; align-items:center; margin-bottom:30px }
    .header-controls { display:flex; gap:12px; align-items:center }
    .back-link { text-decoration: none; color: inherit; font-size: 14px; display: block; margin-bottom: 8px }
    .mobile-back { display: none; text-decoration: none; color: inherit; font-size: 14px; margin-right: 8px }
    .post-wrapper { display: flex; gap: 28px; align-items: flex-start }
    aside.toc { width: 220px; flex: 0 0 220px; margin-top: 4px; }
    aside.toc nav { position: sticky; top: 80px; background: transparent; }
    aside.toc ul { list-style: none; padding-left: 0; margin: 0; }
    aside.toc h3 { margin: 0 0 8px 0; font-size: 15px; font-weight: normal; }
    aside.toc a { text-decoration: none; color: inherit; }
    article { flex: 1 1 auto; min-width: 0 }
    .toc a { display: block; padding: 4px 0; }
    .theme-switch { position: relative; display: inline-block; width: 44px; height: 24px; }
    .theme-switch input { opacity: 0; width: 0; height: 0; }
    .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #e0e0e0; transition: .4s; border-radius: 24px; }
    .slider:before { position: absolute; content: ""; height: 18px; width: 18px; left: 3px; bottom: 3px; background-color: #1a1a1a; transition: .4s; border-radius: 50%; }
    input:checked + .slider { background-color: #333; }
    input:checked + .slider:before { transform: translateX(20px); background-color: #e0e0e0; }
    body.light { background: #fff; color: #111; }
    body.light .slider { background-color: #333; }
    body.light .slider:before { background-color: #fff; }
        @media (max-width: 720px) {
            aside.toc { display: none; }
            .post-wrapper { gap: 12px; }
            .mobile-back { display: inline-block; }
        }
        </style>
'''

def slug_from_path(p: Path):
    return p.stem

def title_from_markdown(text: str, default: str):
    m = re.search(r'^#\s+(.+)', text, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return default

def build_post(md_path: Path):
        raw = md_path.read_text(encoding='utf-8')
        title = title_from_markdown(raw, slug_from_path(md_path))
        # Remove the first-level heading from the markdown to avoid duplicate H1
        text = re.sub(r'^\s*#\s+.*\n', '\n', raw, count=1, flags=re.MULTILINE)
        md = markdown.Markdown(extensions=['fenced_code', 'toc'])
        html_body = md.convert(text)
        toc_html = md.toc or ''
        slug = slug_from_path(md_path)
        out_path = md_path.with_suffix('.html')
        page = f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{title} — Rohan Adwankar</title>
        {PAGE_CSS}
    </head>
    <body>
        <header>
            <h1>{title}</h1>
            <div class="header-controls">
            <a class="mobile-back" href="/">← Home</a>
            <label class="theme-switch">
                <input type="checkbox" id="theme-toggle">
                <span class="slider"></span>
            </label>
            </div>
        </header>
        <main>
            <div class="post-wrapper">
                <aside class="toc">
                    <nav><a class="back-link" href="/">← Home</a><h3>Contents</h3>{toc_html}</nav>
                </aside>
                <article>
                    {html_body}
                </article>
            </div>
        </main>
        <script>
            const toggle = document.getElementById('theme-toggle');
            if (toggle) toggle.addEventListener('change', () => document.body.classList.toggle('light'));
        </script>
    </body>
    </html>"""
        out_path.write_text(page, encoding='utf-8')
        print(f'Wrote {out_path.relative_to(ROOT)}')
        return slug, title

def build_index(posts):
    items = []
    for slug, title in posts:
        items.append(f'<li><a href="posts/{slug}.html">{title}</a></li>')
    posts_html = '<ul>\n' + '\n'.join(items) + '\n</ul>'
    index_page = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"UTF-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
<title>Rohan Adwankar</title>
{PAGE_CSS}
</head>
<body>
<header>
    <h1>Rohan Adwankar</h1>
    <div class=\"header-controls\">
        <label class=\"theme-switch\">
            <input type=\"checkbox\" id=\"theme-toggle\">
            <span class=\"slider\"></span>
        </label>
    </div>
</header>
<main>
    <p>Hi my name is Rohan Adwankar.</p>
    <h3>Notes</h3>
    {posts_html}
</main>
<script>
    const toggle = document.getElementById('theme-toggle');
    if (toggle) toggle.addEventListener('change', () => document.body.classList.toggle('light'));
</script>
</body>
</html>"""
    OUT_INDEX.write_text(index_page, encoding='utf-8')
    print(f'Wrote {OUT_INDEX.relative_to(ROOT)}')

def main():
    if not POSTS_DIR.exists():
        print('No posts/ directory found.')
        return
    md_files = sorted(POSTS_DIR.glob('*.md'))
    posts = []
    for md in md_files:
        slug, title = build_post(md)
        posts.append((slug, title))
    build_index(posts)

if __name__ == '__main__':
    main()
