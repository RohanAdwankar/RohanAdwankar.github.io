#!/usr/bin/env python3
"""Draw a place's map from OpenStreetMap data, in the style of the map app
everyone can read: pale land, white streets with grey edges, yellow
arterials, blue water, green parks, grey district names.

    uv run --with pillow scenes/build_map.py vienna-1913

Reads the place's `map.bbox` and `map.osm` (an Overpass query result cached
in .cache/) and writes `static/places/<place>/map.webp`. The page draws the
pins over it from their lat/lon with the same Mercator projection.
"""
import json
import math
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.cache'
OVERPASS = 'https://overpass.kumi.systems/api/interpreter'

# Colours from the app.
C = {
    'land': '#f2efe9', 'water': '#aadaff', 'park': '#c9e6c4', 'wood': '#b8dcb0', 'cemetery': '#d3e1cd',
    'pitch': '#d0e8c8', 'campus': '#eae4d8', 'hospital': '#f6e6e6', 'railyard': '#e8e6e2',
    'rail': '#c8c4bc', 'label': '#6b6b6b', 'area_label': '#8a8a8a', 'water_label': '#3a7fc1',
}
# Road class: (casing colour, fill colour, casing width, fill width) at 1x.
ROADS = {
    'motorway': ('#e0a545', '#f5c85c', 9, 6.5), 'trunk': ('#e0a545', '#f5c85c', 9, 6.5),
    'primary': ('#e6c98a', '#ffe9a8', 8, 5.5), 'secondary': ('#e6d5a0', '#fff2c2', 6.5, 4.5),
    'tertiary': ('#d6d2c8', '#ffffff', 5, 3.5),
    'residential': ('#d6d2c8', '#ffffff', 3, 2), 'unclassified': ('#d6d2c8', '#ffffff', 3, 2),
    'living_street': ('#d6d2c8', '#ffffff', 2.5, 1.5), 'pedestrian': ('#d6d2c8', '#f6f3ee', 2.5, 1.5),
    'motorway_link': ('#e0a545', '#f5c85c', 5, 3.5), 'trunk_link': ('#e0a545', '#f5c85c', 5, 3.5),
    'primary_link': ('#e6c98a', '#ffe9a8', 5, 3.5), 'secondary_link': ('#e6d5a0', '#fff2c2', 4, 2.5),
    'tertiary_link': ('#d6d2c8', '#ffffff', 3.5, 2.5),
}
ROAD_ORDER = ['living_street', 'pedestrian', 'unclassified', 'residential', 'tertiary_link', 'tertiary',
              'secondary_link', 'secondary', 'primary_link', 'primary', 'trunk_link', 'trunk', 'motorway_link', 'motorway']


def merc_y(lat):
    return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


class Projection:
    def __init__(self, bbox, width, height):
        self.s, self.w, self.n, self.e = bbox  # south, west, north, east
        self.width, self.height = width, height
        self.y0, self.y1 = merc_y(self.n), merc_y(self.s)

    def __call__(self, lat, lon):
        x = (lon - self.w) / (self.e - self.w) * self.width
        y = (merc_y(lat) - self.y0) / (self.y1 - self.y0) * self.height
        return x, y


def load_place(place):
    data_js = ROOT / 'static' / 'places' / place / 'data.js'
    script = f"import('{data_js.as_posix()}').then(m => console.log(JSON.stringify({{map: m.default.map, pins: m.default.pins.map(p => ({{id: p.id, lat: p.lat, lon: p.lon, label: p.label}}))}})))"
    return json.loads(subprocess.run(['node', '-e', script], capture_output=True, text=True, check=True).stdout)


