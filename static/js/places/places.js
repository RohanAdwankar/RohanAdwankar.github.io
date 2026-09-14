// A mock map with pins. Drag the little man onto a pin and the page opens a
// 3D scene of what was happening there, with the people annotated.
//
// A place is data (see static/places/<id>/data.js): a map drawing, pins, and
// one scene per pin. A scene is either a Blender export (a .glb next to the
// data file) or, until one exists, a procedural set built here from a short
// list of props and figures. Either way the annotations come from the data.

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const SVG_NS = 'http://www.w3.org/2000/svg';

function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'class') node.className = v;
    else if (k === 'text') node.textContent = v;
    else if (k === 'html') node.innerHTML = v;
    else node.setAttribute(k, v);
  }
  for (const c of children) node.append(c);
  return node;
}

function svg(tag, attrs = {}) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  return node;
}

// ---------------------------------------------------------------------------
// The map
// ---------------------------------------------------------------------------

// Drawing helpers handed to a place's draw(map) function. Coordinates are in
// the map's own units (the viewBox), so a place lays itself out once.
class MapCanvas {
  constructor(root, width, height) {
    this.w = width;
    this.h = height;
    this.svg = svg('svg', { viewBox: `0 0 ${width} ${height}`, class: 'pl-map-svg' });
    this.layers = {};
    for (const name of ['land', 'park', 'water', 'block', 'road', 'label', 'pin']) {
      this.layers[name] = svg('g', { class: `pl-layer pl-${name}` });
      this.svg.append(this.layers[name]);
    }
    this.layers.land.append(svg('rect', { x: 0, y: 0, width, height, class: 'pl-land' }));
    root.append(this.svg);
  }
  water(d) { this.layers.water.append(svg('path', { d, class: 'pl-water' })); }
  park(d) { this.layers.park.append(svg('path', { d, class: 'pl-park' })); }
  block(d) { this.layers.block.append(svg('path', { d, class: 'pl-block' })); }
  road(d, kind = 'minor') {
    // A road is a grey casing under a lighter fill, like the real thing.
    this.layers.road.append(svg('path', { d, class: `pl-road-case pl-${kind}` }));
    this.layers.road.append(svg('path', { d, class: `pl-road-fill pl-${kind}` }));
  }
  label(text, x, y, kind = 'area') {
    const t = svg('text', { x, y, class: `pl-label pl-label-${kind}` });
    t.textContent = text;
    this.layers.label.append(t);
  }
}

// A Google-style red teardrop with a dot. Off-map pins sit at the edge with
// an arrow and a distance, the way the reddit map did it.
function makePin(pin) {
  const g = svg('g', { class: 'pl-pin', transform: `translate(${pin.x} ${pin.y})` });
  g.dataset.id = pin.id;
  g.append(svg('circle', { cx: 0, cy: 0, r: 22, class: 'pl-pin-halo' }));
  g.append(svg('ellipse', { cx: 0, cy: 2, rx: 7, ry: 3, class: 'pl-pin-shadow' }));
  g.append(svg('path', {
    d: 'M0 0 C -4 -8 -12 -14 -12 -24 A 12 12 0 1 1 12 -24 C 12 -14 4 -8 0 0 Z',
    class: 'pl-pin-body',
  }));
  g.append(svg('circle', { cx: 0, cy: -24, r: 4.5, class: 'pl-pin-dot' }));
  const anchor = pin.labelSide === 'left' ? 'end' : 'start';
  const lx = pin.labelSide === 'left' ? -16 : 16;
  const text = pin.offmap ? `${pin.offmap.arrow} ${pin.label} · ${pin.offmap.distance}` : pin.label;
  const t = svg('text', { x: lx, y: -20, class: 'pl-pin-label', 'text-anchor': anchor });
  t.textContent = text;
  const bg = svg('rect', { class: 'pl-pin-label-bg', rx: 4, ry: 4 });
  g.append(bg, t);
  // Size the label plate once it is in the document, and again whenever
  // the type size changes.
  g.sizeLabel = () => {
    const b = t.getBBox();
    bg.setAttribute('x', b.x - 6); bg.setAttribute('y', b.y - 3);
    bg.setAttribute('width', b.width + 12); bg.setAttribute('height', b.height + 6);
  };
  requestAnimationFrame(g.sizeLabel);
  return g;
}

const PEGMAN_SVG = `
<svg viewBox="0 0 40 64" class="pl-pegman-svg" aria-hidden="true">
  <g class="pl-pegman-body">
    <circle cx="20" cy="9" r="7"/>
    <rect x="12" y="16" width="16" height="22" rx="6"/>
    <rect x="8" y="18" width="5" height="16" rx="2.5" transform="rotate(12 8 18)"/>
    <rect x="27" y="18" width="5" height="16" rx="2.5" transform="rotate(-12 32 18)"/>
    <rect x="12.5" y="36" width="6" height="22" rx="3"/>
    <rect x="21.5" y="36" width="6" height="22" rx="3"/>
    <rect x="11" y="56" width="8" height="5" rx="2"/>
    <rect x="21" y="56" width="8" height="5" rx="2"/>
  </g>
</svg>`;

