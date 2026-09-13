#!/usr/bin/env python3
"""Build each scene of a map post as a .glb, with Blender.

The scene layout lives in the post's data.js: one room, a list of props and a
list of figures per pin, the same list the page uses for its procedural
fallback. This script reads that file, assembles the room in Blender from the
Kenney CC0 kits (furniture, mini characters, car kit) plus a few pieces built
from primitives, poses each figure with the kit's own rig, and exports one
glb per pin next to the data file.

Run with the Blender Python module:

    uv run --python 3.13 --with bpy --with pillow scenes/build_scenes.py vienna-1913

Building one pin: add its id (`... vienna-1913 cafe-central`).

The kits are downloaded once into .cache/kits/. Output goes to
static/places/<place>/<pin>.glb; the page loads a pin's glb when the scene's
`glb` field names it.
"""
import io
import json
import math
import os
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

import bpy
from mathutils import Vector
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.cache' / 'kits'
KITS = {
    'furniture': 'https://kenney.nl/media/pages/assets/furniture-kit/440e0608a4-1677580847/kenney_furniture-kit.zip',
    'mini': 'https://kenney.nl/media/pages/assets/mini-characters/bfc7e272b4-1774770718/kenney_mini-characters.zip',
    'car': 'https://kenney.nl/media/pages/assets/car-kit/1a312ec241-1775131960/kenney_car-kit.zip',
}
KIT_DIRS = {
    'furniture': 'Models/GLTF format',
    'mini': 'Models/GLB format',
    'car': 'Models/GLB format',
}
# The Kenney kits share one grid; scaled together a chair is a chair.
KIT_SCALE = 2.3
CHAR_HEIGHT = 0.67  # rest-pose height of a mini character, unscaled

# ---------------------------------------------------------------------------
# Kits
# ---------------------------------------------------------------------------

def fetch_kits():
    for name, url in KITS.items():
        dest = CACHE / name
        if dest.exists():
            continue
        print(f'downloading {name} kit')
        data = urllib.request.urlopen(url, timeout=120).read()
        zipfile.ZipFile(io.BytesIO(data)).extractall(dest)


def kit_path(kit, model):
    return str(CACHE / kit / KIT_DIRS[kit] / f'{model}.glb')


# ---------------------------------------------------------------------------
# Scene data: read the pins straight out of data.js so there is one source.
# ---------------------------------------------------------------------------

def load_pins(place):
    data_js = ROOT / 'static' / 'places' / place / 'data.js'
    script = (
        f"import('{data_js.as_posix()}').then(m => "
        "console.log(JSON.stringify(m.default.pins.map(p => ({id: p.id, scene: p.scene})))))"
    )
    out = subprocess.run(['node', '-e', script], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


# ---------------------------------------------------------------------------
# Blender helpers
# ---------------------------------------------------------------------------

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _mats.clear()
    _imports.clear()
    _actions.clear()


_mats = {}

def hexrgb(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))

def srgb_to_linear(c):
    return tuple((v / 12.92) if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c)

def mat(color, rough=0.8, emission=None, strength=1.0, image=None, metallic=0.0):
    key = (color, rough, emission, strength, image, metallic)
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new(f'm_{len(_mats)}')
    m.use_nodes = True
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (*srgb_to_linear(hexrgb(color)), 1)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metallic
    if emission:
        bsdf.inputs['Emission Color'].default_value = (*srgb_to_linear(hexrgb(emission)), 1)
        bsdf.inputs['Emission Strength'].default_value = strength
    if image:
        tex = m.node_tree.nodes.new('ShaderNodeTexImage')
        tex.image = image
        m.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    _mats[key] = m
    return m


def link(obj, parent=None):
    bpy.context.scene.collection.objects.link(obj)
    if parent is not None:
        obj.parent = parent
    return obj


def bevel(obj, width=0.02, segments=3):
    mod = obj.modifiers.new('bevel', 'BEVEL')
    mod.width = width
    mod.segments = segments
    mod.limit_method = 'ANGLE'
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def box(w, h, d, color, x=0, y=0, z=0, parent=None, rough=0.8, emission=None, strength=1.0, bev=0.02, name='box', metallic=0.0):
    """A box in the page's coordinates: w along x, h up, d along the viewer's
    z. Position is the box centre, like three.js."""
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.active_object
    o.name = name
    o.scale = (w, d, h)
    o.location = (x, -z, y)
    o.data.materials.append(mat(color, rough, emission, strength, metallic=metallic))
    if parent is not None:
        o.parent = parent
    if bev:
        bevel(o, min(bev, w / 3, h / 3, d / 3))
    return o


def cyl(rt, rb, h, color, x=0, y=0, z=0, parent=None, seg=24, rough=0.8, emission=None, strength=1.0, bev=0.015, name='cyl', metallic=0.0):
    bpy.ops.mesh.primitive_cone_add(vertices=seg, radius1=rb, radius2=rt, depth=h)
    o = bpy.context.active_object
    o.name = name
    o.location = (x, -z, y)
    o.data.materials.append(mat(color, rough, emission, strength, metallic=metallic))
    if parent is not None:
        o.parent = parent
    if bev:
        bevel(o, min(bev, h / 3, max(rt, rb) / 3))
    else:
        for p in o.data.polygons:
            p.use_smooth = True
    return o


