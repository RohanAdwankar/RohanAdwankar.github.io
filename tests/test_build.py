"""The site build: drafts stay off the homepage but are still published."""
import re
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
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

    def test_feed_is_valid_xml_and_has_every_listed_post(self):
        channel = ET.parse(DIST / 'feed.xml').getroot().find('channel')
        links = {i.findtext('link') for i in channel.findall('item')}
        self.assertEqual(links, {f'{SITE_URL}posts/{slug(md)}.html' for md in self.listed})
        for item in channel.findall('item'):
            for field in ('title', 'link', 'guid', 'pubDate', 'description'):
                self.assertTrue((item.findtext(field) or '').strip(), f'{field} is empty')

    def test_feed_is_newest_first(self):
        channel = ET.parse(DIST / 'feed.xml').getroot().find('channel')
        dates = [parsedate_to_datetime(i.findtext('pubDate')) for i in channel.findall('item')]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_every_page_links_the_feed_and_carries_the_footer(self):
        pages = [DIST / 'index.html', DIST / 'posts' / 'index.html']
        pages += [DIST / 'posts' / f'{slug(md)}.html' for md in self.listed + self.drafts]
        for page in pages:
            text = page.read_text(encoding='utf-8')
            rel = page.relative_to(DIST)
            self.assertIn('type="application/rss+xml"', text, f'{rel} has no feed autodiscovery')
            self.assertIn('class="site-footer"', text, f'{rel} has no footer')
            self.assertIn('href="/feed.xml"', text, f'{rel} does not link the feed')

    def test_listings_match_the_feed_order(self):
        """The feed is already asserted to be newest first, so this pins the two
        listings to that same order without re-deriving any dates."""
        channel = ET.parse(DIST / 'feed.xml').getroot().find('channel')
        expected = [i.findtext('link').rsplit('/', 1)[1].removesuffix('.html')
                    for i in channel.findall('item')]
        for page, pattern in (
            (DIST / 'index.html', r'<li><a href="posts/([^"]+)\.html">'),
            (DIST / 'posts' / 'index.html', r'<li><a href="([^"]+)\.html">'),
        ):
            text = page.read_text(encoding='utf-8')
            order = re.findall(pattern, text)
            self.assertEqual(order, expected, f'{page.relative_to(DIST)} is not newest first')

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
