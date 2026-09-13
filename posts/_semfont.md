# A font that reads what you wrote

[semfont](https://github.com/RohanAdwankar/semfont) is a small library that sets typography from what the text means instead of from markup. Negative things go red. Important things get heavier. Surprising things get highlighted. Hedged things lean. Nothing in the pipeline is a model.

The box below is live and every word in it is editable. It is running the same engine the library ships.

<style>
@import url('https://fonts.googleapis.com/css2?family=Recursive:CASL,MONO,slnt,wght@0..1,0..1,-15..0,300..1000&display=swap');
.sf, .sf-demo { font-family: 'Recursive', ui-sans-serif, system-ui, sans-serif; font-variation-settings: 'MONO' 0, 'CASL' 0; -webkit-font-smoothing: antialiased; }
.sf span, .sf-out span { transition: color .22s ease, background .22s ease, opacity .22s ease; }
@media (prefers-reduced-motion: reduce) { .sf span, .sf-out span { transition: none; } }
.sf-samples { display: flex; flex-wrap: wrap; gap: 8px; margin: 22px 0 10px; }
.sf-samples button, .sf-themes label { font: inherit; font-family: 'Recursive', ui-sans-serif, system-ui, sans-serif; font-size: .8rem; color: inherit; opacity: .75; cursor: pointer; background: transparent; border: 1px solid #3a3a3a; border-radius: 2rem; padding: 4px 13px; }
.sf-samples button:hover, .sf-themes label:hover { opacity: 1; }
.sf-samples button[aria-pressed="true"], .sf-themes label:has(input:checked) { opacity: 1; border-color: currentColor; }
.sf-themes input { position: absolute; opacity: 0; width: 0; height: 0; }
.sf-demo { position: relative; border: 1px solid #3a3a3a; border-radius: 8px; overflow: hidden; margin: 0 0 8px; }
.sf-measure { position: absolute; left: 0; top: 0; box-sizing: border-box; visibility: hidden; pointer-events: none; min-height: 0; }
.sf-out { padding: 22px 24px; font-size: clamp(1.25rem, 2.6vw, 1.6rem); line-height: 1.5; letter-spacing: -0.006em; min-height: 4em; white-space: pre-wrap; }
.sf-out { outline: none; cursor: text; caret-color: currentColor; }
.sf-out:empty::before { content: attr(data-placeholder); opacity: .45; }
.sf-demo:focus-within { border-color: #6a6a6a; }
.sf-cap { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 6px 16px; font-size: .8rem; opacity: .7; margin: 0 0 12px; }
.sf-themes { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; font-size: .8rem; margin: 0 0 30px; }
.sf-themes span { opacity: .7; margin-right: 4px; }
.sf-timing { font-variation-settings: 'MONO' 1; font-variant-numeric: tabular-nums; }
body.light .sf-demo, body.light .sf-samples button, body.light .sf-themes label { border-color: #d0d0d0; }
body.light .sf-samples button[aria-pressed="true"], body.light .sf-themes label:has(input:checked) { border-color: currentColor; }
body.light .sf-demo:focus-within { border-color: #888; }
</style>

<div class="sf-samples" id="sf-samples"></div>

<div class="sf-demo">
<div class="sf-out" id="sf-out" contenteditable="plaintext-only" spellcheck="false" role="textbox" aria-multiline="true" aria-label="text to set" data-placeholder="Type anything. It is set as you type."></div>
<div class="sf-out sf-measure" id="sf-measure" aria-hidden="true"></div>
</div>

<p class="sf-cap"><span class="sf-timing" id="sf-timing"></span></p>

<div class="sf-themes" id="sf-themes">
<span>theme</span>
<label><input type="radio" name="sf-theme" value="editorial" checked> editorial</label>
<label><input type="radio" name="sf-theme" value="loud"> loud</label>
<label><input type="radio" name="sf-theme" value="monochrome"> monochrome</label>
<label><input type="radio" name="sf-theme" value="technical"> technical</label>
</div>

## How it works

Every word gets four scores. Each score drives a different typographic axis, so they compose instead of collide.

| channel | detects | moves |
|---|---|---|
| valence | how the text feels | colour |
| salience | what it points at | weight, size |
| surprise | where it turns | highlight |
| certainty | how sure it is | slant, opacity |

The scores come from small lexicons and a few local rules, not a model. Negation flips a word and damps it, so `not great` reads as a complaint rather than a catastrophe. Rarity is measured against the passage, so the topic words of a paragraph float up on their own.

That is what makes it usable as a font rather than a feature. A page of prose scores in about a millisecond, synchronously, offline, with the same answer every time. It runs on every keystroke, during a server render, on a plane. A model would read sarcasm better and could never do that.

## What it gets wrong

Sarcasm, irony, and jargon it has not been taught. It reads words, not arguments, so a calm sentence describing a catastrophe goes straight past it. English only.

## Using it

One React component, no build step, no dependency but React. `analyze(text)` is the engine on its own, four numbers per word, no React and no CSS. Code and demo at [github.com/RohanAdwankar/semfont](https://github.com/RohanAdwankar/semfont). MIT.

<script type="module">
import { analyze } from '/js/semfont/analyze.js';
import { styleFor, themes } from '/js/semfont/theme.js';

const CHANNELS = ['valence', 'salience', 'surprise', 'certainty', 'technicality'];

const SAMPLES = {
  'incident': 'The migration ran clean on staging. In production it deleted the '
    + 'index, and the rollback failed too. Nobody lost data, but the postmortem '
    + 'is going to be painful.',
  'a dangerous command': 'WARNING: this operation is irreversible. It will drop '
    + '1.2TB of production user data immediately and there is no undo. Type the '
    + 'cluster name to continue.',
  'a hedged review': 'I think the allocator might be the culprit, but honestly '
    + 'the profiler output is unreadable. The regression is definitely real: p99 '
    + 'doubled on Tuesday and never came back.',
  'a bad review': 'Absolutely the worst onboarding I have ever suffered through. '
    + 'Three broken links, a crash on signup, and then it silently deleted my '
    + 'project. Support was lovely about it.',
  'release notes': 'The new scheduler shipped on Tuesday. Startup is 40% faster '
    + 'and the old crash on reload is fixed. One known bug: watch mode still '
    + 'leaks file descriptors on very large trees.',
  'a bug report': 'readFileSync throws ENOENT on cluster_config.yaml whenever the '
    + 'kubelet restarts, and p99 latency doubles while the retry loop spins. '
    + 'Probably a race in the watcher, but the stack trace is unreadable.',
};

const out = document.getElementById('sf-out');
const measure = document.getElementById('sf-measure');
const timing = document.getElementById('sf-timing');
const samples = document.getElementById('sf-samples');

let text = SAMPLES.incident;

// The prose specimens keep their original text so a theme change can re-set them.
const specimens = [...document.querySelectorAll('.sf')].map((el) => ({ el, text: el.textContent }));

function theme() {
  return themes[document.querySelector('[name=sf-theme]:checked').value];
}

// The same three lines the React component runs: analyze, style, render.
function paint(el, text, th) {
  const result = analyze(text);
  const frag = document.createDocumentFragment();
  for (const token of result.tokens) {
    const styled = styleFor(token, th);
    if (!styled) { frag.append(token.text); continue; }
    const span = document.createElement('span');
    Object.assign(span.style, styled.style);
    span.title = CHANNELS.map((c) => `${c} ${token[c].toFixed(2)}`).join(' · ');
    span.textContent = token.text;
    frag.append(span);
  }
  el.replaceChildren(frag);
}

// The box is the editor. Re-setting it replaces every node under the
// caret, so the caret's position is saved as a character offset first and
// put back afterwards.
function caretOffset() {
  const sel = window.getSelection();
  if (!sel || !sel.rangeCount || !out.contains(sel.anchorNode)) return null;
  const range = sel.getRangeAt(0).cloneRange();
  range.selectNodeContents(out);
  range.setEnd(sel.getRangeAt(0).endContainer, sel.getRangeAt(0).endOffset);
  return range.toString().length;
}

function placeCaret(offset) {
  if (offset === null) return;
  const walker = document.createTreeWalker(out, NodeFilter.SHOW_TEXT);
  let remaining = offset;
  let node = walker.nextNode();
  let last = null;
  while (node) {
    if (remaining <= node.nodeValue.length) break;
    remaining -= node.nodeValue.length;
    last = node;
    node = walker.nextNode();
  }
  const range = document.createRange();
  if (node) range.setStart(node, remaining);
  else if (last) range.setStart(last, last.nodeValue.length);
  else range.setStart(out, 0);
  range.collapse(true);
  const sel = window.getSelection();
  sel.removeAllRanges();
  sel.addRange(range);
}

// The themes set the same text at different sizes and weights, so the box
// would change height when the theme changes and shove the page around.
// It is held at the height of the tallest theme for the current text.
function lockHeight() {
  measure.style.width = `${out.getBoundingClientRect().width}px`;
  let tallest = 0;
  for (const th of Object.values(themes)) {
    paint(measure, text, th);
    tallest = Math.max(tallest, measure.offsetHeight);
  }
  measure.replaceChildren();
  out.style.minHeight = `${tallest}px`;
}

function renderBox() {
  const caret = caretOffset();
  const started = performance.now();
  paint(out, text, theme());
  const ms = performance.now() - started;
  timing.textContent = text ? `${text.length} characters scored and set in ${ms.toFixed(2)} ms` : '';
  placeCaret(caret);
  lockHeight();
}

function select(button) {
  for (const other of samples.querySelectorAll('button')) {
    other.setAttribute('aria-pressed', String(other === button));
  }
}

function renderAll() {
  const th = theme();
  for (const { el, text } of specimens) paint(el, text, th);
  renderBox();
}

for (const name of Object.keys(SAMPLES)) {
  const b = document.createElement('button');
  b.type = 'button';
  b.textContent = name;
  b.setAttribute('aria-pressed', String(name === 'incident'));
  b.addEventListener('click', () => {
    text = SAMPLES[name];
    select(b);
    renderBox();
  });
  samples.append(b);
}

// The last chip empties the box for text of your own.
const tryIt = document.createElement('button');
tryIt.type = 'button';
tryIt.textContent = 'try it!';
tryIt.setAttribute('aria-pressed', 'false');
tryIt.addEventListener('click', () => {
  text = '';
  select(tryIt);
  renderBox();
  out.focus();
});
samples.append(tryIt);

// Typing into the box re-sets it on every keystroke, except mid-way through
// an IME composition, which would be broken by replacing the nodes.
let composing = false;
out.addEventListener('compositionstart', () => { composing = true; });
out.addEventListener('compositionend', () => { composing = false; text = out.innerText; renderBox(); });
out.addEventListener('input', () => {
  if (composing) return;
  text = out.innerText.replace(/\n$/, '');
  renderBox();
});
// Pasted rich text comes in as plain text.
out.addEventListener('paste', (e) => {
  e.preventDefault();
  document.execCommand('insertText', false, e.clipboardData.getData('text/plain'));
});
document.getElementById('sf-themes').addEventListener('change', renderAll);
let resizeTimer;
window.addEventListener('resize', () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(lockHeight, 100); });
renderAll();
</script>