def sphere(r, color, x=0, y=0, z=0, parent=None, name='sphere'):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=24, ring_count=14)
    o = bpy.context.active_object
    o.name = name
    o.location = (x, -z, y)
    o.data.materials.append(mat(color, 0.7))
    for p in o.data.polygons:
        p.use_smooth = True
    if parent is not None:
        o.parent = parent
    return o


def torus(r, thick, color, x=0, y=0, z=0, parent=None, name='torus'):
    bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=thick, major_segments=24, minor_segments=8)
    o = bpy.context.active_object
    o.name = name
    o.location = (x, -z, y)
    o.data.materials.append(mat(color, 0.5))
    for p in o.data.polygons:
        p.use_smooth = True
    if parent is not None:
        o.parent = parent
    return o


def empty(name, x=0, y=0, z=0, parent=None):
    o = bpy.data.objects.new(name, None)
    o.location = (x, -z, y)
    link(o, parent)
    return o


def group(name, at, rot=0, y=0):
    """An empty in page coordinates, rotated like the page rotates props."""
    g = empty(name, at[0], y, at[1])
    g.rotation_euler = (0, 0, math.radians(rot))
    return g


_imports = {}

def import_kit(kit, model):
    """Import a kit piece once, then hand out copies of it."""
    key = (kit, model)
    if key not in _imports:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=kit_path(kit, model))
        objs = [o for o in bpy.data.objects if o not in before and o.name != 'Icosphere']
        for o in bpy.data.objects:
            if o not in before and o.name == 'Icosphere':
                bpy.data.objects.remove(o)
        _imports[key] = objs
        # Park the master copy far away; copies are what get placed.
        for o in objs:
            if o.parent is None:
                o.location.z = -1000
    return _imports[key]


def copy_tree(objs, parent):
    """Deep-copy a set of imported objects (a kit piece), keeping hierarchy."""
    mapping = {}
    for o in objs:
        c = o.copy()
        if o.data is not None:
            c.data = o.data.copy()
        c.animation_data_clear()
        link(c)
        mapping[o] = c
    for o, c in mapping.items():
        if o.parent in mapping:
            c.parent = mapping[o.parent]
            c.matrix_parent_inverse = o.matrix_parent_inverse.copy()
        else:
            c.parent = parent
            c.location = (0, 0, 0)
        for m in c.modifiers:
            if m.type == 'ARMATURE' and m.object in mapping:
                m.object = mapping[m.object]
    return mapping


def bbox(objs):
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type == 'MESH' for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return lo, hi


def furniture(model, at, rot=0, color=None, scale=KIT_SCALE, y=0, colour_mats=None, parent=None, name=None):
    """Place a Kenney furniture piece centred on `at`, sitting on the floor."""
    g = group(name or model, at, rot, y)
    if parent is not None:
        g.parent = parent
    holder = empty('h', parent=g)
    holder.scale = (scale, scale, scale)
    src = import_kit('furniture', model)
    mapping = copy_tree(src, holder)
    roots = [c for o, c in mapping.items() if c.parent is holder]
    lo, hi = bbox(list(mapping.values()))
    # Kenney pieces have their origin at a corner of the grid cell; move the
    # piece so its footprint is centred on the group and it sits on the floor.
    # The box is measured in world space, so bring it into the holder's frame.
    inv = holder.matrix_world.inverted()
    centre = inv @ ((lo + hi) / 2)
    bottom = inv @ Vector((lo.x, lo.y, lo.z))
    for r in roots:
        r.location = (r.location.x - centre.x, r.location.y - centre.y, r.location.z - bottom.z)
    if color:
        recolour(mapping.values(), color, colour_mats)
    return g


def recolour(objs, color, only=None):
    """Give a kit piece a colour. Kenney pieces carry a few named materials;
    `only` names the ones to change (default: everything but wood/metal)."""
    done = {}
    for o in objs:
        if o.type != 'MESH':
            continue
        for slot in o.material_slots:
            m = slot.material
            if m is None:
                continue
            base = m.name.split('.')[0]
            if only is not None and base not in only:
                continue
            if only is None and base in ('wood', 'metal', 'metalDark', 'woodDark', 'glass'):
                continue
            if m not in done:
                nm = m.copy()
                bsdf = nm.node_tree.nodes.get('Principled BSDF')
                if bsdf:
                    bsdf.inputs['Base Color'].default_value = (*srgb_to_linear(hexrgb(color)), 1)
                    for l in list(bsdf.inputs['Base Color'].links):
                        nm.node_tree.links.remove(l)
                done[m] = nm
            slot.material = done[m]


# ---------------------------------------------------------------------------
# Textures drawn on the fly
# ---------------------------------------------------------------------------

def image_from_pil(name, img):
    path = CACHE / f'{name}.png'
    img.save(path)
    im = bpy.data.images.load(str(path))
    im.name = name
    return im


def checker_image(a, b, n=8):
    img = Image.new('RGB', (512, 512), a)
    d = ImageDraw.Draw(img)
    s = 512 // n
    for i in range(n):
        for j in range(n):
            if (i + j) % 2:
                d.rectangle([i * s, j * s, (i + 1) * s - 1, (j + 1) * s - 1], fill=b)
    return image_from_pil(f'checker_{a}_{b}'.replace('#', ''), img)


