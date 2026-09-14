HTML is generated from Markdown by `scripts/build.py` into `dist/`.

Local build:

```bash
uv run python scripts/build.py
```

Deployment:

```bash
git push origin main
```

The GitHub Actions workflow at `.github/workflows/deploy.yml` rebuilds the site and deploys it to GitHub Pages on push.

Posts whose filename starts with `_` are drafts. A draft is still built and deployed at `posts/<name>.html` (without the underscore), so it can be previewed and shared by link, but it is not listed on the homepage. Rename the file without the underscore to list it.

Files under `static/` are copied into `dist/` as they are. `static/js/semfont/` is a copy of the [semfont](https://github.com/RohanAdwankar/semfont) engine, which the semfont post runs in the browser. `static/js/three/` is three.js 0.170.0 (`three.module.min.js` and the four addons the map posts use), which the map posts under `static/places/` load through an import map.

The map posts under `static/places/` ship their 3D scenes as glTF files built by `scenes/build_scenes.py`, which needs Blender's Python module: `uv run --python 3.13 --with bpy --with pillow scenes/build_scenes.py vienna-1913`. It downloads the Kenney kits and the MakeHuman extension and asset packs it assembles from into `.cache/`, which git ignores; see `static/places/README.md`.
