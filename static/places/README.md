# Places

One folder per map post. `data.js` holds the map drawing, the pins, and a
scene per pin: the room, the props, and who was there, where they stood, and
the note that annotates each of them.

## The map

`map.webp` is the real city, drawn from OpenStreetMap by `scenes/build_map.py`
in the style of the map app everyone reads without thinking. `data.js` gives
the bounding box (south, west, north, east) and a few hand-placed labels; each
pin carries a latitude and longitude and the page projects it onto the image
with the same Mercator projection. Pins outside the box sit on the border
with an arrow. Rebuild after moving the box or the labels:

    uv run --with pillow scenes/build_map.py vienna-1913

The Overpass query result is cached in `.cache/`.

## The scenes

Every scene ships as a `.glb` next to the data file, built in Blender by
`scenes/build_scenes.py` from that same data. The script assembles the room
from the Kenney CC0 kits (furniture, car kit), builds the pieces the kits do
not have from primitives, and makes each person with MakeHuman through the
MPFB Blender extension (`scenes/makehuman_figures.py`): body by age, sex and
build, a suit or dress tinted to the `coat`/`dress` colour, hair, hat,
spectacles, and a pose from the MakeHuman pose library, then exports.
Rebuild after editing the data:

    uv run --python 3.13 --with bpy --with pillow scenes/build_scenes.py vienna-1913

The first run clones MPFB into Blender's extensions directory and downloads
the MakeHuman asset packs it uses (system assets, poses, hats, glasses) into
`.cache/`. `FIGURES=kenney` builds the people from the Kenney mini
characters instead.

## The look

The scenes are drawn, not rendered: the look of an animated history
explainer. `STYLE=toon` is the default for the build script and the page.

- Every surface is one flat colour (`scenes/textures.py` gives each
  material a colour instead of a map).
- Each person keeps MakeHuman's proportions and pose, and gets flat skin
  and clothes, hair as a cap of the scalp in the hair colour, dot eyes, a
  brow over each, ring spectacles, and a beard or moustache as a shell of
  the lower face. The suit's own texture is read once per face and
  posterised into coat, shirt and tie.
- The page shades everything in three bands of light (`MeshToonMaterial`)
  and draws an ink line round each shape (`OutlineEffect`), over a paper
  background with a little grain and a soft vignette.

`STYLE=real` builds the photographic version instead: surfaces from ambientCG
(CC0), parquet, plaster, marble, travertine, carpet, cloth and leather, tiled
by world size, downloaded once into `.cache/textures/`, with MakeHuman's own
skin, hair and clothes textures. A place can set `style: 'real'` in its
`data.js` to have the page light that version as it is.

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