def plank_image(base='#8a6a48'):
    r, g, b = [int(v * 255) for v in hexrgb(base)]
    img = Image.new('RGB', (512, 512), (r, g, b))
    d = ImageDraw.Draw(img)
    import random
    rnd = random.Random(7)
    ph = 64
    for row in range(8):
        off = rnd.randint(0, 200)
        x = -off
        while x < 512:
            w = rnd.randint(120, 260)
            k = rnd.uniform(0.86, 1.1)
            d.rectangle([x, row * ph, x + w - 2, (row + 1) * ph - 2], fill=(min(255, int(r * k)), min(255, int(g * k)), min(255, int(b * k))))
            x += w
        d.line([0, (row + 1) * ph - 1, 512, (row + 1) * ph - 1], fill=(int(r * 0.6), int(g * 0.6), int(b * 0.6)))
    return image_from_pil(f'planks_{base.lstrip("#")}', img)


def floor_material(kind, repeat):
    if kind == 'checker':
        im = checker_image('#e8dcc4', '#3a2e24')
    elif kind == 'concrete':
        return mat('#8f8a80', 0.95)
    elif kind == 'grass':
        return mat('#7a9a5a', 0.95)
    else:
        im = plank_image(kind if kind and kind.startswith('#') else '#8a6a48')
    m = mat('#ffffff', 0.75, image=im)
    # Tile the texture across the floor.
    tex = [n for n in m.node_tree.nodes if n.type == 'TEX_IMAGE'][0]
    mapping = m.node_tree.nodes.new('ShaderNodeMapping')
    coord = m.node_tree.nodes.new('ShaderNodeTexCoord')
    mapping.inputs['Scale'].default_value = (repeat, repeat, 1)
    m.node_tree.links.new(coord.outputs['UV'], mapping.inputs['Vector'])
    m.node_tree.links.new(mapping.outputs['Vector'], tex.inputs['Vector'])
    return m


# ---------------------------------------------------------------------------
# The room
# ---------------------------------------------------------------------------

def build_room(room):
    w, d, h = room.get('w', 12), room.get('d', 10), room.get('h', 4.2)
    outdoor = room.get('outdoor')
    fw, fd = (80, 80) if outdoor else (w + 30, d + 30)
    bpy.ops.mesh.primitive_plane_add(size=1)
    floor = bpy.context.active_object
    floor.name = 'floor'
    floor.scale = (fw, fd, 1)
    kind = room.get('floor', '#8a6a48')
    floor.data.materials.append(floor_material(kind, max(fw, fd) / (1.2 if kind == 'checker' else 3.0)))
    if outdoor:
        return
    wall = room.get('wall', '#d9c9a6')
    trim = room.get('trim', '#8a6a48')
    t = 0.24
    # Three walls; the fourth side is where the camera stands.
    box(w + t, h, t, wall, 0, h / 2, -d / 2 - t / 2, bev=0, name='wall_back')
    box(t, h, d + t, wall, -w / 2 - t / 2, h / 2, 0, bev=0, name='wall_left')
    box(t, h, d + t, wall, w / 2 + t / 2, h / 2, 0, bev=0, name='wall_right')
    # Skirting, dado rail, cornice: the three lines that make a wall a room.
    for yy, hh, dd in ((0.09, 0.18, 0.06), (1.05, 0.05, 0.04), (h - 0.12, 0.24, 0.08)):
        box(w, hh, dd, trim, 0, yy, -d / 2 + dd / 2, bev=0.008)
        box(dd, hh, d, trim, -w / 2 + dd / 2, yy, 0, bev=0.008)
        box(dd, hh, d, trim, w / 2 - dd / 2, yy, 0, bev=0.008)
    # Panels below the dado.
    n = max(2, int(w / 1.4))
    for i in range(n):
        x = -w / 2 + (i + 0.5) * (w / n)
        box(w / n - 0.3, 0.6, 0.03, trim, x, 0.62, -d / 2 + 0.03, bev=0.006)
    for win in room.get('windows', []):
        window(win, w, d, h, room.get('sky', '#fff4dc'))


def window(win, w, d, h, sky):
    ww, wh = 1.4, 2.2
    g = empty('window')
    if win['wall'] == 'back':
        g.location = (win['at'], d / 2 - 0.02, 2.1)
        g.rotation_euler = (0, 0, 0)
    elif win['wall'] == 'left':
        g.location = (-w / 2 + 0.02, -win['at'], 2.1)
        g.rotation_euler = (0, 0, math.radians(-90))
    else:
        g.location = (w / 2 - 0.02, -win['at'], 2.1)
        g.rotation_euler = (0, 0, math.radians(90))
    # Frame, a glowing pane, and a cross bar. Recess suggested by a sill.
    box(ww + 0.3, wh + 0.3, 0.12, '#f4efe4', 0, 0, 0, parent=g, bev=0.01, name='frame')
    box(ww, wh, 0.02, '#fff6e0', 0, 0, 0.04, parent=g, emission='#ffe9c0', strength=2.5, bev=0, name='pane')
    box(0.06, wh, 0.1, '#f4efe4', 0, 0, 0.06, parent=g, bev=0.004)
    box(ww, 0.06, 0.1, '#f4efe4', 0, 0.3, 0.06, parent=g, bev=0.004)
    box(ww + 0.5, 0.08, 0.3, '#f4efe4', 0, -wh / 2 - 0.19, 0.12, parent=g, bev=0.01, name='sill')


