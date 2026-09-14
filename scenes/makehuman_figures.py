"""Figures built with MakeHuman (the MPFB Blender extension) from a scene's
figure list: a proportioned body, skin by age, a suit, hair, hat, glasses,
and a pose from the MakeHuman pose library, exported as static meshes.

Needs MPFB installed as an extension in the Blender Python module and the
MakeHuman asset packs unpacked into its data directory. `install()` does
both, downloading what is missing into .cache/.
"""
import glob
import hashlib
import importlib
import io
import math
import os
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

import bpy
from mathutils import Vector

MPFB_REPO = 'https://github.com/makehumancommunity/mpfb2'
PACKS = {
    # name: (url, licence)
    'makehuman_system_assets': ('https://files.makehumancommunity.org/asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip', 'CC0'),
    'makehuman_system_poses': ('https://files.makehumancommunity.org/asset_packs/makehuman_system_poses/makehuman_system_poses_cc0.zip', 'CC0'),
    'poses01': ('https://files.makehumancommunity.org/asset_packs/poses01/poses01_cc0.zip', 'CC0'),
    'poses03': ('https://files.makehumancommunity.org/asset_packs/poses03/poses03_cc0.zip', 'CC0'),
    'hats03': ('https://files.makehumancommunity.org/asset_packs/hats03/hats03_cc-by.zip', 'CC-BY'),
    'glasses01': ('https://files.makehumancommunity.org/asset_packs/glasses01/glasses01_cc0.zip', 'CC0'),
}

S = {}  # MPFB services, filled by install()
DATA = None  # MPFB's data directory


def install(cache):
    """Enable MPFB (cloning it into the extensions directory if needed), the
    bvh importer, and make sure the asset packs are unpacked."""
    global DATA
    import addon_utils
    ext_dir = Path(bpy.utils.user_resource('EXTENSIONS')) / 'user_default'
    target = ext_dir / 'mpfb'
    if not target.exists():
        src = cache / 'mpfb2'
        if not src.exists():
            print('cloning MPFB')
            os.system(f'git clone -q --depth 1 {MPFB_REPO} "{src}"')
        ext_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src / 'src' / 'mpfb', target)
    addon_utils.enable('io_anim_bvh', default_set=False)
    try:
        bpy.ops.extensions.repo_sync_all()
    except Exception:
        pass
    name = next(m.__name__ for m in addon_utils.modules() if m.__name__.endswith('mpfb'))
    addon_utils.enable(name, default_set=True, persistent=True)

    def find(pkg, key):
        for amod in list(sys.modules):
            if amod.endswith(pkg):
                return getattr(importlib.import_module(amod), key)
        raise ImportError(pkg)
    for key, pkg in {
        'Human': 'mpfb.services.humanservice', 'Target': 'mpfb.services.targetservice',
        'Asset': 'mpfb.services.assetservice', 'Animation': 'mpfb.services.animationservice',
        'Rig': 'mpfb.services.rigservice', 'Export': 'mpfb.services.exportservice',
        'Location': 'mpfb.services.locationservice',
    }.items():
        S[key] = find(pkg, key + 'Service')
    S['Props'] = find('mpfb.entities.objectproperties', 'HumanObjectProperties')
    DATA = Path(S['Location'].get_user_data())
    for pack, (url, _licence) in PACKS.items():
        marker = DATA / 'packs' / f'{pack}.installed'
        if marker.exists():
            continue
        zip_path = cache / f'{pack}.zip'
        if not zip_path.exists():
            print(f'downloading {pack}')
            with urllib.request.urlopen(url, timeout=600) as r, open(zip_path, 'wb') as f:
                shutil.copyfileobj(r, f)
        zipfile.ZipFile(zip_path).extractall(DATA)
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(url)
    S['Asset'].update_asset_list(asset_subdir='clothes', asset_type='mhclo')


# ---------------------------------------------------------------------------
# What the data's words mean in MakeHuman terms
# ---------------------------------------------------------------------------

