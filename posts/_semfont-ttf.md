# parsing in .woff2 

This post is a [followup](https://rohanadwankar.github.io/posts/semfont.html).
In the last post one of the feedback I got was that the title was clickbaity because the sentiment parsing wasn't occurring on the font level but rather the typesetting level.
This wasn't intentional but in retrospect was definitely true and drove me down a fun rabbithole!

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

Every box holds plain text and instead of scripts the formatting is applied by substitution rule inside the .woff2.
All of these fonts are downloadable as [.woff2 files](https://github.com/RohanAdwankar/RohanAdwankar.github.io/tree/main/static/fonts).

## How it works

A font is not only a set of shapes. Every OpenType font (.ttf, .otf, .woff2 are the same thing in different wrappers)
carries a table called GSUB, a list of substitution rules the text renderer runs on every line before drawing it.
Fonts have always used it for ligatures. This is the rule in most serif fonts that turns an f followed by an i into one joined glyph:

```
feature liga {
  sub f i by f_i;
} liga;
```

Fira Code turns `=>` into an arrow and `!=` into a slashed equals the same way, and Arabic fonts pick a letter's
initial, medial or final shape with it. The rules can also look at neighbours without consuming them. A contextual
rule says "this glyph, when the glyphs around it look like this, becomes that". That is a pattern matcher running inside the font,
and the browser already runs it on every page.

A git diff is the easy case. The pattern is "at the start of a line, a plus, then anything", and the substitution
is "the same letters, painted green". To make this easier I added a simple language to define the parsing.

For the simplest font above:

```
style added   = color "#1a7f37";
style removed = color "#cf222e";
style hunk    = from "LiberationSans-Bold.ttf", color "#8250df";

added   = line_start , "+"  , { any } -> added   keep;
removed = line_start , "-"  , { any } -> removed keep;
header  = line_start , "@@" , { any } -> hunk    keep;
```

A hard case is the same machinery with state. Negation needs a rule to remember that a `not` came earlier,
and Markdown needs to remember which of bold, italic and code are open. A font has no memory, so the
state is carried in the glyphs themselves: each letter exists in a copy per state, and a rule swaps a
letter for the copy that matches what came before it.

The colour font is one rule per word, plus every real inflection of it. Two bits of state ride
along in the glyph stream, one for "negated" and one for "resolved", and a clause break clears
them. So `not great` reads as bad, and `fixed the crash that was corrupting` reads as good. On
my test sentences the library colours 63 words, and the font agrees on the sign of 62. A plain
word list agrees on 41. Bold is the same trick with the salience lexicon and a second set of
outlines from the bold cut, and the highlight behind a surprise word is a box glyph layered
under the letter.

The Markdown font gives every letter a copy per state, and there are thirty-two states. Only
eight sets of those are real outlines, one per Liberation face; the rest are components pointing at one of the eight,
plus a one-em bar scaled to the letter's width for underline and strikethrough. Colour is a
`COLR` record and a `CPAL` entry, so it costs no drawing at all.

A closing `**` does not have to be matched with the `**` that opened it. It turns bold off
because bold was on. So emphasis is a set of flags, not a bracket, and five flags is
thirty-two states. Every glyph carries the state it is in:

```
lookup TOGGLE {
  sub @S0 asterisk.s0' lookup NULL_s1 asterisk.s0' lookup NULL_s1 @Open;  # bold on
  sub @S1 @Any.s0' lookup TO_s1;                                          # carry it
  sub @S1nonspace asterisk.s0' lookup NULL_s0 asterisk.s0' lookup NULL_s0; # bold off
}
```

A delimiter becomes a zero-width glyph carrying the state after the flip, and a lookup walks
left to right seeing its own output as backtrack, so one pass runs the whole machine. Depth
never comes up, which is why the four nested spans in the box above come out right.

The guards are the rest. An opener needs a non-space after it and a closer needs a non-space
before it, so `2 * 3 * 4` survives. An underscore after a word character opens nothing, so
`get_user_name` survives. A heading only fires with nothing to backtrack over, which is the
only line-start test OpenType offers, so `C#` survives.

Feel free to check out [RohanAdwankar/semfont](https://github.com/RohanAdwankar/semfont) for the code. 