# ---------------------------------------------------------------------------
# Props: Kenney pieces where they fit, built ones where they do not.
# ---------------------------------------------------------------------------

def light(name, x, y, z, parent=None):
    """Where the page should hang a point light."""
    return empty(f'light_{name}', x, y, z, parent)


def prop_table(p):
    r = p.get('r', 0.55)
    g = group('table', p['at'], p.get('rot', 0))
    top = p.get('color', '#f2ede4')
    cyl(r, r, 0.05, top, 0, 0.75, 0, parent=g, seg=36, rough=0.5)
    cyl(0.05, 0.05, 0.72, '#2b2b2b', 0, 0.37, 0, parent=g)
    cyl(0.28, 0.32, 0.04, '#2b2b2b', 0, 0.02, 0, parent=g, seg=28)
    return g

def prop_chair(p):
    return furniture('chairCushion' if p.get('cushion') else 'chair', p['at'], p.get('rot', 0), p.get('color'))

def prop_couch(p):
    return furniture('loungeSofa', p['at'], p.get('rot', 0), p.get('color', '#8a2f2f'))

def prop_armchair(p):
    return furniture('loungeChair', p['at'], p.get('rot', 0), p.get('color', '#3f5a3a'))

def prop_desk(p):
    g = furniture('desk', p['at'], p.get('rot', 0), p.get('color'))
    box(0.4, 0.02, 0.3, '#f6f0e2', 0.1, 0.88, 0.1, parent=g, bev=0)
    return g

def prop_standingdesk(p):
    g = group('standingdesk', p['at'], p.get('rot', 0))
    c = p.get('color', '#4a2e1c')
    box(0.9, 1.05, 0.45, c, 0, 0.525, 0, parent=g)
    top = box(1.2, 0.05, 0.62, c, 0, 1.12, 0, parent=g)
    top.rotation_euler = (math.radians(12), 0, 0)
    paper = box(0.5, 0.01, 0.35, '#f6f0e2', 0, 1.17, 0.05, parent=g, bev=0)
    paper.rotation_euler = (math.radians(12), 0, 0)
    return g

def prop_bookshelf(p):
    w = p.get('w', 1.6)
    g = group('bookshelf', p['at'], p.get('rot', 0))
    n = max(1, round(w / (0.4 * KIT_SCALE)))
    for i in range(n):
        x = (i - (n - 1) / 2) * 0.4 * KIT_SCALE
        furniture('bookcaseOpen', [x, 0], 0, p.get('color'), parent=g)
        for level in (0.5, 1.0, 1.5):
            furniture('books', [x, 0.02], 0, parent=g, y=level, name='books')
    return g

def prop_cabinet(p):
    g = furniture('bookcaseClosedDoors', p['at'], p.get('rot', 0), p.get('color'))
    return g

def prop_easel(p):
    g = group('easel', p['at'], p.get('rot', 0))
    c = '#8a6a48'
    for x, z, tilt in ((-0.3, 0.1, 0), (0.3, 0.1, 0), (0, -0.25, -14)):
        leg = box(0.05, 1.8, 0.05, c, x, 0.9, z, parent=g, bev=0.006)
        leg.rotation_euler = (math.radians(tilt), 0, 0)
    box(0.7, 0.05, 0.06, c, 0, 0.85, 0.12, parent=g, bev=0.006)
    box(0.7, 0.5, 0.03, '#f4efe0', 0, 1.15, 0.13, parent=g, bev=0.004)
    box(0.5, 0.3, 0.035, p.get('paint', '#9ab8d0'), 0, 1.15, 0.14, parent=g, bev=0)
    return g

def prop_bunk(p):
    g = furniture('bedSingle', p['at'], p.get('rot', 0), p.get('color', '#d8d0c0'), colour_mats=['fabric', 'fabricBed', 'sheets', 'pillow'])
    return g

def prop_podium(p):
    g = group('podium', p['at'], p.get('rot', 0))
    box(1.2, 0.3, 1.2, '#4a2e1c', 0, 0.15, 0, parent=g)
    box(0.04, 1.0, 0.04, '#2b2b2b', 0, 0.5, 0.5, parent=g, bev=0.004)
    stand = box(0.5, 0.36, 0.03, '#2b2b2b', 0, 1.05, 0.5, parent=g, bev=0.004)
    stand.rotation_euler = (math.radians(-30), 0, 0)
    return g

def prop_stand(p):
    g = group('stand', p['at'], p.get('rot', 0))
    box(0.03, 1.0, 0.03, '#2b2b2b', 0, 0.5, 0, parent=g, bev=0.004)
    top = box(0.4, 0.3, 0.02, '#2b2b2b', 0, 1.1, 0, parent=g, bev=0.003)
    top.rotation_euler = (math.radians(-25), 0, 0)
    paper = box(0.3, 0.2, 0.01, '#f6f0e2', 0, 1.1, 0.012, parent=g, bev=0)
    paper.rotation_euler = (math.radians(-25), 0, 0)
    for x, z in ((-0.15, 0.1), (0.15, 0.1), (0, -0.18)):
        box(0.03, 0.03, 0.3, '#2b2b2b', x, 0.015, z, parent=g, bev=0.004)
    return g