def fetch_osm(place, bbox):
    """The Overpass query for everything the map draws, cached by bbox."""
    s, w, n, e = bbox
    key = f'{s},{w},{n},{e}'
    path = CACHE / f'osm-{place}.json'
    if path.exists():
        try:
            j = json.loads(path.read_text())
            if j.get('_bbox') == key:
                return j
        except json.JSONDecodeError:
            pass
    q = f"""[out:json][timeout:180];
(
  way["highway"~"^(motorway|trunk|primary|secondary|tertiary|residential|unclassified|pedestrian|living_street|motorway_link|trunk_link|primary_link|secondary_link|tertiary_link)$"]({key});
  way["railway"~"^(rail|light_rail|subway|tram)$"]({key});
  way["natural"="water"]({key});
  way["waterway"~"^(river|canal|riverbank)$"]({key});
  relation["natural"="water"]({key});
  relation["waterway"="riverbank"]({key});
  way["leisure"~"^(park|garden|pitch|playground)$"]({key});
  way["landuse"~"^(grass|forest|cemetery|meadow|recreation_ground|village_green)$"]({key});
  way["natural"~"^(wood|scrub|grassland)$"]({key});
  relation["leisure"="park"]({key});
  way["amenity"~"^(hospital|university|school)$"]({key});
  way["landuse"="railway"]({key});
  node["place"~"^(suburb|quarter|neighbourhood)$"]({key});
);
out geom;"""
    print('fetching OpenStreetMap data')
    body = urllib.parse.urlencode({'data': q}).encode()
    with urllib.request.urlopen(urllib.request.Request(OVERPASS, data=body), timeout=900) as r:
        j = json.loads(r.read())
    j['_bbox'] = key
    CACHE.mkdir(exist_ok=True)
    path.write_text(json.dumps(j))
    return j


def polygons_of(el):
    """Closed rings for a way or a multipolygon relation (outer only)."""
    if el['type'] == 'way':
        g = el.get('geometry') or []
        if len(g) > 2:
            yield [(p['lat'], p['lon']) for p in g]
    elif el['type'] == 'relation':
        # Stitch outer member ways into rings.
        segs = [[(p['lat'], p['lon']) for p in m.get('geometry', [])] for m in el.get('members', []) if m.get('role') in ('outer', '') and m.get('geometry')]
        rings = []
        while segs:
            ring = segs.pop(0)
            changed = True
            while changed and ring[0] != ring[-1]:
                changed = False
                for i, s in enumerate(segs):
                    if s[0] == ring[-1]:
                        ring += s[1:]; segs.pop(i); changed = True; break
                    if s[-1] == ring[-1]:
                        ring += s[-2::-1]; segs.pop(i); changed = True; break
                    if s[-1] == ring[0]:
                        ring = s[:-1] + ring; segs.pop(i); changed = True; break
                    if s[0] == ring[0]:
                        ring = s[::-1][:-1] + ring; segs.pop(i); changed = True; break
            if len(ring) > 2:
                rings.append(ring)
        for r in rings:
            yield r


def area_colour(tags):
    if tags.get('natural') == 'water' or tags.get('waterway') == 'riverbank':
        return C['water'], 2
    if tags.get('leisure') in ('park', 'garden'):
        return C['park'], 1
    if tags.get('leisure') in ('pitch', 'playground'):
        return C['pitch'], 1
    if tags.get('landuse') in ('grass', 'meadow', 'recreation_ground', 'village_green'):
        return C['park'], 1
    if tags.get('landuse') == 'forest' or tags.get('natural') in ('wood', 'scrub', 'grassland'):
        return C['wood'], 1
    if tags.get('landuse') == 'cemetery':
        return C['cemetery'], 1
    if tags.get('amenity') in ('university', 'school'):
        return C['campus'], 0
    if tags.get('amenity') == 'hospital':
        return C['hospital'], 0
    if tags.get('landuse') == 'railway':
        return C['railyard'], 0
    return None, 0