export function mountPlace(root, place) {
  root.classList.add('pl-root');
  const stage = el('div', { class: 'pl-stage' });
  const mapWrap = el('div', { class: 'pl-map' });
  const canvas = new MapCanvas(mapWrap, place.map.width, place.map.height);
  if (place.map.image) {
    // A rendered map of the real city; pins are placed from lat/lon with
    // the same Mercator projection that drew it.
    const img = svg('image', { href: `${place.assets}/${place.map.image}`, x: 0, y: 0, width: place.map.width, height: place.map.height, preserveAspectRatio: 'none' });
    canvas.layers.land.append(img);
    const [s, w, n, e] = place.map.bbox;
    const mercY = (lat) => Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI / 180) / 2));
    const y0 = mercY(n), y1 = mercY(s);
    const margin = 34;
    for (const pin of place.pins) {
      if (pin.lat === undefined) continue;
      let x = (pin.lon - w) / (e - w) * place.map.width;
      let y = (mercY(pin.lat) - y0) / (y1 - y0) * place.map.height;
      if (pin.offmap || x < 0 || x > place.map.width || y < 0 || y > place.map.height) {
        // Off the edge: pin it to the border in the right direction.
        x = Math.min(place.map.width - margin, Math.max(margin, x));
        y = Math.min(place.map.height - 12, Math.max(margin + 12, y));
        pin.offmap = pin.offmap || { arrow: '→', distance: '' };
      }
      pin.x = x;
      pin.y = y;
    }
  } else {
    place.map.draw(canvas);
  }
  const pinNodes = new Map();
  for (const pin of place.pins) {
    pin.baseX = pin.x;
    pin.baseY = pin.y;
    const node = makePin(pin);
    canvas.layers.pin.append(node);
    pinNodes.set(pin.id, node);
    // A tap on the pin opens it too, for anyone who does not find the man.
    node.addEventListener('click', () => open(pin));
  }

  // On a narrow screen show the middle of the map, where the pins are,
  // rather than the whole city at postage-stamp size.
  const crop = place.map.crop || [0.14, 0.64];
  function fitMap() {
    const narrow = mapWrap.clientWidth < 600;
    root.classList.toggle('pl-narrow', narrow);
    const W = place.map.width, H = place.map.height;
    const x0 = narrow ? W * crop[0] : 0, w = narrow ? W * crop[1] : W;
    canvas.svg.setAttribute('viewBox', `${x0} 0 ${w} ${H}`);
    mapWrap.style.aspectRatio = `${w} / ${H}`;
    for (const pin of place.pins) {
      const node = pinNodes.get(pin.id);
      if (!node || pin.baseX === undefined) continue;
      let x = pin.baseX;
      if (narrow && (x < x0 + 30 || x > x0 + w - 30)) x = Math.min(x0 + w - 30, Math.max(x0 + 30, x));
      node.setAttribute('transform', `translate(${x} ${pin.baseY})${narrow ? ' scale(1.5)' : ''}`);
    }
    requestAnimationFrame(() => { for (const n of pinNodes.values()) n.sizeLabel?.(); });
  }
  const hint = el('div', { class: 'pl-hint', text: place.hint || 'Drag him onto a pin.' });
  const pegman = el('div', { class: 'pl-pegman', html: PEGMAN_SVG, title: 'Drag me onto a pin' });
  const dock = el('div', { class: 'pl-dock' }, [pegman, hint]);
  stage.append(mapWrap, dock);
  root.append(stage);

  const viewer = new SceneViewer(place, () => leaveScene());
  root.append(viewer.root);
  fitMap();
  addEventListener('resize', fitMap);

  // Drag the man. Pointer events cover mouse and touch; capture keeps the
  // drag alive when the finger leaves the element.
  let drag = null;
  pegman.addEventListener('pointerdown', (e) => {
    e.preventDefault();
    pegman.setPointerCapture(e.pointerId);
    const r = pegman.getBoundingClientRect();
    drag = { dx: e.clientX - r.left, dy: e.clientY - r.top, over: null };
    pegman.classList.add('pl-dragging');
    root.classList.add('pl-armed');
    pegman.style.position = 'fixed';
    move(e);
  });
  pegman.addEventListener('pointermove', (e) => { if (drag) move(e); });
  pegman.addEventListener('pointerup', (e) => finish(e));
  pegman.addEventListener('pointercancel', () => reset());

  function move(e) {
    pegman.style.left = `${e.clientX - drag.dx}px`;
    pegman.style.top = `${e.clientY - drag.dy}px`;
    const hit = pinAt(e.clientX, e.clientY - 10);
    if (hit !== drag.over) {
      if (drag.over) pinNodes.get(drag.over.id).classList.remove('pl-hover');
      if (hit) pinNodes.get(hit.id).classList.add('pl-hover');
      drag.over = hit;
    }
  }
  function pinAt(cx, cy) {
    let best = null, bestD = 40;
    for (const pin of place.pins) {
      const b = pinNodes.get(pin.id).querySelector('.pl-pin-body').getBoundingClientRect();
      const px = b.left + b.width / 2, py = b.top + b.height / 2;
      const d = Math.hypot(cx - px, cy - py);
      if (d < bestD) { bestD = d; best = pin; }
    }
    return best;
  }
  function finish(e) {
    if (!drag) return;
    const hit = drag.over;
    reset();
    if (hit) open(hit);
  }
  function reset() {
    if (drag && drag.over) pinNodes.get(drag.over.id).classList.remove('pl-hover');
    drag = null;
    pegman.classList.remove('pl-dragging');
    root.classList.remove('pl-armed');
    pegman.style.position = '';
    pegman.style.left = '';
    pegman.style.top = '';
  }

  // Zoom the map into the pin, then bring the scene up over it.
  function open(pin) {
    const node = pinNodes.get(pin.id);
    node.classList.add('pl-active');
    const b = node.querySelector('.pl-pin-body').getBoundingClientRect();
    const m = mapWrap.getBoundingClientRect();
    const ox = ((b.left + b.width / 2 - m.left) / m.width) * 100;
    const oy = ((b.top + b.height - m.top) / m.height) * 100;
    mapWrap.style.transformOrigin = `${ox}% ${oy}%`;
    mapWrap.classList.add('pl-zoomed');
    viewer.show(pin);
    history.replaceState(null, '', `#${pin.id}`);
  }
  function leaveScene() {
    mapWrap.classList.remove('pl-zoomed');
    for (const n of pinNodes.values()) n.classList.remove('pl-active');
    history.replaceState(null, '', location.pathname + location.search);
  }

  // A link straight to a pin opens it.
  const openFromHash = () => {
    const linked = place.pins.find((p) => p.id === location.hash.slice(1));
    if (linked && viewer.root.hidden) setTimeout(() => open(linked), 300);
  };
  addEventListener('hashchange', openFromHash);
  openFromHash();
  return { open };
}