HATS = {
    'top': 'elvs_tophat1', 'bowler': 'culturalibre_cl_bowler_hat',
    'cap': 'elvs_male_flat_cap1', 'military': 'mindfront_patrol_cap', 'fedora': 'fedora01',
}
STANDING = ['standing01', 'standing02', 'standing03', 'standing04', 'callharvey3d_standingnatural',
            'callharvey3d_standingatease', 'callharvey3d_standingdefault', 'sohh_standing1', 'sohh_standing2']
POSES = {
    # On a chair at a table or desk: upright, legs down.
    'sit': ['callharvey3d_sittingdefault', 'callharvey3d_sittingnatural', 'anrico_sitting03', 'anrico_sitting07'],
    # In an armchair or on a sofa: settled in.
    'lounge': ['callharvey3d_sittinglegscrossed', 'anrico_sitting10', 'anrico_sitting04'],
    'hold': ['mindfront_standing_holding_wine_glass'],
    'both': ['mindfront_standing_holding_wine_glass'],
    'interact': ['mindfront_standing_holding_wine_glass'],
    'attention': ['callharvey3d_standingatattention'],
    'akimbo': ['drednicolson_arms_akimbo'],
    'lean': ['jjones_leaning_on_counter_hands_folded'],
    'yes': ['standing05'],
    'idle': STANDING,
}
SEAT_HEIGHT = 0.46  # a kit chair at scene scale


def age_macro(years):
    """MakeHuman's age slider: 0 is a baby, 0.5 is 25, 1 is 90."""
    if years <= 25:
        return max(0.0, years / 25 * 0.5)
    return min(1.0, 0.5 + (years - 25) / 65 * 0.5)


def skin_for(fig, years):
    sex = 'female' if fig.get('sex') == 'female' else 'male'
    band = 'young' if years < 42 else 'middleage' if years < 65 else 'old'
    return f'{band}_caucasian_{sex}'


def pick(options, seed):
    h = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    return options[h % len(options)]


