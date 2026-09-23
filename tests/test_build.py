"""The site build: drafts stay off the homepage but are still published."""
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POSTS = ROOT / 'posts'
DIST = ROOT / 'dist'


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

    def test_posts_index_exists_and_lists_the_same_posts(self):
        page = DIST / 'posts' / 'index.html'
        self.assertTrue(page.exists(), '/posts/ was not built, so trimming a post URL 404s')
        linked = set(re.findall(r'<li><a href="([^"]+)\.html">', page.read_text(encoding='utf-8')))
        self.assertEqual(linked, self.linked)

    def test_posts_index_leaves_out_drafts(self):
        text = (DIST / 'posts' / 'index.html').read_text(encoding='utf-8')
        for md in self.drafts:
            self.assertNotIn(f'"{slug(md)}.html"', text, f'{md.name} is a draft but is listed on /posts/')


if __name__ == '__main__':
    unittest.main()