// ---------------------------------------------------------------------------
// The scene viewer
// ---------------------------------------------------------------------------

class SceneViewer {
  constructor(place, onClose) {
    this.place = place;
    this.onClose = onClose;
    this.root = el('div', { class: 'pl-viewer', hidden: '' });
    this.gl = el('div', { class: 'pl-gl' });
    this.top = el('div', { class: 'pl-top' });
    this.title = el('div', { class: 'pl-title' });
    this.back = el('button', { class: 'pl-back', type: 'button', text: '← Back to the map' });
    this.top.append(this.back, this.title);
    this.panel = el('aside', { class: 'pl-panel' });
    this.notesToggle = el('button', { class: 'pl-notes-toggle', type: 'button', text: 'Hide notes', 'aria-expanded': 'true' });
    this.top.append(this.notesToggle);
    this.loading = el('div', { class: 'pl-loading', text: 'Building the scene…' });
    this.root.append(this.gl, this.top, this.panel, this.loading);
    this.back.addEventListener('click', () => this.hide());
    this.notesToggle.addEventListener('click', () => this.toggleNotes());
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !this.root.hidden) this.hide(); });
    this.renderer = null;
  }

  ensureRenderer() {
    if (this.renderer) return;
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.0;
    // A neutral room environment gives cloth, skin and wood something to
    // reflect, which is most of what separates a render from a diagram.
    const pmrem = new THREE.PMREMGenerator(this.renderer);
    this.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    pmrem.dispose();
    this.labels = new CSS2DRenderer();
    this.labels.domElement.className = 'pl-labels';
    this.gl.append(this.renderer.domElement, this.labels.domElement);
    this.camera = new THREE.PerspectiveCamera(42, 1, 0.1, 200);
    this.controls = new OrbitControls(this.camera, this.labels.domElement);
    this.controls.enableDamping = true;
    this.controls.maxPolarAngle = Math.PI * 0.47;
    this.controls.minPolarAngle = Math.PI * 0.12;
    this.controls.minDistance = 1.5;
    this.controls.maxDistance = 18;
    this.controls.zoomToCursor = true;
    this.controls.enablePan = true;
    this.controls.screenSpacePanning = false;
    this.controls.autoRotate = true;
    this.controls.autoRotateSpeed = 0.35;
    this.labels.domElement.addEventListener('pointerdown', () => { this.controls.autoRotate = false; }, { once: true });
    addEventListener('resize', () => this.resize());
  }

  resize() {
    if (!this.renderer || this.root.hidden) return;
    const w = this.gl.clientWidth, h = this.gl.clientHeight;
    this.renderer.setSize(w, h);
    this.labels.setSize(w, h);
    this.camera.aspect = w / h;
    // With the notes open on a wide screen, render the frame shifted left
    // by half the panel so the set sits in the clear.
    const notesOpen = !this.root.classList.contains('pl-notes-hidden');
    if (w > 720 && notesOpen) this.camera.setViewOffset(w, h, 160, 0, w, h);
    else this.camera.clearViewOffset();
    this.camera.updateProjectionMatrix();
  }

  toggleNotes(show) {
    const hidden = show === undefined ? !this.root.classList.contains('pl-notes-hidden') : !show;
    this.root.classList.toggle('pl-notes-hidden', hidden);
    this.notesToggle.textContent = hidden ? 'Show notes' : 'Hide notes';
    this.notesToggle.setAttribute('aria-expanded', String(!hidden));
    this.resize();
  }

  async show(pin) {
    this.ensureRenderer();
    this.root.hidden = false;
    this.loading.hidden = false;
    this.title.innerHTML = '';
    this.title.append(
      el('div', { class: 'pl-title-name', text: pin.scene.title || pin.label }),
      el('div', { class: 'pl-title-sub', text: pin.scene.subtitle || '' }),
    );
    document.body.classList.add('pl-open');
    requestAnimationFrame(() => this.root.classList.add('pl-visible'));
    this.resize();
    if (this.scene) this.disposeScene();
    this.scene = new THREE.Scene();
    this.scene.environment = this.environment;
    this.scene.environmentIntensity = 0.55;
    this.figureObjects = new Map();
    await buildScene(this.scene, pin.scene, this.place, this.figureObjects);
    this.placeCamera(pin.scene);
    this.buildPanel(pin);
    this.loading.hidden = true;
    this.controls.autoRotate = true;
    this.animate();
  }

  placeCamera(scene) {
    const cam = scene.camera || { pos: [7, 4.5, 8], look: [0, 1, 0] };
    this.camera.position.set(...cam.pos);
    this.controls.target.set(...cam.look);
    this.controls.update();
  }

  buildPanel(pin) {
    this.panel.innerHTML = '';
    const heading = el('div', { class: 'pl-panel-head', text: pin.scene.blurb || '' });
    this.panel.append(heading);
    const list = el('ol', { class: 'pl-notes' });
    for (const fig of pin.scene.figures) {
      const item = el('li', { class: 'pl-note' }, [
        el('span', { class: 'pl-note-name', text: fig.name }),
        el('span', { class: 'pl-note-text', text: fig.note }),
      ]);
      item.addEventListener('mouseenter', () => this.highlight(fig.id, true));
      item.addEventListener('mouseleave', () => this.highlight(fig.id, false));
      item.addEventListener('click', () => this.focusOn(fig.id));
      list.append(item);
    }
    this.panel.append(list);
    if (pin.scene.sources) {
      this.panel.append(el('div', { class: 'pl-sources', text: pin.scene.sources }));
    }
  }

  highlight(id, on) {
    const obj = this.figureObjects.get(id);
    if (!obj) return;
    obj.label.element.classList.toggle('pl-chip-hot', on);
  }

  focusOn(id) {
    const obj = this.figureObjects.get(id);
    if (!obj) return;
    this.controls.autoRotate = false;
    const target = new THREE.Vector3();
    obj.anchor.getWorldPosition(target);
    const from = this.controls.target.clone();
    const camFrom = this.camera.position.clone();
    const dir = camFrom.clone().sub(from).normalize();
    const camTo = target.clone().add(dir.multiplyScalar(4.5)).add(new THREE.Vector3(0, 0.6, 0));
    const t0 = performance.now();
    const step = () => {
      const k = Math.min(1, (performance.now() - t0) / 700);
      const e = 1 - Math.pow(1 - k, 3);
      this.controls.target.lerpVectors(from, target, e);
      this.camera.position.lerpVectors(camFrom, camTo, e);
      if (k < 1) requestAnimationFrame(step);
    };
    step();
  }

  animate() {
    if (this.root.hidden) return;
    this.raf = requestAnimationFrame(() => this.animate());
    this.controls.update();
    if (this.controls.target.y < 0.3) { this.controls.target.y = 0.3; }
    if (this.camera.position.y < 0.4) { this.camera.position.y = 0.4; }
    for (const obj of this.figureObjects.values()) obj.tick?.(performance.now() / 1000);
    this.renderer.render(this.scene, this.camera);
    this.labels.render(this.scene, this.camera);
  }

  hide() {
    this.root.classList.remove('pl-visible');
    document.body.classList.remove('pl-open');
    setTimeout(() => {
      this.root.hidden = true;
      cancelAnimationFrame(this.raf);
    }, 350);
    this.onClose();
  }

  disposeScene() {
    this.scene.traverse((o) => {
      if (o.geometry) o.geometry.dispose();
      if (o.material) (Array.isArray(o.material) ? o.material : [o.material]).forEach((m) => m.dispose());
    });
    this.labels.domElement.querySelectorAll('.pl-chip').forEach((n) => n.remove());
  }
}

