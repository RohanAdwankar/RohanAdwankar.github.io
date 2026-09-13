# Vienna, 1913

In 1913 Freud, Trotsky, Stalin, Hitler, Tito, the Emperor and the heir who was going to get shot in Sarajevo all lived within a tram ride of each other. Most of them drank in the same handful of cafés.

Drag the little man onto a pin.

<link rel="stylesheet" href="/js/places/places.css">
<div id="place-vienna-1913"></div>
<script type="importmap">
{ "imports": {
  "three": "/js/three/three.module.js",
  "three/addons/": "/js/three/addons/"
} }
</script>
<script type="module">
import { mountPlace } from '/js/places/places.js';
import place from '/places/vienna-1913/data.js';
mountPlace(document.getElementById('place-vienna-1913'), place);
</script>

## Who is where

- **Café Central.** Trotsky playing chess. Peter Altenberg using the café as a postal address. Alfred Adler, two years after walking out on Freud.
- **Berggasse 19.** Freud, the couch, and a seventeen-year-old Anna.
- **Musikverein.** The Skandalkonzert of 31 March. Schoenberg conducting, Berg's Altenberg songs, a fistfight, a lawsuit.
- **Hofburg.** Franz Joseph at his standing desk at half past four in the morning.
- **Belvedere.** Franz Ferdinand and Sophie, fifteen months out.
- **Schönbrunner Schloßstraße.** Stalin for five weeks, with Bukharin reading the German for him.
- **Meldemannstraße.** Hitler painting postcards in a men's hostel, three months from leaving for Munich.
- **Wiener Neustadt.** Josip Broz test-driving cars at Daimler, a year before the war.

## How it is made

The map is not a map. It is an SVG drawn to look like the app everyone can read without thinking, with a street or two in the right place and the rest made up. The point is the pins, and the man in the corner who does the same thing there that he does in Google Maps.

Each pin opens a scene in [three.js](https://threejs.org). Right now the scenes are built in the browser from a short list of props and people, so a room is twenty lines of data and a person is a coat colour, a hat and a note. The plan is to replace each one with a set modelled in Blender and exported as glTF. The annotations hang off named empties in the file, so the notes and the camera do not change when the model does.

The people are the point, so the notes try to say what each of them was actually doing that year, and only that. Sources are at the bottom of each scene. Where a story is famous because it cannot be checked, it says so.
