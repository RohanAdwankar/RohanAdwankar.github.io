# Places

One folder per map post. `data.js` holds the map drawing, the pins, and a
scene per pin: the room, the props, and who was there, where they stood, and
the note that annotates each of them.

## The scenes

Every scene ships as a `.glb` next to the data file, built in Blender by
`scenes/build_scenes.py` from that same data. The script assembles the room
from the Kenney CC0 kits (furniture, mini characters, car kit), builds the
pieces the kits do not have from primitives, recolours and dresses each
figure, poses it with the kit's rig, and exports. Rebuild after editing the
data:

    uv run --python 3.13 --with bpy --with pillow scenes/build_scenes.py vienna-1913

The page loads the glb a scene names in its `glb` field. If the file is
missing it falls back to a rough procedural set built in the browser from the
same props and figures, so a scene can be laid out before it is built.

## Hand-modelled scenes

A scene can also be a file made by hand in Blender. Keep these so the page's
notes and camera still line up:

- Metres, +Y up on export, the floor at 0, the room centred on the origin,
  the viewer's side at +z.
- An Empty named `figure_<id>` just above each person's head, for the name
  chip.
- An Empty named `light_<anything>` wherever a lamp should throw light.
- One animation clip per figure named `anim_<id>`, on an armature named
  `rig_<id>`, if the figure moves.

Keep exports under a few megabytes: the page loads one per pin, on demand.