// ---------------------------------------------------------------------------
// Building a scene: a Blender export when there is one, a procedural set
// from the data otherwise. Annotations attach the same way in both cases.
// ---------------------------------------------------------------------------

async function buildScene(scene, spec, place, figureObjects) {
  const room = spec.room || {};
  scene.background = new THREE.Color(room.sky || '#e9dcc3');
  scene.fog = new THREE.Fog(scene.background, 18, 60);

  scene.add(new THREE.HemisphereLight(0xfff2dc, 0x6b5a45, 0.5));
  const sun = new THREE.DirectionalLight(0xffe7c4, 1.8);
  sun.position.set(...(room.light || [6, 9, 4]));
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  sun.shadow.camera.left = -14; sun.shadow.camera.right = 14;
  sun.shadow.camera.top = 14; sun.shadow.camera.bottom = -14;
  sun.shadow.bias = -0.0005;
  scene.add(sun);

  let gltf = null;
  let mixer = null;
  if (spec.glb) {
    try {
      gltf = await new GLTFLoader().loadAsync(`${place.assets}/${spec.glb}`);
      gltf.scene.traverse((o) => {
        if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; }
        // The Blender file marks where lamps hang with empties named light_*.
        if (o.name.startsWith('light_')) {
          const l = new THREE.PointLight('#ffd9a0', o.name.includes('chandelier') ? 18 : 6, o.name.includes('chandelier') ? 14 : 6, 2);
          o.add(l);
        }
      });
      scene.add(gltf.scene);
      // One clip per figure, named anim_<id>, bound to that figure's own rig
      // (rig_<id>): every rig shares the kit's bone names, so a clip has to
      // be resolved inside its own subtree or they all drive the first one.
      if (gltf.animations.length) {
        mixer = new THREE.AnimationMixer(gltf.scene);
        for (const clip of gltf.animations) {
          const rig = gltf.scene.getObjectByName(clip.name.replace(/^anim_/, 'rig_'));
          const action = mixer.clipAction(clip, rig || gltf.scene);
          action.time = Math.random() * clip.duration;
          action.play();
        }
      }
    } catch (err) {
      console.warn(`No usable ${spec.glb}; building the procedural set instead.`, err);
    }
  }
  if (!gltf) buildRoom(scene, room);
  if (!gltf) for (const prop of spec.props || []) scene.add(buildProp(prop));
  if (mixer) {
    let last = null;
    figureObjects.set('__mixer', { tick: (t) => { if (last !== null) mixer.update(t - last); last = t; } });
  }

  for (const fig of spec.figures) {
    // With a Blender scene the figure lives in the file; the annotation hangs
    // off the object named `figure_<id>` (an Empty above the head). Without
    // one, build a stick figure from the pose in the data.
    let anchor = gltf ? gltf.scene.getObjectByName(`figure_${fig.id}`) : null;
    let tick = null;
    if (!anchor) {
      const built = buildFigure(fig);
      scene.add(built.group);
      anchor = built.anchor;
      tick = built.tick;
    }
    const chip = el('div', { class: 'pl-chip' }, [
      el('span', { class: 'pl-chip-name', text: fig.name }),
    ]);
    chip.addEventListener('pointerdown', (e) => e.stopPropagation());
    const label = new CSS2DObject(chip);
    label.position.set(0, 0, 0);
    anchor.add(label);
    figureObjects.set(fig.id, { anchor, label, tick });
  }
}