def prop_seats(p):
    g = group('seats', p['at'], p.get('rot', 0))
    rows, cols = p.get('rows', 4), p.get('cols', 8)
    for r in range(rows):
        for c in range(cols):
            x = (c - (cols - 1) / 2) * 0.58
            z = r * 0.85
            furniture('chairCushion', [x, z], 180, '#8a2f2f', parent=g, y=r * 0.1, colour_mats=['fabric', 'cushion'])
        box(cols * 0.58, r * 0.1 + 0.02, 0.85, '#3a2416', 0, (r * 0.1) / 2, r * 0.85, parent=g, bev=0) if r else None
    return g

def prop_column(p):
    g = group('column', p['at'], 0)
    c = '#e6dfcf'
    cyl(0.36, 0.36, 0.3, c, 0, 0.15, 0, parent=g, seg=32, bev=0.03)
    cyl(0.28, 0.32, 4.4, c, 0, 2.35, 0, parent=g, seg=32, bev=0)
    cyl(0.44, 0.3, 0.35, c, 0, 4.72, 0, parent=g, seg=32, bev=0.03)
    box(0.9, 0.12, 0.9, c, 0, 4.95, 0, parent=g, bev=0.02)
    return g

def prop_rug(p):
    g = group('rug', p['at'], p.get('rot', 0))
    w, d = p.get('w', 3), p.get('d', 2)
    box(w, 0.02, d, p.get('color', '#7a3030'), 0, 0.01, 0, parent=g, rough=0.95, bev=0.006)
    box(w - 0.4, 0.005, d - 0.4, p.get('color2', '#c8a878'), 0, 0.022, 0, parent=g, rough=0.95, bev=0)
    box(w - 0.6, 0.005, d - 0.6, p.get('color', '#7a3030'), 0, 0.024, 0, parent=g, rough=0.95, bev=0)
    return g

def prop_car(p):
    """A 1913 tourer: a long bonnet, a bench, brass lamps and four kit wheels."""
    g = group('car', p['at'], p.get('rot', 0))
    c = p.get('color', '#2f4a2f')
    box(3.4, 0.12, 1.5, '#222', 0, 0.45, 0, parent=g)  # chassis
    box(1.5, 0.55, 1.1, c, 0.9, 0.85, 0, parent=g, bev=0.05)  # bonnet
    box(1.7, 0.7, 1.4, c, -0.55, 0.85, 0, parent=g, bev=0.05)  # body
    box(0.05, 0.6, 1.3, '#cfe8f0', 0.15, 1.45, 0, parent=g, bev=0, rough=0.2)  # windscreen
    box(1.2, 0.35, 1.2, '#4a2f1a', -0.7, 1.35, 0, parent=g, bev=0.06, rough=0.9)  # bench
    box(0.35, 0.5, 1.2, '#4a2f1a', -1.2, 1.55, 0, parent=g, bev=0.06, rough=0.9)  # seat back
    cyl(0.03, 0.03, 0.5, '#222', -0.2, 1.4, 0.35, parent=g)  # steering column
    wheel = cyl(0.2, 0.2, 0.03, '#222', -0.2, 1.62, 0.35, parent=g, seg=24)
    wheel.rotation_euler = (0, math.radians(90), 0)
    for x, z in ((-1.2, -0.85), (1.1, -0.85), (-1.2, 0.85), (1.1, 0.85)):
        w = cyl(0.42, 0.42, 0.18, '#2b2b2b', x, 0.42, z, parent=g, seg=28, bev=0.03)
        w.rotation_euler = (math.radians(90), 0, 0)
        hub = cyl(0.2, 0.2, 0.2, '#c8a860', x, 0.42, z, parent=g, seg=20, bev=0.02, metallic=0.6, rough=0.4)
        hub.rotation_euler = (math.radians(90), 0, 0)
    for z in (-0.5, 0.5):
        cyl(0.13, 0.13, 0.15, '#d8b860', 1.7, 1.05, z, parent=g, seg=20, metallic=0.7, rough=0.3)
        box(0.05, 0.35, 0.05, '#d8b860', 1.6, 0.85, z, parent=g, metallic=0.7, rough=0.3, bev=0.006)
    # Running boards and mudguards.
    for z in (-0.95, 0.95):
        box(1.6, 0.05, 0.3, '#222', -0.05, 0.5, z, parent=g)
        for x in (-1.2, 1.1):
            arch = box(0.9, 0.06, 0.4, c, x, 0.88, z, parent=g, bev=0.02)
    return g

def prop_workbench(p):
    g = group('workbench', p['at'], p.get('rot', 0))
    box(2.2, 0.1, 0.8, '#8a6a48', 0, 0.85, 0, parent=g)
    for x in (-1.0, 1.0):
        box(0.1, 0.85, 0.7, '#5a4a3a', x, 0.42, 0, parent=g)
    box(0.3, 0.2, 0.2, '#555', 0.5, 1.0, 0, parent=g, metallic=0.6, rough=0.5)
    cyl(0.05, 0.05, 0.5, '#888', -0.4, 0.93, 0.1, parent=g, metallic=0.6, rough=0.5)
    box(0.5, 0.04, 0.3, '#333', -0.7, 0.92, -0.2, parent=g, bev=0.005)
    return g

