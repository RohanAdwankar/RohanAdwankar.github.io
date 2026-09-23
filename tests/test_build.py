"""The site build: drafts stay off the homepage but are still published."""
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POSTS = ROOT / 'posts'
DIST = ROOT / 'dist'
SITE_URL = 'https://rohanadwankar.github.io/'


def slug(md):
    return md.stem.lstrip('_')


class BuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ROOT / 'scripts' / 'build.py')], check=True, capture_output=True)
        cls.index = (DIST / 'index.html').read_text(encoding='utf-8')
        cls.linked = set(re.findall(r'href="posts/([^"]+)\.html"', cls.index))
        cls.drafts = sorted(p for p in POSTS.glob('*.md') if p.stem.startswith('_'))
        cls.listed = sorted(p for p in POSTS.glob('*.md') if not p.stem.startswith('_'))

    def test_drafts_are_not_on_the_homepage(self):
        for md in self.drafts:
            self.assertNotIn(slug(md), self.linked, f'{md.name} is a draft but is linked from the homepage')
            self.assertNotIn(md.stem, self.linked, f'{md.name} is a draft but is linked from the homepage')

    def test_drafts_are_still_built(self):
        for md in self.drafts:
            self.assertTrue((DIST / 'posts' / f'{slug(md)}.html').exists(), f'{md.name} was not built')

    def test_listed_posts_are_on_the_homepage(self):
        for md in self.listed:
            self.assertIn(slug(md), self.linked, f'{md.name} is not linked from the homepage')

    def test_homepage_links_resolve(self):
        for name in self.linked:
            self.assertTrue((DIST / 'posts' / f'{name}.html').exists(), f'homepage links to posts/{name}.html, which was not built')

    def test_sitemap_lists_the_homepage_and_every_listed_post(self):
        locs = set(re.findall(r'<loc>([^<]+)</loc>', (DIST / 'sitemap.xml').read_text(encoding='utf-8')))
        self.assertIn(SITE_URL, locs)
        for md in self.listed:
            self.assertIn(f'{SITE_URL}posts/{slug(md)}.html', locs, f'{md.name} is listed but missing from the sitemap')

    def test_sitemap_leaves_out_drafts(self):
        text = (DIST / 'sitemap.xml').read_text(encoding='utf-8')
        for md in self.drafts:
            self.assertNotIn(f'posts/{slug(md)}.html', text, f'{md.name} is a draft but is in the sitemap')

    def test_sitemap_urls_all_resolve(self):
        for loc in re.findall(r'<loc>([^<]+)</loc>', (DIST / 'sitemap.xml').read_text(encoding='utf-8')):
            rel = loc[len(SITE_URL):]
            target = DIST / rel if rel and not rel.endswith('/') else DIST / rel / 'index.html'
            self.assertTrue(target.exists(), f'sitemap lists {loc}, which was not built')

    def test_robots_points_at_the_sitemap(self):
        robots = (DIST / 'robots.txt').read_text(encoding='utf-8')
        self.assertIn(f'Sitemap: {SITE_URL}sitemap.xml', robots)


if __name__ == '__main__':
    unittest.main()
