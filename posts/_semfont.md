# A font that reads what you wrote

[semfont](https://github.com/RohanAdwankar/semfont) is a small library that sets typography from what the text means instead of from markup. Negative things go red. Important things get heavier. Surprising things get highlighted. Hedged things lean. Nothing in the pipeline is a model.

The box below is live and every word in it is editable. It is running the same engine the library ships.

<div>
<link rel="preconnect" href="https://cdn.jsdelivr.net">
<link rel="modulepreload" href="https://cdn.jsdelivr.net/npm/semfont@0.1.0/src/analyze.js">
<link rel="modulepreload" href="https://cdn.jsdelivr.net/npm/semfont@0.1.0/src/theme.js">
<link rel="modulepreload" href="https://cdn.jsdelivr.net/npm/semfont@0.1.0/src/lexicon.js">
<link rel="modulepreload" href="https://cdn.jsdelivr.net/npm/semfont@0.1.0/src/deep.js">
</div>

<style>
@import url('https://fonts.googleapis.com/css2?family=Recursive:CASL,MONO,slnt,wght@0..1,0..1,-15..0,300..1000&display=swap');
.sf, .sf-demo { font-family: 'Recursive', ui-sans-serif, system-ui, sans-serif; font-variation-settings: 'MONO' 0, 'CASL' 0; -webkit-font-smoothing: antialiased; }
.sf span, .sf-out span { transition: color .22s ease, background .22s ease, opacity .22s ease; line-height: 1; }
@media (prefers-reduced-motion: reduce) { .sf span, .sf-out span { transition: none; } }
.sf-samples { display: flex; flex-wrap: wrap; gap: 8px; margin: 22px 0 10px; }
.sf-samples button, .sf-themes label { font: inherit; font-family: 'Recursive', ui-sans-serif, system-ui, sans-serif; font-size: .8rem; color: inherit; opacity: .75; cursor: pointer; background: transparent; border: 1px solid #3a3a3a; border-radius: 2rem; padding: 4px 13px; }
.sf-samples button:hover, .sf-themes label:hover { opacity: 1; }
.sf-samples button[aria-pressed="true"], .sf-themes label:has(input:checked) { opacity: 1; border-color: currentColor; }
.sf-themes input { position: absolute; opacity: 0; width: 0; height: 0; }
.sf-demo { border: 1px solid #3a3a3a; border-radius: 8px; overflow: hidden; margin: 0 0 8px; }
.sf-out { padding: 22px 24px; font-size: clamp(1.25rem, 2.6vw, 1.6rem); line-height: 1.5; letter-spacing: -0.006em; height: 6em; overflow-y: auto; white-space: pre-wrap; }
.sf-out { outline: none; cursor: text; caret-color: currentColor; }
.sf-out:empty::before { content: attr(data-placeholder); opacity: .45; }
.sf-demo:focus-within { border-color: #6a6a6a; }
.sf-bar { display: flex; flex-wrap: wrap; justify-content: flex-start; align-items: center; gap: 8px 24px; margin: 10px 0 30px; font-family: 'Recursive', ui-sans-serif, system-ui, sans-serif; font-size: .8rem; }
.sf-themes { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.sf-themes span { opacity: .7; margin-right: 4px; }
.sf-timing { opacity: .7; font-variation-settings: 'MONO' 1; font-variant-numeric: tabular-nums; }
.sf-compare { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; background: #3a3a3a; border: 1px solid #3a3a3a; border-radius: 8px; overflow: hidden; margin: 20px 0 8px; }
.sf-compare > div { background: #1a1a1a; padding: 10px 14px; font-size: .98rem; line-height: 1.5; }
.sf-compare > .h { font-family: 'Recursive', ui-sans-serif, system-ui, sans-serif; font-size: .78rem; opacity: .7; padding: 8px 14px; }
body.light .sf-compare { background: #d0d0d0; border-color: #d0d0d0; }
body.light .sf-compare > div { background: #fff; }
@media (max-width: 480px) { .sf-compare > div { font-size: .88rem; padding: 8px 10px; } }
body.light .sf-demo, body.light .sf-samples button, body.light .sf-themes label { border-color: #d0d0d0; }
body.light .sf-samples button[aria-pressed="true"], body.light .sf-themes label:has(input:checked) { border-color: currentColor; }
body.light .sf-demo:focus-within { border-color: #888; }
</style>

<div class="sf-samples" id="sf-samples"></div>

<div class="sf-demo">
<div class="sf-out" id="sf-out" contenteditable="plaintext-only" spellcheck="false" role="textbox" aria-multiline="true" aria-label="text to set" data-placeholder="Type anything. It is set as you type."></div>
</div>

<div class="sf-bar">
<div class="sf-themes" id="sf-themes">
<span>theme</span>
<label><input type="radio" name="sf-theme" value="editorial" checked> editorial</label>
<label><input type="radio" name="sf-theme" value="loud"> loud</label>
<label><input type="radio" name="sf-theme" value="monochrome"> monochrome</label>
<label><input type="radio" name="sf-theme" value="technical"> technical</label>
</div>
<div class="sf-themes" id="sf-depths">
<span>engine</span>
<label><input type="radio" name="sf-depth" value="fast" checked> fast</label>
<label><input type="radio" name="sf-depth" value="deep"> deep</label>
</div>
<span class="sf-timing" id="sf-timing"></span>
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

## Two engines

The fast engine is what you have been using. Each word gets its lexicon entry and a look at two or three neighbours. That is why it is a millisecond, and it is also why it reads `fixed the crash` as one good word and one bad word, or leaves `great` green six words after a `not`.

The deep engine runs a second pass over clauses instead of windows. Still no model, about twice the cost. Five rules. A negator reaches to the end of its clause. A resolver like `fixed`, `recovered` or `avoided` flips the harm it names, and a bad thing that `is gone` is the good outcome. Less of a bad thing is an improvement. `too` turns praise into a complaint. A lone `Great,` before bad news is sarcasm, and a quoted word the writer then calls `wrong` is not the writer's word.

The ten sentences that led to it, set by both. Left is fast, right is deep.

<div class="sf-compare" id="sf-compare">
<div class="h">fast</div><div class="h">deep</div>
<div class="sf" data-depth="fast">Great, another outage. Just what I needed today.</div><div class="sf" data-depth="deep">Great, another outage. Just what I needed today.</div>
<div class="sf" data-depth="fast">We fixed the crash and closed the security hole before anyone noticed.</div><div class="sf" data-depth="deep">We fixed the crash and closed the security hole before anyone noticed.</div>
<div class="sf" data-depth="fast">Did it fail? No, it passed every test.</div><div class="sf" data-depth="deep">Did it fail? No, it passed every test.</div>
<div class="sf" data-depth="fast">The cluster recovered from the crash in under a minute.</div><div class="sf" data-depth="deep">The cluster recovered from the crash in under a minute.</div>
<div class="sf" data-depth="fast">We avoided a catastrophic outage by catching the bug in staging.</div><div class="sf" data-depth="deep">We avoided a catastrophic outage by catching the bug in staging.</div>
<div class="sf" data-depth="fast">I would not go so far as to call the new editor great.</div><div class="sf" data-depth="deep">I would not go so far as to call the new editor great.</div>
<div class="sf" data-depth="fast">Less broken than last week, and far fewer complaints.</div><div class="sf" data-depth="deep">Less broken than last week, and far fewer complaints.</div>
<div class="sf" data-depth="fast">The memory leak is gone.</div><div class="sf" data-depth="deep">The memory leak is gone.</div>
<div class="sf" data-depth="fast">The reviewer called it "terrible", which is wrong.</div><div class="sf" data-depth="deep">The reviewer called it "terrible", which is wrong.</div>
<div class="sf" data-depth="fast">The API is too simple and the docs are too clever.</div><div class="sf" data-depth="deep">The API is too simple and the docs are too clever.</div>
</div>

The third row is the one case that was a plain bug rather than a missing rule. A one-word `No,` is an answer to the question before it, not a negation of what follows. That fix went into the fast engine too.

## Using it

One React component, no build step, no dependency but React.

```jsx
import { SemanticText } from 'semfont';

<SemanticText as="p">
  The migration ran clean on staging. In production it deleted the index,
  and the rollback failed too.
</SemanticText>
```

Pick a theme, an engine, or only the channels you want:

```jsx
<SemanticText text={incident} theme="monochrome" />
<SemanticText text={incident} depth="deep" />
<SemanticText text={incident} channels={['valence']} />
```

Teach it your own vocabulary:

```jsx
<SemanticText
  lexicon={{ valence: { flaky: -0.7, oncall: -0.4 }, salience: { rollback: 0.8 } }}
  text={incident}
/>
```

Or skip React and take the scores. `analyze` is the engine alone, four numbers per word, no CSS, and these imports work with no React installed:

```js
import { analyze } from 'semfont/analyze';
import { styleFor, themes } from 'semfont/theme';

const { tokens } = analyze('The rollback failed too.');
tokens[4];   // { text: 'failed', valence: -0.7, salience: 0.23, surprise: 0.06, certainty: 0, ... }
styleFor(tokens[4], themes.editorial).style;   // { color: 'color-mix(in oklab, currentColor, oklch(0.58 0.19 25) 53%)' }
```

That last form is how this page works. There is no bundler here, so one import map tells the browser where `semfont/analyze` and `semfont/theme` live, pinned to a version on npm, and the demo box above is the same three lines as the React component: analyze, style, render.

```html
<script type="importmap">
{ "imports": {
  "semfont/analyze": "https://cdn.jsdelivr.net/npm/semfont@0.1.0/src/analyze.js",
  "semfont/theme":   "https://cdn.jsdelivr.net/npm/semfont@0.1.0/src/theme.js"
} }
</script>
<script type="module">
  import { analyze } from 'semfont/analyze';
  import { styleFor, themes } from 'semfont/theme';
</script>
```

Code and demo at [github.com/RohanAdwankar/semfont](https://github.com/RohanAdwankar/semfont). MIT.

<script type="importmap">
{ "imports": {
  "semfont/analyze": "https://cdn.jsdelivr.net/npm/semfont@0.1.0/src/analyze.js",
  "semfont/theme":   "https://cdn.jsdelivr.net/npm/semfont@0.1.0/src/theme.js"
} }
</script>

<script type="module">
import { analyze } from 'semfont/analyze';
import { styleFor, themes } from 'semfont/theme';

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
const timing = document.getElementById('sf-timing');
const samples = document.getElementById('sf-samples');

let text = SAMPLES.incident;

// The prose specimens keep their original text so a theme change can re-set them.
const specimens = [...document.querySelectorAll('.sf')].map((el) => ({ el, text: el.textContent }));

function theme() {
  return themes[document.querySelector('[name=sf-theme]:checked').value];
}
function depth() {
  return document.querySelector('[name=sf-depth]:checked').value;
}

// The same three lines the React component runs: analyze, style, render.
function paint(el, text, th, d = 'fast') {
  const result = analyze(text, { depth: d });
  const frag = document.createDocumentFragment();
  for (const token of result.tokens) {
    const styled = styleFor(token, th);
    if (!styled) { frag.append(token.text); continue; }
    const span = document.createElement('span');
    Object.assign(span.style, styled.style);
    span.title = [...(token.notes ?? []), ...CHANNELS.map((c) => `${c} ${token[c].toFixed(2)}`)].join(' · ');
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

// The box is a fixed four lines and scrolls past that, so re-setting it
// keeps the scroll position and then makes sure the caret is in view.
function renderBox() {
  const caret = caretOffset();
  const scrollTop = out.scrollTop;
  const started = performance.now();
  paint(out, text, theme(), depth());
  const ms = performance.now() - started;
  timing.textContent = text ? `${text.length} characters scored and set in ${ms.toFixed(2)} ms` : '';
  out.scrollTop = scrollTop;
  placeCaret(caret);
  if (caret !== null) {
    const r = window.getSelection().getRangeAt(0).getBoundingClientRect();
    const b = out.getBoundingClientRect();
    if (r.bottom > b.bottom) out.scrollTop += r.bottom - b.bottom + 8;
    else if (r.top < b.top) out.scrollTop -= b.top - r.top + 8;
  }
}

function select(button) {
  for (const other of samples.querySelectorAll('button')) {
    other.setAttribute('aria-pressed', String(other === button));
  }
}

function renderAll() {
  for (const { el, text } of specimens) paint(el, text, themes.editorial, el.dataset.depth || 'fast');
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
document.getElementById('sf-depths').addEventListener('change', renderBox);
renderAll();
</script>
