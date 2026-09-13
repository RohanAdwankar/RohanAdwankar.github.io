# A font that reads what you wrote

I made a small library called [semfont](https://github.com/RohanAdwankar/semfont). It sets typography from what the text means instead of from markup. Negative things go red, important things get heavier, surprising things get highlighted, hedged things lean, and nothing in the pipeline is a model.

Every emphasis in your document is a claim you made by hand. The file keeps the bold and forgets the reason, so when the sentence changes, the emphasis stays where it was. semfont recomputes the emphasis from the sentence every time the sentence changes. You can try that here. The box below is live, and it is running the same engine the library ships.

<style>
@import url('https://fonts.googleapis.com/css2?family=Recursive:CASL,MONO,slnt,wght@0..1,0..1,-15..0,300..1000&display=swap');
.sf, .sf-demo { font-family: 'Recursive', ui-sans-serif, system-ui, sans-serif; font-variation-settings: 'MONO' 0, 'CASL' 0; -webkit-font-smoothing: antialiased; }
.sf span, .sf-out span { transition: font-variation-settings .22s ease, color .22s ease, background .22s ease, font-size .22s ease; }
@media (prefers-reduced-motion: reduce) { .sf span, .sf-out span { transition: none; } }
.sf-samples { display: flex; flex-wrap: wrap; gap: 8px; margin: 22px 0 10px; }
.sf-samples button, .sf-themes label { font: inherit; font-family: 'Recursive', ui-sans-serif, system-ui, sans-serif; font-size: .8rem; color: inherit; opacity: .75; cursor: pointer; background: transparent; border: 1px solid #3a3a3a; border-radius: 2rem; padding: 4px 13px; }
.sf-samples button:hover, .sf-themes label:hover { opacity: 1; }
.sf-samples button[aria-pressed="true"], .sf-themes label:has(input:checked) { opacity: 1; border-color: currentColor; }
.sf-themes input { position: absolute; opacity: 0; width: 0; height: 0; }
.sf-demo { border: 1px solid #3a3a3a; border-radius: 8px; overflow: hidden; margin: 0 0 8px; }
.sf-out { padding: 22px 24px; font-size: clamp(1.25rem, 2.6vw, 1.6rem); line-height: 1.5; letter-spacing: -0.006em; min-height: 4em; white-space: pre-wrap; }
.sf-edit { display: block; width: 100%; box-sizing: border-box; border: 0; border-top: 1px solid #3a3a3a; background: transparent; color: inherit; opacity: .7; resize: vertical; padding: 12px 24px 14px; font: inherit; font-family: 'Recursive', ui-sans-serif, system-ui, sans-serif; font-size: .9rem; line-height: 1.5; min-height: 4.6rem; }
.sf-edit:focus { opacity: 1; outline: none; }
.sf-cap { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 6px 16px; font-size: .8rem; opacity: .7; margin: 0 0 12px; }
.sf-themes { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; font-size: .8rem; margin: 0 0 30px; }
.sf-themes span { opacity: .7; margin-right: 4px; }
.sf-timing { font-variation-settings: 'MONO' 1; font-variant-numeric: tabular-nums; }
.sf-pair { display: grid; gap: 12px; margin: 20px 0 12px; }
@media (min-width: 620px) { .sf-pair { grid-template-columns: 1fr 1fr; } }
.sf-pair > div { border: 1px solid #3a3a3a; border-radius: 8px; padding: 16px 18px; font-size: 1.1rem; line-height: 1.55; }
.sf-quote { border-left: 2px solid #3a3a3a; padding: 4px 0 4px 20px; margin: 20px 0; font-size: 1.15rem; line-height: 1.6; }
body.light .sf-demo, body.light .sf-edit, body.light .sf-pair > div, body.light .sf-quote, body.light .sf-samples button, body.light .sf-themes label { border-color: #d0d0d0; }
body.light .sf-samples button[aria-pressed="true"], body.light .sf-themes label:has(input:checked) { border-color: currentColor; }
</style>

<div class="sf-samples" id="sf-samples"></div>

<div class="sf-demo">
<div class="sf-out" id="sf-out"></div>
<textarea class="sf-edit" id="sf-edit" spellcheck="false" aria-label="text to set" placeholder="Type anything. It is set as you type."></textarea>
</div>

<p class="sf-cap"><span>Nothing here was marked up.</span> <span class="sf-timing" id="sf-timing"></span></p>

<div class="sf-themes" id="sf-themes">
<span>theme</span>
<label><input type="radio" name="sf-theme" value="editorial" checked> editorial</label>
<label><input type="radio" name="sf-theme" value="loud"> loud</label>
<label><input type="radio" name="sf-theme" value="monochrome"> monochrome</label>
<label><input type="radio" name="sf-theme" value="technical"> technical</label>
</div>

Start with the first sample. `clean` comes out green, `deleted` gains weight, `failed` and `painful` go red, and `postmortem` is marked because it sits in the clause after `but`, the half of the sentence that turned. Then edit it. Put a `not` in front of `clean` and watch it change its mind.

If you would rather see it set a whole page, headings included, [this page](/semfont/) is the engine let loose on itself. Every word on it is scored and styled at load, and the rail on the left re-runs it.

## Four channels, four axes

Every token gets four scores, and each score drives a different axis, so they compose rather than collide.

| channel | detects | moves |
|---|---|---|
| valence | how the text feels | colour |
| salience | what it points at | weight, size |
| surprise | where it turns | highlight |
| certainty | how sure it is | slant, opacity |

A word can be negative and hedged and the subject of the paragraph all at once, and you see all three: dark red, leaning, heavy. Switch a channel off and the other three carry on, independent down to the CSS.

Four is the default rather than the limit. The map from channel to axis is a list of rows, so adding one is a line of data. Pick the `technical` theme above and a fifth channel wakes up. It reads identifiers by their shape and sends `readFileSync` and `cluster_config` toward monospace on the font's `MONO` axis while the other four carry on as they were. The ceiling on this is legibility, not speed.

## The six things you are probably thinking of

Nearly everyone who sees this places it next to something they already know, so it is worth saying what each of those is and why it is a different problem.

**Syntax highlighting** colours by grammar, from a parser, and the categories are fixed by the language. Prose has no keywords. There is no token type that `failed` belongs to.

**Bionic Reading** bolds the first few letters of every word. That is one rule applied uniformly, which is why it works at all. But it never reads a word, so `catastrophe` and `the` are treated identically.

**A sentiment dashboard** analyses a document and reports a number about it, somewhere else, afterwards. This sets the document, in place, while you type.

**`<em>` and `<strong>`** are the real incumbent, and they are hand-made claims. The file keeps the emphasis and forgets the reason, so it stays exactly where you put it after the sentence around it has changed.

**An LLM** would beat this on every question of judgement, and could never be a font. More on that below.

**Variable font sliders** are a control surface, not a decision. `wght` from 100 to 1000 is the mechanism this uses. It does not answer what the weight of this particular word should be.

What is left over, once all six are set aside, is the actual claim: the typography is a function of the sentence, and it is recomputed whenever the sentence changes.

## Negation, where the naive version dies

These two sentences are made of the same words. Both are set live by the engine.

<div class="sf-pair">
<div class="sf">The launch was great and the numbers were excellent.</div>
<div class="sf">The launch was not great and the numbers were not excellent.</div>
</div>

The second goes red, and a paler red than a sentence of genuinely nasty words, because `not great` registers as a complaint rather than a catastrophe. One rule does it: on hitting a negator within three content words, flip the sign and multiply by 0.74. Sentiment analysis has known that number since VADER, and it still separates a demo from something you would ship.

## One millisecond, no model

Sending the paragraph to a model buys you sarcasm detection, at a few hundred milliseconds, an API key, a network, and a copy of the reader's draft on someone else's machine, per keystroke.

The number under the box is the argument. Four lexicons and about two hundred lines of rules score a page of prose in roughly a millisecond, synchronously, offline, with the same answer every time. Cheap enough to run inside the input event, during a server render, on a plane, which is what lets it behave the way italics do.

The lexicons are small enough to read in one sitting and to argue with. When the styling is wrong you can see which entry did it and fix it in a line, or teach it your own vocabulary.

```jsx
<SemanticText
  lexicon={{ valence: { flaky: -0.7, oncall: -0.4 } }}
  text={incident}
/>
```

## Restraint

The first version styled every word it had an opinion about and looked like a ransom note. The default thresholds now leave most words alone. A paragraph gets a handful. Emphasis works by contrast, so it exists only relative to text that nothing happened to.

Colour also never carries a channel by itself. Switch the box above to `monochrome` and all four channels ride on slant, weight, size, an underline and tracking, which is both the accessible answer and the better looking one in print.

## Where it fails

It reads words rather than arguments, so a calm sentence describing a catastrophe goes straight past it. Sarcasm defeats it. It speaks only English. A model beats it on all three, and could never be a font.

## Using it

One React component, no build step, no dependency but React.

```jsx
import { SemanticText } from 'semfont';

<SemanticText as="p">
  The migration ran clean on staging. In production it deleted the index,
  and the rollback failed too.
</SemanticText>
```

Take only the part you want. `channels={['valence']}` gives you colour and nothing else. A theme object changes which axis a channel drives. `useSemanticText` hands back the scores for your own rendering. `analyze(text)` is the engine alone, four numbers per token, with no React and no CSS at all. The engine files import nothing, which is how this page is running them.

The code, the tests and the demo are at [github.com/RohanAdwankar/semfont](https://github.com/RohanAdwankar/semfont). MIT.

<script type="module">
import { analyze } from '/semfont/src/analyze.js';
import { styleFor, themes } from '/semfont/src/theme.js';

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
const edit = document.getElementById('sf-edit');
const timing = document.getElementById('sf-timing');
const samples = document.getElementById('sf-samples');

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

function renderBox() {
  const started = performance.now();
  paint(out, edit.value, theme());
  const ms = performance.now() - started;
  timing.textContent = `${edit.value.length} characters scored and set in ${ms.toFixed(2)} ms`;
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
    edit.value = SAMPLES[name];
    for (const other of samples.querySelectorAll('button')) {
      other.setAttribute('aria-pressed', String(other === b));
    }
    renderBox();
  });
  samples.append(b);
}

edit.addEventListener('input', () => {
  for (const b of samples.querySelectorAll('button')) b.setAttribute('aria-pressed', 'false');
  renderBox();
});
document.getElementById('sf-themes').addEventListener('change', renderAll);
edit.value = SAMPLES.incident;
renderAll();
</script>