def prop_chessboard(p):
    g = group('chessboard', p['at'], p.get('rot', 0))
    im = checker_image('#f0e6d0', '#4a3a2a', 8)
    bpy.ops.mesh.primitive_cube_add(size=1)
    b = bpy.context.active_object
    b.scale = (0.42, 0.42, 0.02)
    b.location = (0, 0, 0.79)
    b.parent = g
    b.data.materials.append(mat('#ffffff', 0.6, image=im))
    import random
    rnd = random.Random(3)
    for i in range(12):
        col = '#f6f0e2' if i % 2 else '#222'
        x = -0.16 + (i % 6) * 0.065 + rnd.uniform(-0.01, 0.01)
        z = (-0.14 if i < 6 else 0.14) + rnd.uniform(-0.04, 0.04)
        hgt = 0.06 + rnd.uniform(0, 0.03)
        cyl(0.012, 0.02, hgt, col, x, 0.8 + hgt / 2, z, parent=g, seg=10, bev=0.004)
        sphere(0.014, col, x, 0.8 + hgt + 0.01, z, parent=g)
    return g

def prop_lamp(p):
    g = furniture('lampRoundFloor', p['at'], p.get('rot', 0), p.get('color'))
    light('lamp', 0, 1.55, 0, parent=g)
    return g

def prop_chandelier(p):
    g = group('chandelier', p['at'], 0)
    y = p.get('y', 3.4)
    cyl(0.012, 0.012, 1.4, '#333', 0, y + 0.7, 0, parent=g, seg=8, bev=0)
    ring = cyl(0.6, 0.55, 0.14, '#d8b860', 0, y, 0, parent=g, seg=32, metallic=0.7, rough=0.35)
    cyl(0.12, 0.2, 0.3, '#d8b860', 0, y + 0.2, 0, parent=g, seg=20, metallic=0.7, rough=0.35)
    for i in range(8):
        a = i / 8 * math.pi * 2
        x, z = math.cos(a) * 0.5, math.sin(a) * 0.5
        cyl(0.028, 0.028, 0.22, '#fff5d0', x, y + 0.18, z, parent=g, seg=10, bev=0)
        sphere(0.035, '#ffd070', x, y + 0.33, z, parent=g)
        f = bpy.context.active_object
        f.data.materials.clear()
        f.data.materials.append(mat('#ffd070', 0.5, emission='#ffb040', strength=6))
    light('chandelier', 0, y - 0.2, 0, parent=g)
    return g

def prop_bench(p):
    return furniture('bench', p['at'], p.get('rot', 0), p.get('color'))

def prop_tree(p):
    g = group('tree', p['at'], 0)
    cyl(0.12, 0.18, 1.6, '#5a4030', 0, 0.8, 0, parent=g)
    sphere(1.1, p.get('color', '#5f8a48'), 0, 2.3, 0, parent=g)
    sphere(0.8, p.get('color', '#5f8a48'), 0.5, 2.9, 0.3, parent=g)
    return g

PROPS = {name[5:]: fn for name, fn in globals().items() if name.startswith('prop_')}


# ---------------------------------------------------------------------------
# Figures: Kenney mini characters, recoloured, dressed, posed with the rig.
# ---------------------------------------------------------------------------

def figure(fig):
    model = fig.get('model', 'male-a')
    scale = KIT_SCALE
    g = group(f'fig_{fig["id"]}', fig['at'], fig.get('face', 0), y=0.42 if fig.get('pose') == 'sit' else 0)
    holder = empty('h', parent=g)
    holder.scale = (scale, scale, scale)
    src = import_kit('mini', f'character-{model}')
    if not _actions:
        collect_actions()
    mapping = copy_tree(src, holder)
    arm = [c for c in mapping.values() if c.type == 'ARMATURE'][0]
    arm.location = (0, 0, 0)
    arm.name = f'rig_{fig["id"]}'
    body = [c for c in mapping.values() if c.type == 'MESH' and c.name.startswith('body-mesh')]
    if body and (fig.get('coat') or fig.get('dress')):
        recolour(body, fig.get('dress') or fig.get('coat'), None)
        body[0].material_slots[0].material.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.9
    # The clothes: a coat is a slightly larger torso shell, a collar, buttons.
    dress(fig, arm, scale)
    # Pose: the kit's own animations, one strip per figure so the page can
    # find it by name.
    action = _actions.get(POSES.get(pose_of(fig), 'idle'))
    if action is not None:
        ad = arm.animation_data_create()
        track = ad.nla_tracks.new()
        track.name = f'anim_{fig["id"]}'
        strip = track.strips.new(track.name, int(action.frame_range[0]), action)
        try:
            strip.action_slot = action.slots[0]
        except (AttributeError, IndexError):
            pass
    # The anchor for the name chip sits just above the posed head. It is a
    # plain child of the figure, so a page can find it by name whatever the
    # rig is doing.
    head_z = posed_head_height(arm, action) if action else CHAR_HEIGHT
    anchor = empty(f'figure_{fig["id"]}', 0, head_z * scale + (0.58 if fig.get('hat') else 0.36), 0, parent=g)
    return g


# The page's pose names against the kit's clips. Anyone standing gets the
# idle breath; anyone holding something gets the arm for it.
POSES = {
    'idle': 'idle', 'sit': 'sit', 'hold': 'holding-right', 'both': 'holding-both',
    'interact': 'interact-right', 'yes': 'emote-yes', 'lean': 'idle',
}