const mats = {};
function mat(color, opts = {}) {
  const key = color + JSON.stringify(opts);
  if (!mats[key]) mats[key] = new THREE.MeshStandardMaterial({ color, roughness: 0.85, metalness: 0.02, ...opts });
  return mats[key];
}
function box(w, h, d, color, x = 0, y = 0, z = 0) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat(color));
  m.position.set(x, y, z);
  m.castShadow = true; m.receiveShadow = true;
  return m;
}
function cyl(rt, rb, h, color, x = 0, y = 0, z = 0, seg = 18) {
  const m = new THREE.Mesh(new THREE.CylinderGeometry(rt, rb, h, seg), mat(color));
  m.position.set(x, y, z);
  m.castShadow = true; m.receiveShadow = true;
  return m;
}
function sphere(r, color, x = 0, y = 0, z = 0) {
  const m = new THREE.Mesh(new THREE.SphereGeometry(r, 20, 14), mat(color));
  m.position.set(x, y, z);
  m.castShadow = true;
  return m;
}

function checkerTexture(a, b) {
  const c = document.createElement('canvas');
  c.width = c.height = 64;
  const g = c.getContext('2d');
  g.fillStyle = a; g.fillRect(0, 0, 64, 64);
  g.fillStyle = b; g.fillRect(0, 0, 32, 32); g.fillRect(32, 32, 32, 32);
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

function buildRoom(scene, room) {
  const w = room.w || 12, d = room.d || 10, h = room.h || 4.2;
  let floorMat;
  if (room.floor === 'checker') {
    const t = checkerTexture('#e8dcc4', '#3a2e24');
    t.repeat.set(w / 1.2, d / 1.2);
    floorMat = new THREE.MeshStandardMaterial({ map: t, roughness: 0.6 });
  } else if (room.floor === 'grass') {
    floorMat = mat('#7a9a5a');
  } else if (room.floor === 'concrete') {
    floorMat = mat('#8f8a80');
  } else {
    floorMat = mat(room.floor || '#8a6a48');
  }
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(room.outdoor ? 80 : w, room.outdoor ? 80 : d), floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.receiveShadow = true;
  scene.add(floor);
  if (room.outdoor) return;
  const wallColor = room.wall || '#d9c9a6';
  const back = box(w, h, 0.2, wallColor, 0, h / 2, -d / 2);
  const left = box(0.2, h, d, wallColor, -w / 2, h / 2, 0);
  const right = box(0.2, h, d, wallColor, w / 2, h / 2, 0);
  back.receiveShadow = left.receiveShadow = right.receiveShadow = true;
  scene.add(back, left, right);
  // Panelling line and a skirting board give a bare wall a period.
  const trim = room.trim || '#8a6a48';
  scene.add(box(w, 0.18, 0.26, trim, 0, 0.09, -d / 2));
  scene.add(box(0.26, 0.18, d, trim, -w / 2, 0.09, 0));
  scene.add(box(0.26, 0.18, d, trim, w / 2, 0.09, 0));
  scene.add(box(w, 0.06, 0.26, trim, 0, 1.1, -d / 2));
  scene.add(box(0.26, 0.06, d, trim, -w / 2, 1.1, 0));
  scene.add(box(0.26, 0.06, d, trim, w / 2, 1.1, 0));
  for (const win of room.windows || []) {
    // A window is a bright plane set into the wall it names.
    const g = new THREE.Group();
    const pane = new THREE.Mesh(new THREE.PlaneGeometry(1.4, 2.2),
      new THREE.MeshStandardMaterial({ color: '#fff4dc', emissive: '#ffe9c0', emissiveIntensity: 0.9 }));
    const frame = box(1.7, 2.5, 0.12, '#f4efe4');
    g.add(frame, pane);
    pane.position.z = 0.08;
    g.add(box(0.06, 2.2, 0.16, '#f4efe4', 0, 0, 0.06));
    g.add(box(1.4, 0.06, 0.16, '#f4efe4', 0, 0.3, 0.06));
    if (win.wall === 'back') g.position.set(win.at, 2.1, -d / 2 + 0.1);
    if (win.wall === 'left') { g.position.set(-w / 2 + 0.1, 2.1, win.at); g.rotation.y = Math.PI / 2; }
    if (win.wall === 'right') { g.position.set(w / 2 - 0.1, 2.1, win.at); g.rotation.y = -Math.PI / 2; }
    scene.add(g);
  }
}

// Every prop is a small pile of primitives. They are meant to read as the
// thing from across the room, not up close: that is the Blender file's job.
const PROPS = {
  table(p) {
    const g = new THREE.Group();
    const r = p.r || 0.55;
    g.add(cyl(r, r, 0.05, p.color || '#f2ede4', 0, 0.75, 0, 28));
    g.add(cyl(0.05, 0.05, 0.72, '#2b2b2b', 0, 0.37, 0));
    g.add(cyl(0.28, 0.28, 0.04, '#2b2b2b', 0, 0.02, 0, 24));
    return g;
  },
  chair(p) {
    const g = new THREE.Group();
    const c = p.color || '#5a3a22';
    g.add(box(0.45, 0.05, 0.45, c, 0, 0.45, 0));
    g.add(box(0.45, 0.5, 0.05, c, 0, 0.72, -0.2));
    for (const [x, z] of [[-0.19, -0.19], [0.19, -0.19], [-0.19, 0.19], [0.19, 0.19]]) g.add(box(0.04, 0.45, 0.04, c, x, 0.22, z));
    return g;
  },
  couch(p) {
    const g = new THREE.Group();
    const c = p.color || '#8a2f2f';
    g.add(box(2.0, 0.35, 0.9, c, 0, 0.35, 0));
    g.add(box(2.0, 0.55, 0.25, c, 0, 0.75, -0.33));
    g.add(box(0.28, 0.5, 0.9, c, -0.86, 0.6, 0));
    g.add(box(0.6, 0.18, 0.5, '#c8a878', 0.55, 0.62, 0.1));
    g.add(box(2.0, 0.05, 0.9, '#b04a3a', 0, 0.55, 0));
    return g;
  },
  armchair(p) {
    const g = new THREE.Group();
    const c = p.color || '#3f5a3a';
    g.add(box(0.8, 0.4, 0.8, c, 0, 0.3, 0));
    g.add(box(0.8, 0.7, 0.2, c, 0, 0.75, -0.3));
    g.add(box(0.18, 0.35, 0.8, c, -0.31, 0.62, 0));
    g.add(box(0.18, 0.35, 0.8, c, 0.31, 0.62, 0));
    return g;
  },
  desk(p) {
    const g = new THREE.Group();
    const c = p.color || '#4a2e1c';
    g.add(box(1.7, 0.06, 0.8, c, 0, 0.78, 0));
    g.add(box(0.5, 0.75, 0.75, c, -0.55, 0.375, 0));
    g.add(box(0.5, 0.75, 0.75, c, 0.55, 0.375, 0));
    g.add(box(0.4, 0.02, 0.3, '#f6f0e2', 0.1, 0.82, 0.1));
    return g;
  },
  standingdesk(p) {
    const g = new THREE.Group();
    const c = p.color || '#4a2e1c';
    g.add(box(1.2, 0.05, 0.6, c, 0, 1.12, 0));
    g.add(box(0.9, 1.1, 0.4, c, 0, 0.55, 0));
    g.add(box(0.5, 0.02, 0.35, '#f6f0e2', 0, 1.15, 0.08));
    return g;
  },
  bookshelf(p) {
    const g = new THREE.Group();
    const c = p.color || '#3a2416';
    const w = p.w || 1.6;
    g.add(box(w, 2.6, 0.35, c, 0, 1.3, 0));
    const spines = ['#7a2e2e', '#2e4a7a', '#4a6a2e', '#b08a3a', '#3a3a3a', '#8a5a2e'];
    for (let s = 0; s < 4; s++) {
      let x = -w / 2 + 0.08;
      while (x < w / 2 - 0.1) {
        const bw = 0.06 + Math.random() * 0.06;
        g.add(box(bw, 0.28 + Math.random() * 0.14, 0.24, spines[Math.floor(Math.random() * spines.length)], x + bw / 2, 0.42 + s * 0.6, 0.07));
        x += bw + 0.01;
      }
    }
    return g;
  },
  cabinet(p) {
    const g = new THREE.Group();
    g.add(box(1.4, 1.9, 0.5, p.color || '#3a2416', 0, 0.95, 0));
    for (let i = 0; i < 6; i++) g.add(sphere(0.08, ['#c9b78f', '#8a7a5a', '#5a4a3a'][i % 3], -0.5 + i * 0.2, 1.3 + (i % 2) * 0.35, 0.28));
    return g;
  },
  easel(p) {
    const g = new THREE.Group();
    const c = '#8a6a48';
    g.add(box(0.05, 1.8, 0.05, c, -0.3, 0.9, 0.1));
    g.add(box(0.05, 1.8, 0.05, c, 0.3, 0.9, 0.1));
    g.add(box(0.05, 1.7, 0.05, c, 0, 0.85, -0.25));
    g.add(box(0.7, 0.5, 0.03, '#f4efe0', 0, 1.15, 0.13));
    g.add(box(0.5, 0.3, 0.035, p.paint || '#9ab8d0', 0, 1.15, 0.14));
    return g;
  },
  bunk(p) {
    const g = new THREE.Group();
    const c = '#6a6a6a';
    g.add(box(0.9, 0.12, 2.0, c, 0, 0.45, 0));
    g.add(box(0.9, 0.12, 2.0, '#d8d0c0', 0, 0.55, 0));
    g.add(box(0.5, 0.08, 0.3, '#f0eae0', 0, 0.63, -0.75));
    for (const [x, z] of [[-0.42, -0.97], [0.42, -0.97], [-0.42, 0.97], [0.42, 0.97]]) g.add(box(0.05, 0.9, 0.05, c, x, 0.45, z));
    g.add(box(0.9, 0.05, 0.05, c, 0, 0.9, -0.97));
    return g;
  },
  podium(p) {
    const g = new THREE.Group();
    g.add(box(1.2, 0.3, 1.2, '#4a2e1c', 0, 0.15, 0));
    g.add(box(0.5, 1.0, 0.04, '#2b2b2b', 0, 0.8, 0.5));
    g.add(box(0.04, 1.0, 0.04, '#2b2b2b', 0, 0.5, 0.5));
    return g;
  },
  stand(p) {
    // A music stand with a chair in front of it: an orchestra desk.
    const g = new THREE.Group();
    g.add(box(0.03, 1.0, 0.03, '#2b2b2b', 0, 0.5, 0));
    g.add(box(0.4, 0.3, 0.02, '#2b2b2b', 0, 1.05, 0));
    g.add(box(0.3, 0.2, 0.01, '#f6f0e2', 0, 1.06, 0.01));
    return g;
  },
  seats(p) {
    // A block of theatre seats: rows × cols of small red chairs.
    const g = new THREE.Group();
    const rows = p.rows || 4, cols = p.cols || 8;
    for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
      const x = (c - (cols - 1) / 2) * 0.55, z = r * 0.8;
      g.add(box(0.48, 0.1, 0.45, '#8a2f2f', x, 0.42 + r * 0.12, z));
      g.add(box(0.48, 0.5, 0.08, '#8a2f2f', x, 0.7 + r * 0.12, z + 0.2));
      g.add(box(0.48, 0.35 + r * 0.12, 0.45, '#3a2416', x, 0.18 + r * 0.06, z));
    }
    return g;
  },
  piano(p) {
    const g = new THREE.Group();
    g.add(box(1.5, 0.3, 2.2, '#111', 0, 0.95, 0));
    g.add(box(1.4, 0.05, 0.4, '#f4f0e6', 0, 0.95, 1.2));
    g.add(box(1.5, 0.05, 2.2, '#111', 0, 1.15, -0.05));
    for (const [x, z] of [[-0.6, 0.9], [0.6, 0.9], [0, -0.9]]) g.add(box(0.08, 0.8, 0.08, '#111', x, 0.4, z));
    return g;
  },
  column(p) {
    const g = new THREE.Group();
    g.add(cyl(0.35, 0.35, 0.3, '#e6dfcf', 0, 0.15, 0, 24));
    g.add(cyl(0.28, 0.32, 4.2, '#e6dfcf', 0, 2.25, 0, 24));
    g.add(cyl(0.42, 0.3, 0.35, '#e6dfcf', 0, 4.5, 0, 24));
    return g;
  },
  rug(p) {
    const g = new THREE.Group();
    const r = new THREE.Mesh(new THREE.PlaneGeometry(p.w || 3, p.d || 2), mat(p.color || '#7a3030'));
    r.rotation.x = -Math.PI / 2; r.position.y = 0.011; r.receiveShadow = true;
    g.add(r);
    return g;
  },
  car(p) {
    const g = new THREE.Group();
    const c = p.color || '#2f4a2f';
    g.add(box(3.2, 0.5, 1.4, c, 0, 0.6, 0));
    g.add(box(1.5, 0.6, 1.3, c, -0.4, 1.15, 0));
    g.add(box(0.05, 0.6, 1.3, '#cfe8f0', 0.4, 1.15, 0));
    for (const [x, z] of [[-1.1, -0.72], [1.1, -0.72], [-1.1, 0.72], [1.1, 0.72]]) {
      const w = cyl(0.42, 0.42, 0.18, '#2b2b2b', x, 0.42, z, 20);
      w.rotation.x = Math.PI / 2; g.add(w);
    }
    g.add(cyl(0.16, 0.16, 0.06, '#f6efe0', 1.6, 0.8, 0.5, 14));
    return g;
  },
  workbench(p) {
    const g = new THREE.Group();
    g.add(box(2.2, 0.1, 0.8, '#8a6a48', 0, 0.85, 0));
    g.add(box(0.1, 0.85, 0.7, '#5a4a3a', -1.0, 0.42, 0));
    g.add(box(0.1, 0.85, 0.7, '#5a4a3a', 1.0, 0.42, 0));
    g.add(box(0.3, 0.2, 0.2, '#555', 0.5, 1.0, 0));
    g.add(cyl(0.05, 0.05, 0.5, '#888', -0.4, 0.93, 0.1));
    return g;
  },
  tree(p) {
    const g = new THREE.Group();
    g.add(cyl(0.12, 0.18, 1.6, '#5a4030', 0, 0.8, 0));
    g.add(sphere(1.1, p.color || '#5f8a48', 0, 2.3, 0));
    g.add(sphere(0.8, p.color || '#5f8a48', 0.5, 2.9, 0.3));
    return g;
  },
  bench(p) {
    const g = new THREE.Group();
    g.add(box(1.6, 0.06, 0.45, '#4a6a3a', 0, 0.45, 0));
    g.add(box(1.6, 0.4, 0.06, '#4a6a3a', 0, 0.7, -0.2));
    g.add(box(0.06, 0.45, 0.45, '#333', -0.7, 0.22, 0));
    g.add(box(0.06, 0.45, 0.45, '#333', 0.7, 0.22, 0));
    return g;
  },
  chessboard(p) {
    const g = new THREE.Group();
    const t = checkerTexture('#f0e6d0', '#4a3a2a');
    t.repeat.set(4, 4);
    const b = new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.02, 0.42), new THREE.MeshStandardMaterial({ map: t }));
    b.position.y = 0.79; b.castShadow = true;
    g.add(b);
    for (let i = 0; i < 10; i++) g.add(cyl(0.015, 0.02, 0.06, i % 2 ? '#f6f0e2' : '#222', -0.16 + (i % 5) * 0.08, 0.83, (i < 5 ? -0.15 : 0.13) + (Math.random() - 0.5) * 0.08, 8));
    return g;
  },
  lamp(p) {
    const g = new THREE.Group();
    g.add(cyl(0.02, 0.02, 1.6, '#333', 0, 0.8, 0));
    g.add(cyl(0.25, 0.12, 0.3, '#f6e6b0', 0, 1.65, 0, 16));
    const l = new THREE.PointLight('#ffd9a0', 6, 6, 2);
    l.position.y = 1.55;
    g.add(l);
    return g;
  },
  chandelier(p) {
    const g = new THREE.Group();
    g.add(cyl(0.01, 0.01, 1.2, '#333', 0, 3.7, 0, 6));
    g.add(cyl(0.6, 0.5, 0.15, '#d8b860', 0, 3.1, 0, 16));
    for (let i = 0; i < 6; i++) {
      const a = (i / 6) * Math.PI * 2;
      g.add(cyl(0.03, 0.03, 0.2, '#fff5d0', Math.cos(a) * 0.5, 3.28, Math.sin(a) * 0.5, 8));
    }
    const l = new THREE.PointLight('#ffe0b0', 14, 12, 2);
    l.position.y = 3.0;
    g.add(l);
    return g;
  },
};

