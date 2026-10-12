# parsing in .woff2 

In [my last post](https://rohanadwankar.github.io/posts/semfont.html).post one feedback I got was that the title was inaccurate because the sentiment parsing wasn't occurring on the font level but rather the typesetting level.
This wasn't intentional but in retrospect was definitely true and drove me down a fun rabbit hole!

<style>
@font-face { font-family: "semfont ttf"; src: url("/fonts/semfont-proto.woff2") format("woff2"); font-display: swap; }
@font-face { font-family: "markfont"; src: url("/fonts/markfont.woff2") format("woff2"); font-display: swap; }
@font-face { font-family: "difffont"; src: url("/fonts/difffont.woff2") format("woff2"); font-display: swap; }
.fontbox { border: 1px solid #3a3a3a; border-radius: 8px; padding: 16px 18px; margin: 22px 0 0;
           font-size: 18px; line-height: 1.65; height: 6.2em; overflow-y: auto;
           background: #fff; color: #111; white-space: pre-wrap; }
body.light .fontbox { border-color: #d8d8d8; }
/* The fonts bake absolute colours into CPAL, so they can only be read on a
   light background. This page has no theme to switch. */
.theme-switch { display: none; }
/* "2 * 3" broke across a line and read as two fragments */
article :not(pre) > code { white-space: nowrap; }
.sf { font-family: "semfont ttf", Georgia, serif; }
.mf { font-family: "markfont", "Liberation Sans", Arial, sans-serif; }
/* The left pane is the same typeface markfont is built from, so the only
   difference across the pair is the font feature. */
.raw { font-family: "Liberation Sans", Arial, sans-serif; }
.df { font-family: "difffont", "Liberation Mono", monospace; }
.rawmono { font-family: "Liberation Mono", monospace; }
.pair.diffpair .fontbox { height: 10.4em; font-size: 16px; }
.pair { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.pair .fontbox { margin-top: 0; height: 8.4em; }
@media (max-width: 640px) { .pair { grid-template-columns: 1fr; gap: 0; } }
.fontnote { display: flex; justify-content: space-between; align-items: baseline;
            font-size: 13px; opacity: 0.6; margin: 6px 0 26px; }
</style>

<script>document.body.classList.add('light');</script>

<div class="fontbox sf" contenteditable="true" spellcheck="false">The migration ran clean, but production was not clean. It deleted the index, and the rollback failed too. Surprisingly, nobody lost data.</div>
<div class="fontnote"><span>semfont, 199 KB</span></div>

<script>
// Chrome does not reshape typed text with a font's rules until something makes it.
// Swapping between two equivalent font stacks on each keystroke does, and moves nothing.
(function () {
  var box = document.querySelector('.fontbox.sf'), flip = false;
  box.addEventListener('input', function () {
    flip = !flip;
    box.style.fontFamily = flip ? '"semfont ttf", serif' : '"semfont ttf", Georgia, serif';
  });
})();
</script>

<div class="pair">
  <div>
    <div class="fontbox raw" id="md-src" contenteditable="true" spellcheck="false">## A heading
*italic holding **bold ~~struck~~** inside*, _under_, `code`.
Not a # heading. get_user_name is safe.</div>
    <div class="fontnote"><span>what you type</span></div>
  </div>
  <div>
    <div class="fontbox mf" id="md-out"></div>
    <div class="fontnote"><span>markfont, 156 KB</span></div>
  </div>
</div>

<div class="pair diffpair">
  <div>
    <div class="fontbox rawmono" id="df-src" contenteditable="true" spellcheck="false">@@ -1,6 +1,7 @@
 def render(text):
-    return parse(text)
+    # the font does this now
+    return text</div>
    <div class="fontnote"><span>what you type</span></div>
  </div>
  <div>
    <div class="fontbox df" id="df-out"></div>
    <div class="fontnote"><span>difffont, 11 KB</span></div>
  </div>
</div>

<script>
// The only job of this script is to copy the characters across. Nothing here
// styles anything; each right pane differs from its left by one font feature.
(function () {
  [['md-src', 'md-out'], ['df-src', 'df-out']].forEach(function (ids) {
    var src = document.getElementById(ids[0]), out = document.getElementById(ids[1]);
    var mirror = function () { out.textContent = src.innerText; };
    src.addEventListener('input', mirror);
    mirror();
  });
})();
</script>

Every box holds plain text and instead of scripts the formatting is applied by substitution rule inside the font. 
All of these fonts are downloadable as [.woff2 files](https://github.com/RohanAdwankar/RohanAdwankar.github.io/tree/main/static/fonts).

## How it works

You may have noticed that in some fonts the `f` and `i` combine so that the cross of the f connects with the dash of the i. An example font of this in Google Docs is Lobster. This is called a ligature, and fonts support it through context-sensitive substitution rules. Those same rules are what we use to make a font do formatting.

Every OpenType font (.ttf, .otf, .woff2) carries a table of these substitution rules that the browser runs on each line before drawing it. For example the rule below says that an f followed by an i is drawn as one joined glyph in OpenType Feature File syntax. Fira Code does the same for `=>` and `!=`, and rules can also look at the neighbours around a glyph, which makes them a pattern matcher running inside the font:

```
feature liga {
  sub f i by f_i;
} liga;
```

To make this process easier I put together a simple [tool](https://github.com/RohanAdwankar/semfont/tree/main/gramfont), which takes a grammar and generates the feature syntax for fontTools to build. 

Formatting a git diff with a font is the easy case: a line that starts with `+` is green, with `-` is red, and with `@@` is purple, and `keep` leaves the marker visible.

```
style added   = color "#1a7f37";
style removed = color "#cf222e";
style hunk    = from "LiberationSans-Bold.ttf", color "#8250df";

added   = line_start , "+"  , { any } -> added   keep;
removed = line_start , "-"  , { any } -> removed keep;
header  = line_start , "@@" , { any } -> hunk    keep;
```

The other 2 fonts shown above are a bit harder because they have state.
For example for semfont we try to match the word with the sentiment, so that needs a rule to remember that a negation (in this case a `not`) came earlier to the word we aim to turn red. Similarly for formatting markdown we need to remember which of bold, italic and code tags are open. 
A font has no memory, so my solution is the state is carried in the glyphs themselves. This means each letter exists in a copy per state, and a rule swaps a letter for the copy that matches what came before it.

For example here is the grammer for bolding. It's basically the same as the [markdown font grammer](https://github.com/RohanAdwankar/semfont/blob/main/gramfont/examples/markdown.gram) but for simplicity lets restrict the alphabet to a, b, c, asterisk, and a space.

```
alphabet = "a-c* ";
face      = "LiberationSans-Regular.ttf";
face bold = "LiberationSans-Bold.ttf";
toggle bold = "**" -> bold;
```

The last line says that `**` flips bold on and off because in markdown bolding occurs when a word is in between those 2 symbols.

Now here's what it generates:
```
lookup PRIME   { sub @Plain by [a.s0 b.s0 c.s0 asterisk.s0 space.s0]; } PRIME;
lookup NULL_s0 { sub @Plain by null.s0; sub [a.s0 b.s0 c.s0 asterisk.s0 space.s0] by null.s0; } NULL_s0;
lookup TO_s1   { sub [a.s0 b.s0 c.s0 asterisk.s0 space.s0] by [a.s1 b.s1 c.s1 asterisk.s1 space.s1]; } TO_s1;
lookup NULL_s1 { sub @Plain by null.s1; sub [a.s0 b.s0 c.s0 asterisk.s0 space.s0] by null.s1; } NULL_s1;

lookup TOGGLE {
  sub @S0 asterisk.s0' lookup NULL_s1 asterisk.s0' lookup NULL_s1 [a.s0 b.s0 c.s0];
  sub [a.s1 b.s1 c.s1 asterisk.s1 null.s1] asterisk.s0' lookup NULL_s0 asterisk.s0' lookup NULL_s0;
  sub @S1 [a.s0 b.s0 c.s0 asterisk.s0 space.s0]' lookup TO_s1;
  ignore sub @Styled [asterisk.s0]';
  sub asterisk.s0' lookup NULL_s1 asterisk.s0' lookup NULL_s1 [a.s0 b.s0 c.s0];
} TOGGLE;
```

So let's break down the lookups:

1. `PRIME` renames every letter in the alphabet from `a` to `a.s0`, marking all of them as not bold.
2. `NULL_s0` replaces a glyph with an invisible, zero-width glyph that carries the bold-off flag.
3. `NULL_s1` does the same trick to carry the bold-on flag.
4. `TO_s1` turns a bold-off letter into its bold-on copy, so `a.s0` becomes `a.s1`.
5. `TOGGLE` is the main one. It invokes the other four lookups to generate the bolding.

A bit confusing for sure but the nice part is the tool will handle all this generation for you so you don't have to spend time writing out the lookups yourself!

I had a great time exploring the world of fonts, feel free to check out [semfont](https://github.com/RohanAdwankar/semfont) for the code and thanks for reading!

PS: One fun thing I noticed after publishing. On iOS the semfont box does not flip the colour after a `not`, so "was not clean" shows green, while the Markdown and diff fonts work fine. Every browser on iOS, Chrome included, uses Apple's text engine instead of the one Chrome uses elsewhere, and it seems to handle chained font rules differently. I don't know exactly why yet, so if you do, let me know!