def pose_of(fig):
    if fig.get('pose'):
        return fig['pose']
    if fig.get('held'):
        return 'hold'
    return 'idle'


def posed_head_height(arm, action):
    """Top of the head, in the character's own units, with this clip on."""
    ad = arm.animation_data_create()
    ad.action = action
    try:
        ad.action_slot = action.slots[0]
    except (AttributeError, IndexError):
        pass
    bpy.context.scene.frame_set(int(action.frame_range[0]))
    bpy.context.view_layer.update()
    top = (arm.pose.bones['head'].matrix.translation.z + 0.17)
    ad.action = None
    for pb in arm.pose.bones:
        pb.matrix_basis.identity()
    return top


_actions = {}

def collect_actions():
    """After the first character import, keep the clips we pose with and
    delete the rest so the export stays small."""
    keep = set(POSES.values())
    for a in list(bpy.data.actions):
        base = a.name.split('.')[0]
        if base in keep and base not in _actions:
            _actions[base] = a
        elif base not in keep:
            bpy.data.actions.remove(a)


def bone_parent(objs, arm, bone, target):
    """Merge objs into `target` (the kit's head or body mesh) and weight the
    new vertices to `bone`, so they deform with it. Bevels are applied first,
    since a join drops modifiers."""
    if not isinstance(objs, (list, tuple)):
        objs = [objs]
    objs = [o for o in objs if o is not None]
    if not objs:
        return
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.convert(target='MESH')
    n0 = len(target.data.vertices)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    target.select_set(True)
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.join()
    idx = list(range(n0, len(target.data.vertices)))
    for vg in target.vertex_groups:
        vg.remove(idx)
    target.vertex_groups[bone].add(idx, 1.0, 'REPLACE')


# The face colour of each kit character, for bald heads.
SKIN = {
    'male-a': '#7a4a2a', 'male-b': '#f2c9a6', 'male-c': '#f2c9a6', 'male-d': '#f0c4a0',
    'male-e': '#f0c4a0', 'male-f': '#d69a6a', 'female-a': '#7a4a2a', 'female-b': '#f2c9a6',
    'female-c': '#d69a6a', 'female-d': '#f0c4a0', 'female-e': '#f0c4a0', 'female-f': '#f2c9a6',
}


def dress(fig, arm, scale):
    """Hats, hair, beards, moustaches, glasses: small meshes parented to the
    head bone. The kit's head is a cube, face toward the viewer (+z)."""
    g = arm.parent.parent  # the figure group
    top = CHAR_HEIGHT * scale
    hw, hd, hh = 0.45 * scale, 0.34 * scale, 0.33 * scale  # head cube
    hy = top - hh / 2  # head centre
    front = hd / 2  # the face plane
    hair = fig.get('hair', '#2a2016')
    skin = fig.get('skin') or SKIN.get(fig.get('model', 'male-a'), '#e8b896')
    items = []
    # The kit paints hair onto the head cube in its own colours. A thin cap
    # over the top and back sets the colour we want; a bald head gets skin.
    if fig.get('bald') or fig.get('hair') == 'none':
        hair = skin
    if fig.get('model', 'male-a') != 'male-b' or not (fig.get('bald') or fig.get('hair') == 'none'):
        cap_h = hh * 0.34
        items.append(box(hw + 0.02, cap_h, hd + 0.02, hair, 0, top - cap_h / 2 + 0.01, 0, parent=g, bev=0.07, rough=0.9))
    hat = fig.get('hat')
    r = hw / 2  # hats are cut to the head
    if hat == 'top':
        items.append(cyl(r * 0.72, r * 0.72, 0.42, '#151515', 0, top + 0.24, 0, parent=g, seg=32, rough=0.45))
        items.append(cyl(r * 1.15, r * 1.15, 0.03, '#151515', 0, top + 0.04, 0, parent=g, seg=32, rough=0.45))
    elif hat == 'bowler':
        sp = sphere(r * 0.8, '#151515', 0, top + 0.02, 0, parent=g)
        sp.scale.z = 0.62
        items.append(sp)
        items.append(cyl(r * 1.15, r * 1.15, 0.03, '#151515', 0, top + 0.04, 0, parent=g, seg=32, rough=0.45))
    elif hat == 'cap':
        c = fig.get('capColor', '#444')
        items.append(cyl(r * 0.85, r * 0.95, 0.13, c, 0, top + 0.075, 0, parent=g, seg=28))
        items.append(box(hw * 0.55, 0.02, 0.18, c, 0, top + 0.02, front - 0.01, parent=g, bev=0.005))
    elif hat == 'military':
        c = fig.get('capColor', '#2e4a2e')
        items.append(cyl(r * 0.82, r * 0.92, 0.2, c, 0, top + 0.12, 0, parent=g, seg=28))
        items.append(cyl(r * 0.95, r * 0.95, 0.035, '#111', 0, top + 0.03, 0, parent=g, seg=28, rough=0.4))
        items.append(box(hw * 0.55, 0.02, 0.16, '#111', 0, top + 0.02, front - 0.02, parent=g, bev=0.005, rough=0.4))
    if fig.get('beard'):
        colour = hair if fig['beard'] is True else fig['beard']
        long = fig.get('beardLong')
        chin = top - hh
        # A band round the jaw and a block under the chin, so it wraps the
        # face instead of hanging off it.
        items.append(box(hw + 0.02, hh * 0.13, hd + 0.02, colour, 0, chin + hh * 0.05, 0, parent=g, bev=0.03, rough=0.9))
        items.append(box(hw * 0.7, 0.26 if long else 0.1, 0.08, colour, 0, chin - (0.1 if long else 0.02), front - 0.02, parent=g, bev=0.03, rough=0.9))
    if fig.get('moustache'):
        wdt = hw * 0.28 if fig['moustache'] == 'small' else hw * 0.5
        items.append(box(wdt, 0.06, 0.06, hair if hair != skin else fig.get('beard', '#2a2016') if isinstance(fig.get('beard'), str) else '#2a2016', 0, hy - hh * 0.12, front + 0.02, parent=g, bev=0.015))
    if fig.get('glasses'):
        for x in (-hw * 0.19, hw * 0.19):
            ring = torus(hw * 0.12, 0.012, '#222', x, hy + hh * 0.1, front + 0.015, parent=g)
            ring.rotation_euler = (math.radians(90), 0, 0)
            items.append(ring)
        items.append(box(hw * 0.14, 0.014, 0.014, '#222', 0, hy + hh * 0.1, front + 0.015, parent=g, bev=0))
    if fig.get('shawl'):
        items.append(box(hw + 0.2, 0.2, hd + 0.1, fig['shawl'], 0, top - hh - 0.08, 0, parent=g, bev=0.03, rough=0.95))
    head_mesh = next(c for c in arm.children if c.name.startswith('head-mesh'))
    body_mesh = next(c for c in arm.children if c.name.startswith('body-mesh'))
    bone_parent(items, arm, 'head', head_mesh)
    held = fig.get('held')
    # The right hand at rest: below the arm bone's pivot, on the figure's
    # right, which is the viewer's left because the figure faces us.
    # The arm hangs straight down at rest and the holding clips swing it
    # forward from the shoulder, so anything placed just below the hand at
    # rest ends up out in front once the clip is on. The hand is wherever
    # the kit's arm-weighted vertices end.
    hx, hy, hz = hand_position(body_mesh, 'arm-right')
    if held == 'baton':
        b = cyl(0.008, 0.008, 0.5, '#f6f0e2', hx, hy - 0.2, hz, parent=g, seg=8, bev=0)
        bone_parent(b, arm, 'arm-right', body_mesh)
    elif held == 'brush':
        b = cyl(0.012, 0.012, 0.3, '#8a6a48', hx, hy - 0.12, hz, parent=g, seg=8, bev=0)
        bone_parent(b, arm, 'arm-right', body_mesh)
    elif held == 'paper':
        p = box(0.28, 0.01, 0.34, '#f6f0e2', hx + 0.1, hy - 0.16, hz + 0.02, parent=g, bev=0)
        bone_parent(p, arm, 'arm-right', body_mesh)


