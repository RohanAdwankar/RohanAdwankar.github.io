# Places

One folder per map post. `data.js` holds the map drawing, the pins, and a
scene per pin: who was there, where they stood, and the note that annotates
each of them.

## Replacing a procedural set with a Blender scene

Every scene starts as a procedural set built in the browser from the `props`
and `figures` lists. To swap in a modelled one:

1. Model the room in Blender. Metres, Y up on export, the floor at 0, the
   room centred on the origin, matching the procedural set's `at` coordinates
   so the camera and notes still line up.
2. For each figure in the data, add an Empty named `figure_<id>` and place it
   just above that person's head. The name chip attaches there. A figure
   whose Empty is missing is built procedurally on top of the export.
3. File → Export → glTF 2.0, format glTF Binary, +Y up. Save it into this
   folder and set `glb: '<file>.glb'` on the scene.

Keep exports under a few megabytes: the page loads one per pin, on demand.
