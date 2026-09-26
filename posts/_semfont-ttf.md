# semfont is a font now

<a class="hn-badge" href="https://news.ycombinator.com/item?id=49774161"><svg width="16" height="16" viewBox="0 0 24 24" aria-hidden="true"><rect width="24" height="24" rx="4" fill="#ff6600"/><text x="12" y="17.5" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-weight="bold" font-size="15" fill="#fff">Y</text></svg>Hacker News Discussion</a>

The loudest complaint about [semfont](https://github.com/RohanAdwankar/semfont) was that it is a
JavaScript library and not a font. Four people said it, one called it a typesetter, and they were
right. Someone in the same thread pointed at [fontemon](https://www.coderelay.io/fontemon.html),
a game that runs inside OpenType substitution rules, so I tried putting the lexicon in a `.ttf`.

<style>
@font-face { font-family: "semfont ttf"; src: url("/fonts/semfont-proto.woff2") format("woff2"); font-display: swap; }
.ttf-demo { border: 1px solid #3a3a3a; border-radius: 8px; padding: 18px 20px; margin: 24px 0;
            font-family: "semfont ttf", Georgia, serif; font-size: 18px; line-height: 1.6;
            height: 7.2em; overflow-y: auto; background: #fff; color: #111; }
body.light .ttf-demo { border-color: #d8d8d8; }
.ttf-note { display: flex; justify-content: space-between; align-items: baseline;
            font-size: 13px; opacity: 0.6; margin-top: -16px; }
</style>

<div class="ttf-demo" contenteditable="true" spellcheck="false">The rollback should have helped, but instead it made things worse. We fixed the crash that was corrupting user data, and the team is genuinely proud of how quickly it shipped. Unfortunately the migration failed again overnight, which is a disaster for the launch.</div>
<div class="ttf-note"><span>type in it</span><span>47 KB, no script on this page</span></div>

Nothing above is styled by JavaScript. The colour is in the font file.

Three pieces make that work. Every letter gets a copy per colour level, drawn by a `COLR` record
that points back at the original outline and paints it from a `CPAL` palette entry. A `calt`
feature then carries one contextual rule per lexicon word, swapping that word's letters for the
variants at its valence level. Boundaries are two `ignore` rules per word, so `great` does not
fire inside `greatest`.

```
lookup CLR6 { sub a by a.c6; sub b by b.c6; ... } CLR6;

ignore sub @Letter g' r' e' a' t';
ignore sub g' r' e' a' t' @Letter;
sub g' lookup CLR6 r' lookup CLR6 e' lookup CLR6 a' lookup CLR6 t' lookup CLR6;
```

The colours are computed from semfont's own editorial theme, the same oklab mix at the same 0.2
threshold, so the file agrees with the web version instead of guessing.

## What it costs

| | first build | after |
|---|---|---|
| `.ttf` | 947 KB | 275 KB |
| over the wire as woff2 | 276 KB | 47 KB |
| `glyf` | 538 KB | 16 KB |
| `GSUB` | 248 KB | 248 KB |

One change did all of that: subsetting the base font to Latin, because DejaVu ships 6,253 glyphs
and English valence needs about 100.

Two things I expected to help did not. Merging `great` and `Great` into one rule with a `[g G]`
class halved the rule count and then failed to compile at all: it pushes feaLib off the compact
class-based encoding onto one subtable per rule, 6,455 of them, past an offset limit nothing can
repair. Dropping the boundary `ignore` rules saved 3 KB. `GSUB` is 90% of what is left and I did
not find a way to move it.

## What it gets wrong

Three of the four channels do not survive. Salience counts how often a word repeats in the
passage, and substitution rules have no memory. Certainty spreads one hedge across its whole
sentence, and a sentence is longer than any context a rule can match. Only valence and static
rarity are expressible.

Negation is expressible and is not built yet, so `nobody is happy` still comes out green. That one
is backtrack context and I know how to write it.

It cannot do dark mode. A `CPAL` palette is a list of fixed colours, so the file cannot know what
it is being drawn on. The library sets `color-mix(in oklab, currentColor, ...)` and follows the
page; the font paints the same red whatever is behind it, which is why the box above is white on
a dark page.

There are 2,316 words in this build against 4,065 in the library, and the file is one fixed size
rather than a variable font, so weight and slant are gone.

It is a prototype, not a release. The library is still the thing that works:
[RohanAdwankar/semfont](https://github.com/RohanAdwankar/semfont).
