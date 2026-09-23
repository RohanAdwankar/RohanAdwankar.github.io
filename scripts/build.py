#!/usr/bin/env python3
import re
import shutil
import subprocess
import sys
from collections import namedtuple
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

import markdown

ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / 'posts'
STATIC_DIR = ROOT / 'static'
DIST_DIR = ROOT / 'dist'
OUT_POSTS_DIR = DIST_DIR / 'posts'
OUT_INDEX = DIST_DIR / 'index.html'
OUT_POSTS_INDEX = OUT_POSTS_DIR / 'index.html'
OUT_SITEMAP = DIST_DIR / 'sitemap.xml'
OUT_FEED = DIST_DIR / 'feed.xml'

Post = namedtuple('Post', 'slug title date updated')

SITE_TITLE = 'Rohan Adwankar'
SITE_DESCRIPTION = 'Notes on the things I am working on.'

# Where the built site is served from. robots.txt in static/ points at the
# sitemap by this same absolute URL, so the two have to agree.
SITE_URL = 'https://rohanadwankar.github.io/'

PAGE_CSS = '''
    <style>
    body { background: #1a1a1a; color: #e0e0e0; font-family: Georgia, serif; line-height: 1.6; max-width: 980px; margin: 60px auto; padding: 0 20px; }
    a { color: inherit; text-decoration: underline; text-decoration-thickness: 1px; }
    header { display:flex; justify-content:space-between; align-items:center; margin-bottom:30px }
    .header-controls { display:flex; gap:12px; align-items:center }
    .back-link { text-decoration: none; color: inherit; font-size: 14px; display: block; margin-bottom: 8px }
    .mobile-back { display: none; text-decoration: none; color: inherit; font-size: 14px; margin-right: 8px }
    .hn-badge { display: inline-flex; align-items: center; gap: 8px; padding: 6px 12px; border: 1px solid #3a3a3a; border-radius: 6px; background: #222; font-size: 14px; line-height: 1; text-decoration: none; color: inherit; }
    .hn-badge:hover { border-color: #ff6600; }
    .hn-badge svg { flex: 0 0 auto; display: block; }
    body.light .hn-badge { border-color: #d0d0d0; background: #f7f7f7; }
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
    pre.mermaid { background: transparent; text-align: center; margin: 24px 0; overflow-x: auto; }
    article pre { overflow-x: auto; max-width: 100%; }
    pre code.hljs { border-radius: 6px; padding: 14px 16px; font-size: 13.5px; overflow-x: auto; }
    article :not(pre) > code { background: #262626; border: 1px solid #3a3a3a; border-radius: 4px; padding: 0.08em 0.36em; font-size: 0.86em; color: #e7a6a0; }
    body.light article :not(pre) > code { background: #f4f4f4; border-color: #e2e2e2; color: #c0392b; }
    .table-wrap { overflow-x: auto; margin: 24px 0; }
    article table { border-collapse: collapse; width: 100%; font-size: 15px; line-height: 1.45; }
    article th, article td { border: 1px solid #3a3a3a; padding: 10px 14px; text-align: left; vertical-align: top; }
    article th { background: #2a2a2a; font-weight: bold; }
    article thead th:first-child { background: transparent; border-top-color: transparent; border-left-color: transparent; }
    article tbody tr:nth-child(even) { background: #202020; }
    article td:first-child { font-weight: bold; white-space: nowrap; color: #f0f0f0; }
    article td code, article th code { font-size: 13px; }
    body.light article th, body.light article td { border-color: #d0d0d0; }
    body.light article th { background: #f0f0f0; }
    body.light article thead th:first-child { background: transparent; border-top-color: transparent; border-left-color: transparent; }
    body.light article tbody tr:nth-child(even) { background: #f7f7f7; }
    body.light article td:first-child { color: #111; }
    body.light { background: #fff; color: #111; }
    body.light .slider { background-color: #333; }
    body.light .slider:before { background-color: #fff; }
    .site-footer { margin-top: 56px; padding-top: 18px; border-top: 1px solid #3a3a3a; display: flex; flex-wrap: wrap; gap: 16px; align-items: baseline; font-size: 14px; }
    .site-footer span { opacity: 0.6; }
    body.light .site-footer { border-top-color: #e2e2e2; }
    .post-date { font-size: 14px; opacity: 0.6; margin-left: 8px; white-space: nowrap; }
        @media (max-width: 720px) {
            body { margin: 20px auto; }
            aside.toc { display: none; }
            .post-wrapper { gap: 12px; }
            header { flex-wrap: wrap; margin-bottom: 20px; }
            header h1 { flex: 1 1 100%; font-size: 1.75em; line-height: 1.2; margin: 0; }
            .header-controls { order: -1; flex: 1 1 100%; margin-bottom: 14px; }
            .header-controls .theme-switch { margin-left: auto; }
            .mobile-back { display: inline-block; white-space: nowrap; margin-right: 0; }
        }
        </style>
'''

