"""Surfaces from ambientCG (CC0): parquet, plaster, marble, cloth, leather,
wood. Each one is a colour map and a normal map, tiled by world size, so a
plain box reads as a plastered wall or a waxed floor.

Textures are downloaded once into .cache/textures/ and shrunk on export.
"""
from pathlib import Path
import urllib.request
import zipfile

import bpy

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.cache' / 'textures'

# What each surface in a scene is made of, and how many metres one tile spans.
SURFACES = {
    'parquet': ('WoodFloor034', 2.4), 'planks': ('WoodFloor051', 2.0), 'plaster': ('Plaster001', 3.0),
    'marble': ('Marble012', 2.0), 'stone': ('Travertine009', 2.0), 'carpet': ('Carpet016', 1.5),
    'fabric': ('Fabric030', 0.8), 'leather': ('Leather037', 1.0), 'darkwood': ('Wood051', 1.2),
    'wood': ('Wood094', 1.2), 'concrete': ('Concrete034', 3.0), 'tiles': ('Tiles074', 1.0),
}
_images = {}
_materials = {}


def fetch(asset):
    folder = CACHE / asset
    if not any(folder.glob('*Color.jpg')):
        CACHE.mkdir(parents=True, exist_ok=True)
        zip_path = CACHE / f'{asset}.zip'
        if not zip_path.exists() or zip_path.stat().st_size < 10000:
            print(f'downloading texture {asset}')
            req = urllib.request.Request(f'https://ambientcg.com/get?file={asset}_1K-JPG.zip', headers={'User-Agent': 'curl/8 (vienna-1913 scene build)'})
            with urllib.request.urlopen(req, timeout=300) as r, open(zip_path, 'wb') as f:
                f.write(r.read())
        zipfile.ZipFile(zip_path).extractall(folder)
    colour = next(folder.glob('*Color.jpg'))
    normal = next(iter(folder.glob('*NormalGL.jpg')), None)
    return colour, normal


def image(path, non_colour=False):
    key = str(path)
    if key not in _images:
        img = bpy.data.images.load(key)
        img.name = path.stem
        if non_colour:
            img.colorspace_settings.name = 'Non-Color'
        _images[key] = img
    return _images[key]


def reset():
    _images.clear()
    _materials.clear()


def material(surface, tint=None, rough=None, tile=None, normal_strength=0.6):
    """A Principled material with the surface's colour and normal maps,
    optionally multiplied by a tint colour (hex)."""
    key = (surface, tint, rough, tile)
    if key in _materials:
        return _materials[key]
    asset, size = SURFACES[surface]
    size = tile or size
    colour_path, normal_path = fetch(asset)
    m = bpy.data.materials.new(f'{surface}_{tint or "plain"}')
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = rough if rough is not None else (0.35 if surface in ('marble', 'parquet', 'planks', 'darkwood', 'wood', 'tiles') else 0.85)
    coord = nt.nodes.new('ShaderNodeTexCoord')
    mapping = nt.nodes.new('ShaderNodeMapping')
    mapping.inputs['Scale'].default_value = (1 / size, 1 / size, 1)
    nt.links.new(coord.outputs['UV'], mapping.inputs['Vector'])
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = image(colour_path)
    nt.links.new(mapping.outputs['Vector'], tex.inputs['Vector'])
    colour_out = tex.outputs['Color']
    if tint:
        mix = nt.nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY'
        mix.inputs['Factor'].default_value = 1.0
        h = tint.lstrip('#')
        if len(h) == 3:
            h = ''.join(c * 2 for c in h)
        rgb = tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
        lin = tuple((v / 12.92) if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb)
        # The maps are mid-toned; lift the tint so the product lands on the colour asked for.
        lift = {'carpet': 2.6, 'fabric': 2.2, 'plaster': 1.6}.get(surface, 1.9)
        mix.inputs[7].default_value = (min(1, lin[0] * lift), min(1, lin[1] * lift), min(1, lin[2] * lift), 1)
        nt.links.new(colour_out, mix.inputs[6])
        colour_out = mix.outputs[2]
    nt.links.new(colour_out, bsdf.inputs['Base Color'])
    if normal_path:
        ntex = nt.nodes.new('ShaderNodeTexImage')
        ntex.image = image(normal_path, non_colour=True)
        nt.links.new(mapping.outputs['Vector'], ntex.inputs['Vector'])
        nmap = nt.nodes.new('ShaderNodeNormalMap')
        nmap.inputs['Strength'].default_value = normal_strength
        nt.links.new(ntex.outputs['Color'], nmap.inputs['Color'])
        nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    _materials[key] = m
    return m


def box_uv(obj, size=1.0):
    """Project UVs onto the object from its six sides in world metres, so a
    tiling texture keeps its scale whatever the object's shape or size."""
    if obj.type != 'MESH' or not obj.data.polygons:
        return
    bpy.context.view_layer.update()
    if not obj.data.uv_layers:
        obj.data.uv_layers.new(name='UVMap')
    mw = obj.matrix_world
    uv = obj.data.uv_layers.active.data
    for poly in obj.data.polygons:
        n = (mw.to_3x3() @ poly.normal).normalized()
        ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
        for li in poly.loop_indices:
            p = mw @ obj.data.vertices[obj.data.loops[li].vertex_index].co
            if az >= ax and az >= ay:
                u, v = p.x, p.y
            elif ax >= ay:
                u, v = p.y, p.z
            else:
                u, v = p.x, p.z
            uv[li].uv = (u / size, v / size)


def apply(obj, surface, tint=None, rough=None, tile=None):
    """Give a mesh one textured material, projected by world size."""
    obj.data.materials.clear()
    obj.data.materials.append(material(surface, tint, rough, tile))
    box_uv(obj)
