# A font that reads what you wrote

[semfont](https://github.com/RohanAdwankar/semfont) is a small library that sets typography automatically. 
As you can see below it automatically highlights, colors, bolds, and italicizes text which aims to make it easier to read.

<div>
<link rel="preconnect" href="https://cdn.jsdelivr.net">
<link rel="modulepreload" href="https://cdn.jsdelivr.net/npm/semfont@0.2.0/src/analyze.js">
<link rel="modulepreload" href="https://cdn.jsdelivr.net/npm/semfont@0.2.0/src/theme.js">
<link rel="modulepreload" href="https://cdn.jsdelivr.net/npm/semfont@0.2.0/src/lexicon.js">
<link rel="modulepreload" href="https://cdn.jsdelivr.net/npm/semfont@0.2.0/src/deep.js">
<link rel="modulepreload" href="https://cdn.jsdelivr.net/npm/semfont@0.2.0/src/vader.js">
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
.sf-cases { border: 1px solid #3a3a3a; border-radius: 8px; overflow: hidden; margin: 20px 0; }
.sf-cases > div { background: #1a1a1a; padding: 10px 14px; font-size: .98rem; line-height: 1.5; }
.sf-cases > div + div { border-top: 1px solid #3a3a3a; }
body.light .sf-cases { border-color: #d0d0d0; }
body.light .sf-cases > div { background: #fff; }
body.light .sf-cases > div + div { border-top-color: #d0d0d0; }
.sf-compare { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; background: #3a3a3a; border: 1px solid #3a3a3a; border-radius: 8px; overflow: hidden; margin: 20px 0 8px; }
.sf-compare > div { background: #1a1a1a; padding: 10px 14px; font-size: .98rem; line-height: 1.5; }
.sf-compare > .h { font-family: 'Recursive', ui-sans-serif, system-ui, sans-serif; font-size: .78rem; opacity: .7; padding: 8px 14px; }
body.light .sf-compare { background: #d0d0d0; border-color: #d0d0d0; }
body.light .sf-compare > div { background: #fff; }
@media (max-width: 480px) { .sf-compare > div { font-size: .88rem; padding: 8px 10px; } }
body.light .sf-demo, body.light .sf-samples button, body.light .sf-themes label { border-color: #d0d0d0; }
body.light .sf-samples button[aria-pressed="true"], body.light .sf-themes label:has(input:checked) { border-color: currentColor; }
body.light .sf-demo:focus-within { border-color: #888; }
.sf-chat { border: 1px solid #3a3a3a; border-radius: 8px; overflow: hidden; margin: 20px 0 8px; font-family: 'Recursive', ui-sans-serif, system-ui, sans-serif; font-variation-settings: 'MONO' 0, 'CASL' 0; -webkit-font-smoothing: antialiased; }
.sf-ask { display: flex; gap: 8px; padding: 10px 12px; border-bottom: 1px solid #3a3a3a; margin: 0; }
.sf-ask input { flex: 1; min-width: 0; font: inherit; font-size: .9rem; color: inherit; background: transparent; border: 1px solid #3a3a3a; border-radius: 6px; padding: 6px 10px; opacity: .85; }
.sf-ask button { font: inherit; font-size: .8rem; color: inherit; background: transparent; border: 1px solid currentColor; border-radius: 2rem; padding: 4px 13px; cursor: pointer; }
.sf-ask button:disabled { opacity: .4; cursor: default; }
.sf-reply { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; background: #3a3a3a; }
.sf-reply section { background: #1a1a1a; padding: 10px 14px 14px; }
.sf-reply h4 { margin: 0 0 6px; font-size: .78rem; font-weight: 400; opacity: .7; }
.sf-reply p { margin: 0; font-size: .98rem; line-height: 1.5; height: 19.5em; overflow-y: auto; white-space: pre-wrap; }
.sf-reply p span { line-height: 1; transition: color .22s ease, background .22s ease, opacity .22s ease; }
.sf-reply p.streaming::after { content: ''; display: inline-block; width: .5em; height: 1em; background: currentColor; opacity: .5; vertical-align: -.15em; margin-left: 2px; }
@media (max-width: 480px) { .sf-reply { grid-template-columns: 1fr; } .sf-reply p { font-size: .9rem; height: 16.5em; } }
body.light .sf-chat, body.light .sf-ask, body.light .sf-ask input { border-color: #d0d0d0; }
body.light .sf-reply { background: #d0d0d0; }
body.light .sf-reply section { background: #fff; }
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
<span class="sf-timing" id="sf-timing"></span>
</div>

## How it works

Every word gets four scores. Each one starts as a dictionary lookup and is then adjusted by a couple of rules over the words around it. That is the whole algorithm; there is no model anywhere in it.

**Valence** is how good or bad the word is, from -1 to 1. A negator up to three words back flips the sign and damps it, because `not great` is a mild complaint rather than the mirror image of praise. An intensifier up to two words back scales it instead.

```js
let v = VALENCE[word] ?? 0;          // great -> 0.75
if (negatorWithin(3)) v = -v * 0.74; // not great -> -0.55
v *= gain;                           // really great -> 0.98
```

**Salience** is how much the word is worth looking at, 0 to 1. A frequency list gives each word a rarity, 0 for one of the hundred most common English words and 1 for one it has never seen. Rarity alone is not enough, so the score also rises with how often the word repeats in this particular text: an uncommon word you keep saying is what the text is about.

```js
const seen = Math.min(1, (repeats - 1) / 2);
const repetition = 0.45 + 0.55 * seen;
let s = SALIENCE[word] ?? 0;
s = Math.max(s, 0.55 * rarity * repetition);

// rarity('the') 0.00, rarity('kubelet') 0.93
// kubelet said once   -> 0.23
// kubelet said 3 times -> 0.51
```

**Surprise** is where the sentence turns, 0 to 1. Some words announce it on their own, like `suddenly` or `ironically`. Otherwise it comes from position: everything for six words after a contrast word gets it, decaying with distance, and so does any word much rarer than the rest of the passage.

```js
let s = SURPRISE[word] ?? 0;         // suddenly -> 0.85
if (afterContrast) {
  s = Math.max(s, 0.45 * 0.82 ** (distance - 1));
}
s += 0.3 * Math.max(0, rarity - passageMeanRarity - 0.25);

// 'The tests failed'            -> failed 0.16
// 'It compiled, but the tests failed' -> failed 0.44
```

**Certainty** is how sure the writer sounds, -1 hedged to 1 asserted. A hedge scores itself, and it also leans the rest of its sentence, because hedging one clause hedges the claim.

```js
c = CERTAINTY[word] ?? sentenceCertainty * 0.55;

// 'The build probably failed.'
// probably -0.40, every other word -0.22
```

Then a theme maps each score to one typographic axis, so they stack instead of fighting: valence to colour, salience to weight, surprise to a highlight, certainty to slant. Each axis has a threshold, so most words come out untouched.

That is four lookups and a dozen lines of arithmetic per word, which is why it runs in under a millisecond per hundred words, on every keystroke, offline, with the same answer every time. A model would read sarcasm better and could never do that.

## Improving the algorithm

Those rules only look a few words either side, and that window has a blind spot. Take these two sentences:

<div class="sf-cases">
<div class="sf" data-when="before">I would not go so far as to call the new editor great.</div>
<div class="sf" data-when="before">We fixed the crash.</div>
</div>

The first left `great` green, because the `not` that cancels it sits nine words back, well outside the window. The second painted one word green and one word red, because nothing connected `fixed` to the thing it fixed.

So a second pass now runs after the window rules and reads each clause as a whole. A negator reaches to the end of its clause and fades with distance, which turns `great` red. A verb like `fixed`, `recovered` or `avoided` marks whatever follows it as the thing that got better, which turns `crash` green. The same pass reads `less broken` and `fewer complaints` as improvements, `too simple` as a complaint, and a lone `Great,` in front of bad news as sarcasm.

Every change it makes is recorded on the word, so you can ask why a word came out the colour it did:

```js
analyze('We fixed the crash.').tokens[6];
// { text: 'crash', valence: 0.44,
//   notes: ['resolved by "fixed"'] }
```

It costs about as much as the first pass and stays inside the budget, so there is no switch to flip. These are the ten sentences that led to it. Left is the first version, right is now.

<div class="sf-compare" id="sf-compare">
<div class="h">before</div><div class="h">now</div>
<div class="sf" data-when="before">Great, another outage. Just what I needed today.</div><div class="sf" data-when="now">Great, another outage. Just what I needed today.</div>
<div class="sf" data-when="before">We fixed the crash and closed the security hole before anyone noticed.</div><div class="sf" data-when="now">We fixed the crash and closed the security hole before anyone noticed.</div>
<div class="sf" data-when="before">Did it fail? No, it passed every test.</div><div class="sf" data-when="now">Did it fail? No, it passed every test.</div>
<div class="sf" data-when="before">The cluster recovered from the crash in under a minute.</div><div class="sf" data-when="now">The cluster recovered from the crash in under a minute.</div>
<div class="sf" data-when="before">We avoided a catastrophic outage by catching the bug in staging.</div><div class="sf" data-when="now">We avoided a catastrophic outage by catching the bug in staging.</div>
<div class="sf" data-when="before">I would not go so far as to call the new editor great.</div><div class="sf" data-when="now">I would not go so far as to call the new editor great.</div>
<div class="sf" data-when="before">Less broken than last week, and far fewer complaints.</div><div class="sf" data-when="now">Less broken than last week, and far fewer complaints.</div>
<div class="sf" data-when="before">The memory leak is gone.</div><div class="sf" data-when="now">The memory leak is gone.</div>
<div class="sf" data-when="before">The reviewer called it "terrible", which is wrong.</div><div class="sf" data-when="now">The reviewer called it "terrible", which is wrong.</div>
<div class="sf" data-when="before">The API is too simple and the docs are too clever.</div><div class="sf" data-when="now">The API is too simple and the docs are too clever.</div>
</div>

The third row is the one case that was a plain bug rather than a missing rule. A one-word `No,` is an answer to the question before it, not a negation of what follows. That fix went into the first pass.

## Using it

One React component, no build step, no dependency but React.

```jsx
import { SemanticText } from 'semfont';

<SemanticText as="p">
  The migration ran clean on staging. In production it deleted the index,
  and the rollback failed too.
</SemanticText>
```

Pick a theme, or only the channels you want:

```jsx
<SemanticText text={incident} theme="monochrome" />
<SemanticText text={incident} channels={['valence']} />
```

Teach it your own vocabulary:

```jsx
<SemanticText
  lexicon={{ valence: { flaky: -0.7, oncall: -0.4 }, salience: { rollback: 0.8 } }}
  text={incident}
/>
```

This is where the library started. Model output arrives as a wall of text at one weight, and setting it as it streams makes the answer scannable before it has finished. With the [Vercel AI SDK](https://ai-sdk.dev) that is the component wrapped around the text of each assistant message. Every chunk re-runs the engine on the message so far.

```jsx
import { useChat } from '@ai-sdk/react';
import { SemanticText } from 'semfont';

function Chat() {
  const { messages } = useChat();
  return messages.map((m) => {
    const text = m.parts.filter((p) => p.type === 'text').map((p) => p.text).join('');
    return m.role === 'assistant'
      ? <SemanticText key={m.id} as="p" text={text} />
      : <p key={m.id}>{text}</p>;
  });
}
```

<div class="sf-chat">
<form class="sf-ask" id="sf-ask"><input value="why did the deploy fail?" readonly aria-label="question"><button type="submit">send</button></form>
<div class="sf-reply">
<section><h4>plain text</h4><p id="sf-plain"></p></section>
<section><h4>semfont</h4><p id="sf-set"></p></section>
</div>
</div>

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
  "semfont/analyze": "https://cdn.jsdelivr.net/npm/semfont@0.2.0/src/analyze.js",
  "semfont/theme":   "https://cdn.jsdelivr.net/npm/semfont@0.2.0/src/theme.js"
} }
</script>
<script type="module">
  import { analyze } from 'semfont/analyze';
  import { styleFor, themes } from 'semfont/theme';
</script>
```

## Future work

Every rule so far fits under a millisecond per hundred words and the next ones will too, or they will not go into the default engine. Some things will not fit: sarcasm that needs the whole paragraph, a pronoun resolved back to what it names, a small model for the cases no rule catches. If one of those proves worth having it ships as a second model with its own budget, chosen explicitly, so the engine you get by default never gets slower than the one on this page.

Code and demo at [github.com/RohanAdwankar/semfont](https://github.com/RohanAdwankar/semfont). MIT.

<script type="importmap">
{ "imports": {
  "semfont/analyze": "https://cdn.jsdelivr.net/npm/semfont@0.2.0/src/analyze.js",
  "semfont/theme":   "https://cdn.jsdelivr.net/npm/semfont@0.2.0/src/theme.js",
  "semfont-first/analyze": "https://cdn.jsdelivr.net/npm/semfont@0.1.0/src/analyze.js"
} }
</script>

<script type="module">
import { analyze } from 'semfont/analyze';
import { styleFor, themes } from 'semfont/theme';
import { analyze as analyzeFirst } from 'semfont-first/analyze';

// The engine on the page, and the first version it is compared with below.
const score = (text) => analyze(text);
const scoreFirst = (text) => analyzeFirst(text);

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

// The same three lines the React component runs: analyze, style, render.
function paint(el, text, th, analyzeWith = score) {
  const result = analyzeWith(text);
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

// The reader types into the styled output itself. Re-setting it replaces every node under the
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
  paint(out, text, theme());
  // Browsers round performance.now() to as much as a millisecond, so one run
  // reads 1.00 or 2.00. Twenty runs averaged give a number that means something.
  const runs = 20;
  const started = performance.now();
  for (let i = 0; i < runs; i++) score(text);
  const ms = (performance.now() - started) / runs;
  timing.textContent = text ? `${text.length} characters scored in ${ms.toFixed(2)} ms` : '';
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
  for (const { el, text } of specimens) paint(el, text, themes.editorial, el.dataset.when === 'before' ? scoreFirst : score);
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
renderAll();

// The chat box. A stand-in model: the question is fixed and the reply is
// canned, but it arrives the way fetch('/api/chat') would, chunk by chunk
// through a ReadableStream, and the right pane is re-set on every chunk.
const ANSWER = 'The deploy failed because the migration dropped the sessions index before the new one existed. '
  + 'Traffic looked healthy for two minutes, then every login suddenly timed out. The rollback should '
  + 'have helped, but instead it made things worse by replaying the same migration. Recreating the '
  + 'index by hand fixed it. Staging probably never exercised the login path, so the check definitely '
  + 'passed and caught nothing. I suspect the retry loop is broken too.';
const ask = document.getElementById('sf-ask');
const send = ask.querySelector('button');
const plainOut = document.getElementById('sf-plain');
const setOut = document.getElementById('sf-set');

function fakeModel(text, ms = 100) {
  const words = text.match(/\S+\s*/g);
  let i = 0;
  return new ReadableStream({
    pull(controller) {
      return new Promise((resolve) => setTimeout(() => {
        if (i >= words.length) controller.close();
        else controller.enqueue(words.slice(i, i += 2).join(''));
        resolve();
      }, ms));
    },
  });
}

function show(text) {
  plainOut.textContent = text;
  paint(setOut, text, themes.editorial);
  for (const el of [plainOut, setOut]) el.scrollTop = el.scrollHeight;
}

async function reply() {
  send.disabled = true;
  plainOut.classList.add('streaming');
  setOut.classList.add('streaming');
  let text = '';
  const reader = fakeModel(ANSWER).getReader();
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    text += value;
    show(text);
  }
  plainOut.classList.remove('streaming');
  setOut.classList.remove('streaming');
  send.disabled = false;
}

ask.addEventListener('submit', (e) => { e.preventDefault(); reply(); });
</script>