def render(place, out, width=1600, height=1024, scale=2):
    info = load_place(place)
    bbox = info['map']['bbox']
    osm = fetch_osm(place, bbox)
    W, H = width * scale, height * scale
    proj = Projection(bbox, W, H)
    img = Image.new('RGB', (W, H), C['land'])
    d = ImageDraw.Draw(img)
    els = osm['elements']

    # Areas, dull ones first so parks and water sit on top.
    areas = []
    for el in els:
        tags = el.get('tags', {})
        colour, z = area_colour(tags)
        if colour is None:
            continue
        for ring in polygons_of(el):
            areas.append((z, colour, [proj(*p) for p in ring]))
    for z, colour, pts in sorted(areas, key=lambda a: a[0]):
        d.polygon(pts, fill=colour)
    # Rivers and canals drawn as lines too, so the Danube canal reads at this size.
    for el in els:
        tags = el.get('tags', {})
        if el['type'] == 'way' and tags.get('waterway') in ('river', 'canal'):
            pts = [proj(p['lat'], p['lon']) for p in el.get('geometry', [])]
            if len(pts) > 1:
                d.line(pts, fill=C['water'], width=int((10 if tags.get('waterway') == 'river' else 6) * scale), joint='curve')
    # Railways: grey line with a lighter dash.
    for el in els:
        tags = el.get('tags', {})
        if el['type'] == 'way' and tags.get('railway') in ('rail', 'light_rail'):
            pts = [proj(p['lat'], p['lon']) for p in el.get('geometry', [])]
            if len(pts) > 1:
                d.line(pts, fill=C['rail'], width=int(2.5 * scale), joint='curve')
    # Roads: every casing of a class, then every fill, minor classes first.
    by_class = {}
    for el in els:
        tags = el.get('tags', {})
        cls = tags.get('highway')
        if el['type'] == 'way' and cls in ROADS:
            pts = [proj(p['lat'], p['lon']) for p in el.get('geometry', [])]
            if len(pts) > 1:
                by_class.setdefault(cls, []).append(pts)
    for cls in ROAD_ORDER:
        case, fill, cw, fw = ROADS[cls]
        for pts in by_class.get(cls, []):
            d.line(pts, fill=case, width=max(1, int(cw * scale)), joint='curve')
    for cls in ROAD_ORDER:
        case, fill, cw, fw = ROADS[cls]
        for pts in by_class.get(cls, []):
            d.line(pts, fill=fill, width=max(1, int(fw * scale)), joint='curve')

    img = img.resize((width, height), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    proj1 = Projection(bbox, width, height)
    # The image is shown at about half size, so the type is set large.
    font_area = load_font('DejaVuSans', 26)
    font_small = load_font('DejaVuSans', 18)
    font_water = load_font('DejaVuSerif', 22)
    placed = []
    for lab in info['map'].get('labels', []):
        x, y = proj1(lab['lat'], lab['lon'])
        font = font_water if lab.get('kind') == 'water' else font_small
        colour = C['water_label'] if lab.get('kind') == 'water' else C['label']
        tw = d.textlength(lab['text'], font=font)
        outline(d, (x - tw / 2, y - 11), lab['text'], font, colour)
        placed.append((x, y))
    # District names from the place nodes, spaced out so they do not pile up.
    for el in sorted(els, key=lambda e: {'suburb': 0, 'quarter': 1, 'neighbourhood': 2}.get(e.get('tags', {}).get('place'), 3)):
        tags = el.get('tags', {})
        if el['type'] == 'node' and tags.get('place') in ('suburb', 'quarter') and tags.get('name'):
            x, y = proj1(el['lat'], el['lon'])
            if not (40 < x < width - 40 and 30 < y < height - 30):
                continue
            if any(abs(x - px) < 260 and abs(y - py) < 70 for px, py in placed):
                continue
            font = font_area if tags['place'] == 'suburb' else font_small
            text = tags['name'].upper() if tags['place'] == 'suburb' else tags['name']
            tw = d.textlength(text, font=font)
            outline(d, (x - tw / 2, y - 13), text, font, C['area_label'] if tags['place'] == 'suburb' else C['label'])
            placed.append((x, y))
    img.save(out, 'WEBP', quality=82, method=6)
    print(f'wrote {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB, {len(els)} elements)')


def load_font(name, size):
    """A DejaVu face if the system has it, else whatever Pillow has."""
    for path in (f'/usr/share/fonts/truetype/dejavu/{name}.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                 '/usr/share/fonts/dejavu/DejaVuSans.ttf', '/System/Library/Fonts/Supplemental/Arial.ttf'):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def outline(d, xy, text, font, fill):
    x, y = xy
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)):
        d.text((x + dx, y + dy), text, font=font, fill='#ffffff')
    d.text((x, y), text, font=font, fill=fill)


if __name__ == '__main__':
    place = sys.argv[1] if len(sys.argv) > 1 else 'vienna-1913'
    render(place, ROOT / 'static' / 'places' / place / 'map.webp')