FEED_LINK = '<link rel="alternate" type="application/rss+xml" title="Rohan Adwankar" href="/feed.xml">'

SITE_FOOTER = """<footer class="site-footer">
        <span>Follow:</span>
        <a href="https://github.com/RohanAdwankar">GitHub</a>
        <a href="https://x.com/Rohanadwankar">X</a>
        <a href="/feed.xml">RSS</a>
    </footer>"""

def slug_from_path(p: Path):
    # A draft keeps the same URL it will have once it is listed, so a link
    # shared while it is unlisted keeps working after the underscore comes off.
    return p.stem.lstrip('_')

def title_from_markdown(text: str, default: str):
    m = re.search(r'^#\s+(.+)', text, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return default

def is_draft(md_path: Path):
    """Drafts are built and published like any other post; they are only left
    off the homepage list. Rename the file without the underscore to list it."""
    return md_path.stem.startswith('_')

def git_date(md_path: Path, *args):
    """A date out of git, or None when there is no history to read."""
    try:
        out = subprocess.run(
            ['git', 'log', '--format=%aI', '-1', *args, '--', str(md_path)],
            cwd=ROOT, capture_output=True, text=True, timeout=15,
        ).stdout.strip()
        return datetime.fromisoformat(out) if out else None
    except (OSError, ValueError, subprocess.SubprocessError):
        return None

def post_date(md_path: Path):
    """When the post was published: the commit that gave it its listed name.

    A draft lives at `_name.md` and is published by renaming it to `name.md`,
    so the commit that added the current path is the commit that published it.
    Deliberately no `--follow`: following the rename back would date a post to
    the day it was first drafted, which for a post drafted in July and listed
    in September buries it at the bottom of every subscriber's reader. `-1`
    takes the most recent add, so a post that was listed, pulled back to a
    draft and listed again carries the date it went out for good.
    """
    return git_date(md_path, '--diff-filter=A') or file_date(md_path)

def post_updated(md_path: Path):
    """When the post last changed. This is what a sitemap's lastmod means, and
    it is not the publish date: semfont was published once and edited after."""
    return git_date(md_path) or file_date(md_path)

def file_date(md_path: Path):
    """Fallback when git has no history, as in a shallow CI checkout."""
    return datetime.fromtimestamp(md_path.stat().st_mtime, tz=timezone.utc)

def summary_from_markdown(text: str, limit: int = 280):
    """The post's opening sentences, as plain text, for the feed."""
    for block in re.split(r'\n\s*\n', text):
        block = block.strip()
        # skip the title, raw HTML (the HN badge), code fences and images
        if not block or block.startswith(('#', '<', '```', '!', '|')):
            continue
        block = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', block)   # links -> their text
        block = re.sub(r'[`*_]', '', block)
        block = ' '.join(block.split())
        return block if len(block) <= limit else block[:limit].rsplit(' ', 1)[0] + '…'
    return SITE_DESCRIPTION

MERMAID_CDN = 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js'
HLJS_JS = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js'
HLJS_CSS = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css'

def extract_mermaid(text: str, store: list):
    def repl(m):
        store.append(m.group(1).rstrip('\n'))
        return f'\n\nMERMAIDPLACEHOLDER{len(store) - 1}ENDMERMAID\n\n'
    return re.sub(r'```mermaid\n(.*?)```', repl, text, flags=re.DOTALL)

def restore_mermaid(html: str, store: list):
    for i, block in enumerate(store):
        # markdown wraps the bare placeholder line in <p>...</p>
        html = html.replace(
            f'<p>MERMAIDPLACEHOLDER{i}ENDMERMAID</p>',
            f'<pre class="mermaid">{block}</pre>',
        )
    return html

def build_post(md_path: Path):
        raw = md_path.read_text(encoding='utf-8')
        title = title_from_markdown(raw, slug_from_path(md_path))
        text = re.sub(r'^\s*#\s+.*\n', '\n', raw, count=1, flags=re.MULTILINE)
        mermaid_blocks = []
        text = extract_mermaid(text, mermaid_blocks)
        md = markdown.Markdown(extensions=['fenced_code', 'toc', 'tables'])
        html_body = md.convert(text)
        html_body = restore_mermaid(html_body, mermaid_blocks)
        html_body = html_body.replace('<table>', '<div class="table-wrap"><table>')
        html_body = html_body.replace('</table>', '</table></div>')
        toc_html = md.toc or ''
        mermaid_script = (
            f'<script src="{MERMAID_CDN}"></script>\n'
            '<script>function initMermaid(){var d=document.body.classList.contains("light");'
            'mermaid.initialize({startOnLoad:true,theme:d?"default":"dark",'
            'securityLevel:"loose",fontFamily:"Georgia, serif"});}initMermaid();</script>'
        ) if mermaid_blocks else ''
        highlight_assets = (
            f'<link rel="stylesheet" href="{HLJS_CSS}">\n'
            f'<script src="{HLJS_JS}"></script>\n'
            '<script>document.querySelectorAll("pre code").forEach('
            'function(b){hljs.highlightElement(b);});</script>'
        ) if '<pre><code' in html_body else ''
        slug = slug_from_path(md_path)
        out_path = OUT_POSTS_DIR / f'{slug}.html'
        page = f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{title} — Rohan Adwankar</title>
        {FEED_LINK}
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
                    {SITE_FOOTER}
                </article>
            </div>
        </main>
        <script>
            const toggle = document.getElementById('theme-toggle');
            if (toggle) toggle.addEventListener('change', () => document.body.classList.toggle('light'));
        </script>
        {mermaid_script}
        {highlight_assets}
    </body>
    </html>"""
        out_path.write_text(page, encoding='utf-8')
        note = ' (draft, not listed on the homepage)' if is_draft(md_path) else ''
        print(f'Wrote {out_path.relative_to(ROOT)}{note}')
        post = Post(slug, title, post_date(md_path), post_updated(md_path))
        return post, summary_from_markdown(text)

def build_feed(posts, summaries):
    """An RSS feed of the listed posts, newest first.

    Drafts stay out, same as the homepage and the sitemap. A reader who
    subscribes gets the post on the day it is listed, not on the day it was
    first drafted, which is why an unlisted post is not in here waiting.
    """
    items = []
    for post in posts:
        url = f'{SITE_URL}posts/{post.slug}.html'
        items.append(
            '    <item>\n'
            f'      <title>{escape(post.title)}</title>\n'
            f'      <link>{url}</link>\n'
            f'      <guid isPermaLink="true">{url}</guid>\n'
            f'      <pubDate>{format_datetime(post.date)}</pubDate>\n'
            f'      <description>{escape(summaries[post.slug])}</description>\n'
            '    </item>'
        )
    OUT_FEED.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        '  <channel>\n'
        f'    <title>{SITE_TITLE}</title>\n'
        f'    <link>{SITE_URL}</link>\n'
        f'    <description>{SITE_DESCRIPTION}</description>\n'
        '    <language>en</language>\n'
        f'    <atom:link href="{SITE_URL}feed.xml" rel="self" type="application/rss+xml"/>\n'
        + '\n'.join(items) + '\n'
        '  </channel>\n'
        '</rss>\n',
        encoding='utf-8',
    )
    print(f'Wrote {OUT_FEED.relative_to(ROOT)} ({len(items)} items)')

def build_sitemap(posts):
    """List every page a search engine should index.

    Drafts are left out. They are published and reachable by URL, but nothing
    on the site links to them, and putting an unlisted page in the sitemap is
    the one thing that would undo that.
    """
    newest = max((p.updated for p in posts), default=None)
    entries = [('', newest)]
    if OUT_POSTS_INDEX.exists():
        entries.append(('posts/', newest))
    entries += [(f'posts/{p.slug}.html', p.updated) for p in posts]
    urls = '\n'.join(
        f'  <url><loc>{SITE_URL}{path}</loc>'
        + (f'<lastmod>{date.date().isoformat()}</lastmod>' if date else '')
        + '</url>'
        for path, date in entries
    )
    paths = [path for path, _ in entries]
    OUT_SITEMAP.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'{urls}\n'
        '</urlset>\n',
        encoding='utf-8',
    )
    print(f'Wrote {OUT_SITEMAP.relative_to(ROOT)} ({len(paths)} urls)')
def build_posts_index(posts):
    """/posts is the same list as the homepage, on its own page.

    Anyone who reaches a post by a shared link and then trims the URL lands
    here, so it has to exist. Drafts stay off it for the same reason they stay
    off the homepage.
    """
    items = '\n'.join(
        f'<li><a href="{p.slug}.html">{p.title}</a>'
        f'<span class="post-date">{p.date:%b %-d, %Y}</span></li>'
        for p in posts
    )
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Notes — Rohan Adwankar</title>
{FEED_LINK}
{PAGE_CSS}
</head>
<body>
<header>
    <h1>Notes</h1>
    <div class="header-controls">
        <label class="theme-switch">
            <input type="checkbox" id="theme-toggle">
            <span class="slider"></span>
        </label>
    </div>
</header>
<main>
    <!-- .back-link shows at every width here, so no .mobile-back in the header:
         a post page hides its copy inside the TOC aside below 720px, this page
         has no aside and would show two. -->
    <a class="back-link" href="/">← Home</a>
    <ul>
{items}
    </ul>
    {SITE_FOOTER}
</main>
<script>
    const toggle = document.getElementById('theme-toggle');
    if (toggle) toggle.addEventListener('change', () => document.body.classList.toggle('light'));
</script>
</body>
</html>"""
    OUT_POSTS_INDEX.write_text(page, encoding='utf-8')
    print(f'Wrote {OUT_POSTS_INDEX.relative_to(ROOT)}')

def build_index(posts):
    items = [
        f'<li><a href="posts/{p.slug}.html">{p.title}</a>'
        f'<span class="post-date">{p.date:%b %-d, %Y}</span></li>'
        for p in posts
    ]
    posts_html = '<ul>\n' + '\n'.join(items) + '\n</ul>'
    index_page = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"UTF-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
<title>Rohan Adwankar</title>
{FEED_LINK}
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
    <p>Hi my name is Rohan Adwankar, welcome to my personal website!</p>
    <p>My goal with this site is to document some of the things I am working on in a long-form context.</p>
    <p>To stay updated on what I'm doing feel free to connect with me on <a href="https://github.com/RohanAdwankar">Github</a>, <a href="https://x.com/Rohanadwankar">X</a>, or <a href="https://linkedin.com/in/rohanadwankar">LinkedIn</a>.</p>
    <p>Injected below is my Github profile card which will stay updated even when this site isn't, and below that are my longer form notes.</p>
    <div id="injected-readme">Loading...</div>
    <h3><a href="posts/">Notes</a></h3>
    {posts_html}
    {SITE_FOOTER}
</main>
<script>
    const toggle = document.getElementById('theme-toggle');
    if (toggle) toggle.addEventListener('change', () => document.body.classList.toggle('light'));

    async function loadReadme() {{
        const container = document.getElementById('injected-readme');
        if (!container) return;
        const url = 'https://raw.githubusercontent.com/RohanAdwankar/RohanAdwankar/main/README.md';
        try {{
            const res = await fetch(url);
            if (!res.ok) {{
                container.textContent = 'Failed to load content.';
                return;
            }}
            const text = await res.text();
            container.innerHTML = text;
        }} catch (err) {{
            container.textContent = 'The Github Card did not load. No worries you can check it out using the link above.';
            console.error(err);
        }}
    }}
    document.addEventListener('DOMContentLoaded', loadReadme);
</script>
</body>
</html>"""
    OUT_INDEX.write_text(index_page, encoding='utf-8')
    print(f'Wrote {OUT_INDEX.relative_to(ROOT)}')

def main():
    if not POSTS_DIR.exists():
        print('No posts/ directory found.')
        return
    shutil.rmtree(DIST_DIR, ignore_errors=True)
    OUT_POSTS_DIR.mkdir(parents=True, exist_ok=True)
    md_files = sorted(POSTS_DIR.glob('*.md'))
    by_slug = {}
    for md in md_files:
        other = by_slug.setdefault(slug_from_path(md), md)
        if other is not md:
            sys.exit(f'{md.relative_to(ROOT)} and {other.relative_to(ROOT)} '
                     f'would both be written to posts/{slug_from_path(md)}.html')
    listed, summaries = [], {}
    for md in md_files:
        post, summary = build_post(md)
        if not is_draft(md):
            listed.append(post)
            summaries[post.slug] = summary
    # newest first everywhere: a blog's front page is not an alphabetical index
    listed.sort(key=lambda p: p.date, reverse=True)
    build_index(listed)
    build_posts_index(listed)
    build_feed(listed, summaries)
    # after build_posts_index, so the sitemap sees /posts/ and can list it
    build_sitemap(listed)
    copy_static()


def copy_static():
    """Copy static/ verbatim into dist/, preserving subdirectories."""
    if not STATIC_DIR.exists():
        return
    for src in sorted(STATIC_DIR.rglob('*')):
        if not src.is_file():
            continue
        dest = DIST_DIR / src.relative_to(STATIC_DIR)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        print(f'Copied {src.relative_to(ROOT)} -> {dest.relative_to(ROOT)}')

if __name__ == '__main__':
    main()