function buildProp(p) {
  const maker = PROPS[p.type];
  if (!maker) { console.warn('unknown prop', p.type); return new THREE.Group(); }
  const g = maker(p);
  g.position.set(p.at[0], p.y || 0, p.at[1]);
  g.rotation.y = THREE.MathUtils.degToRad(p.rot || 0);
  if (p.scale) g.scale.setScalar(p.scale);
  return g;
}

// A person: enough shape to read stance, coat and hat from across the room.
function buildFigure(fig) {
  const g = new THREE.Group();
  const coat = fig.coat || '#3a3a3a';
  const skin = fig.skin || '#e0b896';
  const hair = fig.hair && fig.hair !== 'none' ? fig.hair : '#2a2016';
  const sit = fig.pose === 'sit';
  const lean = fig.pose === 'lean';
  const legH = 0.85;
  const torsoY = sit ? 0.45 + 0.5 : legH + 0.42;
  if (sit) {
    // Thighs forward, shins down.
    g.add(box(0.36, 0.16, 0.45, fig.trousers || coat, 0, 0.5, 0.2));
    g.add(box(0.12, 0.45, 0.12, fig.trousers || coat, -0.11, 0.22, 0.42));
    g.add(box(0.12, 0.45, 0.12, fig.trousers || coat, 0.11, 0.22, 0.42));
  } else {
    g.add(box(0.14, legH, 0.16, fig.trousers || coat, -0.11, legH / 2, 0));
    g.add(box(0.14, legH, 0.16, fig.trousers || coat, 0.11, legH / 2, 0));
  }
  const torso = box(0.44, 0.7, 0.28, coat, 0, torsoY, 0);
  g.add(torso);
  if (fig.vest) g.add(box(0.2, 0.55, 0.06, fig.vest, 0, torsoY - 0.02, 0.15));
  // Arms: down, or forward when the figure is doing something with them.
  const armY = torsoY + 0.15;
  const forward = fig.hands === 'forward' || sit;
  const la = box(0.11, 0.6, 0.11, coat, -0.28, forward ? armY - 0.1 : armY - 0.25, forward ? 0.2 : 0);
  const ra = box(0.11, 0.6, 0.11, coat, 0.28, forward ? armY - 0.1 : armY - 0.25, forward ? 0.2 : 0);
  if (forward) { la.rotation.x = -1.2; ra.rotation.x = -1.2; }
  if (fig.hands === 'raised') { ra.rotation.x = Math.PI * 0.9; ra.position.y = armY + 0.2; }
  g.add(la, ra);
  const headY = torsoY + 0.35 + 0.22;
  g.add(cyl(0.06, 0.06, 0.1, skin, 0, torsoY + 0.38, 0, 10));
  g.add(sphere(0.2, skin, 0, headY, 0));
  if (fig.hair !== 'none') {
    const cap = sphere(0.205, hair, 0, headY + 0.05, -0.02);
    cap.scale.set(1, 0.7, 1);
    g.add(cap);
    if (fig.bald) cap.scale.set(1.02, 0.45, 1.02), cap.position.y = headY + 0.01;
  }
  if (fig.beard) {
    const b = sphere(0.14, fig.beard === true ? hair : fig.beard, 0, headY - 0.14, 0.1);
    b.scale.set(1.1, fig.beardLong ? 1.6 : 0.9, 0.7);
    g.add(b);
  }
  if (fig.moustache) g.add(box(fig.moustache === 'small' ? 0.08 : 0.18, 0.04, 0.05, hair, 0, headY - 0.06, 0.19));
  if (fig.glasses) {
    for (const x of [-0.07, 0.07]) {
      const lens = cyl(0.05, 0.05, 0.01, '#222', x, headY + 0.02, 0.2, 12);
      lens.rotation.x = Math.PI / 2;
      g.add(lens);
    }
  }
  if (fig.hat === 'top') { g.add(cyl(0.16, 0.16, 0.3, '#151515', 0, headY + 0.33, 0, 20)); g.add(cyl(0.26, 0.26, 0.02, '#151515', 0, headY + 0.18, 0, 20)); }
  if (fig.hat === 'bowler') { g.add(sphere(0.18, '#151515', 0, headY + 0.12, 0)); g.add(cyl(0.27, 0.27, 0.02, '#151515', 0, headY + 0.12, 0, 20)); }
  if (fig.hat === 'cap') { g.add(cyl(0.2, 0.21, 0.08, fig.capColor || '#444', 0, headY + 0.16, 0, 20)); g.add(box(0.28, 0.02, 0.14, fig.capColor || '#444', 0, headY + 0.13, 0.2)); }
  if (fig.hat === 'military') { g.add(cyl(0.2, 0.22, 0.14, fig.capColor || '#2e4a2e', 0, headY + 0.2, 0, 20)); g.add(box(0.3, 0.02, 0.14, '#111', 0, headY + 0.14, 0.2)); }
  if (fig.shawl) g.add(box(0.5, 0.2, 0.34, fig.shawl, 0, torsoY + 0.3, 0));
  if (fig.held === 'baton') { const b = cyl(0.008, 0.008, 0.45, '#f6f0e2', 0.32, armY + 0.35, 0.15, 6); b.rotation.x = -0.6; g.add(b); }
  if (fig.held === 'brush') { g.add(cyl(0.01, 0.01, 0.25, '#8a6a48', 0.3, armY, 0.42, 6)); }
  if (fig.held === 'paper') { g.add(box(0.22, 0.28, 0.01, '#f6f0e2', 0, armY, 0.4)); }

  g.position.set(fig.at[0], 0, fig.at[1]);
  g.rotation.y = THREE.MathUtils.degToRad(fig.face || 0);
  const anchor = new THREE.Object3D();
  anchor.position.set(0, headY + (fig.hat ? 0.62 : 0.4), 0);
  g.add(anchor);
  // A slow breathing bob keeps the set from looking like a diorama.
  const phase = Math.random() * 6;
  const tick = (t) => { torso.position.y = torsoY + Math.sin(t * 1.4 + phase) * 0.008; };
  return { group: g, anchor, tick };
}