def hexrgb(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def srgb_to_linear(c):
    return tuple((v / 12.92) if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c)


# ---------------------------------------------------------------------------
# Building one figure
# ---------------------------------------------------------------------------

def figure(fig, group, box, cyl, mat):
    """Build the figure under `group` (an empty already placed and turned).
    `box`, `cyl`, `mat` are the scene script's primitive helpers, for the
    held things. Returns (anchor_height, seat_offset)."""
    Human, Target, Asset, Animation, Rig, Export, Props = (S[k] for k in ('Human', 'Target', 'Asset', 'Animation', 'Rig', 'Export', 'Props'))
    years = fig.get('age', 40)
    female = fig.get('sex') == 'female'
    h = Human.create_human()
    macros = dict(
        gender=0.0 if female else 1.0, age=age_macro(years),
        weight=fig.get('weight', 0.5), muscle=fig.get('muscle', 0.5),
        height=fig.get('height', 0.5), proportions=fig.get('proportions', 0.5),
        caucasian=1.0, african=0.0, asian=0.0,
    )
    for k, v in macros.items():
        Props.set_value(k, v, entity_reference=h)
    Target.reapply_macro_details(h)
    skin = DATA / 'skins' / skin_for(fig, years) / f'{skin_for(fig, years)}.mhmat'
    Human.set_character_skin(str(skin), h, skin_type='GAMEENGINE')
    rig = Human.add_builtin_rig(h, 'default')

    def add(kind, name, atype, subdir=None):
        subdir = subdir or kind
        path = Asset.find_asset_absolute_path(name, asset_subdir=subdir)
        if path is None:
            hits = glob.glob(str(DATA / subdir / name / '*.mhclo'))
            path = hits[0] if hits else None
        if path is None:
            print(f'  no asset {subdir}/{name}')
            return None
        return Human.add_mhclo_asset(path, h, asset_type=atype, material_type='GAMEENGINE', subdiv_levels=0)

    parts = {}
    parts['eyes'] = add('eyes', 'low-poly.mhclo', 'Eyes')
    parts['eyebrows'] = add('eyebrows', 'eyebrow006.mhclo' if female else 'eyebrow001.mhclo', 'Eyebrows')
    parts['eyelashes'] = add('eyelashes', 'eyelashes01.mhclo', 'Eyelashes')
    parts['teeth'] = add('teeth', 'teeth_base.mhclo', 'Teeth')
    parts['tongue'] = add('tongue', 'tongue01.mhclo', 'Tongue')
    if not fig.get('bald') and fig.get('hair') != 'none':
        style = fig.get('hairstyle') or ('long01' if female else pick(['short02', 'short03', 'short04'], fig['id']))
        parts['hair'] = add('hair', style, 'Hair')
    suit = fig.get('suit') or ('female_elegantsuit01' if female else 'male_elegantsuit01')
    parts['suit'] = add('clothes', suit, 'Clothes')
    parts['shoes'] = add('clothes', 'shoes03' if female else 'shoes01', 'Clothes')
    if fig.get('hat') in HATS:
        parts['hat'] = add('clothes', HATS[fig['hat']], 'Clothes')
    if fig.get('glasses'):
        parts['glasses'] = add('clothes', 'frankyaye_glasses_library_male', 'Clothes')

    # Pose from the library, then freeze it into the meshes.
    pose_key = fig.get('pose') or ('hold' if fig.get('held') else 'idle')
    if pose_key == 'lounge':
        fig = dict(fig, pose='sit')
    pose_name = pick(POSES.get(pose_key, STANDING), fig['id'] + pose_key)
    bvh = DATA / 'poses' / pose_name / f'{pose_name}.bvh'
    if bvh.exists():
        Animation.import_bvh_file_as_pose(rig, str(bvh))
    else:
        print(f'  no pose {pose_name}')
    Rig.apply_pose_as_rest_pose(rig)
    # Where the hands and head are, before the rig goes.
    bpy.context.view_layer.update()
    def bone_at(name):
        try:
            return rig.matrix_world @ rig.pose.bones[name].head
        except KeyError:
            return None
    head_top = bone_at('head')
    hand = bone_at('finger2-1.R') or bone_at('wrist.R')
    wrist = bone_at('wrist.R')
    Export.bake_modifiers_remove_helpers(h, bake_masks=True, bake_subdiv=True, remove_helpers=True, also_proxy=True)

    meshes = [h] + [o for o in rig.children_recursive if o.type == 'MESH' and o is not h]
    for o in meshes:
        bpy.context.view_layer.objects.active = o
        for m in list(o.modifiers):
            try:
                bpy.ops.object.modifier_apply(modifier=m.name)
            except Exception:
                o.modifiers.remove(m)
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
    bpy.data.objects.remove(rig)

    fix_materials(meshes, fig)
    shrink_under_clothes(h)
    if fig.get('beard') or fig.get('moustache'):
        facial_hair(h, fig, parts, mat)

    # Sitting figures: the seat of the trousers goes on the chair, centred on
    # it, whatever the pose did with the hips.
    seat_offset = 0.0
    shift = Vector((0, 0, 0))
    if pose_key in ('sit', 'lounge'):
        seat = fig.get('_seat', SEAT_HEIGHT)
        names = {vg.index: vg.name for vg in h.vertex_groups}
        pts = [h.matrix_world @ v.co for v in h.data.vertices
               if sum(g.weight for g in v.groups if names[g.group].startswith(('pelvis', 'thigh', 'upperleg'))) > 0.6]
        if pts:
            cx = sum(p.x for p in pts) / len(pts)
            cy = sum(p.y for p in pts) / len(pts)
            seat_offset = seat - min(p.z for p in pts)
            shift = Vector((-cx, -cy + 0.04, seat_offset))
    for o in meshes:
        o.parent = group
        o.matrix_parent_inverse.identity()
        o.location += shift
        o.name = f'{fig["id"]}_{o.name}'
    if hand is not None:
        hand = hand + shift
        if wrist is not None:
            wrist = wrist + shift
    if head_top is not None:
        head_top = head_top + shift
    for o in list(bpy.data.objects):
        if o.name.startswith('Human') and o.parent is None and o not in meshes and o.type != 'EMPTY':
            bpy.data.objects.remove(o)

    # Something in the right hand, in page coordinates relative to the group.
    held = fig.get('held')
    if held and hand is not None:
        hx, hy, hz = hand.x, hand.z, -hand.y
        d = (hand - wrist).normalized() if wrist is not None else Vector((0, -1, 0))
        # Page-space direction of the fingers.
        dx, dy, dz = d.x, d.z, -d.y
        if held == 'baton':
            b = cyl(0.006, 0.006, 0.45, '#f6f0e2', hx + dx * 0.15, hy + dy * 0.15, hz + dz * 0.15, parent=group, seg=8, bev=0)
            b.rotation_euler = Vector((0, 0, 1)).rotation_difference(Vector((dx, -dz, dy))).to_euler()
        elif held == 'brush':
            b = cyl(0.008, 0.008, 0.26, '#8a6a48', hx + dx * 0.08, hy + dy * 0.08, hz + dz * 0.08, parent=group, seg=8, bev=0)
            b.rotation_euler = Vector((0, 0, 1)).rotation_difference(Vector((dx, -dz, dy))).to_euler()
        elif held == 'paper':
            p = box(0.22, 0.3, 0.004, '#f6f0e2', hx + dx * 0.1, hy + dy * 0.1 + 0.06, hz + dz * 0.1 + 0.04, parent=group, bev=0)
            p.rotation_euler = (math.radians(-15), 0, 0)
    anchor_h = (head_top.z if head_top is not None else 1.6) + 0.22 + (0.12 if fig.get('hat') else 0)
    return anchor_h


def lowest_z(body, prefixes):
    names = {vg.index: vg.name for vg in body.vertex_groups}
    zs = [(body.matrix_world @ v.co).z for v in body.data.vertices
          if sum(g.weight for g in v.groups if names[g.group].startswith(prefixes)) > 0.6]
    return min(zs) if zs else 0.0


def fix_materials(meshes, fig):
    """Opaque things opaque and cut-outs clipped, so nothing exports as
    blended and sorts against itself; tint the suit and the hair."""
    for o in meshes:
        lname = o.name.lower()
        cutout = any(k in lname for k in ('short0', 'long0', 'bob0', 'braid', 'ponytail', 'afro', 'eyebrow', 'eyelash', 'low-poly', 'glasses'))
        for slot in o.material_slots:
            m = slot.material
            if not m or not m.node_tree:
                continue
            nt = m.node_tree
            bsdf = nt.nodes.get('Principled BSDF')
            if cutout:
                m.blend_method = 'CLIP'
                if hasattr(m, 'alpha_threshold'):
                    m.alpha_threshold = 0.5
            else:
                for l in list(nt.links):
                    if bsdf and l.to_node == bsdf and l.to_socket.name == 'Alpha':
                        nt.links.remove(l)
                if bsdf:
                    bsdf.inputs['Alpha'].default_value = 1.0
                m.blend_method = 'OPAQUE'
                m.use_backface_culling = True
            if bsdf:
                bsdf.inputs['Roughness'].default_value = 0.75 if 'suit' in lname or 'shoes' in lname else 0.6
            tint = None
            if ('suit' in lname or 'coveralls' in lname) and (fig.get('coat') or fig.get('dress')):
                tint = fig.get('dress') or fig.get('coat')
            if any(k in lname for k in ('short0', 'long0', 'bob0', 'braid', 'ponytail')) and fig.get('hair') not in (None, 'none'):
                tint = fig['hair']
            if tint and bsdf:
                tint_material(nt, bsdf, tint)


def tint_material(nt, bsdf, colour):
    """Multiply the base colour texture by a colour. The suit textures are
    mid grey with detail, so this reads as a coloured cloth."""
    link = next((l for l in nt.links if l.to_node == bsdf and l.to_socket.name == 'Base Color'), None)
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.blend_type = 'MIX'
    mix.inputs['Factor'].default_value = 0.6
    c = srgb_to_linear(hexrgb(colour))
    mix.inputs[7].default_value = (min(1, c[0] * 1.3), min(1, c[1] * 1.3), min(1, c[2] * 1.3), 1)
    if link:
        nt.links.new(link.from_socket, mix.inputs[6])
        nt.links.remove(link)
    else:
        mix.inputs[6].default_value = bsdf.inputs['Base Color'].default_value
    nt.links.new(mix.outputs[2], bsdf.inputs['Base Color'])


def shrink_under_clothes(body):
    """Pull the body in a little wherever clothes could cover it, leaving
    the head, neck and hands alone, so knees and elbows stay inside."""
    keep = ('head', 'neck', 'wrist', 'finger', 'palm', 'hand', 'eye', 'jaw', 'tongue', 'teeth', 'special', 'clavicle')
    names = {vg.index: vg.name for vg in body.vertex_groups}
    for v in body.data.vertices:
        exposed = sum(g.weight for g in v.groups if names[g.group].startswith(keep))
        if exposed < 0.5:
            v.co -= v.normal * 0.006


def facial_hair(body, fig, parts, mat):
    """A beard or moustache as a shell of the lower face, pushed out along
    the normals and given a dark, slightly rough material. It reads as
    facial hair from where the camera stands."""
    tongue = parts.get('tongue')
    if tongue is None:
        return
    mouth = tongue.matrix_world @ Vector(sum((Vector(c) for c in tongue.bound_box), Vector()) / 8)
    names = {vg.index: vg.name for vg in body.vertex_groups}
    head_verts = [v for v in body.data.vertices if sum(g.weight for g in v.groups if names[g.group].startswith(('head', 'jaw'))) > 0.5]
    if not head_verts:
        return
    chin_z = min((body.matrix_world @ v.co).z for v in head_verts if (body.matrix_world @ v.co).y < mouth.y + 0.02)
    front = mouth.y  # the face is at -y
    keep = set()
    for v in head_verts:
        p = body.matrix_world @ v.co
        if p.y > front + 0.075:  # not on the face
            continue
        if fig.get('beard') and chin_z - 0.01 <= p.z <= mouth.z - 0.008 and abs(p.x - mouth.x) < 0.08:
            keep.add(v.index)
        if fig.get('moustache') and mouth.z + 0.006 <= p.z <= mouth.z + 0.028 and abs(p.x - mouth.x) < (0.022 if fig['moustache'] == 'small' else 0.05) and p.y < front + 0.03:
            keep.add(v.index)
    if not keep:
        return
    shell = body.copy()
    shell.data = body.data.copy()
    bpy.context.scene.collection.objects.link(shell)
    shell.parent = body.parent
    shell.matrix_parent_inverse = body.matrix_parent_inverse.copy()
    shell.matrix_world = body.matrix_world.copy()
    shell.name = f'{fig["id"]}_facial_hair'
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(shell.data)
    bm.verts.ensure_lookup_table()
    doomed = [v for v in bm.verts if v.index not in keep]
    bmesh.ops.delete(bm, geom=doomed, context='VERTS')
    for v in bm.verts:
        v.co += v.normal * 0.012
    bm.to_mesh(shell.data)
    bm.free()
    shell.data.materials.clear()
    colour = fig['beard'] if isinstance(fig.get('beard'), str) else fig.get('hair', '#2a2016')
    if colour == 'none':
        colour = '#2a2016'
    shell.data.materials.append(mat(colour, 0.95))
    shell.vertex_groups.clear()
