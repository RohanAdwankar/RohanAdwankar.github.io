# parsing in .woff2 

This post is a [followup](https://rohanadwankar.github.io/posts/semfont.html).
In the last post one feedback I got was that the title was inaccurate because the sentiment parsing wasn't occurring on the font level but rather the typesetting level.
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
<div class="fontnote"><span>semfont, 199 KB</span><span>type in it</span></div>

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
    <div class="fontnote"><span>what you type</span><span>type in it</span></div>
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
    <div class="fontnote"><span>what you type</span><span>type in it</span></div>
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

Every box holds plain text and instead of scripts the formatting is applied by substitution rule inside the `.woff2`.
All of these fonts are downloadable as [.woff2 files](https://github.com/RohanAdwankar/RohanAdwankar.github.io/tree/main/static/fonts).

## How it works

You may have noticed that in some fonts the `f` and `i` combine so that the cross of the f connects with the dash of the i. An example font of this in Google Docs is Lobster. This operation is called ligatures and these type of context sensitive operations are why fonts implement the substitutions we need for the fonts.

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

<>

The colour font is one rule per word, plus every real inflection of it. Two bits of state ride along in the glyph stream, one for "negated" and one for "resolved", and a clause break clears them. So `not great` reads as bad, and `fixed the crash that was corrupting` reads as good. The Markdown font gives every letter a copy per state, and there are thirty-two states. Only eight sets of those are real outlines, one per Liberation face; the rest are components pointing at one of the eight,
plus a one-em bar scaled to the letter's width for underline and strikethrough. Colour is a `COLR` record and a `CPAL` entry, so it costs no drawing at all.

Was fun exploring the world of fonts, feel free to check out [semfont](https://github.com/RohanAdwankar/semfont) for the code!