def hand_position(body_mesh, bone):
    """Bottom centre of the vertices the kit weights to an arm, in page
    coordinates relative to the figure group (x, height, z)."""
    vg = body_mesh.vertex_groups[bone]
    pts = [body_mesh.matrix_world @ v.co for v in body_mesh.data.vertices
           if any(gr.group == vg.index and gr.weight > 0.5 for gr in v.groups)]
    g = body_mesh.parent.parent.parent  # armature -> holder -> group
    inv = g.matrix_world.inverted()
    pts = [inv @ p for p in pts]
    x = sum(p.x for p in pts) / len(pts)
    y = sum(p.y for p in pts) / len(pts)
    z = min(p.z for p in pts)
    return x, z + 0.04, -y


# ---------------------------------------------------------------------------
# Build and export
# ---------------------------------------------------------------------------

def build(pin, out_path):
    spec = pin['scene']
    reset()
    build_room(spec.get('room', {}))
    for p in spec.get('props', []):
        fn = PROPS.get(p['type'])
        if fn is None:
            print(f'  no builder for prop {p["type"]}, skipped')
            continue
        fn(p)
    for fig in spec.get('figures', []):
        figure(fig)
    for (kit, model), objs in _imports.items():
        for o in objs:
            bpy.data.objects.remove(o, do_unlink=True)
    for a in list(bpy.data.actions):
        if a not in _actions.values():
            bpy.data.actions.remove(a)
    bpy.ops.export_scene.gltf(
        filepath=str(out_path),
        export_format='GLB',
        export_apply=True,
        export_yup=True,
        export_animations=True,
        export_animation_mode='NLA_TRACKS',
        export_lights=False,
        export_cameras=False,
        export_image_format='AUTO',
        export_jpeg_quality=85,
    )
    print(f'  wrote {out_path.relative_to(ROOT)} ({out_path.stat().st_size // 1024} KB)')


def main():
    place = sys.argv[1] if len(sys.argv) > 1 else 'vienna-1913'
    only = set(sys.argv[2:])
    CACHE.mkdir(parents=True, exist_ok=True)
    fetch_kits()
    out_dir = ROOT / 'static' / 'places' / place
    for pin in load_pins(place):
        if only and pin['id'] not in only:
            continue
        print(pin['id'])
        build(pin, out_dir / f'{pin["id"]}.glb')


if __name__ == '__main__':
    main()
